#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${HOME}/.floxmap"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing floxmap..."

# Create ~/.floxmap/ structure
mkdir -p "${INSTALL_DIR}/projects"

# Copy flow-schema.yaml if not present
if [ ! -f "${INSTALL_DIR}/flow-schema.yaml" ]; then
    cp "${SCRIPT_DIR}/flow-schema.yaml" "${INSTALL_DIR}/flow-schema.yaml"
    echo "  Copied flow-schema.yaml"
else
    echo "  flow-schema.yaml already exists, skipping"
fi

# Create empty config.yaml if not present
if [ ! -f "${INSTALL_DIR}/config.yaml" ]; then
    cat > "${INSTALL_DIR}/config.yaml" << 'EOF'
llm:
  provider: openrouter
  model: tencent/hy3:free
  api_key: ""
  base_url: https://openrouter.ai/api/v1
EOF
    echo "  Created config.yaml"
else
    echo "  config.yaml already exists, skipping"
fi

# Symlink entry point to /usr/local/bin (or ~/.local/bin)
BIN_DIR="${HOME}/.local/bin"
mkdir -p "${BIN_DIR}"

if [ -L "${BIN_DIR}/floxmap" ] || [ -f "${BIN_DIR}/floxmap" ]; then
    rm -f "${BIN_DIR}/floxmap"
fi

ln -s "${SCRIPT_DIR}/floxmap" "${BIN_DIR}/floxmap"
chmod +x "${SCRIPT_DIR}/floxmap"

echo "  Linked floxmap → ${BIN_DIR}/floxmap"

# Ensure ~/.local/bin is in PATH
if ! echo "${PATH}" | grep -q "${BIN_DIR}"; then
    echo ""
    echo "  NOTE: Add to your shell profile if not already present:"
    echo "    export PATH=\"${BIN_DIR}:\$PATH\""
fi

echo ""
echo "Done. Run 'floxmap --help' to get started."
