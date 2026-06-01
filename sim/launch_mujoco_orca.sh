#!/usr/bin/env bash
# MuJoCo viewer: PoMDAR Orca hand + one task. Requires: pip install mujoco
set -euo pipefail
cd "$(dirname "$0")"
exec python3 launch_mujoco_orca.py "$@"
