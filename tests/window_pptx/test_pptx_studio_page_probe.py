from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

import pptx_studio.cover_probe as cover_probe  # noqa: E402


def _catalog_and_observations() -> tuple[dict[str, object], dict[str, object], str]:
    candidate_id = "page_bbbbbbbbbbbbbbbbbbbbbbbb_001"
    catalog = {
        "active_categories": ["049-时间轴图"],
        "pages": [{
            "page_id": candidate_id,
            "deck_id": "deck_bbbbbbbbbbbbbbbbbbbbbbbb",
            "package_sha256": "a" * 64,
            "slide_number": 1,
            "category": "049-时间轴图",
            "render": {"image_sha256": "b" * 64, "visual_quality": 0.9},
            "materialization": {"status": "eligible"},
            "shapes": [{"max_chars": 64}],
        }],
        "regions": [{
            "region_id": "region-timeline-title", "page_id": candidate_id,
            "capacity": {"max_text_chars": 64},
        }],
    }
    observations = {candidate_id: {
        "page_id": candidate_id,
        "image_sha256": "b" * 64,
        "observation": {
            "semantic_tags": ["annual_work_plan"], "suggested_roles": ["timeline"],
            "visual_style": ["corporate", "blue", "balanced"], "uncertainty": "none",
        },
    }}
    return catalog, observations, candidate_id


def _request(candidate_id: str, *, role: str = "timeline") -> dict[str, object]:
    return {
        "schema_version": "pptx-studio-page-probe.v1",
        "candidate_id": candidate_id,
        "role": role,
        "suitability": "institutional-finance",
        "minimum_capacity": 2,
        "facts": [
            {"fact_id": "title", "value": "项目实施路径", "semantic_role": "title"},
            {"fact_id": "m1-date", "value": "2026年9月", "semantic_role": "label"},
            {"fact_id": "m1-action", "value": "完成数据底座建设", "semantic_role": "body"},
        ],
    }


def _patch_pipeline(monkeypatch, *, qa: dict[str, object]) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cover_probe, "compile_composition", lambda *args, **kwargs: {"status": "PASS"})
    monkeypatch.setattr(cover_probe, "preflight_native_slots", lambda *args, **kwargs: {"status": "PASS"})
    monkeypatch.setattr(cover_probe, "compile_outline_bindings", lambda *args, **kwargs: {
        "schema_version": "1.0", "facts": [], "assets": [], "bindings": [], "structured_data": [],
    })
    monkeypatch.setattr(cover_probe, "compile_adaptation", lambda *args, **kwargs: {
        "status": "PASS", "operations": [{"operation": "replace_text"}],
    })
    monkeypatch.setattr(
        cover_probe,
        "assemble_from_plans",
        lambda *args, **kwargs: (SimpleNamespace(status="pass"), {"qa": qa, "output_sha256": "c" * 64}),
    )


def test_page_probe_returns_disposable_physical_evidence(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    catalog, observations, candidate_id = _catalog_and_observations()
    _patch_pipeline(monkeypatch, qa={"status": "pass", "blockers": []})

    result = cover_probe.probe_page_candidate(
        catalog, observations=observations, request=_request(candidate_id),
        private_source_root=tmp_path / "private", workspace=tmp_path / "probes",
    )

    assert result["status"] == "PASS"
    assert result["candidate_id"] == candidate_id
    assert result["role"] == "timeline"
    assert result["evidence"] == {
        "physical_status": "pass", "qa_status": "pass",
        "output_sha256": "c" * 64, "binding_count": 1,
    }
    assert list((tmp_path / "probes").iterdir()) == []


def test_page_probe_rejects_failed_physical_qa(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    catalog, observations, candidate_id = _catalog_and_observations()
    _patch_pipeline(monkeypatch, qa={"status": "fail", "blockers": [{"rule": "text-overlap"}]})

    result = cover_probe.probe_page_candidate(
        catalog, observations=observations, request=_request(candidate_id),
        private_source_root=tmp_path / "private", workspace=tmp_path / "probes",
    )

    assert result == {
        "schema_version": "pptx-studio-page-probe.v1", "status": "NO_MATCH",
        "candidate_id": candidate_id, "role": "timeline", "code": "PAGE_PROBE_PHYSICAL_QA_FAILED",
        "evidence": {
            "physical_status": "pass", "qa_status": "fail", "blocker_rules": ["text-overlap"],
            "physical_checks": {
                "opc_integrity": "not_available", "editability": "not_available",
                "style_cluster": "not_available", "authority": "not_available",
                "selection_authority": "not_available", "source_residue": "not_available",
                "libreoffice": "not_available", "size": "not_available",
            },
            "physical_summary": {
                "acceptance_profile": "not_available", "target_slide_count": "not_available",
                "lineage_record_count": 0, "lineage_statuses": [],
                "lineage_gates": [],
                "duplicate_page_record_count": 0,
            },
        },
    }
    assert list((tmp_path / "probes").iterdir()) == []


def test_page_probe_rejects_structural_roles_before_assembly(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    catalog, observations, candidate_id = _catalog_and_observations()
    _patch_pipeline(monkeypatch, qa={"status": "pass", "blockers": []})

    try:
        cover_probe.probe_page_candidate(
            catalog, observations=observations, request=_request(candidate_id, role="cover"),
            private_source_root=tmp_path / "private", workspace=tmp_path / "probes",
        )
    except cover_probe.CoverProbeError as exc:
        assert str(exc) == "PAGE_PROBE_ROLE_INVALID"
    else:
        raise AssertionError("a structural page reached physical assembly")
