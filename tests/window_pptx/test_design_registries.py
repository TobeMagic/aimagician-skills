from __future__ import annotations

import json
import math
import sys
from dataclasses import replace
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import window_pptx
import window_pptx.layouts as layouts_module
from window_pptx.assets import (
    AssetIntent,
    AssetRecord,
    AssetSession,
    choose_asset,
    load_asset_policy,
)
from window_pptx.layouts import (
    SlideSize,
    load_components,
    load_layout_registry,
    load_legacy_templates,
    resolve_layout,
    validate_registry_bundle,
)
from window_pptx.themes import (
    BrandOverrides,
    contrast_ratio,
    load_themes,
    resolve_theme,
    select_theme,
)


THEME_IDS = {
    "executive-light",
    "executive-dark",
    "technology",
    "finance-investor",
    "marketing-vibrant",
    "ecommerce-editorial",
    "education-training",
    "public-enterprise",
}

FAMILY_IDS = {
    "agenda",
    "big-number",
    "cards",
    "case-study",
    "comparison",
    "cover",
    "cta",
    "data-chart",
    "executive-summary",
    "focal-statement",
    "funnel",
    "image-story",
    "matrix",
    "process",
    "product-showcase",
    "quadrant",
    "risk-recommendation",
    "roadmap",
    "section",
    "summary",
    "table",
    "team",
    "text-media",
    "timeline",
}

PHASE23_FORMS = {
    "area-chart",
    "bar-chart",
    "before-after",
    "big-number",
    "bubble-chart",
    "cards",
    "comparison",
    "composition-chart",
    "distribution-chart",
    "dot-plot",
    "focal-statement",
    "image-story",
    "kpi-dashboard",
    "line-chart",
    "matrix",
    "modular-grid",
    "process",
    "product-showcase",
    "quadrant",
    "recommendation",
    "risk-recommendation",
    "roadmap",
    "scatter-plot",
    "stacked-bar",
    "structured-content",
    "table",
    "text-media",
    "timeline",
}


def test_eight_exact_themes_resolve_complete_design_tokens() -> None:
    themes = load_themes()

    assert set(themes) == THEME_IDS
    for theme_id in sorted(themes):
        resolved = resolve_theme(theme_id, installed_fonts={"Arial"})
        assert resolved.grid["columns"] == 12
        assert resolved.grid["safe_margin_x_in"] == 0.5
        assert resolved.grid["safe_margin_y_in"] == 0.4
        assert resolved.spacing == (0, 8, 16, 24, 32, 48, 64)
        assert resolved.typography["body"] >= 16
        assert resolved.typography["label"] >= 11
        assert resolved.typography["footnote"] >= 11
        assert min(resolved.typography.values()) >= 11
        assert {"border", "radius", "shadow", "decoration"} <= set(
            resolved.effects
        )


def test_theme_contrast_pairs_meet_governed_thresholds() -> None:
    for theme_id in THEME_IDS:
        theme = resolve_theme(theme_id, installed_fonts={"Arial"})
        assert contrast_ratio(theme.colors["text"], theme.colors["background"]) >= 4.5
        assert contrast_ratio(theme.colors["on_primary"], theme.colors["primary"]) >= 4.5
        assert contrast_ratio(theme.colors["muted_text"], theme.colors["background"]) >= 3.0


def test_brand_and_font_overrides_are_deterministic_and_reported() -> None:
    brand = BrandOverrides(
        primary="#0057B8",
        accent="#FFB81C",
        heading_font="Brand Sans",
        body_font="Brand Text",
    )

    first = resolve_theme(
        "executive-light", brand=brand, installed_fonts={"Arial", "Brand Sans"}
    )
    second = resolve_theme(
        "executive-light", brand=brand, installed_fonts={"Arial", "Brand Sans"}
    )

    assert first == second
    assert first.colors["primary"] == "#0057B8"
    assert first.colors["accent"] == "#FFB81C"
    assert first.fonts["heading"] == "Brand Sans"
    assert first.fonts["body"] == "Arial"
    assert {event.code for event in first.events} >= {
        "BRAND_COLOR_OVERRIDE",
        "FONT_OVERRIDE_APPLIED",
        "FONT_FALLBACK",
    }
    assert contrast_ratio(first.colors["on_primary"], first.colors["primary"]) >= 4.5


def test_brand_color_with_no_background_contrast_falls_back_explicitly() -> None:
    theme = resolve_theme(
        "executive-light",
        brand=BrandOverrides(primary="#FFFFFF", accent="#F7F8FA"),
        installed_fonts={"Arial"},
    )

    assert theme.colors["primary"] == "#0B3A67"
    assert theme.colors["accent"] == "#2F80ED"
    assert sum(
        event.code == "BRAND_COLOR_CONTRAST_FALLBACK" for event in theme.events
    ) == 2


