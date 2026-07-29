"""Frozen weak-model benchmark primitives for the Window-PPTX v5 workflow."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from .assets import read_raster_dimensions
from .brand import discover_installed_fonts
from .deck_plan import DeckPlanValidationError, validate_deck_plan
from .design_quality import inspect_design_quality
from .errors import WindowPptxError
from .fingerprints import (
    governed_engine_source_paths,
    validate_fingerprint_bundle,
    validate_fingerprint_components,
)
from .generation import BriefGeneration, GenerationGateError, prepare_brief_generation
from .layouts import SlideSize
from .portable_runner import PortablePipelineResult
from .quality_v2 import QualityFindingV2, generation_quality_findings
from .registry import resolve_archetype
from .render_plan import RenderPlan, RenderPlanError, compile_render_plan
from .transaction import validate_ooxml_package
from .weak_model import (
    WeakModelValidationError,
    load_narrative_rules,
    normalize_brief_plan,
)


BENCHMARK_SCHEMA_VERSION = "1.0"
EXPECTED_SCENARIO_IDS = (
    "business-report",
    "project-proposal",
    "product-launch",
    "market-analysis",
    "sales-proposal",
    "investor-pitch",
    "annual-review",
    "strategic-plan",
    "data-analysis",
    "research-report",
    "training",
    "brand-introduction",
    "project-kickoff",
    "operations-review",
    "ecommerce-marketing",
)
EXPECTED_ARM_IDS = ("unassisted-json", "governed-plan", "full-v5")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_METRIC_IDS = (
    "response_json_valid",
    "deck_plan_valid",
    "fact_retention",
    "prohibited_claim_safety",
    "numeric_claim_safety",
    "compile_success",
    "archetype_match",
    "slide_count_fit",
    "semantic_form_coverage",
    "rhythm_compliance",
    "native_editable_coverage",
    "hard_gate_pass",
)
EXPECTED_THRESHOLD_IDS = (
    "full_v5_plan_validity",
    "full_v5_compile_success",
    "full_v5_hard_gate_pass",
    "full_v5_fact_retention",
    "prohibited_numeric_inventions",
    "delta_vs_unassisted_points",
    "delta_vs_governed_plan_points",
    "human_delivery_mean",
    "human_delta_vs_unassisted",
    "human_repeat_stddev_max",
    "artifact_hash_coverage",
)


def _canonical_value(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


def canonical_json(value: Any) -> str:
    """Serialize a JSON-compatible value without timestamps or key-order drift."""

    return json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    return dict(value)


def _require_exact_keys(
    value: Mapping[str, Any], required: set[str], path: str
) -> None:
    missing = required - set(value)
    extra = set(value) - required
    if missing or extra:
        raise ValueError(
            f"{path} keys mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )


def _require_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{path} must be a trimmed non-empty string")
    return value


def _require_strings(value: Any, path: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{path} must be a non-empty string array")
    result = tuple(_require_string(item, f"{path}[{index}]") for index, item in enumerate(value))
    if len(result) != len(set(result)):
        raise ValueError(f"{path} contains duplicates")
    return result


@dataclass(frozen=True)
class BenchmarkFact:
    id: str
    text: str
    required_terms: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "required_terms": list(self.required_terms),
        }


@dataclass(frozen=True)
class BenchmarkScenario:
    id: str
    presentation_type: str
    title: str
    language: str
    audience: str
    objective: str
    expected_archetype: str
    slide_count_min: int
    slide_count_max: int
    required_beats: tuple[str, ...]
    expected_forms: tuple[str, ...]
    asset_condition: str
    facts: tuple[BenchmarkFact, ...]
    prohibited_claims: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.presentation_type,
            "title": self.title,
            "language": self.language,
            "audience": self.audience,
            "objective": self.objective,
            "expected_archetype": self.expected_archetype,
            "slide_count_range": [self.slide_count_min, self.slide_count_max],
            "required_beats": list(self.required_beats),
            "expected_forms": list(self.expected_forms),
            "asset_condition": self.asset_condition,
            "facts": [fact.to_dict() for fact in self.facts],
            "prohibited_claims": list(self.prohibited_claims),
        }


@dataclass(frozen=True)
class BenchmarkArm:
    id: str
    pipeline: str
    prompt_contract: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "pipeline": self.pipeline,
            "prompt_contract": self.prompt_contract,
        }


@dataclass(frozen=True)
class BenchmarkModel:
    id: str
    label: str
    ordinary: bool

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "label": self.label, "ordinary": self.ordinary}


@dataclass(frozen=True)
class BenchmarkProtocol:
    benchmark_id: str
    seed: int
    repeats: int
    models: tuple[BenchmarkModel, ...]
    arms: tuple[BenchmarkArm, ...]
    metric_weights: tuple[tuple[str, float], ...]
    thresholds: dict[str, float]
    blind_review_rubric: tuple[str, ...]

    def weights_dict(self) -> dict[str, float]:
        return dict(self.metric_weights)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": BENCHMARK_SCHEMA_VERSION,
            "benchmark_id": self.benchmark_id,
            "seed": self.seed,
            "repeats": self.repeats,
            "models": [model.to_dict() for model in self.models],
            "arms": [arm.to_dict() for arm in self.arms],
            "metric_weights": self.weights_dict(),
            "thresholds": dict(sorted(self.thresholds.items())),
            "blind_review_rubric": list(self.blind_review_rubric),
        }


@dataclass(frozen=True)
class BenchmarkSpec:
    schema_version: str
    scenarios: tuple[BenchmarkScenario, ...]
    protocol: BenchmarkProtocol
    corpus_sha256: str
    protocol_sha256: str

    def scenario_by_id(self, scenario_id: str) -> BenchmarkScenario:
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        raise KeyError(f"unknown benchmark scenario: {scenario_id}")

    def arm_by_id(self, arm_id: str) -> BenchmarkArm:
        for arm in self.protocol.arms:
            if arm.id == arm_id:
                return arm
        raise KeyError(f"unknown benchmark arm: {arm_id}")


def _parse_fact(value: Any, path: str) -> BenchmarkFact:
    raw = _require_object(value, path)
    _require_exact_keys(raw, {"id", "text", "required_terms"}, path)
    return BenchmarkFact(
        id=_require_string(raw["id"], f"{path}.id"),
        text=_require_string(raw["text"], f"{path}.text"),
        required_terms=_require_strings(raw["required_terms"], f"{path}.required_terms"),
    )


def _parse_scenario(value: Any, path: str) -> BenchmarkScenario:
    raw = _require_object(value, path)
    required = {
        "id",
        "type",
        "title",
        "language",
        "audience",
        "objective",
        "expected_archetype",
        "slide_count_range",
        "required_beats",
        "expected_forms",
        "asset_condition",
        "facts",
        "prohibited_claims",
    }
    _require_exact_keys(raw, required, path)
    slide_range = raw["slide_count_range"]
    if (
        not isinstance(slide_range, list)
        or len(slide_range) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) for item in slide_range)
        or slide_range[0] < 1
        or slide_range[1] < slide_range[0]
    ):
        raise ValueError(f"{path}.slide_count_range is invalid")
    facts_raw = raw["facts"]
    if not isinstance(facts_raw, list) or len(facts_raw) < 3:
        raise ValueError(f"{path}.facts must contain at least three facts")
    facts = tuple(
        _parse_fact(item, f"{path}.facts[{index}]")
        for index, item in enumerate(facts_raw)
    )
    if len({fact.id for fact in facts}) != len(facts):
        raise ValueError(f"{path}.facts contains duplicate ids")
    scenario = BenchmarkScenario(
        id=_require_string(raw["id"], f"{path}.id"),
        presentation_type=_require_string(raw["type"], f"{path}.type"),
        title=_require_string(raw["title"], f"{path}.title"),
        language=_require_string(raw["language"], f"{path}.language"),
        audience=_require_string(raw["audience"], f"{path}.audience"),
        objective=_require_string(raw["objective"], f"{path}.objective"),
        expected_archetype=_require_string(
            raw["expected_archetype"], f"{path}.expected_archetype"
        ),
        slide_count_min=slide_range[0],
        slide_count_max=slide_range[1],
        required_beats=_require_strings(raw["required_beats"], f"{path}.required_beats"),
        expected_forms=_require_strings(raw["expected_forms"], f"{path}.expected_forms"),
        asset_condition=_require_string(raw["asset_condition"], f"{path}.asset_condition"),
        facts=facts,
        prohibited_claims=_require_strings(
            raw["prohibited_claims"], f"{path}.prohibited_claims"
        ),
    )
    if scenario.presentation_type != scenario.id or scenario.expected_archetype != scenario.id:
        raise ValueError(f"{path} must bind type and archetype to its registered id")
    return scenario


def _parse_protocol(value: Any) -> BenchmarkProtocol:
    raw = _require_object(value, "protocol")
    required = {
        "schema_version",
        "benchmark_id",
        "seed",
        "repeats",
        "models",
        "arms",
        "metric_weights",
        "thresholds",
        "blind_review_rubric",
    }
    _require_exact_keys(raw, required, "protocol")
    if raw["schema_version"] != BENCHMARK_SCHEMA_VERSION:
        raise ValueError("protocol.schema_version must equal 1.0")
    if isinstance(raw["seed"], bool) or not isinstance(raw["seed"], int):
        raise ValueError("protocol.seed must be an integer")
    if raw["repeats"] != 2:
        raise ValueError("protocol.repeats must remain frozen at two")
    models_raw = raw["models"]
    if not isinstance(models_raw, list) or len(models_raw) != 2:
        raise ValueError("protocol.models must contain two ordinary models")
    models: list[BenchmarkModel] = []
    for index, value_model in enumerate(models_raw):
        model = _require_object(value_model, f"protocol.models[{index}]")
        _require_exact_keys(model, {"id", "label", "ordinary"}, f"protocol.models[{index}]")
        if model["ordinary"] is not True:
            raise ValueError("benchmark models must be marked ordinary")
        models.append(
            BenchmarkModel(
                _require_string(model["id"], f"protocol.models[{index}].id"),
                _require_string(model["label"], f"protocol.models[{index}].label"),
                True,
            )
        )
    arms_raw = raw["arms"]
    if not isinstance(arms_raw, list) or len(arms_raw) != 3:
        raise ValueError("protocol.arms must contain three arms")
    arms: list[BenchmarkArm] = []
    for index, value_arm in enumerate(arms_raw):
        arm = _require_object(value_arm, f"protocol.arms[{index}]")
        _require_exact_keys(
            arm, {"id", "pipeline", "prompt_contract"}, f"protocol.arms[{index}]"
        )
        arms.append(
            BenchmarkArm(
                _require_string(arm["id"], f"protocol.arms[{index}].id"),
                _require_string(arm["pipeline"], f"protocol.arms[{index}].pipeline"),
                _require_string(
                    arm["prompt_contract"], f"protocol.arms[{index}].prompt_contract"
                ),
            )
        )
    if tuple(arm.id for arm in arms) != EXPECTED_ARM_IDS:
        raise ValueError("protocol arm order/ids changed")
    weights_raw = _require_object(raw["metric_weights"], "protocol.metric_weights")
    if set(weights_raw) != set(EXPECTED_METRIC_IDS):
        raise ValueError("protocol metric ids changed")
    weights: list[tuple[str, float]] = []
    for key in sorted(weights_raw):
        value_weight = weights_raw[key]
        if isinstance(value_weight, bool) or not isinstance(value_weight, (int, float)):
            raise ValueError(f"protocol.metric_weights.{key} must be numeric")
        weights.append((key, float(value_weight)))
    if not math.isclose(sum(value for _key, value in weights), 1.0, abs_tol=1e-9):
        raise ValueError("protocol metric weights must total 1.0")
    thresholds_raw = _require_object(raw["thresholds"], "protocol.thresholds")
    if set(thresholds_raw) != set(EXPECTED_THRESHOLD_IDS):
        raise ValueError("protocol threshold ids changed")
    thresholds: dict[str, float] = {}
    for key, value_threshold in thresholds_raw.items():
        if isinstance(value_threshold, bool) or not isinstance(value_threshold, (int, float)):
            raise ValueError(f"protocol.thresholds.{key} must be numeric")
        thresholds[key] = float(value_threshold)
    return BenchmarkProtocol(
        benchmark_id=_require_string(raw["benchmark_id"], "protocol.benchmark_id"),
        seed=raw["seed"],
        repeats=raw["repeats"],
        models=tuple(models),
        arms=tuple(arms),
        metric_weights=tuple(weights),
        thresholds=dict(sorted(thresholds.items())),
        blind_review_rubric=_require_strings(
            raw["blind_review_rubric"], "protocol.blind_review_rubric"
        ),
    )


def load_benchmark_spec(root: Path | str) -> BenchmarkSpec:
    benchmark_root = Path(root)
    corpus_path = benchmark_root / "scenarios.json"
    protocol_path = benchmark_root / "protocol.json"
    try:
        corpus_raw = json.loads(corpus_path.read_text(encoding="utf-8"))
        protocol_raw = json.loads(protocol_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load frozen benchmark: {exc}") from exc
    corpus = _require_object(corpus_raw, "corpus")
    _require_exact_keys(corpus, {"schema_version", "scenarios"}, "corpus")
    if corpus["schema_version"] != BENCHMARK_SCHEMA_VERSION:
        raise ValueError("corpus.schema_version must equal 1.0")
    scenarios_raw = corpus["scenarios"]
    if not isinstance(scenarios_raw, list):
        raise ValueError("corpus.scenarios must be an array")
    scenarios = tuple(
        _parse_scenario(item, f"corpus.scenarios[{index}]")
        for index, item in enumerate(scenarios_raw)
    )
    if tuple(scenario.id for scenario in scenarios) != EXPECTED_SCENARIO_IDS:
        raise ValueError("benchmark scenario order/coverage changed")
    protocol = _parse_protocol(protocol_raw)
    return BenchmarkSpec(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        scenarios=scenarios,
        protocol=protocol,
        corpus_sha256=canonical_sha256(corpus_raw),
        protocol_sha256=canonical_sha256(protocol_raw),
    )


@dataclass(frozen=True)
class BenchmarkTrial:
    trial_id: str
    scenario_id: str
    arm_id: str
    model_id: str
    repeat_index: int
    seed: int
    prompt_sha256: str
    input_sha256: str
    status: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "scenario_id": self.scenario_id,
            "arm_id": self.arm_id,
            "model_id": self.model_id,
            "repeat_index": self.repeat_index,
            "seed": self.seed,
            "prompt_sha256": self.prompt_sha256,
            "input_sha256": self.input_sha256,
            "status": self.status,
        }


@dataclass(frozen=True)
class BenchmarkManifest:
    schema_version: str
    benchmark_id: str
    corpus_sha256: str
    protocol_sha256: str
    thresholds_sha256: str
    trials: tuple[BenchmarkTrial, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "benchmark_id": self.benchmark_id,
            "corpus_sha256": self.corpus_sha256,
            "protocol_sha256": self.protocol_sha256,
            "thresholds_sha256": self.thresholds_sha256,
            "trials": [trial.to_dict() for trial in self.trials],
        }


def _prompt_input(scenario: BenchmarkScenario, arm: BenchmarkArm) -> dict[str, Any]:
    payload = scenario.to_dict()
    if arm.id == "full-v5":
        archetype = resolve_archetype(scenario.id)
        payload["full_v5_registry_contract"] = {
            "required_critical_beats": list(load_narrative_rules()[scenario.id]),
            "allowed_beat_hints": [
                beat
                for beat in archetype.sections
                if beat not in {"cover", "agenda", "closing"}
            ],
            "fact_reference_policy": "reference every fact id exactly once",
            "free_text_policy": "do not copy, paraphrase, or invent factual text",
        }
    return payload


def _compose_trial_prompt(scenario: BenchmarkScenario, arm: BenchmarkArm) -> str:
    return (
        f"{arm.prompt_contract}\n\n"
        "Use only the frozen brief below. Preserve every fact and do not repeat "
        "the prohibited claims.\n\n"
        + canonical_json(_prompt_input(scenario, arm))
    )


def build_trial_prompt(spec: BenchmarkSpec, trial: BenchmarkTrial) -> str:
    return _compose_trial_prompt(
        spec.scenario_by_id(trial.scenario_id), spec.arm_by_id(trial.arm_id)
    )


def build_trial_manifest(spec: BenchmarkSpec) -> BenchmarkManifest:
    trials: list[BenchmarkTrial] = []
    for scenario in spec.scenarios:
        for arm in spec.protocol.arms:
            for model in spec.protocol.models:
                for repeat_index in range(1, spec.protocol.repeats + 1):
                    prompt = _compose_trial_prompt(scenario, arm)
                    trial_basis = {
                        "benchmark_id": spec.protocol.benchmark_id,
                        "corpus_sha256": spec.corpus_sha256,
                        "protocol_sha256": spec.protocol_sha256,
                        "scenario": scenario.to_dict(),
                        "arm": arm.to_dict(),
                        "model": model.to_dict(),
                        "repeat_index": repeat_index,
                        "seed": spec.protocol.seed,
                        "prompt": prompt,
                    }
                    input_sha = canonical_sha256(trial_basis)
                    seed = int(input_sha[:8], 16)
                    model_slug = re.sub(r"[^a-z0-9]+", "-", model.label.casefold()).strip("-")
                    trial_id = (
                        f"T-{scenario.id}-{arm.id}-{model_slug}-r{repeat_index}-{input_sha[:8]}"
                    )
                    trials.append(
                        BenchmarkTrial(
                            trial_id=trial_id,
                            scenario_id=scenario.id,
                            arm_id=arm.id,
                            model_id=model.id,
                            repeat_index=repeat_index,
                            seed=seed,
                            prompt_sha256=canonical_sha256(prompt),
                            input_sha256=input_sha,
                        )
                    )
    return BenchmarkManifest(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        benchmark_id=spec.protocol.benchmark_id,
        corpus_sha256=spec.corpus_sha256,
        protocol_sha256=spec.protocol_sha256,
        thresholds_sha256=canonical_sha256(spec.protocol.thresholds),
        trials=tuple(trials),
    )


@dataclass(frozen=True)
class ArtifactDigest:
    relative_path: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


def digest_artifact(path: Path | str, *, root: Path | str) -> ArtifactDigest:
    artifact = Path(path)
    base = Path(root).resolve()
    resolved = artifact.resolve(strict=True)
    try:
        relative = resolved.relative_to(base)
    except ValueError as exc:
        raise ValueError("benchmark artifact is outside its governed root") from exc
    data = resolved.read_bytes()
    return ArtifactDigest(
        relative_path=relative.as_posix(),
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
    )


def verify_artifact_digest(digest: ArtifactDigest, *, root: Path | str) -> bool:
    if not SHA256_PATTERN.fullmatch(digest.sha256):
        return False
    try:
        current = digest_artifact(Path(root) / digest.relative_path, root=root)
    except (OSError, ValueError):
        return False
    return current == digest


@dataclass(frozen=True)
class TrialScorecard:
    schema_version: str
    trial_id: str
    scenario_id: str
    arm_id: str
    model_id: str
    repeat_index: int
    status: str
    failure_code: str | None
    failure_detail: str | None
    raw_response_sha256: str | None
    deck_plan_sha256: str | None
    compiled_sha256: str | None
    render_plan_sha256: str | None
    quality_report_sha256: str | None
    metrics: dict[str, float]
    violations: tuple[str, ...]
    composite: float | None
    artifact_digests: tuple[ArtifactDigest, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trial_id": self.trial_id,
            "scenario_id": self.scenario_id,
            "arm_id": self.arm_id,
            "model_id": self.model_id,
            "repeat_index": self.repeat_index,
            "status": self.status,
            "failure_code": self.failure_code,
            "failure_detail": self.failure_detail,
            "raw_response_sha256": self.raw_response_sha256,
            "deck_plan_sha256": self.deck_plan_sha256,
            "compiled_sha256": self.compiled_sha256,
            "render_plan_sha256": self.render_plan_sha256,
            "quality_report_sha256": self.quality_report_sha256,
            "metrics": dict(sorted(self.metrics.items())),
            "violations": list(self.violations),
            "composite": self.composite,
            "artifact_digests": [item.to_dict() for item in self.artifact_digests],
        }


def _scorecard(
    trial: BenchmarkTrial,
    *,
    status: str,
    failure_code: str | None = None,
    failure_detail: str | None = None,
    raw_response_sha256: str | None = None,
    deck_plan_sha256: str | None = None,
    compiled_sha256: str | None = None,
    render_plan_sha256: str | None = None,
    quality_report_sha256: str | None = None,
    metrics: dict[str, float] | None = None,
    violations: tuple[str, ...] = (),
    composite: float | None = None,
) -> TrialScorecard:
    return TrialScorecard(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        trial_id=trial.trial_id,
        scenario_id=trial.scenario_id,
        arm_id=trial.arm_id,
        model_id=trial.model_id,
        repeat_index=trial.repeat_index,
        status=status,
        failure_code=failure_code,
        failure_detail=failure_detail,
        raw_response_sha256=raw_response_sha256,
        deck_plan_sha256=deck_plan_sha256,
        compiled_sha256=compiled_sha256,
        render_plan_sha256=render_plan_sha256,
        quality_report_sha256=quality_report_sha256,
        metrics=dict(metrics or {}),
        violations=violations,
        composite=composite,
    )


def _extract_response_json(raw_response: str) -> Any:
    stripped = raw_response.strip()
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", stripped)
    if fenced is not None:
        return json.loads(fenced.group(1))
    decoder = json.JSONDecoder()
    for index, character in enumerate(stripped):
        if character != "{":
            continue
        try:
            value, _end = decoder.raw_decode(stripped[index:])
            return value
        except json.JSONDecodeError:
            continue
    return json.loads(stripped)


def _extract_trial_payload(trial: BenchmarkTrial, raw_response: str) -> Any:
    """Apply the production response boundary for the governed weak-model arm."""

    if trial.arm_id != "full-v5":
        return _extract_response_json(raw_response)
    payload, _trace = normalize_brief_plan(raw_response)
    return payload


def _max_run(values: list[str]) -> int:
    maximum = 0
    previous: str | None = None
    current = 0
    for value in values:
        if value == previous:
            current += 1
        else:
            previous = value
            current = 1
        maximum = max(maximum, current)
    return maximum


def _normalize_evidence_text(value: str) -> str:
    normalized = (
        value.casefold()
        .replace("\\n", " ")
        .replace("\\r", " ")
        .replace("\\t", " ")
        .replace(",", "")
    )
    normalized = re.sub(r"\$\s*([0-9]+(?:\.[0-9]+)?)\s*m\b", r"\1 million", normalized)
    normalized = re.sub(r"\$\s*([0-9]+(?:\.[0-9]+)?)\s*b\b", r"\1 billion", normalized)
    normalized = re.sub(r"\$\s*([0-9]+(?:\.[0-9]+)?)\s*k\b", r"\1 thousand", normalized)
    normalized = re.sub(r"([0-9]+(?:\.[0-9]+)?)\s*%", r"\1 percent", normalized)
    normalized = normalized.replace("dollars", "").replace("dollar", "")
    normalized = re.sub(r"[^a-z0-9.]+", " ", normalized)
    return " ".join(normalized.split())


_NUMERIC_CLAIM_PATTERN = re.compile(
    r"\b(?:"
    r"(?:19|20)\d{2}"
    r"|(?<![\d.])\d+(?:\.\d+)?\s+(?:"
    r"percent(?:age point)?s?|cagr|million|billion|thousand|"
    r"hours?|minutes?|days?|weeks?|months?|years?|"
    r"customer teams?|customers?|records?|retailers?|warehouses?|offices?|brands?|regions?|"
    r"subscriptions?|releases?|pillars?"
    r")"
    r")\b"
)


def _numeric_claims(value: str) -> set[str]:
    """Extract governed quantities while ignoring schema versions and slide indexes."""

    normalized = _normalize_evidence_text(value)
    return {
        " ".join(match.group(0).split())
        for match in _NUMERIC_CLAIM_PATTERN.finditer(normalized)
    }


def _composite(metrics: Mapping[str, float], weights: Mapping[str, float]) -> float:
    return round(
        100.0 * sum(weights[key] * metrics.get(key, 0.0) for key in weights),
        4,
    )


def _benchmark_beat_sequence(scenario: BenchmarkScenario) -> tuple[str, ...]:
    archetype = resolve_archetype(scenario.id)
    critical = load_narrative_rules()[scenario.id][0]
    requested = tuple(
        beat.casefold().replace(" ", "-")
        for beat in scenario.required_beats
        if beat.casefold().replace(" ", "-") in archetype.sections
    )
    return tuple(
        dict.fromkeys(
            (
                critical,
                *requested,
                *(
                    beat
                    for beat in archetype.sections
                    if beat not in {"cover", "agenda", "closing"}
                ),
            )
        )
    )


def _benchmark_semantic(value: str) -> str:
    return {
        "cards": "bullets",
        "case-study": "statement",
        "competition": "matrix",
        "product-showcase": "image",
        "practice": "process",
        "team": "bullets",
    }.get(value, value if value in {
        "statement", "bullets", "metrics", "comparison", "sequence",
        "timeline", "process", "roadmap", "quadrant", "funnel", "trend",
        "composition", "matrix", "risk", "recommendation", "quote", "table",
        "image", "generic",
    } else "statement")


_BENCHMARK_MEASURE_PATTERN = re.compile(
    r"(?P<value>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s+"
    r"(?P<unit>percent|percentage points?|million dollars?|billion dollars?|"
    r"thousand dollars?|accounts?|customer teams?|customers?|records?|retailers?|warehouses?|"
    r"offices?|brands?|regions?|subscriptions?|releases?|hours?|minutes?|"
    r"days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
_BENCHMARK_WORD_MEASURE_PATTERN = re.compile(
    r"\b(?P<value>zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|"
    r"nineteen|twenty(?:-(?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"thirty(?:-(?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"forty(?:-(?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"fifty(?:-(?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"sixty(?:-(?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"seventy(?:-(?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"eighty(?:-(?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"ninety(?:-(?:one|two|three|four|five|six|seven|eight|nine))?)\s+"
    r"(?P<unit>percent|percentage points?)\b",
    re.IGNORECASE,
)


def _benchmark_fact_fields(fact: BenchmarkFact) -> dict[str, Any]:
    """Derive only exact, source-present structure for benchmark facts.

    The benchmark harness must not manufacture trusted design advice.  Earlier
    versions mechanically cycled ``recommended_beat`` and
    ``recommended_semantic`` across facts; that overrode correct ordinary-model
    choices and split related evidence.  This helper records conservative data
    structure only: exact numeric tokens, their explicit unit, an id-derived
    claim key, and an explicit quarter/year token when present.
    """

    lowered = fact.text.casefold()
    instruction_markers = (
        "priority",
        "priorities",
        "recommend",
        "recommended",
        "must ",
        "should ",
        "next step",
        "call to action",
    )
    word_measure = _BENCHMARK_WORD_MEASURE_PATTERN.search(fact.text)
    result: dict[str, Any] = {
        "kind": (
            "instruction"
            if any(marker in lowered for marker in instruction_markers)
            else "metric"
            if re.search(r"\d", fact.text) or word_measure is not None
            else "claim"
        )
    }
    id_parts = fact.id.split("-")
    claim_key = "-".join(id_parts[1:]) if len(id_parts) > 1 else fact.id
    if claim_key:
        result["claim_key"] = claim_key
    if result["kind"] == "metric":
        matches = tuple(_BENCHMARK_MEASURE_PATTERN.finditer(fact.text))
        if matches:
            selected = (
                matches[-1]
                if " from " in f" {lowered} " and " to " in f" {lowered} "
                else next(
                    (
                        match
                        for match in matches
                        if "dollar" in match.group("unit").casefold()
                    ),
                    matches[0],
                )
            )
            raw_value = selected.group("value").replace(",", "")
            result["value"] = (
                float(raw_value) if "." in raw_value else int(raw_value)
            )
            result["unit"] = selected.group("unit")
        elif word_measure is not None:
            # Preserve the exact authored number word.  The Skill may give it
            # metric hierarchy, but never silently translate or round it.
            result["value"] = word_measure.group("value")
            result["unit"] = word_measure.group("unit")
        time_scope = re.search(r"\bQ[1-4]\b|\b(?:19|20)\d{2}\b", fact.text)
        if time_scope is not None:
            result["time_scope"] = time_scope.group(0)
    return result


def build_benchmark_fact_store(scenario: BenchmarkScenario) -> dict[str, Any]:
    """Build trusted benchmark facts outside the ordinary-model response contract."""

    return {
        "schema_version": "1.0",
        "project": {
            "title": scenario.title,
            "objective": scenario.objective,
            "audience": scenario.audience,
            "language": scenario.language,
        },
        "sources": [
            {
                "id": "benchmark",
                "kind": "request",
                "locator": f"benchmarks/v5/scenarios.json#{scenario.id}",
            }
        ],
        "facts": [
            {
                "id": fact.id,
                "text": fact.text,
                "language": scenario.language,
                "source_id": "benchmark",
                "locator": f"{scenario.id}/{fact.id}",
                "required": True,
                **_benchmark_fact_fields(fact),
            }
            for fact in scenario.facts
        ],
    }


def _prepare_full_v5(
    scenario: BenchmarkScenario,
    brief_payload: Mapping[str, Any],
    *,
    installed_fonts: set[str],
) -> tuple[dict[str, Any], BriefGeneration]:
    fact_store = build_benchmark_fact_store(scenario)
    generation = prepare_brief_generation(
        fact_store,
        brief_payload,
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts=installed_fonts,
        direction_mode="auto",
        design_system_version="art-direction-v1",
        build_render=True,
    )
    if generation.render_plan is None:
        raise RuntimeError("full-v5 benchmark did not build a RenderPlan")
    return fact_store, generation


def _benchmark_fonts(installed_fonts: set[str] | None) -> set[str]:
    """Resolve the exact font inventory used by benchmark compilation.

    Formal callers pass the hash-bound fingerprint inventory. Diagnostic and
    unit-test callers discover the current host inventory rather than silently
    pretending that Arial is the only installed font.
    """

    fonts = (
        {str(font).strip() for font in installed_fonts if str(font).strip()}
        if installed_fonts is not None
        else set(discover_installed_fonts())
    )
    if not fonts:
        raise ValueError("benchmark font inventory is empty")
    return fonts


def evaluate_trial_response(
    spec: BenchmarkSpec,
    trial: BenchmarkTrial,
    raw_response: str | None,
    *,
    installed_fonts: set[str] | None = None,
) -> TrialScorecard:
    """Evaluate an immutable provider response without repairing or rewriting it."""

    spec.scenario_by_id(trial.scenario_id)
    spec.arm_by_id(trial.arm_id)
    if raw_response is None:
        return _scorecard(
            trial,
            status="unavailable",
            failure_code="PROVIDER_UNAVAILABLE",
            failure_detail="provider returned no model response",
        )
    if not isinstance(raw_response, str):
        raise TypeError("raw benchmark response must be text or None")
    raw_hash = canonical_sha256(raw_response)
    try:
        payload = _extract_trial_payload(trial, raw_response)
    except (AttributeError, json.JSONDecodeError, WeakModelValidationError, ValueError):
        return _scorecard(
            trial,
            status="invalid",
            failure_code="RESPONSE_JSON_INVALID",
            failure_detail=(
                "response is not one production-compatible JSON object "
                "(an exact whole-response JSON fence is allowed for full-v5)"
            ),
            raw_response_sha256=raw_hash,
            metrics={"response_json_valid": 0.0},
            composite=0.0,
        )
    if not isinstance(payload, dict):
        return _scorecard(
            trial,
            status="invalid",
            failure_code="RESPONSE_JSON_INVALID",
            failure_detail="response JSON root is not an object",
            raw_response_sha256=raw_hash,
            metrics={"response_json_valid": 0.0},
            composite=0.0,
        )

    scenario = spec.scenario_by_id(trial.scenario_id)
    searchable = _normalize_evidence_text(canonical_json(payload))
    retained = sum(
        all(_normalize_evidence_text(term) in searchable for term in fact.required_terms)
        for fact in scenario.facts
    )
    prohibited_violations = tuple(
        claim
        for claim in scenario.prohibited_claims
        if _normalize_evidence_text(claim) in searchable
    )
    allowed_numeric_claims = set().union(
        *(_numeric_claims(fact.text) for fact in scenario.facts)
    )
    prohibited_numeric_claims = set().union(
        *(_numeric_claims(claim) for claim in scenario.prohibited_claims)
    )
    allowed_numeric_claims -= prohibited_numeric_claims
    unsupported_numeric_claims = tuple(
        sorted(_numeric_claims(canonical_json(payload)) - allowed_numeric_claims)
    )
    violations = prohibited_violations + tuple(
        f"UNSUPPORTED_NUMERIC:{claim}" for claim in unsupported_numeric_claims
    )
    metrics = {
        "response_json_valid": 1.0,
        "deck_plan_valid": 0.0,
        "fact_retention": retained / len(scenario.facts),
        "prohibited_claim_safety": 1.0 if not prohibited_violations else 0.0,
        "numeric_claim_safety": 1.0 if not unsupported_numeric_claims else 0.0,
        "compile_success": 0.0,
        "archetype_match": 0.0,
        "slide_count_fit": 0.0,
        "semantic_form_coverage": 0.0,
        "rhythm_compliance": 0.0,
        "native_editable_coverage": 0.0,
        "hard_gate_pass": 0.0,
    }
    fonts = _benchmark_fonts(installed_fonts)
    if trial.arm_id == "full-v5":
        try:
            _fact_store, generation = _prepare_full_v5(
                scenario,
                payload,
                installed_fonts=fonts,
            )
        except (WeakModelValidationError, GenerationGateError, ValueError) as exc:
            return _scorecard(
                trial,
                status="invalid",
                failure_code="BRIEF_PLAN_INVALID",
                failure_detail=str(exc),
                raw_response_sha256=raw_hash,
                metrics=metrics,
                violations=violations,
                composite=_composite(metrics, spec.protocol.weights_dict()),
            )
        metrics["deck_plan_valid"] = 1.0
        metrics["fact_retention"] = float(
            generation.compilation.narrative.coverage["required_fact_coverage"]
        )
        deck_plan = generation.effective_deck_plan
        compiled = generation.compiled_deck
        render_plan = generation.render_plan
        if render_plan is None:
            raise RuntimeError("full-v5 benchmark lost its RenderPlan")
    else:
        try:
            validate_deck_plan(payload)
            metrics["deck_plan_valid"] = 1.0
        except DeckPlanValidationError as exc:
            return _scorecard(
                trial,
                status="invalid",
                failure_code="DECK_PLAN_INVALID",
                failure_detail=str(exc),
                raw_response_sha256=raw_hash,
                deck_plan_sha256=canonical_sha256(payload),
                metrics=metrics,
                violations=violations,
                composite=_composite(metrics, spec.protocol.weights_dict()),
            )
        deck_plan = payload
        try:
            compiled, render_plan = compile_render_plan(
                deck_plan,
                slide_size=SlideSize(13.333, 7.5),
                installed_fonts=fonts,
            )
        except (DeckPlanValidationError, RenderPlanError, ValueError) as exc:
            return _scorecard(
                trial,
                status="failed",
                failure_code="COMPILE_FAILED",
                failure_detail=str(exc),
                raw_response_sha256=raw_hash,
                deck_plan_sha256=canonical_sha256(deck_plan),
                metrics=metrics,
                violations=violations,
                composite=_composite(metrics, spec.protocol.weights_dict()),
            )

    deck_plan_hash = canonical_sha256(deck_plan)
    if not isinstance(compiled, dict):
        return _scorecard(
            trial,
            status="failed",
            failure_code="COMPILE_FAILED",
            failure_detail="compiler returned a non-object document",
            raw_response_sha256=raw_hash,
            deck_plan_sha256=deck_plan_hash,
            metrics=metrics,
            violations=violations,
            composite=_composite(metrics, spec.protocol.weights_dict()),
        )

    # Re-run quantity safety over the generated delivery semantics, not only
    # over the ordinary model's JSON.  Deterministic compilation is trusted
    # for layout, but it is still capable of breaking a value/unit binding
    # (for example, rendering source-present "3 hours" as "3 minutes").
    # Such a defect must be visible in the benchmark even when every numeric
    # token independently appeared in the source.
    generated_numeric_claims = _numeric_claims(
        canonical_json(
            {
                "deck_plan": deck_plan,
                "compiled": compiled,
                "render_plan": render_plan.to_dict(),
            }
        )
    )
    unsupported_numeric_claims = tuple(
        sorted(
            set(unsupported_numeric_claims)
            | (generated_numeric_claims - allowed_numeric_claims)
        )
    )
    violations = prohibited_violations + tuple(
        f"UNSUPPORTED_NUMERIC:{claim}" for claim in unsupported_numeric_claims
    )
    metrics["numeric_claim_safety"] = (
        1.0 if not unsupported_numeric_claims else 0.0
    )

    metrics["compile_success"] = 1.0
    metrics["archetype_match"] = (
        1.0 if compiled.get("archetype_id") == scenario.expected_archetype else 0.0
    )
    slide_count = len(compiled["slides"])
    metrics["slide_count_fit"] = (
        1.0 if scenario.slide_count_min <= slide_count <= scenario.slide_count_max else 0.0
    )
    semantic_forms = {
        str(slide.get("page_family", "")) for slide in compiled["slides"]
    }
    semantic_forms.update(
        {
            "risk" if str(slide.get("role", "")) in {"risk", "risks", "issues"}
            else "recommendation"
            if str(slide.get("role", ""))
            in {"recommendation", "recommendations", "action-plan", "next-steps"}
            else "trend"
            if str(slide.get("role", "")) in {"trend", "trends", "market-trends"}
            else str(slide.get("role", ""))
            for slide in compiled["slides"]
        }
    )
    semantic_forms.update(
        str(block.get("kind", ""))
        for slide in compiled["slides"]
        for block in slide.get("blocks", [])
    )
    metrics["semantic_form_coverage"] = sum(
        form in semantic_forms for form in scenario.expected_forms
    ) / len(scenario.expected_forms)
    family_sequence = [str(slide.get("page_family", "")) for slide in compiled["slides"]]
    metrics["rhythm_compliance"] = 1.0 if _max_run(family_sequence) <= 2 else 0.0
    compiled_hash = canonical_sha256(compiled)
    render_hash = canonical_sha256(render_plan.to_dict())
    return _scorecard(
        trial,
        status="evaluated",
        raw_response_sha256=raw_hash,
        deck_plan_sha256=deck_plan_hash,
        compiled_sha256=compiled_hash,
        render_plan_sha256=render_hash,
        # Delivery metrics remain zero until the real portable bundle succeeds.
        # A RecordingPresentation is intentionally never accepted as benchmark
        # delivery evidence.
        quality_report_sha256=None,
        metrics=metrics,
        violations=violations,
        composite=_composite(metrics, spec.protocol.weights_dict()),
    )


@dataclass(frozen=True)
class TrialEvaluation:
    """A scorecard plus the deterministic documents used to derive its hashes."""

    scorecard: TrialScorecard
    documents: tuple[tuple[str, dict[str, Any]], ...] = ()
    compiled_deck: Mapping[str, Any] | None = None
    render_plan: RenderPlan | None = None
    quality_v2_findings: tuple[QualityFindingV2, ...] = ()


def evaluate_trial_evidence(
    spec: BenchmarkSpec,
    trial: BenchmarkTrial,
    raw_response: str | None,
    *,
    installed_fonts: set[str] | None = None,
) -> TrialEvaluation:
    """Evaluate one response and expose independently auditable pipeline documents."""

    fonts = _benchmark_fonts(installed_fonts)
    score = evaluate_trial_response(
        spec,
        trial,
        raw_response,
        installed_fonts=fonts,
    )
    if score.status != "evaluated" or raw_response is None:
        return TrialEvaluation(scorecard=score)

    payload = _extract_trial_payload(trial, raw_response)
    if not isinstance(payload, dict):
        raise RuntimeError("evaluated response no longer contains a plan object")
    scenario = spec.scenario_by_id(trial.scenario_id)
    if trial.arm_id == "full-v5":
        fact_store, generation = _prepare_full_v5(
            scenario,
            payload,
            installed_fonts=fonts,
        )
        deck_plan = generation.effective_deck_plan
        compiled = generation.compiled_deck
        render_plan = generation.render_plan
        if render_plan is None or generation.direction is None:
            raise RuntimeError("full-v5 evidence lost governed design artifacts")
        documents: list[tuple[str, dict[str, Any]]] = [
            ("fact-store.json", fact_store),
            ("brief-plan.json", payload),
            ("narrative-plan.json", generation.compilation.narrative.to_dict()),
            ("direction-decision.json", generation.direction.to_dict()),
            (
                "generation-manifest.json",
                generation.to_dict(include_render_plan=False),
            ),
            (
                "repair-log.v2.json",
                {
                    "schema_version": "2.0",
                    "passes": [
                        {
                            "stage": item.stage,
                            "before_vector": list(item.before_vector),
                            "after_vector": list(item.after_vector),
                            "accepted": item.accepted,
                            "rolled_back": item.rolled_back,
                            "failure_code": item.failure_code,
                        }
                        for item in generation.pre_render_repair_passes
                    ],
                },
            ),
        ]
        quality_findings = (
            *generation_quality_findings(generation),
            *inspect_design_quality(generation),
        )
    else:
        deck_plan = payload
        compiled, render_plan = compile_render_plan(
            deck_plan,
            slide_size=SlideSize(13.333, 7.5),
            installed_fonts=fonts,
        )
        documents = []
        quality_findings = ()
    render_document = render_plan.to_dict()
    documents.extend(
        [
            ("deck-plan.json", deck_plan),
            ("compiled-plan.json", compiled),
            ("render-plan.json", render_document),
        ]
    )

    expected_hashes = {
        "deck-plan.json": score.deck_plan_sha256,
        "compiled-plan.json": score.compiled_sha256,
        "render-plan.json": score.render_plan_sha256,
    }
    for name, expected_hash in expected_hashes.items():
        document = dict(documents)[name]
        if canonical_sha256(document) != expected_hash:
            raise RuntimeError(f"benchmark evidence hash drifted: {name}")

    return TrialEvaluation(
        scorecard=score,
        documents=tuple(documents),
        compiled_deck=compiled,
        render_plan=render_plan,
        quality_v2_findings=tuple(quality_findings),
    )


def finalize_portable_trial_scorecard(
    spec: BenchmarkSpec,
    evaluation: TrialEvaluation,
    result: PortablePipelineResult,
) -> TrialScorecard:
    """Bind a full-v5 scorecard to a promoted, real portable delivery bundle."""

    score = evaluation.scorecard
    if score.arm_id != "full-v5" or score.status != "evaluated":
        raise ValueError("portable finalization requires an evaluated full-v5 plan")
    if (
        result.render_report is None
        or result.verification is None
        or result.candidate_result is None
        or not result.candidate_result.promoted
    ):
        raise ValueError("portable finalization requires promoted delivery evidence")
    quality = result.verification.quality
    if not quality.passed or quality.hard_gate_failures:
        raise ValueError("portable finalization requires a passing Quality-v2 report")
    report = result.render_report
    expected_editable_count = (
        report.planned_object_count + report.diagram_child_count
    )
    editable_coverage = (
        1.0
        if expected_editable_count == 0
        else report.native_editable_count / expected_editable_count
    )
    if not 0.0 <= editable_coverage <= 1.0:
        raise ValueError("portable renderer returned invalid editability coverage")
    metrics = {
        **score.metrics,
        "native_editable_coverage": float(editable_coverage),
        "hard_gate_pass": 1.0,
    }
    return replace(
        score,
        quality_report_sha256=canonical_sha256(quality.to_dict()),
        metrics=metrics,
        composite=_composite(metrics, spec.protocol.weights_dict()),
    )


def fail_portable_trial_scorecard(
    spec: BenchmarkSpec,
    score: TrialScorecard,
    *,
    failure_code: str,
    failure_detail: str,
    quality_report: Mapping[str, Any] | None = None,
) -> TrialScorecard:
    """Fail closed after portable delivery without discarding plan evidence."""

    if score.arm_id != "full-v5":
        raise ValueError("portable failure is only valid for the full-v5 arm")
    metrics = {
        **score.metrics,
        "native_editable_coverage": 0.0,
        "hard_gate_pass": 0.0,
    }
    return replace(
        score,
        status="failed",
        failure_code=failure_code,
        failure_detail=failure_detail.strip() or "portable delivery failed",
        quality_report_sha256=(
            canonical_sha256(dict(quality_report))
            if quality_report is not None
            else None
        ),
        metrics=metrics,
        composite=_composite(metrics, spec.protocol.weights_dict()),
    )


@dataclass(frozen=True)
class ProviderResponse:
    status: str
    response: str | None
    response_sha256: str | None
    exit_code: int | None
    stdout_sha256: str
    stderr_sha256: str
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "response_sha256": self.response_sha256,
            "exit_code": self.exit_code,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
        }


def parse_opencode_events(stdout: str) -> str | None:
    """Extract assistant text from OpenCode JSONL without treating logs as output."""

    parts: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("type") != "text":
            continue
        part = event.get("part")
        if isinstance(part, dict) and part.get("type") == "text":
            text = part.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts) if parts else None


def run_opencode_response(
    *,
    model_id: str,
    prompt: str,
    directory: Path | str,
    timeout_seconds: int,
    runner: Any = subprocess.run,
) -> ProviderResponse:
    """Run one ordinary-model trial without a shell or write permissions."""

    if timeout_seconds < 1:
        raise ValueError("OpenCode timeout must be positive")
    args = [
        "opencode",
        "--pure",
        "run",
        "--agent",
        "plan",
        "--model",
        model_id,
        "--format",
        "json",
        "--title",
        "window-pptx frozen benchmark trial",
        "--dir",
        str(Path(directory).resolve()),
        prompt,
    ]
    try:
        completed = runner(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return ProviderResponse(
            status="unavailable",
            response=None,
            response_sha256=None,
            exit_code=None,
            stdout_sha256=canonical_sha256(stdout),
            stderr_sha256=canonical_sha256(stderr),
            stdout=stdout,
            stderr=stderr,
        )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    response = parse_opencode_events(stdout) if completed.returncode == 0 else None
    return ProviderResponse(
        status="received" if response is not None else "unavailable",
        response=response,
        response_sha256=canonical_sha256(response) if response is not None else None,
        exit_code=completed.returncode,
        stdout_sha256=canonical_sha256(stdout),
        stderr_sha256=canonical_sha256(stderr),
        stdout=stdout,
        stderr=stderr,
    )


@dataclass(frozen=True)
class BlindReviewArtifact:
    kind: str
    review_path: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "review_path": self.review_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class BlindReviewEntry:
    blind_id: str
    scenario_id: str
    evidence_sha256: str
    rubric: tuple[str, ...]
    artifacts: tuple[BlindReviewArtifact, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "blind_id": self.blind_id,
            "scenario_id": self.scenario_id,
            "evidence_sha256": self.evidence_sha256,
            "rubric": list(self.rubric),
            "artifacts": [item.to_dict() for item in self.artifacts],
        }


@dataclass(frozen=True)
class BlindReviewPacket:
    schema_version: str
    benchmark_id: str
    packet_sha256: str
    delivery_evidence_ready: bool
    entries: tuple[BlindReviewEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "benchmark_id": self.benchmark_id,
            "packet_sha256": self.packet_sha256,
            "delivery_evidence_ready": self.delivery_evidence_ready,
            "entries": [entry.to_dict() for entry in self.entries],
        }


def load_blind_review_packet(
    value: Any,
    *,
    review_root: Path | str | None = None,
) -> BlindReviewPacket:
    """Reload a frozen blind packet and optionally re-verify every staged file."""

    raw = _require_object(value, "blind_review_packet")
    _require_exact_keys(
        raw,
        {
            "schema_version",
            "benchmark_id",
            "packet_sha256",
            "delivery_evidence_ready",
            "entries",
        },
        "blind_review_packet",
    )
    if raw["schema_version"] != BENCHMARK_SCHEMA_VERSION:
        raise ValueError("blind_review_packet.schema_version must equal 1.0")
    benchmark_id = _require_string(
        raw["benchmark_id"], "blind_review_packet.benchmark_id"
    )
    packet_sha256 = _require_string(
        raw["packet_sha256"], "blind_review_packet.packet_sha256"
    )
    if SHA256_PATTERN.fullmatch(packet_sha256) is None:
        raise ValueError("blind_review_packet.packet_sha256 must be SHA-256")
    delivery_evidence_ready = raw["delivery_evidence_ready"]
    if not isinstance(delivery_evidence_ready, bool):
        raise ValueError(
            "blind_review_packet.delivery_evidence_ready must be a boolean"
        )
    entries_raw = raw["entries"]
    if not isinstance(entries_raw, list) or not entries_raw:
        raise ValueError("blind_review_packet.entries must be a non-empty array")

    entries: list[BlindReviewEntry] = []
    blind_ids: set[str] = set()
    review_paths: set[str] = set()
    for entry_index, entry_value in enumerate(entries_raw):
        entry_path = f"blind_review_packet.entries[{entry_index}]"
        entry_raw = _require_object(entry_value, entry_path)
        _require_exact_keys(
            entry_raw,
            {"blind_id", "scenario_id", "evidence_sha256", "rubric", "artifacts"},
            entry_path,
        )
        blind_id = _require_string(entry_raw["blind_id"], f"{entry_path}.blind_id")
        if re.fullmatch(r"B-\d{3}-[0-9a-f]{8}", blind_id) is None:
            raise ValueError(f"{entry_path}.blind_id is invalid")
        if blind_id in blind_ids:
            raise ValueError("blind_review_packet blind_id values must be unique")
        blind_ids.add(blind_id)
        scenario_id = _require_string(
            entry_raw["scenario_id"], f"{entry_path}.scenario_id"
        )
        evidence_sha256 = _require_string(
            entry_raw["evidence_sha256"], f"{entry_path}.evidence_sha256"
        )
        if SHA256_PATTERN.fullmatch(evidence_sha256) is None:
            raise ValueError(f"{entry_path}.evidence_sha256 must be SHA-256")
        rubric = _require_strings(entry_raw["rubric"], f"{entry_path}.rubric")
        artifacts_raw = entry_raw["artifacts"]
        if not isinstance(artifacts_raw, list):
            raise ValueError(f"{entry_path}.artifacts must be an array")
        artifacts: list[BlindReviewArtifact] = []
        for artifact_index, artifact_value in enumerate(artifacts_raw):
            artifact_path = f"{entry_path}.artifacts[{artifact_index}]"
            artifact_raw = _require_object(artifact_value, artifact_path)
            _require_exact_keys(
                artifact_raw,
                {"kind", "review_path", "sha256", "size_bytes"},
                artifact_path,
            )
            kind = _require_string(artifact_raw["kind"], f"{artifact_path}.kind")
            if kind not in {"editable-pptx", "slide-preview"}:
                raise ValueError(f"{artifact_path}.kind is invalid")
            relative_path = _require_string(
                artifact_raw["review_path"], f"{artifact_path}.review_path"
            )
            normalized = Path(relative_path)
            if (
                normalized.is_absolute()
                or "\\" in relative_path
                or normalized.as_posix() != relative_path
                or ".." in normalized.parts
                or normalized.parts[:1] != (blind_id,)
            ):
                raise ValueError(f"{artifact_path}.review_path is unsafe")
            if relative_path in review_paths:
                raise ValueError(
                    "blind_review_packet artifact review_path values must be unique"
                )
            review_paths.add(relative_path)
            sha256 = _require_string(
                artifact_raw["sha256"], f"{artifact_path}.sha256"
            )
            if SHA256_PATTERN.fullmatch(sha256) is None:
                raise ValueError(f"{artifact_path}.sha256 must be SHA-256")
            size_bytes = artifact_raw["size_bytes"]
            if (
                isinstance(size_bytes, bool)
                or not isinstance(size_bytes, int)
                or size_bytes <= 0
            ):
                raise ValueError(f"{artifact_path}.size_bytes must be positive")
            artifacts.append(
                BlindReviewArtifact(
                    kind=kind,
                    review_path=relative_path,
                    sha256=sha256,
                    size_bytes=size_bytes,
                )
            )
        pptx = [item for item in artifacts if item.kind == "editable-pptx"]
        previews = [item for item in artifacts if item.kind == "slide-preview"]
        expected_previews = [
            f"{blind_id}/slide-{index:03d}.png"
            for index in range(1, len(previews) + 1)
        ]
        if delivery_evidence_ready and (
            len(pptx) != 1
            or pptx[0].review_path != f"{blind_id}/delivery.pptx"
            or [item.review_path for item in previews] != expected_previews
        ):
            raise ValueError(
                f"{entry_path}.artifacts lacks one PPTX and contiguous PNG previews"
            )
        entries.append(
            BlindReviewEntry(
                blind_id=blind_id,
                scenario_id=scenario_id,
                evidence_sha256=evidence_sha256,
                rubric=rubric,
                artifacts=tuple(artifacts),
            )
        )

    packet_basis = {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "benchmark_id": benchmark_id,
        "delivery_evidence_ready": delivery_evidence_ready,
        "entries": [entry.to_dict() for entry in entries],
    }
    if canonical_sha256(packet_basis) != packet_sha256:
        raise ValueError("blind_review_packet.packet_sha256 mismatch")
    packet = BlindReviewPacket(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        benchmark_id=benchmark_id,
        packet_sha256=packet_sha256,
        delivery_evidence_ready=delivery_evidence_ready,
        entries=tuple(entries),
    )

    if review_root is not None:
        root = Path(review_root).resolve()
        for entry in packet.entries:
            for artifact in entry.artifacts:
                digest = ArtifactDigest(
                    relative_path=artifact.review_path,
                    sha256=artifact.sha256,
                    size_bytes=artifact.size_bytes,
                )
                if not verify_artifact_digest(digest, root=root):
                    raise ValueError(
                        f"blind-review artifact hash mismatch: {artifact.review_path}"
                    )
                path = root / artifact.review_path
                try:
                    if artifact.kind == "editable-pptx":
                        validate_ooxml_package(path)
                    else:
                        read_raster_dimensions(path)
                except (OSError, ValueError, WindowPptxError) as exc:
                    raise ValueError(
                        f"blind-review artifact is unreadable: {artifact.review_path}"
                    ) from exc
    return packet


def _verified_review_artifacts(
    score: TrialScorecard,
    *,
    artifact_root: Path | None,
    review_root: Path | None,
    blind_id: str,
) -> tuple[BlindReviewArtifact, ...]:
    """Expose only verified delivery files under anonymized review paths."""

    if artifact_root is None or review_root is None or score.status != "evaluated":
        return ()
    pptx: list[ArtifactDigest] = []
    previews: list[ArtifactDigest] = []
    for digest in score.artifact_digests:
        relative = Path(digest.relative_path)
        suffix = relative.suffix.casefold()
        expected_prefix = Path("trials") / score.trial_id
        is_delivery = relative == expected_prefix / "delivery.pptx"
        is_slide_preview = (
            relative.parent == expected_prefix / "portable-proof"
            and re.fullmatch(r"slide-\d{3}", relative.stem) is not None
        )
        if not (is_delivery or is_slide_preview) or not verify_artifact_digest(
            digest, root=artifact_root
        ):
            continue
        path = artifact_root / digest.relative_path
        try:
            if is_delivery:
                validate_ooxml_package(path)
                pptx.append(digest)
            else:
                read_raster_dimensions(path)
                previews.append(digest)
        except (OSError, ValueError, WindowPptxError):
            continue
    previews.sort(key=lambda item: int(Path(item.relative_path).stem.rsplit("-", 1)[1]))
    expected_numbers = list(range(1, len(previews) + 1))
    observed_numbers = [
        int(Path(item.relative_path).stem.rsplit("-", 1)[1]) for item in previews
    ]
    if len(pptx) != 1 or not previews or observed_numbers != expected_numbers:
        return ()

    staged_now: list[Path] = []

    def stage(source_digest: ArtifactDigest, review_path: str) -> None:
        source = artifact_root / source_digest.relative_path
        target = review_root / review_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            existing = digest_artifact(target, root=review_root)
            if (
                existing.sha256 == source_digest.sha256
                and existing.size_bytes == source_digest.size_bytes
            ):
                return
            raise ValueError(f"blind-review staging target conflicts: {target}")
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
            shutil.copyfile(source, temporary)
            copied = digest_artifact(temporary, root=target.parent)
            if (
                copied.sha256 != source_digest.sha256
                or copied.size_bytes != source_digest.size_bytes
            ):
                raise ValueError("blind-review staged artifact hash mismatch")
            os.replace(temporary, target)
            temporary = None
            staged_now.append(target)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    try:
        stage(pptx[0], f"{blind_id}/delivery.pptx")
        for index, digest in enumerate(
            previews, start=1
        ):
            stage(digest, f"{blind_id}/slide-{index:03d}.png")
    except (OSError, ValueError):
        for target in reversed(staged_now):
            try:
                target.unlink()
            except OSError:
                pass
        return ()
    artifacts = [
        BlindReviewArtifact(
            "editable-pptx",
            f"{blind_id}/delivery.pptx",
            pptx[0].sha256,
            pptx[0].size_bytes,
        )
    ]
    artifacts.extend(
        BlindReviewArtifact(
            "slide-preview",
            f"{blind_id}/slide-{index:03d}.png",
            digest.sha256,
            digest.size_bytes,
        )
        for index, digest in enumerate(
            previews, start=1
        )
    )
    return tuple(artifacts)


def build_blind_review_packet(
    spec: BenchmarkSpec,
    scorecards: tuple[TrialScorecard, ...],
    *,
    artifact_root: Path | str | None = None,
    review_root: Path | str | None = None,
) -> tuple[BlindReviewPacket, dict[str, str]]:
    unique = {score.trial_id: score for score in scorecards}
    ordered = [unique[key] for key in sorted(unique)]
    random.Random(spec.protocol.seed).shuffle(ordered)
    entries: list[BlindReviewEntry] = []
    mapping: dict[str, str] = {}
    resolved_root = Path(artifact_root).resolve() if artifact_root is not None else None
    resolved_review_root = (
        Path(review_root).resolve() if review_root is not None else None
    )
    if (resolved_root is None) != (resolved_review_root is None):
        raise ValueError("artifact_root and review_root are required together")
    for index, score in enumerate(ordered, start=1):
        evidence_hash = canonical_sha256(score.to_dict())
        blind_id = f"B-{index:03d}-{evidence_hash[:8]}"
        artifacts = _verified_review_artifacts(
            score,
            artifact_root=resolved_root,
            review_root=resolved_review_root,
            blind_id=blind_id,
        )
        entries.append(
            BlindReviewEntry(
                blind_id=blind_id,
                scenario_id=score.scenario_id,
                evidence_sha256=evidence_hash,
                rubric=spec.protocol.blind_review_rubric,
                artifacts=artifacts,
            )
        )
        mapping[blind_id] = score.trial_id
    delivery_evidence_ready = bool(entries) and all(
        {artifact.kind for artifact in entry.artifacts}
        == {"editable-pptx", "slide-preview"}
        for entry in entries
    )
    packet_basis = {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "benchmark_id": spec.protocol.benchmark_id,
        "delivery_evidence_ready": delivery_evidence_ready,
        "entries": [entry.to_dict() for entry in entries],
    }
    packet = BlindReviewPacket(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        benchmark_id=spec.protocol.benchmark_id,
        packet_sha256=canonical_sha256(packet_basis),
        delivery_evidence_ready=delivery_evidence_ready,
        entries=tuple(entries),
    )
    return packet, mapping


@dataclass(frozen=True)
class BlindReviewScore:
    blind_id: str
    evidence_sha256: str
    scores: tuple[tuple[str, int], ...]
    notes: str | None

    @property
    def mean_score(self) -> float:
        return sum(value for _rubric, value in self.scores) / len(self.scores)

    def to_dict(self) -> dict[str, Any]:
        return {
            "blind_id": self.blind_id,
            "evidence_sha256": self.evidence_sha256,
            "scores": dict(self.scores),
            "notes": self.notes,
        }


@dataclass(frozen=True)
class BlindReviewScoreSheet:
    schema_version: str
    benchmark_id: str
    packet_sha256: str
    reviewer_id: str
    reviews: tuple[BlindReviewScore, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "benchmark_id": self.benchmark_id,
            "packet_sha256": self.packet_sha256,
            "reviewer_id": self.reviewer_id,
            "reviews": [review.to_dict() for review in self.reviews],
        }


@dataclass(frozen=True)
class BlindReviewGateReport:
    schema_version: str
    benchmark_id: str
    packet_sha256: str
    score_sheet_sha256: str
    reviewer_id: str
    status: str
    review_count: int
    score_count: int
    overall_mean: float
    dimension_means: tuple[tuple[str, float], ...]
    overall_threshold: float
    dimension_threshold: float
    failed_dimensions: tuple[str, ...]
    artifact_hash_coverage: float
    findings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "benchmark_id": self.benchmark_id,
            "packet_sha256": self.packet_sha256,
            "score_sheet_sha256": self.score_sheet_sha256,
            "reviewer_id": self.reviewer_id,
            "status": self.status,
            "review_count": self.review_count,
            "score_count": self.score_count,
            "overall_mean": self.overall_mean,
            "dimension_means": dict(self.dimension_means),
            "thresholds": {
                "overall_mean": self.overall_threshold,
                "dimension_mean": self.dimension_threshold,
            },
            "failed_dimensions": list(self.failed_dimensions),
            "artifact_hash_coverage": self.artifact_hash_coverage,
            "findings": list(self.findings),
        }


def load_blind_review_score_sheet(
    packet: BlindReviewPacket,
    value: Any,
) -> BlindReviewScoreSheet:
    """Validate a completed human sheet against its anonymized frozen packet."""

    if not packet.delivery_evidence_ready:
        raise ValueError(
            "blind review requires hash-verified editable PPTX and PNG evidence"
        )

    raw = _require_object(value, "blind_review_score")
    _require_exact_keys(
        raw,
        {"schema_version", "benchmark_id", "packet_sha256", "reviewer_id", "reviews"},
        "blind_review_score",
    )
    if raw["schema_version"] != BENCHMARK_SCHEMA_VERSION:
        raise ValueError("blind_review_score.schema_version must equal 1.0")
    if raw["benchmark_id"] != packet.benchmark_id:
        raise ValueError("blind review benchmark id mismatch")
    if raw["packet_sha256"] != packet.packet_sha256:
        raise ValueError("blind review packet hash mismatch")
    reviewer_id = _require_string(raw["reviewer_id"], "blind_review_score.reviewer_id")
    if re.fullmatch(r"R-[A-Za-z0-9][A-Za-z0-9._-]{0,31}", reviewer_id) is None:
        raise ValueError("blind review reviewer_id must be a pseudonymous R-* id")
    reviews_raw = raw["reviews"]
    if not isinstance(reviews_raw, list):
        raise ValueError("blind_review_score.reviews must be an array")

    packet_entries = {entry.blind_id: entry for entry in packet.entries}
    review_ids = [
        item.get("blind_id") if isinstance(item, dict) else None for item in reviews_raw
    ]
    if len(review_ids) != len(set(review_ids)) or set(review_ids) != set(packet_entries):
        raise ValueError("blind review entries mismatch; every packet entry is required once")

    reviews: list[BlindReviewScore] = []
    for index, review_value in enumerate(reviews_raw):
        path = f"blind_review_score.reviews[{index}]"
        review = _require_object(review_value, path)
        _require_exact_keys(
            review, {"blind_id", "evidence_sha256", "scores", "notes"}, path
        )
        blind_id = _require_string(review["blind_id"], f"{path}.blind_id")
        entry = packet_entries[blind_id]
        if review["evidence_sha256"] != entry.evidence_sha256:
            raise ValueError(f"{path}.evidence_sha256 mismatch")
        scores_raw = _require_object(review["scores"], f"{path}.scores")
        _require_exact_keys(scores_raw, set(entry.rubric), f"{path}.scores")
        scores: list[tuple[str, int]] = []
        for rubric in entry.rubric:
            score = scores_raw[rubric]
            if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
                raise ValueError(f"{path}.scores.{rubric} must be an integer from 1 to 5")
            scores.append((rubric, score))
        notes = review["notes"]
        if notes is not None:
            notes = _require_string(notes, f"{path}.notes")
        reviews.append(
            BlindReviewScore(
                blind_id=blind_id,
                evidence_sha256=entry.evidence_sha256,
                scores=tuple(scores),
                notes=notes,
            )
        )
    return BlindReviewScoreSheet(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        benchmark_id=packet.benchmark_id,
        packet_sha256=packet.packet_sha256,
        reviewer_id=reviewer_id,
        reviews=tuple(reviews),
    )


def evaluate_blind_review_gate(
    packet: BlindReviewPacket,
    sheet: BlindReviewScoreSheet,
    *,
    overall_threshold: float = 4.2,
    dimension_threshold: float = 4.0,
) -> BlindReviewGateReport:
    """Evaluate the locked human gate without synthesizing or repairing scores."""

    for label, threshold in (
        ("overall_threshold", overall_threshold),
        ("dimension_threshold", dimension_threshold),
    ):
        if (
            isinstance(threshold, bool)
            or not isinstance(threshold, (int, float))
            or not math.isfinite(float(threshold))
            or not 1.0 <= float(threshold) <= 5.0
        ):
            raise ValueError(f"{label} must be a finite number from 1 to 5")
    if not packet.delivery_evidence_ready:
        raise ValueError(
            "blind review requires hash-verified editable PPTX and PNG evidence"
        )
    if (
        sheet.benchmark_id != packet.benchmark_id
        or sheet.packet_sha256 != packet.packet_sha256
    ):
        raise ValueError("blind review score sheet is not bound to the packet")
    expected_ids = {entry.blind_id for entry in packet.entries}
    if {review.blind_id for review in sheet.reviews} != expected_ids:
        raise ValueError("blind review score sheet entries do not match the packet")

    dimension_values: dict[str, list[int]] = {}
    all_values: list[int] = []
    for review in sheet.reviews:
        for rubric, score in review.scores:
            dimension_values.setdefault(rubric, []).append(score)
            all_values.append(score)
    if not all_values:
        raise ValueError("blind review score sheet contains no scores")
    dimension_means = tuple(
        (rubric, round(sum(values) / len(values), 6))
        for rubric, values in sorted(dimension_values.items())
    )
    overall_mean = round(sum(all_values) / len(all_values), 6)
    failed_dimensions = tuple(
        rubric
        for rubric, mean in dimension_means
        if mean < float(dimension_threshold)
    )
    findings: list[str] = []
    if overall_mean < float(overall_threshold):
        findings.append(
            f"overall_mean {overall_mean:.3f} is below {float(overall_threshold):.3f}"
        )
    findings.extend(
        f"{rubric} mean {mean:.3f} is below {float(dimension_threshold):.3f}"
        for rubric, mean in dimension_means
        if rubric in failed_dimensions
    )
    return BlindReviewGateReport(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        benchmark_id=packet.benchmark_id,
        packet_sha256=packet.packet_sha256,
        score_sheet_sha256=canonical_sha256(sheet),
        reviewer_id=sheet.reviewer_id,
        status="PASS" if not findings else "FAIL",
        review_count=len(sheet.reviews),
        score_count=len(all_values),
        overall_mean=overall_mean,
        dimension_means=dimension_means,
        overall_threshold=float(overall_threshold),
        dimension_threshold=float(dimension_threshold),
        failed_dimensions=failed_dimensions,
        artifact_hash_coverage=1.0,
        findings=tuple(findings),
    )


@dataclass(frozen=True)
class AggregateScorecard:
    schema_version: str
    benchmark_id: str
    planned_trials: int
    recorded_trials: int
    available_trials: int
    completeness: float
    arm_composites: tuple[tuple[str, float | None], ...]
    automatic_gates: tuple[tuple[str, bool], ...]
    artifact_hash_coverage: float
    fingerprint_status: str
    thresholds_sha256: str
    release_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "benchmark_id": self.benchmark_id,
            "planned_trials": self.planned_trials,
            "recorded_trials": self.recorded_trials,
            "available_trials": self.available_trials,
            "completeness": self.completeness,
            "arm_composites": dict(self.arm_composites),
            "automatic_gates": dict(self.automatic_gates),
            "artifact_hash_coverage": self.artifact_hash_coverage,
            "fingerprint_status": self.fingerprint_status,
            "thresholds_sha256": self.thresholds_sha256,
            "release_status": self.release_status,
        }


def _validate_scorecard_identity(
    trial: BenchmarkTrial, score: TrialScorecard
) -> None:
    expected = (
        trial.trial_id,
        trial.scenario_id,
        trial.arm_id,
        trial.model_id,
        trial.repeat_index,
    )
    actual = (
        score.trial_id,
        score.scenario_id,
        score.arm_id,
        score.model_id,
        score.repeat_index,
    )
    if actual != expected:
        raise ValueError(f"scorecard identity mismatch: {trial.trial_id}")
    if score.schema_version != BENCHMARK_SCHEMA_VERSION:
        raise ValueError(f"scorecard schema mismatch: {trial.trial_id}")
    if score.status not in {"unavailable", "invalid", "failed", "evaluated"}:
        raise ValueError(f"scorecard status is invalid: {trial.trial_id}")
    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
        or not 0.0 <= float(value) <= 1.0
        for value in score.metrics.values()
    ):
        raise ValueError(f"scorecard metrics are invalid: {trial.trial_id}")
    if score.composite is not None and (
        not math.isfinite(score.composite) or not 0.0 <= score.composite <= 100.0
    ):
        raise ValueError(f"scorecard composite is invalid: {trial.trial_id}")
    if score.status == "unavailable":
        if score.raw_response_sha256 is not None or score.composite is not None:
            raise ValueError(f"unavailable scorecard contains invented output: {trial.trial_id}")
    elif score.raw_response_sha256 is None or not SHA256_PATTERN.fullmatch(
        score.raw_response_sha256
    ):
        raise ValueError(f"recorded scorecard lacks a raw response hash: {trial.trial_id}")
    if score.status == "evaluated":
        required_hashes = (
            score.deck_plan_sha256,
            score.compiled_sha256,
            score.render_plan_sha256,
        )
        if any(
            value is None or SHA256_PATTERN.fullmatch(value) is None
            for value in required_hashes
        ):
            raise ValueError(f"evaluated scorecard lacks pipeline hashes: {trial.trial_id}")
        if (
            trial.arm_id == "full-v5"
            and score.metrics.get("hard_gate_pass") == 1.0
            and (
                score.quality_report_sha256 is None
                or SHA256_PATTERN.fullmatch(score.quality_report_sha256) is None
            )
        ):
            raise ValueError(
                f"delivered full-v5 scorecard lacks its Quality-v2 hash: {trial.trial_id}"
            )


def _required_trial_artifacts(
    trial: BenchmarkTrial, score: TrialScorecard
) -> tuple[str, ...]:
    names = [
        "prompt.txt",
        "provider-events.jsonl",
        "provider-stderr.txt",
        "provider-metadata.json",
    ]
    if score.raw_response_sha256 is not None:
        names.append("response.txt")
    if score.deck_plan_sha256 is not None:
        names.extend(("deck-plan.json", "compiled-plan.json", "render-plan.json"))
        if trial.arm_id == "full-v5":
            names.extend(
                (
                    "fact-store.json",
                    "brief-plan.json",
                    "narrative-plan.json",
                    "direction-decision.json",
                    "generation-manifest.json",
                    "repair-log.v2.json",
                )
            )
    if (
        trial.arm_id == "full-v5"
        and score.status == "evaluated"
        and score.metrics.get("hard_gate_pass") == 1.0
    ):
        names.extend(
            (
                "delivery.pptx",
                "delivery.pdf",
                "ooxml-report.json",
                "quality-report.v2.json",
                "portable-verification.json",
                "backend-render-report.json",
                "libreoffice-report.json",
                "portable-result.json",
                "portable-proof/portable-proof.pdf",
                "contact-sheet.png",
            )
        )
    if (
        trial.arm_id == "full-v5"
        and score.status == "failed"
        and (score.failure_code or "").startswith("PORTABLE_")
    ):
        names.append("portable-failure.json")
    return tuple(names)


def _read_json_artifact(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _trial_artifacts_verified(
    trial: BenchmarkTrial,
    score: TrialScorecard,
    *,
    artifact_root: Path | None,
) -> bool:
    if artifact_root is None:
        return False
    expected_prefix = f"trials/{trial.trial_id}/"
    trial_dir = artifact_root / "trials" / trial.trial_id
    scorecard_path = trial_dir / "scorecard.json"
    inventory_path = trial_dir / "sha256-inventory.json"
    persisted_score = _read_json_artifact(scorecard_path)
    inventory = _read_json_artifact(inventory_path)
    if persisted_score != score.to_dict() or not isinstance(inventory, dict):
        return False
    rows = inventory.get("files")
    if inventory.get("schema_version") != "1.0" or not isinstance(rows, list):
        return False
    inventory_by_path: dict[str, tuple[str, int]] = {}
    for row in rows:
        if (
            not isinstance(row, dict)
            or set(row) != {"relative_path", "sha256", "size_bytes"}
            or not isinstance(row.get("relative_path"), str)
            or not isinstance(row.get("sha256"), str)
            or SHA256_PATTERN.fullmatch(row["sha256"]) is None
            or isinstance(row.get("size_bytes"), bool)
            or not isinstance(row.get("size_bytes"), int)
            or row["size_bytes"] < 0
            or row["relative_path"] in inventory_by_path
        ):
            return False
        relative = Path(row["relative_path"])
        if relative.is_absolute() or ".." in relative.parts:
            return False
        path = trial_dir / relative
        if not path.is_file():
            return False
        payload = path.read_bytes()
        observed = (hashlib.sha256(payload).hexdigest(), len(payload))
        expected = (row["sha256"], row["size_bytes"])
        if observed != expected:
            return False
        inventory_by_path[row["relative_path"]] = expected
    actual_inventory_paths = {
        path.relative_to(trial_dir).as_posix()
        for path in trial_dir.rglob("*")
        if path.is_file() and path != inventory_path
    }
    if set(inventory_by_path) != actual_inventory_paths:
        return False
    by_path: dict[str, ArtifactDigest] = {}
    for digest in score.artifact_digests:
        if digest.relative_path in by_path or not digest.relative_path.startswith(
            expected_prefix
        ):
            return False
        if not verify_artifact_digest(digest, root=artifact_root):
            return False
        by_path[digest.relative_path] = digest
    expected_digest_paths = {
        f"{expected_prefix}{name}"
        for name in inventory_by_path
        if name != "scorecard.json"
    }
    if set(by_path) != expected_digest_paths:
        return False
    required = {
        f"{expected_prefix}{name}" for name in _required_trial_artifacts(trial, score)
    }
    if not required.issubset(by_path):
        return False

    prompt_path = artifact_root / expected_prefix / "prompt.txt"
    try:
        if canonical_sha256(prompt_path.read_text(encoding="utf-8")) != trial.prompt_sha256:
            return False
    except (OSError, UnicodeDecodeError):
        return False

    metadata = _read_json_artifact(
        artifact_root / expected_prefix / "provider-metadata.json"
    )
    expected_identity = {
        "trial_id": trial.trial_id,
        "scenario_id": trial.scenario_id,
        "arm_id": trial.arm_id,
        "model_id": trial.model_id,
        "repeat_index": trial.repeat_index,
    }
    if not isinstance(metadata, dict) or metadata.get("trial_identity") != expected_identity:
        return False
    if not isinstance(metadata.get("provider"), dict):
        return False

    if score.raw_response_sha256 is not None:
        try:
            response = (artifact_root / expected_prefix / "response.txt").read_text(
                encoding="utf-8"
            )
        except (OSError, UnicodeDecodeError):
            return False
        if canonical_sha256(response) != score.raw_response_sha256:
            return False

    document_hashes = {
        "deck-plan.json": score.deck_plan_sha256,
        "compiled-plan.json": score.compiled_sha256,
        "render-plan.json": score.render_plan_sha256,
    }
    if trial.arm_id == "full-v5" and score.quality_report_sha256 is not None:
        document_hashes["quality-report.v2.json"] = score.quality_report_sha256
    for name, expected_hash in document_hashes.items():
        if expected_hash is None:
            continue
        document = _read_json_artifact(artifact_root / expected_prefix / name)
        if document is None or canonical_sha256(document) != expected_hash:
            return False
    if (
        trial.arm_id == "full-v5"
        and score.status == "evaluated"
        and score.metrics.get("hard_gate_pass") == 1.0
    ):
        delivery = trial_dir / "delivery.pptx"
        delivery_pdf = trial_dir / "delivery.pdf"
        proof_pdf = trial_dir / "portable-proof" / "portable-proof.pdf"
        contact_sheet = trial_dir / "contact-sheet.png"
        verification = _read_json_artifact(trial_dir / "portable-verification.json")
        if not isinstance(verification, dict):
            return False
        try:
            validate_ooxml_package(delivery)
            if not delivery_pdf.read_bytes().startswith(b"%PDF-"):
                return False
            if not proof_pdf.read_bytes().startswith(b"%PDF-"):
                return False
            read_raster_dimensions(contact_sheet)
        except (OSError, ValueError, WindowPptxError):
            return False
        candidate_sha = verification.get("candidate_sha256")
        if candidate_sha != hashlib.sha256(delivery.read_bytes()).hexdigest():
            return False
        verification_body = verification.get("verification")
        if not isinstance(verification_body, dict):
            return False
        libreoffice = verification_body.get("libreoffice")
        if not isinstance(libreoffice, dict):
            return False
        page_count = libreoffice.get("page_count")
        if isinstance(page_count, bool) or not isinstance(page_count, int) or page_count < 1:
            return False
        previews = sorted(
            (trial_dir / "portable-proof").glob("slide-*.png"),
            key=lambda path: path.name,
        )
        expected_names = [f"slide-{index:03d}.png" for index in range(1, page_count + 1)]
        if [path.name for path in previews] != expected_names:
            return False
        try:
            for path in previews:
                read_raster_dimensions(path)
        except (OSError, ValueError):
            return False
    return True


def verify_trial_artifacts(
    trial: BenchmarkTrial,
    score: TrialScorecard,
    *,
    artifact_root: Path | str,
) -> bool:
    """Public fail-closed verifier used by aggregate and safe resume."""

    return _trial_artifacts_verified(
        trial,
        score,
        artifact_root=Path(artifact_root).resolve(),
    )


def _tree_hash(paths: list[Path], *, base: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: str(item).casefold()):
        digest.update(path.relative_to(base).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _static_fingerprint_values(
    spec: BenchmarkSpec, manifest: BenchmarkManifest
) -> dict[str, str]:
    skill_root = Path(__file__).resolve().parents[2]
    repo_root = skill_root.parents[2]
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=skill_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "git_commit": completed.stdout.strip(),
        "engine_sha256": _tree_hash(
            list(governed_engine_source_paths(skill_root)), base=repo_root
        ),
        "registry_bundle_sha256": _tree_hash(
            list((skill_root / "registries").glob("*.json")), base=repo_root
        ),
        "schemas_sha256": _tree_hash(
            list((skill_root / "schemas").glob("*.json")), base=repo_root
        ),
        "skill_sha256": _tree_hash(
            [
                skill_root / "SKILL.md",
                *list((skill_root / "references").glob("*.md")),
            ],
            base=repo_root,
        ),
        "corpus_sha256": spec.corpus_sha256,
        "protocol_sha256": spec.protocol_sha256,
        "prompt_sha256": canonical_sha256(
            {trial.trial_id: trial.prompt_sha256 for trial in manifest.trials}
        ),
        "thresholds_sha256": canonical_sha256(spec.protocol.thresholds),
    }


def _workspace_clean_except_artifacts(artifact_root: Path | None) -> bool:
    skill_root = Path(__file__).resolve().parents[2]
    git_root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=skill_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    ).resolve()
    resolved_artifacts = artifact_root.resolve() if artifact_root else None
    if resolved_artifacts is not None:
        try:
            artifact_relative = resolved_artifacts.relative_to(git_root)
        except ValueError:
            artifact_relative = None
        if artifact_relative is not None and artifact_relative.parts[:2] != (
            ".planning",
            "evidence",
        ):
            return False
    tracked = subprocess.run(
        ["git", "diff-index", "--quiet", "HEAD", "--"],
        cwd=git_root,
        check=False,
    )
    if tracked.returncode != 0:
        return False
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=git_root,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    for raw_path in untracked:
        if not raw_path:
            continue
        path = (git_root / raw_path.decode("utf-8")).resolve()
        if resolved_artifacts is not None and (
            path == resolved_artifacts or resolved_artifacts in path.parents
        ):
            continue
        return False
    return True


def validate_benchmark_fingerprint_source(
    spec: BenchmarkSpec,
    manifest: BenchmarkManifest,
    fingerprints: tuple[Mapping[str, Any], ...],
    *,
    artifact_root: Path | None = None,
    component_manifests: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate source-bound fingerprint fields before spending provider budget."""

    fingerprint = validate_fingerprint_bundle(fingerprints)
    if component_manifests is None:
        raise ValueError("fingerprint component manifests are required")
    components = validate_fingerprint_components(
        fingerprint,
        component_manifests,
    )
    provider_models = components["model_provider"].get("models")
    if provider_models != [model.id for model in spec.protocol.models]:
        raise ValueError("fingerprint provider models do not match the protocol")
    if (
        "portable_runtime" not in components
        and components["environment"].get("system", "").casefold() != "windows"
    ):
        raise ValueError(
            "legacy PowerPoint benchmark evidence requires a Windows environment"
        )
    if not _workspace_clean_except_artifacts(artifact_root):
        raise ValueError("formal fingerprint claims a dirty source tree is clean")
    expected = _static_fingerprint_values(spec, manifest)
    if any(fingerprint[key] != value for key, value in expected.items()):
        raise ValueError("fingerprint does not match the benchmark source tree")
    return fingerprint


