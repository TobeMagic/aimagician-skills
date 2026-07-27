from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from window_pptx.backends import BackendSelection, backend_capabilities  # noqa: E402
from window_pptx.fingerprints import (  # noqa: E402
    FINGERPRINT_COMPONENT_FIELDS,
    FINGERPRINT_FIELDS,
    PINNED_PPTXGENJS_VERSION,
    PORTABLE_FINGERPRINT_COMPONENT_FIELDS,
    PORTABLE_FINGERPRINT_FIELDS,
    canonical_sha256,
    collect_environment_manifest,
    collect_font_inventory_manifest,
    collect_portable_fingerprint_components,
    collect_portable_runtime_manifest,
    governed_engine_source_paths,
    validate_fingerprint,
    validate_fingerprint_bundle,
    validate_fingerprint_components,
    validate_portable_runtime_manifest,
)
from window_pptx.libreoffice import LibreOfficeVerificationResult  # noqa: E402
from window_pptx.ooxml import OoxmlSemanticReport  # noqa: E402
from window_pptx.portable_renderer import BackendRenderResult  # noqa: E402
from window_pptx.portable_runner import VerificationResult  # noqa: E402
from window_pptx.quality_v2 import QualityReportV2  # noqa: E402
from window_pptx.transaction import sha256_file  # noqa: E402


def _base_fingerprint(fields: tuple[str, ...]) -> dict[str, object]:
    result: dict[str, object] = {}
    for field in fields:
        if field == "git_commit":
            result[field] = "1" * 40
        elif field == "dirty_state":
            result[field] = False
        elif field == "evidence_generation":
            result[field] = "post-huashu"
        elif field.endswith("_sha256"):
            result[field] = "a" * 64
        else:  # pragma: no cover - catches public-contract drift
            raise AssertionError(field)
    return result


def _legacy_components() -> dict[str, object]:
    return {
        "dependencies": {"python": "3.12.0", "packages": {}},
        "model_provider": {
            "opencode_version": "1.0.0",
            "models": ["provider/model"],
        },
        "environment": {
            "system": "Windows",
            "release": "11",
            "locale": "en-US",
        },
        "font_inventory": {"fonts": ["Arial"]},
        "powerpoint_build": {"version": "16.0.18025.20160"},
        "asset_manifest": {"bindings": {}},
    }


def _portable_components(runtime: dict[str, object]) -> dict[str, object]:
    return {
        "dependencies": {"python": "3.12.0", "packages": {}},
        "model_provider": {
            "opencode_version": "1.0.0",
            "models": ["deepseek/deepseek-v4-flash-free"],
        },
        "environment": {
            "system": "Linux",
            "release": "6.6.0",
            "machine": "x86_64",
            "locale": "C.UTF-8",
        },
        "font_inventory": {"fonts": ["Arial", "Noto Sans CJK SC"]},
        "portable_runtime": runtime,
        "asset_manifest": {"bindings": {}},
    }


def _certified_powerpoint_component() -> dict[str, object]:
    return {
        "version": "16.0.20131.20154",
        "status": "passed",
        "certification_evidence_sha256": "b" * 64,
        "candidate_sha256": "c" * 64,
        "pdf_sha256": "d" * 64,
        "png_sha256": ["e" * 64],
        "process_ownership": "hwnd-pid-bound",
    }


def _bind(
    fingerprint: dict[str, object],
    components: dict[str, object],
    mapping: dict[str, str],
) -> dict[str, object]:
    result = dict(fingerprint)
    for component, hash_field in mapping.items():
        if component in components:
            result[hash_field] = canonical_sha256(components[component])
    return result


def _schema_errors(schema_name: str, value: object) -> list[str]:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((SKILL_ROOT / "schemas" / schema_name).read_text())
    return [
        error.message
        for error in jsonschema.Draft202012Validator(schema).iter_errors(value)
    ]


def test_governed_engine_sources_cover_python_node_worker_and_package_manifests(
    tmp_path: Path,
) -> None:
    skill_root = tmp_path / "window-pptx"
    source_files = {
        "scripts/run.py": "print('runner')\n",
        "scripts/window_pptx/core.py": "VALUE = 1\n",
        "scripts/node/window_pptx_worker.mjs": "export const worker = true;\n",
        "scripts/node/secondary.mjs": "export const secondary = true;\n",
        "scripts/node/package.json": "{}\n",
        "scripts/node/package-lock.json": "{}\n",
        "scripts/node/ignored.js": "throw new Error('not governed');\n",
        "scripts/node/node_modules/vendor.py": "VALUE = 'ignored'\n",
        "scripts/node/node_modules/vendor.mjs": "export default 'ignored';\n",
    }
    for relative, contents in source_files.items():
        path = skill_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")

    governed = governed_engine_source_paths(skill_root)
    relative_paths = tuple(path.relative_to(skill_root).as_posix() for path in governed)

    assert relative_paths == (
        "scripts/node/package-lock.json",
        "scripts/node/package.json",
        "scripts/node/secondary.mjs",
        "scripts/node/window_pptx_worker.mjs",
        "scripts/run.py",
        "scripts/window_pptx/core.py",
    )
    assert all("node_modules" not in path.parts for path in governed)


