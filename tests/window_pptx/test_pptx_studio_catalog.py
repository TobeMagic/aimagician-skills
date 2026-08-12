from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pytest
from jsonschema import validate


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.catalog import CatalogError, compile_catalog, serialize_catalog  # noqa: E402
from pptx_studio.curation import ACTIVE_GAOJIE_CATEGORIES  # noqa: E402


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _pptx(path: Path, *, image_only: bool = False) -> str:
    slide = (
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld>'
        '<p:spTree><p:nvGrpSpPr/><p:grpSpPr/>'
    )
    if image_only:
        slide += '<p:pic><p:nvPicPr><p:cNvPr id="2" name="Hero"/></p:nvPicPr><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="12192000" cy="6858000"/></a:xfrm></p:spPr></p:pic>'
    else:
        slide += (
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/></p:nvSpPr><p:spPr><a:xfrm><a:off x="100000" y="100000"/><a:ext cx="6000000" cy="800000"/></a:xfrm></p:spPr><p:txBody><a:p><a:r><a:t>Quarterly outlook</a:t></a:r></a:p></p:txBody></p:sp>'
            '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Body"/></p:nvSpPr><p:spPr><a:xfrm><a:off x="100000" y="1200000"/><a:ext cx="6000000" cy="2500000"/></a:xfrm></p:spPr><p:txBody><a:p><a:r><a:t>Evidence and action</a:t></a:r></a:p></p:txBody></p:sp>'
        )
    slide += "</p:spTree></p:cSld></p:sld>"
    presentation = (
        '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        '<p:sldSz cx="12192000" cy="6858000"/></p:presentation>'
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/presentation.xml", presentation)
        archive.writestr("ppt/slides/slide1.xml", slide)
    return _sha(path.read_bytes())


def _root(tmp_path: Path, *, image_only: bool = False) -> tuple[Path, dict[str, dict[str, object]]]:
    root = tmp_path / "private" / "sources" / "gaojie"
    for category in ACTIVE_GAOJIE_CATEGORIES:
        (root / category).mkdir(parents=True)
    package = root / ACTIVE_GAOJIE_CATEGORIES[0] / "example.pptx"
    digest = _pptx(package, image_only=image_only)
    render = {
        f"{digest}:001": {
            "image_sha256": "a" * 64,
            "width": 1280,
            "height": 720,
            "visual_quality": 0.9,
        }
    }
    return root, render


def test_catalog_is_deterministic_and_uses_hash_identity(tmp_path: Path) -> None:
    root, render = _root(tmp_path)

    first = compile_catalog(root, render_index=render)
    second = compile_catalog(root, render_index=render)

    assert serialize_catalog(first) == serialize_catalog(second)
    page = first["pages"][0]
    assert page["page_id"].startswith("page_")
    assert "example.pptx" not in page["page_id"]
    assert page["render"]["image_sha256"] == "a" * 64
    assert page["shapes"][0]["text"] == "Quarterly outlook"
    assert page["materialization"] == {
        "status": "eligible",
        "governed_content_slot_count": 0,
        "blocker_codes": [],
    }
    assert first["region_count"] == len(first["regions"])
    assert first["region_count"] >= 1
    assert first["category_index"] == {ACTIVE_GAOJIE_CATEGORIES[0]: 1}
    schema = json.loads(
        (REPO_ROOT / "skills" / "owned" / "pptx-studio" / "schemas" / "pptx-studio-catalog.v1.schema.json").read_text(encoding="utf-8")
    )
    validate(first, schema)
    json.dumps(first, ensure_ascii=False)


def test_catalog_rejects_missing_render_or_category_escape(tmp_path: Path) -> None:
    root, render = _root(tmp_path)
    with pytest.raises(CatalogError, match="RENDER_EVIDENCE_MISSING"):
        compile_catalog(root, render_index={})

    outside = tmp_path / "other"
    outside.mkdir()
    with pytest.raises(CatalogError, match="SOURCE_SCOPE_INVALID"):
        compile_catalog(outside, render_index=render)


def test_catalog_marks_image_only_page_non_component_eligible(tmp_path: Path) -> None:
    root, render = _root(tmp_path, image_only=True)

    catalog = compile_catalog(root, render_index=render)

    assert catalog["pages"][0]["editability"] == "image_only"
    assert catalog["pages"][0]["component_eligible"] is False
