#!/usr/bin/env bash
# ==============================================================================
# Helper to fetch all dependencies into deps/ from project root
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "==> Pulling Pico SDK and TinyUSB dependencies..."
bash "${PROJECT_ROOT}/model/firmware/drivers/usb/pull_dependencies.sh"

echo "==> Installing Python requirements..."
pip3 install -r "${PROJECT_ROOT}/tools/requirements.txt"

echo "==> All dependencies are up to date."
