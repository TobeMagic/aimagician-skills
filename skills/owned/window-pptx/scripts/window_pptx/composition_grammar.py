"""Deterministic scenario-to-composition recipes for weak-model generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .design_packs import canonical_scenario_id


SKILL_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GRAMMAR_PATH = SKILL_ROOT / "registries" / "composition-grammars.json"
_DENSITIES = {"sparse", "balanced", "dense"}
_EMPHASIS = {"quiet", "standard", "hero"}


class CompositionGrammarError(ValueError):
    """A composition grammar is malformed or ambiguous."""


@dataclass(frozen=True)
class CompositionRecipe:
    id: str
    role_patterns: tuple[str, ...]
    semantic_kinds: tuple[str, ...]
    family: str
    variant: str
    density: str
    emphasis: str
    components: tuple[str, ...]
    max_items: int
    max_body_chars: int


@dataclass(frozen=True)
class CompositionGrammar:
    id: str
    scenario: str
    design_pack_id: str
    recipes: tuple[CompositionRecipe, ...]


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CompositionGrammarError(f"{path} must be a trimmed string")
    return value


def _strings(value: Any, path: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise CompositionGrammarError(f"{path} must be an array of strings")
    result = tuple(_string(item, f"{path}[{index}]") for index, item in enumerate(value))
    if len(set(result)) != len(result):
        raise CompositionGrammarError(f"{path} cannot contain duplicates")
    return result


def load_composition_grammars(
    path: str | Path = DEFAULT_GRAMMAR_PATH,
) -> tuple[CompositionGrammar, ...]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompositionGrammarError(f"cannot load composition grammar: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "grammars"}:
        raise CompositionGrammarError("composition grammar root is invalid")
    if raw["schema_version"] != "1.0" or not isinstance(raw["grammars"], list):
        raise CompositionGrammarError("composition grammar schema_version is invalid")
    grammars: list[CompositionGrammar] = []
    grammar_ids: set[str] = set()
    scenarios: set[str] = set()
    for grammar_index, entry in enumerate(raw["grammars"]):
        path_prefix = f"$.grammars[{grammar_index}]"
        if not isinstance(entry, dict) or set(entry) != {
            "id",
            "scenario",
            "design_pack_id",
            "recipes",
        }:
            raise CompositionGrammarError(f"{path_prefix} is invalid")
        grammar_id = _string(entry["id"], f"{path_prefix}.id")
        scenario = canonical_scenario_id(
            _string(entry["scenario"], f"{path_prefix}.scenario")
        )
        if grammar_id in grammar_ids or scenario in scenarios:
            raise CompositionGrammarError("grammar ids and scenarios must be unique")
        if not isinstance(entry["recipes"], list) or not entry["recipes"]:
            raise CompositionGrammarError(f"{path_prefix}.recipes must not be empty")
        recipes: list[CompositionRecipe] = []
        recipe_ids: set[str] = set()
        for recipe_index, recipe in enumerate(entry["recipes"]):
            recipe_path = f"{path_prefix}.recipes[{recipe_index}]"
            required = {
                "id",
                "role_patterns",
                "semantic_kinds",
                "family",
                "variant",
                "density",
                "emphasis",
                "components",
                "max_items",
                "max_body_chars",
            }
            if not isinstance(recipe, dict) or set(recipe) != required:
                raise CompositionGrammarError(f"{recipe_path} is invalid")
            recipe_id = _string(recipe["id"], f"{recipe_path}.id")
            density = _string(recipe["density"], f"{recipe_path}.density")
            emphasis = _string(recipe["emphasis"], f"{recipe_path}.emphasis")
            max_items = recipe["max_items"]
            max_body_chars = recipe["max_body_chars"]
            if (
                recipe_id in recipe_ids
                or density not in _DENSITIES
                or emphasis not in _EMPHASIS
                or type(max_items) is not int
                or not 1 <= max_items <= 12
                or type(max_body_chars) is not int
                or not 40 <= max_body_chars <= 400
            ):
                raise CompositionGrammarError(f"{recipe_path} has invalid constraints")
            recipes.append(
                CompositionRecipe(
                    id=recipe_id,
                    role_patterns=_strings(
                        recipe["role_patterns"], f"{recipe_path}.role_patterns"
                    ),
                    semantic_kinds=_strings(
                        recipe["semantic_kinds"],
                        f"{recipe_path}.semantic_kinds",
                        allow_empty=True,
                    ),
                    family=_string(recipe["family"], f"{recipe_path}.family"),
                    variant=_string(recipe["variant"], f"{recipe_path}.variant"),
                    density=density,
                    emphasis=emphasis,
                    components=_strings(
                        recipe["components"], f"{recipe_path}.components"
                    ),
                    max_items=max_items,
                    max_body_chars=max_body_chars,
                )
            )
            recipe_ids.add(recipe_id)
        fallback = [recipe for recipe in recipes if "*" in recipe.role_patterns]
        if len(fallback) != 1:
            raise CompositionGrammarError(
                f"{path_prefix} requires exactly one wildcard safe recipe"
            )
        grammars.append(
            CompositionGrammar(
                id=grammar_id,
                scenario=scenario,
                design_pack_id=_string(
                    entry["design_pack_id"], f"{path_prefix}.design_pack_id"
                ),
                recipes=tuple(recipes),
            )
        )
        grammar_ids.add(grammar_id)
        scenarios.add(scenario)
    return tuple(grammars)


def select_composition_recipe(
    scenario: str,
    *,
    design_pack_id: str,
    role: str,
    semantic_kind: str,
    grammars: tuple[CompositionGrammar, ...] | None = None,
) -> CompositionRecipe | None:
    canonical = canonical_scenario_id(scenario)
    selected = next(
        (
            grammar
            for grammar in (grammars or load_composition_grammars())
            if grammar.scenario == canonical
            and grammar.design_pack_id == design_pack_id
        ),
        None,
    )
    if selected is None:
        return None
    role_key = role.casefold()
    semantic_key = semantic_kind.casefold()
    fallback: CompositionRecipe | None = None
    scored: list[tuple[int, int, CompositionRecipe]] = []
    for index, recipe in enumerate(selected.recipes):
        if "*" in recipe.role_patterns:
            fallback = recipe
            continue
        role_score = max(
            (
                100
                if role_key == pattern.casefold()
                else 80
                if pattern.casefold() in role_key
                else 0
            )
            for pattern in recipe.role_patterns
        )
        semantic_score = (
            60
            if semantic_key in {value.casefold() for value in recipe.semantic_kinds}
            else 0
        )
        if role_score or semantic_score:
            scored.append((role_score + semantic_score, -index, recipe))
    if scored:
        return max(scored, key=lambda item: item[:2])[2]
    return fallback


__all__ = [
    "CompositionGrammar",
    "CompositionGrammarError",
    "CompositionRecipe",
    "load_composition_grammars",
    "select_composition_recipe",
]
