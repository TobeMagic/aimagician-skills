from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.component_curation import (  # noqa: E402
    ComponentCurationError,
    compile_component_profile,
)
from pptx_studio.component_profiles import load_component_profiles  # noqa: E402
from manage_pptx_studio_library import run  # noqa: E402


def _shape(identifier: int, name: str, x: int, y: int, *, text: str = "value", width: int = 200, height: int = 80) -> str:
    return f'''<p:sp><p:nvSpPr><p:cNvPr id="{identifier}" name="{name}"/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{width}" cy="{height}"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>'''


def _fixture(tmp_path: Path, *, anchor_width: int = 200) -> tuple[dict[str, object], dict[str, object], Path]:
    private_root = tmp_path / "private"
    package = private_root / "sources" / "gaojie" / "fixture.pptx"
    package.parent.mkdir(parents=True)
    slide = f'''<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree>
{_shape(2, "component-label", 100, 100, text="指标")}
{_shape(3, "component-body", 100, 180, text="说明")}
{_shape(4, "host-label", 600, 100, text="占位", width=anchor_width)}
{_shape(5, "host-body", 600, 180, text="占位", width=anchor_width)}
</p:spTree></p:cSld></p:sld>'''.encode("utf-8")
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", slide)
    package_sha = hashlib.sha256(package.read_bytes()).hexdigest()
    page_id = f"page_{package_sha[:24]}_001"
    catalog: dict[str, object] = {
        "pages": [{
            "page_id": page_id, "package_sha256": package_sha, "slide_number": 1,
            "category": "043-四段内容",
        }],
    }
    asset_index: dict[str, object] = {
        "packages": [{"package_sha256": package_sha, "private_path": "sources/gaojie/fixture.pptx"}],
    }
    return catalog, asset_index, private_root


def _request(page_id: str) -> dict[str, object]:
    return {
        "schema_version": "pptx-studio-component-curation-request.v1",
        "profile_id": "fixture-component-core.v1",
        "components": [{
            "component_key": "kpi-card", "source_page_id": page_id,
            "shape_ids": [2, 3], "semantic_intent": "operating-kpi-card",
            "allowed_roles": ["dashboard"], "host_anchor_keys": ["host-card"],
            "fields": [
                {"field_id": "label", "shape_id": 2, "semantic_role": "label"},
                {"field_id": "body", "shape_id": 3, "semantic_role": "body"},
            ],
        }],
        "host_anchors": [{
            "anchor_key": "host-card", "source_page_id": page_id, "shape_ids": [4, 5],
            "removable_shape_ids": [], "compatible_component_keys": ["kpi-card"],
        }],
    }


def test_component_curation_derives_complete_hash_bound_profile(tmp_path: Path) -> None:
    catalog, asset_index, private_root = _fixture(tmp_path)
    page_id = catalog["pages"][0]["page_id"]  # type: ignore[index]
    profile = compile_component_profile(
        catalog=catalog, asset_index=asset_index, private_root=private_root,
        request=_request(page_id),
    )

    assert profile["schema_version"] == "pptx-studio-component-profile.v2"
    assert profile["components"][0]["component_id"].startswith("component_")  # type: ignore[index]
    assert profile["host_anchors"][0]["host_anchor_id"].startswith("anchor_")  # type: ignore[index]
    assert profile["components"][0]["fields"][0]["max_chars"] >= 1  # type: ignore[index]

    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    loaded = load_component_profiles(profile_path, catalog=catalog)
    assert len(loaded.components) == 1
    assert len(loaded.host_anchors) == 1

    # A certified source may be intentionally absent from an older asset-index
    # snapshot. Operator curation may recover it only from the explicit source
    # root; normal production retrieval never takes this scan path.
    recovered = compile_component_profile(
        catalog=catalog, asset_index={"packages": []}, private_root=private_root,
        private_source_root=private_root / "sources" / "gaojie", request=_request(page_id),
    )
    assert recovered["profile_sha256"] == profile["profile_sha256"]


