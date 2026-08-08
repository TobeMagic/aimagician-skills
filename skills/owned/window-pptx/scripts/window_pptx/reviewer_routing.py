"""Fail-closed reviewer routing for code audits and pixel-level visual UAT."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal


ReviewTaskKind = Literal["visual-pixel-uat", "code-contract-audit"]
ReviewRouteStatus = Literal["ready", "unavailable"]

DEFAULT_VISUAL_REVIEWERS = ("agnes/agnes-2.0-flash",)
DEFAULT_CODE_REVIEWER = "opencode/deepseek-v4-flash-free"
TEXT_ONLY_REVIEWERS = frozenset({DEFAULT_CODE_REVIEWER})


class ReviewerRoutingError(ValueError):
    """Raised when review evidence violates the reviewer route contract."""


@dataclass(frozen=True)
class ReviewerCapabilityProbe:
    """Observed provider capability; ``None`` means unknown, never assumed true."""

    model_id: str
    image_input: bool | None
    evidence: str

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ReviewerRoutingError("reviewer probe model_id must not be empty")
        if not self.evidence.strip():
            raise ReviewerRoutingError("reviewer probe evidence must not be empty")


@dataclass(frozen=True)
class ReviewerRoute:
    task_kind: ReviewTaskKind
    status: ReviewRouteStatus
    selected_model: str | None
    attempted_models: tuple[str, ...]
    requires_image_input: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "task_kind": self.task_kind,
            "status": self.status,
            "selected_model": self.selected_model,
            "attempted_models": list(self.attempted_models),
            "requires_image_input": self.requires_image_input,
            "reason": self.reason,
        }


def select_reviewer(
    task_kind: ReviewTaskKind,
    probes: Iterable[ReviewerCapabilityProbe] = (),
    *,
    visual_candidates: tuple[str, ...] = DEFAULT_VISUAL_REVIEWERS,
) -> ReviewerRoute:
    """Select a reviewer without inferring image support from a model name.

    Pixel-level UAT selects only a candidate with an explicit successful
    image-input probe. DeepSeek is intentionally reserved for code/contract
    auditing and cannot be used as a visual fallback.
    """

    if task_kind == "code-contract-audit":
        return ReviewerRoute(
            task_kind=task_kind,
            status="ready",
            selected_model=DEFAULT_CODE_REVIEWER,
            attempted_models=(DEFAULT_CODE_REVIEWER,),
            requires_image_input=False,
            reason="DeepSeek is the default deterministic code and contract auditor.",
        )
    if task_kind != "visual-pixel-uat":
        raise ReviewerRoutingError(f"unsupported review task kind: {task_kind!r}")
    if not visual_candidates:
        raise ReviewerRoutingError("visual reviewer candidates must not be empty")

    probe_by_model = {probe.model_id: probe for probe in probes}
    attempted: list[str] = []
    rejected: list[str] = []
    for model_id in visual_candidates:
        if not model_id.strip():
            raise ReviewerRoutingError("visual reviewer model id must not be empty")
        attempted.append(model_id)
        if model_id in TEXT_ONLY_REVIEWERS:
            rejected.append(f"{model_id}: text-only reviewer is forbidden")
            continue
        probe = probe_by_model.get(model_id)
        if probe is None:
            rejected.append(f"{model_id}: image-input capability is unprobed")
            continue
        if probe.image_input is not True:
            state = "unsupported" if probe.image_input is False else "unknown"
            rejected.append(f"{model_id}: image-input capability is {state}")
            continue
        return ReviewerRoute(
            task_kind=task_kind,
            status="ready",
            selected_model=model_id,
            attempted_models=tuple(attempted),
            requires_image_input=True,
            reason=f"{model_id} passed an explicit image-input capability probe.",
        )

    return ReviewerRoute(
        task_kind=task_kind,
        status="unavailable",
        selected_model=None,
        attempted_models=tuple(attempted),
        requires_image_input=True,
        reason="No visual reviewer passed the image-input probe; "
        + "; ".join(rejected),
    )


def require_visual_review_evidence(
    route: ReviewerRoute,
    *,
    has_readable_pngs: bool,
) -> None:
    """Reject a pixel verdict unless routing and rendered evidence are valid."""

    if route.task_kind != "visual-pixel-uat":
        raise ReviewerRoutingError("pixel verdict requires a visual-pixel-uat route")
    if route.status != "ready" or route.selected_model is None:
        raise ReviewerRoutingError("visual review is unavailable; verdict must remain NOT_RUN")
    if not route.requires_image_input:
        raise ReviewerRoutingError("visual route must require image input")
    if not has_readable_pngs:
        raise ReviewerRoutingError(
            "visual review requires readable PNG evidence, not JSON or PPTX alone"
        )
