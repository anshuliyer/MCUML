#!/usr/bin/env bash
# ==============================================================================
# Script to pull external git dependencies declared in manifest.json into deps/
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
DEPS_DIR="${PROJECT_ROOT}/deps"
TARGET_SDK="${DEPS_DIR}/pico-sdk"
echo "[Manifest] Ensuring dependencies in ${DEPS_DIR}..."
mkdir -p "${DEPS_DIR}"

if [ -d "${TARGET_SDK}" ]; then
    echo "[Manifest] pico-sdk already installed at ${TARGET_SDK}"
elif [ -n "${PICO_SDK_PATH:-}" ] && [ -d "${PICO_SDK_PATH}" ]; then
    echo "[Manifest] Linking existing PICO_SDK_PATH (${PICO_SDK_PATH}) to ${TARGET_SDK}..."
    ln -s "${PICO_SDK_PATH}" "${TARGET_SDK}"
else
    echo "[Manifest] Cloning pico-sdk from https://github.com/raspberrypi/pico-sdk.git..."
    git clone -b 2.1.0 --depth 1 https://github.com/raspberrypi/pico-sdk.git "${TARGET_SDK}"
    echo "[Manifest] Initializing TinyUSB submodule..."
    cd "${TARGET_SDK}"
    git submodule update --init lib/tinyusb
    cd "${SCRIPT_DIR}"
fi

echo "[Manifest] Dependencies ready at: ${TARGET_SDK}"
