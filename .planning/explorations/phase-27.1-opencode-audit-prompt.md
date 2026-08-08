You are an independent audit agent working under a strict read-only contract.

Goal: systematically review the current Window-PPTX Skill after the Phase 27.1 Huashu-design assimilation implementation. Determine whether the implementation materially raises the quality floor for ordinary models while preserving fact safety, native editability, deterministic design, and delivery gates. This is an audit, not an implementation task.

Allowed scope:

- `skills/owned/window-pptx/**`
- `tests/window_pptx/**`
- `.planning/phases/27.1-window-pptx-huashu-design-assimilation/**`
- `.planning/{PROJECT,STATE,ROADMAP,REQUIREMENTS,MILESTONES}.md`

Forbidden scope:

- Do not inspect `.env`, credentials, tokens, provider configuration, home-directory config, or secret values.
- Do not inspect or use `.planning/evidence/**`; it is pre-Huashu noncanonical WIP.
- Do not inspect the root user files `Northstar_Q2_Business_Review_DeckPlan.json` or `deckplan.json`.
- Do not modify, create, delete, move, format, or stage files.
- Do not run destructive commands, network mutations, package installs, PowerPoint, or write-capable scripts.
- Do not change Git state or configuration.

Allowed commands: read-only file listing/searching, file reads, Git status/diff/log, Python syntax/import inspection, and tests only if they create no repository files. Prefer source inspection; do not spend the whole audit rerunning the already reported suite.

Audit dimensions:

1. FactStore -> BriefPlan -> NarrativePlan -> DeckPlan authority and invention prevention.
2. Coverage of 15 commercial archetypes and critical narrative beats.
3. Exact 12 art directions, three-candidate selection, safe fallback, BrandSpec, font/asset gates.
4. Semantic-to-form authority, 24-family/72-variant layout system, capacity, rhythm, and geometry differentiation.
5. Native editable charts/tables/diagrams/images/text and asset fallback behavior.
6. QualityReport v2 namespaces, preview checks, one pre-render plus one post-render repair, rollback, and transaction safety.
7. CLI integration, backward compatibility, progressive Skill workflow, two-retry/safe-default instructions, schemas, and eval metadata.
8. Huashu clean-room/license/provenance boundary and whether claims are independently implemented.
9. Calibration/fingerprint/ordinary-model evidence readiness and any overclaims.
10. Bugs, missing integrations, schema/runtime mismatches, test weaknesses, false-positive/negative risks, and Windows-only gaps.

Required output:

# Audit Summary
# Requirement Matrix
For V5-REF-01 through V5-REF-06, state PASS, PARTIAL, FAIL, or NOT_RUN, with concrete file/symbol evidence.
# Blocking Findings
List only high-severity defects that can invalidate generation or delivery, ordered by severity.
# Important Findings
# Strengths
# Architecture and Data Flow
# Weak-Model Failure Modes Now Prevented
# Remaining Weak-Model Failure Modes
# Test and Evidence Assessment
# Huashu 1+1>2 Assessment
# Recommended Fixes
Separate must-fix before Phase 27.1 closure from Phase 28/29 follow-ups.
# Validation Commands
# Open Questions
# Reliability Notes

Use exact paths and symbols. Separate verified facts from inference. Do not praise generally; give falsifiable findings. If a requirement cannot be proven without Windows PowerPoint or new ordinary-model runs, mark it NOT_RUN/PARTIAL rather than inferring success.
