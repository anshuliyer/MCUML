#!/usr/bin/env bash
# ==============================================================================
# Helper to fetch all dependencies into deps/ from project root
# Handles Debian/Raspberry Pi OS PEP 668 externally-managed environments
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "==> Pulling Pico SDK and TinyUSB dependencies..."
bash "${PROJECT_ROOT}/model/firmware/drivers/usb/pull_dependencies.sh"

echo "==> Installing Python requirements..."
REQ_FILE="${PROJECT_ROOT}/tools/requirements.txt"

# 1. Try standard pip install (e.g. macOS or active virtual environment)
if pip3 install -r "${REQ_FILE}" 2>/dev/null; then
    echo "==> Python requirements installed successfully."
# 2. Try with --break-system-packages (for Debian 12 / Raspberry Pi OS Bookworm)
elif pip3 install --user --break-system-packages -r "${REQ_FILE}" 2>/dev/null; then
    echo "==> Python requirements installed successfully (user / break-system-packages)."
elif pip3 install --break-system-packages -r "${REQ_FILE}" 2>/dev/null; then
    echo "==> Python requirements installed successfully (break-system-packages)."
# 3. Fallback: create local virtualenv in repo
else
    echo "==> Setting up local Python virtual environment at .venv..."
    python3 -m venv "${PROJECT_ROOT}/.venv"
    "${PROJECT_ROOT}/.venv/bin/pip" install --upgrade pip
    "${PROJECT_ROOT}/.venv/bin/pip" install -r "${REQ_FILE}"
    echo "==> Python requirements installed in ${PROJECT_ROOT}/.venv."
    echo "    To activate: source .venv/bin/activate"
fi

echo "==> All dependencies are up to date."
