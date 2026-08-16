from __future__ import annotations

import base64
import hashlib
import io
import json
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio"
EVAL_ROOT = REPO_ROOT / "quality" / "skill-evals" / "pptx-studio"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from window_pptx.agnes_direct import GeneratedAsset
from window_pptx.asset_materialization import _prompt, materialize_asset_plan
from window_pptx.design_packs import select_design_pack
from window_pptx.generation import prepare_brief_generation
from window_pptx.layouts import SlideSize
from window_pptx.visual_plan import AssetPlan, PlannedAsset


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _asset_plan() -> AssetPlan:
    return AssetPlan(
        design_pack_id="consulting-executive",
        assets=(
            PlannedAsset(
                id="asset-cover",
                slide_id="cover",
                purpose="cover visual anchor",
                kind="photo",
                priority=("user", "generated", "native"),
                fallback="branded-native-geometry",
                editable=False,
            ),
            PlannedAsset(
                id="asset-process",
                slide_id="process",
                purpose="process visual anchor",
                kind="diagram",
                priority=("native",),
                fallback="native-editable-diagram",
                editable=True,
            ),
        ),
    )


def test_materialization_resolves_generated_and_native_assets(tmp_path: Path) -> None:
    digest = hashlib.sha256(PNG_1X1).hexdigest()

    def generate(*, prompt: str) -> GeneratedAsset:
        assert "no text" in prompt.casefold()
        assert "no logo" in prompt.casefold()
        assert "no watermark" in prompt.casefold()
        assert "no factual data" in prompt.casefold()
        return GeneratedAsset(
            route_id="agnes-direct/agnes-image-2.1-flash",
            model="agnes-image-2.1-flash",
            image_bytes=PNG_1X1,
            manifest={
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "input_sha256": [],
                "output_sha256": digest,
                "size": "1x1",
                "content_policy": {
                    "facts": "forbidden",
                    "text": "forbidden",
                    "logos": "forbidden",
                    "watermarks": "forbidden",
                },
            },
        )

    result = materialize_asset_plan(
        _asset_plan(),
        select_design_pack("project-proposal"),
        required_asset_ids=frozenset({"asset-cover"}),
        image_generator=generate,
        output_dir=tmp_path,
        retrieved_at="2026-07-28",
    )

    assert [asset.status for asset in result.asset_plan.assets] == [
        "generated",
        "native-materialized",
    ]
    assert set(result.bindings) == {"asset-cover"}
    assert result.bindings["asset-cover"].path.is_file()
    assert min(
        result.bindings["asset-cover"].record.width_px,
        result.bindings["asset-cover"].record.height_px,
    ) >= 1000
    assert result.entries[0].byte_sha256 == hashlib.sha256(
        result.bindings["asset-cover"].path.read_bytes()
    ).hexdigest()
    assert result.entries[0].provider_route == (
        "agnes-direct/agnes-image-2.1-flash"
    )
    assert result.entries[1].path is None
    result.assert_release_ready()


def test_generation_failure_uses_declared_native_fallback(tmp_path: Path) -> None:
    def fail(*, prompt: str) -> GeneratedAsset:
        raise RuntimeError("provider unavailable")

    result = materialize_asset_plan(
        _asset_plan(),
        select_design_pack("project-proposal"),
        required_asset_ids=frozenset({"asset-cover"}),
        image_generator=fail,
        output_dir=tmp_path,
        retrieved_at="2026-07-28",
    )

    assert result.asset_plan.assets[0].status == "fallback"
    assert result.entries[0].reason == "GENERATION_FAILED:RuntimeError"
    assert result.entries[0].fallback == "branded-native-geometry"
    assert not result.bindings
    assert all(asset.status != "planned" for asset in result.asset_plan.assets)


def test_missing_generator_never_leaves_release_asset_planned() -> None:
    result = materialize_asset_plan(
        _asset_plan(),
        select_design_pack("project-proposal"),
        required_asset_ids=frozenset({"asset-cover"}),
        retrieved_at="2026-07-28",
    )

    assert [asset.status for asset in result.asset_plan.assets] == [
        "fallback",
        "native-materialized",
    ]
    assert result.entries[0].reason == "NO_GOVERNED_BYTES"


def test_consulting_prompt_avoids_pseudo_text_prone_objects() -> None:
    prompt = _prompt(
        _asset_plan().assets[0],
        select_design_pack("project-proposal"),
    ).casefold()

    assert "abstract editorial still life" in prompt
    assert "do not depict screens" in prompt
    assert "no text, no logo, no watermark" in prompt


def test_product_prompt_rejects_physical_retail_product_metaphors() -> None:
    prompt = _prompt(
        _asset_plan().assets[0],
        select_design_pack("product-launch"),
    ).casefold()

    assert "ai work assistant" in prompt
    assert "do not depict perfume" in prompt
    assert "software intelligence" in prompt


def test_research_prompt_rejects_generic_people_and_stock_scenes() -> None:
    prompt = _prompt(
        _asset_plan().assets[0],
        select_design_pack("data-analysis"),
    ).casefold()

    assert "datum lines" in prompt
    assert "do not depict people" in prompt
    assert "evidence-led tone" in prompt


def test_generation_binds_materialized_cover_to_image_led_layout(
    tmp_path: Path,
) -> None:
    buffer = io.BytesIO()
    Image.new("RGB", (1536, 1024), "#197C78").save(buffer, format="PNG")
    payload = buffer.getvalue()
    digest = hashlib.sha256(payload).hexdigest()

    def generate(*, prompt: str) -> GeneratedAsset:
        return GeneratedAsset(
            route_id="agnes-direct/agnes-image-2.1-flash",
            model="agnes-image-2.1-flash",
            image_bytes=payload,
            manifest={
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "input_sha256": [],
                "output_sha256": digest,
                "size": "1536x1024",
                "content_policy": {
                    "facts": "forbidden",
                    "text": "forbidden",
                    "logos": "forbidden",
                    "watermarks": "forbidden",
                },
            },
        )

    facts = json.loads(
        (
            EVAL_ROOT / "consulting-project-proposal-facts.json"
        ).read_text(encoding="utf-8")
    )
    brief = json.loads(
        (
            EVAL_ROOT / "consulting-project-proposal-brief.json"
        ).read_text(encoding="utf-8")
    )
    generation = prepare_brief_generation(
        facts,
        brief,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        image_generator=generate,
        asset_output_dir=tmp_path,
        build_render=True,
    )

    assert generation.render_plan is not None
    assert generation.asset_plan.assets[0].status == "generated"
    cover = generation.render_plan.slides[0]
    assert cover.layout_id == "cover.poster-editorial"
    images = [item for item in cover.objects if item.kind == "image"]
    assert len(images) == 1
    assert images[0].asset_record is not None
    assert images[0].asset_record.id == "asset-cover"
    assert images[0].source_path == (
        generation.asset_materialization.bindings["asset-cover"].path
    )
