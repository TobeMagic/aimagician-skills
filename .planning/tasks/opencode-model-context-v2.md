# Task: opencode-model-context-v2

**Task ID:** opencode-model-context-v2
**Status:** Complete
**Source request:** USR-20260803-001
**Parent milestone:** v5.0
**Parent phase:** 28
**Exception status:** Approved
**Approval source:** USR-20260803-001
**Return checkpoint:** Resume Phase 28 frozen weak-model benchmark briefs, manifests, scoring, and ordinary-model trials after this task is audited, synchronized, and handed off.
**Review point:** Worktree at `2f1b21ca97c03d96dc8057be0637f479c46d5534`, frozen fingerprint `a117c5d8d7e335200a12743f076022232c4d79ab4c9750580c6d103a3d372c72`

## Original Request

Let the controller list and explicitly choose any active free OpenCode model by task difficulty, use quota-aware ordered fallbacks with Agnes last, and add a canonical project context that preserves architecture and cross-phase decisions without forcing every Quick task through the full planning workflow.

## Accepted Decisions

- Every run explicitly names its primary model.
- The controller declares better fallback models; the runtime appends Agnes once at the end.
- OpenCode Zen shares one quota pool; Agnes is an unlimited final fallback; other configured providers use model-specific quota pools.
- Recent relevant documents guide navigation, while source authority still decides conflicts.
- Missing adopted project context blocks phase/milestone/High/resume work but not isolated Quick work.
- Material uncertainty is discussed after recent relevant sources have been read.

## Checklist

- [x] REQ-MODEL-V2-001: expose standalone multi-provider free-model inventory.
- [x] REQ-MODEL-V2-002: require explicit primary model and validate an ordered fallback chain.
- [x] REQ-MODEL-V2-003: enforce user-policy quota scopes and Agnes-final behavior.
- [x] REQ-MODEL-V2-004: implement scoped transitions, retries, rolling quota detection, and schema-v2 provenance.
- [x] REQ-MODEL-V2-005: preserve direct vision-analysis evidence routing with explicit text-model selection.
- [x] REQ-CONTEXT-V1-001: add canonical project context schema, template, migration, and current project record.
- [x] REQ-CONTEXT-V1-002: implement risk-scaled context loading and missing-context gates.
- [x] REQ-CONTEXT-V1-003: add verifiable phase/milestone context promotion.
- [x] REQ-COMPAT-V2-001: preserve legacy audit records and public result fields.
- [x] REQ-SYNC-V2-001: run tests, audit, synchronize Codex/OpenCode, and verify parity.

## Evidence

| Requirement | Evidence | Status |
|---|---|---|
| REQ-MODEL-V2-001 | Live `--list-models --format table --refresh-models` returned 60+ free models across Agnes, OpenCode Zen, sub2api Anthropic, and sub2api OpenAI providers. | PASS |
| REQ-MODEL-V2-002 | `opencode-runner.test.ts` plus live dry-run proved required `--model`, repeated ordered `--fallback-model`, eligibility checks, and compact declared/effective chains. | PASS |
| REQ-MODEL-V2-003 | Unit and fake-CLI integration tests proved `shared:opencode`, model-specific non-Zen scopes, user-policy provenance, sibling skip, and one final Agnes entry. | PASS |
| REQ-MODEL-V2-004 | Fake CLI quota transition, failure classification, network/provider/model rules, rolling output detection, and schema v2 result tests passed. | PASS |
| REQ-MODEL-V2-005 | Vision docs, prompt contract, dry-run route, and content tests preserve `vision-analysis` acquisition followed by explicit text-model selection. | PASS |
| REQ-CONTEXT-V1-001 | Added `PROJECT.md` and `CONTEXT.md` templates, current `.planning/CONTEXT.md`, config adoption, init support, and schema validation tests. | PASS |
| REQ-CONTEXT-V1-002 | Skill and continuity module define recent-first navigation, authority resolution, material uncertainty, Quick exemption, and blocking alignment tests. | PASS |
| REQ-CONTEXT-V1-003 | Phase and milestone closure require PASS promotion or explicit `NO_CHANGE`; exact `CTX-*` membership rejects prefix collisions and the missing/prefix/exact milestone tests pass. | PASS |
| REQ-COMPAT-V2-001 | Legacy Agnes and model-neutral audit fixtures remain accepted; v2 records require rationale and chain provenance; public primary/final/attempt/fallback fields remain. | PASS |
| REQ-SYNC-V2-001 | Build, formatter, 160-test verification set, live list/dry-run, Codex/OpenCode bootstrap, healthy 25/25 doctor, exact key-skill parity, and final independent audit session `ses_03777c62cffeuNvKMPM6QeDt0C` passed. | PASS |

