#!/usr/bin/env python3
"""Minimal Rokoko Studio UDP tracker for MANO keypoints and wrist pose."""

from __future__ import annotations

import json
import socket
import threading
import time
from typing import Any

import numpy as np
from scipy.spatial.transform import Rotation


_FINGER_BONES = (
    "ThumbProximal",
    "ThumbMedial",
    "ThumbDistal",
    "ThumbTip",
    "IndexProximal",
    "IndexMedial",
    "IndexDistal",
    "IndexTip",
    "MiddleProximal",
    "MiddleMedial",
    "MiddleDistal",
    "MiddleTip",
    "RingProximal",
    "RingMedial",
    "RingDistal",
    "RingTip",
    "LittleProximal",
    "LittleMedial",
    "LittleDistal",
    "LittleTip",
)

_R_Z_180 = Rotation.from_matrix(
    np.array([[-1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]])
)


def _mano_bone_names(hand: str) -> tuple[str, ...]:
    """Return Rokoko bone names in the 22-point layout used by Retargeter."""
    side = hand.lower()
    prefix = side
    return (
        f"{prefix}LowerArm",
        f"{prefix}Hand",
        *(f"{prefix}{bone}" for bone in _FINGER_BONES),
    )


class RokokoTracker:
    """
    Receive one Rokoko glove from Rokoko Studio's Custom Streaming UDP output.

    ``get_keypoint_positions()`` returns a 22x3 array in MANO order:
    forearm, wrist, then four joints for thumb through little finger.
    ``get_mocap_pose()`` returns the filtered, zero-calibrated 6-DoF hand pose.
    """

    def __init__(
        self,
        ip: str = "0.0.0.0",
        port: int = 14043,
        hand: str = "right",
        initial_position: tuple[float, float, float] = (0.34, 0.1, 0.3),
        initial_quaternion: tuple[float, float, float, float] = (
            1.0,
            0.0,
            0.0,
            0.0,
        ),
        position_alpha: float = 0.95,
        quaternion_alpha: float = 0.85,
    ) -> None:
        if hand not in {"left", "right"}:
            raise ValueError("hand must be 'left' or 'right'")
        if not 0.0 <= position_alpha < 1.0:
            raise ValueError("position_alpha must be in [0, 1)")
        if not 0.0 <= quaternion_alpha < 1.0:
            raise ValueError("quaternion_alpha must be in [0, 1)")

        self.ip = ip
        self.port = port
        self.hand = hand
        self.initial_position = np.asarray(initial_position, dtype=np.float64)
        if self.initial_position.shape != (3,):
            raise ValueError("initial_position must contain three values")
        self.initial_quaternion = np.asarray(
            initial_quaternion, dtype=np.float64
        )
        if self.initial_quaternion.shape != (4,):
            raise ValueError("initial_quaternion must contain four values")
        quaternion_norm = np.linalg.norm(self.initial_quaternion)
        if quaternion_norm == 0.0:
            raise ValueError("initial_quaternion must be nonzero")
        self.initial_quaternion /= quaternion_norm
        self.position_alpha = position_alpha
        self.quaternion_alpha = quaternion_alpha
        self._bone_names = _mano_bone_names(hand)
        self._keypoints: np.ndarray | None = None
        self._mocap_position: np.ndarray | None = None
        self._mocap_quaternion: np.ndarray | None = None
        self._filtered_position: np.ndarray | None = None
        self._filtered_quaternion: np.ndarray | None = None
        self._zero_position: np.ndarray | None = None
        self._zero_quaternion: np.ndarray | None = None
        self._keypoints_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_warning = 0.0

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(0.25)
        self._socket.bind((ip, port))

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._read_rokoko_data,
            name="rokoko-udp",
            daemon=True,
        )
        self._thread.start()
        print(
            f"[rokoko] listening on {self.ip}:{self.port} for {self.hand} glove",
            flush=True,
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._socket.close()

    def get_keypoint_positions(self) -> np.ndarray | None:
        with self._keypoints_lock:
            return self._keypoints.copy() if self._keypoints is not None else None

    def get_mocap_pose(self) -> tuple[np.ndarray, np.ndarray] | None:
        """Return calibrated MuJoCo position and quaternion (w, x, y, z)."""
        with self._keypoints_lock:
            if self._mocap_position is None or self._mocap_quaternion is None:
                return None
            return self._mocap_position.copy(), self._mocap_quaternion.copy()

    @staticmethod
    def _position(value: dict[str, Any]) -> np.ndarray:
        return np.array([value["x"], value["y"], value["z"]], dtype=np.float64)

    @staticmethod
    def _quaternion(value: dict[str, Any]) -> np.ndarray:
        return np.array(
            [value["x"], value["y"], value["z"], value["w"]],
            dtype=np.float64,
        )

    def _extract_keypoints(self, packet: dict[str, Any]) -> np.ndarray:
        body = packet["scene"]["actors"][0]["body"]
        points = np.stack(
            [self._position(body[name]["position"]) for name in self._bone_names]
        )

        # Match the coordinate conversion used by faive_system's Rokoko ingress.
        # It mirrors the right hand about the actor's chest; the left-hand stream
        # is intentionally left unchanged so it can drive the same right-hand model.
        if self.hand == "right":
            chest = self._position(body["chest"]["position"])
            points = chest - points

        if points.shape != (22, 3):
            raise ValueError(f"expected 22x3 hand keypoints, got {points.shape}")
        return points

    def _extract_wrist_pose(
        self, packet: dict[str, Any]
    ) -> tuple[np.ndarray, np.ndarray]:
        """Apply the reference Rokoko ingress and MuJoCo axis conversions."""
        body = packet["scene"]["actors"][0]["body"]
        hand_data = body[f"{self.hand}Hand"]

        # faive_system ingress: invert Z and rotate 180 degrees around Z.
        ingress_position = self._position(hand_data["position"])
        ingress_position[2] *= -1.0
        ingress_rotation = _R_Z_180 * Rotation.from_quat(
            self._quaternion(hand_data["rotation"])
        )
        ingress_quaternion = ingress_rotation.as_quat()

        # Reference MuJoCo controller:
        #   position (x, y, z) -> (-z, -x, y)
        #   quaternion xyzw    -> (w, -z, -x, y)
        position = np.array(
            [
                -ingress_position[2],
                -ingress_position[0],
                ingress_position[1],
            ],
            dtype=np.float64,
        )
        quaternion = np.array(
            [
                ingress_quaternion[3],
                -ingress_quaternion[2],
                -ingress_quaternion[0],
                ingress_quaternion[1],
            ],
            dtype=np.float64,
        )
        quaternion /= np.linalg.norm(quaternion)
        return position, quaternion

    def _calibrate_mocap_pose(
        self, position: np.ndarray, quaternion: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Smooth the signal and make the first received pose the scene origin."""
        if self._filtered_position is None:
            self._filtered_position = position.copy()
            self._filtered_quaternion = quaternion.copy()
        else:
            self._filtered_position = (
                self.position_alpha * self._filtered_position
                + (1.0 - self.position_alpha) * position
            )

            # Normalized linear quaternion interpolation with hemisphere matching.
            if np.dot(self._filtered_quaternion, quaternion) < 0.0:
                quaternion = -quaternion
            self._filtered_quaternion = (
                self.quaternion_alpha * self._filtered_quaternion
                + (1.0 - self.quaternion_alpha) * quaternion
            )
            self._filtered_quaternion /= np.linalg.norm(
                self._filtered_quaternion
            )

        if self._zero_position is None:
            self._zero_position = self._filtered_position.copy()
            self._zero_quaternion = self._filtered_quaternion.copy()
            print("[rokoko] wrist zero pose captured", flush=True)

        mocap_position = (
            self._filtered_position - self._zero_position + self.initial_position
        )

        rotation_now = Rotation.from_quat(np.roll(self._filtered_quaternion, -1))
        rotation_zero = Rotation.from_quat(np.roll(self._zero_quaternion, -1))
        rotation_initial = Rotation.from_quat(
            np.roll(self.initial_quaternion, -1)
        )

        # Remove the zero-pose orientation in the MuJoCo world frame. Using
        # rotation_zero.inv() * rotation_now instead would express the delta in
        # the initial hand frame, whose +X/+Y/+Z map to MuJoCo -Y/+Z/-X.
        rotation_delta = rotation_now * rotation_zero.inv()
        rotation_out = rotation_delta * rotation_initial
        mocap_quaternion = np.roll(rotation_out.as_quat(), 1)
        return mocap_position, mocap_quaternion

    def _warn(self, message: str) -> None:
        now = time.monotonic()
        if now - self._last_warning >= 1.0:
            print(f"[rokoko] ignoring packet: {message}", flush=True)
            self._last_warning = now

    def _read_rokoko_data(self) -> None:
        packet_count = 0
        report_start = time.monotonic()

        while not self._stop_event.is_set():
            try:
                payload, _ = self._socket.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError as exc:
                if not self._stop_event.is_set():
                    self._warn(str(exc))
                break

            try:
                packet = json.loads(payload.decode("utf-8"))
                keypoints = self._extract_keypoints(packet)
                wrist_position, wrist_quaternion = self._extract_wrist_pose(packet)
                mocap_position, mocap_quaternion = self._calibrate_mocap_pose(
                    wrist_position, wrist_quaternion
                )
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError,
                    TypeError, ValueError) as exc:
                self._warn(str(exc))
                continue

            with self._keypoints_lock:
                self._keypoints = keypoints
                self._mocap_position = mocap_position
                self._mocap_quaternion = mocap_quaternion

            packet_count += 1
            now = time.monotonic()
            if now - report_start >= 2.0:
                print(
                    f"[rokoko] {packet_count / (now - report_start):.1f} Hz",
                    flush=True,
                )
                packet_count = 0
                report_start = now
