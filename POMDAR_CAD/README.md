# POMDAR CAD Files

STEP files for all physical task fixtures used in the PoMDAR benchmark. Parts are organized by task category. Many components are shared and reused across multiple tasks.

> **PoMDAR v2 is in progress** — a more reliable and stable version of the hardware will be released in **August 2026**.
> Assembly and 3D printing documentation will be released soon.

---

## Assembly & Mounting

**Table attachment:** Use table clamps to secure the mounting plate and placement plate to any lab bench or table edge.

**Mounting plates to fixtures:** Attach fixtures to mounting plates using **M8×20 screws and M8 nuts** (recommended — strongest and most stable option). Alternatively, use the printed `mounting_plate_screw_long.step` / `mounting_plate_screw_short.step` and `mounting_plate_nut.step` parts to avoid relying on hardware screws, though this results in a less rigid and less stable assembly.

---

## Directory Structure

```
POMDAR_CAD/
├── General/        # Shared hardware: plates, holders, threaded connectors
├── Vertical/       # Task fixtures for V1–V3 (vertical manipulation)
├── Horizontal/     # Task fixtures for H1–H5 (horizontal manipulation)
└── Continuous/     # Task fixtures for C1–C4 (continuous rotation)
```

---

## General

Shared components reused across all task categories.

| File | Description |
|------|-------------|
| `mounting_plate_v1.step` | Main mounting plate — attaches to the table via clamps; all task fixtures bolt onto this |
| `place_plate_v1.step` | Flat placement plate for positioning task objects — also attaches to the table via clamps |
| `mounting_plate_vertical_holder.step` | Vertical riser on the mounting plate — used for **G1 (Grasp Wheel)** and **G2 (Grasp Sphere)** tasks |
| `place_plate_vertical_holder.step` | Vertical holder on the placement plate — used for grasping tasks **G1, G2, G3** |
| `mounting_plate_screw_long.step` | Long 3D-printed screw for attaching fixtures to the mounting plate (alternative to M8) |
| `mounting_plate_screw_short.step` | Short 3D-printed screw for attaching fixtures to the mounting plate |
| `mounting_plate_nut.step` | 3D-printed nut paired with the printed screws above |
| `D6C0.5P2.5N2_nut.step` | Universal nut used throughout the benchmark to fasten components — **print several copies**, as with the printed screws |
| `D6d4P2.5N2_thread.step` | Matching thread insert for the D6 nut |
| `D7N3_male_rod.step` | Male threaded rod (Ø7 mm, M3) — structural connector used across categories |
| `D7N3_nut.step` | Nut for the D7N3 rod |
| `D7N3_thread.step` | Thread insert for D7N3 connections |
| `D7N3_tube.step` | Tube spacer for the D7N3 rod system |

---

## Vertical (V1–V3)

Fixtures for tasks involving vertical manipulation: wheel turning (V1), stick insertion (V2), and sphere handling (V3).

| File | Task | Description |
|------|------|-------------|
| `tower_base_v3.step` | V1–V3 | Base tower that anchors all vertical fixtures; attach to mounting plate with M8 screws or 3D-printed long screws |
| `wheel_handle.step` | V1 | Circular wheel handle — task object for **V1 (Vertical Wheel)** |
| `stick_handle.step` | V2 | 7 mm diameter rod — task object for **V2 (Vertical Stick)** |
| `sphere_handle.step` | V3 | Spherical handle — task object for **V3 (Vertical Sphere)** |
| `D7N3_rod.step` | V1–V3 | Rod that connects to the task handles via the vertical connection nut |
| `vertical_connection_nut.step` | V1–V3 | Nut that joins the D7N3 rod to the task handles |
| `D7N3_nut_platform_top.step` | V1–V3 | Top platform with D7N3 interface — mounts flat on the tower |
| `D7N3_nut_platform_15deg.step` | V1–V3 | 15° angled platform — attach to tower with 3D-printed long screws (from General) |
| `D7N3_nut_platform_30deg.step` | V1–V3 | 30° angled platform |
| `D7N3_nut_platform_45deg.step` | V1–V3 | 45° angled platform |
| `D7N3S4_screw.step` | V1–V3 | 3D-printed screw (Ø7 mm, M3, 4 mm shoulder) for vertical fixture fastening |

---

## Horizontal (H1–H5)

Fixtures for tasks performed in the horizontal plane: scissors (H1), chopsticks (H2), syringe squeeze (H3), and palmar/pinch grasping (H4, H5).

All horizontal fixtures attach to the mounting plate with **M8 screws** or **3D-printed short screws**.

