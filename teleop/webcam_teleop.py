#!/usr/bin/env python3
"""
Webcam teleoperation of the Orca hand (v1b, 17 DOF) in MuJoCo.
No ROS, no fixed paths — runs from any working directory.

Architecture:
  • Tracker thread    — webcam + MediaPipe hand detection
  • Retargeter thread — gradient-descent mapping from landmarks to joint angles
  • Sim thread        — mj_step at fixed Hz (holds data_lock)
  • Main thread       — writes ctrl, calls viewer.sync() (same lock as sim thread)

Usage:
  python teleop/webcam_teleop.py
  python teleop/webcam_teleop.py --task V1_Wheel
  python teleop/webcam_teleop.py --no-preview
  python teleop/webcam_teleop.py --help

See README.md for installation instructions.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import torch

# Keep PyTorch to one intra-op thread so it doesn't fight MediaPipe/GLFW
# for CPU cores.  Must be set before any torch ops run.
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

_TELEOP = Path(__file__).resolve().parent
if str(_TELEOP) not in sys.path:
    sys.path.insert(0, str(_TELEOP))

from tracker    import MediaPipeTracker   # noqa: E402
from retargeter import Retargeter         # noqa: E402
import mujoco                             # noqa: E402
import mujoco.viewer                      # noqa: E402

# ── Paths ─────────────────────────────────────────────────────────────────────
_SIM_DIR = _TELEOP.parent / "sim"

# Retargeter uses orca_v1_nowrist.xml (no free joint → clean FK chain)
# MuJoCo scene uses orca_v1.xml (full model with free joint + mocap weld)
_MJCF_FK  = _TELEOP / "orca_v1_nowrist.xml"
_SCHEME   = _TELEOP / "scheme_orca_v1_nowrist.yaml"
_MANO_ADJ = _TELEOP / "mano_adjustment_orca_v1.yaml"

_RETARGETER_CFG = {
    "lr": 2.5,
    "loss_func_cfg": {
        "keyvector_fingers2palm":    2.0,
        "keyvector_fingers2fingers": 1.0,
        "zero_regularizor": {
            "weight": 0.01,
            "kwargs": {
                "index_abd":   [0, 1.0],
                "middle_abd":  [0, 1.0],
                "ring_abd":    [0, 1.0],
                "pinky_abd":   [0, 1.0],
                "thumb_pp2mp": [0.7, 0.5],
                "thumb_mp2dp": [0.7, 0.5],
            },
        },
    },
}

_SCENE_TEMPLATE = """\
<mujoco model="orca_teleop">
  <compiler angle="radian" meshdir="assets" autolimits="true" inertiafromgeom="true"/>
  <include file="hand/orca_v1.xml"/>
{task_include}
  <option cone="elliptic" impratio="10"/>
  <statistic extent="1" center="0 0 0"/>
  <visual>
    <rgba haze="0.15 0.25 0.35 1"/>
    <quality shadowsize="8192"/>
    <global azimuth="220" elevation="-30"/>
  </visual>
  <asset>
    <texture name="wood" type="2d" file="assets/table_texture.png"/>
    <material name="wood" texture="wood" reflectance="0.1"/>
    <material name="dark_wood" rgba="0.4 0.2 0.1 1"/>
    <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="3072"/>
    <texture type="2d" name="groundplane" builtin="checker" mark="edge"
             rgb1="0.2 0.3 0.4" rgb2="0.1 0.2 0.3" markrgb="0.8 0.8 0.8" width="300" height="300"/>
    <material name="groundplane" texture="groundplane" texuniform="true" texrepeat="5 5" reflectance="0.2"/>
  </asset>
  <worldbody>
    <light name="top" directional="true" pos="0 0 3" dir="0 0 -1"
           diffuse="0.55 0.55 0.55" ambient="0.15 0.15 0.15" castshadow="false"/>
    <geom name="floor" pos="0 0 -1" size="0 0 0.02" type="plane" material="groundplane"/>
    <body name="table_body" pos="0 0 -0.02">
      <geom type="box" size="0.6 0.4 0.02" material="wood" mass="10"/>
      <geom type="box" size="0.02 0.02 0.48" pos=" 0.58  0.38 -0.5" material="dark_wood" density="700"/>
      <geom type="box" size="0.02 0.02 0.48" pos="-0.58  0.38 -0.5" material="dark_wood" density="700"/>
      <geom type="box" size="0.02 0.02 0.48" pos=" 0.58 -0.38 -0.5" material="dark_wood" density="700"/>
      <geom type="box" size="0.02 0.02 0.48" pos="-0.58 -0.38 -0.5" material="dark_wood" density="700"/>
    </body>
    <body name="hand_mocap" mocap="true" pos="0.34 0.1 0.3" quat="1 0 0 0">
      <geom type="sphere" size="0.005" rgba="1 0 0 0" contype="0" conaffinity="0"/>
    </body>
  </worldbody>
  <equality>
    <weld body1="hand_mocap" body2="root" solimp="0.97 0.99 0.0005" solref="0.005 1"/>
  </equality>
