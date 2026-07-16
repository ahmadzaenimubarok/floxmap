#!/usr/bin/env bash
set -euo pipefail

echo "Uninstalling floxmap..."

# Remove symlink
BIN_DIR="${HOME}/.local/bin"
if [ -L "${BIN_DIR}/floxmap" ] || [ -f "${BIN_DIR}/floxmap" ]; then
    rm -f "${BIN_DIR}/floxmap"
    echo "  Removed ${BIN_DIR}/floxmap"
fi

# Remove ~/.floxmap/
INSTALL_DIR="${HOME}/.floxmap"
if [ -d "${INSTALL_DIR}" ]; then
    echo ""
    echo "  WARNING: This will delete all floxmap data:"
    echo "    - config (LLM credentials)"
    echo "    - all project docs (flows, flow-maps, viewers)"
    echo ""
    read -p "  Delete ${INSTALL_DIR}? [y/N]: " confirm
    if [ "${confirm}" = "y" ] || [ "${confirm}" = "Y" ]; then
        rm -rf "${INSTALL_DIR}"
        echo "  Removed ${INSTALL_DIR}"
    else
        echo "  Skipped. ${INSTALL_DIR} preserved."
    fi
fi

echo ""
echo "Done."
