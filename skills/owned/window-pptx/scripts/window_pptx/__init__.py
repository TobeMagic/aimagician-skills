"""Pure safety primitives for Windows PowerPoint automation."""

from .com_session import dispatch_powerpoint, macro_security
from .cli import build_dry_run_result, collect_requested_actions, emit_result, parse_args
from .capacity import split_slide
from .deck_plan import (
    ContentBlock,
    DeckPlan,
    DeckPlanValidationError,
    ProjectIntent,
    SlideIntent,
    compile_deck_plan,
    load_deck_plan,
    validate_deck_plan,
)
from .errors import ComSessionError, OutputPolicyError, WindowPptxError
from .models import CandidateResult, OutputPolicy, PowerPointHandle
from .output_policy import calculate_export_size, validate_output_policy
from .registry import Archetype, RegistryError, load_archetypes, resolve_archetype
from .rules import CandidateScore, DecisionTrace, rank_page_families
from .transaction import (
    PartialSaveError,
    SourceIntegrityError,
    TransactionError,
    candidate_path_for,
    save_candidate,
    sha256_file,
    validate_ooxml_package,
)

__all__ = [
    "ComSessionError",
    "ContentBlock",
    "CandidateResult",
    "CandidateScore",
    "DeckPlan",
    "DeckPlanValidationError",
    "DecisionTrace",
    "OutputPolicy",
    "OutputPolicyError",
    "PowerPointHandle",
    "ProjectIntent",
    "RegistryError",
    "SlideIntent",
    "Archetype",
    "PartialSaveError",
    "SourceIntegrityError",
    "TransactionError",
    "WindowPptxError",
    "build_dry_run_result",
    "calculate_export_size",
    "candidate_path_for",
    "collect_requested_actions",
    "compile_deck_plan",
    "dispatch_powerpoint",
    "emit_result",
    "macro_security",
    "load_archetypes",
    "load_deck_plan",
    "parse_args",
    "save_candidate",
    "rank_page_families",
    "resolve_archetype",
    "sha256_file",
    "validate_ooxml_package",
    "validate_output_policy",
    "validate_deck_plan",
    "split_slide",
]
