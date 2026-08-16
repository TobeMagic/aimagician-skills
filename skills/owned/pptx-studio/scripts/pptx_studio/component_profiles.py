"""Private, hash-bound authorities for native component insertion.

The public composition plan contains only opaque component and host-anchor
identifiers.  This module is deliberately the private boundary that maps those
identifiers to the native shape closures consumed by the physical assembler.
It never derives an insertion region from geometry at client runtime.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .query import _SUITABILITY_PROFILES, _suitability_safe, materialization_eligible


class ComponentProfileError(ValueError):
    """A private component authority is absent, malformed, or stale."""


_SCHEMAS = frozenset({
    "pptx-studio-component-profile.v1",
    "pptx-studio-component-profile.v2",
    "pptx-studio-component-profile.v3",
    "pptx-studio-component-profile.v4",
})
_STATUS = "COMPLETE"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_PAGE_ID_RE = re.compile(r"page_[0-9a-f]{24}_[0-9]{3}")
_COMPONENT_ID_RE = re.compile(r"component_[0-9a-f]{24}")
_ANCHOR_ID_RE = re.compile(r"anchor_[0-9a-f]{24}")
_STYLE_PROFILE_FIELDS = frozenset({"archetype", "tone", "color_family"})
_STYLE_ARCHETYPES = frozenset({
    "academic", "corporate", "editorial", "festive", "general",
    "infographic", "minimal", "technology",
})
_STYLE_TONES = frozenset({"light", "balanced", "dark"})
_STYLE_COLORS = frozenset({"cool", "green", "mixed", "neutral", "warm"})
_REVIEW_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def catalog_sha256(catalog: Mapping[str, Any]) -> str:
    """Return the same stable catalog digest used by composition replay."""

    return hashlib.sha256(_canonical_json(catalog).encode("utf-8")).hexdigest()


def component_profile_sha256(payload: Mapping[str, Any]) -> str:
    """Fingerprint a profile excluding its self-referential digest field."""

    value = dict(payload)
    value.pop("profile_sha256", None)
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _positive_shape_ids(value: Any, *, code: str) -> tuple[int, ...]:
    if (
        not isinstance(value, list)
        or not value
        or any(type(item) is not int or item < 1 for item in value)
        or len(set(value)) != len(value)
    ):
        raise ComponentProfileError(code)
    return tuple(value)


def _string_list(value: Any, *, code: str, pattern: re.Pattern[str] | None = None) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
        or (pattern is not None and any(pattern.fullmatch(item) is None for item in value))
    ):
        raise ComponentProfileError(code)
    return tuple(value)


def _visual_certification(value: Any) -> ComponentVisualCertification:
    if not isinstance(value, Mapping) or set(value) != {
        "review_id", "review_sha256", "style_profile", "suitability",
    }:
        raise ComponentProfileError("COMPONENT_PROFILE_VISUAL_CERTIFICATION_INVALID")
    review_id, review_sha, profile = (
        value.get("review_id"), value.get("review_sha256"), value.get("style_profile"),
    )
    if (
        not isinstance(review_id, str) or _REVIEW_ID_RE.fullmatch(review_id) is None
        or not isinstance(review_sha, str) or _SHA256_RE.fullmatch(review_sha) is None
        or not isinstance(profile, Mapping) or set(profile) != _STYLE_PROFILE_FIELDS
        or profile.get("archetype") not in _STYLE_ARCHETYPES
        or profile.get("tone") not in _STYLE_TONES
        or profile.get("color_family") not in _STYLE_COLORS
    ):
        raise ComponentProfileError("COMPONENT_PROFILE_VISUAL_CERTIFICATION_INVALID")
    suitability = _string_list(
        value.get("suitability"), code="COMPONENT_PROFILE_VISUAL_CERTIFICATION_INVALID",
    )
    if any(item not in _SUITABILITY_PROFILES for item in suitability):
        raise ComponentProfileError("COMPONENT_PROFILE_VISUAL_CERTIFICATION_INVALID")
    return ComponentVisualCertification(
        review_id=review_id,
        review_sha256=review_sha,
        style_profile={key: str(profile[key]) for key in sorted(_STYLE_PROFILE_FIELDS)},
        suitability=suitability,
    )


@dataclass(frozen=True)
class ComponentProfile:
    component_id: str
    page_id: str
    package_sha256: str
    slide_number: int
    slide_sha256: str
    shape_ids: tuple[int, ...]
    component_sha256: str
    relationship_ids: tuple[str, ...]
    semantic_intent: str
    allowed_roles: tuple[str, ...]
    fields: tuple["ComponentField", ...]
    allowed_host_anchor_ids: tuple[str, ...]
    visual_certification: "ComponentVisualCertification | None" = None


@dataclass(frozen=True)
class ComponentField:
    """One private, fact-bindable text surface inside a certified component."""

    field_id: str
    shape_id: int
    semantic_role: str
    max_chars: int


@dataclass(frozen=True)
class ComponentVisualCertification:
    """Private visual approval for an extracted native component closure.

    A source page can contain an unrelated stock photo while a selected title
    or statement closure contains none of that material. This certification is
    curator-only evidence for the closure itself, not a permission for an
    agent to restyle or redraw it.
    """

    review_id: str
    review_sha256: str
    style_profile: Mapping[str, str]
    suitability: tuple[str, ...]


@dataclass(frozen=True)
class HostAnchorProfile:
    host_anchor_id: str
    page_id: str
    package_sha256: str
    slide_number: int
    slide_sha256: str
    shape_ids: tuple[int, ...]
    host_anchor_sha256: str
    compatible_component_ids: tuple[str, ...]
    removable_shape_ids: tuple[int, ...] = ()
    removable_shape_sha256: str | None = None
    # ``replacement`` anchors swap a source closure for another closure.
    # ``canvas`` anchors add a certified component to an operator-proven empty
    # native zone.  The bbox is private profile data; no agent request can
    # name or alter it.
    anchor_mode: str = "replacement"
    canvas_source_package_sha256: str | None = None
    canvas_source_slide_number: int | None = None
    canvas_source_slide_sha256: str | None = None
    canvas_shape_ids: tuple[int, ...] = ()
    canvas_sha256: str | None = None
    canvas_bbox: tuple[int, int, int, int] | None = None


@dataclass(frozen=True)
class ComponentProfileIndex:
    profile_id: str
    profile_sha256: str
    catalog_sha256: str
    components: Mapping[str, ComponentProfile]
    host_anchors: Mapping[str, HostAnchorProfile]

    def component(self, component_id: str) -> ComponentProfile:
        try:
            return self.components[component_id]
        except KeyError as exc:
            raise ComponentProfileError("COMPONENT_PROFILE_COMPONENT_UNKNOWN") from exc

    def host_anchor(self, host_anchor_id: str) -> HostAnchorProfile:
        try:
            return self.host_anchors[host_anchor_id]
        except KeyError as exc:
            raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_UNKNOWN") from exc

    def validate_selection(
        self,
        *,
        host_page_id: str,
        host_anchor_id: str,
        component_ids: tuple[str, ...],
    ) -> tuple[HostAnchorProfile, tuple[ComponentProfile, ...]]:
        """Validate an agent's opaque selection without resolving geometry."""

        # V3 represented one host reservation plus an array of components.
        # The physical importer can remove that reservation only once, so an
        # array of two or three components was never a real placement model.
        # Keep V3 as a backward-compatible *single* placement and require V4
        # callers to submit one explicit anchor per component.
        if len(component_ids) != 1:
            raise ComponentProfileError("COMPONENT_PROFILE_SELECTION_INVALID")
        anchor = self.host_anchor(host_anchor_id)
        if anchor.page_id != host_page_id:
            raise ComponentProfileError("COMPONENT_PROFILE_HOST_PAGE_MISMATCH")
        components = tuple(self.component(item) for item in component_ids)
        for component in components:
            if component.component_id not in anchor.compatible_component_ids:
                raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_INCOMPATIBLE")
            if anchor.host_anchor_id not in component.allowed_host_anchor_ids:
                raise ComponentProfileError("COMPONENT_PROFILE_COMPONENT_INCOMPATIBLE")
        return anchor, components

    def validate_placements(
        self,
        *,
        host_page_id: str,
        placements: tuple[tuple[str, str], ...],
    ) -> tuple[tuple[HostAnchorProfile, ComponentProfile], ...]:
        """Validate V4 component-to-anchor placements without exposing geometry.

        A repeated anchor would make one imported component erase another
        reservation.  A repeated component would duplicate an otherwise
        certified visual object.  Both are rejected before a source package is
        opened, leaving physical assembly with a one-to-one placement contract.
        """

        # Six is the largest curated parallel-card family in the active
        # library. It covers real four-KPI and up-to-six-item business pages
        # without exposing an unbounded layout-composition surface.
        if not 1 <= len(placements) <= 6:
            raise ComponentProfileError("COMPONENT_PROFILE_PLACEMENTS_INVALID")
        anchors = [anchor_id for anchor_id, _component_id in placements]
        components = [component_id for _anchor_id, component_id in placements]
        if len(set(anchors)) != len(anchors) or len(set(components)) != len(components):
            raise ComponentProfileError("COMPONENT_PROFILE_PLACEMENTS_DUPLICATE")
        result: list[tuple[HostAnchorProfile, ComponentProfile]] = []
        for anchor_id, component_id in placements:
            anchor, selected = self.validate_selection(
                host_page_id=host_page_id,
                host_anchor_id=anchor_id,
                component_ids=(component_id,),
            )
            result.append((anchor, selected[0]))
        return tuple(result)


