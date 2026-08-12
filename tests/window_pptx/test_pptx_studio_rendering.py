from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.rendering import RenderEvidenceError, complete_render_index  # noqa: E402


def _presentation(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "ppt/presentation.xml",
            '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:sldSz cx="12192000" cy="6858000"/>'
            "</p:presentation>",
        )
        archive.writestr("ppt/slides/slide1.xml", "<slide/>")


def test_existing_evidence_is_reused_without_invoking_renderer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    category = "003-封面模板"
    package = source / category / "cover.pptx"
    package.parent.mkdir(parents=True)
    _presentation(package)
    digest = hashlib.sha256(package.read_bytes()).hexdigest()

    class UnexpectedRenderer:
        def __init__(self, **_: object) -> None:
            raise AssertionError("renderer must not run when evidence exists")

    monkeypatch.setattr("pptx_studio.rendering.LibreOfficeVerifier", UnexpectedRenderer)
    result = complete_render_index(
        source,
        existing_index={
            f"{digest}:001": {
                "image_sha256": "a" * 64,
                "width": 1280,
                "height": 720,
                "visual_quality": 0.9,
            }
        },
        evidence_root=tmp_path / "private" / "evidence",
        active_categories=(category,),
    )

    assert result["rendered_package_count"] == 0
    assert result["page_count"] == 1
    assert result["pages"][f"{digest}:001"]["image_sha256"] == "a" * 64


def test_invalid_source_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(RenderEvidenceError, match="ROOT_INVALID"):
        complete_render_index(
            tmp_path / "missing",
            existing_index={},
            evidence_root=tmp_path / "private" / "evidence",
            active_categories=(),
        )