def _fingerprint_gate_status(
    spec: BenchmarkSpec,
    manifest: BenchmarkManifest,
    fingerprints: tuple[Mapping[str, Any], ...] | None,
    *,
    artifact_root: Path | None,
    fingerprint_artifact: ArtifactDigest | None,
) -> str:
    if fingerprints is None:
        return "missing"
    try:
        if artifact_root is None or fingerprint_artifact is None:
            raise ValueError("fingerprint artifact is missing")
        if fingerprint_artifact.relative_path != "fingerprint-bundle.json":
            raise ValueError("fingerprint artifact path is invalid")
        if not verify_artifact_digest(fingerprint_artifact, root=artifact_root):
            raise ValueError("fingerprint artifact digest is invalid")
        stored = _read_json_artifact(artifact_root / "fingerprint-bundle.json")
        if not isinstance(stored, dict) or set(stored) != {
            "schema_version",
            "fingerprints",
            "components",
        }:
            raise ValueError("fingerprint artifact structure is invalid")
        fingerprint = validate_benchmark_fingerprint_source(
            spec,
            manifest,
            fingerprints,
            artifact_root=artifact_root,
            component_manifests=stored["components"],
        )
        expected_bundle = {
            "schema_version": BENCHMARK_SCHEMA_VERSION,
            "fingerprints": [fingerprint for _item in fingerprints],
            "components": stored["components"],
        }
        if stored != expected_bundle:
            raise ValueError("fingerprint artifact content mismatch")
    except (OSError, subprocess.SubprocessError, ValueError):
        return "rejected"
    return "verified"


