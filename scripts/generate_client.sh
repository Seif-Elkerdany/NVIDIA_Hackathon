#!/usr/bin/env bash
# Use the same exporter for both artifacts; never combine generated types by hand.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$script_dir/.."
uv run --frozen --offline python scripts/export_openapi.py "$@"
