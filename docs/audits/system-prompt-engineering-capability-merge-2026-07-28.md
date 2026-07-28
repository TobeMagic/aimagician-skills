# System Prompt Engineering Capability Merge Audit

**Status:** Implemented
**Owned skill:** `skills/owned/system-prompt-engineering`

## Evidence Baseline

| Source | Baseline commit | Role |
|---|---|---|
| `kangarooking/system-prompt-skills` | `252cd5251641ea0f3bb67878a684785651ccd09d` | Fifteen explicit capability playbooks |
| `asgeirtj/system_prompts_leaks` | `87578587f873183f90dc8205d665527d5e4ee560` | Cross-product examples used only to identify general patterns |

The repositories are cloned under ignored `.planning/references/`. They are not packaged, installed, or copied into the owned runtime.

## Complete Capability Mapping

| Source capability | Owned module | Preserved capability |
|---|---|---|
| persona-design | `02-identity-persona-personality.md` | Role, expertise, audience, behavior boundaries |
| personality-system | `02-identity-persona-personality.md` | Stable traits, contextual adaptation, policy invariance |
| tool-specification | `03-tools-agency-delegation.md` | Schema, discovery, permissions, side effects, recovery |
| agent-delegation | `03-tools-agency-delegation.md` | Worker contracts, context isolation, controller validation |
| safety-guardrails | `04-safety-trust-injection.md` | Risk classification, refusal, containment, recovery |
| injection-defense | `04-safety-trust-injection.md` | Trust boundaries, taint propagation, action-boundary checks |
| memory-system | `05-memory-context-continuity.md` | Layered memory, writes, retention, correction, deletion |
| context-management | `05-memory-context-continuity.md` | Lazy loading, compression, resume, source preservation |
| conversation-flow | `06-conversation-output-citations.md` | States, transitions, clarification, completion |
| output-formatting | `06-conversation-output-citations.md` | Schemas, partial results, channel formatting |
| citation-system | `06` and `07` | Citation integrity, preservation, grounding |
| search-integration | `07-search-grounding-research.md` | Search triggers, source hierarchy, query diversity |
| voice-optimization | `08-channel-and-product-adaptation.md` | Answer-first speech, interruption, audio safety |
| mobile-adaptation | `08-channel-and-product-adaptation.md` | Short resumable interaction and high-impact confirmation |
| code-engineering | `09-code-agent-engineering.md` | Repository workflow, Git safety, tests, review, audit |

## Cross-product Patterns Distilled

The corpus was sampled by path category rather than copied:

- coding and CLI agents: explicit workflow states, bounded writes, repository evidence, test and Git safety;
- general assistants: instruction precedence, persona separation, uncertainty and output contracts;
- search and research: search triggers, source priority, citation preservation, evidence conflict;
- tool and computer-use agents: schema-on-demand, permission tiers, result validation, prompt injection boundaries;
- memory and long-context agents: layered state, compact handoffs, correction and deletion;
- mobile, voice, and multimodal agents: answer-first interaction, channel-specific formatting, interruption and modality limits;
- design and product agents: artifact contracts, iterative review, observable acceptance.

No vendor identity, proprietary wording, hidden prompt, credential, endpoint, or internal operational path is part of the owned skill.

## Combined Enhancements

The owned skill adds capabilities not present as one complete workflow in either source:

- requirement-first composition and explicit authority graph;
- deterministic scenario router;
- structural prompt linter with conditional tool, memory, search, and delegation checks;
- reusable tool permission, memory, threat-model, and evaluation templates;
- adversarial evaluation, versioning, model/runtime compatibility, rollout, monitoring, and rollback;
- source-neutral boundaries with runtime controls explicitly separated from prompt controls.

## Repeatable Audit

Run:

```bash
node scripts/audit-system-prompt-upstreams.mjs
```

The command reports source commits and capability-path deltas. It never fetches, installs, or mutates owned skills. A changed commit or capability list requires human capability review.