## Delivery Contract

- **Delivery contract:** v1
- **Delivery class:** Non-deployable
- **Context coverage:** PASS
- **Local verification:** PASS
- **CI verification:** N/A
- **Preview verification:** N/A
- **Online-only exceptions:** N/A
- **Artifact provenance:** PASS
- **Premerge decision:** MERGE_READY
- **Implementation merge SHA:** N/A
- **Postmerge verification:** N/A
- **Deployed artifact match:** N/A
- **Provenance exception:** NONE
- **Recovery status:** NOT_REQUIRED
- **Postmerge decision:** N/A

### Stage Evidence

| Stage | Revision / artifact | Environment | Evidence | Result |
|---|---|---|---|---|
| LOCAL | Current controlled worktree | WSL/Linux | Build, formatter, 156 regular/acceptance tests after the final fix, 20 focused runtime tests, and 4 unaffected Bootstrap/TUI smoke tests | PASS |
| CI / PREMERGE | N/A | N/A | Non-deployable skill/runtime change; full local suite is decisive | N/A |
| PREVIEW | Installed owned skills | Codex and OpenCode user directories | Bootstrap, doctor, counts, and `diff -qr` parity | PASS |
| POSTMERGE | N/A | N/A | Non-deployable owned-skill and local CLI runtime update | N/A |

### Online-Only Exceptions

| Check | Why local is insufficient | Target | Expected evidence | Failure response | Owner |
|---|---|---|---|---|---|
| None | N/A | N/A | N/A | N/A | N/A |

### Artifact Provenance

| Implementation SHA | Build / release | Deployed identity | Verification | Result |
|---|---|---|---|---|
| N/A | Local TypeScript build plus owned skill source | Codex/OpenCode installed copies | doctor healthy and exact key-skill parity | PASS |

## Independent Completion Audit

- **Result schema:** v2
- **Provider:** OpenCode
- **Model selection rationale:** `sub2api_openai/gpt-5.6` was selected for cross-runtime workflow reasoning and exact remediation review; Anthropic and Zen fallbacks provided provider diversity, with Agnes appended only as the final fallback.
- **Declared model chain:** `sub2api_openai/gpt-5.6 -> sub2api_anthropic/claude-opus-4-6 -> opencode/nemotron-3-ultra-free`
- **Effective model chain:** `sub2api_openai/gpt-5.6 -> sub2api_anthropic/claude-opus-4-6 -> opencode/nemotron-3-ultra-free -> agnes/agnes-2.0-flash`
- **Primary model:** `sub2api_openai/gpt-5.6`
- **Model:** `sub2api_openai/gpt-5.6`
- **Attempt chain:** `sub2api_openai/gpt-5.6` exit 0, classification success, session `ses_03777c62cffeuNvKMPM6QeDt0C`
- **Model transitions:** NONE
- **Fallback reason:** NONE
- **Session:** `ses_03777c62cffeuNvKMPM6QeDt0C`
- **Run status:** DONE
- **Review point:** Worktree at `2f1b21ca97c03d96dc8057be0637f479c46d5534`, fingerprint `a117c5d8d7e335200a12743f076022232c4d79ab4c9750580c6d103a3d372c72`, stable through audit
- **Requirement matrix:** PASS
- **Blocker:** 0
- **Important:** 0
- **Nitpick:** 0
- **Controller spot-check:** PASS - verified exact-ID Set membership, prefix-collision regression, source/install parity, test evidence, and the no-transition primary audit result.

## Final Decision

**Status:** Complete
**Reason:** All ten locked requirements have passing implementation evidence, local verification, Codex/OpenCode synchronization, and an independent frozen-worktree audit with no unresolved findings.
