#!/usr/bin/env bash
# ========================================================================
# SHAE COBOL Bank Account Manager — install.sh
# Copyright (c) 2026 spdedsec <legendsatya7272@gmail.com>
# License: MIT
#
# Installs shae-bank as a CLI command via a symlink in ~/.local/bin.
# ========================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${SCRIPT_DIR}/src/main.py"
BIN_DIR="${HOME}/.local/bin"
TARGET="${BIN_DIR}/shae-bank"

echo "==> SHAE COBOL Bank Account Manager installer"
echo "    Source : ${SRC}"
echo "    Target : ${TARGET}"
echo

if [ ! -f "${SRC}" ]; then
  echo "ERROR: source file not found: ${SRC}" >&2
  exit 1
fi

# Ensure bin dir exists
if [ ! -d "${BIN_DIR}" ]; then
  echo "==> Creating ${BIN_DIR}"
  mkdir -p "${BIN_DIR}"
fi

# Remove old link if present
if [ -L "${TARGET}" ] || [ -e "${TARGET}" ]; then
  echo "==> Removing existing target"
  rm -f "${TARGET}"
fi

# Create wrapper script so Python shebang is respected
cat > "${TARGET}" <<EOF
#!/usr/bin/env python3
import runpy
runpy.run_path("${SRC}", run_name="__main__")
EOF
chmod +x "${TARGET}"

echo "==> Installed."
echo
echo "Run it with:"
echo "  shae-bank"
echo
echo "If ~/.local/bin is not on your PATH, add this to your shell profile:"
echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""