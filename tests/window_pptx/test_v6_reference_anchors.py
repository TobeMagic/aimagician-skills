from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
EXPORTER = SCRIPTS_ROOT / "export_window_pptx_brief_corpus.py"
GENERATOR = SCRIPTS_ROOT / "build_window_pptx_v6_reference_anchors.py"
VERIFIER = SCRIPTS_ROOT / "verify_window_pptx_v6_reference_anchors.py"
SCHEMA = SKILL_ROOT / "schemas" / "anchor-deck-blueprint.v1.schema.json"


@pytest.fixture(scope="module")
def anchor_output(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("v6-reference-anchors")
    briefs = root / "briefs"
    assets = root / "assets"
    output = root / "output"
    assets.mkdir()
    for name, color in (
        ("work-hero.png", "#0A604D"),
        ("campus-hero.png", "#0A263D"),
        ("academic-hero.png", "#081B36"),
    ):
        Image.new("RGB", (1600, 900), color).save(assets / name)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(SCRIPTS_ROOT)
    subprocess.run(
        [sys.executable, str(EXPORTER), "--output-dir", str(briefs)],
        cwd=REPO_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--brief-dir",
            str(briefs),
            "--output-dir",
            str(output),
            "--asset-dir",
            str(assets),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    physical_ids = set()
    for manifest_path in output.glob("*.manifest.json"):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        physical_ids.update(
            slide["candidate_id"].removeprefix("physical:")
            for slide in manifest["slides"]
            if slide["candidate_id"].startswith("physical:")
        )
    core = root / "certified-core.json"
    core.write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page_id": page_id,
                        "certification": "certified-private",
                        "visual_disposition": "keep",
                        "pool": "test-certified",
                        "visual_sha256": "0" * 64,
                    }
                    for page_id in sorted(physical_ids)
                ]
            }
        ),
        encoding="utf-8",
    )
    report = root / "provenance-report.json"
    subprocess.run(
        [
            sys.executable,
            str(VERIFIER),
            "--output-dir",
            str(output),
            "--schema",
            str(SCHEMA),
            "--certified-core",
            str(core),
            "--report",
            str(report),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return output, report


@pytest.mark.parametrize(
    ("scenario", "slide_count"),
    [
        ("annual-work-report", 15),
        ("campus-competition-defense", 18),
        ("academic-thesis-defense", 19),
    ],
)
def test_reference_anchor_contract(
    anchor_output: tuple[Path, Path],
    scenario: str,
    slide_count: int,
) -> None:
    output, _ = anchor_output
    deck = output / f"{scenario}-reference-anchor.pptx"
    manifest = json.loads(
        deck.with_suffix(".pptx.manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["schema_version"] == "anchor-deck-blueprint.v1"
    assert manifest["slide_count"] == slide_count
    assert manifest["native_editable"] is True
    assert manifest["whole_slide_rasterization"] is False
    assert manifest["candidate_policy"]["reference_only_materialized"] is False
    assert len({slide["slide_id"] for slide in manifest["slides"]}) == slide_count

    with zipfile.ZipFile(deck) as archive:
        slides = [
            name
            for name in archive.namelist()
            if name.startswith("ppt/slides/slide")
            and name.endswith(".xml")
            and "/_rels/" not in name
        ]
        assert len(slides) == slide_count
        assert all(
            b"<p:sp>" in archive.read(name) or b"<p:graphicFrame>" in archive.read(name)
            for name in slides
        )


def test_reference_anchor_provenance_is_honest_and_complete(
    anchor_output: tuple[Path, Path],
) -> None:
    _, report_path = anchor_output
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["reference_only_materialized"] is False
    assert report["whole_slide_rasterization"] is False
    assert {deck["scenario_id"] for deck in report["decks"]} == {
        "annual-work-report",
        "campus-competition-defense",
        "academic-thesis-defense",
    }
    assert all(deck["status"] == "PASS" for deck in report["decks"])
    assert all(
        item.get("whole_slide_rasterization", False) is False
        for deck in report["decks"]
        for item in deck["provenance"]
    )
    assert any(
        item["use"] == "exact-template-pack-materialization"
        for deck in report["decks"]
        for item in deck["provenance"]
    )