def test_legacy_fingerprint_profile_and_schema_remain_compatible() -> None:
    components = _legacy_components()
    fingerprint = _bind(
        _base_fingerprint(FINGERPRINT_FIELDS),
        components,
        FINGERPRINT_COMPONENT_FIELDS,
    )

    assert validate_fingerprint(fingerprint) == fingerprint
    assert validate_fingerprint_components(fingerprint, components) == components
    bundle = {
        "schema_version": "1.0",
        "fingerprints": [fingerprint],
        "components": components,
    }
    assert not _schema_errors("fingerprint-bundle.v1.schema.json", bundle)

def test_real_portable_runtime_fingerprint_records_every_required_engine() -> None:
    runtime = collect_portable_runtime_manifest(skill_root=SKILL_ROOT)

    assert runtime["node"]["version"]  # type: ignore[index]
    assert runtime["npm"]["version"]  # type: ignore[index]
    assert runtime["pptxgenjs"]["version"] == PINNED_PPTXGENJS_VERSION  # type: ignore[index]
    assert "LibreOffice" in runtime["libreoffice"]["version"]  # type: ignore[index]
    if "poppler" in runtime:
        assert "pdfinfo" in runtime["poppler"]["pdfinfo_version"]  # type: ignore[index]
        assert "pdftoppm" in runtime["poppler"]["pdftoppm_version"]  # type: ignore[index]
    else:
        assert runtime["ghostscript"]["version"]  # type: ignore[index]
        assert runtime["ghostscript"]["executable"]  # type: ignore[index]
    environment = collect_environment_manifest()
    assert all(environment[field] for field in ("system", "release", "machine", "locale"))
    assert collect_font_inventory_manifest(["Arial", "Arial", " Noto Sans "]) == {
        "fonts": ["Arial", "Noto Sans"]
    }


def test_portable_profile_does_not_require_powerpoint_and_is_schema_valid() -> None:
    runtime = collect_portable_runtime_manifest(skill_root=SKILL_ROOT)
    components = _portable_components(runtime)
    fingerprint = _bind(
        _base_fingerprint(PORTABLE_FINGERPRINT_FIELDS),
        components,
        PORTABLE_FINGERPRINT_COMPONENT_FIELDS,
    )

    assert "powerpoint_build_sha256" not in fingerprint
    assert "powerpoint_build" not in components
    assert validate_fingerprint_components(fingerprint, components) == components
    assert validate_fingerprint_bundle((fingerprint, fingerprint)) == fingerprint
    bundle = {
        "schema_version": "1.0",
        "fingerprints": [fingerprint],
        "components": components,
    }
    assert not _schema_errors("fingerprint-bundle.v1.schema.json", bundle)

    mismatched_bundle = {
        **bundle,
        "components": {
            **components,
            "powerpoint_build": _certified_powerpoint_component(),
        },
    }
    assert _schema_errors("fingerprint-bundle.v1.schema.json", mismatched_bundle)


def test_portable_powerpoint_fingerprint_requires_hash_bound_pass_evidence() -> None:
    runtime = collect_portable_runtime_manifest(skill_root=SKILL_ROOT)
    components = _portable_components(runtime)
    components["powerpoint_build"] = _certified_powerpoint_component()
    mapping = {
        **PORTABLE_FINGERPRINT_COMPONENT_FIELDS,
        "powerpoint_build": "powerpoint_build_sha256",
    }
    fingerprint = _bind(
        {
            **_base_fingerprint(PORTABLE_FINGERPRINT_FIELDS),
            "powerpoint_build_sha256": "a" * 64,
        },
        components,
        mapping,
    )

    assert validate_fingerprint_components(fingerprint, components) == components
    bundle = {
        "schema_version": "1.0",
        "fingerprints": [fingerprint],
        "components": components,
    }
    assert not _schema_errors("fingerprint-bundle.v1.schema.json", bundle)

    uncertified = {
        **components,
        "powerpoint_build": {"version": "16.0.20131.20154"},
    }
    uncertified_fingerprint = {
        **fingerprint,
        "powerpoint_build_sha256": canonical_sha256(
            uncertified["powerpoint_build"]
        ),
    }
    with pytest.raises(ValueError, match="passed certification evidence"):
        validate_fingerprint_components(uncertified_fingerprint, uncertified)