def test_component_curation_rejects_scaled_host_anchor(tmp_path: Path) -> None:
    catalog, asset_index, private_root = _fixture(tmp_path, anchor_width=201)
    page_id = catalog["pages"][0]["page_id"]  # type: ignore[index]

    with pytest.raises(ComponentCurationError, match="COMPONENT_CURATION_ANCHOR_BOUNDS_MISMATCH"):
        compile_component_profile(
            catalog=catalog, asset_index=asset_index, private_root=private_root,
            request=_request(page_id),
        )


def test_component_curation_binds_closure_level_visual_certification(tmp_path: Path) -> None:
    catalog, asset_index, private_root = _fixture(tmp_path)
    page_id = catalog["pages"][0]["page_id"]  # type: ignore[index]
    request = _request(page_id)
    request["schema_version"] = "pptx-studio-component-curation-request.v3"
    request["canvas_anchors"] = []
    request["components"][0]["visual_certification"] = {  # type: ignore[index]
        "review_id": "agnes.component-title.20260817",
        "review_sha256": "a" * 64,
        "style_profile": {
            "archetype": "corporate", "tone": "light", "color_family": "cool",
        },
        "suitability": ["institutional-finance"],
    }

    profile = compile_component_profile(
        catalog=catalog, asset_index=asset_index, private_root=private_root, request=request,
    )
    assert profile["schema_version"] == "pptx-studio-component-profile.v4"
    component = profile["components"][0]  # type: ignore[index]
    assert component["visual_certification"]["style_profile"]["color_family"] == "cool"
    profile_path = tmp_path / "visual-component-profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    loaded = load_component_profiles(profile_path, catalog=catalog)
    assert loaded.components[component["component_id"]].visual_certification is not None

    request["components"][0]["visual_certification"]["suitability"] = ["unsupported"]  # type: ignore[index]
    with pytest.raises(ComponentCurationError, match="COMPONENT_CURATION_VISUAL_CERTIFICATION_INVALID"):
        compile_component_profile(
            catalog=catalog, asset_index=asset_index, private_root=private_root, request=request,
        )


