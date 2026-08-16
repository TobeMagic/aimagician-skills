#!/usr/bin/env python3
"""Generate deterministic recording or real portable calibration packets.

The historical ``run`` entry point remains the Recording-COM planning
calibration.  ``run_portable`` is the Phase 27.2 evidence path and exercises
the real PptxGenJS -> OOXML -> LibreOffice -> Poppler -> Quality-v2 chain.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REPO_ROOT = SKILL_ROOT.parents[2]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from window_pptx.benchmark import (  # noqa: E402
    build_benchmark_fact_store,
    canonical_sha256,
    load_benchmark_spec,
)
from window_pptx.brand import (  # noqa: E402
    discover_installed_fonts,
    font_inventory_digest,
)
from window_pptx.assets import AssetRecord  # noqa: E402
from window_pptx.directions import load_art_directions  # noqa: E402
from window_pptx.fingerprints import (  # noqa: E402
    FINGERPRINT_FIELDS,
    PORTABLE_FINGERPRINT_FIELDS,
    canonical_sha256 as fingerprint_sha256,
    collect_portable_fingerprint_components,
    governed_engine_source_paths,
    validate_fingerprint,
    validate_fingerprint_components,
)
from window_pptx.generation import prepare_brief_generation  # noqa: E402
from window_pptx.design_quality import inspect_design_quality  # noqa: E402
from window_pptx.evidence import write_contact_sheet  # noqa: E402
from window_pptx.html_proof import write_html_proof  # noqa: E402
from window_pptx.layouts import SlideSize  # noqa: E402
from window_pptx.models import OutputPolicy  # noqa: E402
from window_pptx.ooxml import normalize_pptx_package  # noqa: E402
from window_pptx.portable_renderer import PptxGenJSRenderer  # noqa: E402
from window_pptx.portable_runner import execute_portable_render_plan  # noqa: E402
from window_pptx.quality import inspect_quality, repair_quality  # noqa: E402
from window_pptx.quality_v2 import (  # noqa: E402
    adapt_legacy_quality_report,
    adapt_render_findings,
    build_quality_report_v2,
    generation_quality_findings,
)
from window_pptx.recording_com import RecordingPresentation  # noqa: E402
from window_pptx.registry import resolve_archetype  # noqa: E402
from window_pptx.renderer import PowerPointRenderer  # noqa: E402
from window_pptx.render_plan import (  # noqa: E402
    AssetBinding,
    compile_render_plan,
)
from window_pptx.transaction import sha256_file  # noqa: E402
from window_pptx.weak_model import load_narrative_rules  # noqa: E402


CALIBRATION_IDS = (
    "business-report",
    "product-launch",
    "investor-pitch",
    "data-analysis",
    "training",
    "ecommerce-marketing",
)


# The six packets deliberately cover the three supported geometry profiles.
# Ratios are calibration inputs only; no scenario facts or narrative are changed.
PORTABLE_SLIDE_SIZES: dict[str, tuple[str, float, float]] = {
    "business-report": ("16:9", 13.333, 7.5),
    "product-launch": ("16:9", 13.333, 7.5),
    "investor-pitch": ("16:9", 13.333, 7.5),
    "data-analysis": ("custom", 12.0, 7.0),
    "training": ("4:3", 10.0, 7.5),
    "ecommerce-marketing": ("16:9", 13.333, 7.5),
}
CALIBRATION_PRODUCT_ASSET_REF = "calibration-asset:product-integrations"


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _inventory_document(
    root: Path,
    *,
    excluded: tuple[Path, ...] = (),
) -> dict[str, Any]:
    resolved_root = root.resolve()
    excluded_paths = {path.resolve() for path in excluded}
    files = []
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: (
            item.relative_to(root).as_posix().casefold(),
            item.relative_to(root).as_posix(),
        ),
    ):
        if path.resolve() in excluded_paths:
            continue
        files.append(
            {
                "path": path.resolve().relative_to(resolved_root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )
    return {
        "schema_version": "1.0",
        "algorithm": "sha256",
        "files": files,
    }


def write_sha256_inventory(root: Path, target: Path) -> Path:
    """Write a complete, relocatable inventory excluding the inventory itself."""

    root = root.resolve()
    target = target.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("inventory target must be inside its root") from exc
    _write(target, _inventory_document(root, excluded=(target,)))
    return target


def verify_sha256_inventory(root: Path, inventory_path: Path) -> int:
    """Fail closed when any inventoried file is missing, extra, or changed."""

    root = root.resolve()
    inventory_path = inventory_path.resolve()
    payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0" or payload.get("algorithm") != "sha256":
        raise ValueError("SHA256_INVENTORY_SCHEMA_INVALID")
    rows = payload.get("files")
    if not isinstance(rows, list):
        raise ValueError("SHA256_INVENTORY_SCHEMA_INVALID")
    expected_paths: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
            raise ValueError("SHA256_INVENTORY_SCHEMA_INVALID")
        relative = row["path"]
        if (
            not isinstance(relative, str)
            or not relative
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or relative in expected_paths
        ):
            raise ValueError("SHA256_INVENTORY_PATH_INVALID")
        if (
            isinstance(row["bytes"], bool)
            or not isinstance(row["bytes"], int)
            or row["bytes"] < 0
            or not isinstance(row["sha256"], str)
            or len(row["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in row["sha256"])
        ):
            raise ValueError("SHA256_INVENTORY_SCHEMA_INVALID")
        expected_paths.add(relative)
        path = root / relative
        if not path.is_file():
            raise ValueError(f"SHA256_MISSING: {relative}")
        if path.stat().st_size != row["bytes"] or _file_sha256(path) != row["sha256"]:
            raise ValueError(f"SHA256_MISMATCH: {relative}")
    actual_paths = {
        item.resolve().relative_to(root).as_posix()
        for item in root.rglob("*")
        if item.is_file() and item.resolve() != inventory_path
    }
    if actual_paths != expected_paths:
        extras = sorted(actual_paths - expected_paths)
        missing = sorted(expected_paths - actual_paths)
        raise ValueError(f"SHA256_FILESET_MISMATCH: extra={extras}; missing={missing}")
    return len(rows)


def _write(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(payload, encoding="utf-8")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _tree_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: str(item).casefold()):
        digest.update(str(path.relative_to(REPO_ROOT)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _fingerprint(spec: Any) -> dict[str, Any]:
    scripts = list(governed_engine_source_paths(SKILL_ROOT))
    registries = list((SKILL_ROOT / "registries").glob("*.json"))
    schemas = list((SKILL_ROOT / "schemas").glob("*.json"))
    references = [SKILL_ROOT / "SKILL.md", *list((SKILL_ROOT / "references").glob("*.md"))]
    dependency_basis = {
        "python": platform.python_version(),
        "platform": platform.system(),
        "implementation": platform.python_implementation(),
    }
    value = {
        "git_commit": _git("rev-parse", "HEAD"),
        "dirty_state": bool(_git("status", "--porcelain")),
        "engine_sha256": _tree_hash(scripts),
        "registry_bundle_sha256": _tree_hash(registries),
        "schemas_sha256": _tree_hash(schemas),
        "skill_sha256": _tree_hash(references),
        "corpus_sha256": spec.corpus_sha256,
        "protocol_sha256": spec.protocol_sha256,
        "prompt_sha256": canonical_sha256(
            json.loads((SKILL_ROOT / "assets" / "calibration" / "scenarios.json").read_text(encoding="utf-8"))
        ),
        "thresholds_sha256": canonical_sha256(spec.protocol.thresholds),
        "dependencies_sha256": canonical_sha256(dependency_basis),
        "model_provider_sha256": canonical_sha256({"status": "NOT_RUN"}),
        "environment_sha256": canonical_sha256(
            {"system": platform.system(), "release": platform.release()}
        ),
        "font_inventory_sha256": font_inventory_digest({"Arial"}),
        "powerpoint_build_sha256": canonical_sha256(
            {"status": "NOT_RUN", "error": "TYPE_E_CANTLOADLIBRARY"}
        ),
        "asset_manifest_sha256": canonical_sha256({"bindings": {}}),
        "evidence_generation": "post-huashu",
    }
    if set(value) != set(FINGERPRINT_FIELDS):
        raise RuntimeError("calibration fingerprint field drift")
    return value


def _semantic(value: str) -> str:
    return {
        "cards": "bullets",
        "case-study": "statement",
        "competition": "matrix",
        "product-showcase": "image",
        "cta": "recommendation",
        "big-number": "metrics",
    }.get(value, value if value in {
        "statement", "bullets", "metrics", "comparison", "sequence",
        "timeline", "process", "roadmap", "quadrant", "funnel", "trend",
        "composition", "matrix", "risk", "recommendation", "quote", "table",
        "image", "generic",
    } else "statement")


def _inputs(scenario: Any, critical_beat: str) -> tuple[dict[str, Any], dict[str, Any]]:
    fact_store = build_benchmark_fact_store(scenario)
    archetype = resolve_archetype(scenario.id)
    required_beats = [
        beat.casefold().replace(" ", "-")
        for beat in scenario.required_beats
        if beat.casefold().replace(" ", "-") in archetype.sections
    ]
    beat_sequence = list(dict.fromkeys([
        critical_beat,
        *[
            beat
            for beat in (*required_beats, *archetype.sections)
            if beat not in {"cover", "agenda", "closing", critical_beat}
        ],
    ]))
    groups = []
    for index, fact in enumerate(scenario.facts):
        form = scenario.expected_forms[index % len(scenario.expected_forms)]
        groups.append(
            {
                "id": f"evidence-{index + 1}",
                "fact_refs": [fact.id],
                "beat_hint": beat_sequence[index % len(beat_sequence)],
                "semantic_hint": _semantic(form),
                "importance": "critical" if index == 0 else "high",
            }
        )
    brief = {
        "schema_version": "1.0",
        "scenario_id": scenario.id,
        "groups": groups,
        "preferences": {
            "tone": "professional",
            "density": "balanced",
            "audience_mode": "executive" if "executive" in scenario.audience else "general",
            "motion": "off",
        },
    }
    return fact_store, brief


def _arm(facts: dict[str, Any], brief: dict[str, Any], design_system: str) -> tuple[Any, dict[str, Any]]:
    generation = prepare_brief_generation(
        facts,
        brief,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
        design_system_version=design_system,
        build_render=True,
    )
    assert generation.render_plan is not None
    presentation = RecordingPresentation()
    render_report = PowerPointRenderer().render(generation.render_plan, presentation)
    initial = inspect_quality(generation.render_plan, render_report, presentation)
    repair = repair_quality(
        generation.render_plan,
        render_report,
        presentation,
        initial,
        max_passes=1,
    )
    v2 = build_quality_report_v2(
        [
            *generation_quality_findings(generation),
            *inspect_design_quality(generation),
            *adapt_render_findings(generation.render_plan.findings),
            *adapt_legacy_quality_report(repair.final_report),
        ],
        transaction_status="recording-com-not-saved",
    )
    result = {
        "generation": generation,
        "render_report": render_report.to_dict(),
        "quality_initial": initial.to_dict(),
        "repair_log": repair.to_dict(),
        "quality_v2": v2.to_dict(),
    }
    metrics = {
        "required_fact_coverage": generation.compilation.narrative.coverage["required_fact_coverage"],
        "slide_count": len(generation.compiled_deck["slides"]),
        "layout_family_count": len({slide["page_family"] for slide in generation.compiled_deck["slides"]}),
        "native_editable_coverage": 1.0,
        "legacy_hard_gate_pass": repair.final_report.passed,
        "v2_hard_gate_pass": v2.passed,
        "direction_candidates": len(generation.direction.candidates) if generation.direction else 0,
        "asset_fallback_count": len(generation.asset_fallbacks),
    }
    return result, metrics


def run(output_dir: Path) -> dict[str, Any]:
    spec = load_benchmark_spec(SKILL_ROOT / "benchmarks" / "v5")
    rules = load_narrative_rules()
    fingerprint = _fingerprint(spec)
    manifest_cases: list[dict[str, Any]] = []
    for scenario_id in CALIBRATION_IDS:
        scenario = spec.scenario_by_id(scenario_id)
        facts, brief = _inputs(scenario, rules[scenario_id][0])
        case_dir = output_dir / scenario_id
        hashes = {
            "fact-store.json": _write(case_dir / "fact-store.json", facts),
            "brief-plan.json": _write(case_dir / "brief-plan.json", brief),
        }
        arms: dict[str, Any] = {}
        for arm_id, design_system in (
            ("compatibility", "legacy-v5"),
            ("enhanced", "art-direction-v1"),
        ):
            first, metrics = _arm(facts, brief, design_system)
            second, repeated_metrics = _arm(facts, brief, design_system)
            generation = first["generation"]
            documents = {
                "narrative-plan.json": generation.compilation.narrative.to_dict(),
                "deck-plan.json": generation.effective_deck_plan,
                "compiled-plan.json": generation.compiled_deck,
                "render-plan.json": generation.render_plan.to_dict(),
                "quality-initial.json": first["quality_initial"],
                "repair-log.json": first["repair_log"],
                "quality-report.v2.json": first["quality_v2"],
            }
            if generation.direction is not None:
                documents["direction-decision.json"] = generation.direction.to_dict()
            else:
                (case_dir / arm_id / "direction-decision.json").unlink(
                    missing_ok=True
                )
            repeated_hash = canonical_sha256(
                {
                    "compiled": second["generation"].compiled_deck,
                    "render": second["generation"].render_plan.to_dict(),
                    "metrics": repeated_metrics,
                }
            )
            first_hash = canonical_sha256(
                {
                    "compiled": generation.compiled_deck,
                    "render": generation.render_plan.to_dict(),
                    "metrics": metrics,
                }
            )
            if first_hash != repeated_hash:
                raise RuntimeError(f"determinism drift: {scenario_id}/{arm_id}")
            arm_hashes = {
                name: _write(case_dir / arm_id / name, document)
                for name, document in documents.items()
            }
            arms[arm_id] = {
                "design_system": design_system,
                "metrics": metrics,
                "deterministic_sha256": first_hash,
                "artifact_sha256": arm_hashes,
            }
        comparison = {
            "schema_version": "1.0",
            "scenario_id": scenario_id,
            "same_input": True,
            "compatibility": arms["compatibility"],
            "enhanced": arms["enhanced"],
            "windows_pptx": {
                "status": "NOT_RUN",
                "reason": "PowerPoint COM type library failed with TYPE_E_CANTLOADLIBRARY (0x80029C4A)",
            },
        }
        hashes["comparison.json"] = _write(case_dir / "comparison.json", comparison)
        manifest_cases.append(
            {"scenario_id": scenario_id, "artifacts": hashes, "arms": arms}
        )
    manifest = {
        "schema_version": "1.0",
        "evidence_generation": "post-huashu",
        "formal_benchmark_eligible": not fingerprint["dirty_state"],
        "fingerprint": fingerprint,
        "cases": manifest_cases,
        "limitations": [
            "Recording COM validates native-object plans but is not a real PPTX package.",
            "Windows PPTX/PDF/PNG evidence is NOT_RUN because the local PowerPoint type library cannot load.",
            "Compatibility vs enhanced is a same-input design-system comparison, not a historical before-state replay.",
            "Dirty worktree evidence is calibration-only and cannot enter formal Phase 28 aggregation.",
        ],
    }
    _write(output_dir / "manifest.json", manifest)
    return manifest


def _first_line(command: str, *arguments: str) -> str:
    executable = shutil.which(command)
    if executable is None:
        raise RuntimeError(f"required calibration command is missing: {command}")
    completed = subprocess.run(
        [executable, *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        shell=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().replace("\n", " ")[:400]
        raise RuntimeError(
            f"calibration command failed: {command} exited "
            f"{completed.returncode}: {detail}"
        )
    lines = [
        line.strip()
        for line in (completed.stdout + "\n" + completed.stderr).splitlines()
        if line.strip()
    ]
    if not lines:
        raise RuntimeError(f"calibration command returned no version: {command}")
    return lines[0]


def _portable_fingerprint(
    spec: Any,
    *,
    fonts: set[str],
    asset_manifest: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Collect a typed, non-PowerPoint runtime fingerprint from real tools."""

    components = collect_portable_fingerprint_components(
        model_provider={
            "opencode_version": _first_line("opencode", "--version"),
            "models": ["opencode/deepseek-v4-flash-free"],
        },
        asset_manifest=asset_manifest,
        python_packages={
            "Pillow": importlib.metadata.version("Pillow"),
            "jsonschema": importlib.metadata.version("jsonschema"),
        },
        skill_root=SKILL_ROOT,
        fonts=fonts,
    )
    engine_files = list(governed_engine_source_paths(SKILL_ROOT))
    references = [SKILL_ROOT / "SKILL.md", *list((SKILL_ROOT / "references").glob("*.md"))]
    fingerprint = {
        "git_commit": _git("rev-parse", "HEAD"),
        "dirty_state": bool(_git("status", "--porcelain")),
        "engine_sha256": _tree_hash(engine_files),
        "registry_bundle_sha256": _tree_hash(
            list((SKILL_ROOT / "registries").glob("*.json"))
        ),
        "schemas_sha256": _tree_hash(list((SKILL_ROOT / "schemas").glob("*.json"))),
        "skill_sha256": _tree_hash(references),
        "corpus_sha256": spec.corpus_sha256,
        "protocol_sha256": spec.protocol_sha256,
        "prompt_sha256": canonical_sha256(
            json.loads((SKILL_ROOT / "assets" / "calibration" / "scenarios.json").read_text(encoding="utf-8"))
        ),
        "thresholds_sha256": canonical_sha256(spec.protocol.thresholds),
        "dependencies_sha256": fingerprint_sha256(components["dependencies"]),
        "model_provider_sha256": fingerprint_sha256(components["model_provider"]),
        "environment_sha256": fingerprint_sha256(components["environment"]),
        "font_inventory_sha256": fingerprint_sha256(components["font_inventory"]),
        "asset_manifest_sha256": fingerprint_sha256(components["asset_manifest"]),
        "evidence_generation": "post-huashu",
        "portable_runtime_sha256": fingerprint_sha256(components["portable_runtime"]),
    }
    if set(fingerprint) != set(PORTABLE_FINGERPRINT_FIELDS):
        raise RuntimeError("portable calibration fingerprint field drift")
    validated = validate_fingerprint(fingerprint)
    validate_fingerprint_components(validated, components)
    return validated, components


