#!/usr/bin/env python3
"""Run the Window-PPTX trusted TemplatePack golden replay."""

from __future__ import annotations

import argparse
from pathlib import Path

from window_pptx.golden_template_replay import run_golden_template_replay
from window_pptx.libreoffice import LibreOfficeVerifier


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-pack", required=True)
    parser.add_argument("--bindings", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--dpi", type=int, default=144)
    args = parser.parse_args()
    result = run_golden_template_replay(
        args.template_pack,
        args.bindings,
        args.output_dir,
        verifier=LibreOfficeVerifier(dpi=args.dpi),
    )
    print(result.manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
