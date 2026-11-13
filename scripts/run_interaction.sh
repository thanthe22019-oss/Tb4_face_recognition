#!/usr/bin/env bash
set -eo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv-face/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Chạy ./scripts/setup_face_venv.sh trước." >&2
  exit 2
fi
if [[ ! -f "$PROJECT_DIR/install/setup.bash" ]]; then
  echo "Chạy ./scripts/build.sh trước." >&2
  exit 2
fi

source /opt/ros/humble/setup.bash
source "$PROJECT_DIR/install/setup.bash"
exec ros2 launch tbe4_face_recognition interaction.launch.py \
  python_executable:="$VENV_PYTHON" "$@"
