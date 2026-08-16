#!/usr/bin/env python3
"""v6.1 page-template library management commands.

Adds the catalog and retrieval commands used by the v6.1 physical-assembly
flow:

- ``compile-pages`` — compiles a ``page-template-library-v4.json`` from the
  certified Gaojie core into ``<private-root>/v61/library-v4.json``.
- ``query-pages`` — deterministic ranked lookup by role, capacity, and
  semantic categories.
- ``query-bundle`` — run a locked multi-slide query request and persist one
  public, source-redacted evidence bundle for the client project.

Compilation never writes a project or client folder. Query-bundle writes only
the public result path explicitly supplied by the caller; private source paths
and literal source copy are redacted before serialization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from window_pptx.page_template_library import (
    DEFAULT_SCORING,
    LibraryIndex,
    compile_page_templates,
    compile_reference_deck,
    load_library_index,
    query_page_template_candidates,
    resolve_private_root,
    write_library_index,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "compile-pages",
            "compile-reference",
            "query-pages",
            "query-bundle",
        ],
    )
    parser.add_argument("--deck")
    parser.add_argument("--private-root")
    parser.add_argument("--library")
    parser.add_argument("--query-request")
    parser.add_argument("--output")
    parser.add_argument("--role")
    parser.add_argument(
        "--required-source-ordinal",
        type=int,
        help="hard-filter candidates to this positive source slide number",
    )
    parser.add_argument(
        "--capacity-budget",
        type=int,
        default=0,
        help="required text capacity; 0 means no capacity requirement",
    )
    parser.add_argument("--semantic-category", action="append", default=[])
    parser.add_argument("--asset-requirement", action="append", default=[])
    parser.add_argument("--customer-assets-available", action="store_true")
    # An omitted cluster follows the compiled library's dominant cluster.  This
    # matters for reference-family libraries whose cluster is intentionally not
    # the Gaojie default.
    parser.add_argument("--style-cluster")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--allow-fallback", action="store_true")
    parser.add_argument("--include-ineligible", action="store_true")
    return parser


def _run_compile_pages(args: argparse.Namespace) -> dict[str, Any]:
    root = resolve_private_root(explicit=args.private_root)
    index = compile_page_templates(root)
    out = _resolve_private_output(
        root,
        args.output,
        default_relative="v61/library-v4.json",
    )
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


def _resolve_library_path(args: argparse.Namespace) -> tuple[Path, str]:
    if not args.library:
        raise SystemExit("--library is required")
    requested = Path(args.library).expanduser()
    if requested.is_absolute():
        library_path = requested.resolve(strict=False)
        resolution_source = "absolute-library"
    else:
        private_root = resolve_private_root(explicit=args.private_root)
        library_path = (private_root / requested).resolve(strict=False)
        if not library_path.is_relative_to(private_root):
            raise SystemExit("relative --library escapes the configured private root")
        if args.private_root:
            resolution_source = "explicit-private-root"
        elif os.environ.get("WINDOW_PPTX_PRIVATE_ROOT"):
            resolution_source = "environment-private-root"
        else:
            resolution_source = "config-private-root"
    if not library_path.is_file():
        raise SystemExit(f"library missing: {library_path}")
    return library_path, resolution_source


def _resolve_private_output(
    private_root: Path,
    requested: str | None,
    *,
    default_relative: str,
) -> Path:
    raw = Path(requested).expanduser() if requested else Path(default_relative)
    candidate = raw if raw.is_absolute() else private_root / raw
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(private_root):
        raise SystemExit("compiled private index output must remain under private root")
    relative = resolved.relative_to(private_root)
    cursor = private_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise SystemExit("compiled private index output crosses a symlink")
    return resolved


def _query_result(
    *,
    index: LibraryIndex,
    library_index_sha256: str,
    role: str,
    capacity_budget: int,
    semantic_categories: Sequence[str],
    asset_requirements: Sequence[str],
    customer_assets_available: bool,
    style_cluster: str | None,
    limit: int,
    allow_fallback: bool,
    include_ineligible: bool,
    required_source_ordinal: int | None = None,
) -> dict[str, Any]:
    if required_source_ordinal is not None and required_source_ordinal < 1:
        raise SystemExit("--required-source-ordinal must be a positive integer")
    selected_style = style_cluster or index.dominant_style_cluster_id
    # Preserve the established scoring and ranking algorithm.  When an exact
    # source ordinal is locked, ask it for the complete ranked universe first,
    # then apply the hard constraint and only then enforce the public limit.
    # This avoids a false no-match when the required page ranks just outside
    # the requested result window.
    query_limit = (
        max(limit, index.page_template_count)
        if required_source_ordinal is not None
        else limit
    )
    ranked_candidates = query_page_template_candidates(
        index,
        role=role,
        capacity_budget=capacity_budget,
        semantic_categories=tuple(semantic_categories),
        style_cluster=selected_style,
        asset_requirements=tuple(asset_requirements),
        customer_assets_available=customer_assets_available,
        limit=query_limit,
        allow_fallback=allow_fallback,
        include_ineligible=include_ineligible,
    )
    candidates = (
        tuple(
            candidate
            for candidate in ranked_candidates
            if candidate.page_template.slide_number == required_source_ordinal
        )[:limit]
        if required_source_ordinal is not None
        else ranked_candidates
    )
    if required_source_ordinal is not None and not candidates:
        raise SystemExit(
            "no eligible page-template candidate matches "
            f"required_source_ordinal={required_source_ordinal}"
        )
    result = {
        "schema_version": "page-template-query-result.v1",
        "library_index_sha256": library_index_sha256,
        "role": role,
        "capacity_budget": capacity_budget,
        "semantic_categories": list(semantic_categories),
        "style_cluster": selected_style,
        "asset_requirements": list(asset_requirements),
        "customer_assets_available": customer_assets_available,
        "limit": limit,
        "allow_fallback": allow_fallback,
        "direct_use_only": True,
        "include_ineligible": include_ineligible,
        "weights": dict(DEFAULT_SCORING),
        "count": len(candidates),
        "eligible_count": sum(candidate.eligibility for candidate in candidates),
        "candidates": [candidate.to_dict() for candidate in candidates],
    }
    if required_source_ordinal is not None:
        result["required_source_ordinal"] = required_source_ordinal
    return result


def _run_query_pages(args: argparse.Namespace) -> dict[str, Any]:
    library_path, resolution_source = _resolve_library_path(args)
    index: LibraryIndex = load_library_index(library_path)
    if not args.role:
        raise SystemExit("--role is required for query-pages")
    result = _query_result(
        index=index,
        library_index_sha256=hashlib.sha256(library_path.read_bytes()).hexdigest(),
        role=args.role,
        capacity_budget=args.capacity_budget,
        semantic_categories=args.semantic_category or (),
        style_cluster=args.style_cluster,
        asset_requirements=args.asset_requirement or (),
        customer_assets_available=args.customer_assets_available,
        limit=args.limit,
        allow_fallback=args.allow_fallback,
        include_ineligible=args.include_ineligible,
        required_source_ordinal=args.required_source_ordinal,
    )
    result["library_resolution_source"] = resolution_source
    return result


def _load_query_request(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read --query-request: {exc}") from exc
    if payload.get("schema_version") != "page-template-query-request.v1":
        raise SystemExit("unsupported query-request schema_version")
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - installation contract
        raise SystemExit("jsonschema is required to validate query requests") from exc
    schema = json.loads(
        (THIS_DIR.parent / "schemas" / "page-template-query-request.v1.schema.json")
        .read_text(encoding="utf-8")
    )
    try:
        jsonschema.Draft202012Validator(schema).validate(payload)
    except jsonschema.ValidationError as exc:
        raise SystemExit(f"query-request schema validation failed: {exc.message}") from exc
    slides = payload.get("slides")
    if not isinstance(slides, list) or not slides:
        raise SystemExit("query-request slides must be a non-empty array")
    ordinals: set[int] = set()
    for item in slides:
        if not isinstance(item, dict):
            raise SystemExit("each query-request slide must be an object")
        ordinal = item.get("target_ordinal")
        if not isinstance(ordinal, int) or ordinal < 1:
            raise SystemExit("target_ordinal must be a positive integer")
        if ordinal in ordinals:
            raise SystemExit(f"duplicate target_ordinal: {ordinal}")
        ordinals.add(ordinal)
        if not isinstance(item.get("role"), str) or not item["role"].strip():
            raise SystemExit(f"role is required for target_ordinal {ordinal}")
        budget = item.get("capacity_budget")
        if not isinstance(budget, int) or budget < 1:
            raise SystemExit(
                f"capacity_budget must be >= 1 for target_ordinal {ordinal}"
            )
    return payload


def _run_query_bundle(args: argparse.Namespace) -> dict[str, Any]:
    if not args.query_request:
        raise SystemExit("--query-request is required for query-bundle")
    if not args.output:
        raise SystemExit("--output is required for query-bundle")
    request_path = Path(args.query_request).expanduser().resolve(strict=True)
    request = _load_query_request(request_path)
    library_path, resolution_source = _resolve_library_path(args)
    library_sha = hashlib.sha256(library_path.read_bytes()).hexdigest()
    index = load_library_index(library_path)
    queries: list[dict[str, Any]] = []
    for item in sorted(request["slides"], key=lambda value: value["target_ordinal"]):
        result = _query_result(
            index=index,
            library_index_sha256=library_sha,
            role=item["role"],
            capacity_budget=item["capacity_budget"],
            semantic_categories=item.get("semantic_categories", ()),
            asset_requirements=item.get("asset_requirements", ()),
            customer_assets_available=bool(
                item.get("customer_assets_available", False)
            ),
            style_cluster=item.get("style_cluster"),
            limit=item.get("limit", 6),
            allow_fallback=bool(item.get("allow_fallback", False)),
            include_ineligible=False,
            required_source_ordinal=item.get("required_source_ordinal"),
        )
        queries.append(
            {
                "target_ordinal": item["target_ordinal"],
                "query_id": item.get("query_id", f"slide-{item['target_ordinal']:02d}"),
                "result": result,
            }
        )
    bundle = {
        "schema_version": "page-template-query-bundle.v1",
        "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
        "library_index_sha256": library_sha,
        "library_resolution_source": resolution_source,
        "query_count": len(queries),
        "queries": queries,
    }
    output = Path(args.output).expanduser().resolve(strict=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return bundle


def _run_compile_reference(args: argparse.Namespace) -> dict[str, Any]:
    if not args.deck:
        raise SystemExit("--deck is required for compile-reference")
    root = resolve_private_root(explicit=args.private_root)
    index = compile_reference_deck(args.deck)
    if not args.output:
        raise SystemExit("--output is required for compile-reference")
    out = _resolve_private_output(
        root,
        args.output,
        default_relative="v61/reference-work-summary-library-v4.json",
    )
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
    if args.command == "query-bundle":
        return _run_query_bundle(args)
    raise SystemExit(f"unknown command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    print(json.dumps(run(argv), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