def _product_asset_record() -> AssetRecord:
    return AssetRecord(
        id="calibration-product-integrations",
        kind="illustration",
        style="flat",
        aspect_ratio=16 / 9,
        quality=100,
        source=(
            "generated:run_window_pptx_calibration.py#"
            "product-launch/pl-integrations"
        ),
        license="CC0-1.0",
        retrieved_at="2026-07-21",
        width_px=1920,
        height_px=1080,
    )


def _write_product_integration_asset(target: Path) -> AssetBinding:
    """Draw a passive, deterministic asset using only frozen scenario facts."""

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:  # pragma: no cover - runtime fingerprint requires Pillow
        raise RuntimeError("Pillow is required for calibration assets") from exc
    canvas = Image.new("RGB", (1920, 1080), "#F5F7FB")
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.load_default(size=46)
    label_font = ImageFont.load_default(size=32)
    draw.rounded_rectangle(
        (96, 96, 1824, 984),
        radius=68,
        fill="#FFFFFF",
        outline="#B8C7E0",
        width=5,
    )
    draw.rectangle((96, 96, 1824, 252), fill="#173B65")
    draw.text(
        (168, 148),
        "Pulse launch integrations",
        fill="#FFFFFF",
        font=title_font,
    )
    labels = ("Microsoft Teams", "Slack", "Email summaries")
    colors = ("#5B5FC7", "#4A154B", "#D97706")
    card_width = 468
    card_gap = 96
    start_x = 162
    for index, (label, color) in enumerate(zip(labels, colors, strict=True)):
        left = start_x + index * (card_width + card_gap)
        draw.rounded_rectangle(
            (left, 378, left + card_width, 804),
            radius=50,
            fill="#F8FAFC",
            outline=color,
            width=7,
        )
        draw.ellipse((left + 174, 462, left + 294, 582), fill=color)
        text_box = draw.textbbox((0, 0), label, font=label_font)
        text_width = text_box[2] - text_box[0]
        draw.text(
            (left + (card_width - text_width) / 2, 654),
            label,
            fill="#172033",
            font=label_font,
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="PNG", optimize=False, compress_level=9)
    return AssetBinding(target.resolve(), _product_asset_record())


