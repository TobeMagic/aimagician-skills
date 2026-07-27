"""Reference-grade quality gates and bounded CompositionPlan repair."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .composition_plan import CompositionPlan


VISUAL_HARD_GATE_CODES = {
    "SEMANTIC_COMPONENT_UNMATERIALIZED",
    "ASSET_INTENT_UNMATERIALIZED",
    "EMPTY_PANEL_SHELL",
    "DECK_CONTENT_INK_FLOOR",
    "ART_DIRECTION_NOT_MATERIALIZED",
    "DECORATION_DOMINATES_CONTENT",
    "EVIDENCE_ANNOTATION_COVERAGE_LOW",
    "DECK_CHOREOGRAPHY_FLAT",
}
REGISTERED_REPAIR_CODES = {
    "BIND_NATIVE_COMPONENT",
    "MATERIALIZE_ASSET_FALLBACK",
    "REDUCE_DECORATION",
    "ADD_EVIDENCE_ANNOTATION",
    "VARY_REGISTERED_COMPOSITION",
    "INCREASE_CONTENT_INK",
}
SEVERITY_ORDER = {"blocker": 0, "important": 1, "minor": 2}


@dataclass(frozen=True)
class QualityAxisScores:
    hierarchy_readability: float
    composition_space: float
    art_direction: float
    business_evidence: float
    deck_rhythm: float
    asset_polish: float

    def to_dict(self) -> dict[str, float]:
        return {
            "hierarchy_readability": self.hierarchy_readability,
            "composition_space": self.composition_space,
            "art_direction": self.art_direction,
            "business_evidence": self.business_evidence,
            "deck_rhythm": self.deck_rhythm,
            "asset_polish": self.asset_polish,
        }

    def values(self) -> tuple[float, ...]:
        return tuple(self.to_dict().values())


@dataclass(frozen=True)
class QualityFindingV3:
    code: str
    severity: str
    message: str
    slide_id: str | None = None
    region: str | None = None
    repair_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "slide_id": self.slide_id,
            "region": self.region,
            "repair_code": self.repair_code,
        }


@dataclass(frozen=True)
class QualityReportV3:
    scores: QualityAxisScores
    total_score: float
    findings: tuple[QualityFindingV3, ...]
    engineering_passed: bool
    visual_passed: bool
    art_review_status: str
    art_review_passed: bool
    release_passed: bool
    total_threshold: int = 84
    axis_threshold: int = 75

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "3.0",
            "scores": self.scores.to_dict(),
            "total_score": self.total_score,
            "thresholds": {
                "total": self.total_threshold,
                "axis": self.axis_threshold,
            },
            "findings": [item.to_dict() for item in self.findings],
            "engineering_passed": self.engineering_passed,
            "visual_passed": self.visual_passed,
            "art_review_status": self.art_review_status,
            "art_review_passed": self.art_review_passed,
            "release_passed": self.release_passed,
        }

    def defect_vector(self) -> tuple[int, int, int, int]:
        counts = {
            severity: sum(
                1 for finding in self.findings if finding.severity == severity
            )
            for severity in SEVERITY_ORDER
        }
        return (
            counts["blocker"],
            counts["important"],
            counts["minor"],
            max(0, round(600 - sum(self.scores.values()))),
        )


@dataclass(frozen=True)
class CompositionRepairPass:
    round_index: int
    action: str
    before_vector: tuple[int, int, int, int]
    after_vector: tuple[int, int, int, int]
    accepted: bool
    failure_code: str | None


@dataclass(frozen=True)
class CompositionRepairResult:
    final_plan: CompositionPlan
    final_report: QualityReportV3
    passes: tuple[CompositionRepairPass, ...]


def _validate_scores(scores: QualityAxisScores) -> None:
    if not isinstance(scores, QualityAxisScores) or any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0 <= value <= 100
        for value in scores.values()
    ):
        raise ValueError("Quality v3 scores must be six values between 0 and 100")


def build_quality_report_v3(
    *,
    scores: QualityAxisScores,
    findings: Iterable[QualityFindingV3],
    engineering_passed: bool,
    art_review_status: str,
    total_threshold: int = 84,
    axis_threshold: int = 75,
) -> QualityReportV3:
    _validate_scores(scores)
    if art_review_status not in {"PASS", "FAIL", "NOT_RUN"}:
        raise ValueError("art_review_status must be PASS, FAIL, or NOT_RUN")
    governed_findings = tuple(findings)
    for finding in governed_findings:
        if finding.severity not in SEVERITY_ORDER:
            raise ValueError("Quality v3 finding severity is invalid")
        if (
            finding.repair_code is not None
            and finding.repair_code not in REGISTERED_REPAIR_CODES
        ):
            raise ValueError("Quality v3 repair code is not registered")
    total_score = round(sum(scores.values()) / 6, 2)
    has_visual_hard_gate = any(
        finding.code in VISUAL_HARD_GATE_CODES for finding in governed_findings
    )
    visual_passed = (
        total_score >= total_threshold
        and min(scores.values()) >= axis_threshold
        and not has_visual_hard_gate
    )
    art_review_passed = art_review_status == "PASS"
    return QualityReportV3(
        scores=scores,
        total_score=total_score,
        findings=governed_findings,
        engineering_passed=bool(engineering_passed),
        visual_passed=visual_passed,
        art_review_status=art_review_status,
        art_review_passed=art_review_passed,
        release_passed=(
            bool(engineering_passed) and visual_passed and art_review_passed
        ),
        total_threshold=total_threshold,
        axis_threshold=axis_threshold,
    )


def assess_evidence_bundle_v3(path: Path | str) -> QualityReportV3:
    """Adapt a frozen evidence bundle without pretending old evidence is v3."""

    evidence = Path(path).resolve()
    audits = evidence / ".window-pptx" / "audits"
    quality_v2_path = audits / "quality-report.v2.json"
    asset_plan_path = audits / "asset-plan.json"
    composition_path = audits / "composition-plan.json"
    pptx_files = tuple(evidence.glob("output/*.pptx"))
    try:
        quality_v2 = json.loads(quality_v2_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        quality_v2 = {}
    engineering_passed = bool(quality_v2.get("passed")) and bool(pptx_files)
    findings: list[QualityFindingV3] = []
    if not composition_path.is_file():
        findings.extend(
            (
                QualityFindingV3(
                    "SEMANTIC_COMPONENT_UNMATERIALIZED",
                    "blocker",
                    "The bundle predates CompositionPlan and cannot prove semantic components were rendered.",
                    repair_code="BIND_NATIVE_COMPONENT",
                ),
                QualityFindingV3(
                    "ART_DIRECTION_NOT_MATERIALIZED",
                    "blocker",
                    "The bundle has no executable motif, anchor, or scene-composition evidence.",
                    repair_code="VARY_REGISTERED_COMPOSITION",
                ),
            )
        )
    try:
        asset_plan = json.loads(asset_plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        asset_plan = {}
    planned_assets = [
        asset
        for asset in asset_plan.get("assets", [])
        if asset.get("status") == "planned"
    ]
    if planned_assets:
        findings.append(
            QualityFindingV3(
                "ASSET_INTENT_UNMATERIALIZED",
                "blocker",
                f"{len(planned_assets)} asset intents remain planned with no frozen bytes or native materialization.",
                repair_code="MATERIALIZE_ASSET_FALLBACK",
            )
        )
    decoration_findings = [
        item
        for item in quality_v2.get("findings", [])
        if item.get("code") == "DECORATION_OVERUSE"
    ]
    if decoration_findings:
        findings.append(
            QualityFindingV3(
                "DECORATION_DOMINATES_CONTENT",
                "important",
                f"{len(decoration_findings)} slides exceed the legacy decoration ceiling.",
                repair_code="REDUCE_DECORATION",
            )
        )
    findings.extend(
        (
            QualityFindingV3(
                "EVIDENCE_ANNOTATION_COVERAGE_LOW",
                "important",
                "R2 does not prove page-level visual evidence annotations.",
                repair_code="ADD_EVIDENCE_ANNOTATION",
            ),
            QualityFindingV3(
                "DECK_CHOREOGRAPHY_FLAT",
                "important",
                "R2 has no scored pause/flow/peak choreography contract.",
                repair_code="VARY_REGISTERED_COMPOSITION",
            ),
        )
    )
    return build_quality_report_v3(
        scores=QualityAxisScores(76, 62, 58, 78, 68, 55),
        findings=findings,
        engineering_passed=engineering_passed,
        art_review_status="NOT_RUN",
    )


def inspect_generation_quality_v3(
    generation: Any,
    *,
    art_review_status: str = "NOT_RUN",
    external_scores: QualityAxisScores | None = None,
) -> QualityReportV3:
    """Inspect the executable composition/render seam before release."""

    render_plan = getattr(generation, "render_plan", None)
    composition_plan = getattr(generation, "composition_plan", None)
    if render_plan is None or composition_plan is None:
        return build_quality_report_v3(
            scores=QualityAxisScores(0, 0, 0, 0, 0, 0),
            findings=(
                QualityFindingV3(
                    "SEMANTIC_COMPONENT_UNMATERIALIZED",
                    "blocker",
                    "Generation has no CompositionPlan-backed RenderPlan.",
                    repair_code="BIND_NATIVE_COMPONENT",
                ),
            ),
            engineering_passed=False,
            art_review_status=art_review_status,
        )
    rendered = {slide.source_id: slide for slide in render_plan.slides}
    findings: list[QualityFindingV3] = []
    materialized = 0
    required_total = 0
    required_assets = 0
    materialized_assets = 0
    evidence_pages = 0
    annotated_pages = 0
    motif_pages = 0
    for composition in composition_plan.slides:
        slide = rendered.get(composition.slide_id)
        if slide is None:
            findings.append(
                QualityFindingV3(
                    "SEMANTIC_COMPONENT_UNMATERIALIZED",
                    "blocker",
                    "Composition slide has no rendered page.",
                    slide_id=composition.slide_id,
                    repair_code="BIND_NATIVE_COMPONENT",
                )
            )
            continue
        actual_components = Counter(item.component for item in slide.objects)
        for binding in composition.slot_bindings:
            if not binding.required:
                continue
            required_total += 1
            if actual_components[binding.component_id] > 0:
                materialized += 1
                actual_components[binding.component_id] -= 1
            else:
                findings.append(
                    QualityFindingV3(
                        "SEMANTIC_COMPONENT_UNMATERIALIZED",
                        "blocker",
                        (
                            f"Required {binding.semantic_slot} component "
                            f"{binding.component_id} was not rendered."
                        ),
                        slide_id=composition.slide_id,
                        repair_code="BIND_NATIVE_COMPONENT",
                    )
                )
        for binding in composition.asset_bindings:
            if not binding.required:
                continue
            required_assets += 1
            if binding.status in {
                "resolved",
                "generated",
                "native-materialized",
                "fallback",
            }:
                materialized_assets += 1
            else:
                findings.append(
                    QualityFindingV3(
                        "ASSET_INTENT_UNMATERIALIZED",
                        "blocker",
                        f"Required asset {binding.asset_id} remains {binding.status}.",
                        slide_id=composition.slide_id,
                        repair_code="MATERIALIZE_ASSET_FALLBACK",
                    )
                )
        empty_shells = [
            item
            for item in slide.objects
            if item.component
            in {
                "card",
                "comparison-panel",
                "risk-panel",
                "recommendation-panel",
                "team-member",
            }
            and not (item.text or "").strip()
            and item.advanced is None
        ]
        if empty_shells:
            findings.append(
                QualityFindingV3(
                    "EMPTY_PANEL_SHELL",
                    "blocker",
                    f"{len(empty_shells)} empty panel shells are visible.",
                    slide_id=composition.slide_id,
                    repair_code="BIND_NATIVE_COMPONENT",
                )
            )
        art_objects = [
            item
            for item in slide.objects
            if item.group_id == f"wp_s{slide.index:03d}_art"
        ]
        if composition.motif.motif_id and art_objects:
            motif_pages += 1
        content_objects = [
            item
            for item in slide.objects
            if item not in art_objects
            and item.component not in {"footer", "decoration", "accent"}
        ]
        art_area = sum(item.width * item.height for item in art_objects)
        content_area = sum(item.width * item.height for item in content_objects)
        area_limit = (
            1.5
            if composition.role == "cover"
            else 0.6
            if composition.role in {"closing", "section"}
            else 0.45
        )
        if content_area and art_area / content_area > area_limit:
            findings.append(
                QualityFindingV3(
                    "DECORATION_DOMINATES_CONTENT",
                    "important",
                    (
                        f"Art occupies {art_area / content_area:.2f}x the "
                        "content area."
                    ),
                    slide_id=composition.slide_id,
                    repair_code="REDUCE_DECORATION",
                )
            )
        if composition.fact_refs or composition.derived_fact_refs:
            evidence_pages += 1
            if any(
                item.text
                and (
                    item.text.startswith("EVIDENCE")
                    or item.text.startswith("证据")
                )
                for item in art_objects
            ):
                annotated_pages += 1
    slide_count = max(1, len(composition_plan.slides))
    if motif_pages < len(composition_plan.slides):
        findings.append(
            QualityFindingV3(
                "ART_DIRECTION_NOT_MATERIALIZED",
                "blocker",
                "The Knowledge Wayfinding motif is missing from rendered pages.",
                repair_code="VARY_REGISTERED_COMPOSITION",
            )
        )
    if evidence_pages and annotated_pages / evidence_pages < 0.8:
        findings.append(
            QualityFindingV3(
                "EVIDENCE_ANNOTATION_COVERAGE_LOW",
                "blocker",
                (
                    f"Only {annotated_pages}/{evidence_pages} evidence pages "
                    "materialize a visible evidence tag."
                ),
                repair_code="ADD_EVIDENCE_ANNOTATION",
            )
        )
    layout_count = len({slide.layout_id for slide in render_plan.slides})
    energy_count = len(
        {slide.energy for slide in render_plan.slides if slide.energy}
    )
    if layout_count < 6 or energy_count < 3:
        findings.append(
            QualityFindingV3(
                "DECK_CHOREOGRAPHY_FLAT",
                "blocker",
                (
                    f"Deck uses {layout_count} layouts and {energy_count} "
                    "energy levels."
                ),
                repair_code="VARY_REGISTERED_COMPOSITION",
            )
        )
    semantic_ratio = materialized / max(1, required_total)
    asset_ratio = materialized_assets / max(1, required_assets)
    internal = QualityAxisScores(
        hierarchy_readability=86,
        composition_space=max(55, 88 - len(findings) * 2),
        art_direction=round(70 + 20 * motif_pages / slide_count),
        business_evidence=round(65 + 25 * semantic_ratio),
        deck_rhythm=min(92, 62 + layout_count * 3 + energy_count * 3),
        asset_polish=round(65 + 25 * asset_ratio),
    )
    scores = (
        QualityAxisScores(
            *(
                min(left, right)
                for left, right in zip(
                    internal.values(),
                    external_scores.values(),
                    strict=True,
                )
            )
        )
        if external_scores is not None
        else internal
    )
    return build_quality_report_v3(
        scores=scores,
        findings=findings,
        engineering_passed=True,
        art_review_status=art_review_status,
    )


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _protected_content(plan: CompositionPlan) -> str:
    return _canonical_hash(
        {
            "fact_store_digest": plan.fact_store_digest,
            "slides": [
                {
                    "slide_id": slide.slide_id,
                    "source_slide_ids": slide.source_slide_ids,
                    "fact_refs": slide.fact_refs,
                    "derived_fact_refs": slide.derived_fact_refs,
                }
                for slide in plan.slides
            ],
        }
    )


def execute_composition_repairs(
    initial_plan: CompositionPlan,
    *,
    evaluate: Callable[[CompositionPlan], QualityReportV3],
    recompile: Callable[[CompositionPlan, str, int], CompositionPlan],
    max_rounds: int = 2,
) -> CompositionRepairResult:
    if type(max_rounds) is not int or not 0 <= max_rounds <= 2:
        raise ValueError("CompositionPlan repair allows at most two rounds")
    current_plan = initial_plan
    current_report = evaluate(current_plan)
    protected = _protected_content(initial_plan)
    fingerprints = {_canonical_hash(initial_plan.to_dict())}
    passes: list[CompositionRepairPass] = []
    for round_index in range(1, max_rounds + 1):
        repairable = sorted(
            (
                finding
                for finding in current_report.findings
                if finding.repair_code in REGISTERED_REPAIR_CODES
            ),
            key=lambda item: (
                SEVERITY_ORDER[item.severity],
                item.code,
                item.slide_id or "",
            ),
        )
        if not repairable:
            break
        action = repairable[0].repair_code
        assert action is not None
        before = current_report.defect_vector()
        candidate = recompile(current_plan, action, round_index)
        candidate_fingerprint = _canonical_hash(candidate.to_dict())
        failure_code: str | None = None
        candidate_report = current_report
        if _protected_content(candidate) != protected:
            failure_code = "PROTECTED_CONTENT_CHANGED"
        elif candidate_fingerprint in fingerprints:
            failure_code = "REPEATED_CANDIDATE"
        else:
            candidate_report = evaluate(candidate)
            if candidate_report.defect_vector() >= before:
                failure_code = "DEFECT_VECTOR_NOT_IMPROVED"
        accepted = failure_code is None
        passes.append(
            CompositionRepairPass(
                round_index=round_index,
                action=action,
                before_vector=before,
                after_vector=candidate_report.defect_vector(),
                accepted=accepted,
                failure_code=failure_code,
            )
        )
        if not accepted:
            break
        fingerprints.add(candidate_fingerprint)
        current_plan = candidate
        current_report = candidate_report
        if current_report.release_passed:
            break
    return CompositionRepairResult(
        final_plan=current_plan,
        final_report=current_report,
        passes=tuple(passes),
    )


__all__ = [
    "CompositionRepairPass",
    "CompositionRepairResult",
    "QualityAxisScores",
    "QualityFindingV3",
    "QualityReportV3",
    "REGISTERED_REPAIR_CODES",
    "VISUAL_HARD_GATE_CODES",
    "assess_evidence_bundle_v3",
    "build_quality_report_v3",
    "execute_composition_repairs",
    "inspect_generation_quality_v3",
]
