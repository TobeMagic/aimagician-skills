# Project Context

**Context schema:** v1
**Adoption source:** USR-20260803-001
**Last reviewed:** 2026-08-21

## Architecture Snapshot

AImagician Skills is a local-first owned-asset repository plus the Skillbird catalog and installation runtime. Canonical sources are `skills/owned/` (23 active skills), `rules/owned/` (always-on generic habits), and `memory/owned/project-memory-policy/` (memory read/write policy). Skillbird currently synchronizes skills into supported AI CLI skill directories. Rule and memory projection to CLI targets is a later engine slice. Disabled external repositories stay as reference material rather than runtime dependencies. Current agent contract: [`docs/RULES-AND-MEMORY.md`](../docs/RULES-AND-MEMORY.md).

The repository also contains a planning-managed Window-PPTX production engine. Its active milestone and phase remain defined by `.planning/STATE.md` and `.planning/ROADMAP.md`; capability work outside that phase uses a traceable controlled task and returns to the recorded checkpoint.

## Stable Boundaries And Invariants

| ID | Contract | Canonical source | Status |
|---|---|---|---|
| CTX-ARCH-001 | Owned skills are maintained in-repository and synchronized through Skillbird. | `.planning/PROJECT.md` | Active |
| CTX-ARCH-002 | External skill sources are disabled references unless the user explicitly enables installation. | `.planning/STATE.md` | Active |
| CTX-ARCH-003 | Always-on habits live in `rules/owned`; memory policy lives in `memory/owned`. They are first-class owned assets, not skills. Skillbird does not yet project them onto CLI rule/memory paths. | `docs/RULES-AND-MEMORY.md` | Active |
| CTX-WORKFLOW-001 | Latest user decisions, locked requirements/specifications, planning state, project context, and evidence use distinct authority levels; recency is navigation, not authority. | `skills/owned/aimagician-superpower/references/capabilities/state-and-continuity.md` | Active |
| CTX-WORKFLOW-002 | Off-phase work requires an approved task with parent milestone, parent phase, and return checkpoint. | `.planning/REQUESTS.md` | Active |
| CTX-AGENT-001 | Host-native subagents are bounded executors and reviewers; the controller owns architecture, risk, reconciliation, validation, and completion. Foreign CLI (archived `cli-agent-delegator`) is opt-in only. | `rules/owned/host-native-delegation/RULE.md` | Active |
| CTX-AGENT-002 | Images are read with the current model's native vision when available; `vision-analysis` is the fallback when the session cannot see pixels or the user asks for an Agnes evidence package. | `rules/owned/native-capability-first/RULE.md` | Active |
| CTX-PPTX-001 | Direct-use eligibility and complete physical lineage are mandatory for automated template reuse; reference-only pages may guide art direction but cannot be assembled automatically. | USR-V61-01 / Phase 49 | Active |
| CTX-PPTX-002 | OPC import resolves each target relative to its relationship owner, traverses every internal dependency, rejects unsafe targets, and conservatively deduplicates only safe immutable parts. | Phase 49 specification | Active |

## Durable Decisions

