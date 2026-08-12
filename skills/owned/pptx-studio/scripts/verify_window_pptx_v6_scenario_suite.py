#!/usr/bin/env python3
"""Fail-closed verification for the 15-scenario Window PPTX V6 suite."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from window_pptx.ordinary_model_suite import evaluate_ordinary_plan


EXPECTED_SLIDES = {
    "annual-work-report": 15,
    "campus-competition-defense": 18,
    "academic-thesis-defense": 19,
    "business-operations-review": 20,
    "project-proposal": 20,
    "product-launch": 20,
    "market-analysis": 20,
    "sales-proposal": 20,
    "investor-pitch": 20,
    "strategy-planning": 20,
    "data-analysis-report": 20,
    "training-course": 20,
    "brand-company-introduction": 20,
    "project-kickoff": 20,
    "ecommerce-marketing-plan": 20,
}
FLAGSHIPS = {
    "annual-work-report",
    "campus-competition-defense",
    "academic-thesis-defense",
}
LEAKAGE_TOKENS = (
    "普通模型选择",
    "synthetic-evaluation-only",
    "undefined",
    "lorem ipsum",
    "placeholder",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _review_payload(path: Path) -> dict[str, object] | None:
    outer = json.loads(path.read_text(encoding="utf-8"))
    analysis = outer.get("analysis")
    if not isinstance(analysis, str):
        return None
    match = re.search(r"\{.*\}", analysis, flags=re.DOTALL)
    if match is None:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    serious = [
        finding
        for finding in payload.get("findings", [])
        if finding.get("severity") in {"Blocker", "Important"}
    ]
    score = float(payload.get("mean_score", 0.0))
    if not (
        payload.get("status") == "PASS"
        and score >= 4.2
        and payload.get("reference_grade_craft") is True
        and not serious
    ):
        return None
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--proof-dir", type=Path, required=True)
    parser.add_argument("--brief-dir", type=Path, required=True)
    parser.add_argument("--plan-dir", type=Path, required=True)
    parser.add_argument("--review-dir", type=Path, action="append", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    failures: list[str] = []
    records: list[dict[str, object]] = []
    signatures: set[str] = set()
    semantic_families: set[str] = set()
    accepted_reviews: dict[str, tuple[Path, dict[str, object]]] = {}
    for review_dir in args.review_dir:
        for path in sorted(review_dir.glob("*-anchor.json")):
            deck = path.name.removesuffix(".json")
            payload = _review_payload(path)
            if payload is not None:
                accepted_reviews[deck] = (path, payload)

    for scenario, expected_count in EXPECTED_SLIDES.items():
        deck_name = f"{scenario}-reference-anchor"
        deck = args.output_dir / f"{deck_name}.pptx"
        manifest_path = Path(f"{deck}.manifest.json")
        proof = args.proof_dir / deck_name / "portable-proof"
        local_failures: list[str] = []
        if not deck.is_file() or not manifest_path.is_file():
            failures.append(f"{scenario}: output or manifest missing")
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("scenario_id") != scenario:
            local_failures.append("manifest scenario mismatch")
        if manifest.get("slide_count") != expected_count:
            local_failures.append("manifest slide count mismatch")
        if manifest.get("output_sha256") != _sha256(deck):
            local_failures.append("output hash mismatch")
        if manifest.get("native_editable") is not True:
            local_failures.append("native_editable is not true")
        if manifest.get("whole_slide_rasterization") is not False:
            local_failures.append("whole_slide_rasterization is not false")
        slides = manifest.get("slides", [])
        if len(slides) != expected_count:
            local_failures.append("manifest slide inventory mismatch")

        if scenario not in FLAGSHIPS:
            roles = [slide.get("role") for slide in slides]
            if roles.count("section") != 4 or roles.count("appendix") != 3:
                local_failures.append("commercial anatomy role count mismatch")
            signature = next(
                (
                    str(slide.get("family"))
                    for slide in slides
                    if slide.get("role") == "scenario-signature"
                ),
                "",
            )
            semantic = next(
                (
                    str(slide.get("family"))
                    for slide in slides
                    if slide.get("role") == "model-semantic"
                ),
                "",
            )
            signatures.add(signature)
            semantic_families.add(semantic)
            provenance = manifest.get("ordinary_model_plan", {})
            plan_path = args.plan_dir / f"{scenario}.brief-plan.v1.json"
            brief_path = args.brief_dir / f"{scenario}.project-brief-pack.v1.json"
            if provenance.get("authority") != "semantic-fact-grouping-and-order-only":
                local_failures.append("ordinary model authority mismatch")
            if not plan_path.is_file() or not brief_path.is_file():
                local_failures.append("ordinary plan or source brief missing")
            else:
                if provenance.get("sha256") != _sha256(plan_path):
                    local_failures.append("ordinary plan hash mismatch")
                evaluation = evaluate_ordinary_plan(
                    json.loads(brief_path.read_text(encoding="utf-8")),
                    json.loads(plan_path.read_text(encoding="utf-8")),
                )
                if evaluation.status != "PASS" or evaluation.fact_coverage != 1.0:
                    local_failures.append(
                        f"ordinary plan validation failed: {evaluation.error}"
                    )

        try:
            with zipfile.ZipFile(deck) as archive:
                names = archive.namelist()
                slide_xml_names = sorted(
                    name
                    for name in names
                    if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
                )
                notes_names = [
                    name
                    for name in names
                    if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
                ]
                if len(slide_xml_names) != expected_count:
                    local_failures.append("OOXML slide count mismatch")
                if len(notes_names) != expected_count:
                    local_failures.append("speaker-note coverage mismatch")
                xml_text = "\n".join(
                    archive.read(name).decode("utf-8", errors="replace")
                    for name in slide_xml_names
                )
                visible_text = "\n".join(
                    re.findall(r"<a:t>(.*?)</a:t>", xml_text, flags=re.DOTALL)
                )
                lowered = visible_text.casefold()
                leaked = [token for token in LEAKAGE_TOKENS if token.casefold() in lowered]
                if leaked:
                    local_failures.append(f"customer-visible leakage: {leaked}")
                for name in slide_xml_names:
                    xml = archive.read(name).decode("utf-8", errors="replace")
                    if xml.count("<p:sp>") + xml.count("<p:graphicFrame>") < 2:
                        local_failures.append(f"insufficient native objects: {name}")
                        break
                relationships = "\n".join(
                    archive.read(name).decode("utf-8", errors="replace")
                    for name in names
                    if name.endswith(".rels")
                )
                if 'TargetMode="External"' in relationships:
                    local_failures.append("external relationship present")
        except zipfile.BadZipFile:
            local_failures.append("PPTX package is unreadable")

        pages = sorted(proof.glob("slide-*.png"))
        pdf = proof / "portable-proof.pdf"
        if len(pages) != expected_count:
            local_failures.append("portable proof page count mismatch")
        if not pdf.is_file() or not pdf.read_bytes().startswith(b"%PDF-"):
            local_failures.append("portable proof PDF missing or unreadable")

        review = accepted_reviews.get(deck_name)
        if review is None:
            local_failures.append("no strict passing independent visual review")
            review_source = None
            review_score = None
        else:
            review_source = str(review[0])
            review_score = review[1].get("mean_score")
        failures.extend(f"{scenario}: {item}" for item in local_failures)
        records.append(
            {
                "scenario_id": scenario,
                "output": str(deck),
                "sha256": _sha256(deck),
                "slide_count": expected_count,
                "review_source": review_source,
                "review_score": review_score,
                "status": "PASS" if not local_failures else "FAIL",
                "failures": local_failures,
            }
        )

    if len(signatures) != 12 or "" in signatures:
        failures.append(f"scenario signatures are not 12-way distinct: {sorted(signatures)}")
    required_semantics = {
        "semantic-metric-ledger",
        "semantic-comparison",
        "semantic-matrix",
        "semantic-process",
    }
    if not semantic_families.issuperset(required_semantics):
        failures.append(
            f"semantic family coverage mismatch: {sorted(semantic_families)}"
        )
    report = {
        "schema_version": "window-pptx-v6-scenario-suite-verification.v1",
        "status": "PASS" if not failures else "FAIL",
        "scenario_count": len(records),
        "portable_page_count": sum(
            int(record["slide_count"]) for record in records
        ),
        "strict_visual_pass_count": sum(
            record["review_source"] is not None for record in records
        ),
        "visual_score_mean": round(
            sum(float(record["review_score"]) for record in records)
            / len(records),
            3,
        )
        if records and all(record["review_score"] is not None for record in records)
        else None,
        "distinct_scenario_signatures": sorted(signatures),
        "semantic_families": sorted(semantic_families),
        "failures": failures,
        "records": records,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