### Base Structure

| File | Description |
|------|-------------|
| `horizontal_interface_A.step` | First of two parallel base holders — mounts to the mounting plate |
| `horizontal_interface_B.step` | Second parallel base holder — mounts alongside interface A |
| `hex_rod.step` | Hexagonal rod connecting the two interface holders |

### Scissors Assembly (H1)

| File | Description |
|------|-------------|
| `scissors_sketch.step` | Scissors — task object for **H1** |
| `scissors_bearing_base.step` | Bearing base for the scissors pivot joint |
| `scissors_nut.step` | Nut for the scissors pivot |
| `scissors_traj_rod_lower.STEP` | Lower guide rod constraining scissors motion |
| `scissors_traj_rod_upper.STEP` | Upper guide rod constraining scissors motion |

### Chopsticks Assembly (H2)

> **Note:** Chopsticks are very sensitive to print settings — print both pieces together. Detailed printing documentation coming soon.

| File | Description |
|------|-------------|
| `chopstick.step` | Chopstick pair — task object for **H2**; print both together |
| `chopstick_traj_rod.STEP` | Guide rod constraining chopstick motion |

### Syringe Assembly (H3)

| File | Description |
|------|-------------|
| `syringe_bottom.STEP` | Syringe body housing |
| `syringe_ring_rod.STEP` | Ring rod constraining the syringe plunger |
| `syringe_traj_rod.STEP` | Guide rod for syringe plunger trajectory |
| `syringe_barrier.step` | Stop barrier limiting syringe travel range |

### Palmar / Pinch Grasping (H4, H5)

| File | Description |
|------|-------------|
| `holding_tube.step` | Tube that holds the object — used for both **H4 (Palmar)** and **H5 (Pinch)** |
| `slide_long_rod.step` | Long rod that the holding tube slides along |

---

## Continuous (C1–C4)

Fixtures for continuous rotation tasks: threading (C1), stick rotation (C2), wheel rotation (C3), and fidget spinning (C4).

### Clutch Assembly (C1–C3)

| File | Description |
|------|-------------|
| `clutch_interface.step` | Main clutch body — transmits rotation from hand to object |
| `clutch_interface_shaft.step` | Shaft part of the clutch |
| `clutch_interface_rotor.step` | Rotor part of the clutch — also reused for **G6 (Grasp Cylinder Large)** |
| `D7N3_male_rod.step` | Threaded rod used in the clutch assembly |
| `continuous_rot_base_cylinder.step` | Base cylinder housing the rotation mechanism |
| `continuous_rot_angle_plate.step` | Angle plate for setting the rotation axis — also reused as base for **G3 (Grasp Disk)** |

### Fidget Assembly (C4)

| File | Description |
|------|-------------|
| `fidget_spinner.step` | Fidget spinner — task object for **C4** |
| `fidget_nut.step` | Central nut / bearing seat for the fidget spinner |
| `fidget_base_holder.step` | Holder that mounts the fidget spinner assembly |
| `fidget_support_frame.step` | Support frame for the fidget fixture |
| `m2z15_gear1.step` | Spur gear — module 2, 15 teeth (stage input, gear 1) |
| `m2z15_gear2.step` | Spur gear — module 2, 15 teeth (stage input, gear 2) |
| `m2z27_gear.step` | Spur gear — module 2, 27 teeth (output gear) |

### Screwing Task (C1)

| File | Description |
|------|-------------|
| `screwing_base.step` | Base fixture for the screwing task |
| `D7N10S10_screw.step` | Very long screw (Ø7 mm, M10, 10 mm shoulder) — the object being screwed in |

---

## Grasping Tasks (G1–G6) — Component Reuse

The six grasping tasks do not have dedicated folders — they reuse components from the other categories:

| Task | Reused Components |
|------|-------------------|
| **G1 Grasp Wheel** | `wheel_handle` (Vertical) + `mounting_plate_vertical_holder` + `place_plate_vertical_holder` (General) |
| **G2 Grasp Sphere** | `sphere_handle` (Vertical) + `mounting_plate_vertical_holder` + `place_plate_vertical_holder` (General) |
| **G3 Grasp Disk** | `continuous_rot_angle_plate` as base (Continuous) + `place_plate_vertical_holder` (General) |
| **G4 Grasp Cylinder Small** | `stick_handle` / slim rod (Vertical) |
| **G5 Grasp Cylinder** | Tower assembly (Vertical) |
| **G6 Grasp Cylinder Large** | `clutch_interface_rotor` (Continuous) |
