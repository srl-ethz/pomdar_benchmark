# Bill of Materials — PoMDAR Benchmark

All quantities refer to the complete benchmark assembly.
Parts marked with * are 3D-printed. Items in the **Hardware** section are off-the-shelf and must be purchased separately.

---

## Hardware

| # | Item | Description | Qty |
|---|------|-------------|-----|
| H1 | Table clamps | Standard lab clamps to secure mounting plate and placement plate to the table | 2 |
| H2 | M8×16 screw | Hex socket cap screw M8×16 — for attaching fixtures to mounting plates | 10 |
| H3 | M8 nut | Standard M8 hex nut | 10 |

> **Note:** Files `D6d4P2.5N2_thread`, `D7N3_nut`, `D7N3_thread`, `D7N3_tube` (General) and `clutch_interface` (Continuous) are referenced in the README but not currently present on disk — check if they are needed for your assembly.

---

## General

| # | File | Description | Qty |
|---|------|-------------|-----|
| 001 | `001_mounting_plate.step` | Main mounting plate — clamp to table | 1 |
| 002 | `002_place_plate.step` | Placement plate for task objects — clamp to table | 1 |
| 003 | `003_mounting_plate_vertical_holder.step` | Vertical riser on mounting plate (G1, G2) | 1 |
| 004 | `004_place_plate_vertical_holder.step` | Vertical holder on placement plate (G1, G2, G3) | 1 |
| 005 | `005_mounting_plate_screw_long.step` | Long 3D-printed screw for plate attachment * | (10) |
| 006 | `006_mounting_plate_screw_short.step` | Short 3D-printed screw for plate attachment * | (10) |
| 007 | `007_mounting_plate_nut.step` | 3D-printed nut for plate screws + fix the fidget task | 10 |
| 008 | `008_D6_nut.step` | Universal benchmark nut — used throughout to fix the curvy rods of the horizontal tasks | 8 |

---

## Vertical (V1–V3)

| # | File | Description | Qty |
|---|------|-------------|-----|
| 009 | `009_tower_base.step` | Base tower for all vertical fixtures; attach to plate with M8 or printed screws | 1 |
| 010 | `010_wheel_handle.step` | Circular wheel handle — task object V1 (Wheel) | 1 |
| 011 | `011_stick_handle.step` | Stick handle (7 mm rod) — task object V2 (Stick) | 1 |
| 012 | `012_sphere_handle.step` | Sphere handle — task object V3 (Sphere) | 1 |
| 013 | `013_D7N3_rod.step` | Rod connecting handles to platforms via item 014 | 1 |
| 014 | `014_vertical_connection_nut.step` | Nut joining item 013 rod to task handles | 1 |
| 015 | `015_nut_platform_top.step` | Top platform (0°) — mounts on tower | 1 |
| 016 | `016_nut_platform_15deg.step` | 15° angled platform — attach with printed long screws (005) | 2 |
| 017 | `017_nut_platform_30deg.step` | 30° angled platform | 2 |
| 018 | `018_nut_platform_45deg.step` | 45° angled platform | 2 |
| 019 | `019_D7N3S4_screw.step` | 3D-printed screw for vertical fixture fastening * | 6 |

---

## Horizontal (H1–H5)

| # | File | Description | Qty |
|---|------|-------------|-----|
| 020 | `020_horizontal_interface_A.step` | First parallel base holder — mounts to mounting plate | 1 |
| 021 | `021_horizontal_interface_B.step` | Second parallel base holder — mounts alongside 020 | 1 |
| 022 | `022_hex_rod.step` | Hexagonal rod connecting the two interface holders | 1 |
| 023 | `023_scissors.step` | Scissors — task object H1 | 1 |
| 024 | `024_scissors_bearing_base.step` | Bearing base for scissors pivot | 1 |
| 025 | `025_scissors_nut.step` | Nut for scissors pivot | 1 |
| 026 | `026_scissors_traj_rod_lower.STEP` | Lower guide rod for scissors trajectory | 1 |
| 027 | `027_scissors_traj_rod_upper.STEP` | Upper guide rod for scissors trajectory | 1 |
| 028 | `028_chopstick.step` | Chopstick pair — task object H2; **print both together** * | 1 |
| 029 | `029_chopstick_traj_rod.STEP` | Guide rod for chopstick trajectory | 1 |
| 030 | `030_syringe_bottom.STEP` | Syringe body housing — task object H3 | 1 |
| 031 | `031_syringe_ring_rod.STEP` | Ring rod constraining syringe plunger | 1 |
| 032 | `032_syringe_traj_rod.STEP` | Guide rod for syringe plunger | 1 |
| 033 | `033_syringe_barrier.step` | Stop barrier limiting syringe travel | 1 |
| 034 | `034_holding_tube.step` | Object holding tube — used for H4 (Palmar) and H5 (Pinch) | 1 |
| 035 | `035_slide_long_rod.step` | Long rod that item 034 slides along | 1 |

---

## Continuous (C1–C4)

| # | File | Description | Qty |
|---|------|-------------|-----|
| 036 | `036_D7N3_male_rod.step` | Male threaded rod (Ø7 mm, M3) — used in clutch assembly | 1 |
| 037 | `037_clutch_interface_shaft.step` | Shaft of the clutch | 1 |
| 038 | `038_clutch_interface_rotor.step` | Rotor of the clutch — also reused for G6 (Grasp Cylinder Large) | 1 |
| 039 | `039_continuous_rot_base_cylinder.step` | Base cylinder housing the rotation mechanism | 1 |
| 040 | `040_continuous_rot_angle_plate.step` | Angle plate for rotation axis — also reused as base for G3 (Grasp Disk) | 1 |
| 041 | `041_fidget_spinner.step` | Fidget spinner — task object C4 | 1 |
| 042 | `042_fidget_nut.step` | Central bearing nut for fidget spinner | 1 |
| 043 | `043_fidget_base_holder.step` | Holder mounting the fidget assembly | 1 |
| 044 | `044_fidget_support_frame.step` | Support frame for fidget fixture | 1 |
| 045 | `045_m2z15_gear1.step` | Spur gear M2 Z15 — stage input gear 1 | 1 |
| 046 | `046_m2z15_gear2.step` | Spur gear M2 Z15 — stage input gear 2 | 1 |
| 047 | `047_m2z27_gear.step` | Spur gear M2 Z27 — output gear | 1 |
| 048 | `048_screwing_base.step` | Base fixture for the screwing task (C1) | 1 |
| 049 | `049_D7N10S10_screw.step` | Very long screw — object being screwed in task C1 | 1 |