def test_invalid_brand_color_is_rejected() -> None:
    with pytest.raises(ValueError, match="color"):
        resolve_theme(
            "executive-light",
            brand=BrandOverrides(primary="red"),
            installed_fonts={"Arial"},
        )


def test_unavailable_font_override_is_reported_even_when_preferred_exists() -> None:
    theme = resolve_theme(
        "executive-light",
        brand=BrandOverrides(heading_font="Missing Brand Font"),
        installed_fonts={"Aptos Display", "Arial"},
    )

    assert theme.fonts["heading"] == "Aptos Display"
    assert any(
        event.code == "FONT_FALLBACK"
        and event.requested == "Missing Brand Font"
        and event.resolved == "Aptos Display"
        for event in theme.events
    )


def test_cjk_locale_uses_verified_cjk_profile_before_latin_fonts() -> None:
    theme = resolve_theme(
        "executive-light",
        installed_fonts={"Aptos Display", "Aptos", "Microsoft YaHei", "Arial"},
        locale="zh-CN",
    )

    assert theme.fonts == {
        "heading": "Microsoft YaHei",
        "body": "Microsoft YaHei",
    }
    assert {event.code for event in theme.events} >= {"FONT_SCRIPT_PROFILE"}


@pytest.mark.parametrize(
    ("scenario", "audience", "industry", "expected"),
    [
        ("investor-pitch", "investor", None, "finance-investor"),
        ("training", "learner", None, "education-training"),
        ("ecommerce-marketing", "customer", None, "ecommerce-editorial"),
        ("brand-introduction", "customer", None, "marketing-vibrant"),
        ("product-launch", "customer", None, "marketing-vibrant"),
        ("business-report", "executive", "government", "public-enterprise"),
        ("public-enterprise", "executive", None, "public-enterprise"),
        ("public enterprise", "executive", None, "public-enterprise"),
        ("business-report", "executive", "banking", "finance-investor"),
        ("financial-report", "executive", None, "finance-investor"),
        ("data-analysis", "executive", "technology", "technology"),
        ("business-report", "executive", None, "executive-light"),
    ],
)
def test_project_context_selects_theme_deterministically(
    scenario: str, audience: str, industry: str | None, expected: str
) -> None:
    assert select_theme(scenario, audience=audience, industry=industry) == expected


def test_dark_theme_is_an_explicit_safe_default_not_model_improvisation() -> None:
    assert select_theme("business-report", prefer_dark=True) == "executive-dark"


def test_twenty_four_families_have_at_least_three_unique_variants() -> None:
    registry = load_layout_registry()

    assert set(registry.families) == FAMILY_IDS
    assert len(registry.variants) >= 72
    assert len(registry.variants) == len(set(registry.variants))
    for family in registry.families.values():
        assert len(family.variant_ids) >= 3
        assert len(set(family.variant_ids)) == len(family.variant_ids)
    for recipe_id, capacity in registry.recipe_capacities.items():
        assert 0 <= capacity.min_items <= capacity.max_items
        assert capacity.max_items >= 1
        assert capacity.densities
        assert recipe_id in registry.recipes


def test_layout_geometry_is_derived_from_governed_grid_tokens() -> None:
    registry = load_layout_registry()

    assert registry.grid.columns == 12
    assert registry.grid.spacing_base_pt == 8
    assert registry.grid.reference_width_in == pytest.approx(13.333)
    assert registry.grid.reference_height_in == pytest.approx(7.5)
    for slots in registry.recipes.values():
        for slot in slots:
            assert 0 <= slot.col < registry.grid.columns
            assert 1 <= slot.col_span <= registry.grid.columns - slot.col
            assert 0 <= slot.row < registry.grid.rows
            assert 1 <= slot.row_span <= registry.grid.rows - slot.row


def test_every_phase23_form_resolves_to_a_registered_family() -> None:
    registry = load_layout_registry()

    assert PHASE23_FORMS <= set(registry.semantic_form_map)
    assert {
        registry.semantic_form_map[form] for form in PHASE23_FORMS
    } <= FAMILY_IDS


