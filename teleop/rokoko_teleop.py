#!/usr/bin/env python3
"""
Rokoko glove teleoperation of the Orca hand (v1b, 17 DOF) in MuJoCo.

Configure Rokoko Studio Custom Streaming to send JSON data to this machine,
then run from any working directory:

  python teleop/rokoko_teleop.py
  python teleop/rokoko_teleop.py --task V1_Wheel
  python teleop/rokoko_teleop.py --hand left
  python teleop/rokoko_teleop.py --help
"""

from __future__ import annotations

import argparse

from rokoko_tracker import RokokoTracker
from webcam_teleop import _SIM_DIR, run_teleop


def main() -> None:
    available = sorted(p.stem for p in (_SIM_DIR / "tasks").glob("*.xml"))

    parser = argparse.ArgumentParser(
        description="Rokoko glove teleoperation of the Orca hand in MuJoCo."
    )
    parser.add_argument(
        "--task",
        default=None,
        help=f"PoMDAR task to load. Available: {', '.join(available)}",
    )
    parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="Print available tasks and exit.",
    )
    parser.add_argument(
        "--ip",
        default="0.0.0.0",
        help="Local IP address on which to receive Rokoko UDP data (default: 0.0.0.0).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=14043,
        help="Local UDP port configured in Rokoko Studio (default: 14043).",
    )
    parser.add_argument(
        "--hand",
        choices=("right", "left"),
        default="right",
        help="Rokoko glove to use (default: right).",
    )
    parser.add_argument(
        "--opt-steps",
        type=int,
        default=2,
        help="Retargeter gradient steps (default: 2).",
    )
    parser.add_argument(
        "--sim-hz",
        type=float,
        default=500.0,
        help="Physics rate in Hz (default: 500).",
    )
    args = parser.parse_args()

    if args.list_tasks:
        print("\n".join(available))
        return

    run_teleop(
        tracker_factory=lambda: RokokoTracker(
            ip=args.ip,
            port=args.port,
            hand=args.hand,
        ),
        task=args.task,
        opt_steps=args.opt_steps,
        sim_hz=args.sim_hz,
    )


if __name__ == "__main__":
    main()
