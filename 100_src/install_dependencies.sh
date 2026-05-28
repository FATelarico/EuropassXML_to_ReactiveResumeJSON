#!/usr/bin/env bash
set -euo pipefail

INSTALL_TARGET="."

usage() {
    cat <<EOF
Usage: bash ./100_src/install_dependencies.sh [--gui] [--dev]

Options:
  --gui    Install CLI + GUI dependencies
  --dev    Install CLI + GUI + development dependencies
  -h, --help
          Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --gui)
            INSTALL_TARGET=".[gui]"
            shift
            ;;
        --dev)
            INSTALL_TARGET=".[gui,dev]"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e "$INSTALL_TARGET"
