"""Shared, value-free classification of native template text surfaces."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


CLIENT_TITLE_RE = re.compile(
    r"(?:年度|年终|工作汇报|工作总结|财务决算|工作思路|收入情况|支出情况|经济指标|项目及)"
)
NUMERIC_VALUE_RE = re.compile(
    r"[0-9０-９][0-9０-９,，.．%％]*\s*(?:万|亿|元|人|次|项|个|家|年|月|日|%|％)?"
)
SEQUENCE_DATE_SOURCE_RE = re.compile(
    r"(?:20(?:XX|xx|\d{2})|第[一二三四五六七八九十\d]+(?:阶段|步)|STEP\s*\d+)",
    re.IGNORECASE,
)
TEMPLATE_BRAND_RE = re.compile(
    r"(?:B站|哔哩哔哩|bilibili|nestle|雀巢|erke|安踏|Abbott|完美日记|蚂蚁森林)",
    re.IGNORECASE,
)
STRUCTURAL_ORDINAL_RE = re.compile(r"(?:0?[1-9]|[1-9][0-9])[.、-]?")


def compact_text(value: str) -> str:
    return "".join(value.split())


def is_sequence_date_source(value: str) -> bool:
    return SEQUENCE_DATE_SOURCE_RE.search(compact_text(value)) is not None


def classify_text_surface(
    *,
    text: str,
    semantic_role: str | None,
    bbox: Mapping[str, Any],
    declared_role: str | None = None,
) -> str:
    """Return the same author-facing role for catalog and native preflight.

    The function intentionally consumes only source-private semantic hints and
    normalized geometry. Callers may publish the returned role/count, but not
    the source text or coordinates used to derive it.
    """

    compact = compact_text(text)
    if not compact or TEMPLATE_BRAND_RE.search(compact) or compact.casefold() == "logo":
        return "ignore"
    # Agenda ordinals are navigation structure derived from visual order, not
    # customer claims. Keep them editable and visible without forcing a weak
    # author to invent four extra facts merely to preserve 01-04.
    if declared_role == "contents" and STRUCTURAL_ORDINAL_RE.fullmatch(compact):
        return "ignore"
    if declared_role in {"timeline", "roadmap"} and is_sequence_date_source(compact):
        return "label"
    if declared_role in {"process", "business-model", "risk"} and semantic_role == "title":
        return "title"
    # Process pages publish linked step labels and descriptions.  Preserve an
    # importer-certified body slot even when its Chinese copy is compact;
    # otherwise the generic short-copy heuristic collapses every step surface
    # into a label and the binder cannot keep each label/body pair together.
    if declared_role in {"process", "risk"} and semantic_role in {"label", "body"}:
        return semantic_role
    if int(bbox.get("y", 1000)) < 240 and (
        CLIENT_TITLE_RE.search(compact)
        or "标题" in compact
        or "title" in compact.casefold()
        or semantic_role in {"title", "subtitle"}
    ):
        return "title"
    if NUMERIC_VALUE_RE.fullmatch(compact) or (
        NUMERIC_VALUE_RE.search(compact)
        and any(unit in compact for unit in ("万", "亿", "元", "%", "％", "人", "次", "项", "个"))
    ):
        return "metric"
    if "标题" in compact or compact.startswith(("添加", "输入", "请替换")):
        return "label"
    if len(compact) <= 18:
        return "label"
    return "body"
