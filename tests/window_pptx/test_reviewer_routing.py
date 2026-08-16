from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from window_pptx.reviewer_routing import (  # noqa: E402
    DEFAULT_CODE_REVIEWER,
    ReviewerCapabilityProbe,
    ReviewerRoutingError,
    require_visual_review_evidence,
    select_reviewer,
)


def test_visual_review_prefers_agnes_after_successful_image_probe() -> None:
    route = select_reviewer(
        "visual-pixel-uat",
        [
            ReviewerCapabilityProbe(
                model_id="agnes/agnes-2.0-flash",
                image_input=True,
                evidence="attached PNG decoded successfully",
            )
        ],
    )

    assert route.status == "ready"
    assert route.selected_model == "agnes/agnes-2.0-flash"
    require_visual_review_evidence(route, has_readable_pngs=True)


@pytest.mark.parametrize("image_input", [False, None])
def test_visual_review_fails_closed_when_agnes_cannot_read_images(
    image_input: bool | None,
) -> None:
    route = select_reviewer(
        "visual-pixel-uat",
        [
            ReviewerCapabilityProbe(
                model_id="agnes/agnes-2.0-flash",
                image_input=image_input,
                evidence="OpenCode attachment probe result",
            )
        ],
    )

    assert route.status == "unavailable"
    assert route.selected_model is None
    with pytest.raises(ReviewerRoutingError, match="NOT_RUN"):
        require_visual_review_evidence(route, has_readable_pngs=True)


def test_deepseek_is_never_a_visual_fallback() -> None:
    route = select_reviewer(
        "visual-pixel-uat",
        [
            ReviewerCapabilityProbe(
                model_id=DEFAULT_CODE_REVIEWER,
                image_input=True,
                evidence="forged positive must not override the routing policy",
            )
        ],
        visual_candidates=(DEFAULT_CODE_REVIEWER,),
    )

    assert route.status == "unavailable"
    assert route.selected_model is None
    assert "forbidden" in route.reason


def test_verified_image_capable_fallback_is_allowed() -> None:
    route = select_reviewer(
        "visual-pixel-uat",
        [
            ReviewerCapabilityProbe(
                model_id="agnes/agnes-2.0-flash",
                image_input=False,
                evidence="provider rejected image attachment",
            ),
            ReviewerCapabilityProbe(
                model_id="provider/vision-fallback",
                image_input=True,
                evidence="PNG decoded and described",
            ),
        ],
        visual_candidates=(
            "agnes/agnes-2.0-flash",
            "provider/vision-fallback",
        ),
    )

    assert route.status == "ready"
    assert route.selected_model == "provider/vision-fallback"
    assert route.attempted_models == (
        "agnes/agnes-2.0-flash",
        "provider/vision-fallback",
    )


def test_code_contract_audit_defaults_to_deepseek() -> None:
    route = select_reviewer("code-contract-audit")

    assert route.status == "ready"
    assert route.selected_model == DEFAULT_CODE_REVIEWER
    assert route.requires_image_input is False


def test_visual_review_rejects_json_only_evidence() -> None:
    route = select_reviewer(
        "visual-pixel-uat",
        [
            ReviewerCapabilityProbe(
                model_id="agnes/agnes-2.0-flash",
                image_input=True,
                evidence="image probe passed",
            )
        ],
    )

    with pytest.raises(ReviewerRoutingError, match="readable PNG"):
        require_visual_review_evidence(route, has_readable_pngs=False)
