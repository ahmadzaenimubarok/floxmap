#!/usr/bin/env bash
set -euo pipefail

echo "Uninstalling floxmap..."
echo ""

# 1. Remove symlink
BIN_DIR="${HOME}/.local/bin"
if [ -L "${BIN_DIR}/floxmap" ] || [ -f "${BIN_DIR}/floxmap" ]; then
    rm -f "${BIN_DIR}/floxmap"
    echo "  Removed ${BIN_DIR}/floxmap"
fi

INSTALL_DIR="${HOME}/.floxmap"

# 2. Project data
if [ -d "${INSTALL_DIR}/projects" ]; then
    PROJECTS=$(ls -1 "${INSTALL_DIR}/projects" 2>/dev/null || true)
    if [ -n "${PROJECTS}" ]; then echo ""
        echo "  Registered projects:"
        while IFS= read -r proj; do
            flow_count=$(ls -1 "${INSTALL_DIR}/projects/${proj}/flows/"*.flow.yaml 2>/dev/null | wc -l)
            echo "    - ${proj} (${flow_count} flow(s))"
        done <<< "${PROJECTS}"
        echo ""
        read -p "  Delete all project data? [y/N]: " confirm_proj
        if [ "${confirm_proj}" = "y" ] || [ "${confirm_proj}" = "Y" ]; then
            rm -rf "${INSTALL_DIR}/projects"
            echo "  Removed project data"
        else
            echo "  Project data preserved."
        fi
    fi
fi

# 3. Config
if [ -f "${INSTALL_DIR}/config.yaml" ]; then
    echo ""
    read -p "  Delete config (LLM credentials)? [y/N]: " confirm_cfg
    if [ "${confirm_cfg}" = "y" ] || [ "${confirm_cfg}" = "Y" ]; then
        rm -f "${INSTALL_DIR}/config.yaml"
        echo "  Removed config.yaml"
    else
        echo "  Config preserved."
    fi
fi

# 4. Clean up empty ~/.floxmap/
if [ -d "${INSTALL_DIR}" ]; then
    if [ -z "$(ls -A "${INSTALL_DIR}" 2>/dev/null)" ]; then
        rmdir "${INSTALL_DIR}"
        echo "  Removed empty ${INSTALL_DIR}"
    fi
fi

echo ""
echo "Done."
