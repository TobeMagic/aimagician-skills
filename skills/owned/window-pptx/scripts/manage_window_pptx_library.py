#!/usr/bin/env python3
"""Manage the Window-PPTX private library through dry-run-first JSON commands."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from window_pptx.acquisition import (
    AcquisitionError,
    build_acquisition_manifest,
    validate_private_credential_file,
    write_resume_state,
)
from window_pptx.catalog import CatalogError, DEFAULT_CATALOG, load_catalog, query_catalog
from window_pptx.quarantine import inspect_package_bytes, validate_quarantine_report
from window_pptx.rights import RightsError, certification_evidence, load_rights_record


PUBLIC_METADATA_SOURCE_ID = "public-metadata-seed"


def _state_source_name(source_id: str) -> str:
    if (
        source_id
        and source_id not in {".", ".."}
        and all(character.isalnum() or character in "-_." for character in source_id)
    ):
        return source_id
    digest = hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:16]
    return f"source-{digest}"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["discover", "sync", "ingest", "certify", "query"]
    )
    parser.add_argument("--private-root", required=True)
    parser.add_argument("--source-id", default=PUBLIC_METADATA_SOURCE_ID)
    parser.add_argument("--origin", default="https://templates.example.com")
    parser.add_argument("--allow-host", action="append", default=[])
    parser.add_argument("--credential-file")
    parser.add_argument("--public-metadata-only", action="store_true")
    parser.add_argument("--package")
    parser.add_argument("--quarantine-report")
    parser.add_argument("--rights-record")
    parser.add_argument("--item-id")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--scenario")
    parser.add_argument("--style-tag", action="append", default=[])
    parser.add_argument("--minimum-slides", type=int)
    parser.add_argument("--include-uncertified", action="store_true")
    parser.add_argument("--apply", action="store_true")
    return parser


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parser().parse_args(argv)
    mode = "apply" if args.apply else "dry_run"
    hosts = args.allow_host or [
        args.origin.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
    ]
    status = "PASS"
    findings: list[dict[str, str]] = []
    completed: list[str] = []
    unavailable: list[str] = []
    requested = [args.item_id] if args.item_id else []

    private_root = Path(args.private_root)

    def private_file(value: str | None) -> Path | None:
        if value is None:
            return None
        path = Path(value)
        if private_root.name != ".private" or private_root.is_symlink():
            return None
        try:
            path.resolve().relative_to(private_root.resolve())
        except (OSError, ValueError):
            return None
        return path if path.is_file() else None

    if args.command == "sync":
        if args.public_metadata_only:
            if args.source_id != PUBLIC_METADATA_SOURCE_ID:
                status = "FAIL"
                findings.append({"code": "PUBLIC_METADATA_SOURCE_NOT_ALLOWLISTED"})
            else:
                findings.append({"code": "PUBLIC_METADATA_SYNC_PLANNED"})
        elif not args.credential_file:
            status = "NEEDS_AUTH"
            findings.append({"code": "PRIVATE_CREDENTIAL_REQUIRED"})
        else:
            try:
                validate_private_credential_file(
                    args.credential_file, args.private_root
                )
            except AcquisitionError:
                status = "NEEDS_AUTH"
                findings.append({"code": "PRIVATE_CREDENTIAL_INVALID"})
            else:
                status = "PARTIAL"
                findings.append({"code": "SITE_ADAPTER_NOT_CONFIGURED"})
    elif args.command == "ingest":
        if args.package:
            package_path = private_file(args.package)
            if package_path is None:
                status = "FAIL"
                findings.append({"code": "PACKAGE_OUTSIDE_PRIVATE_ROOT"})
            else:
                try:
                    report = inspect_package_bytes(package_path.read_bytes())
                except OSError:
                    status = "FAIL"
                    findings.append({"code": "PACKAGE_READ_FAILED"})
                else:
                    status = report["status"]
                    findings.extend(report["findings"])
                    if report["disposition"] == "ACCEPT":
                        completed.append(report["package_sha256"])
        else:
            findings.append({"code": "PACKAGE_NOT_SUPPLIED_DRY_RUN"})
    elif args.command == "certify":
        rights_path = private_file(args.rights_record)
        quarantine_path = private_file(args.quarantine_report)
        if not args.item_id:
            status = "FAIL"
            findings.append({"code": "ITEM_ID_REQUIRED"})
        elif rights_path is None:
            status = "NEEDS_RIGHTS"
            findings.append({"code": "RIGHTS_RECORD_REQUIRED"})
        elif quarantine_path is None:
            status = "FAIL"
            findings.append({"code": "QUARANTINE_REPORT_REQUIRED"})
        else:
            try:
                rights = load_rights_record(rights_path)
            except RightsError:
                status = "NEEDS_RIGHTS"
                findings.append({"code": "RIGHTS_RECORD_INVALID"})
            else:
                try:
                    report = validate_quarantine_report(
                        json.loads(quarantine_path.read_text(encoding="utf-8"))
                    )
                except (OSError, json.JSONDecodeError, ValueError):
                    status = "FAIL"
                    findings.append({"code": "QUARANTINE_REPORT_INVALID"})
                else:
                    if report["disposition"] != "ACCEPT":
                        status = "QUARANTINED"
                        findings.append({"code": "PACKAGE_NOT_ACCEPTED"})
                    else:
                        try:
                            certification_evidence(
                                source_id=args.source_id,
                                item_id=args.item_id,
                                quarantine_report=report,
                                rights_record=rights,
                            )
                        except RightsError:
                            status = "NEEDS_RIGHTS"
                            findings.append(
                                {"code": "CERTIFICATION_RIGHTS_MISMATCH"}
                            )
                        else:
                            completed.append(args.item_id)
    elif args.command == "query":
        try:
            catalog = load_catalog(args.catalog)
            matches = query_catalog(
                catalog,
                scenario=args.scenario,
                style_tags=args.style_tag,
                minimum_slides=args.minimum_slides,
                include_uncertified=args.include_uncertified,
            )
        except CatalogError:
            status = "FAIL"
            findings.append({"code": "CATALOG_INVALID"})
        else:
            completed.extend(item["catalog_item_id"] for item in matches)

    relative_state_path = (
        f"state/{_state_source_name(args.source_id)}-{args.command}.json"
    )
    manifest = build_acquisition_manifest(
        command=args.command,
        source_id=args.source_id,
        origin=args.origin,
        allowlisted_hosts=hosts,
        requested_item_ids=requested,
        completed_item_ids=completed,
        unavailable_item_ids=unavailable,
        status=status,
        mode=mode,
        state_path=relative_state_path if args.apply else None,
        findings=findings,
    )
    if args.apply:
        write_resume_state(
            args.private_root,
            relative_state_path,
            manifest,
        )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    result = run(argv)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
