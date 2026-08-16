"""Discussion-locked project intake for quality-first Window-PPTX authoring.

ProjectBriefPack is the authoritative boundary before narrative planning.  It
keeps client facts, source and rights metadata, presentation decisions, deck
anatomy, and acceptance criteria together under one deterministic lock.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .weak_model import FactStore, WeakModelValidationError, validate_fact_store


SCHEMA_VERSION = "1.0"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_ANATOMY_ROLES = frozenset(
    {"cover", "directory", "section-divider", "closing", "appendix"}
)
ROOT_FIELDS = frozenset(
    {
        "schema_version",
        "brief_id",
        "scenario_id",
        "state",
        "raw_intake",
        "fact_store",
        "assets",
        "audience",
        "goals",
        "timing",
        "brand",
        "slide_budget",
        "anatomy",
        "decisions",
        "prohibitions",
        "rubric",
        "unresolved_questions",
        "lock_sha256",
    }
)
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class BriefValidationError(ValueError):
    """The pack is malformed and cannot be discussed or locked safely."""


class BriefLockError(BriefValidationError):
    """The pack crossed the discussion or integrity boundary."""


class BriefState(str, Enum):
    DRAFT = "Draft"
    NEEDS_DISCUSSION = "NeedsDiscussion"
    LOCKED = "Locked"


@dataclass(frozen=True)
class DiscussionQuestion:
    code: str
    path: str
    prompt: str


@dataclass(frozen=True)
class ProjectBriefPack:
    schema_version: str
    brief_id: str
    scenario_id: str
    state: BriefState
    fact_store: FactStore | None
    questions: tuple[DiscussionQuestion, ...]
    lock_sha256: str | None
    payload: dict[str, Any]

    @property
    def formal_ready(self) -> bool:
        return (
            self.state is BriefState.LOCKED
            and not self.questions
            and self.lock_sha256 is not None
        )


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _lock_material(payload: Mapping[str, Any]) -> dict[str, Any]:
    material = copy.deepcopy(dict(payload))
    material["state"] = BriefState.LOCKED.value
    material["lock_sha256"] = None
    return material


def project_brief_digest(payload: Mapping[str, Any]) -> str:
    """Return the digest for the normalized authoritative locked material."""

    try:
        canonical = _canonical_json(_lock_material(payload))
    except (TypeError, ValueError) as exc:
        raise BriefValidationError(f"BRIEF_NOT_CANONICAL: {exc}") from exc
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _question(
    questions: list[DiscussionQuestion],
    code: str,
    path: str,
    prompt: str,
) -> None:
    questions.append(DiscussionQuestion(code=code, path=path, prompt=prompt))


def _non_empty_text(
    value: Any,
    *,
    path: str,
    code: str,
    prompt: str,
    questions: list[DiscussionQuestion],
) -> str | None:
    if not isinstance(value, str) or not value.strip():
        _question(questions, code, path, prompt)
        return None
    return value.strip()


def _identifier(
    value: Any,
    *,
    path: str,
    code: str,
    prompt: str,
    questions: list[DiscussionQuestion],
) -> str | None:
    text = _non_empty_text(
        value,
        path=path,
        code=code,
        prompt=prompt,
        questions=questions,
    )
    if text is not None and not IDENTIFIER_PATTERN.fullmatch(text):
        _question(questions, code, path, prompt)
        return None
    return text


def _object(
    value: Any,
    *,
    path: str,
    questions: list[DiscussionQuestion],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        _question(
            questions,
            "SECTION_REQUIRED",
            path,
            f"请补充 {path} 的完整结构化信息。",
        )
        return {}
    return value


def _positive_int(
    value: Any,
    *,
    path: str,
    questions: list[DiscussionQuestion],
) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _question(
            questions,
            "NON_NEGATIVE_INTEGER_REQUIRED",
            path,
            f"请确认 {path} 的非负整数值。",
        )
        return None
    return value


def _validate_raw_intake(
    value: Any, questions: list[DiscussionQuestion]
) -> None:
    intake = _object(value, path="$.raw_intake", questions=questions)
    for field in ("request_id", "received_at", "language", "original_request"):
        _non_empty_text(
            intake.get(field),
            path=f"$.raw_intake.{field}",
            code="RAW_INTAKE_FIELD_REQUIRED",
            prompt=f"请补充原始需求字段：{field}。",
            questions=questions,
        )
    attachments = intake.get("attachments")
    if not isinstance(attachments, list):
        _question(
            questions,
            "ATTACHMENT_MANIFEST_REQUIRED",
            "$.raw_intake.attachments",
            "请提供附件清单；无附件时使用空数组。",
        )
        return
    for index, item in enumerate(attachments):
        attachment = _object(
            item,
            path=f"$.raw_intake.attachments[{index}]",
            questions=questions,
        )
        for field in ("id", "locator", "kind", "rights"):
            _non_empty_text(
                attachment.get(field),
                path=f"$.raw_intake.attachments[{index}].{field}",
                code="ATTACHMENT_FIELD_REQUIRED",
                prompt=f"请补充附件 {index + 1} 的 {field}。",
                questions=questions,
            )


def _validate_assets(
    value: Any,
    questions: list[DiscussionQuestion],
    *,
    source_ids: frozenset[str],
) -> None:
    if not isinstance(value, list) or not value:
        _question(
            questions,
            "ASSET_MANIFEST_REQUIRED",
            "$.assets",
            "请列出制作所需素材及其来源、用途和授权状态。",
        )
        return
    for index, item in enumerate(value):
        asset = _object(item, path=f"$.assets[{index}]", questions=questions)
        for field in ("id", "role", "source_id", "locator"):
            _non_empty_text(
                asset.get(field),
                path=f"$.assets[{index}].{field}",
                code="ASSET_FIELD_REQUIRED",
                prompt=f"请补充素材 {index + 1} 的 {field}。",
                questions=questions,
            )
        source_id = asset.get("source_id")
        if (
            isinstance(source_id, str)
            and source_id.strip()
            and source_id not in source_ids
        ):
            _question(
                questions,
                "ASSET_SOURCE_UNKNOWN",
                f"$.assets[{index}].source_id",
                f"素材 {index + 1} 必须引用 FactStore 中已登记的来源。",
            )
        _non_empty_text(
            asset.get("rights"),
            path=f"$.assets[{index}].rights",
            code="ASSET_RIGHTS_REQUIRED",
            prompt=f"请确认素材 {index + 1} 的使用授权或保密边界。",
            questions=questions,
        )
        if not isinstance(asset.get("required"), bool):
            _question(
                questions,
                "ASSET_REQUIRED_FLAG_REQUIRED",
                f"$.assets[{index}].required",
                "请明确该素材是否为必须项。",
            )


def _validate_goals(value: Any, questions: list[DiscussionQuestion]) -> None:
    goals = _object(value, path="$.goals", questions=questions)
    _non_empty_text(
        goals.get("purpose"),
        path="$.goals.purpose",
        code="PURPOSE_REQUIRED",
        prompt="这份演示用于什么场景？",
        questions=questions,
    )
    _non_empty_text(
        goals.get("decision"),
        path="$.goals.decision",
        code="DECISION_REQUIRED",
        prompt="观众看完后必须做出什么决定或行动？",
        questions=questions,
    )
    outcomes = goals.get("success_outcomes")
    if not isinstance(outcomes, list) or not any(
        isinstance(item, str) and item.strip() for item in outcomes
    ):
        _question(
            questions,
            "SUCCESS_OUTCOME_REQUIRED",
            "$.goals.success_outcomes",
            "如何判断这次演示成功？请给出至少一项可观察结果。",
        )


def _validate_audience(value: Any, questions: list[DiscussionQuestion]) -> None:
    audience = _object(value, path="$.audience", questions=questions)
    for field in ("primary", "knowledge_level", "decision_role"):
        _non_empty_text(
            audience.get(field),
            path=f"$.audience.{field}",
            code="AUDIENCE_FIELD_REQUIRED",
            prompt=f"请补充受众的 {field}。",
            questions=questions,
        )


def _validate_timing(value: Any, questions: list[DiscussionQuestion]) -> None:
    timing = _object(value, path="$.timing", questions=questions)
    presentation = _positive_int(
        timing.get("presentation_minutes"),
        path="$.timing.presentation_minutes",
        questions=questions,
    )
    _positive_int(
        timing.get("qa_minutes"),
        path="$.timing.qa_minutes",
        questions=questions,
    )
    if presentation == 0:
        _question(
            questions,
            "PRESENTATION_TIME_REQUIRED",
            "$.timing.presentation_minutes",
            "正式演示时长必须大于 0 分钟。",
        )


def _validate_brand(value: Any, questions: list[DiscussionQuestion]) -> None:
    brand = _object(value, path="$.brand", questions=questions)
    for field in ("tone", "mode"):
        _non_empty_text(
            brand.get(field),
            path=f"$.brand.{field}",
            code="BRAND_FIELD_REQUIRED",
            prompt=f"请确认视觉品牌字段：{field}。",
            questions=questions,
        )
    for field in ("required_colors", "forbidden_styles"):
        if not isinstance(brand.get(field), list):
            _question(
                questions,
                "BRAND_LIST_REQUIRED",
                f"$.brand.{field}",
                f"请提供 {field} 列表；无约束时使用空数组。",
            )


def _validate_slide_budget(value: Any, questions: list[DiscussionQuestion]) -> None:
    budget = _object(value, path="$.slide_budget", questions=questions)
    parsed = {
        field: _positive_int(
            budget.get(field),
            path=f"$.slide_budget.{field}",
            questions=questions,
        )
        for field in ("main", "minimum", "maximum", "appendix", "backup")
    }
    main = parsed["main"]
    minimum = parsed["minimum"]
    maximum = parsed["maximum"]
    if (
        main is not None
        and minimum is not None
        and maximum is not None
        and not minimum <= main <= maximum
    ):
        _question(
            questions,
            "SLIDE_BUDGET_INCONSISTENT",
            "$.slide_budget",
            "主讲页数必须处于 minimum 与 maximum 之间。",
        )


def _validate_anatomy(value: Any, questions: list[DiscussionQuestion]) -> None:
    if not isinstance(value, list) or not value:
        _question(
            questions,
            "ANATOMY_REQUIRED",
            "$.anatomy",
            "请定义封面、目录、章节、主体、结尾和附录等页面骨架。",
        )
        roles: set[str] = set()
    else:
        roles = set()
        for index, item in enumerate(value):
            entry = _object(item, path=f"$.anatomy[{index}]", questions=questions)
            role = _non_empty_text(
                entry.get("role"),
                path=f"$.anatomy[{index}].role",
                code="ANATOMY_FIELD_REQUIRED",
                prompt=f"请补充页面骨架 {index + 1} 的 role。",
                questions=questions,
            )
            if role:
                roles.add(role)
            minimum = _positive_int(
                entry.get("min_count"),
                path=f"$.anatomy[{index}].min_count",
                questions=questions,
            )
            maximum = _positive_int(
                entry.get("max_count"),
                path=f"$.anatomy[{index}].max_count",
                questions=questions,
            )
            if minimum is not None and maximum is not None and minimum > maximum:
                _question(
                    questions,
                    "ANATOMY_COUNT_INCONSISTENT",
                    f"$.anatomy[{index}]",
                    "页面类型的 min_count 不能大于 max_count。",
                )
            if not isinstance(entry.get("required"), bool):
                _question(
                    questions,
                    "ANATOMY_REQUIRED_FLAG_REQUIRED",
                    f"$.anatomy[{index}].required",
                    "请明确该页面类型是否为必须项。",
                )
    missing = sorted(REQUIRED_ANATOMY_ROLES - roles)
    for role in missing:
        _question(
            questions,
            "ANATOMY_ROLE_REQUIRED",
            "$.anatomy",
            f"页面骨架缺少必须角色：{role}。",
        )


def _validate_text_list(
    value: Any,
    *,
    path: str,
    code: str,
    prompt: str,
    questions: list[DiscussionQuestion],
) -> None:
    if not isinstance(value, list) or not any(
        isinstance(item, str) and item.strip() for item in value
    ):
        _question(questions, code, path, prompt)


def _validate_rubric(value: Any, questions: list[DiscussionQuestion]) -> None:
    if not isinstance(value, list) or not value:
        _question(
            questions,
            "RUBRIC_REQUIRED",
            "$.rubric",
            "请定义本项目的验收维度、权重与最低分。",
        )
        return
    weights: list[float] = []
    for index, item in enumerate(value):
        entry = _object(item, path=f"$.rubric[{index}]", questions=questions)
        _non_empty_text(
            entry.get("criterion"),
            path=f"$.rubric[{index}].criterion",
            code="RUBRIC_CRITERION_REQUIRED",
            prompt=f"请补充验收项 {index + 1} 的 criterion。",
            questions=questions,
        )
        weight = entry.get("weight")
        minimum = entry.get("minimum_score")
        if (
            isinstance(weight, bool)
            or not isinstance(weight, (int, float))
            or not math.isfinite(float(weight))
            or float(weight) <= 0
        ):
            _question(
                questions,
                "RUBRIC_WEIGHT_INVALID",
                f"$.rubric[{index}].weight",
                "验收权重必须是大于 0 的有限数值。",
            )
        else:
            weights.append(float(weight))
        if (
            isinstance(minimum, bool)
            or not isinstance(minimum, (int, float))
            or not math.isfinite(float(minimum))
            or not 0 <= float(minimum) <= 5
        ):
            _question(
                questions,
                "RUBRIC_SCORE_INVALID",
                f"$.rubric[{index}].minimum_score",
                "最低分必须处于 0 到 5 之间。",
            )
    if weights and not math.isclose(sum(weights), 1.0, abs_tol=1e-6):
        _question(
            questions,
            "RUBRIC_WEIGHT_SUM_INVALID",
            "$.rubric",
            "验收权重之和必须等于 1。",
        )


def validate_project_brief_pack(payload: Mapping[str, Any]) -> ProjectBriefPack:
    """Validate a pack and return every discussion question in stable order."""

    if not isinstance(payload, Mapping):
        raise BriefValidationError("BRIEF_OBJECT_REQUIRED")
    raw = copy.deepcopy(dict(payload))
    unknown = sorted(set(raw) - ROOT_FIELDS)
    if unknown:
        raise BriefValidationError(
            f"BRIEF_UNKNOWN_FIELDS: {','.join(unknown)}"
        )
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise BriefValidationError("BRIEF_SCHEMA_VERSION_UNSUPPORTED")
    try:
        state = BriefState(raw.get("state"))
    except ValueError as exc:
        raise BriefValidationError("BRIEF_STATE_INVALID") from exc

    questions: list[DiscussionQuestion] = []
    brief_id = _identifier(
        raw.get("brief_id"),
        path="$.brief_id",
        code="BRIEF_ID_REQUIRED",
        prompt="请提供稳定的 brief_id。",
        questions=questions,
    )
    scenario_id = _identifier(
        raw.get("scenario_id"),
        path="$.scenario_id",
        code="SCENARIO_ID_REQUIRED",
        prompt="请确认演示场景类型。",
        questions=questions,
    )
    _validate_raw_intake(raw.get("raw_intake"), questions)

    fact_store: FactStore | None = None
    try:
        fact_store = validate_fact_store(raw.get("fact_store"))
    except WeakModelValidationError as exc:
        _question(
            questions,
            "FACT_STORE_INVALID",
            "$.fact_store",
            f"请修复事实与来源清单：{exc}",
        )

    source_ids = (
        frozenset(item.id for item in fact_store.sources)
        if fact_store is not None
        else frozenset()
    )
    _validate_assets(raw.get("assets"), questions, source_ids=source_ids)
    _validate_audience(raw.get("audience"), questions)
    _validate_goals(raw.get("goals"), questions)
    _validate_timing(raw.get("timing"), questions)
    _validate_brand(raw.get("brand"), questions)
    _validate_slide_budget(raw.get("slide_budget"), questions)
    _validate_anatomy(raw.get("anatomy"), questions)
    _validate_text_list(
        raw.get("decisions"),
        path="$.decisions",
        code="DECISION_LIST_REQUIRED",
        prompt="请列出本次演示需要促成或记录的决定。",
        questions=questions,
    )
    _validate_text_list(
        raw.get("prohibitions"),
        path="$.prohibitions",
        code="PROHIBITION_LIST_REQUIRED",
        prompt="请列出不得虚构、不得误导或不得使用的内容。",
        questions=questions,
    )
    _validate_rubric(raw.get("rubric"), questions)

    unresolved = raw.get("unresolved_questions")
    if not isinstance(unresolved, list):
        _question(
            questions,
            "UNRESOLVED_LIST_REQUIRED",
            "$.unresolved_questions",
            "请提供待讨论问题列表；没有时使用空数组。",
        )
    else:
        for index, item in enumerate(unresolved):
            if not isinstance(item, str) or not item.strip():
                _question(
                    questions,
                    "UNRESOLVED_QUESTION_INVALID",
                    f"$.unresolved_questions[{index}]",
                    "待讨论问题必须是非空文本。",
                )
            else:
                _question(
                    questions,
                    "UNRESOLVED_QUESTION",
                    f"$.unresolved_questions[{index}]",
                    item.strip(),
                )

    lock_sha256 = raw.get("lock_sha256")
    if lock_sha256 is not None and (
        not isinstance(lock_sha256, str) or not SHA256_PATTERN.fullmatch(lock_sha256)
    ):
        raise BriefLockError("BRIEF_LOCK_FORMAT_INVALID")
    if state is BriefState.LOCKED:
        if lock_sha256 is None:
            raise BriefLockError("BRIEF_LOCK_REQUIRED")
        expected = project_brief_digest(raw)
        if lock_sha256 != expected:
            raise BriefLockError("BRIEF_LOCK_MISMATCH")
        if questions:
            raise BriefLockError("BRIEF_LOCKED_BUT_INCOMPLETE")

    ordered = tuple(
        sorted(questions, key=lambda item: (item.path, item.code, item.prompt))
    )
    return ProjectBriefPack(
        schema_version=SCHEMA_VERSION,
        brief_id=brief_id or "",
        scenario_id=scenario_id or "",
        state=state,
        fact_store=fact_store,
        questions=ordered,
        lock_sha256=lock_sha256,
        payload=raw,
    )


def lock_project_brief_pack(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Lock a complete discussed pack and return a canonicalizable copy."""

    candidate = copy.deepcopy(dict(payload))
    candidate["state"] = BriefState.NEEDS_DISCUSSION.value
    candidate["lock_sha256"] = None
    validated = validate_project_brief_pack(candidate)
    if validated.questions:
        codes = ",".join(sorted({item.code for item in validated.questions}))
        raise BriefLockError(f"BRIEF_INCOMPLETE: {codes}")
    locked = _lock_material(candidate)
    locked["lock_sha256"] = project_brief_digest(locked)
    validate_project_brief_pack(locked)
    return locked


def prepare_formal_brief(payload: Mapping[str, Any]) -> ProjectBriefPack:
    """Require an intact lock before any formal narrative or PPTX generation."""

    validated = validate_project_brief_pack(payload)
    if not validated.formal_ready:
        raise BriefLockError("BRIEF_NOT_LOCKED")
    return validated


__all__ = [
    "BriefLockError",
    "BriefState",
    "BriefValidationError",
    "DiscussionQuestion",
    "ProjectBriefPack",
    "lock_project_brief_pack",
    "prepare_formal_brief",
    "project_brief_digest",
    "validate_project_brief_pack",
]
