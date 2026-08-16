from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from run_window_pptx_calibration import (  # noqa: E402
    CALIBRATION_IDS,
    PORTABLE_SLIDE_SIZES,
    _augment_generation,
    _fingerprint,
    _inputs,
    _portable_generation,
    _prepare_calibration_assets,
    _tree_hash,
    load_benchmark_spec,
    load_narrative_rules,
    run_portable,
    verify_sha256_inventory,
    write_sha256_inventory,
)
from window_pptx.benchmark import (  # noqa: E402
    _static_fingerprint_values,
    build_trial_manifest,
)
from window_pptx.brand import discover_installed_fonts  # noqa: E402
from window_pptx.evidence import (  # noqa: E402
    select_portable_slide_pngs,
    validate_portable_slide_pngs,
    write_contact_sheet,
)
from window_pptx.fingerprints import governed_engine_source_paths  # noqa: E402
from window_pptx.layouts import SlideSize  # noqa: E402


def _portable_runtime_ready() -> bool:
    return all(
        shutil.which(command)
        for command in ("node", "libreoffice", "pdfinfo", "pdftoppm")
    ) and (
        SKILL_ROOT
        / "scripts"
        / "node"
        / "node_modules"
        / "pptxgenjs"
        / "package.json"
    ).is_file()


def _write_test_png(path: Path, color: str = "#2563EB") -> Path:
    image_module = pytest.importorskip("PIL.Image")
    path.parent.mkdir(parents=True, exist_ok=True)
    image = image_module.new("RGB", (160, 90), color)
    try:
        image.save(path, format="PNG", optimize=False, compress_level=9)
    finally:
        image.close()
    return path


def test_portable_slide_png_selector_excludes_nonpages_and_other_proofs(
    tmp_path: Path,
) -> None:
    proof = tmp_path / "trial" / "portable-proof"
    first = _write_test_png(proof / "slide-001.png")
    second = _write_test_png(proof / "slide-002.png", "#10B981")
    contact = _write_test_png(proof / "contact-sheet.png", "#111827")
    asset = _write_test_png(tmp_path / "trial" / "assets" / "product.png")
    near_miss = _write_test_png(proof / "slide-02.png")
    other_trial = _write_test_png(
        tmp_path / "other-trial" / "portable-proof" / "slide-001.png"
    )

    selected = select_portable_slide_pngs(
        (contact, second, asset, other_trial, near_miss, first),
        proof_dir=proof,
        expected_count=2,
    )

    assert selected == (first.resolve(), second.resolve())
    assert contact.resolve() not in selected
    assert asset.resolve() not in selected
    assert other_trial.resolve() not in selected


def test_portable_slide_png_validator_rejects_nonpages_gaps_and_bad_pngs(
    tmp_path: Path,
) -> None:
    proof = tmp_path / "declared" / "portable-proof"
    first = _write_test_png(proof / "slide-001.png")
    contact = _write_test_png(proof / "contact-sheet.png")

    with pytest.raises(ValueError, match="non-page"):
        validate_portable_slide_pngs((first, contact), proof_dir=proof)

    gap_proof = tmp_path / "gap" / "portable-proof"
    gap_first = _write_test_png(gap_proof / "slide-001.png")
    gap_third = _write_test_png(gap_proof / "slide-003.png")
    with pytest.raises(ValueError, match="not continuous"):
        select_portable_slide_pngs((gap_first, gap_third), proof_dir=gap_proof)

    bad_proof = tmp_path / "bad" / "portable-proof"
    bad = bad_proof / "slide-001.png"
    bad.parent.mkdir(parents=True)
    bad.write_bytes(b"not a png")
    with pytest.raises(ValueError, match="invalid signature"):
        validate_portable_slide_pngs((bad,), proof_dir=bad_proof)


def test_contact_sheet_is_deterministic_atomic_and_requires_exact_pages(
    tmp_path: Path,
) -> None:
    image_module = pytest.importorskip("PIL.Image")
    proof = tmp_path / "portable-proof"
    pages = (
        _write_test_png(proof / "slide-001.png", "#2563EB"),
        _write_test_png(proof / "slide-002.png", "#10B981"),
        _write_test_png(proof / "slide-003.png", "#F59E0B"),
    )
    first_target = tmp_path / "contact-sheet-a.png"
    second_target = tmp_path / "contact-sheet-b.png"

    assert write_contact_sheet(reversed(pages), first_target) == first_target
    assert write_contact_sheet(pages, second_target) == second_target
    assert first_target.read_bytes() == second_target.read_bytes()
    assert not list(tmp_path.glob(".*.tmp"))
    with image_module.open(first_target) as opened:
        assert opened.format == "PNG"
        assert opened.size == (1512, 338)

    asset_slide = _write_test_png(tmp_path / "assets" / "slide-001.png")
    with pytest.raises(ValueError, match="no portable-proof"):
        write_contact_sheet((asset_slide,), tmp_path / "must-not-exist.png")
    assert not (tmp_path / "must-not-exist.png").exists()


