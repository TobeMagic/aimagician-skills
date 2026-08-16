from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import validate


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from manage_pptx_studio_library import run  # noqa: E402
from pptx_studio.narrative import NarrativeError, validate_narrative_plan  # noqa: E402


def _brief() -> dict[str, object]:
    return {
        "schema_version": "pptx-studio-brief-normalized.v1",
        "brief_id": "hospital-upgrade-2026",
        "audience": "医院院务会",
        "purpose": "决策是否立项",
        "delivery_context": "15分钟立项汇报",
        "facts": [
            {"fact_id": "f-investment", "value": "预计投入 1,800 万元"},
            {"fact_id": "f-efficiency", "value": "结算周期预计缩短 30%"},
        ],
        "assets": [],
        "constraints": ["保持专业医疗金融气质"],
        "assumptions": ["无额外品牌手册"],
    }


def _beat(
    beat_id: str,
    kind: str,
    *,
    section_id: str | None = None,
    facts: list[str] | None = None,
    grammar: str | None = None,
    estimated: int = 0,
    capacity: int = 8,
    disposition: str = "keep",
) -> dict[str, object]:
    return {
        "beat_id": beat_id,
        "kind": kind,
        "section_id": section_id,
        "page_intent": f"让受众理解 {beat_id}",
        "key_message": f"{beat_id} 的明确结论",
        "fact_ids": facts or [],
        "grammar": grammar or {"cover": "cover", "contents": "agenda", "section": "section", "body": "kpi", "closing": "closing"}[kind],
        "density": "balanced",
        "estimated_units": estimated,
        "capacity_units": capacity,
        "disposition": disposition,
    }


def _plan() -> dict[str, object]:
    return {
        "schema_version": "pptx-studio-narrative-plan.v1",
        "brief_id": "hospital-upgrade-2026",
        "style_intent": {
            "industry": "医疗财务",
            "audience_tone": "审慎专业",
            "visual_tone": "现代可信",
            "brand_constraints": "蓝绿低饱和",
        },
        "beats": [
            _beat("cover", "cover"),
            _beat("agenda", "contents"),
            _beat("section-value", "section", section_id="value"),
            _beat("value-kpi", "body", section_id="value", facts=["f-efficiency"], estimated=4),
            _beat("investment", "body", section_id="value", facts=["f-investment"], grammar="comparison", estimated=4),
            _beat("closing", "closing"),
        ],
        "fact_coverage": [
            {"fact_id": "f-investment", "disposition": "used", "reason": "支撑立项投入决策"},
            {"fact_id": "f-efficiency", "disposition": "used", "reason": "支撑项目收益结论"},
        ],
    }


def test_narrative_derives_count_without_a_fixed_slide_count() -> None:
    result = validate_narrative_plan(_brief(), _plan())

    assert result["status"] == "PASS"
    assert result["slide_count"] == 6
    assert result["delivery_beat_ids"] == ["cover", "agenda", "section-value", "value-kpi", "investment", "closing"]
    assert "slide_count" not in _plan()

    for schema_name, payload in (
        ("pptx-studio-brief-normalized.v1.schema.json", _brief()),
        ("pptx-studio-narrative-plan.v1.schema.json", _plan()),
    ):
        schema = json.loads((SKILL_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
        validate(payload, schema)


def test_narrative_rejects_section_without_nearby_evidence() -> None:
    plan = _plan()
    plan["beats"][3]["section_id"] = "another-section"  # type: ignore[index]
    plan["beats"][4]["section_id"] = "another-section"  # type: ignore[index]

    with pytest.raises(NarrativeError, match="SECTION_EVIDENCE_REQUIRED:section-value"):
        validate_narrative_plan(_brief(), plan)


def test_narrative_rejects_over_capacity_body_without_split() -> None:
    plan = _plan()
    plan["beats"][3]["estimated_units"] = 9  # type: ignore[index]
    plan["beats"][3]["capacity_units"] = 8  # type: ignore[index]

    with pytest.raises(NarrativeError, match="BEAT_CAPACITY_SPLIT_REQUIRED:value-kpi"):
        validate_narrative_plan(_brief(), plan)


def test_narrative_cli_emits_a_stable_validation_report(tmp_path: Path) -> None:
    brief_path = tmp_path / "brief.normalized.json"
    plan_path = tmp_path / "narrative-plan.json"
    output_path = tmp_path / "narrative-validation.json"
    brief_path.write_text(json.dumps(_brief(), ensure_ascii=False), encoding="utf-8")
    plan_path.write_text(json.dumps(_plan(), ensure_ascii=False), encoding="utf-8")

    result = run([
        "validate-narrative",
        "--source-root", str(tmp_path / "source.sentinel"),
        "--archive-root", str(tmp_path / "archive.sentinel"),
        "--manifest", str(tmp_path / "manifest.sentinel"),
        "--brief-normalized", str(brief_path),
        "--narrative-input", str(plan_path),
        "--narrative-output", str(output_path),
    ])

    assert result["status"] == "PASS"
    assert json.loads(output_path.read_text(encoding="utf-8"))["slide_count"] == 6


def test_hospital_upgrade_acceptance_brief_derives_its_own_count() -> None:
    fixture_root = SKILL_ROOT / "evals" / "v7-hospital-finance-upgrade"
    result = validate_narrative_plan(
        json.loads((fixture_root / "brief.normalized.json").read_text(encoding="utf-8")),
        json.loads((fixture_root / "narrative-plan.json").read_text(encoding="utf-8")),
    )

    assert result["slide_count"] == len(result["delivery_beat_ids"])
    assert result["slide_count"] == 14
    assert result["delivery_beat_ids"][2:5] == [
        "section-current", "current-pressure", "current-friction",
    ]
