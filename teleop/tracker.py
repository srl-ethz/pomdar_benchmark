"""
MediaPipe hand tracker using the Tasks API (mediapipe >= 0.10).
Runs detection in a background thread; optional cv2 preview also lives there
so it never conflicts with MuJoCo's Qt window in the main thread.
"""

from __future__ import annotations

import threading
import time
import urllib.request
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as _mp_python
from mediapipe.tasks.python import vision as _mp_vision


# ── Model auto-download ───────────────────────────────────────────────────────
_MODEL_CACHE = Path.home() / ".cache" / "mediapipe" / "hand_landmarker.task"
_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)


def _ensure_model() -> str:
    if not _MODEL_CACHE.is_file():
        _MODEL_CACHE.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading MediaPipe hand landmarker → {_MODEL_CACHE} …")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_CACHE)
        print("Download complete.")
    return str(_MODEL_CACHE)


# ── Skeleton connections for drawing ─────────────────────────────────────────
_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17),
]


class MediaPipeTracker:
    """
    Captures webcam frames and runs MediaPipe hand landmark detection
    in a background thread.

    World landmarks for the user's RIGHT hand (label 'Left' in MediaPipe's
    mirrored convention) are stored and retrievable via get_keypoint_positions().

    If show_preview=True the annotated frame is displayed from the same
    background thread — never from the main thread — so Qt does not conflict
    with MuJoCo's viewer.
    """

    def __init__(self, camera_index: int = 0, show_preview: bool = True):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise IOError(f"Cannot open camera {camera_index}")

        options = _mp_vision.HandLandmarkerOptions(
            base_options=_mp_python.BaseOptions(model_asset_path=_ensure_model()),
            running_mode=_mp_vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._detector = _mp_vision.HandLandmarker.create_from_options(options)
        self.show_preview = show_preview

        self._kp: Optional[np.ndarray] = None
        # Normalized wrist position in image space: (x, y) in [0,1]
        # x=0 left, x=1 right; y=0 top, y=1 bottom (raw camera, not flipped)
        self._wrist_norm: Optional[np.ndarray] = None
        self._kp_lock = threading.Lock()
        self.running = False
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.running = True
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        self._thread.join(timeout=3.0)
        self.cap.release()

    def get_keypoint_positions(self) -> Optional[np.ndarray]:
        """Returns a copy of the latest 21×3 world-landmark array, or None."""
        with self._kp_lock:
            return self._kp.copy() if self._kp is not None else None

    def get_wrist_norm(self) -> Optional[np.ndarray]:
        """Returns (x, y) normalized wrist position in image space, or None.
        x in [0,1] left→right, y in [0,1] top→bottom (raw camera frame)."""
        with self._kp_lock:
            return self._wrist_norm.copy() if self._wrist_norm is not None else None

    def _run(self) -> None:
        t0 = time.monotonic()
        if self.show_preview:
            cv2.namedWindow("Webcam – hand tracking", cv2.WINDOW_NORMAL)

        n_frames = n_detected = 0
        t_last = time.monotonic()

        while self.running and self.cap.isOpened():
            ok, bgr = self.cap.read()
            if not ok:
                print("[tracker] cap.read() failed", flush=True)
                continue

            ts_ms = int((time.monotonic() - t0) * 1000)
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self._detector.detect_for_video(mp_img, ts_ms)

            # Update world keypoints + normalized wrist (thread-safe)
            new_kp = None
            new_wrist_norm = None
            if result.hand_world_landmarks and result.handedness:
                for i, (wlms, cat) in enumerate(zip(result.hand_world_landmarks, result.handedness)):
                    if cat[0].category_name == "Right":
                        new_kp = np.array(
                            [(lm.x, lm.y, lm.z) for lm in wlms],
                            dtype=np.float32,
                        )
                        # Normalized landmarks give wrist 2-D position in image
                        if result.hand_landmarks and i < len(result.hand_landmarks):
                            wrist_lm = result.hand_landmarks[i][0]
                            new_wrist_norm = np.array([wrist_lm.x, wrist_lm.y], dtype=np.float32)
                        n_detected += 1
            with self._kp_lock:
                self._kp = new_kp
                self._wrist_norm = new_wrist_norm

            n_frames += 1
            now = time.monotonic()
            if now - t_last >= 2.0:
                print(f"[tracker]  {n_frames/(now-t_last):.1f} Hz total  "
                      f"hand detected {n_detected/(now-t_last):.1f} Hz", flush=True)
                n_frames = n_detected = 0
                t_last = now

            if self.show_preview:
                h, w = bgr.shape[:2]
                vis = cv2.flip(bgr, 1)
                if result.hand_landmarks:
                    for nlms in result.hand_landmarks:
                        pts = [(int((1.0 - lm.x) * w), int(lm.y * h)) for lm in nlms]
                        for a, b in _CONNECTIONS:
                            cv2.line(vis, pts[a], pts[b], (0, 220, 0), 2)
                        for pt in pts:
                            cv2.circle(vis, pt, 4, (255, 80, 0), -1)
                cv2.imshow("Webcam – hand tracking", vis)
                if cv2.waitKey(1) & 0xFF == 27:  # ESC
                    self.running = False
                    break

        self.cap.release()
        if self.show_preview:
            cv2.destroyAllWindows()
