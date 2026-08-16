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
from pptx_studio.curation import ACTIVE_GAOJIE_CATEGORIES, COMPONENT_PROMOTION_TARGET_CATEGORY  # noqa: E402


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _pptx(path: Path, *, image_only: bool = False, nested_group: bool = False) -> str:
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
        if nested_group:
            slide += (
                '<p:grpSp><p:nvGrpSpPr><p:cNvPr id="4" name="MetricGroup"/></p:nvGrpSpPr><p:grpSpPr/>'
                '<p:sp><p:nvSpPr><p:cNvPr id="5" name="Metric"/></p:nvSpPr><p:spPr><a:xfrm><a:off x="100000" y="4000000"/><a:ext cx="2000000" cy="500000"/></a:xfrm></p:spPr><p:txBody><a:p><a:r><a:t>96.9%</a:t></a:r></a:p></p:txBody></p:sp>'
                '</p:grpSp>'
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


def _root(tmp_path: Path, *, image_only: bool = False, nested_group: bool = False) -> tuple[Path, dict[str, dict[str, object]]]:
    root = tmp_path / "private" / "sources" / "gaojie"
    for category in ACTIVE_GAOJIE_CATEGORIES:
        (root / category).mkdir(parents=True)
    package = root / ACTIVE_GAOJIE_CATEGORIES[0] / "example.pptx"
    digest = _pptx(package, image_only=image_only, nested_group=nested_group)
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
    assert page["materialization"]["status"] == "eligible"
    assert page["materialization"]["governed_content_slot_count"] == 0
    assert page["materialization"]["blocker_codes"] == []
    assert page["materialization"]["dependency_bytes"] > 0
    assert page["materialization"]["fragment_slot_count"] == 0
    assert page["materialization"]["visual_text_unit_count"] >= 1
    assert first["certification_overlay"]["status"] == "NOT_APPLIED"
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


def test_catalog_marks_selected_data_base_category_component_only(tmp_path: Path) -> None:
    root, render = _root(tmp_path)
    package = root / COMPONENT_PROMOTION_TARGET_CATEGORY / "component.pptx"
    _pptx(package)
    with zipfile.ZipFile(package, "a") as archive:
        archive.writestr("ppt/custom-data-base-marker.txt", "component-only")
    digest = _sha(package.read_bytes())
    render[f"{digest}:001"] = {
        "image_sha256": "c" * 64,
        "width": 1280,
        "height": 720,
        "visual_quality": 0.9,
    }

    catalog = compile_catalog(root, render_index=render)

    component_page = next(page for page in catalog["pages"] if page["package_sha256"] == digest)
    assert component_page["component_only"] is True


def test_catalog_recursively_indexes_native_text_in_grouped_diagrams(tmp_path: Path) -> None:
    root, render = _root(tmp_path, nested_group=True)

    catalog = compile_catalog(root, render_index=render)

    page = catalog["pages"][0]
    assert [shape["shape_id"] for shape in page["shapes"]] == ["2", "3", "5"]
    assert page["shapes"][-1]["text"] == "96.9%"
    assert len([region for region in catalog["regions"] if region["page_id"] == page["page_id"]]) == 3


def test_catalog_applies_hash_bound_visual_denial_to_materialization(tmp_path: Path) -> None:
    root, render = _root(tmp_path)
    package_sha = next(iter(render)).split(":", 1)[0]
    certification = {
        "schema_version": "gaojie-certified-core.v2",
        "denied_page_count": 1,
        "denied_pages": [{
            "package_sha256": package_sha,
            "page_id": f"{package_sha}:001",
            "slide_number": 1,
            "visual_sha256": "a" * 64,
            "visual_disposition": "deny",
            "reason_code": "I-LOW",
        }],
    }

    catalog = compile_catalog(
        root, render_index=render, certification_evidence=certification,
    )

    overlay = catalog["certification_overlay"]
    assert overlay["status"] == "PASS"
    assert overlay["denied_page_count"] == 1
    assert overlay["applied_denied_page_count"] == 1
    assert overlay["out_of_scope_denied_page_count"] == 0
    page = catalog["pages"][0]
    assert page["certification"] == {
        "visual_disposition": "deny",
        "reason_code": "I-LOW",
        "visual_sha256": "a" * 64,
    }
    assert page["materialization"]["status"] == "blocked"
    assert "visual-certification-denied" in page["materialization"]["blocker_codes"]


def test_catalog_rejects_visual_denial_with_stale_render_hash(tmp_path: Path) -> None:
    root, render = _root(tmp_path)
    package_sha = next(iter(render)).split(":", 1)[0]
    certification = {
        "schema_version": "gaojie-certified-core.v2",
        "denied_page_count": 1,
        "denied_pages": [{
            "package_sha256": package_sha,
            "page_id": f"{package_sha}:001",
            "slide_number": 1,
            "visual_sha256": "b" * 64,
            "visual_disposition": "deny",
            "reason_code": "I-LOW",
        }],
    }

    with pytest.raises(CatalogError, match="CERTIFICATION_VISUAL_EVIDENCE_DRIFT"):
        compile_catalog(
            root, render_index=render, certification_evidence=certification,
        )


def test_catalog_does_not_block_final_keep_override_in_review_partition(tmp_path: Path) -> None:
    root, render = _root(tmp_path)
    package_sha = next(iter(render)).split(":", 1)[0]
    certification = {
        "schema_version": "gaojie-certified-core.v2",
        "denied_page_count": 1,
        "denied_pages": [{
            "package_sha256": package_sha,
            "page_id": f"{package_sha}:001",
            "slide_number": 1,
            "visual_sha256": "a" * 64,
            "visual_disposition": "keep",
            "reason_code": "I-OVERRIDE",
        }],
    }

    catalog = compile_catalog(
        root, render_index=render, certification_evidence=certification,
    )

    assert catalog["certification_overlay"]["source_entry_count"] == 1
    assert catalog["certification_overlay"]["denied_page_count"] == 0
    assert catalog["pages"][0]["materialization"]["status"] == "eligible"
    assert "certification" not in catalog["pages"][0]
