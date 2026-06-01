# PoMDAR Benchmark

MuJoCo simulation assets for the **Orca hand** and all **18 PoMDAR benchmark tasks**, plus a webcam teleoperation example.

![PoMDAR benchmark overview](benchmark_overview-1.png)

> **PoMDAR v2 is in progress** — an more stable version of the benchmark with improvements is planned for release in **August 2026**.

---

## Contents

```
Multimedia/
├── sim/                        # MuJoCo scene: hand + task objects
│   ├── hand/                   #   Orca hand MJCF models
│   ├── tasks/                  #   17 PoMDAR task fragments
│   ├── assets/                 #   Meshes, textures
│   ├── launch_mujoco_orca.py   #   Passive viewer launcher (no teleop)
│   └── README.md               #   Sim-only instructions
├── teleop/                     # Webcam teleop example (self-contained)
│   ├── webcam_teleop.py        #   Main entry point
│   ├── tracker.py              #   MediaPipe hand tracker
│   ├── retargeter.py           #   Gradient-descent retargeter
│   ├── retarget_utils.py       #   Retargeting utilities
│   ├── orcahand_v1b.urdf       #   Hand kinematics (for retargeter FK)
│   ├── orcahand_v1*.xml        #   Orca hand model variants
│   └── *.yaml                  #   Hand scheme + retargeter configs
├── benchmark_overview-1.png    # Benchmark overview figure
├── requirements.txt            # minimal: mujoco only (viewer)
├── requirements-teleop.txt     # full: adds mediapipe, torch, etc.
├── environment.yml             # conda minimal
├── environment-teleop.yml      # conda full (teleop)
└── README.md                   # This file
```

---

## Requirements

- Python **3.10 or 3.11**
- A webcam (for teleoperation only)
- A display with OpenGL support (required by the MuJoCo viewer)

---

## Installation

### Minimal — passive viewer only

Only `mujoco` is needed to open the hand and tasks in the viewer.

```bash
# conda
conda env create -f environment.yml && conda activate pomdar

# pip
pip install -r requirements.txt
```

### Full — webcam teleoperation

Adds MediaPipe, OpenCV, PyTorch, and the retargeter dependencies.

```bash
# conda
conda env create -f environment-teleop.yml && conda activate pomdar-teleop

# pip
pip install -r requirements-teleop.txt
```

> **GPU note:** PyTorch runs on CPU by default, which is sufficient.  
> For faster retargeting with CUDA, replace the `torch` line in `requirements-teleop.txt` with the wheel from [pytorch.org](https://pytorch.org) for your CUDA version.

---

## Running the passive viewer (no webcam)

Visualise any task with the MuJoCo viewer. Run from the `sim/` directory:

```bash
cd sim/
python launch_mujoco_orca.py --task V1_Wheel
python launch_mujoco_orca.py --list-tasks     # print all task names
```

---

## Webcam teleoperation example

> **Disclaimer:** The webcam teleoperation script is provided as a **proof-of-concept example only**. A standard RGB webcam cannot recover reliable 3D wrist pose or absolute hand depth, and MediaPipe landmark accuracy degrades significantly under occlusion, lighting variation, and fast motion. As a result, finger tracking is approximate and wrist positioning is not available.
>
> For accurate, low-latency teleoperation we recommend:
> - **Apple Vision Pro** — [VisionProTeleop](https://github.com/Improbable-AI/VisionProTeleop) provides full 6-DoF wrist pose and high-quality hand landmarks via ARKit.
> - **Motion capture gloves** — e.g. Rokoko, StretchSense, or similar.

Run from anywhere — all paths are resolved relative to the script:

```bash
# Bare hand (no task object)
python teleop/webcam_teleop.py

# With a task object loaded
python teleop/webcam_teleop.py --task V1_Wheel
python teleop/webcam_teleop.py --task H2_Chopsticks

# All options
python teleop/webcam_teleop.py --help
```

### Moving the hand in the scene

Hold **Ctrl** and **click-drag** the hand in the MuJoCo viewer to reposition it. This moves the mocap anchor that the wrist is welded to.

### Tips

- Show your **right hand** to the camera, palm facing forward.
- The first few seconds may be slower while PyTorch JIT compiles — this is normal.
- Adjust `--opt-steps` (default 2) to trade retargeting quality for speed.
- Close the MuJoCo window to quit.

---

## PoMDAR Tasks

All 17 benchmark tasks. Pass any `ID` to `--task`.

| ID | Full name | Category | Object |
|----|-----------|----------|--------|
| `V1_Wheel` | In-Hand Wheel | V — In-Hand | Steering wheel |
| `V2_Stick` | In-Hand Stick | V — In-Hand | Cylindrical stick |
| `V3_Sphere` | In-Hand Sphere | V — In-Hand | Sphere |
| `C1_Thread` | Constrained Thread | C — Constrained | Threaded bolt |
| `C2_Stick` | Constrained Stick | C — Constrained | Constrained rod |
| `C3_Wheel` | Constrained Wheel | C — Constrained | Wheel on axle |
| `C4_Fidget` | Fidget Spinner | C — Constrained | Fidget spinner |
| `H1_Scissors` | Scissors | H — Human-Tool | Scissors |
| `H2_Chopsticks` | Chopsticks | H — Human-Tool | Chopsticks |
| `H3_Squeeze` | Squeeze | H — Human-Tool | Squeeze toy |
| `H4_Palmar_H5_Pinch` | Palmar / Pinch | H — Human-Tool | Dual-grasp object |
| `G1_Wheel` | Grasp Wheel | G — Grasping | Wheel |
| `G2_Sphere` | Grasp Sphere | G — Grasping | Sphere |
| `G3_Disk` | Grasp Disk | G — Grasping | Flat disk |
| `G4_Cylinder_Small` | Grasp Small Cylinder | G — Grasping | Small cylinder |
| `G5_Cylinder` | Grasp Cylinder | G — Grasping | Medium cylinder |
| `G6_Cylinder_Large` | Grasp Large Cylinder | G — Grasping | Large cylinder |
