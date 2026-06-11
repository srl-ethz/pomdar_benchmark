# POMDAR CAD Files

STEP files for all physical task fixtures used in the PoMDAR benchmark. Parts are organized by task category. Many components are shared and reused across multiple tasks.

See [BOM.md](BOM.md) for the full Bill of Materials with part numbers and quantities.

> **PoMDAR v2 is in progress** — a more reliable and stable version of the hardware will be released in **August 2026**.
> Assembly and 3D printing documentation will be released soon.

---

## Assembly & Mounting

**Table attachment:** Use table clamps to secure the mounting plate and placement plate to any lab bench or table edge.

**Mounting plates to fixtures:** Attach fixtures to mounting plates using **M8×20 screws and M8 nuts** (recommended — strongest and most stable option). Alternatively, use the printed `005_mounting_plate_screw_long` / `006_mounting_plate_screw_short` and `007_mounting_plate_nut` parts to avoid relying on hardware screws, though this results in a less rigid and less stable assembly.

---

## Directory Structure

```
cad/
├── General/        # Shared hardware: plates, holders, threaded connectors
├── Vertical/       # Task fixtures for V1–V3 (vertical manipulation)
├── Horizontal/     # Task fixtures for H1–H5 (horizontal manipulation)
├── Continuous/     # Task fixtures for C1–C4 (continuous rotation)
├── BOM.md          # Bill of Materials with part numbers and quantities
└── README.md       # This file
```

---

## General

Shared components reused across all task categories.

| # | File | Description |
|---|------|-------------|
| 001 | `001_mounting_plate.step` | Main mounting plate — attaches to the table via clamps; all task fixtures bolt onto this |
| 002 | `002_place_plate.step` | Flat placement plate for positioning task objects — also attaches to the table via clamps |
| 003 | `003_mounting_plate_vertical_holder.step` | Vertical riser on the mounting plate — used for **G1 (Grasp Wheel)** and **G2 (Grasp Sphere)** tasks |
| 004 | `004_place_plate_vertical_holder.step` | Vertical holder on the placement plate — used for grasping tasks **G1, G2, G3** |
| 005 | `005_mounting_plate_screw_long.step` | Long 3D-printed screw for attaching fixtures to the mounting plate (alternative to M8) |
| 006 | `006_mounting_plate_screw_short.step` | Short 3D-printed screw for attaching fixtures to the mounting plate |
| 007 | `007_mounting_plate_nut.step` | 3D-printed nut paired with the printed screws above |
| 008 | `008_D6_nut.step` | Universal nut used throughout the benchmark to fasten components — **print many copies** |

---

## Vertical (V1–V3)

Fixtures for tasks involving vertical manipulation: wheel turning (V1), stick insertion (V2), and sphere handling (V3).

| # | File | Task | Description |
|---|------|------|-------------|
| 009 | `009_tower_base.step` | V1–V3 | Base tower that anchors all vertical fixtures; attach to mounting plate with M8 screws or printed long screws (005) |
| 010 | `010_wheel_handle.step` | V1 | Circular wheel handle — task object for **V1 (Vertical Wheel)** |
| 011 | `011_stick_handle.step` | V2 | 7 mm diameter rod — task object for **V2 (Vertical Stick)** |
| 012 | `012_sphere_handle.step` | V3 | Spherical handle — task object for **V3 (Vertical Sphere)** |
| 013 | `013_D7N3_rod.step` | V1–V3 | Rod that connects to the task handles via the vertical connection nut (014) |
| 014 | `014_vertical_connection_nut.step` | V1–V3 | Nut that joins the rod (013) to the task handles |
| 015 | `015_nut_platform_top.step` | V1–V3 | Top platform (0°) — mounts flat on the tower |
| 016 | `016_nut_platform_15deg.step` | V1–V3 | 15° angled platform — attach to tower with printed long screws (005) |
| 017 | `017_nut_platform_30deg.step` | V1–V3 | 30° angled platform |
| 018 | `018_nut_platform_45deg.step` | V1–V3 | 45° angled platform |
| 019 | `019_D7N3S4_screw.step` | V1–V3 | 3D-printed screw (Ø7 mm, M3, 4 mm shoulder) for vertical fixture fastening |

---

## Horizontal (H1–H5)

Fixtures for tasks performed in the horizontal plane: scissors (H1), chopsticks (H2), syringe squeeze (H3), and palmar/pinch grasping (H4, H5).

All horizontal fixtures attach to the mounting plate with **M8 screws** or **printed short screws (006)**.

### Base Structure

| # | File | Description |
|---|------|-------------|
| 020 | `020_horizontal_interface_A.step` | First of two parallel base holders — mounts to the mounting plate |
| 021 | `021_horizontal_interface_B.step` | Second parallel base holder — mounts alongside 020 |
| 022 | `022_hex_rod.step` | Hexagonal rod connecting the two interface holders |