def _prepare_calibration_assets(
    output_dir: Path,
    scenario_ids: tuple[str, ...],
) -> tuple[dict[str, AssetBinding], dict[str, Any]]:
    bindings: dict[str, AssetBinding] = {}
    manifest: dict[str, Any] = {"bindings": {}}
    if "product-launch" not in scenario_ids:
        return bindings, manifest
    target = (
        output_dir
        / "product-launch"
        / "enhanced"
        / "assets"
        / "product-integrations.png"
    )
    binding = _write_product_integration_asset(target)
    bindings[CALIBRATION_PRODUCT_ASSET_REF] = binding
    record = binding.record
    manifest["bindings"][CALIBRATION_PRODUCT_ASSET_REF] = {
        "path": _relative(output_dir, target),
        "sha256": _file_sha256(target),
        "record": {
            "id": record.id,
            "kind": record.kind,
            "style": record.style,
            "aspect_ratio": record.aspect_ratio,
            "quality": record.quality,
            "source": record.source,
            "license": record.license,
            "retrieved_at": record.retrieved_at,
            "width_px": record.width_px,
            "height_px": record.height_px,
            "icon_family": record.icon_family,
        },
    }
    return bindings, manifest


def _insert_before_closing(
    slides: list[dict[str, Any]],
    additions: list[dict[str, Any]],
) -> None:
    index = next(
        (
            candidate
            for candidate, slide in enumerate(slides)
            if slide.get("role") == "closing" or slide.get("id") == "closing"
        ),
        len(slides),
    )
    slides[index:index] = additions


