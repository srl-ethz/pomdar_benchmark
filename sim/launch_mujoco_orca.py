#!/usr/bin/env python3
"""
Open the PoMDAR MuJoCo scene: Orca nowrist hand + one benchmark task.
Self-contained under this directory (no retargeting required).

Usage:
  python3 launch_mujoco_orca.py --task V1_Wheel
  python3 launch_mujoco_orca.py --list-tasks
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import mujoco
import mujoco.viewer


SCENE_TEMPLATE = """<mujoco model="sim_pomdar_scene">
  <compiler angle="radian" meshdir="assets" autolimits="true" inertiafromgeom="true"/>
  <include file="hand/orca_v1.xml"/>
  <include file="{task_rel}"/>

  <option cone="elliptic" impratio="10"/>
  <statistic extent="1" center="0 0 0"/>

  <visual>
    <rgba haze="0.15 0.25 0.35 1"/>
    <quality shadowsize="8192"/>
    <global azimuth="220" elevation="-30"/>
  </visual>

  <asset>
    <texture name="wood_texture_map" type="2d" file="assets/table_texture.png"/>
    <material name="textured_wood" texture="wood_texture_map" rgba="1 1 1 1" reflectance="0.1"/>
    <material name="dark_wood" rgba="0.4 0.2 0.1 1"/>
    <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="3072"/>
    <texture type="2d" name="groundplane" builtin="checker" mark="edge" rgb1="0.2 0.3 0.4" rgb2="0.1 0.2 0.3"
      markrgb="0.8 0.8 0.8" width="300" height="300"/>
    <material name="groundplane" texture="groundplane" texuniform="true" texrepeat="5 5" reflectance="0.2"/>
  </asset>

  <worldbody>
    <light name="lite_top" directional="true" pos="0 0 3" dir="0 0 -1"
           diffuse="0.55 0.55 0.55" ambient="0.15 0.15 0.15" castshadow="false"/>
    <geom name="floor" pos="0 0 -1" size="0 0 0.02" type="plane" material="groundplane"/>
    <body name="table_body" pos="0 0 -0.02">
      <geom name="table_top" type="box" size="0.6 0.4 0.02" material="textured_wood" mass="10"/>
      <geom name="leg1" type="box" size="0.02 0.02 0.48" pos=" 0.58  0.38 -0.5" material="dark_wood" density="700"/>
      <geom name="leg2" type="box" size="0.02 0.02 0.48" pos="-0.58  0.38 -0.5" material="dark_wood" density="700"/>
      <geom name="leg3" type="box" size="0.02 0.02 0.48" pos=" 0.58 -0.38 -0.5" material="dark_wood" density="700"/>
      <geom name="leg4" type="box" size="0.02 0.02 0.48" pos="-0.58 -0.38 -0.5" material="dark_wood" density="700"/>
    </body>
    <body name="hand_mocap" mocap="true" pos="0.34 0.1 0.3" quat="1 0 0 0">
      <geom type="sphere" size="0.01" rgba="1 0 0 0" contype="0" conaffinity="0"/>
    </body>
  </worldbody>

  <equality>
    <weld body1="hand_mocap" body2="root" solimp="0.97 0.99 0.0005" solref="0.005 1"/>
  </equality>

</mujoco>
"""


def _task_path(root: Path, task: str) -> Path:
    raw = task.strip()
    p = Path(raw)
    if p.is_file():
        return p.resolve()
    name = raw if raw.endswith(".xml") else raw + ".xml"
    for candidate in [root / "tasks" / name, root / name]:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Task {task!r} not found under {root / 'tasks'}.")


def _rel_posix(here: Path, target: Path) -> str:
    return os.path.relpath(target, here).replace(os.sep, "/")


def main() -> None:
    root = Path(__file__).resolve().parent
    available = sorted(p.stem for p in (root / "tasks").glob("*.xml"))

    ap = argparse.ArgumentParser(
        description="MuJoCo passive viewer: Orca hand + one PoMDAR task."
    )
    ap.add_argument("--task", default="V1_Wheel",
                    help=f"Task name or path (default V1_Wheel). Available: {', '.join(available)}")
    ap.add_argument("--list-tasks", action="store_true",
                    help="Print available task names and exit.")
    args = ap.parse_args()

    if args.list_tasks:
        for name in available:
            print(name)
        return

    hand = root / "hand" / "orca_v1.xml"
    if not hand.is_file():
        raise SystemExit(f"Missing hand MJCF: {hand}")

    task_path = _task_path(root, args.task)
    scene = SCENE_TEMPLATE.format(task_rel=_rel_posix(root, task_path))

    with tempfile.NamedTemporaryFile(
        mode="w", suffix="_pomdar_scene.xml", delete=False, dir=root
    ) as f:
        f.write(scene)
        scene_path = f.name

    try:
        model = mujoco.MjModel.from_xml_path(scene_path)
    except Exception as e:
        try:
            os.unlink(scene_path)
        except OSError:
            pass
        raise SystemExit(f"Failed to load scene (task={args.task}): {e}") from e

    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    try:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            while viewer.is_running():
                mujoco.mj_step(model, data)
                viewer.sync()
    finally:
        try:
            os.unlink(scene_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
