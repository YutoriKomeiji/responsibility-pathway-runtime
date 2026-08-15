# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .inspection import inspect_pathway
from .models import PathwayDefinition


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rpr")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="Inspect a responsibility pathway JSON file")
    check.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    # utf-8-sig accepts both plain UTF-8 and UTF-8 files with a BOM, which are
    # commonly produced by Windows tooling such as PowerShell.
    value = json.loads(args.path.read_text(encoding="utf-8-sig"))
    result = inspect_pathway(PathwayDefinition.from_dict(value))
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
