#!/usr/bin/env python3
"""Minimal Rokoko Studio UDP tracker for MANO hand keypoints."""

from __future__ import annotations

import json
import socket
import threading
import time
from typing import Any

import numpy as np


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
    """

    def __init__(
        self,
        ip: str = "0.0.0.0",
        port: int = 14043,
        hand: str = "right",
    ) -> None:
        if hand not in {"left", "right"}:
            raise ValueError("hand must be 'left' or 'right'")

        self.ip = ip
        self.port = port
        self.hand = hand
        self._bone_names = _mano_bone_names(hand)
        self._keypoints: np.ndarray | None = None
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

    @staticmethod
    def _position(value: dict[str, Any]) -> np.ndarray:
        return np.array([value["x"], value["y"], value["z"]], dtype=np.float64)

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
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError,
                    TypeError, ValueError) as exc:
                self._warn(str(exc))
                continue

            with self._keypoints_lock:
                self._keypoints = keypoints

            packet_count += 1
            now = time.monotonic()
            if now - report_start >= 2.0:
                print(
                    f"[rokoko] {packet_count / (now - report_start):.1f} Hz",
                    flush=True,
                )
                packet_count = 0
                report_start = now