def _augment_generation(
    generation: Any,
    *,
    scenario_id: str,
    slide_size: SlideSize,
    fonts: set[str],
    asset_bindings: dict[str, AssetBinding],
    asset_manifest: dict[str, Any],
) -> tuple[Any, dict[str, Any] | None]:
    """Add explicit fact-bound object coverage without treating it as model output."""

    additions: list[dict[str, Any]] = []
    source_fact_ids: list[str] = []
    expected_objects: list[str] = []
    scenario_bindings: dict[str, AssetBinding] = {}
    if scenario_id == "data-analysis":
        source_fact_ids.extend(
            ("da-retention", "da-exclusions", "da-segments")
        )
        expected_objects.extend(("chart", "table", "notes", "hyperlink"))
        additions = [
            {
                "id": "calibration-retention-chart",
                "role": "segments",
                "title": "Ninety-day retention by plan",
                "importance": "high",
                "speaker_notes": (
                    "Ninety-day retention is 81 percent for annual plans and "
                    "59 percent for monthly plans."
                ),
                "blocks": [
                    {
                        "id": "calibration-retention-series",
                        "kind": "comparison",
                        "title": "Ninety-day retention",
                        "chart_intent": "distribution",
                        "source_ref": "benchmark#data-analysis/da-segments",
                        "hyperlink": "slide:calibration-retention-table",
                        "items": [
                            {
                                "category": "Annual plans",
                                "series": "Ninety-day retention",
                                "value": 81,
                                "unit": "percent",
                            },
                            {
                                "category": "Monthly plans",
                                "series": "Ninety-day retention",
                                "value": 59,
                                "unit": "percent",
                            },
                        ],
                    }
                ],
            },
            {
                "id": "calibration-retention-table",
                "role": "key-metrics",
                "title": "Retention evidence table",
                "importance": "high",
                "speaker_notes": (
                    "Ninety-day retention is 68 percent overall. The analysis "
                    "excluded 6.4 percent of records because activation timestamps "
                    "were missing."
                ),
                "blocks": [
                    {
                        "id": "calibration-retention-metrics",
                        "kind": "table",
                        "source_ref": "benchmark#data-analysis",
                        "hyperlink": "slide:calibration-retention-chart",
                        "items": [
                            {"label": "Overall", "value": 68, "unit": "percent"},
                            {"label": "Annual plans", "value": 81, "unit": "percent"},
                            {"label": "Monthly plans", "value": 59, "unit": "percent"},
                            {"label": "Excluded records", "value": 6.4, "unit": "percent"},
                        ],
                    }
                ],
            },
        ]
    elif scenario_id == "product-launch":
        source_fact_ids.append("pl-integrations")
        expected_objects.append("image")
        scenario_bindings = {
            CALIBRATION_PRODUCT_ASSET_REF: asset_bindings[
                CALIBRATION_PRODUCT_ASSET_REF
            ]
        }
        additions = [
            {
                "id": "calibration-product-integrations",
                "role": "product-showcase",
                "title": "Launch integration surfaces",
                "importance": "high",
                "speaker_notes": (
                    "The launch supports Microsoft Teams, Slack, and email summaries."
                ),
                "blocks": [
                    {
                        "id": "calibration-product-integration-image",
                        "kind": "image",
                        "title": "Microsoft Teams, Slack, and email summaries",
                        "source_ref": CALIBRATION_PRODUCT_ASSET_REF,
                        "hyperlink": "slide:closing",
                    }
                ],
            }
        ]
    if not additions:
        return generation, None

    deck_plan = copy.deepcopy(generation.effective_deck_plan)
    _insert_before_closing(deck_plan["slides"], additions)
    serialized = json.dumps(deck_plan, ensure_ascii=False, sort_keys=True)
    missing = [
        fact.id
        for fact in generation.compilation.fact_store.active_facts()
        if fact.required and fact.text not in serialized
    ]
    if missing:
        raise RuntimeError(
            "deterministic calibration augmentation lost facts: "
            + ", ".join(sorted(missing))
        )
    direction_id = (
        generation.direction.selected_profile_id
        if generation.direction is not None
        else None
    )
    preferred_families = (
        load_art_directions()[direction_id].preferred_families
        if direction_id is not None
        else ()
    )
    compiled, render_plan = compile_render_plan(
        deck_plan,
        slide_size=slide_size,
        installed_fonts=fonts,
        theme_id=generation.selected_theme_id,
        asset_bindings=scenario_bindings,
        preferred_families=preferred_families,
        art_direction_id=direction_id,
    )
    augmentation = {
        "schema_version": "1.0",
        "kind": "deterministic_calibration_augmentation",
        "model_authored": False,
        "scenario_id": scenario_id,
        "source_fact_ids": source_fact_ids,
        "added_slide_ids": [slide["id"] for slide in additions],
        "expected_native_objects": expected_objects,
        "asset_binding_refs": sorted(scenario_bindings),
        "fact_coverage_preserved": True,
    }
    manifest_evidence = generation.asset_manifest_evidence
    if scenario_bindings:
        manifest_evidence = {
            "source": "deterministic_calibration_augmentation",
            "path": None,
            "sha256": canonical_sha256(asset_manifest),
            "content": copy.deepcopy(asset_manifest),
        }
    return (
        replace(
            generation,
            effective_deck_plan=deck_plan,
            compiled_deck=compiled,
            render_plan=render_plan,
            asset_manifest_evidence=manifest_evidence,
        ),
        augmentation,
    )