def test_portable_calibration_sizes_cover_wide_standard_and_custom() -> None:
    assert set(PORTABLE_SLIDE_SIZES) == set(CALIBRATION_IDS)
    profiles = {value[0] for value in PORTABLE_SLIDE_SIZES.values()}
    assert profiles == {"16:9", "4:3", "custom"}


def test_calibration_and_benchmark_share_the_governed_engine_source_hash() -> None:
    spec = load_benchmark_spec(SKILL_ROOT / "benchmarks" / "v5")
    manifest = build_trial_manifest(spec)
    governed_sources = list(governed_engine_source_paths(SKILL_ROOT))
    expected = _tree_hash(governed_sources)

    assert _fingerprint(spec)["engine_sha256"] == expected
    assert _static_fingerprint_values(spec, manifest)["engine_sha256"] == expected


def test_sha256_inventory_is_complete_and_verifiable(tmp_path: Path) -> None:
    (tmp_path / "nested").mkdir()
    (tmp_path / "alpha.txt").write_text("alpha\n", encoding="utf-8")
    (tmp_path / "nested" / "beta.bin").write_bytes(b"beta")

    inventory_path = write_sha256_inventory(tmp_path, tmp_path / "sha256-inventory.json")
    payload = json.loads(inventory_path.read_text(encoding="utf-8"))

    assert [item["path"] for item in payload["files"]] == [
        "alpha.txt",
        "nested/beta.bin",
    ]
    assert verify_sha256_inventory(tmp_path, inventory_path) == 2

    (tmp_path / "alpha.txt").write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA256_MISMATCH"):
        verify_sha256_inventory(tmp_path, inventory_path)


