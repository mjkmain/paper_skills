#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
    echo "Usage:"
    echo "  install_skills.sh --global                    Install to ~/.claude/ (available in all projects)"
    echo "  install_skills.sh --project /path/to/project  Install to /path/to/project/.claude/"
    echo ""
    echo "Examples:"
    echo "  install_skills.sh --global"
    echo "  install_skills.sh --project ~/research/my-project"
}

if [ $# -eq 0 ]; then
    echo "Please select an installation location:"
    echo ""
    usage
    exit 1
fi

case "$1" in
    --global)
        TARGET_DIR="$HOME/.claude"
        ;;
    --project)
        if [ -z "$2" ]; then
            echo "Error: --project requires a path argument."
            echo ""
            usage
            exit 1
        fi
        TARGET_DIR="$2/.claude"
        ;;
    *)
        echo "Error: unknown option '$1'"
        echo ""
        usage
        exit 1
        ;;
esac

mkdir -p "$TARGET_DIR/skills" "$TARGET_DIR/tools"
cp -r "$SCRIPT_DIR/skills/"* "$TARGET_DIR/skills/"
cp -r "$SCRIPT_DIR/tools/"* "$TARGET_DIR/tools/"

echo "Installed skills and tools to $TARGET_DIR/"