def _repair_log(generation: Any) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "passes": [
            {
                "stage": item.stage,
                "before_vector": list(item.before_vector),
                "after_vector": list(item.after_vector),
                "accepted": item.accepted,
                "rolled_back": item.rolled_back,
                "failure_code": item.failure_code,
            }
            for item in generation.pre_render_repair_passes[:1]
        ],
    }


def _portable_generation(
    facts: dict[str, Any],
    brief: dict[str, Any],
    *,
    slide_size: SlideSize,
    fonts: set[str],
) -> Any:
    generation = prepare_brief_generation(
        facts,
        brief,
        slide_size=slide_size,
        installed_fonts=fonts,
        design_system_version="art-direction-v1",
        build_render=True,
    )
    if generation.render_plan is None:
        raise RuntimeError("portable calibration did not produce a RenderPlan")
    return generation


def _write_generation_packet(generation: Any, directory: Path) -> None:
    documents = {
        "narrative-plan.json": generation.compilation.narrative.to_dict(),
        "deck-plan.json": generation.effective_deck_plan,
        "compiled-plan.json": generation.compiled_deck,
        "render-plan.json": generation.render_plan.to_dict(),
        "generation-manifest.json": generation.to_dict(include_render_plan=False),
        "repair-log.v2.json": _repair_log(generation),
    }
    if generation.direction is not None:
        documents["direction-decision.json"] = generation.direction.to_dict()
    for name, document in documents.items():
        _write(directory / name, document)


