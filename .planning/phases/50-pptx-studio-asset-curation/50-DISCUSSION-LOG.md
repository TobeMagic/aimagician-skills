# Phase 50: Asset Curation and Visual Catalog - Discussion Log

**Updated:** 2026-08-11

## Decisions

| Topic | Options considered | Decision | Reason |
|---|---|---|---|
| Product outcome | One deck copy vs flexible reuse | Three modes: whole deck, coherent pages, bounded regions | Matches user's senior-designer workflow and avoids one-reference lock-in |
| Private source reduction | Delete vs archive unused categories | Archive seven inactive categories with a hash/recovery manifest | User explicitly requested clean active selection without irreversible data loss |
| Search evidence | Filename/manual browsing vs visual catalog | Deck/page/region records plus Agnes rendered-page observations | Opaque source filenames and 377 packages are not agent-searchable |
| Visual model role | Let Agnes determine implementation | Agnes supplies hash-bound visual observation only | Geometry/editability/fact safety must remain deterministic/OOXML-backed |
| Naming | Retain compatibility shell vs flag-day rename | `pptx-studio`, no shell after Phase 52 tests | Explicit user decision |

## Assumptions

| Assumption | Status | Evidence or action |
|---|---|---|
| Rendered private active pages can be uploaded to Agnes for catalog analysis | Confirmed | USR-V7-01 says Agnes should inspect retained rendered pages; no original PPTX/media upload |
| All active category names listed by the user are exact directory names | Confirmed | Local inventory shows all 22 names exactly |
| Archive action is safe only after a dry-run and hash snapshot | Design constraint | Recorded in AC-50-01/02 and curation interface |

## Rejected Options

- Treating existing certificate quality scores as semantic visual descriptions:
  rejected because they do not describe use conditions.
- Reusing all 377 packages in one retrieval catalog: rejected because it
  conflicts with the explicit curated active scope and harms candidate quality.
- Shipping a `window-pptx` compatibility command: rejected by user decision.

## Deferred Work

- Physical component import/adaptation and deck-composition selection: Phase 51.
- Public package rename, concise Skill rewrite, QA harness and installed sync:
  Phase 52.
- Clean-room 15-slide acceptance/release: Phase 53.
