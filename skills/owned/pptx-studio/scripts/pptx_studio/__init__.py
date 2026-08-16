"""Private, curated presentation-library primitives for the PPTX Studio migration.

Phase 50 deliberately keeps this namespace separate from ``window_pptx`` so
the stable v6.1 physical-assembly contract is not changed while a catalog and
eventual public identity are introduced.
"""

from .curation import (
    ACTIVE_GAOJIE_CATEGORIES,
    INACTIVE_GAOJIE_CATEGORIES,
    CurationError,
    apply_curation,
    plan_curation,
    recover_curation,
    verify_curation,
)
from .composition import CompositionError, compile_composition, composition_plan_sha256, style_profile, style_signature, verify_composition_replay_lock
from .adaptation import AdaptationError, compile_adaptation
from .brief_binding import BriefBindingError, compile_outline_bindings
from .narrative import NarrativeError, narrative_digest, validate_narrative_plan, validate_normalized_brief
from .runtime import RuntimeError, resolve_private_library_root, runtime_health, runtime_paths
from .style_planning import StylePlanningError, plan_style_cluster

__all__ = [
    "ACTIVE_GAOJIE_CATEGORIES",
    "INACTIVE_GAOJIE_CATEGORIES",
    "CurationError",
    "apply_curation",
    "plan_curation",
    "recover_curation",
    "verify_curation",
    "AdaptationError",
    "BriefBindingError",
    "CompositionError",
    "NarrativeError",
    "RuntimeError",
    "StylePlanningError",
    "compile_adaptation",
    "compile_outline_bindings",
    "compile_composition",
    "narrative_digest",
    "validate_narrative_plan",
    "validate_normalized_brief",
    "resolve_private_library_root",
    "runtime_health",
    "runtime_paths",
    "plan_style_cluster",
    "composition_plan_sha256",
    "style_signature",
    "style_profile",
    "verify_composition_replay_lock",
]
