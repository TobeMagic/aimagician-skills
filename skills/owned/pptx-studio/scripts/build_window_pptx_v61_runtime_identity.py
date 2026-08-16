#!/usr/bin/env python3
"""Build the external runtime identity authority for Phase 49 acceptance.

This preparation CLI never discovers Codex through ``PATH``.  Call it from the
Python interpreter that will run the installed acceptance controller, supply
the canonical absolute native Codex binary, freeze the printed manifest SHA,
and pass both the path and SHA to the production controller.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


# The builder itself is normally executed from the already-installed Skill.
# Do not mutate that tree while preparing its external runtime authority.
sys.dont_write_bytecode = True
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from window_pptx.v61_runtime_identity import (  # noqa: E402
    RuntimeIdentityError,
    build_runtime_identity_payload,
    write_runtime_identity_manifest,
)
from validate_window_pptx_v61_clean_pack import tree_fingerprint  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed-skill-root", required=True, type=Path)
    parser.add_argument("--expected-installed-skill-sha256", required=True)
    parser.add_argument("--codex-native-executable", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        installed_root = args.installed_skill_root.expanduser().resolve()
        output_path = args.output.expanduser().resolve(strict=False)
        if output_path == installed_root or output_path.is_relative_to(installed_root):
            raise RuntimeIdentityError("RUNTIME_IDENTITY_MANIFEST_INSIDE_INSTALLED_SKILL")
        installed_fingerprint = tree_fingerprint(installed_root)
        if installed_fingerprint["sha256"] != args.expected_installed_skill_sha256:
            raise RuntimeIdentityError("INSTALLED_SKILL_EXPECTED_DIGEST_MISMATCH")
        payload = build_runtime_identity_payload(
            installed_skill_root=installed_root,
            expected_installed_skill_sha256=args.expected_installed_skill_sha256,
            controller_interpreter=Path(sys.executable).resolve(),
            codex_native_executable=args.codex_native_executable,
        )
        record = write_runtime_identity_manifest(output_path, payload)
        result = {
            "schema_version": "1.0",
            "status": "FROZEN",
            "runtime_identity_manifest": record,
            "expected_runtime_identity_manifest_sha256": record["sha256"],
        }
    except (OSError, ValueError, RuntimeIdentityError) as exc:
        result = {
            "schema_version": "1.0",
            "status": "NOT_WRITTEN",
            "issues": [str(exc)],
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "FROZEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