def _mean_metric(scorecards: list[TrialScorecard], metric: str) -> float:
    if not scorecards:
        return 0.0
    return sum(float(score.metrics.get(metric, 0.0)) for score in scorecards) / len(
        scorecards
    )


def aggregate_scorecards(
    spec: BenchmarkSpec,
    manifest: BenchmarkManifest,
    scorecards: tuple[TrialScorecard, ...],
    *,
    fingerprints: tuple[Mapping[str, Any], ...] | None = None,
    artifact_root: Path | str | None = None,
    fingerprint_artifact: ArtifactDigest | None = None,
) -> AggregateScorecard:
    frozen_manifest = build_trial_manifest(spec)
    if manifest != frozen_manifest:
        raise ValueError("manifest does not match the frozen benchmark protocol")
    manifest_by_id = {trial.trial_id: trial for trial in manifest.trials}
    unique: dict[str, TrialScorecard] = {}
    for score in scorecards:
        if score.trial_id not in manifest_by_id:
            raise ValueError(f"scorecard is not in the frozen manifest: {score.trial_id}")
        if score.trial_id in unique:
            raise ValueError(f"duplicate scorecard: {score.trial_id}")
        _validate_scorecard_identity(manifest_by_id[score.trial_id], score)
        if score.composite is not None and not math.isclose(
            score.composite,
            _composite(score.metrics, spec.protocol.weights_dict()),
            abs_tol=1e-4,
        ):
            raise ValueError(f"scorecard composite mismatch: {score.trial_id}")
        unique[score.trial_id] = score
    available = [score for score in unique.values() if score.status != "unavailable"]
    arm_composites: list[tuple[str, float | None]] = []
    for arm in spec.protocol.arms:
        values = [
            score.composite
            for score in available
            if score.arm_id == arm.id and score.composite is not None
        ]
        arm_composites.append(
            (arm.id, None if not values else round(sum(values) / len(values), 4))
        )
    planned = len(manifest.trials)
    completeness = 0.0 if planned == 0 else len(available) / planned
    resolved_artifact_root = Path(artifact_root).resolve() if artifact_root else None
    verified_artifacts = sum(
        _trial_artifacts_verified(
            manifest_by_id[trial_id],
            score,
            artifact_root=resolved_artifact_root,
        )
        for trial_id, score in unique.items()
    )
    artifact_hash_coverage = (
        0.0 if planned == 0 else verified_artifacts / planned
    )

    full_v5 = [
        unique[trial.trial_id]
        for trial in manifest.trials
        if trial.arm_id == "full-v5" and trial.trial_id in unique
    ]
    arm_means = dict(arm_composites)
    unsupported_numeric = sum(
        violation.startswith("UNSUPPORTED_NUMERIC:")
        for score in unique.values()
        for violation in score.violations
    )
    thresholds = spec.protocol.thresholds
    automatic_gates = (
        (
            "full_v5_plan_validity",
            _mean_metric(full_v5, "deck_plan_valid")
            >= thresholds["full_v5_plan_validity"],
        ),
        (
            "full_v5_compile_success",
            _mean_metric(full_v5, "compile_success")
            >= thresholds["full_v5_compile_success"],
        ),
        (
            "full_v5_hard_gate_pass",
            _mean_metric(full_v5, "hard_gate_pass")
            >= thresholds["full_v5_hard_gate_pass"],
        ),
        (
            "full_v5_fact_retention",
            _mean_metric(full_v5, "fact_retention")
            >= thresholds["full_v5_fact_retention"],
        ),
        (
            "prohibited_numeric_inventions",
            unsupported_numeric <= thresholds["prohibited_numeric_inventions"],
        ),
        (
            "delta_vs_unassisted_points",
            arm_means.get("full-v5") is not None
            and arm_means.get("unassisted-json") is not None
            and float(arm_means["full-v5"])
            - float(arm_means["unassisted-json"])
            >= thresholds["delta_vs_unassisted_points"],
        ),
        (
            "delta_vs_governed_plan_points",
            arm_means.get("full-v5") is not None
            and arm_means.get("governed-plan") is not None
            and float(arm_means["full-v5"])
            - float(arm_means["governed-plan"])
            >= thresholds["delta_vs_governed_plan_points"],
        ),
        (
            "artifact_hash_coverage",
            artifact_hash_coverage >= thresholds["artifact_hash_coverage"],
        ),
    )
    fingerprint_status = _fingerprint_gate_status(
        spec,
        manifest,
        fingerprints,
        artifact_root=resolved_artifact_root,
        fingerprint_artifact=fingerprint_artifact,
    )
    automatic_without_artifacts = dict(automatic_gates).copy()
    automatic_without_artifacts.pop("artifact_hash_coverage")
    if len(unique) < planned or len(available) < planned:
        release_status = "incomplete"
    elif not any(score.status == "evaluated" for score in unique.values()):
        release_status = "threshold-rejected"
    elif not all(automatic_without_artifacts.values()):
        release_status = "threshold-rejected"
    elif not dict(automatic_gates)["artifact_hash_coverage"]:
        release_status = "artifact-rejected"
    elif fingerprint_status == "missing":
        release_status = "fingerprint-missing"
    elif fingerprint_status != "verified":
        release_status = "fingerprint-rejected"
    else:
        release_status = "pending-human-review"
    return AggregateScorecard(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        benchmark_id=spec.protocol.benchmark_id,
        planned_trials=planned,
        recorded_trials=len(unique),
        available_trials=len(available),
        completeness=completeness,
        arm_composites=tuple(arm_composites),
        automatic_gates=automatic_gates,
        artifact_hash_coverage=artifact_hash_coverage,
        fingerprint_status=fingerprint_status,
        thresholds_sha256=canonical_sha256(spec.protocol.thresholds),
        release_status=release_status,
    )


__all__ = [
    "AggregateScorecard",
    "ArtifactDigest",
    "BenchmarkArm",
    "BenchmarkFact",
    "BenchmarkManifest",
    "BenchmarkModel",
    "BenchmarkProtocol",
    "BenchmarkScenario",
    "BenchmarkSpec",
    "BenchmarkTrial",
    "BlindReviewArtifact",
    "BlindReviewEntry",
    "BlindReviewGateReport",
    "BlindReviewPacket",
    "BlindReviewScore",
    "BlindReviewScoreSheet",
    "ProviderResponse",
    "TrialScorecard",
    "TrialEvaluation",
    "aggregate_scorecards",
    "build_benchmark_fact_store",
    "build_blind_review_packet",
    "build_trial_manifest",
    "build_trial_prompt",
    "canonical_json",
    "canonical_sha256",
    "digest_artifact",
    "evaluate_trial_response",
    "evaluate_trial_evidence",
    "evaluate_blind_review_gate",
    "load_benchmark_spec",
    "load_blind_review_packet",
    "load_blind_review_score_sheet",
    "parse_opencode_events",
    "run_opencode_response",
    "validate_benchmark_fingerprint_source",
    "verify_artifact_digest",
]
