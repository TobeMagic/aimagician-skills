"""Strict loaders for governed window-pptx registries."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_ARCHETYPE_REGISTRY = (
    Path(__file__).resolve().parents[2] / "registries" / "archetypes.json"
)


class RegistryError(ValueError):
    """A governed registry is missing, malformed, or ambiguous."""


@dataclass(frozen=True)
class Archetype:
    """A predefined commercial narrative sequence."""

    id: str
    name: str
    aliases: tuple[str, ...]
    sections: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "aliases": list(self.aliases),
            "sections": list(self.sections),
        }


def _required_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistryError(f"{path} must be a non-empty string")
    return value.strip()


def _required_string_list(value: Any, path: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise RegistryError(f"{path} must be a non-empty array")
    result = tuple(_required_string(item, f"{path}[{index}]") for index, item in enumerate(value))
    if len(result) != len(set(result)):
        raise RegistryError(f"{path} contains duplicate values")
    return result


def load_archetypes(path: Path | str | None = None) -> dict[str, Archetype]:
    """Load and validate the complete commercial-archetype registry."""

    registry_path = Path(path) if path is not None else DEFAULT_ARCHETYPE_REGISTRY
    try:
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot load archetype registry {registry_path}: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "archetypes"}:
        raise RegistryError("archetype registry must contain only schema_version and archetypes")
    if raw["schema_version"] != "1.0":
        raise RegistryError("unsupported archetype registry schema_version")
    entries = raw["archetypes"]
    if not isinstance(entries, list) or not entries:
        raise RegistryError("archetypes must be a non-empty array")

    registry: dict[str, Archetype] = {}
    aliases: dict[str, str] = {}
    for index, entry in enumerate(entries):
        path_prefix = f"archetypes[{index}]"
        if not isinstance(entry, dict):
            raise RegistryError(f"{path_prefix} must be an object")
        allowed = {"id", "name", "aliases", "sections"}
        unknown = sorted(set(entry) - allowed)
        if unknown:
            raise RegistryError(f"{path_prefix} has unknown fields: {', '.join(unknown)}")
        archetype_id = _required_string(entry.get("id"), f"{path_prefix}.id")
        if archetype_id in registry:
            raise RegistryError(f"duplicate archetype id: {archetype_id}")
        sections = _required_string_list(entry.get("sections"), f"{path_prefix}.sections")
        if len(sections) < 6 or sections[0] != "cover" or sections[-1] != "closing":
            raise RegistryError(
                f"{path_prefix}.sections must contain at least six roles from cover to closing"
            )
        archetype = Archetype(
            id=archetype_id,
            name=_required_string(entry.get("name"), f"{path_prefix}.name"),
            aliases=_required_string_list(entry.get("aliases"), f"{path_prefix}.aliases"),
            sections=sections,
        )
        registry[archetype_id] = archetype
        for alias in (archetype_id, *archetype.aliases):
            normalized = alias.casefold().strip()
            owner = aliases.get(normalized)
            if owner is not None and owner != archetype_id:
                raise RegistryError(
                    f"ambiguous archetype alias {alias!r}: {owner} and {archetype_id}"
                )
            aliases[normalized] = archetype_id
    return registry


def resolve_archetype(
    scenario: str, registry: dict[str, Archetype] | None = None
) -> Archetype:
    """Resolve a stable archetype ID from an ID or multilingual alias."""

    if not isinstance(scenario, str) or not scenario.strip():
        raise RegistryError("scenario must be a non-empty string")
    available = registry if registry is not None else load_archetypes()
    normalized = scenario.casefold().strip()
    for archetype in available.values():
        if normalized in {
            archetype.id.casefold(),
            *(alias.casefold().strip() for alias in archetype.aliases),
        }:
            return archetype
    raise RegistryError(f"unknown presentation scenario: {scenario}")
