# Task: skill-capability-optimization-2026-08-13

**Task ID:** skill-capability-optimization-2026-08-13
**Status:** In progress
**Source request:** USR-20260813-001
**Parent milestone:** v6.1
**Parent phase:** 49
**Exception status:** Approved
**Approval source:** USR-20260813-001
**Return checkpoint:** Preserve Phase 49 and resume its workflow completion gate after this controlled off-phase task.
**Review point:** NOT_RUN

## Original Request

Raise the selected owned Skills to a credible 90+ Darwin total through measured
capability improvement. Complete the first and second optimization batches plus
`github-readme-highstar` and `interface-design`; do not modify `docx`, `pdf`,
`xlsx`, or `window-pptx`.

## Accepted Decisions

- A credible 90+ result requires a static weighted score of at least 70 and a
  controlled effectiveness score of at least 9/10; static-only scores remain
  diagnostic rather than final.
- The 19 selected Skills are grouped into core control-plane, research, and
  design batches. Shared planning records and quality evidence are serialized;
  Skill file ownership is partitioned for review and editing.
- `quality/skill-evals/skill-capability-optimization-2026-08-13/` is the
  allowed non-runtime location for prompt contracts and blind comparison
  evidence. No installable Skill folder may contain an `evals/` directory.
- The work is non-deployable. Local quality checks, frozen-point review, and
  source/install parity are required; no online-only evidence is applicable.
- `cli-agent-delegator` remains an external-worker runtime, but dispatch is
  optional and requires a net context, independence, or long-running-operation
  benefit. `agent-workstream-orchestrator` is reserved for multi-lane or
  durable-session coordination. Skill-system maintenance and specialist Skills
  are retained as non-default routes.

## Checklist

- [x] SKILL-90-CORE-01: Improve the 11 core control-plane and operational Skills with explicit executable routes, failure branches, checkpoints, and sibling boundaries.
- [x] SKILL-90-RESEARCH-01: Improve the six research and knowledge Skills with precise trigger boundaries, evidence-quality failures, checkpoints, and reusable output contracts.
- [x] SKILL-90-DESIGN-01: Improve `github-readme-highstar` and `interface-design` without reducing their existing HTML-first, repository-branding, or presentation boundaries.
- [ ] SKILL-90-EVAL-01: For every selected Skill, run accepted baseline/treatment pressure scenarios including a non-trigger or ambiguity route, at least one real-tool/artifact test, and an independent blind evaluation.
- [ ] SKILL-90-PURITY-01: Prove referenced paths resolve, source/runtime neutrality holds, no Skill-local eval corpus exists, and excluded Skills are unchanged.
- [ ] SKILL-90-VERIFY-01: Pass formatting, static audit, quality-evidence validation, package checks, frozen independent audit, and Codex/OpenCode source-install parity.
- [x] ROUTING-01: Narrow external-worker and workstream triggers; retain
  maintainer and specialist Skills as explicit on-demand routes.
- [x] RUNTIME-01: Propagate controller cancellation through the OpenCode model
  chain so cancellation cannot launch an Agnes fallback.

## Evidence

| Requirement | Evidence | Status |
|---|---|---|
| SKILL-90-CORE-01 | 11 modified Skill contracts; all selected static audits >=70/77 | PASS |
| SKILL-90-RESEARCH-01 | 6 modified Skill contracts; all selected static audits >=70/77 | PASS |
| SKILL-90-DESIGN-01 | `github-readme-highstar` and `interface-design` static audits >=70/77 | PASS |
| SKILL-90-EVAL-01 | `.planning/audits/skill-capability-opencode-scope-incidents-2026-08-13.md` | NOT_RUN: controlled evaluator invalid |
| ROUTING-01 | `.planning/audits/skill-routing-rationalization-2026-08-13.md` | PASS |
| RUNTIME-01 | `tests/skills/opencode-runner.test.ts` | PASS |
| SKILL-90-PURITY-01 | NOT_RUN | NOT_RUN |
| SKILL-90-VERIFY-01 | NOT_RUN | NOT_RUN |

## Delivery Contract

- **Delivery contract:** v1
- **Delivery class:** Non-deployable
- **Context coverage:** NOT_RUN
- **Local verification:** NOT_RUN
- **CI verification:** NOT_RUN
- **Preview verification:** NOT_RUN
- **Online-only exceptions:** NOT_RUN
- **Artifact provenance:** NOT_RUN
- **Premerge decision:** NOT_RUN
- **Implementation merge SHA:** NOT_RUN
- **Postmerge verification:** NOT_RUN
- **Deployed artifact match:** NOT_RUN
- **Provenance exception:** NONE
- **Recovery status:** NOT_REQUIRED
- **Postmerge decision:** NOT_RUN

### Stage Evidence

| Stage | Revision / artifact | Environment | Evidence | Result |
|---|---|---|---|---|
| LOCAL | TBD | Local | Skill format, static audit, behavioral evidence, targeted tests | NOT_RUN |
| CI / PREMERGE | TBD | CI | Typecheck, test, build, package dry-run, frozen review | NOT_RUN |
| PREVIEW | N/A | N/A | Non-deployable Skill content | N/A |
| POSTMERGE | N/A | N/A | No deployed artifact | N/A |

### Online-Only Exceptions

| Check | Why local is insufficient | Target | Expected evidence | Failure response | Owner |
|---|---|---|---|---|---|
| None | Non-deployable Skill content | N/A | N/A | N/A | N/A |

### Artifact Provenance

| Implementation SHA | Build / release | Deployed identity | Verification | Result |
|---|---|---|---|---|
| TBD | N/A | N/A | Non-deployable task | N/A |

## Independent Completion Audit

- **Result schema:** v2
- **Provider:** OpenCode
- **Model selection rationale:** NOT_RUN
- **Declared model chain:** NOT_RUN
- **Effective model chain:** NOT_RUN
- **Primary model:** NOT_RUN
- **Model:** NOT_RUN
- **Attempt chain:** NOT_RUN
- **Model transitions:** NOT_RUN
- **Fallback reason:** NOT_RUN
- **Session:** NOT_RUN
- **Run status:** NOT_RUN
- **Review point:** NOT_RUN
- **Requirement matrix:** NOT_RUN
- **Blocker:** NOT_RUN
- **Important:** NOT_RUN
- **Nitpick:** NOT_RUN
- **Controller spot-check:** NOT_RUN

## Final Decision

**Status:** In progress
**Reason:** Implementation and audit are pending.
