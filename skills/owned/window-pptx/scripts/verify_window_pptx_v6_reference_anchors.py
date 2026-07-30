#!/usr/bin/env python3
"""Verify Phase 46 anchor manifests, provenance, and native OOXML structure."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from window_pptx.template_pack import load_template_pack


EXPECTED = {
    "annual-work-report": 15,
    "campus-competition-defense": 18,
    "academic-thesis-defense": 19,
}
NATIVE_CANDIDATES = {
    "native:agenda.grid-four",
    "native:bar-chart.editorial",
    "native:comparison.editorial",
    "native:cover.editorial",
    "native:cta.centered",
    "native:focal-statement.centered",
    "native:focal-statement.editorial-left",
    "native:funnel.editorial",
    "native:multi-card.editorial",
    "native:process.editorial",
    "native:product-showcase.dashboard",
    "native:section.centered",
    "native:table.editorial",
    "native:trend-line.editorial",
}
SLIDE_XML = re.compile(r"^ppt/slides/slide[0-9]+\.xml$")
NOTES_XML = re.compile(r"^ppt/notesSlides/notesSlide[0-9]+\.xml$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def verify_ooxml(
    deck: Path,
    expected_slides: int,
    *,
    template_materialized: bool = False,
) -> dict[str, Any]:
    with zipfile.ZipFile(deck) as archive:
        names = set(archive.namelist())
        slides = sorted(name for name in names if SLIDE_XML.match(name))
        notes = sorted(name for name in names if NOTES_XML.match(name))
        if len(slides) != expected_slides:
            raise ValueError(f"{deck}: expected {expected_slides} slides, found {len(slides)}")
        if len(notes) != expected_slides:
            raise ValueError(f"{deck}: every slide must carry provenance notes")
        if not all(b"FACT_IDS:" in archive.read(name) for name in notes):
            raise ValueError(f"{deck}: missing FACT_IDS notes")
        if any(
            b'TargetMode="External"' in archive.read(name)
            for name in names
            if name.endswith(".rels")
        ):
            raise ValueError(f"{deck}: external OOXML relationships are forbidden")
        slide_bytes = [archive.read(name) for name in slides]
        native_graphic_slides = sum(
            b"<p:sp>" in data or b"<p:graphicFrame>" in data for data in slide_bytes
        )
        if native_graphic_slides != expected_slides:
            raise ValueError(f"{deck}: every page must contain native editable objects")
        picture_slides = sum(b"<p:pic>" in data for data in slide_bytes)
        if picture_slides > (expected_slides if template_materialized else 4):
            raise ValueError(f"{deck}: bitmap usage exceeds bounded hero/map allowance")
        charts = sum(
            name.startswith("ppt/charts/chart") and name.endswith(".xml")
            for name in names
        )
        tables = sum(b"<a:tbl>" in data for data in slide_bytes)
        return {
            "slide_count": len(slides),
            "notes_count": len(notes),
            "native_graphic_slides": native_graphic_slides,
            "picture_slides": picture_slides,
            "chart_parts": charts,
            "table_slides": tables,
            "external_relationships": 0,
        }


def verify(
    output_dir: Path,
    schema_path: Path,
    certified_core_path: Path,
) -> dict[str, Any]:
    schema = load(schema_path)
    validator = Draft202012Validator(schema)
    core = load(certified_core_path)
    certified = {
        page["page_id"]: page
        for page in core.get("pages", [])
        if isinstance(page, dict) and isinstance(page.get("page_id"), str)
    }
    decks: list[dict[str, Any]] = []
    for scenario, expected_slides in EXPECTED.items():
        deck = output_dir / f"{scenario}-reference-anchor.pptx"
        manifest_path = deck.with_suffix(".pptx.manifest.json")
        if not deck.is_file() or not manifest_path.is_file():
            raise ValueError(f"missing anchor output for {scenario}")
        manifest = load(manifest_path)
        errors = sorted(validator.iter_errors(manifest), key=lambda error: error.json_path)
        if errors:
            raise ValueError(
                f"{manifest_path}: schema failure: "
                + "; ".join(f"{error.json_path}: {error.message}" for error in errors)
            )
        if manifest["scenario_id"] != scenario or manifest["slide_count"] != expected_slides:
            raise ValueError(f"{manifest_path}: scenario/slide-count mismatch")
        if manifest["output_sha256"] != sha256(deck):
            raise ValueError(f"{manifest_path}: output fingerprint mismatch")
        slides = manifest["slides"]
        if len(slides) != expected_slides:
            raise ValueError(f"{manifest_path}: slide manifest is incomplete")
        if len({slide["slide_id"] for slide in slides}) != expected_slides:
            raise ValueError(f"{manifest_path}: slide ids must be unique")
        family_counts = Counter(slide["family"] for slide in slides)
        body_family_counts = Counter(
            slide["family"]
            for slide in slides
            if slide["role"] not in {"cover", "agenda", "section", "closing"}
        )
        if body_family_counts and max(body_family_counts.values()) > 3:
            raise ValueError(f"{manifest_path}: one layout family is repeated more than three times")

        provenance: list[dict[str, Any]] = []
        for slide in slides:
            candidate_id = slide["candidate_id"]
            if candidate_id.startswith("template:"):
                expected_id = (
                    "template:physical.work-summary.s"
                    + slide["slide_id"].rsplit("-", 1)[-1]
                )
                if scenario != "annual-work-report" or candidate_id != expected_id:
                    raise ValueError(
                        f"{manifest_path}: invalid exact TemplatePack page binding"
                    )
                materialization = manifest.get("template_materialization")
                if not isinstance(materialization, dict):
                    raise ValueError(f"{manifest_path}: missing template materialization")
                pack = load_template_pack(materialization["template_pack_id"])
                if materialization["source_sha256"] != pack.template_sha256:
                    raise ValueError(f"{manifest_path}: template source hash drift")
                if materialization["output_sha256"] != sha256(deck):
                    raise ValueError(f"{manifest_path}: template output hash drift")
                provenance.append(
                    {
                        "slide_id": slide["slide_id"],
                        "candidate_id": candidate_id,
                        "use": "exact-template-pack-materialization",
                        "materialized_as_whole_slide": True,
                        "whole_slide_rasterization": False,
                        "source_sha256": pack.template_sha256,
                    }
                )
            elif candidate_id.startswith("physical:"):
                page_id = candidate_id.removeprefix("physical:")
                page = certified.get(page_id)
                if page is None:
                    raise ValueError(f"{manifest_path}: uncertified private candidate {page_id}")
                if page.get("certification") != "certified-private":
                    raise ValueError(f"{manifest_path}: candidate lacks certified-private status")
                if page.get("visual_disposition") not in {"keep", "reroute"}:
                    raise ValueError(f"{manifest_path}: denied/reference-only candidate used as influence")
                provenance.append(
                    {
                        "slide_id": slide["slide_id"],
                        "candidate_id": candidate_id,
                        "use": "certified-influence-only",
                        "materialized_as_whole_slide": False,
                        "pool": page.get("pool"),
                        "visual_sha256": page.get("visual_sha256"),
                    }
                )
            else:
                if candidate_id not in NATIVE_CANDIDATES:
                    raise ValueError(f"{manifest_path}: unknown governed native candidate {candidate_id}")
                provenance.append(
                    {
                        "slide_id": slide["slide_id"],
                        "candidate_id": candidate_id,
                        "use": "anchor-native-composition",
                        "materialized_as_whole_slide": False,
                        "observed_family": slide["family"],
                    }
                )
        decks.append(
            {
                "scenario_id": scenario,
                "manifest": str(manifest_path),
                "deck": str(deck),
                "sha256": sha256(deck),
                "ooxml": verify_ooxml(
                    deck,
                    expected_slides,
                    template_materialized="template_materialization" in manifest,
                ),
                "family_counts": dict(sorted(family_counts.items())),
                "body_family_counts": dict(sorted(body_family_counts.items())),
                "provenance": provenance,
                "status": "PASS",
            }
        )
    return {
        "schema_version": "anchor-provenance-report.v1",
        "status": "PASS",
        "certified_core": str(certified_core_path),
        "reference_only_materialized": False,
        "whole_slide_rasterization": False,
        "decks": decks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--certified-core", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify(
        args.output_dir.resolve(),
        args.schema.resolve(),
        args.certified_core.resolve(),
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "report": str(args.report)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
