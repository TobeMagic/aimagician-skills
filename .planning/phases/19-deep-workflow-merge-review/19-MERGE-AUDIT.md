# Phase 19 Merge Audit: Deep Workflow Merge Review

**Date:** 2026-06-14
**Milestone:** v4.0 AImagician Superpower + Skillbird Consolidation
**Requirements:** V4-MERGE-01, V4-MERGE-02, V4-MERGE-03

## Reference Sources Reviewed

- GSD reference repo: `.planning/references/external-skills/repos/gsd-build_get-shit-done`
  - `docs/COMMANDS.md`
  - `docs/AGENTS.md`
- Superpowers reference repo: `.planning/references/external-skills/repos/obra_superpowers`
  - `writing-plans/SKILL.md`
  - `executing-plans/SKILL.md`
  - `writing-skills/SKILL.md`
  - `using-superpowers/SKILL.md`
  - `brainstorming/SKILL.md`
- Claude / community reference repos:
  - `.planning/references/external-skills/repos/anthropics_skills`
  - `.planning/references/external-skills/repos/ComposioHQ_awesome-claude-skills`

## Merge Decisions

| Source Capability | Owned Destination | Decision |
| --- | --- | --- |
| GSD discuss/plan/execute/verify/audit state machine | `skills/owned/aimagician-superpower/SKILL.md` | Kept as canonical workflow backbone |
| GSD durable phase artifacts (`CONTEXT`, `DISCUSSION-LOG`, `RESEARCH`, `VALIDATION`, `UAT`) | `aimagician-superpower` | Preserved as named artifacts |
| GSD plan checker and dependency waves | `aimagician-superpower` | Preserved as `8 Verification Dimensions` and execution waves |
| GSD package legitimacy / install failure checkpoints | `aimagician-superpower` | Preserved as `Package Legitimacy` gate |
| Superpowers `writing-plans` concrete plan discipline | `aimagician-superpower` | Folded into canonical GSD plan phase |
| Superpowers `executing-plans` checkpoint execution | `aimagician-superpower` | Folded into GSD execute phase |
| Superpowers `writing-skills` TDD for skill docs | `skills/owned/skill-creator/SKILL.md` | Preserved as baseline vs with-skill eval loop |
| Claude official skill authoring loop | `skill-creator` | Preserved with eval metadata and progressive disclosure |
| Claude / community webapp testing probe pattern | `skills/owned/webapp-testing/SKILL.md` | Preserved with helper `--help`, `/tmp` probes, `networkidle`, and reconnaissance-first flow |
| Claude / community MCP guidance | `skills/owned/mcp-builder/SKILL.md` | Preserved with protocol checklist, `structuredContent`, annotations, hints, and eval set |
| `code-guidelines` engineering discipline | `skills/owned/code-guidelines/SKILL.md` | Kept independent; `aimagician-superpower` references it instead of duplicating it |
| External auto-update hooks, installer commands, Discord/community links | Not merged | Excluded as noise or environment mutation risk |
| Superpowers creator skill | `skill-creator` | Not kept as separate default skill; useful authoring behavior merged into owned skill |

## Capability Regression Check

Automated content regression coverage was added in:

- `tests/skills/consolidated-skill-content.test.ts`

The test asserts that the owned merged skills retain the specific capability markers that were most likely to regress during consolidation:

- `aimagician-superpower`: GSD artifacts, validation/UAT, 8 verification dimensions, package legitimacy, dependency waves, independent `code-guidelines`.
- `skill-creator`: baseline, with-skill, `evals/evals.json`, quantitative assertions, progressive disclosure, trigger-focused descriptions.
- `webapp-testing`: `with_server.py --help`, `networkidle`, reconnaissance-first flow, `/tmp` probes.
- `mcp-builder`: `structuredContent`, annotations, `readOnlyHint`, `destructiveHint`, 10 read-only eval questions, MCP Inspector.

Targeted verification:

```bash
npx vitest run tests/skills/consolidated-skill-content.test.ts
```

Result: 1 test file, 4 tests passed.

## Outcome

- V4-MERGE-01: Complete. GSD remains the single milestone/phase backbone, while Superpowers plan-writing is folded into the GSD plan phase.
- V4-MERGE-02: Complete. `code-guidelines` remains an independent execution discipline and is referenced by the workflow skill.
- V4-MERGE-03: Complete. Regression coverage now checks the merged owned skills against the highest-value reference capabilities.
