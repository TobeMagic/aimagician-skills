"""Cross-stage quality findings and bounded two-stage repair."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .quality import QualityGateError, QualityReport, RepairLog


NAMESPACES = ("input", "narrative", "compile", "render", "preview", "package", "editability")
SEVERITIES = ("hard-gate", "critical", "important", "warning", "info")
SEVERITY_WEIGHTS = {"hard-gate": 1000, "critical": 100, "important": 10, "warning": 1, "info": 0}


@dataclass(frozen=True)
class QualityFindingV2:
    namespace: str
    code: str
    severity: str
    slide_id: str | None
    object_id: str | None
    message: str
    path: str | None = None
    metric: float | int | str | None = None
    threshold: float | int | str | None = None
    repairable: bool = False
    source_stage: str | None = None

    def dedupe_key(self) -> tuple[str, str, str, str]:
        return (
            self.namespace,
            self.code,
            self.slide_id or "",
            self.object_id or self.path or "",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "code": self.code,
            "severity": self.severity,
            "slide_id": self.slide_id,
            "object_id": self.object_id,
            "message": self.message,
            "path": self.path,
            "metric": self.metric,
            "threshold": self.threshold,
            "repairable": self.repairable,
            "source_stage": self.source_stage or self.namespace,
        }


@dataclass(frozen=True)
class QualityReportV2:
    schema_version: str
    findings: tuple[QualityFindingV2, ...]
    hard_gate_failures: tuple[str, ...]
    weighted_defect_score: int
    passed: bool
    transaction_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "findings": [item.to_dict() for item in self.findings],
            "hard_gate_failures": list(self.hard_gate_failures),
            "weighted_defect_score": self.weighted_defect_score,
            "passed": self.passed,
            "transaction_status": self.transaction_status,
        }


@dataclass(frozen=True)
class StageRepairPass:
    stage: str
    before_vector: tuple[int, int, int, int, int]
    after_vector: tuple[int, int, int, int, int]
    accepted: bool
    rolled_back: bool
    failure_code: str | None


@dataclass(frozen=True)
class TwoStageRepairResult:
    state: dict[str, Any]
    report: QualityReportV2
    passes: tuple[StageRepairPass, ...]


class QualityV2GateError(QualityGateError):
    """A cross-stage v2 hard gate failed before candidate promotion."""

    def __init__(
        self,
        message: str,
        *,
        quality_report_v2: QualityReportV2,
        legacy_report: QualityReport | None = None,
        repair: RepairLog | None = None,
        artifacts: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message,
            report=legacy_report,
            repair=repair,
            artifacts=artifacts,
        )
        self.quality_report_v2 = quality_report_v2


def build_quality_report_v2(findings: list[QualityFindingV2] | tuple[QualityFindingV2, ...], *, transaction_status: str) -> QualityReportV2:
    unique: dict[tuple[str, str, str, str], QualityFindingV2] = {}
    for item in findings:
        if item.namespace not in NAMESPACES or item.severity not in SEVERITIES:
            raise ValueError("quality v2 finding crossed the registered vocabulary")
        key = item.dedupe_key()
        previous = unique.get(key)
        if previous is None or SEVERITY_WEIGHTS[item.severity] > SEVERITY_WEIGHTS[previous.severity]:
            unique[key] = item
    ordered = tuple(
        sorted(
            unique.values(),
            key=lambda item: (
                -SEVERITY_WEIGHTS[item.severity],
                NAMESPACES.index(item.namespace),
                item.slide_id or "",
                item.object_id or item.path or "",
                item.code,
            ),
        )
    )
    hard = tuple(sorted({item.code for item in ordered if item.severity == "hard-gate"}))
    score = sum(SEVERITY_WEIGHTS[item.severity] for item in ordered)
    return QualityReportV2("2.0", ordered, hard, score, not hard, transaction_status)


def defect_vector(report: QualityReportV2) -> tuple[int, int, int, int, int]:
    counts = {
        severity: sum(item.severity == severity for item in report.findings)
        for severity in SEVERITIES
    }
    return (
        counts["hard-gate"],
        counts["critical"],
        counts["important"],
        counts["warning"],
        report.weighted_defect_score,
    )


RepairFunction = Callable[[dict[str, Any]], tuple[Mapping[str, Any], QualityReportV2]]
ProtectedStateCanonicalizer = Callable[[Mapping[str, Any]], Any]


# These fields describe how protected content is presented, not the content
# itself.  Every other scalar under the repair state is retained in the
# canonical projection, including text, numbers, units, citations and sources.
_REPAIR_MUTABLE_KEYS = frozenset(
    {
        "art_direction_id",
        "asset_fallbacks",
        "background",
        "border",
        "color",
        "corner_radius",
        "fact_digest",
        "fill",
        "font",
        "font_family",
        "font_size",
        "geometry",
        "h",
        "height",
        "kind",
        "layout",
        "layout_id",
        "opacity",
        "page_family",
        "preferred_families",
        "shadow",
        "spacing",
        "stroke",
        "style",
        "theme",
        "theme_id",
        "variant",
        "variant_id",
        "w",
        "width",
        "x",
        "y",
        "z",
        "z_order",
    }
)


def canonicalize_protected_content(state: Mapping[str, Any]) -> Any:
    """Project factual/user-authored content out of a repair state.

    The projection deliberately ignores registered visual and geometry fields,
    while retaining all other scalar values.  Callers with a narrower domain
    model may provide their own canonicalizer to ``execute_two_stage_repair``.
    """

    def project(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                str(key): project(child)
                for key, child in sorted(value.items(), key=lambda item: str(item[0]))
                if str(key) not in _REPAIR_MUTABLE_KEYS
            }
        if isinstance(value, (list, tuple)):
            return [project(child) for child in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        raise TypeError(
            "protected repair state must contain only canonical JSON values"
        )

    return project(state)


def protected_content_digest(
    state: Mapping[str, Any],
    canonicalizer: ProtectedStateCanonicalizer = canonicalize_protected_content,
) -> str:
    """Hash the canonical protected projection for mutation detection."""

    payload = json.dumps(
        canonicalizer(state),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def execute_two_stage_repair(
    *,
    state: Mapping[str, Any],
    initial_report: QualityReportV2,
    pre_render: RepairFunction | None = None,
    post_render: RepairFunction | None = None,
    protected_state_canonicalizer: ProtectedStateCanonicalizer = canonicalize_protected_content,
) -> TwoStageRepairResult:
    """Run at most one pre-render and one post-render repair with rollback."""

    current_state = copy.deepcopy(dict(state))
    current_report = initial_report
    passes: list[StageRepairPass] = []
    immutable_fact_digest = current_state.get("fact_digest")
    immutable_protected_digest = protected_content_digest(
        current_state,
        protected_state_canonicalizer,
    )
    for stage, operation in (("pre-render", pre_render), ("post-render", post_render)):
        if operation is None:
            continue
        before_state = copy.deepcopy(current_state)
        before_report = current_report
        before = defect_vector(before_report)
        try:
            proposed_state_raw, proposed_report = operation(copy.deepcopy(current_state))
            proposed_state = copy.deepcopy(dict(proposed_state_raw))
            if proposed_state.get("fact_digest") != immutable_fact_digest:
                raise ValueError("FACT_MUTATED")
            if protected_content_digest(
                proposed_state,
                protected_state_canonicalizer,
            ) != immutable_protected_digest:
                raise ValueError("PROTECTED_CONTENT_MUTATED")
            after = defect_vector(proposed_report)
            accepted = after < before
            if accepted:
                current_state = proposed_state
                current_report = proposed_report
                passes.append(StageRepairPass(stage, before, after, True, False, None))
            else:
                current_state = before_state
                current_report = before_report
                passes.append(StageRepairPass(stage, before, after, False, True, "NON_MONOTONIC"))
        except Exception as exc:
            current_state = before_state
            current_report = before_report
            passes.append(
                StageRepairPass(stage, before, before, False, True, str(exc) or type(exc).__name__)
            )
    return TwoStageRepairResult(current_state, current_report, tuple(passes))


def adapt_legacy_quality_report(report: Any) -> tuple[QualityFindingV2, ...]:
    """Project the established COM/package inspection into v2 namespaces."""

    editability_codes = {
        "CHART_DATA_MISMATCH",
        "DIAGRAM_NODE_MISMATCH",
        "EDITABLE_COVERAGE_LOW",
        "EDITABLE_TAG_MISSING",
        "NATIVE_OBJECT_MISSING",
        "OBJECT_MISSING",
        "OBJECT_NAME_DRIFT",
        "OBJECT_TAG_DRIFT",
        "TABLE_DATA_MISMATCH",
        "TEXT_CONTENT_MISMATCH",
    }
    layer_namespace = {
        "package": "package",
        "com": "render",
        "geometry": "render",
        "visual": "preview",
        "deck": "preview",
    }
    hard_codes = set(getattr(report, "hard_gate_failures", ()))
    result: list[QualityFindingV2] = []
    for item in getattr(report, "findings", ()):
        severity = (
            "hard-gate"
            if item.code in hard_codes
            else {"critical": "critical", "error": "important", "warning": "warning", "info": "info"}.get(item.severity, "warning")
        )
        result.append(
            QualityFindingV2(
                namespace=(
                    "editability"
                    if item.code in editability_codes
                    else layer_namespace.get(item.layer, "render")
                ),
                code=item.code,
                severity=severity,
                slide_id=item.slide_id,
                object_id=item.object_name,
                message=item.message,
                repairable=item.repairable,
                source_stage=f"legacy-{item.layer}",
            )
        )
    return tuple(result)


def adapt_render_findings(findings: Any) -> tuple[QualityFindingV2, ...]:
    result: list[QualityFindingV2] = []
    for item in findings or ():
        path = str(getattr(item, "path", "")) or None
        slide_id = None
        if path and path.startswith("slides."):
            parts = path.split(".")
            slide_id = parts[1] if len(parts) > 1 else None
        result.append(
            QualityFindingV2(
                namespace="compile",
                code=str(getattr(item, "code", "COMPILE_FINDING")),
                severity="warning",
                slide_id=slide_id,
                object_id=None,
                message=str(getattr(item, "message", "compile finding")),
                path=path,
                repairable=False,
                source_stage="render-plan",
            )
        )
    return tuple(result)


def generation_quality_findings(generation: Any) -> tuple[QualityFindingV2, ...]:
    """Create cross-stage findings from a validated BriefGeneration."""

    result: list[QualityFindingV2] = [
        QualityFindingV2(
            namespace="input",
            code="FACTSTORE_VALIDATED",
            severity="info",
            slide_id=None,
            object_id=None,
            message="immutable FactStore validated with a canonical digest",
            repairable=False,
            source_stage="fact-store",
        )
    ]
    coverage = generation.compilation.narrative.coverage
    ratio = float(coverage.get("required_fact_coverage", 0.0))
    result.append(
        QualityFindingV2(
            namespace="narrative",
            code="REQUIRED_FACT_COVERAGE",
            severity="info" if ratio == 1.0 else "hard-gate",
            slide_id=None,
            object_id=None,
            message="required facts are assigned to the narrative",
            metric=ratio,
            threshold=1.0,
            repairable=False,
            source_stage="narrative-plan",
        )
    )
    for item in generation.brand_findings:
        result.append(
            QualityFindingV2(
                namespace="input",
                code=item.code,
                severity="hard-gate" if item.hard_gate else "warning",
                slide_id=None,
                object_id=item.asset_kind,
                message=item.message,
                repairable=not item.hard_gate,
                source_stage="brand-spec",
            )
        )
    for fallback in generation.asset_fallbacks:
        slide_id = fallback.split(".", 1)[0] if "." in fallback else None
        result.append(
            QualityFindingV2(
                namespace="compile",
                code="ASSET_SAFE_NATIVE_FALLBACK_APPLIED",
                severity="info",
                slide_id=slide_id,
                object_id=None,
                message=fallback,
                repairable=False,
                source_stage="pre-render",
            )
        )
    for rejection in generation.asset_rejections:
        result.append(
            QualityFindingV2(
                namespace="input",
                code="ASSET_BINDING_REJECTED_PRE_LAYOUT",
                severity="warning",
                slide_id=None,
                object_id=None,
                message=rejection,
                repairable=True,
                source_stage="asset-preflight",
            )
        )
    direction = generation.direction
    if direction is not None and direction.fallback_reason is not None:
        result.append(
            QualityFindingV2(
                namespace="compile",
                code="ART_DIRECTION_SAFE_FALLBACK",
                severity="info",
                slide_id=None,
                object_id=direction.selected_profile_id,
                message=direction.fallback_reason,
                repairable=False,
                source_stage="direction-selector",
            )
        )
    return tuple(result)


def write_quality_report_v2(
    report: QualityReportV2,
    directory: Path | str,
) -> str:
    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "quality-report.v2.json"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target_dir,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return str(target)


__all__ = [
    "NAMESPACES", "QualityFindingV2", "QualityReportV2", "QualityV2GateError", "SEVERITIES",
    "StageRepairPass", "TwoStageRepairResult", "build_quality_report_v2",
    "canonicalize_protected_content", "defect_vector", "execute_two_stage_repair",
    "protected_content_digest",
    "adapt_legacy_quality_report", "adapt_render_findings",
    "generation_quality_findings", "write_quality_report_v2",
]
