from __future__ import annotations

import sys
import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from window_pptx.template_geometry import VisualMask  # noqa: E402
from window_pptx.visual_similarity import (  # noqa: E402
    VisualSimilarityError,
    compare_masked_previews,
)


def _page(path: Path, *, mutation: tuple[int, int, int, int] | None = None) -> Path:
    image = Image.new("RGB", (100, 100), "white")
    if mutation is not None:
        ImageDraw.Draw(image).rectangle(mutation, fill="black")
    image.save(path)
    return path


def _mask(
    *,
    x: float = 0.1,
    y: float = 0.1,
    width: float = 0.21,
    height: float = 0.21,
) -> VisualMask:
    return VisualMask(
        slide=1,
        target_kind="shape",
        target_id="5",
        x=x,
        y=y,
        width=width,
        height=height,
    )


def test_change_fully_inside_trusted_mask_passes(tmp_path: Path) -> None:
    source = _page(tmp_path / "source.png")
    candidate = _page(tmp_path / "candidate.png", mutation=(10, 10, 30, 30))

    report = compare_masked_previews(
        [source],
        [candidate],
        [_mask()],
        source_renderer_fingerprint="libreoffice:1|poppler:1|dpi:144",
        candidate_renderer_fingerprint="libreoffice:1|poppler:1|dpi:144",
    )

    assert report.passed is True
    assert report.slides[0].similarity == 1.0
    assert report.slides[0].changed_pixel_ratio == 0.0


def test_change_outside_trusted_mask_fails(tmp_path: Path) -> None:
    source = _page(tmp_path / "source.png")
    candidate = _page(tmp_path / "candidate.png", mutation=(60, 60, 90, 90))

    report = compare_masked_previews(
        [source],
        [candidate],
        [_mask()],
        source_renderer_fingerprint="same",
        candidate_renderer_fingerprint="same",
    )

    assert report.passed is False
    assert report.slides[0].similarity < 0.98
    assert report.slides[0].changed_pixel_ratio > 0.02


@pytest.mark.parametrize(
    ("source_size", "candidate_size", "source_renderer", "candidate_renderer", "match"),
    [
        ((100, 100), (90, 100), "same", "same", "page dimensions"),
        ((100, 100), (100, 100), "one", "two", "renderer fingerprint"),
    ],
)
def test_mismatch_fails_closed(
    tmp_path: Path,
    source_size: tuple[int, int],
    candidate_size: tuple[int, int],
    source_renderer: str,
    candidate_renderer: str,
    match: str,
) -> None:
    source = Image.new("RGB", source_size, "white")
    candidate = Image.new("RGB", candidate_size, "white")
    source_path = tmp_path / "source.png"
    candidate_path = tmp_path / "candidate.png"
    source.save(source_path)
    candidate.save(candidate_path)

    with pytest.raises(VisualSimilarityError, match=match):
        compare_masked_previews(
            [source_path],
            [candidate_path],
            [_mask()],
            source_renderer_fingerprint=source_renderer,
            candidate_renderer_fingerprint=candidate_renderer,
        )


def test_excessive_mask_coverage_fails_closed(tmp_path: Path) -> None:
    source = _page(tmp_path / "source.png")
    candidate = _page(tmp_path / "candidate.png")

    with pytest.raises(VisualSimilarityError, match="coverage"):
        compare_masked_previews(
            [source],
            [candidate],
            [_mask(x=0, y=0, width=0.95, height=0.95)],
            source_renderer_fingerprint="same",
            candidate_renderer_fingerprint="same",
        )


def test_visual_similarity_report_matches_owned_schema(tmp_path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    source = _page(tmp_path / "source.png")
    candidate = _page(tmp_path / "candidate.png")
    report = compare_masked_previews(
        [source],
        [candidate],
        [_mask()],
        source_renderer_fingerprint="same",
        candidate_renderer_fingerprint="same",
    )
    schema = json.loads(
        (
            SKILL_ROOT
            / "schemas"
            / "visual-similarity-report.v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(schema).validate(report.to_dict())
