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

__all__ = [
    "ACTIVE_GAOJIE_CATEGORIES",
    "INACTIVE_GAOJIE_CATEGORIES",
    "CurationError",
    "apply_curation",
    "plan_curation",
    "recover_curation",
    "verify_curation",
]
