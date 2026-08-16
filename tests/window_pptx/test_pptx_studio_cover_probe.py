from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

import pptx_studio.cover_probe as cover_probe  # noqa: E402


def _catalog_and_observations() -> tuple[dict[str, object], dict[str, object], str]:
    candidate_id = "page_aaaaaaaaaaaaaaaaaaaaaaaa_001"
    catalog = {
        "active_categories": ["003-封面模板"],
        "pages": [{
            "page_id": candidate_id,
            "deck_id": "deck_aaaaaaaaaaaaaaaaaaaaaaaa",
            "package_sha256": "a" * 64,
            "slide_number": 1,
            "category": "003-封面模板",
            "render": {"image_sha256": "b" * 64, "visual_quality": 0.9},
            "materialization": {"status": "eligible"},
            "shapes": [{"max_chars": 32}],
        }],
        "regions": [{
            "region_id": "region-cover-title", "page_id": candidate_id,
            "capacity": {"max_text_chars": 32},
        }],
    }
    observations = {candidate_id: {
        "page_id": candidate_id,
        "image_sha256": "b" * 64,
        "observation": {
            "semantic_tags": ["annual-report"], "suggested_roles": ["cover"],
            "visual_style": ["corporate", "blue", "balanced"], "uncertainty": "none",
        },
    }}
    return catalog, observations, candidate_id


def _request(candidate_id: str) -> dict[str, object]:
    return {
        "schema_version": "pptx-studio-cover-probe.v1",
        "candidate_id": candidate_id,
        "suitability": "institutional-finance",
        "facts": [
            {"fact_id": "cover-title", "value": "2026年度工作汇报", "semantic_role": "title"},
            {"fact_id": "department", "value": "财务运营部", "semantic_role": "label"},
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


def test_cover_probe_rejects_a_physically_overlapping_populated_cover(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Capacity alone is insufficient: release QA owns cover eligibility."""

    catalog, observations, candidate_id = _catalog_and_observations()
    _patch_pipeline(monkeypatch, qa={
        "status": "fail",
        "blockers": [{"rule": "text-overlap", "slide": 1}],
    })

    result = cover_probe.probe_cover_candidate(
        catalog, observations=observations, request=_request(candidate_id),
        private_source_root=tmp_path / "private", workspace=tmp_path / "probes",
    )

    assert result == {
        "schema_version": "pptx-studio-cover-probe.v1",
        "status": "NO_MATCH",
        "candidate_id": candidate_id,
        "code": "COVER_PROBE_PHYSICAL_QA_FAILED",
        "evidence": {
            "physical_status": "pass", "qa_status": "fail",
            "blocker_rules": ["text-overlap"],
        },
    }
    assert list((tmp_path / "probes").iterdir()) == []


def test_cover_probe_returns_only_a_safe_locked_anchor_identity(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    catalog, observations, candidate_id = _catalog_and_observations()
    _patch_pipeline(monkeypatch, qa={"status": "pass", "blockers": []})

    result = cover_probe.probe_cover_candidate(
        catalog, observations=observations, request=_request(candidate_id),
        private_source_root=tmp_path / "private", workspace=tmp_path / "probes",
    )

    assert result["status"] == "PASS"
    assert result["locked_anchor_page_id"] == candidate_id
    assert result["evidence"] == {
        "physical_status": "pass", "qa_status": "pass",
        "output_sha256": "c" * 64, "binding_count": 1,
    }
    assert list((tmp_path / "probes").iterdir()) == []


def test_cover_probe_rejects_a_non_cover_before_assembly(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    catalog, observations, candidate_id = _catalog_and_observations()
    catalog["pages"][0]["category"] = "041-二段内容"  # type: ignore[index]
    observations[candidate_id]["observation"]["suggested_roles"] = ["two-item"]  # type: ignore[index]
    _patch_pipeline(monkeypatch, qa={"status": "pass", "blockers": []})

    try:
        cover_probe.probe_cover_candidate(
            catalog, observations=observations, request=_request(candidate_id),
            private_source_root=tmp_path / "private", workspace=tmp_path / "probes",
        )
    except cover_probe.CoverProbeError as exc:
        assert str(exc) == "COVER_PROBE_CANDIDATE_INELIGIBLE"
    else:
        raise AssertionError("an ineligible source page reached physical assembly")
