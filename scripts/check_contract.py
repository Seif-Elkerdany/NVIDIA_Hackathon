"""Read-only deterministic contract gate; run with uv run --frozen --offline python."""

import argparse
import sys
from pathlib import Path

from export_openapi import generated_files

ROOT = Path(__file__).resolve().parents[1]


def check_contract(output_dir: Path) -> tuple[str, ...]:
    first = generated_files()
    if first != generated_files():
        return ("non-deterministic OpenAPI/client generation",)
    return tuple(
        name
        for name, content in first.items()
        if not (output_dir / name).is_file()
        or (output_dir / name).read_bytes() != content.encode("utf-8")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "frontend/src/generated")
    args = parser.parse_args()
    drift = check_contract(args.output_dir)
    if drift:
        print("Contract gate failed: " + ", ".join(drift), file=sys.stderr)
        return 1
    print("Contract gate passed: deterministic OpenAPI and client match the merged implementation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