def test_specialized_families_keep_semantic_components_in_every_variant() -> None:
    registry = load_layout_registry()
    required = {
        "big-number": {"kpi"},
        "cards": {"card"},
        "comparison": {"comparison-panel"},
        "timeline": {"timeline-node"},
        "process": {"process-step"},
        "matrix": {"matrix-cell"},
        "quadrant": {"matrix-cell", "chart"},
        "risk-recommendation": {
            "risk-panel",
            "recommendation-panel",
            "matrix-cell",
        },
        "funnel": {"process-step", "chart"},
        "roadmap": {"timeline-node", "process-step"},
        "data-chart": {"chart"},
        "table": {"table"},
        "product-showcase": {"image-frame"},
        "team": {"team-member"},
        "cta": {"cta"},
        "image-story": {"image-frame"},
    }

    for family_id, component_ids in required.items():
        for variant_id in registry.families[family_id].variant_ids:
            layout = resolve_layout(variant_id, SlideSize(13.333, 7.5))
            assert component_ids & {slot.component for slot in layout.slots}, variant_id


def test_each_family_has_three_distinct_geometry_component_variants() -> None:
    registry = load_layout_registry()
    size = SlideSize(13.333, 7.5)

    for family in registry.families.values():
        signatures = {
            tuple(
                (slot.component, slot.x, slot.y, slot.width, slot.height)
                for slot in resolve_layout(variant_id, size).slots
            )
            for variant_id in family.variant_ids
        }
        assert len(signatures) >= 3, family.id


@pytest.mark.parametrize(
    ("form", "max_items"),
    [
        ("cards", 5),
        ("process", 6),
        ("timeline", 6),
        ("roadmap", 6),
        ("comparison", 5),
        ("before-after", 5),
        ("table", 9),
        ("big-number", 5),
        ("kpi-dashboard", 5),
        ("line-chart", 10),
        ("area-chart", 10),
        ("bar-chart", 10),
        ("composition-chart", 9),
        ("distribution-chart", 10),
        ("scatter-plot", 10),
        ("matrix", 9),
        ("quadrant", 9),
        ("risk-recommendation", 5),
        ("recommendation", 5),
        ("image-story", 4),
        ("product-showcase", 4),
        ("text-media", 4),
        ("focal-statement", 1),
    ],
)
@pytest.mark.parametrize("density", ["sparse", "balanced", "dense"])
def test_phase23_outputs_have_a_phase24_layout_service_path(
    form: str, max_items: int, density: str
) -> None:
    for item_count in {1, max_items}:
        layout = resolve_layout(
            form,
            SlideSize(13.333, 7.5),
            item_count=item_count,
            density=density,
        )
        assert layout.capacity.min_items <= item_count <= layout.capacity.max_items
        assert layout.requested_density == density
        assert layout.resolved_density in layout.capacity.densities


def test_registry_bundle_has_no_geometry_or_contract_issues() -> None:
    issues = validate_registry_bundle()

    assert issues == []


@pytest.mark.parametrize(
    "size", [SlideSize(13.333, 7.5), SlideSize(10.0, 7.5), SlideSize(7.5, 13.333)]
)
def test_resolved_layout_scales_inside_custom_page(size: SlideSize) -> None:
    layout = resolve_layout("line-chart", size)

    assert layout.family_id == "data-chart"
    assert layout.slots
    for slot in layout.slots:
        assert 0 <= slot.x < size.width
        assert 0 <= slot.y < size.height
        assert slot.width > 0 and slot.height > 0
        assert slot.x + slot.width <= size.width + 1e-6
        assert slot.y + slot.height <= size.height + 1e-6


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_slide_size_is_rejected(bad: float) -> None:
    with pytest.raises(ValueError, match="finite and positive"):
        resolve_layout("cards", SlideSize(bad, 7.5))


def test_layout_selection_varies_deterministically_after_repetition() -> None:
    size = SlideSize(13.333, 7.5)
    first = resolve_layout("cards", size)
    second = resolve_layout("cards", size, previous_layouts=(first.id,))
    third = resolve_layout(
        "cards", size, previous_layouts=(first.id, second.id)
    )

    assert len({first.id, second.id, third.id}) == 3
    assert (first, second, third) == (
        resolve_layout("cards", size),
        resolve_layout("cards", size, previous_layouts=(first.id,)),
        resolve_layout("cards", size, previous_layouts=(first.id, second.id)),
    )


def test_layout_rhythm_cycles_after_all_compatible_variants_are_used() -> None:
    size = SlideSize(13.333, 7.5)
    history: tuple[str, ...] = ()
    selected: list[str] = []
    for _ in range(6):
        layout = resolve_layout("cards", size, previous_layouts=history)
        selected.append(layout.id)
        history += (layout.id,)

    assert selected[:3] == selected[3:]