</mujoco>
"""


# ── Keypoint helpers ──────────────────────────────────────────────────────────

def normalize_scale(kp: np.ndarray) -> np.ndarray:
    wrist = kp[0]
    avg = np.mean([np.linalg.norm(wrist - kp[i]) for i in [5, 9, 13, 17]])
    return (kp - wrist) * (0.09 / avg) + wrist


def add_forearm(kp: np.ndarray) -> np.ndarray:
    wrist, mid_base = kp[0], kp[9]
    return np.vstack((wrist + (wrist - mid_base), kp))


# ── Retargeter worker thread ──────────────────────────────────────────────────

class RetargeterWorker:
    """Runs retarget() in a dedicated thread; main thread reads ctrl non-blocking."""

    def __init__(self, retargeter: Retargeter, tracker: MediaPipeTracker, opt_steps: int = 2):
        self._ret       = retargeter
        self._tracker   = tracker
        self._opt_steps = opt_steps
        self._ctrl: np.ndarray | None = None
        self._lock  = threading.Lock()
        self.running = False
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.running = True
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        self._thread.join(timeout=3.0)

    def get_ctrl(self) -> np.ndarray | None:
        with self._lock:
            return self._ctrl.copy() if self._ctrl is not None else None

    def _run(self) -> None:
        n = 0
        t0 = time.monotonic()
        while self.running:
            kp = self._tracker.get_keypoint_positions()
            if kp is None:
                time.sleep(0.005)
                continue
            try:
                kp_mano = add_forearm(normalize_scale(kp))
                angles_deg, _ = self._ret.retarget(kp_mano, opt_steps=self._opt_steps)
                with self._lock:
                    self._ctrl = angles_deg / 180.0 * np.pi
                n += 1
                now = time.monotonic()
                if now - t0 >= 2.0:
                    print(f"[retargeter] {n/(now-t0):.1f} Hz", flush=True)
                    n, t0 = 0, now
            except Exception as e:
                print(f"[retargeter] ERROR: {e}", flush=True)
                time.sleep(0.05)


# ── Sim thread — mj_step only, protected by data_lock ────────────────────────

def sim_loop(model: mujoco.MjModel, data: mujoco.MjData,
             data_lock: threading.Lock, stop_evt: threading.Event,
             sim_hz: float = 500.0) -> None:
    """Mirrors sim_loop() from run_teleop_mujoco.py exactly."""
    dt = 1.0 / sim_hz
    n = 0
    t0 = time.monotonic()
    while not stop_evt.is_set():
        t_step = time.perf_counter()
        with data_lock:
            mujoco.mj_step(model, data)
        n += 1
        now = time.monotonic()
        if now - t0 >= 2.0:
            print(f"[sim]  {n/(now-t0):.0f} Hz", flush=True)
            n, t0 = 0, now
        elapsed = time.perf_counter() - t_step
        rem = dt - elapsed
        if rem > 0:
            time.sleep(rem)


# ── Scene helpers ─────────────────────────────────────────────────────────────

def _resolve_task(sim_dir: Path, task: str) -> Path:
    name = task if task.endswith(".xml") else task + ".xml"
    for p in [sim_dir / "tasks" / name, sim_dir / name, Path(name)]:
        if p.is_file():
            return p.resolve()
    raise FileNotFoundError(f"Task {task!r} not found under {sim_dir / 'tasks'}")


def _build_scene(sim_dir: Path, task: str | None) -> str:
    if task:
        rel = os.path.relpath(_resolve_task(sim_dir, task), sim_dir).replace(os.sep, "/")
        task_line = f'  <include file="{rel}"/>'
    else:
        task_line = ""
    return _SCENE_TEMPLATE.format(task_include=task_line)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    available = sorted(p.stem for p in (_SIM_DIR / "tasks").glob("*.xml"))

    ap = argparse.ArgumentParser(description="Webcam teleoperation of the Orca hand in MuJoCo.")
    ap.add_argument("--task",         default=None,
                    help=f"PoMDAR task to load. Available: {', '.join(available)}")
    ap.add_argument("--list-tasks",   action="store_true", help="Print available tasks and exit.")
    ap.add_argument("--camera-index", type=int, default=0,  help="Webcam device index (default 0).")
    ap.add_argument("--opt-steps",    type=int, default=2,  help="Retargeter gradient steps (default 2).")
    ap.add_argument("--sim-hz",       type=float, default=500.0, help="Physics rate in Hz (default 500).")
    ap.add_argument("--no-preview",   action="store_true",  help="Disable the webcam preview window.")
    args = ap.parse_args()

    if args.list_tasks:
        print("\n".join(available))
        return

    # ── Retargeter ────────────────────────────────────────────────────────────
    print("Loading retargeter …", flush=True)
    retargeter = Retargeter(
        mjcf_filepath    = str(_MJCF_FK),
        hand_scheme      = str(_SCHEME),
        mano_adjustments = str(_MANO_ADJ),
        retargeter_cfg   = _RETARGETER_CFG,
        device           = "cpu",
    )
    print("Retargeter ready.", flush=True)

    # ── MuJoCo scene ─────────────────────────────────────────────────────────
    scene_xml = _build_scene(_SIM_DIR, args.task)
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix="_teleop.xml", delete=False, dir=_SIM_DIR)
    tmp.write(scene_xml)
    tmp.close()
    scene_path = tmp.name

    try:
        model = mujoco.MjModel.from_xml_path(scene_path)
    except Exception as e:
        os.unlink(scene_path)
        raise SystemExit(f"MuJoCo load error: {e}") from e

    data = mujoco.MjData(model)
    print(f"Scene loaded: nq={model.nq} nv={model.nv} nu={model.nu}", flush=True)

    # ── Start tracker + retargeter threads ───────────────────────────────────
    tracker = MediaPipeTracker(
        camera_index=args.camera_index,
        show_preview=not args.no_preview,
    )
    worker = RetargeterWorker(retargeter, tracker, opt_steps=args.opt_steps)
    tracker.start()
    worker.start()
    print("Tracker and retargeter started.", flush=True)

    # ── Sim thread + main viewer loop ─────────────────────────────────────────
    # Pattern from run_teleop_mujoco.py:
    #   sim thread:  with data_lock: mj_step(model, data)
    #   main thread: with data_lock: data.ctrl[:] = ctrl
    #                viewer.sync()   ← same thread that owns data writes,
    #                                  so NO concurrent C-level access on data.
    data_lock = threading.Lock()
    stop_evt  = threading.Event()

    sim_thread = threading.Thread(
        target=sim_loop,
        args=(model, data, data_lock, stop_evt, args.sim_hz),
        daemon=True,
    )

    print("Close the MuJoCo window to quit.", flush=True)
    try:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            sim_thread.start()   # start AFTER launch_passive initialises data
            n_sync = 0
            t0 = time.monotonic()
            while viewer.is_running():
                ctrl = worker.get_ctrl()
                with data_lock:
                    if ctrl is not None:
                        data.ctrl[:] = ctrl
                    viewer.sync()
                time.sleep(0.016)   # ~60 Hz render
                n_sync += 1
                now = time.monotonic()
                if now - t0 >= 2.0:
                    print(f"[viewer] {n_sync/(now-t0):.0f} Hz  "
                          f"ctrl={'live' if ctrl is not None else 'waiting'}", flush=True)
                    n_sync, t0 = 0, now
    finally:
        stop_evt.set()
        sim_thread.join(timeout=2.0)
        worker.stop()
        tracker.stop()
        try:
            os.unlink(scene_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