def _catalog_pages(catalog: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    pages = catalog.get("pages")
    if not isinstance(pages, list):
        raise ComponentProfileError("COMPONENT_PROFILE_CATALOG_INVALID")
    result: dict[str, Mapping[str, Any]] = {}
    for page in pages:
        if not isinstance(page, Mapping):
            raise ComponentProfileError("COMPONENT_PROFILE_CATALOG_INVALID")
        page_id = page.get("page_id")
        if not isinstance(page_id, str) or _PAGE_ID_RE.fullmatch(page_id) is None or page_id in result:
            raise ComponentProfileError("COMPONENT_PROFILE_CATALOG_INVALID")
        result[page_id] = page
    return result


def _profile_source(entry: Mapping[str, Any], *, code: str) -> tuple[str, str, int, str]:
    source = entry.get("source")
    if not isinstance(source, Mapping) or set(source) != {
        "page_id", "package_sha256", "slide_number", "slide_sha256",
    }:
        raise ComponentProfileError(code)
    page_id = source.get("page_id")
    package_sha = source.get("package_sha256")
    slide_number = source.get("slide_number")
    slide_sha = source.get("slide_sha256")
    if (
        not isinstance(page_id, str)
        or _PAGE_ID_RE.fullmatch(page_id) is None
        or not isinstance(package_sha, str)
        or _SHA256_RE.fullmatch(package_sha) is None
        or type(slide_number) is not int
        or slide_number < 1
        or not isinstance(slide_sha, str)
        or _SHA256_RE.fullmatch(slide_sha) is None
    ):
        raise ComponentProfileError(code)
    return page_id, package_sha, slide_number, slide_sha


def _validate_catalog_source(
    pages: Mapping[str, Mapping[str, Any]],
    *,
    page_id: str,
    package_sha256: str,
    slide_number: int,
) -> None:
    page = pages.get(page_id)
    if (
        page is None
        or page.get("package_sha256") != package_sha256
        or page.get("slide_number") != slide_number
    ):
        raise ComponentProfileError("COMPONENT_PROFILE_CATALOG_SOURCE_DRIFT")


def load_component_profiles(
    path: Path | str,
    *,
    catalog: Mapping[str, Any],
) -> ComponentProfileIndex:
    """Load a complete private authority and fail closed on catalog drift."""

    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ComponentProfileError("COMPONENT_PROFILE_UNAVAILABLE") from exc
    if not isinstance(payload, Mapping) or set(payload) != {
        "schema_version", "status", "profile_id", "profile_sha256", "catalog_sha256",
        "components", "host_anchors",
    }:
        raise ComponentProfileError("COMPONENT_PROFILE_SCHEMA_INVALID")
    schema_version = payload.get("schema_version")
    if schema_version not in _SCHEMAS or payload.get("status") != _STATUS:
        raise ComponentProfileError("COMPONENT_PROFILE_SCHEMA_INVALID")
    profile_id = payload.get("profile_id")
    profile_digest = payload.get("profile_sha256")
    catalog_digest = payload.get("catalog_sha256")
    if (
        not isinstance(profile_id, str)
        or not profile_id
        or not isinstance(profile_digest, str)
        or _SHA256_RE.fullmatch(profile_digest) is None
        or not isinstance(catalog_digest, str)
        or _SHA256_RE.fullmatch(catalog_digest) is None
    ):
        raise ComponentProfileError("COMPONENT_PROFILE_SCHEMA_INVALID")
    if profile_digest != component_profile_sha256(payload):
        raise ComponentProfileError("COMPONENT_PROFILE_FINGERPRINT_INVALID")
    actual_catalog_digest = catalog_sha256(catalog)
    if catalog_digest != actual_catalog_digest:
        raise ComponentProfileError("COMPONENT_PROFILE_CATALOG_DRIFT")
    pages = _catalog_pages(catalog)
    raw_components = payload.get("components")
    raw_anchors = payload.get("host_anchors")
    if not isinstance(raw_components, list) or not raw_components or not isinstance(raw_anchors, list) or not raw_anchors:
        raise ComponentProfileError("COMPONENT_PROFILE_EMPTY")

    components: dict[str, ComponentProfile] = {}
    for raw in raw_components:
        component_fields = {
            "component_id", "source", "shape_ids", "component_sha256",
            "relationship_ids", "semantic_intent", "allowed_roles",
            "fields", "allowed_host_anchor_ids",
        }
        if schema_version == "pptx-studio-component-profile.v4":
            component_fields.add("visual_certification")
        if not isinstance(raw, Mapping) or set(raw) != component_fields:
            raise ComponentProfileError("COMPONENT_PROFILE_COMPONENT_INVALID")
        component_id = raw.get("component_id")
        if not isinstance(component_id, str) or _COMPONENT_ID_RE.fullmatch(component_id) is None or component_id in components:
            raise ComponentProfileError("COMPONENT_PROFILE_COMPONENT_INVALID")
        page_id, package_sha, slide_number, slide_sha = _profile_source(raw, code="COMPONENT_PROFILE_COMPONENT_INVALID")
        _validate_catalog_source(pages, page_id=page_id, package_sha256=package_sha, slide_number=slide_number)
        component_sha = raw.get("component_sha256")
        intent = raw.get("semantic_intent")
        if (
            not isinstance(component_sha, str)
            or _SHA256_RE.fullmatch(component_sha) is None
            or not isinstance(intent, str)
            or not intent
        ):
            raise ComponentProfileError("COMPONENT_PROFILE_COMPONENT_INVALID")
        raw_fields = raw.get("fields")
        if not isinstance(raw_fields, list) or not raw_fields:
            raise ComponentProfileError("COMPONENT_PROFILE_COMPONENT_INVALID")
        fields: list[ComponentField] = []
        field_ids: set[str] = set()
        field_shape_ids: set[int] = set()
        shape_ids = _positive_shape_ids(raw.get("shape_ids"), code="COMPONENT_PROFILE_COMPONENT_INVALID")
        for field in raw_fields:
            if not isinstance(field, Mapping) or set(field) != {
                "field_id", "shape_id", "semantic_role", "max_chars",
            }:
                raise ComponentProfileError("COMPONENT_PROFILE_COMPONENT_INVALID")
            field_id, shape_id, role, max_chars = (
                field.get("field_id"), field.get("shape_id"),
                field.get("semantic_role"), field.get("max_chars"),
            )
            if (
                not isinstance(field_id, str) or not field_id or field_id in field_ids
                or type(shape_id) is not int or shape_id not in shape_ids or shape_id in field_shape_ids
                or role not in {"title", "label", "metric", "body"}
                or type(max_chars) is not int or max_chars < 1
            ):
                raise ComponentProfileError("COMPONENT_PROFILE_COMPONENT_INVALID")
            field_ids.add(field_id)
            field_shape_ids.add(shape_id)
            fields.append(ComponentField(field_id, shape_id, role, max_chars))
        components[component_id] = ComponentProfile(
            component_id=component_id,
            page_id=page_id,
            package_sha256=package_sha,
            slide_number=slide_number,
            slide_sha256=slide_sha,
            shape_ids=shape_ids,
            component_sha256=component_sha,
            relationship_ids=_string_list(raw.get("relationship_ids"), code="COMPONENT_PROFILE_COMPONENT_INVALID"),
            semantic_intent=intent,
            allowed_roles=_string_list(raw.get("allowed_roles"), code="COMPONENT_PROFILE_COMPONENT_INVALID"),
            fields=tuple(fields),
            allowed_host_anchor_ids=_string_list(
                raw.get("allowed_host_anchor_ids"),
                code="COMPONENT_PROFILE_COMPONENT_INVALID",
                pattern=_ANCHOR_ID_RE,
            ),
            visual_certification=(
                _visual_certification(raw.get("visual_certification"))
                if schema_version == "pptx-studio-component-profile.v4" else None
            ),
        )

    anchors: dict[str, HostAnchorProfile] = {}
    for raw in raw_anchors:
        if not isinstance(raw, Mapping):
            raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_INVALID")
        canvas_mode = raw.get("anchor_mode") == "canvas"
        if canvas_mode:
            anchor_fields = {
                "host_anchor_id", "anchor_mode", "source", "canvas_source",
                "canvas_shape_ids", "canvas_sha256", "canvas_bbox",
                "compatible_component_ids",
            }
        else:
            anchor_fields = {
                "host_anchor_id", "source", "shape_ids", "host_anchor_sha256",
                "compatible_component_ids",
            }
            if schema_version in {"pptx-studio-component-profile.v2", "pptx-studio-component-profile.v3", "pptx-studio-component-profile.v4"}:
                anchor_fields |= {"removable_shape_ids", "removable_shape_sha256"}
        if set(raw) != anchor_fields:
            raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_INVALID")
        anchor_id = raw.get("host_anchor_id")
        if not isinstance(anchor_id, str) or _ANCHOR_ID_RE.fullmatch(anchor_id) is None or anchor_id in anchors:
            raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_INVALID")
        page_id, package_sha, slide_number, slide_sha = _profile_source(raw, code="COMPONENT_PROFILE_ANCHOR_INVALID")
        _validate_catalog_source(pages, page_id=page_id, package_sha256=package_sha, slide_number=slide_number)
        compatible_component_ids = _string_list(
            raw.get("compatible_component_ids"),
            code="COMPONENT_PROFILE_ANCHOR_INVALID",
            pattern=_COMPONENT_ID_RE,
        )
        if canvas_mode:
            if schema_version not in {"pptx-studio-component-profile.v3", "pptx-studio-component-profile.v4"}:
                raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_INVALID")
            canvas_source = raw.get("canvas_source")
            if not isinstance(canvas_source, Mapping):
                raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_INVALID")
            canvas_page_id, canvas_package_sha, canvas_slide_number, canvas_slide_sha = _profile_source(
                {"source": canvas_source}, code="COMPONENT_PROFILE_ANCHOR_INVALID",
            )
            _validate_catalog_source(
                pages, page_id=canvas_page_id, package_sha256=canvas_package_sha,
                slide_number=canvas_slide_number,
            )
            canvas_shape_ids = _positive_shape_ids(
                raw.get("canvas_shape_ids"), code="COMPONENT_PROFILE_ANCHOR_INVALID",
            )
            canvas_sha = raw.get("canvas_sha256")
            canvas_bbox_raw = raw.get("canvas_bbox")
            if (
                not isinstance(canvas_sha, str)
                or _SHA256_RE.fullmatch(canvas_sha) is None
                or not isinstance(canvas_bbox_raw, list)
                or len(canvas_bbox_raw) != 4
                or any(type(value) is not int for value in canvas_bbox_raw)
                or canvas_bbox_raw[2] <= 0
                or canvas_bbox_raw[3] <= 0
            ):
                raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_INVALID")
            anchors[anchor_id] = HostAnchorProfile(
                host_anchor_id=anchor_id,
                page_id=page_id,
                package_sha256=package_sha,
                slide_number=slide_number,
                slide_sha256=slide_sha,
                shape_ids=(),
                # Reuse the existing field for stable legacy diagnostics. The
                # assembler branches on anchor_mode and never treats this as a
                # host replacement closure.
                host_anchor_sha256=canvas_sha,
                compatible_component_ids=compatible_component_ids,
                anchor_mode="canvas",
                canvas_source_package_sha256=canvas_package_sha,
                canvas_source_slide_number=canvas_slide_number,
                canvas_source_slide_sha256=canvas_slide_sha,
                canvas_shape_ids=canvas_shape_ids,
                canvas_sha256=canvas_sha,
                canvas_bbox=tuple(canvas_bbox_raw),
            )
            continue
        anchor_sha = raw.get("host_anchor_sha256")
        if not isinstance(anchor_sha, str) or _SHA256_RE.fullmatch(anchor_sha) is None:
            raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_INVALID")
        removable_shape_ids: tuple[int, ...] = ()
        removable_shape_sha256: str | None = None
        if schema_version in {"pptx-studio-component-profile.v2", "pptx-studio-component-profile.v3", "pptx-studio-component-profile.v4"}:
            raw_removable = raw.get("removable_shape_ids")
            raw_removable_sha = raw.get("removable_shape_sha256")
            if not isinstance(raw_removable, list) or any(
                type(value) is not int or value < 1 for value in raw_removable
            ) or len(set(raw_removable)) != len(raw_removable):
                raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_INVALID")
            if raw_removable:
                if (
                    not isinstance(raw_removable_sha, str)
                    or _SHA256_RE.fullmatch(raw_removable_sha) is None
                    or set(raw_removable).intersection(raw.get("shape_ids", []))
                ):
                    raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_INVALID")
                removable_shape_ids = tuple(raw_removable)
                removable_shape_sha256 = raw_removable_sha
            elif raw_removable_sha is not None:
                raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_INVALID")
        anchors[anchor_id] = HostAnchorProfile(
            host_anchor_id=anchor_id,
            page_id=page_id,
            package_sha256=package_sha,
            slide_number=slide_number,
            slide_sha256=slide_sha,
            shape_ids=_positive_shape_ids(raw.get("shape_ids"), code="COMPONENT_PROFILE_ANCHOR_INVALID"),
            host_anchor_sha256=anchor_sha,
            compatible_component_ids=compatible_component_ids,
            removable_shape_ids=removable_shape_ids,
            removable_shape_sha256=removable_shape_sha256,
        )
    for component in components.values():
        if any(anchor_id not in anchors for anchor_id in component.allowed_host_anchor_ids):
            raise ComponentProfileError("COMPONENT_PROFILE_COMPONENT_ANCHOR_UNKNOWN")
    for anchor in anchors.values():
        if any(component_id not in components for component_id in anchor.compatible_component_ids):
            raise ComponentProfileError("COMPONENT_PROFILE_ANCHOR_COMPONENT_UNKNOWN")
    return ComponentProfileIndex(
        profile_id=profile_id,
        profile_sha256=profile_digest,
        catalog_sha256=catalog_digest,
        components=components,
        host_anchors=anchors,
    )


def query_component_profiles(
    profiles: ComponentProfileIndex, *,
    catalog: Mapping[str, Any],
    observations: Mapping[str, Mapping[str, Any]],
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Return an agent-safe shortlist of certified component/host pairs."""

    if set(request) != {"role", "style", "suitability", "limit"}:
        raise ComponentProfileError("COMPONENT_QUERY_SCHEMA_INVALID")
    role, style, suitability, limit = (
        request.get("role"), request.get("style"),
        request.get("suitability"), request.get("limit"),
    )
    if (
        not isinstance(role, str) or not role
        or style is not None and not isinstance(style, str)
        or suitability not in _SUITABILITY_PROFILES
        or type(limit) is not int or not 1 <= limit <= 6
    ):
        raise ComponentProfileError("COMPONENT_QUERY_SCHEMA_INVALID")
    pages = _catalog_pages(catalog)
    candidates: list[dict[str, Any]] = []
    for component in profiles.components.values():
        if role not in component.allowed_roles:
            continue
        source_page = pages.get(component.page_id)
        source_observation = observations.get(component.page_id)
        certified_visual = component.visual_certification
        if (
            source_page is None or not materialization_eligible(source_page)
        ):
            continue
        if certified_visual is None:
            if (
                not isinstance(source_observation, Mapping)
                or not isinstance(source_observation.get("observation"), Mapping)
                or not _suitability_safe(source_observation["observation"], profile=str(suitability))
            ):
                continue
            source_style = source_observation["observation"].get("visual_style")
            if style is not None and (not isinstance(source_style, list) or style not in source_style):
                continue
        elif suitability not in certified_visual.suitability:
            continue
        elif style is not None:
            # A component-level certification intentionally carries a compact
            # profile rather than the source page's free-form vision labels.
            # It can only satisfy an exact style request when that request is
            # the digest of its certified profile.
            digest = hashlib.sha256(_canonical_json(dict(certified_visual.style_profile)).encode("utf-8")).hexdigest()[:24]
            if style != f"style_{digest}":
                continue
        hosts: list[dict[str, str]] = []
        for anchor_id in component.allowed_host_anchor_ids:
            anchor = profiles.host_anchor(anchor_id)
            host_page = pages.get(anchor.page_id)
            host_observation = observations.get(anchor.page_id)
            if (
                host_page is None or not materialization_eligible(host_page)
                or not isinstance(host_observation, Mapping)
                or not isinstance(host_observation.get("observation"), Mapping)
                or not _suitability_safe(host_observation["observation"], profile=str(suitability))
            ):
                continue
            hosts.append({"host_anchor_id": anchor_id, "host_page_id": anchor.page_id})
        if not hosts:
            continue
        candidates.append({
            "component_id": component.component_id,
            "semantic_intent": component.semantic_intent,
            "allowed_roles": list(component.allowed_roles),
            "fields": [
                {
                    "field_id": field.field_id,
                    "semantic_role": field.semantic_role,
                    "max_chars": field.max_chars,
                }
                for field in component.fields
            ],
            "hosts": hosts,
        })
    # Profile declaration order is curator-authored visual order. In contrast,
    # opaque hash ordering can cut the fourth card from a certified KPI row at
    # the public ``limit=6`` boundary, leaving an agent with individually
    # valid but non-completable components. Preserve that private ordering
    # while still returning only opaque public descriptors.
    return {
        "schema_version": "pptx-studio-component-query.v1",
        "status": "PASS" if candidates else "NO_MATCH",
        "role": role,
        "candidates": candidates[:limit],
    }


__all__ = [
    "ComponentProfile",
    "ComponentProfileError",
    "ComponentProfileIndex",
    "ComponentField",
    "HostAnchorProfile",
    "catalog_sha256",
    "component_profile_sha256",
    "load_component_profiles",
    "query_component_profiles",
]