def test_component_curation_derives_fixed_empty_canvas_anchor(tmp_path: Path) -> None:
    private_root = tmp_path / "private"
    package = private_root / "sources" / "gaojie" / "canvas-fixture.pptx"
    package.parent.mkdir(parents=True)
    component_slide = f'''<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree>
{_shape(2, "source-title", 100, 100, text="标题", width=200, height=80)}
</p:spTree></p:cSld></p:sld>'''.encode("utf-8")
    host_slide = f'''<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree>
{_shape(4, "host-card", 600, 100, text="指标", width=200, height=80)}
</p:spTree></p:cSld></p:sld>'''.encode("utf-8")
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", component_slide)
        archive.writestr("ppt/slides/slide2.xml", host_slide)
    package_sha = hashlib.sha256(package.read_bytes()).hexdigest()
    source_page_id = f"page_{package_sha[:24]}_001"
    host_page_id = f"page_{package_sha[:24]}_002"
    catalog: dict[str, object] = {"pages": [
        {"page_id": source_page_id, "package_sha256": package_sha, "slide_number": 1, "category": "105-文本组件"},
        {"page_id": host_page_id, "package_sha256": package_sha, "slide_number": 2, "category": "104-数据基座-精选"},
    ]}
    asset_index: dict[str, object] = {"packages": [
        {"package_sha256": package_sha, "private_path": "sources/gaojie/canvas-fixture.pptx"},
    ]}
    request: dict[str, object] = {
        "schema_version": "pptx-studio-component-curation-request.v2",
        "profile_id": "fixture-canvas-core.v1",
        "components": [{
            "component_key": "title", "source_page_id": source_page_id,
            "shape_ids": [2], "semantic_intent": "report-title",
            "allowed_roles": ["dashboard"], "host_anchor_keys": ["title-canvas"],
            "fields": [{"field_id": "title", "shape_id": 2, "semantic_role": "title"}],
        }],
        "host_anchors": [],
        "canvas_anchors": [{
            "anchor_key": "title-canvas", "host_page_id": host_page_id,
            "canvas_source_page_id": source_page_id, "canvas_shape_ids": [2],
            "safe_underlay_shape_ids": [], "compatible_component_keys": ["title"],
        }],
    }

    profile = compile_component_profile(
        catalog=catalog, asset_index=asset_index, private_root=private_root, request=request,
    )
    assert profile["schema_version"] == "pptx-studio-component-profile.v3"
    anchor = profile["host_anchors"][0]  # type: ignore[index]
    assert anchor["anchor_mode"] == "canvas"
    assert anchor["canvas_bbox"] == [100, 100, 200, 80]
    profile_path = tmp_path / "canvas-profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    loaded = load_component_profiles(profile_path, catalog=catalog)
    assert loaded.host_anchor(anchor["host_anchor_id"]).anchor_mode == "canvas"

    # A canvas must actually be blank in the target host; this is not a
    # convenient bypass for placing a title on top of client evidence.
    host_slide = host_slide.replace(b'x="600" y="100"', b'x="100" y="100"')
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", component_slide)
        archive.writestr("ppt/slides/slide2.xml", host_slide)
    changed_sha = hashlib.sha256(package.read_bytes()).hexdigest()
    changed_catalog: dict[str, object] = {"pages": [
        {"page_id": f"page_{changed_sha[:24]}_001", "package_sha256": changed_sha, "slide_number": 1, "category": "105-文本组件"},
        {"page_id": f"page_{changed_sha[:24]}_002", "package_sha256": changed_sha, "slide_number": 2, "category": "104-数据基座-精选"},
    ]}
    changed_request = json.loads(json.dumps(request))
    changed_request["components"][0]["source_page_id"] = changed_catalog["pages"][0]["page_id"]
    changed_request["canvas_anchors"][0]["host_page_id"] = changed_catalog["pages"][1]["page_id"]
    changed_request["canvas_anchors"][0]["canvas_source_page_id"] = changed_catalog["pages"][0]["page_id"]
    changed_index = {"packages": [{"package_sha256": changed_sha, "private_path": "sources/gaojie/canvas-fixture.pptx"}]}
    with pytest.raises(ComponentCurationError, match="COMPONENT_CURATION_CANVAS_NOT_EMPTY"):
        compile_component_profile(
            catalog=changed_catalog, asset_index=changed_index, private_root=private_root,
            request=changed_request,
        )


def test_manager_writes_operator_curated_component_profile(tmp_path: Path) -> None:
    catalog, asset_index, private_root = _fixture(tmp_path)
    page_id = catalog["pages"][0]["page_id"]  # type: ignore[index]
    catalog_path = tmp_path / "catalog.json"
    asset_index_path = tmp_path / "asset-index.json"
    request_path = tmp_path / "curation.json"
    output_path = tmp_path / "component-profile.json"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    asset_index_path.write_text(json.dumps(asset_index), encoding="utf-8")
    request_path.write_text(json.dumps(_request(page_id)), encoding="utf-8")

    result = run([
        "curate-components", "--source-root", str(tmp_path / "source.sentinel"),
        "--archive-root", str(tmp_path / "archive.sentinel"),
        "--manifest", str(tmp_path / "manifest.sentinel"), "--catalog", str(catalog_path),
        "--asset-index", str(asset_index_path), "--private-root", str(private_root),
        "--private-source-root", str(private_root / "sources" / "gaojie"),
        "--component-curation-input", str(request_path),
        "--component-profile-output", str(output_path),
    ])

    assert result["status"] == "PASS"
    assert output_path.is_file()
    assert len(load_component_profiles(output_path, catalog=catalog).components) == 1
