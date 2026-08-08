# Project Context

**Context schema:** v1
**Adoption source:** USR-20260803-001
**Last reviewed:** 2026-08-08

## Architecture Snapshot

AImagician Skills is a local-first owned-skill repository plus the Skillbird catalog and installation runtime. Owned skills under `skills/owned/` are the canonical capability source. Skillbird discovers and synchronizes them into supported AI CLI skill directories while keeping disabled external repositories as reference material rather than runtime dependencies.

The repository also contains a planning-managed Window-PPTX production engine. Its active milestone and phase remain defined by `.planning/STATE.md` and `.planning/ROADMAP.md`; capability work outside that phase uses a traceable controlled task and returns to the recorded checkpoint.

## Stable Boundaries And Invariants

| ID | Contract | Canonical source | Status |
|---|---|---|---|
| CTX-ARCH-001 | Owned skills are maintained in-repository and synchronized through Skillbird. | `.planning/PROJECT.md` | Active |
| CTX-ARCH-002 | External skill sources are disabled references unless the user explicitly enables installation. | `.planning/STATE.md` | Active |
| CTX-WORKFLOW-001 | Latest user decisions, locked requirements/specifications, planning state, project context, and evidence use distinct authority levels; recency is navigation, not authority. | `skills/owned/aimagician-superpower/references/capabilities/state-and-continuity.md` | Active |
| CTX-WORKFLOW-002 | Off-phase work requires an approved task with parent milestone, parent phase, and return checkpoint. | `.planning/REQUESTS.md` | Active |
| CTX-AGENT-001 | CLI workers are bounded executors and reviewers; the controller owns architecture, risk, reconciliation, validation, and completion. | `skills/owned/cli-agent-delegator/SKILL.md` | Active |
| CTX-AGENT-002 | Images are acquired through `vision-analysis`; OpenCode receives sanitized text evidence rather than native Agnes image attachments. | `skills/owned/vision-analysis/SKILL.md` | Active |
| CTX-PPTX-001 | Direct-use eligibility and complete physical lineage are mandatory for automated template reuse; reference-only pages may guide art direction but cannot be assembled automatically. | USR-V61-01 / Phase 49 | Active |
| CTX-PPTX-002 | OPC import resolves each target relative to its relationship owner, traverses every internal dependency, rejects unsafe targets, and conservatively deduplicates only safe immutable parts. | Phase 49 specification | Active |

## Durable Decisions

| ID | Decision | Source | Status | Supersedes |
|---|---|---|---|---|
| CTX-DEC-001 | GSD-style planning state remains the phase and milestone backbone; useful engineering capabilities are consolidated into owned skills. | Phase 19 | Active | NONE |
| CTX-DEC-002 | Workflow ceremony is risk-scaled; Quick and Standard work use the shortest reliable delivery path. | USR-20260730-002 | Active | NONE |
| CTX-DEC-003 | OpenCode models are selected explicitly by the controller from live free inventory; Agnes is the final fallback after better declared models are unavailable. | USR-20260803-001 | Active | DeepSeek-first portion of REQ-MODEL-001 and REQ-ROUTE-002 |
| CTX-DEC-004 | `opencode/*` uses one shared user-asserted quota pool, Agnes is user-asserted unlimited, and other configured models use model-specific pools. | USR-20260803-001 | Active | NONE |
| CTX-DEC-005 | The specialized presentation Skill will be renamed to `pptx-studio`; after the v7 migration is verified, `window-pptx` is deleted completely rather than retained as a compatibility shell. | Latest explicit user decision, 2026-08-08 | Accepted for next milestone | NONE |
| CTX-DEC-006 | The approved active Gaojie library target is 97 highly reusable PPTX assets (about 117–160 pages); other assets are archived or deleted only through a SHA-bound prune manifest after v6.1 stabilization. | User-approved asset-pruning discussion, 2026-08-08 | Accepted for next milestone | NONE |

## Verification And Delivery Baseline

- Run focused tests first, then full tests, typecheck, build, and package or install smoke checks according to blast radius.
- Owned-skill changes require `skillbird format-skills --check` and content-parity verification after Codex/OpenCode synchronization.
- High, planning-managed, phase, milestone, or explicit completion claims require an independent frozen-point OpenCode audit and controller spot-checks.
- Deployable work remains open through required postmerge evidence; non-deployable work records explicit `N/A` delivery fields.

## Source Routing

| Source ID | Topic | Path | Policy | Authority |
|---|---|---|---|---|
| SRC-STATE | Active milestone, phase, checkpoint, blockers | `.planning/STATE.md` | MUST_READ for resume, phase, milestone, High | Planning state |
| SRC-PROJECT | Product purpose, scope, constraints | `.planning/PROJECT.md` | MUST_READ for first entry, resume, Standard/High | Project context |
| SRC-CONTEXT | Architecture, invariants, durable decisions | `.planning/CONTEXT.md` | MUST_READ for resume, shared contracts, phase, milestone, Standard/High | Project context |
| SRC-ROADMAP | Phase goal and success criteria | `.planning/ROADMAP.md` | MUST_READ for phase/milestone | Locked planning |
| SRC-REQUIREMENTS | Requirement ownership and acceptance | `.planning/REQUIREMENTS.md` | MUST_READ for phase/milestone | Locked planning |
| SRC-ACTIVE-PHASE | Most recent phase context, plan, validation, audit, summary | `.planning/phases/<active-phase>/` | MUST_READ by current stage | Locked phase/current evidence |
| SRC-README | User-facing product and CLI contract | `README.md` | READ_IF_RELEVANT | Project docs |
| SRC-WIKI | Project knowledge base when present | `LLM-know-how-wiki/` or project-defined path | READ_IF_RELEVANT | Knowledge base |
| SRC-PRIOR-PHASE | Prior decisions and evidence linked by this context or the active phase | `.planning/phases/<linked-phase>/` | READ_IF_RELEVANT | Historical evidence |

## Superseded Decisions

- DeepSeek-first remains valid historical evidence for completed records created under USR-20260729-001 and USR-20260730-001. It is no longer the prospective model-selection policy after USR-20260803-001.

## Open Questions

- Model quality is intentionally not encoded as a static ranking. The controller records task-specific selection rationale and revises its choice from observed evidence.
- A missing or conflicting source that can change behavior, architecture, interfaces, data, security, scope, acceptance, or irreversible work requires user discussion before mutation.