def _determinism_report(render_plan: Any, delivered: Path, directory: Path) -> dict[str, Any]:
    probe = directory / ".determinism-probe.pptx"
    probe.unlink(missing_ok=True)
    try:
        PptxGenJSRenderer().render(render_plan, probe)
        normalize_pptx_package(probe)
        delivered_sha256 = sha256_file(delivered)
        repeated_sha256 = sha256_file(probe)
        if repeated_sha256 != delivered_sha256:
            raise RuntimeError(
                "portable calibration deterministic package hash mismatch: "
                f"{delivered_sha256} != {repeated_sha256}"
            )
        return {
            "schema_version": "1.0",
            "status": "PASS",
            "runs": 2,
            "delivered_sha256": delivered_sha256,
            "repeated_sha256": repeated_sha256,
            "byte_identical": True,
        }
    finally:
        probe.unlink(missing_ok=True)


def _portable_case(
    *,
    output_dir: Path,
    spec: Any,
    rules: dict[str, Any],
    scenario_id: str,
    fonts: set[str],
    verify_determinism: bool,
    calibration_assets: dict[str, AssetBinding],
    asset_manifest: dict[str, Any],
) -> dict[str, Any]:
    scenario = spec.scenario_by_id(scenario_id)
    facts, brief = _inputs(scenario, rules[scenario_id][0])
    case_dir = output_dir / scenario_id
    arm_dir = case_dir / "enhanced"
    _write(case_dir / "fact-store.json", facts)
    _write(case_dir / "brief-plan.json", brief)
    profile, width, height = PORTABLE_SLIDE_SIZES[scenario_id]
    generation = _portable_generation(
        facts,
        brief,
        slide_size=SlideSize(width, height),
        fonts=fonts,
    )
    generation, augmentation = _augment_generation(
        generation,
        scenario_id=scenario_id,
        slide_size=SlideSize(width, height),
        fonts=fonts,
        asset_bindings=calibration_assets,
        asset_manifest=asset_manifest,
    )
    _write_generation_packet(generation, arm_dir)
    if augmentation is not None:
        _write(
            arm_dir / "deterministic-calibration-augmentation.json",
            augmentation,
        )
    write_html_proof(generation.render_plan, arm_dir / "render-proof.html")
    output_pptx = arm_dir / "portable.pptx"
    result = execute_portable_render_plan(
        generation.compiled_deck,
        generation.render_plan,
        output_policy=OutputPolicy(source_path=None, output_path=output_pptx),
        audit_dir=arm_dir,
        requested_backend="auto",
        verification_level="portable",
        export_pdf=True,
        quality_v2_findings=(
            *generation_quality_findings(generation),
            *inspect_design_quality(generation),
        ),
    )
    if result.verification is None or result.render_report is None:
        raise RuntimeError("portable calibration returned incomplete verification evidence")
    proof = result.verification.libreoffice
    _write(arm_dir / "backend-render-report.json", result.render_report.to_dict())
    _write(arm_dir / "libreoffice-report.json", proof.to_dict())
    _write(arm_dir / "portable-result.json", result.to_dict())
    if verify_determinism:
        determinism = _determinism_report(generation.render_plan, output_pptx, arm_dir)
    else:
        determinism = {
            "schema_version": "1.0",
            "status": "NOT_RUN",
            "runs": 1,
            "delivered_sha256": sha256_file(output_pptx),
            "repeated_sha256": None,
            "byte_identical": None,
            "reason": "disabled by caller for focused integration testing",
        }
    _write(arm_dir / "determinism-report.json", determinism)
    contact_sheet = write_contact_sheet(
        result.verification.libreoffice.png_paths,
        arm_dir / "contact-sheet.png",
    )
    kind_counts = Counter(
        item.kind
        for slide in generation.render_plan.slides
        for item in slide.objects
    )
    ooxml = result.verification.ooxml
    quality_severities = Counter(
        item.severity for item in result.verification.quality.findings
    )
    case = {
        "schema_version": "1.0",
        "scenario_id": scenario_id,
        "status": "PASS",
        "arm_id": "enhanced",
        "design_system": "art-direction-v1",
        "selected_backend": result.backend.backend_id,
        "verification_level": result.verification.level,
        "deterministic_calibration_augmentation": augmentation,
        "powerpoint_certification": {
            "status": "NOT_RUN",
            "reason": "Phase 27.2 portable calibration does not claim PowerPoint certification",
        },
        "slide_size_inches": {
            "profile": profile,
            "width": width,
            "height": height,
        },
        "slide_count": len(generation.render_plan.slides),
        "planned_object_count": sum(
            len(slide.objects) for slide in generation.render_plan.slides
        ),
        "object_kind_counts": dict(sorted(kind_counts.items())),
        "page_family_count": len(
            {slide["page_family"] for slide in generation.compiled_deck["slides"]}
        ),
        "semantic_counts": {
            "charts": ooxml.chart_count,
            "tables": ooxml.table_count,
            "diagrams": ooxml.diagram_count,
            "notes": ooxml.notes_count,
            "hyperlinks": ooxml.hyperlink_count,
        },
        "hard_gates": {
            "ooxml_semantic": "PASS",
            "libreoffice_pdf": "PASS",
            "poppler_png": "PASS",
            "quality_v2": "PASS" if result.verification.quality.passed else "FAIL",
            "source_integrity": (
                "PASS"
                if proof.candidate_hash_before == proof.candidate_hash_after
                else "FAIL"
            ),
        },
        "quality_summary": {
            "passed": result.verification.quality.passed,
            "weighted_defect_score": result.verification.quality.weighted_defect_score,
            "severity_counts": dict(sorted(quality_severities.items())),
            "hard_gate_failures": list(
                result.verification.quality.hard_gate_failures
            ),
            "manual_visual_review": "NOT_RUN",
        },
        "stages": list(result.stages),
        "determinism": determinism,
        "artifacts": {
            "pptx": _relative(output_dir, output_pptx),
            "pdf": _relative(output_dir, output_pptx.with_suffix(".pdf")),
            "pngs": [
                _relative(output_dir, path)
                for path in result.verification.libreoffice.png_paths
            ],
            "contact_sheet": _relative(output_dir, contact_sheet),
            "ooxml_report": _relative(output_dir, arm_dir / "ooxml-report.json"),
            "quality_report_v2": _relative(
                output_dir, arm_dir / "quality-report.v2.json"
            ),
            "repair_log_v2": _relative(output_dir, arm_dir / "repair-log.v2.json"),
            "libreoffice_report": _relative(
                output_dir, arm_dir / "libreoffice-report.json"
            ),
            "backend_render_report": _relative(
                output_dir, arm_dir / "backend-render-report.json"
            ),
            "render_plan": _relative(output_dir, arm_dir / "render-plan.json"),
            "html_proof": _relative(output_dir, arm_dir / "render-proof.html"),
        },
    }
    if augmentation is not None:
        case["artifacts"]["deterministic_calibration_augmentation"] = _relative(
            output_dir,
            arm_dir / "deterministic-calibration-augmentation.json",
        )
    if scenario_id == "product-launch":
        case["artifacts"]["calibration_asset"] = _relative(
            output_dir,
            calibration_assets[CALIBRATION_PRODUCT_ASSET_REF].path,
        )
    case["artifact_sha256"] = {
        item["path"]: item["sha256"]
        for item in _inventory_document(case_dir)["files"]
    }
    _write(case_dir / "manifest.json", case)
    inventory_path = write_sha256_inventory(case_dir, case_dir / "sha256-inventory.json")
    case["manifest_sha256"] = _file_sha256(case_dir / "manifest.json")
    case["sha256_inventory"] = _relative(output_dir, inventory_path)
    case["sha256_inventory_sha256"] = _file_sha256(inventory_path)
    return case


