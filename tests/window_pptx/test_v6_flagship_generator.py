from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
EXPORTER = SCRIPTS_ROOT / "export_window_pptx_brief_corpus.py"
GENERATOR = SCRIPTS_ROOT / "build_window_pptx_v6_flagships.mjs"


@pytest.fixture(scope="module")
def flagship_output(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("v6-flagships")
    briefs = root / "briefs"
    output = root / "output"
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
            "node",
            str(GENERATOR),
            "--brief-dir",
            str(briefs),
            "--output-dir",
            str(output),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return output


@pytest.mark.parametrize(
    ("filename", "spine_id"),
    [
        ("annual-work-report-v6.pptx", "institutional-work-summary"),
        ("campus-competition-defense-v6.pptx", "product-launch-stage"),
        ("academic-thesis-defense-v6.pptx", "data-research-editorial"),
    ],
)
def test_flagships_are_exact_native_editable_decks(
    flagship_output: Path, filename: str, spine_id: str
) -> None:
    deck = flagship_output / filename
    manifest = json.loads(
        deck.with_suffix(".pptx.manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["slide_count"] == 32
    assert manifest["native_editable"] is True
    assert manifest["whole_slide_rasterization"] is False
    assert manifest["certification"]["spine_id"] == spine_id

    with zipfile.ZipFile(deck) as archive:
        names = set(archive.namelist())
        slides = sorted(
            name
            for name in names
            if name.startswith("ppt/slides/slide")
            and name.endswith(".xml")
            and "/_rels/" not in name
        )
        notes = sorted(
            name
            for name in names
            if name.startswith("ppt/notesSlides/notesSlide")
            and name.endswith(".xml")
            and "/_rels/" not in name
        )
        assert len(slides) == 32
        assert len(notes) == 32
        assert all(b"FACT_IDS:" in archive.read(name) for name in notes)
        assert not any(b"<p:pic>" in archive.read(name) for name in slides)
        assert not any(
            b'TargetMode="External"' in archive.read(name)
            for name in names
            if name.endswith(".rels")
        )


def test_work_report_meets_native_chart_and_table_floor(flagship_output: Path) -> None:
    deck = flagship_output / "annual-work-report-v6.pptx"
    with zipfile.ZipFile(deck) as archive:
        names = set(archive.namelist())
        charts = [
            name
            for name in names
            if name.startswith("ppt/charts/chart") and name.endswith(".xml")
        ]
        table_slides = [
            name
            for name in names
            if name.startswith("ppt/slides/slide")
            and name.endswith(".xml")
            and b"<a:tbl>" in archive.read(name)
        ]
        assert len(charts) >= 8
        assert len(table_slides) >= 2
