# PoMDAR MuJoCo bundle (Orca hand + tasks)

**Confidential — supplementary material for a RAL submission only.** This archive is not intended for public distribution; it is provided as additional material to support the review process and must be handled in line with the journal’s confidentiality expectations.

This folder is a self-contained subset of the benchmark simulation assets: the **Orca nowrist** hand model and **PoMDAR task** MJCF fragments, plus meshes and textures under `assets/`. It is meant for inspection, visualization, or reuse in the MuJoCo viewer.

## Requirements

- **Python 3.9+** (3.10+ recommended)
- **MuJoCo** (official Python package)
- A **graphical display** and OpenGL (the launcher opens the native MuJoCo viewer)

## Install

From this directory, install the official bindings:

```bash
pip install mujoco
```

(Use a virtual environment if you prefer: `python -m venv .venv && source .venv/bin/activate` then `pip install mujoco`.)

No other packages are required for the included launcher. If the viewer window fails to start, check that your OS has working GPU/GL support for MuJoCo (see the [MuJoCo documentation](https://mujoco.readthedocs.io/)).

## What’s in this folder

| Path | Description |
|------|-------------|
| `launch_mujoco_orca.py` | Python script: builds a small **scene** MJCF (table, floor, lighting, mocap anchor, weld to the hand) and opens `mujoco.viewer` with the chosen task. |
| `launch_mujoco_orca.sh` | Shell wrapper: runs `launch_mujoco_orca.py` from this directory. |
| `hand/orca_v1.xml` | **Hand** model: actuated fingers, `free` root, meshes under `assets/orca/`. The composed scene welds a mocap body to the hand’s `root` so the hand stays fixed for viewing (same idea as the project’s `0_sim_pomdar_scene_orca.xml` pattern). |
| `tasks/*.xml` | **Task** fragments: object and mechanism definitions only. Filenames match the **current paper** task names (see table below). Meshes are resolved via the top-level `meshdir` pointing at `assets/`. |
| `assets/` | All meshes, collision decompositions, and scene textures (table, `orca/*.stl`, per-task STLs/OBJs, etc.). This directory is large on purpose. |

**Not included (by design):** teleop / hand-tracking scripts, MANO or retargeting configuration, or the generated 6-DoF wrist variant (`_generated_include_*.xml`). The bundle is only what is needed to open the hand plus a task in the stock viewer.

## How to run

Always run from **this** directory so paths in the MJCF resolve correctly, or use the provided shell script (which `cd`s here).

**List task IDs (XML stems in `tasks/`):**

```bash
python3 launch_mujoco_orca.py --list-tasks
```

**Open a specific task (default is `V1_Wheel`):**

```bash
python3 launch_mujoco_orca.py --task V1_Wheel
python3 launch_mujoco_orca.py --task H2_Chopsticks
python3 launch_mujoco_orca.py --task G5_Cylinder
```

**Equivalent with the shell wrapper:**

```bash
chmod +x launch_mujoco_orca.sh   # once, if needed
./launch_mujoco_orca.sh --task C1_Thread
```

**Advanced:** you can point `--task` at an **absolute or relative path** to another task MJCF file (same mesh layout conventions as the bundled `tasks/` files).

## Tasks (paper names and files)

Task **files** use underscores instead of spaces. The table is the naming used in the paper; **V** = in-hand variants, **C** = constrained, **H** = human-tool, **G** = grasping.

| Paper name | File (`tasks/…`) |
|------------|------------------|
| V1 Wheel | `V1_Wheel.xml` |
| V2 Stick | `V2_Stick.xml` |
| V3 Sphere | `V3_Sphere.xml` |
| C3 Wheel | `C3_Wheel.xml` |
| C2 Stick | `C2_Stick.xml` |
| C4 Fidget | `C4_Fidget.xml` |
| C1 Thread | `C1_Thread.xml` |
| H1 Scissors | `H1_Scissors.xml` |
| H3 Squeeze | `H3_Squeeze.xml` |
| H2 Chopsticks | `H2_Chopsticks.xml` |
| H4 Palmar – H5 Pinch | `H4_Palmar_H5_Pinch.xml` |
| G6 Cylinder Large | `G6_Cylinder_Large.xml` |
| G5 Cylinder | `G5_Cylinder.xml` |
| G4 Cylinder Small | `G4_Cylinder_Small.xml` |
| G1 Wheel | `G1_Wheel.xml` |
| G2 Sphere | `G2_Sphere.xml` |
| G3 Disk | `G3_Disk.xml` |


## Notes

- The launcher writes a **temporary** combined MJCF in this folder while the viewer is running, then removes it. If a run crashes, you may see a leftover `tmp*_pomdar_orca_mocap.xml` file; you can delete it.
- The simulation timestep and actuation are the defaults from the hand and scene fragments; the primary goal of this bundle is **visualization** of the models shipped with the paper, not a full control stack.