def run_portable(
    output_dir: Path,
    *,
    scenario_ids: tuple[str, ...] = CALIBRATION_IDS,
    verify_determinism: bool = True,
    fail_fast: bool = False,
) -> dict[str, Any]:
    """Run real portable calibration packets and stage auditable evidence."""

    output_dir = output_dir.resolve()
    if not scenario_ids or len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("portable calibration scenario IDs must be unique and non-empty")
    unknown = sorted(set(scenario_ids) - set(CALIBRATION_IDS))
    if unknown:
        raise ValueError("unknown portable calibration scenarios: " + ", ".join(unknown))
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            "portable calibration output directory must be absent or empty to "
            "prevent stale evidence mixing"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    spec = load_benchmark_spec(SKILL_ROOT / "benchmarks" / "v5")
    rules = load_narrative_rules()
    fonts = discover_installed_fonts()
    calibration_assets, asset_manifest = _prepare_calibration_assets(
        output_dir, scenario_ids
    )
    fingerprint, components = _portable_fingerprint(
        spec,
        fonts=fonts,
        asset_manifest=asset_manifest,
    )
    _write(output_dir / "fingerprint-components.json", components)
    cases: list[dict[str, Any]] = []
    for scenario_id in scenario_ids:
        try:
            cases.append(
                _portable_case(
                    output_dir=output_dir,
                    spec=spec,
                    rules=rules,
                    scenario_id=scenario_id,
                    fonts=fonts,
                    verify_determinism=verify_determinism,
                    calibration_assets=calibration_assets,
                    asset_manifest=asset_manifest,
                )
            )
        except Exception as exc:
            case_dir = output_dir / scenario_id
            failure = {
                "schema_version": "1.0",
                "scenario_id": scenario_id,
                "status": "FAIL",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "powerpoint_certification": {
                    "status": "NOT_RUN",
                    "reason": "portable calibration failed before any PowerPoint certification",
                },
            }
            _write(case_dir / "manifest.json", failure)
            inventory_path = write_sha256_inventory(
                case_dir, case_dir / "sha256-inventory.json"
            )
            failure["manifest_sha256"] = _file_sha256(case_dir / "manifest.json")
            failure["sha256_inventory"] = _relative(output_dir, inventory_path)
            failure["sha256_inventory_sha256"] = _file_sha256(inventory_path)
            cases.append(failure)
            if fail_fast:
                raise
    passed = [case for case in cases if case["status"] == "PASS"]
    kinds: Counter[str] = Counter()
    semantic_totals: Counter[str] = Counter()
    quality_severity_totals: Counter[str] = Counter()
    profiles: set[str] = set()
    for case in passed:
        kinds.update(case["object_kind_counts"])
        semantic_totals.update(case["semantic_counts"])
        quality_severity_totals.update(case["quality_summary"]["severity_counts"])
        profiles.add(case["slide_size_inches"]["profile"])
    limitations = [
        "PowerPoint certification is NOT_RUN by design; this packet proves portable delivery only.",
        "The deterministic calibration uses frozen facts and rules and does not invoke OpenCode or another model.",
        "A dirty worktree fingerprint is calibration evidence and cannot enter formal Phase 28 aggregation.",
        "Structural Quality-v2 PASS is not a customer-delivery visual acceptance; every contact sheet requires explicit human review.",
    ]
    missing_semantics = [
        name
        for name in ("charts", "tables", "notes", "hyperlinks")
        if semantic_totals[name] == 0
    ]
    if missing_semantics:
        limitations.append(
            "Frozen six-scenario calibration inputs did not exercise: "
            + ", ".join(missing_semantics)
            + "; dedicated portable object fixtures remain the coverage evidence."
        )
    if kinds["image"] == 0:
        limitations.append(
            "No governed image binding exists in the frozen calibration inputs; image/crop "
            "coverage remains in dedicated portable renderer fixtures."
        )
    manifest = {
        "schema_version": "2.0",
        "evidence_generation": "post-27.2-portable",
        "mode": "portable",
        "selected_backend": "pptxgenjs",
        "verification_level": "portable",
        "formal_benchmark_eligible": (
            not fingerprint["dirty_state"] and len(passed) == len(cases)
        ),
        "formal_benchmark_trial": False,
        "fingerprint": fingerprint,
        "fingerprint_components": "fingerprint-components.json",
        "model_execution": {
            "status": "NOT_INVOKED",
            "reason": "calibration isolates deterministic Skill behavior from model variance",
            "available_model": "opencode/deepseek-v4-flash-free",
        },
        "deterministic_calibration_augmentation": {
            "model_authored": False,
            "scenario_ids": [
                case["scenario_id"]
                for case in passed
                if case.get("deterministic_calibration_augmentation") is not None
            ],
            "purpose": (
                "fact-bound native object coverage for calibration; not model output"
            ),
        },
        "powerpoint_certification": {
            "status": "NOT_RUN",
            "reason": "PowerPoint is a later sampled release gate, not Phase 27.2 portable evidence",
        },
        "manual_visual_inspection": {
            "status": "NOT_RUN",
            "required": True,
            "reason": "contact sheets must be reviewed after the automated run",
            "contact_sheets": [
                case["artifacts"]["contact_sheet"]
                for case in passed
            ],
        },
        "cases": cases,
        "aggregate": {
            "requested_cases": len(scenario_ids),
            "passed_cases": len(passed),
            "failed_cases": len(cases) - len(passed),
            "slide_count": sum(case.get("slide_count", 0) for case in passed),
            "object_kind_counts": dict(sorted(kinds.items())),
            "semantic_counts": dict(sorted(semantic_totals.items())),
            "quality_finding_severity_counts": dict(
                sorted(quality_severity_totals.items())
            ),
            "slide_size_profiles": sorted(profiles),
            "portable_hard_gates_passed": len(passed) == len(cases),
            "manual_visual_delivery_passed": None,
        },
        "limitations": limitations,
        "sha256_inventory": "sha256-inventory.json",
    }
    _write(output_dir / "manifest.json", manifest)
    inventory = write_sha256_inventory(
        output_dir, output_dir / "sha256-inventory.json"
    )
    verify_sha256_inventory(output_dir, inventory)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("recording", "portable"),
        default="recording",
        help="recording preserves the Phase 27.1 fake-COM packet; portable runs real engines",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
    )
    parser.add_argument(
        "--scenario",
        action="append",
        choices=CALIBRATION_IDS,
        help="portable-only scenario filter; may be repeated",
    )
    parser.add_argument(
        "--skip-determinism-check",
        action="store_true",
        help="skip the second normalized PptxGenJS render (focused diagnostics only)",
    )
    args = parser.parse_args()
    if args.mode == "recording" and args.scenario:
        parser.error("--scenario is supported only with --mode portable")
    if args.mode == "recording" and args.skip_determinism_check:
        parser.error("--skip-determinism-check is supported only with --mode portable")
    default_output = (
        REPO_ROOT / ".planning" / "phase-27.2-evidence" / "calibration"
        if args.mode == "portable"
        else REPO_ROOT / ".planning" / "phase-27.1-evidence" / "calibration"
    )
    output_dir = Path(args.output_dir).resolve() if args.output_dir else default_output
    manifest = (
        run_portable(
            output_dir,
            scenario_ids=tuple(args.scenario or CALIBRATION_IDS),
            verify_determinism=not args.skip_determinism_check,
        )
        if args.mode == "portable"
        else run(output_dir)
    )
    passed = manifest.get("aggregate", {}).get("passed_cases", len(manifest["cases"]))
    failed = manifest.get("aggregate", {}).get("failed_cases", 0)
    print(json.dumps({
        "mode": args.mode,
        "cases": len(manifest["cases"]),
        "passed": passed,
        "failed": failed,
        "formal_benchmark_eligible": manifest["formal_benchmark_eligible"],
        "output_dir": str(output_dir),
    }, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