def test_portable_fingerprint_collector_requires_real_powerpoint_proof_files(
    tmp_path: Path,
) -> None:
    common = {
        "model_provider": {
            "opencode_version": "1.0.0",
            "models": ["opencode/deepseek-v4-flash-free"],
        },
        "asset_manifest": {"bindings": {}},
        "python_packages": {},
        "skill_root": SKILL_ROOT,
        "fonts": ["Arial"],
    }
    invalid_evidence = {
        "powerpoint_version": "16.0",
        "pdf_path": str(tmp_path / "missing.pdf"),
        "png_paths": [str(tmp_path / "missing.png")],
        "candidate_hash_before": "a" * 64,
        "candidate_hash_after": "a" * 64,
        "owned_pid": 4242,
    }
    with pytest.raises(ValueError, match="proof files are incomplete"):
        collect_portable_fingerprint_components(
            **common,
            powerpoint_certification=invalid_evidence,
        )

    pdf = tmp_path / "proof.pdf"
    png = tmp_path / "proof.png"
    pdf.write_bytes(b"%PDF-1.7\nproof")
    png.write_bytes(b"\x89PNG\r\n\x1a\nproof")
    evidence = {
        **invalid_evidence,
        "pdf_path": str(pdf),
        "png_paths": [str(png)],
    }
    components = collect_portable_fingerprint_components(
        **common,
        powerpoint_certification=evidence,
    )
    powerpoint = components["powerpoint_build"]
    assert powerpoint == {
        "version": "16.0",
        "status": "passed",
        "certification_evidence_sha256": canonical_sha256(evidence),
        "candidate_sha256": "a" * 64,
        "pdf_sha256": sha256_file(pdf),
        "png_sha256": [sha256_file(png)],
        "process_ownership": "hwnd-pid-bound",
    }
    assert powerpoint["pdf_sha256"] != powerpoint["png_sha256"][0]


def test_portable_fingerprint_rejects_missing_or_mixed_runtime_evidence() -> None:
    runtime = collect_portable_runtime_manifest(skill_root=SKILL_ROOT)
    components = _portable_components(runtime)
    fingerprint = _bind(
        _base_fingerprint(PORTABLE_FINGERPRINT_FIELDS),
        components,
        PORTABLE_FINGERPRINT_COMPONENT_FIELDS,
    )

    without_runtime = {key: value for key, value in components.items() if key != "portable_runtime"}
    with pytest.raises(ValueError, match="manifests are incomplete"):
        validate_fingerprint_components(fingerprint, without_runtime)
    legacy = _bind(
        _base_fingerprint(FINGERPRINT_FIELDS),
        _legacy_components(),
        FINGERPRINT_COMPONENT_FIELDS,
    )
    with pytest.raises(ValueError, match="mixed fingerprint bundle"):
        validate_fingerprint_bundle((fingerprint, legacy))

    wrong_version = {
        **runtime,
        "pptxgenjs": {**runtime["pptxgenjs"], "version": "4.0.0"},
    }
    with pytest.raises(ValueError, match="requires PptxGenJS 4.0.1"):
        validate_portable_runtime_manifest(wrong_version)


def test_backend_and_verification_public_results_match_versioned_schemas(
    tmp_path: Path,
) -> None:
    selection = BackendSelection(
        "pptxgenjs",
        backend_capabilities("pptxgenjs"),
        ("master_layout", "native_text"),
    ).to_dict()
    render = BackendRenderResult(
        backend_id="pptxgenjs",
        backend_version="4.0.1",
        output_path=tmp_path / "delivery.pptx",
        slide_count=1,
        planned_object_count=1,
        native_editable_count=1,
        diagram_child_count=0,
        object_names=("headline",),
        group_names=(),
        warnings=(),
    ).to_dict()
    sha = "c" * 64
    verification = VerificationResult(
        level="portable",
        ooxml=OoxmlSemanticReport(1, ("headline",), 0, 0, 0, 0, 0, 12),
        libreoffice=LibreOfficeVerificationResult(
            "LibreOffice 25.2.3.2",
            "pdfinfo version 26.02.0",
            1,
            960.0,
            540.0,
            tmp_path / "proof.pdf",
            (tmp_path / "slide-001.png",),
            sha,
            sha,
        ),
        quality=QualityReportV2("2.0", (), (), 0, True, "portable-pre-promotion"),
    ).to_dict()

    assert not _schema_errors("backend-selection.v1.schema.json", selection)
    assert not _schema_errors("backend-render-result.v1.schema.json", render)
    assert not _schema_errors(
        "portable-verification-result.v1.schema.json", verification
    )
