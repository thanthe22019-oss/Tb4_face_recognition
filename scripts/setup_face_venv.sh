#!/usr/bin/env bash
set -eo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv-face"

source /opt/ros/humble/setup.bash

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  /usr/bin/python3 -m venv --without-pip --system-site-packages "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" -m pip --version >/dev/null 2>&1; then
  GET_PIP_FILE="$(mktemp /tmp/tbe4_get_pip.XXXXXX.py)"
  curl -fsSL https://bootstrap.pypa.io/get-pip.py -o "$GET_PIP_FILE"
  "$VENV_DIR/bin/python" "$GET_PIP_FILE"
  rm -f "$GET_PIP_FILE"
fi

"$VENV_DIR/bin/python" -m pip install -r "$PROJECT_DIR/requirements-face.txt"
"$VENV_DIR/bin/python" -m pip install --no-deps fer==25.10.3

"$VENV_DIR/bin/python" - <<'PY'
import cv2
from fer.fer import FER
import numpy
import rclpy
import tensorflow as tf

detector = FER(use_tflite=True, mtcnn=False)
print('Face environment ready')
print('NumPy:', numpy.__version__)
print('OpenCV:', cv2.__version__)
print('TensorFlow:', tf.__version__)
print('FER detector:', type(detector).__name__)
print('rclpy:', rclpy.__file__)
PY
