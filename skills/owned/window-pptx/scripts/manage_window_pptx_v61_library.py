#!/usr/bin/env python3
"""v6.1 page-template library management commands.

Adds two subcommands to the v6 physical-assembly flow:

- ``compile-pages`` — compiles a ``page-template-library-v4.json`` from the
  certified Gaojie core into ``<private-root>/v61/library-v4.json``.
- ``query-pages`` — deterministic ranked lookup by role, capacity, and
  semantic categories.

The commands never read or write any project or client folder.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from window_pptx.page_template_library import (
    DEFAULT_DOMINANT_STYLE_CLUSTER,
    LibraryIndex,
    compile_page_templates,
    compile_reference_deck,
    load_library_index,
    query_page_templates,
    resolve_private_root,
    write_library_index,
    _template_reuse_risk,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["compile-pages", "compile-reference", "query-pages"]
    )
    parser.add_argument("--deck")
    parser.add_argument("--private-root")
    parser.add_argument("--library")
    parser.add_argument("--output")
    parser.add_argument("--role")
    parser.add_argument("--capacity-budget", type=int, default=1000)
    parser.add_argument("--semantic-category", action="append", default=[])
    # An omitted cluster follows the compiled library's dominant cluster.  This
    # matters for reference-family libraries whose cluster is intentionally not
    # the Gaojie default.
    parser.add_argument("--style-cluster")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--allow-fallback", action="store_true")
    return parser


def _run_compile_pages(args: argparse.Namespace) -> dict[str, Any]:
    root = resolve_private_root(explicit=args.private_root)
    index = compile_page_templates(root)
    if args.output:
        out = Path(args.output).expanduser().resolve(strict=False)
    else:
        out = root / "v61" / "library-v4.json"
    sha = write_library_index(index, out)
    return {
        "schema_version": index.schema_version,
        "library_id": index.library_id,
        "page_template_count": index.page_template_count,
        "private_root_sha256": index.private_root_sha256,
        "library_index_sha256": sha,
        "output_path": str(out),
        "role_index": dict(index.role_index),
        "style_cluster_index": dict(index.style_cluster_index),
    }


def _run_query_pages(args: argparse.Namespace) -> dict[str, Any]:
    library_path = Path(args.library).expanduser().resolve(strict=False)
    if not library_path.is_file():
        raise SystemExit(f"library missing: {library_path}")
    index: LibraryIndex = load_library_index(library_path)
    if not args.role:
        raise SystemExit("--role is required for query-pages")
    style_cluster = args.style_cluster or index.dominant_style_cluster_id
    candidates = query_page_templates(
        index,
        role=args.role,
        capacity_budget=args.capacity_budget,
        semantic_categories=tuple(args.semantic_category or ()),
        style_cluster=style_cluster,
        limit=args.limit,
        allow_fallback=args.allow_fallback,
    )
    return {
        "library_index_sha256": __import__("hashlib").sha256(
            library_path.read_bytes()
        ).hexdigest(),
        "role": args.role,
        "style_cluster": style_cluster,
        "count": len(candidates),
        "candidates": [
            {
                "page_id": t.page_id,
                "package_sha256": t.package_sha256,
                "slide_number": t.slide_number,
                "page_role": t.page_role,
                "category_names": list(t.category_names),
                "style_cluster_id": t.style_cluster_id,
                "deck_family_id": t.deck_family_id,
                "theme_palette": list(t.theme_palette),
                "source_sha256": t.source_sha256,
                "editability": t.editability,
                "reuse_risk": round(_template_reuse_risk(t), 4),
                "slot_graph": dict(t.slot_graph),
            }
            for t in candidates
        ],
    }


def _run_compile_reference(args: argparse.Namespace) -> dict[str, Any]:
    if not args.deck:
        raise SystemExit("--deck is required for compile-reference")
    index = compile_reference_deck(args.deck)
    if args.output:
        out = Path(args.output).expanduser().resolve(strict=False)
    else:
        raise SystemExit("--output is required for compile-reference")
    sha = write_library_index(index, out)
    return {
        "schema_version": index.schema_version,
        "library_id": index.library_id,
        "page_template_count": index.page_template_count,
        "private_root_sha256": index.private_root_sha256,
        "library_index_sha256": sha,
        "output_path": str(out),
        "style_cluster_index": dict(index.style_cluster_index),
    }


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parser().parse_args(argv)
    if args.command == "compile-pages":
        return _run_compile_pages(args)
    if args.command == "compile-reference":
        return _run_compile_reference(args)
    if args.command == "query-pages":
        return _run_query_pages(args)
    raise SystemExit(f"unknown command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    print(json.dumps(run(argv), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
