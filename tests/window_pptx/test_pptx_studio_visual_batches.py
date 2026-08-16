from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.visual_batches import VisualBatchError, ingest_batch_report, plan_visual_batches, prompt_for_batch  # noqa: E402


def _fixture(tmp_path: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object], Path, Path]:
    private = tmp_path / "private"
    evidence = private / "evidence" / "complete"
    legacy = private / "evidence" / "legacy" / "one.png"
    evidence.mkdir(parents=True)
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(b"one-image")
    image_sha = hashlib.sha256(legacy.read_bytes()).hexdigest()
    package_sha = "a" * 64
    catalog = {
        "catalog_id": "catalog",
        "page_count": 1,
        "pages": [{
            "page_id": "page_" + "a" * 24 + "_001",
            "package_sha256": package_sha,
            "slide_number": 1,
            "render": {"image_sha256": image_sha},
        }],
    }
    assets = {"packages": [{"status": "ACCEPTED", "render_status": "PASS", "package_sha256": package_sha, "rendered_pages": [{"slide_number": 1, "png_path": "evidence/legacy/one.png"}]}]}
    completed = {"pages": {}}
    return catalog, assets, completed, private, evidence


def _agnes_report(_: str, __: str) -> dict[str, str]:
    return {"analysis": json.dumps([{
        "observation": {
            "visual_style": ["editorial"], "composition": "title-first", "hierarchy": "title-first",
            "semantic_tags": ["annual-report"], "suggested_roles": ["cover"],
            "text_density": "low", "uncertainty": "low",
        },
    }])}


def test_plan_prompt_and_ingest_are_hash_bound(tmp_path: Path) -> None:
    catalog, assets, completed, private, evidence = _fixture(tmp_path)
    plan = plan_visual_batches(catalog, asset_index=assets, completion_render_index=completed, private_root=private, completion_evidence_root=evidence)
    assert plan["pending_page_count"] == 1
    assert "private_png_locator" not in prompt_for_batch(plan, batch_index=0)
    item = plan["batches"][0][0]
    result = ingest_batch_report(plan, batch_index=0, report=_agnes_report(item["page_id"], item["image_sha256"]))
    assert result["status"] == "COMPLETE"
    assert result["observation_count"] == 1


def test_plan_fails_when_local_png_hash_does_not_match_catalog(tmp_path: Path) -> None:
    catalog, assets, completed, private, evidence = _fixture(tmp_path)
    catalog["pages"][0]["render"]["image_sha256"] = "b" * 64  # type: ignore[index]
    with pytest.raises(VisualBatchError, match="PNG_EVIDENCE_MISSING"):
        plan_visual_batches(catalog, asset_index=assets, completion_render_index=completed, private_root=private, completion_evidence_root=evidence)


def test_exact_page_reobservation_overrides_matching_existing_hash(tmp_path: Path) -> None:
    catalog, assets, completed, private, evidence = _fixture(tmp_path)
    original = plan_visual_batches(catalog, asset_index=assets, completion_render_index=completed, private_root=private, completion_evidence_root=evidence)
    item = original["batches"][0][0]
    existing = ingest_batch_report(original, batch_index=0, report=_agnes_report(item["page_id"], item["image_sha256"]))

    repaired = plan_visual_batches(
        catalog, asset_index=assets, completion_render_index=completed,
        private_root=private, completion_evidence_root=evidence,
        existing_observations=existing, page_ids=[item["page_id"]],
    )
    assert repaired["pending_page_count"] == 1
    assert repaired["batches"][0][0]["page_id"] == item["page_id"]


def test_exact_page_reobservation_rejects_unknown_or_duplicate_ids(tmp_path: Path) -> None:
    catalog, assets, completed, private, evidence = _fixture(tmp_path)
    page_id = catalog["pages"][0]["page_id"]  # type: ignore[index]
    with pytest.raises(VisualBatchError, match="VISION_PAGE_IDS_INVALID"):
        plan_visual_batches(
            catalog, asset_index=assets, completion_render_index=completed,
            private_root=private, completion_evidence_root=evidence,
            page_ids=["page_" + "b" * 24 + "_001"],
        )
    with pytest.raises(VisualBatchError, match="VISION_PAGE_IDS_INVALID"):
        plan_visual_batches(
            catalog, asset_index=assets, completion_render_index=completed,
            private_root=private, completion_evidence_root=evidence,
            page_ids=[page_id, page_id],
        )


def test_ingest_rejects_model_supplied_identity(tmp_path: Path) -> None:
    catalog, assets, completed, private, evidence = _fixture(tmp_path)
    plan = plan_visual_batches(catalog, asset_index=assets, completion_render_index=completed, private_root=private, completion_evidence_root=evidence)
    item = plan["batches"][0][0]
    report = _agnes_report(item["page_id"], item["image_sha256"])
    payload = json.loads(report["analysis"])
    payload[0]["page_id"] = "page_" + "b" * 24 + "_001"
    report["analysis"] = json.dumps(payload)
    with pytest.raises(VisualBatchError, match="AGNES_RESPONSE_SCHEMA_INVALID"):
        ingest_batch_report(plan, batch_index=0, report=report)


def test_ingest_accepts_a_single_json_fence_but_not_prose(tmp_path: Path) -> None:
    catalog, assets, completed, private, evidence = _fixture(tmp_path)
    plan = plan_visual_batches(catalog, asset_index=assets, completion_render_index=completed, private_root=private, completion_evidence_root=evidence)
    item = plan["batches"][0][0]
    report = _agnes_report(item["page_id"], item["image_sha256"])
    report["analysis"] = "```json\n" + report["analysis"] + "\n```"
    assert ingest_batch_report(plan, batch_index=0, report=report)["status"] == "COMPLETE"
    report["analysis"] = "Here is the result: " + report["analysis"]
    with pytest.raises(VisualBatchError, match="AGNES_REPORT_JSON_INVALID"):
        ingest_batch_report(plan, batch_index=0, report=report)