| ID | Decision | Source | Status | Supersedes |
|---|---|---|---|---|
| CTX-DEC-001 | GSD-style planning state remains the phase and milestone backbone; useful engineering capabilities are consolidated into owned skills. | Phase 19 | Active | NONE |
| CTX-DEC-002 | Workflow ceremony is risk-scaled; Quick and Standard work use the shortest reliable delivery path. | USR-20260730-002 | Active | NONE |
| CTX-DEC-003 | When an OpenCode worker is explicitly opted in, models are selected by the controller from live free inventory; Agnes is the final fallback after better declared models are unavailable. This is not the default dispatch policy. | USR-20260803-001 | Active, scoped to opt-in OpenCode | DeepSeek-first portion of REQ-MODEL-001 and REQ-ROUTE-002 |
| CTX-DEC-004 | For opt-in OpenCode runs, `opencode/*` uses one shared user-asserted quota pool, Agnes is user-asserted unlimited, and other configured models use model-specific pools. | USR-20260803-001 | Active, scoped to opt-in OpenCode | NONE |
| CTX-DEC-005 | The specialized presentation Skill will be renamed to `pptx-studio`; after the v7 migration is verified, `window-pptx` is deleted completely rather than retained as a compatibility shell. | Latest explicit user decision, 2026-08-08 | Accepted for next milestone | NONE |
| CTX-DEC-006 | The approved active Gaojie library target is 97 highly reusable PPTX assets (about 117–160 pages); other assets are archived or deleted only through a SHA-bound prune manifest after v6.1 stabilization. | User-approved asset-pruning discussion, 2026-08-08 | Accepted for next milestone | NONE |
| CTX-DEC-007 | `pptx-studio` is the target public Skill identity. There is no compatibility shim; `window-pptx` remains only until the migration phase has passing source/install tests. | USR-V7-01 | Active | CTX-DEC-005 |
| CTX-DEC-008 | Private Gaojie bytes remain local and ignored. Phase 50 keeps only user-approved category directories active and archives all other source categories recoverably with a hash manifest; it never deletes them. | USR-V7-01 | Active | CTX-DEC-006 |
| CTX-DEC-009 | Retrieval is three-layered: deck record for complete reuse, page record for coherent assembly, and region record for controlled component adaptation. Visual observations are derived from authorized rendered PNGs, hash-bound, and never committed as private payloads. | USR-V7-01 | Active | NONE |
| CTX-PPTX-STUDIO-010 | PPTX Studio composition uses deterministic strategy precedence (`exact_deck`, `page_assembly`, `component_assembly`), one catalog-derived style anchor plus explicit signature allowlist, and fact/asset-ID-only adaptation plans. The model cannot emit geometry, colors/fonts, OOXML, or literal replacement text in a materialization plan. | V7 Phase 51 | Active | CTX-DEC-009 |
| CTX-DEC-010 | Default worker is the current host's native subagent. `cli-agent-delegator` is archived from the default install set (2026-08-19). Rules are generic only. Memory uses both `~/.skillbird/memory/` and `.planning/memory/`. Skillbird rule/memory sync is a later engine slice. | User lock 2026-08-19 / content landed `8444d68` | Active | OpenCode-as-default dispatch |

## Verification And Delivery Baseline

- Run focused tests first, then full tests, typecheck, build, and package or install smoke checks according to blast radius.
- Owned-skill changes require `skillbird format-skills --check`. Rule and memory files are not yet part of that formatter.
- High, planning-managed, phase, milestone, or explicit completion claims require an independent frozen-point **host-native** audit and controller spot-checks. Foreign OpenCode audit is opt-in.
- Leftover: `workflow.mjs` `validateOpenCodeAudit` still requires the literal `Provider: OpenCode` on this repository's planning-managed complete gate. Generalize that gate; do not treat it as the default dispatch policy. See `docs/RULES-AND-MEMORY.md`.
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
| SRC-RULES-MEMORY | Current rules, memory policy, leftover engine work | `docs/RULES-AND-MEMORY.md` | MUST_READ for resume, skill/rule/memory, or delegation changes | Project docs |
| SRC-OWNED-RULES | Always-on generic habits | `rules/owned/` | MUST_READ for implementation, mutation, git, vision, or delegation | Owned rules |
| SRC-MEMORY | Resume index and daily notes | `.planning/memory/` and `~/.skillbird/memory/` | MUST_READ for resume, missing context, High | Memory; never overrides requirements or code |
| SRC-WIKI | Project knowledge base when present | `LLM-know-how-wiki/` or project-defined path | READ_IF_RELEVANT | Knowledge base |
| SRC-PRIOR-PHASE | Prior decisions and evidence linked by this context or the active phase | `.planning/phases/<linked-phase>/` | READ_IF_RELEVANT | Historical evidence |

## Superseded Decisions

- DeepSeek-first remains valid historical evidence for completed records created under USR-20260729-001 and USR-20260730-001. It is no longer the prospective model-selection policy after USR-20260803-001.

## Open Questions

- Model quality is intentionally not encoded as a static ranking. The controller records task-specific selection rationale and revises its choice from observed evidence.
- A missing or conflicting source that can change behavior, architecture, interfaces, data, security, scope, acceptance, or irreversible work requires user discussion before mutation.
- Skillbird does not yet project `rules/owned` or memory templates onto CLI homes. Until that engine slice lands, hosts without another rule channel need a manual pointer or copy.
- `validateOpenCodeAudit` still hard-requires `Provider: OpenCode`. Next optimization: accept the actual auditor host, then update templates and tests.
