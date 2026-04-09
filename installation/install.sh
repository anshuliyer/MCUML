#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/venv"
REQUIREMENTS_FILE="$ROOT_DIR/requirements.txt"
PROJECT_ROOT="$(cd "$ROOT_DIR/.." && pwd)"

print_banner() {
    clear
    echo -e "\033[38;2;255;100;100m============================================\033[0m"
    echo -e "\033[38;2;200;255;100m   \033[38;2;100;255;255mM I X E D S I G N A L I D E   \033[38;2;255;150;100mI N S T A L L\033[0m"
    echo -e "\033[38;2;100;150;255m============================================\033[0m"
    echo
    echo -e "\033[38;2;240;240;240mPreparing your analog SDK environment...\033[0m"
    echo
}

print_stage() {
    local stage="$1"
    local message="$2"
    echo
    echo -e "\033[1;34m[$stage]\033[0m $message"
}

show_circuit_animation() {
    local frames=(
$'      [V] --- R ---+\n                 |\n                 C\n                 |\n                 0\n'
$'      [V] --- R ---+\n                 |\n         *       C\n                 |\n                 0\n'
$'      [V] --- R ---+\n                 |\n        ***      C\n                 |\n                 0\n'
$'      [V] --- R ---+\n                 |\n       *****     C\n                 |\n                 0\n'
$'      [V] --- R ---+\n                 |\n      *******    C\n                 |\n                 0\n'
$'      [V] --- R ---+\n                 |\n     *********   C\n                 |\n                 0\n'
$'      [V] --- R ---+\n                 |\n      *******    C\n                 |\n                 0\n'
    )

    local colors=(
        "255;0;0"
        "255;85;0"
        "255;170;0"
        "255;255;0"
        "0;255;0"
        "0;255;255"
        "0;0;255"
    )

    local labels=(
        "Initializing power rails..."
        "Charging the resistor..."
        "Sweeping the capacitor..."
        "Measuring node current..."
        "Building the analog path..."
        "Finalizing simulation..."
        "Almost ready..."
    )

    for i in "${!frames[@]}"; do
        clear
        print_banner
        local color="${colors[i % ${#colors[@]}]}"
        echo -e "\033[38;2;${color}m${frames[i]}\033[0m"
        echo -e "\033[38;2;255;255;255m${labels[i]}\033[0m"
        sleep 0.15
    done
    clear
    print_banner
}

find_python() {
    if command -v python3 >/dev/null 2>&1; then
        echo "$(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        echo "$(command -v python)"
    else
        echo ""
    fi
}

install_venv() {
    local python_cmd
    python_cmd="$(find_python)"

    if [[ -z "$python_cmd" ]]; then
        echo "Python 3 is required but was not found on PATH."
        exit 1
    fi

    print_stage "STEP 1" "Creating virtual environment with $python_cmd"
    "$python_cmd" -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"

    print_stage "STEP 2" "Upgrading pip, setuptools, and wheel"
    python -m pip install --upgrade pip setuptools wheel

    print_stage "STEP 3" "Installing runtime dependencies"
    python -m pip install -r "$REQUIREMENTS_FILE"

    print_stage "STEP 4" "Installing MixedSignalIDE package in editable mode"
    python -m pip install -e "$PROJECT_ROOT"
}

main() {
    print_banner
    show_circuit_animation
    echo "Starting MixedSignalIDE SDK installation..."
    install_venv
    echo
    echo "Installation complete."
    echo "Activate the environment with: source $VENV_DIR/bin/activate"
    echo "Or run: bash $ROOT_DIR/manage.sh and choose option 2 to enter the environment."
}

main