### Scissors Assembly (H1)

| # | File | Description |
|---|------|-------------|
| 023 | `023_scissors.step` | Scissors — task object for **H1** |
| 024 | `024_scissors_bearing_base.step` | Bearing base for the scissors pivot joint |
| 025 | `025_scissors_nut.step` | Nut for the scissors pivot |
| 026 | `026_scissors_traj_rod_lower.STEP` | Lower guide rod constraining scissors motion |
| 027 | `027_scissors_traj_rod_upper.STEP` | Upper guide rod constraining scissors motion |

### Chopsticks Assembly (H2)

> **Note:** Chopsticks are very sensitive to print settings — print both pieces together. Detailed printing documentation coming soon.

| # | File | Description |
|---|------|-------------|
| 028 | `028_chopstick.step` | Chopstick pair — task object for **H2**; print both together |
| 029 | `029_chopstick_traj_rod.STEP` | Guide rod constraining chopstick motion |

### Syringe Assembly (H3)

| # | File | Description |
|---|------|-------------|
| 030 | `030_syringe_bottom.STEP` | Syringe body housing |
| 031 | `031_syringe_ring_rod.STEP` | Ring rod constraining the syringe plunger |
| 032 | `032_syringe_traj_rod.STEP` | Guide rod for syringe plunger trajectory |
| 033 | `033_syringe_barrier.step` | Stop barrier limiting syringe travel range |

### Palmar / Pinch Grasping (H4, H5)

| # | File | Description |
|---|------|-------------|
| 034 | `034_holding_tube.step` | Tube holding the object — used for both **H4 (Palmar)** and **H5 (Pinch)** |
| 035 | `035_slide_long_rod.step` | Long rod that the holding tube slides along |

---

## Continuous (C1–C4)

Fixtures for continuous rotation tasks: threading (C1), stick rotation (C2), wheel rotation (C3), and fidget spinning (C4).

### Clutch Assembly (C1–C3)

| # | File | Description |
|---|------|-------------|
| 036 | `036_D7N3_male_rod.step` | Male threaded rod (Ø7 mm, M3) — used in clutch assembly |
| 037 | `037_clutch_interface_shaft.step` | Shaft of the clutch |
| 038 | `038_clutch_interface_rotor.step` | Rotor of the clutch — also reused for **G6 (Grasp Cylinder Large)** |
| 039 | `039_continuous_rot_base_cylinder.step` | Base cylinder housing the rotation mechanism |
| 040 | `040_continuous_rot_angle_plate.step` | Angle plate for setting the rotation axis — also reused as base for **G3 (Grasp Disk)** |

### Fidget Assembly (C4)

| # | File | Description |
|---|------|-------------|
| 041 | `041_fidget_spinner.step` | Fidget spinner — task object for **C4** |
| 042 | `042_fidget_nut.step` | Central bearing nut for the fidget spinner |
| 043 | `043_fidget_base_holder.step` | Holder that mounts the fidget spinner assembly |
| 044 | `044_fidget_support_frame.step` | Support frame for the fidget fixture |
| 045 | `045_m2z15_gear1.step` | Spur gear — module 2, 15 teeth (stage input, gear 1) |
| 046 | `046_m2z15_gear2.step` | Spur gear — module 2, 15 teeth (stage input, gear 2) |
| 047 | `047_m2z27_gear.step` | Spur gear — module 2, 27 teeth (output gear) |

### Screwing Task (C1)

| # | File | Description |
|---|------|-------------|
| 048 | `048_screwing_base.step` | Base fixture for the screwing task |
| 049 | `049_D7N10S10_screw.step` | Very long screw (Ø7 mm, M10, 10 mm shoulder) — the object being screwed |

---

## Grasping Tasks (G1–G6) — Component Reuse

The six grasping tasks do not have dedicated folders — they reuse components from the other categories:

| Task | Reused Components |
|------|-------------------|
| **G1 Grasp Wheel** | 010 `wheel_handle` + 003 `mounting_plate_vertical_holder` + 004 `place_plate_vertical_holder` |
| **G2 Grasp Sphere** | 012 `sphere_handle` + 003 `mounting_plate_vertical_holder` + 004 `place_plate_vertical_holder` |
| **G3 Grasp Disk** | 040 `continuous_rot_angle_plate` as base + 004 `place_plate_vertical_holder` |
| **G4 Grasp Cylinder Small** | 011 `stick_handle` / slim rod (Vertical) |
| **G5 Grasp Cylinder** | Tower assembly (Vertical) |
| **G6 Grasp Cylinder Large** | 038 `clutch_interface_rotor` (Continuous) |