def test_layout_capacity_filters_incompatible_variants_before_rhythm() -> None:
    size = SlideSize(13.333, 7.5)

    sparse = resolve_layout("cards", size, item_count=1, density="sparse")
    dense = resolve_layout("cards", size, item_count=5, density="dense")

    assert sparse.capacity.min_items <= 1 <= sparse.capacity.max_items
    assert "sparse" in sparse.capacity.densities
    assert dense.capacity.min_items <= 5 <= dense.capacity.max_items
    assert "dense" in dense.capacity.densities


def test_layout_capacity_rejects_invalid_or_unserviceable_requests() -> None:
    size = SlideSize(13.333, 7.5)

    with pytest.raises(ValueError, match="density"):
        resolve_layout("cards", size, density="crowded")
    with pytest.raises(ValueError, match="non-negative integer"):
        resolve_layout("cards", size, item_count=-1)
    with pytest.raises(ValueError, match="non-negative integer"):
        resolve_layout("cards", size, item_count=1.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cannot fit"):
        resolve_layout("cards.three-column", size, item_count=1, density="sparse")


def test_effective_capacity_never_exceeds_overridden_component_capacity() -> None:
    size = SlideSize(13.333, 7.5)

    assert resolve_layout("process.focus", size, item_count=6).capacity.max_items == 6
    assert resolve_layout("cards.top-band", size, item_count=5).capacity.max_items == 5
    with pytest.raises(ValueError, match="cannot fit"):
        resolve_layout("process.focus", size, item_count=7)
    with pytest.raises(ValueError, match="cannot fit"):
        resolve_layout("cards.top-band", size, item_count=6)


def test_phase24_runtime_is_exposed_from_the_public_package() -> None:
    assert window_pptx.select_theme is select_theme
    assert window_pptx.resolve_layout is resolve_layout
    assert window_pptx.choose_asset is choose_asset


def test_required_editable_components_and_font_minima_exist() -> None:
    components = load_components()
    required = {
        "body-text",
        "card",
        "chart",
        "decoration",
        "footer",
        "icon",
        "image-frame",
        "kpi",
        "matrix-cell",
        "process-step",
        "table",
        "timeline-node",
        "title",
    }

    assert required <= set(components)
    for component in components.values():
        assert component.object_policy in {"native_editable", "linked_asset"}
        assert component.min_font_pt >= 11
        assert component.max_items >= 1


def test_asset_policy_requires_crop_provenance_and_no_stretch() -> None:
    policy = load_asset_policy()

    assert policy.crop_mode == "cover"
    assert policy.allow_stretch is False
    assert set(policy.required_provenance) == {"source", "license", "retrieved_at"}
    assert policy.missing_asset_fallback == "native-editable-composition"


def test_asset_choice_is_deterministic_and_rejects_missing_provenance() -> None:
    intent = AssetIntent(kind="photo", style="editorial", aspect_ratio=16 / 9)
    records = (
        AssetRecord(
            id="missing",
            kind="photo",
            style="editorial",
            aspect_ratio=16 / 9,
            quality=100,
            source=None,
            license="CC0",
            retrieved_at="2026-07-20",
            width_px=2400,
            height_px=1600,
        ),
        AssetRecord(
            id="valid-b",
            kind="photo",
            style="editorial",
            aspect_ratio=1.5,
            quality=90,
            source="https://example.test/b",
            license="CC0",
            retrieved_at="2026-07-20",
            width_px=2400,
            height_px=1600,
        ),
        AssetRecord(
            id="valid-a",
            kind="photo",
            style="editorial",
            aspect_ratio=16 / 9,
            quality=90,
            source="https://example.test/a",
            license="CC0",
            retrieved_at="2026-07-20",
            width_px=3200,
            height_px=1800,
        ),
    )

    choice = choose_asset(intent, records)

    assert choice.asset_id == "valid-a"
    assert choice.crop_mode == "cover"
    assert choice.fallback is None
    assert choice.rejected["missing"] == "MISSING_PROVENANCE"


def test_asset_choice_uses_editable_fallback_when_no_safe_asset_exists() -> None:
    choice = choose_asset(AssetIntent(kind="icon"), ())

    assert choice.asset_id is None
    assert choice.fallback == "native-editable-composition"
    assert choice.reason == "NO_SAFE_ASSET"


def test_asset_choice_rejects_non_finite_quality_and_blank_provenance() -> None:
    intent = AssetIntent(kind="photo", aspect_ratio=16 / 9)
    records = (
        AssetRecord(
            id="nan",
            kind="photo",
            style=None,
            aspect_ratio=16 / 9,
            quality=math.nan,
            source="https://example.test/nan",
            license="CC0",
            retrieved_at="2026-07-20",
            width_px=1920,
            height_px=1080,
        ),
        AssetRecord(
            id="blank",
            kind="photo",
            style=None,
            aspect_ratio=16 / 9,
            quality=100,
            source=" ",
            license=" ",
            retrieved_at=" ",
            width_px=1920,
            height_px=1080,
        ),
    )

    choice = choose_asset(intent, records)

    assert choice.asset_id is None
    assert choice.rejected == {
        "blank": "MISSING_PROVENANCE",
        "nan": "INVALID_QUALITY",
    }


def test_icon_choice_enforces_one_family_per_deck() -> None:
    records = (
        AssetRecord(
            id="outline-home",
            kind="icon",
            style="outline",
            aspect_ratio=1,
            quality=90,
            source="internal://icons/outline/home",
            license="brand-owned",
            retrieved_at="2026-07-20",
            icon_family="outline-v1",
        ),
        AssetRecord(
            id="filled-home",
            kind="icon",
            style="filled",
            aspect_ratio=1,
            quality=99,
            source="internal://icons/filled/home",
            license="brand-owned",
            retrieved_at="2026-07-20",
            icon_family="filled-v1",
        ),
    )

    choice = choose_asset(
        AssetIntent(kind="icon"), records, active_icon_family="outline-v1"
    )

    assert choice.asset_id == "outline-home"
    assert choice.icon_family == "outline-v1"
    assert choice.rejected["filled-home"] == "ICON_FAMILY_MISMATCH"


def test_asset_session_locks_icon_family_after_first_selection() -> None:
    outline = AssetRecord(
        id="outline-home",
        kind="icon",
        style="outline",
        aspect_ratio=1,
        quality=90,
        source="internal://icons/outline/home",
        license="brand-owned",
        retrieved_at="2026-07-20",
        icon_family="outline-v1",
    )
    filled = replace(
        outline,
        id="filled-home",
        style="filled",
        quality=99,
        source="internal://icons/filled/home",
        icon_family="filled-v1",
    )
    session = AssetSession()

    assert session.choose(AssetIntent(kind="icon"), (outline,)).asset_id == outline.id
    second = session.choose(AssetIntent(kind="icon"), (filled, outline))

    assert session.icon_family == "outline-v1"
    assert second.asset_id == outline.id
    assert second.rejected[filled.id] == "ICON_FAMILY_MISMATCH"


def test_duplicate_asset_ids_are_rejected_independent_of_input_order() -> None:
    base = AssetRecord(
        id="duplicate",
        kind="icon",
        style="outline",
        aspect_ratio=1,
        quality=90,
        source="internal://icons/outline/home",
        license="brand-owned",
        retrieved_at="2026-07-20",
        icon_family="outline-v1",
    )
    duplicate = replace(base, source="internal://icons/outline/other")

    first = choose_asset(AssetIntent(kind="icon"), (base, duplicate))
    second = choose_asset(AssetIntent(kind="icon"), (duplicate, base))

    assert first == second
    assert first.asset_id is None
    assert first.rejected == {"duplicate": "DUPLICATE_ID"}


def test_runtime_registry_gate_checks_exact_sets_and_type_minima(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = load_layout_registry()
    themes = load_themes()
    broken_families = dict(registry.families)
    del broken_families["cta"]
    broken_map = dict(registry.semantic_form_map)
    del broken_map["line-chart"]
    broken_theme = themes["executive-light"]
    broken_foundation = dict(broken_theme.foundation)
    broken_foundation["typography"] = {
        **broken_foundation["typography"],
        "body": 8,
    }
    broken_themes = {
        **themes,
        "executive-light": replace(broken_theme, foundation=broken_foundation),
    }
    monkeypatch.setattr(
        layouts_module,
        "load_layout_registry",
        lambda: replace(
            registry,
            families=broken_families,
            semantic_form_map=broken_map,
        ),
    )
    monkeypatch.setattr(layouts_module, "load_themes", lambda: broken_themes)

    assert {issue.code for issue in validate_registry_bundle()} >= {
        "FAMILY_SET",
        "SEMANTIC_FORM_SET",
        "THEME_TYPOGRAPHY",
    }


def test_legacy_templates_are_quarantined_from_recommendation() -> None:
    templates = load_legacy_templates()

    assert len(templates) == 4
    assert all(template.status == "legacy_unverified" for template in templates)
    assert all(template.auto_recommend is False for template in templates)
    assert all(template.path.endswith(".pptx") for template in templates)


def test_all_design_registries_are_utf8_json() -> None:
    for name in ("themes", "components", "layouts", "legacy-templates"):
        payload = json.loads(
            (SKILL_ROOT / "registries" / f"{name}.json").read_text(encoding="utf-8")
        )
        assert payload["schema_version"] == "1.0"