def test_portable_calibration_rejects_unknown_or_stale_evidence_before_runtime(
    tmp_path: Path,
) -> None:
    unknown_output = tmp_path / "unknown"
    with pytest.raises(ValueError, match="unknown portable calibration scenarios"):
        run_portable(unknown_output, scenario_ids=("not-a-scenario",))
    assert not unknown_output.exists()

    stale_output = tmp_path / "stale"
    stale_output.mkdir()
    (stale_output / "unmanaged.txt").write_text("preserve me\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="stale evidence mixing"):
        run_portable(stale_output, scenario_ids=("business-report",))
    assert (stale_output / "unmanaged.txt").read_text(encoding="utf-8") == "preserve me\n"


def test_deterministic_augmentations_cover_missing_native_object_classes(
    tmp_path: Path,
) -> None:
    spec = load_benchmark_spec(SKILL_ROOT / "benchmarks" / "v5")
    rules = load_narrative_rules()
    fonts = discover_installed_fonts()
    assets, asset_manifest = _prepare_calibration_assets(tmp_path, CALIBRATION_IDS)
    kinds: set[str] = set()
    notes = 0
    hyperlinks = 0
    evidence = []
    for scenario_id in ("product-launch", "data-analysis"):
        scenario = spec.scenario_by_id(scenario_id)
        facts, brief = _inputs(scenario, rules[scenario_id][0])
        _, width, height = PORTABLE_SLIDE_SIZES[scenario_id]
        slide_size = SlideSize(width, height)
        generation = _portable_generation(
            facts,
            brief,
            slide_size=slide_size,
            fonts=fonts,
        )
        augmented, record = _augment_generation(
            generation,
            scenario_id=scenario_id,
            slide_size=slide_size,
            fonts=fonts,
            asset_bindings=assets,
            asset_manifest=asset_manifest,
        )
        assert record is not None
        assert record["kind"] == "deterministic_calibration_augmentation"
        assert record["model_authored"] is False
        evidence.append(record)
        for slide in augmented.render_plan.slides:
            notes += int(bool(slide.speaker_notes))
            for item in slide.objects:
                kinds.add(item.kind)
                hyperlinks += int(bool(item.hyperlink))

    assert {"chart", "table", "image"} <= kinds
    assert notes > 0
    assert hyperlinks > 0
    assert {item["scenario_id"] for item in evidence} == {
        "product-launch",
        "data-analysis",
    }
    binding = asset_manifest["bindings"]["calibration-asset:product-integrations"]
    assert binding["sha256"]
    assert binding["record"]["source"].startswith("generated:")
    assert binding["record"]["license"] == "CC0-1.0"


@pytest.mark.skipif(
    not _portable_runtime_ready(),
    reason="real portable calibration requires Node, PptxGenJS, LibreOffice, and Poppler",
)
def test_one_real_portable_calibration_packet_passes(tmp_path: Path) -> None:
    output = tmp_path / "portable-calibration"

    manifest = run_portable(
        output,
        scenario_ids=("business-report",),
        verify_determinism=False,
    )

    assert manifest["mode"] == "portable"
    assert manifest["selected_backend"] == "pptxgenjs"
    assert manifest["powerpoint_certification"]["status"] == "NOT_RUN"
    assert manifest["aggregate"]["passed_cases"] == 1
    components = json.loads(
        (output / "fingerprint-components.json").read_text(encoding="utf-8")
    )
    jsonschema = pytest.importorskip("jsonschema")
    fingerprint_schema = json.loads(
        (SKILL_ROOT / "schemas" / "fingerprint-bundle.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    fingerprint_bundle = {
        "schema_version": "1.0",
        "fingerprints": [manifest["fingerprint"]],
        "components": components,
    }
    assert not list(
        jsonschema.Draft202012Validator(fingerprint_schema).iter_errors(
            fingerprint_bundle
        )
    )
    case = manifest["cases"][0]
    assert case["status"] == "PASS"
    assert case["hard_gates"] == {
        "ooxml_semantic": "PASS",
        "libreoffice_pdf": "PASS",
        "poppler_png": "PASS",
        "quality_v2": "PASS",
        "source_integrity": "PASS",
    }
    for relative in (
        "business-report/enhanced/portable.pptx",
        "business-report/enhanced/portable.pdf",
        "business-report/enhanced/contact-sheet.png",
        "business-report/enhanced/ooxml-report.json",
        "business-report/enhanced/quality-report.v2.json",
        "business-report/enhanced/repair-log.v2.json",
        "business-report/manifest.json",
    ):
        assert (output / relative).is_file(), relative
    assert verify_sha256_inventory(output, output / "sha256-inventory.json") > 0


@pytest.mark.skipif(
    not _portable_runtime_ready(),
    reason="real portable calibration requires Node, PptxGenJS, LibreOffice, and Poppler",
)
def test_real_augmented_packets_cover_advanced_objects(tmp_path: Path) -> None:
    output = tmp_path / "portable-advanced-calibration"

    manifest = run_portable(
        output,
        scenario_ids=("product-launch", "data-analysis"),
        verify_determinism=False,
    )

    assert manifest["aggregate"]["passed_cases"] == 2
    assert manifest["aggregate"]["object_kind_counts"]["image"] > 0
    for semantic in ("charts", "tables", "notes", "hyperlinks"):
        assert manifest["aggregate"]["semantic_counts"][semantic] > 0
    augmentation = manifest["deterministic_calibration_augmentation"]
    assert augmentation["model_authored"] is False
    assert augmentation["scenario_ids"] == ["product-launch", "data-analysis"]
    for case in manifest["cases"]:
        record = case["deterministic_calibration_augmentation"]
        assert record["model_authored"] is False
        assert (
            output / case["artifacts"]["deterministic_calibration_augmentation"]
        ).is_file()
        if case["scenario_id"] == "product-launch":
            assert (output / case["artifacts"]["calibration_asset"]).is_file()
    assert verify_sha256_inventory(output, output / "sha256-inventory.json") > 0


@pytest.mark.skipif(
    not _portable_runtime_ready(),
    reason="real portable calibration requires Node, PptxGenJS, LibreOffice, and Poppler",
)
def test_real_training_and_ecommerce_packets_pass_quality_gates(
    tmp_path: Path,
) -> None:
    """Cover the two final-six packets not exercised by the smoke/advanced tests."""

    output = tmp_path / "portable-training-ecommerce-calibration"

    manifest = run_portable(
        output,
        scenario_ids=("training", "ecommerce-marketing"),
        verify_determinism=False,
    )

    assert manifest["aggregate"]["passed_cases"] == 2
    assert manifest["aggregate"]["failed_cases"] == 0
    assert manifest["aggregate"]["portable_hard_gates_passed"] is True
    assert {case["status"] for case in manifest["cases"]} == {"PASS"}
    assert "4:3" in manifest["aggregate"]["slide_size_profiles"]
    assert verify_sha256_inventory(output, output / "sha256-inventory.json") > 0
