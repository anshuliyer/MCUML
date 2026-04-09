#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/venv"
INSTALL_SCRIPT="$ROOT_DIR/install.sh"

print_header() {
    clear
    cat <<'EOF'
===============================================
         MixedSignalIDE SDK Manager
===============================================
EOF
}

print_menu() {
    print_header
    cat <<'EOF'
1) Install or update the SDK
2) Enter the MixedSignalIDE virtual environment
3) Show environment status
4) Exit
EOF
}

show_status() {
    echo "Installation root: $ROOT_DIR"
    if [[ -d "$VENV_DIR" ]]; then
        echo "Virtual environment: present"
        echo "Activate with: source $VENV_DIR/bin/activate"
    else
        echo "Virtual environment: not found"
    fi
}

enter_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        echo "Virtual environment not found. Run option 1 first."
        return 1
    fi

    echo "Entering MixedSignalIDE virtual environment..."
    source "$VENV_DIR/bin/activate"
    exec "$SHELL"
}

main() {
    while true; do
        print_menu
        read -rp $'Enter choice (1-4): ' choice
        case "$choice" in
            1)
                bash "$INSTALL_SCRIPT"
                ;;
            2)
                enter_venv
                ;;
            3)
                show_status
                ;;
            4)
                echo "Goodbye."
                exit 0
                ;;
            *)
                echo "Invalid option. Please choose 1-4."
                ;;
        esac
    done
}

main
