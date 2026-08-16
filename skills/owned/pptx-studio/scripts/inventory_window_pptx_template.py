#!/usr/bin/env python3
"""Emit a read-only, source-hash-bound TemplatePack geometry inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from window_pptx.template_geometry import build_template_geometry_inventory
from window_pptx.template_pack import load_template_pack


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-pack", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    inventory = build_template_geometry_inventory(
        load_template_pack(args.template_pack)
    ).to_dict()
    payload = json.dumps(inventory, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
