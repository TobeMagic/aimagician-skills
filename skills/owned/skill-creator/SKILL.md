---
name: skill-creator
description: Maintainer-only. Use when adding or consolidating owned Skills, editing Skill triggers/workflows, or updating taxonomy/category frontmatter. Do not use for ordinary application development, repository exploration, or one-off prompting.
category: build
subcategory: skills
tags:
  - skills
  - authoring
  - taxonomy
  - maintainer-only
compatibility:
  tools: [bash]
  requires: Skill goal, target users, and a testable trigger/workflow
---

# Skill Creator

Use this skill to keep owned skills small, triggered correctly, and easy to manage through Skillbird.

This is not a default engineering companion. Load it only when the delivered artifact is an owned Skill or Skillbird taxonomy change.

## Skill Shape

Every owned skill should include:

- YAML frontmatter with `name`, `description`, `category`, `subcategory`, and `tags`;
- clear trigger conditions;
- a workflow the agent can follow;
- guardrails that prevent misuse;
- an output contract or acceptance checklist;
- references/scripts only when they materially improve execution.

Frontmatter rules:

- `description = trigger`: describe when to use the skill, not the workflow steps.
- Keep the description narrow enough that unrelated tasks do not load the skill.
- Put workflow detail in the body, not the description shortcut.

## Merge Workflow

1. Inventory source skills.
   - Identify overlapping triggers, duplicated workflows, and unique strengths.
2. Choose the canonical owner skill.
   - Merge by user outcome, not by source repository.
   - Keep the strongest workflow and fold useful checks from the others into it.
3. Remove noise.
   - Do not copy update hooks, installer commands, community links, or branding that does not help execution.
4. Add taxonomy.
   - Use one of the six categories: `build`, `research`, `design`, `documents`, `operate`, `strategy`.
   - Use lowercase slug tags.
5. Verify.
   - From the owner repository root, run `node dist/cli/index.js format-skills --check` (or the installed `skillbird format-skills --check`). It validates that owner repository's `skills/owned` tree; it is not a generic formatter for an arbitrary temporary directory.
   - Run catalog/manager tests when install behavior changes.

## Skill TDD And Eval Loop

Treat skill authoring like test-driven development for process documentation:

1. Define pressure scenarios.
   - List tasks where an agent should use the skill and tasks where it should not.
   - Include at least one misuse scenario that would catch an overly broad trigger.
2. Run a baseline.
   - Capture how the agent behaves without the new or edited skill.
   - Record the failure mode: skipped step, wrong tool, shallow answer, unsafe edit, or over-triggering.
3. Draft the smallest skill body that fixes that behavior.
   - Prefer direct rules, compact examples, and references over long prose.
4. Run with-skill evaluation.
   - Compare baseline and with-skill outputs on the same prompts.
   - Use quantitative assertions where possible, such as "mentions all required artifacts", "asks no more than one blocking question", or "does not include installer hooks".
5. Record eval metadata.
   - Store durable checks in tests when possible.
   - In an owner repository, store manual evals at `quality/skill-evals/<skill-id>/evals.json`; otherwise use an external harness or phase validation note with prompt, expected behavior, observed behavior, and pass/fail result. Installed runtime packages must not depend on eval files.
6. Iterate only on observed failures.
   - Tighten descriptions, add guardrails, or move heavy material into references.

## Authoring Checkpoints

### 1. Lock The Public Contract

Record the outcome, trigger and non-trigger prompts, sibling boundary, runtime scope, and one observable acceptance signal before editing a Skill.

### 2. Prove The Treatment

Keep the model, task, tools, repository state, and budget comparable; reject a treatment that improves wording but not a predefined observable behavior.

### 3. Release Only A Pure Package

Verify referenced paths, taxonomy, runtime/source neutrality, and the external quality record before installing or publishing.

**CHECKPOINT:** A Skill is not ready when baseline/treatment evidence, a negative scenario, or a package-purity check is missing.

**CHECKPOINT:** Confirm every referenced path resolves and every public trigger has a sibling or non-trigger boundary before static scoring or installation.

**CHECKPOINT:** If an evaluator cannot compare equivalent prompts, model, tools, repository state, and budget, mark the experiment invalid instead of assigning an effectiveness score.

## Progressive Disclosure

Keep `SKILL.md` focused on the decision and workflow the agent must follow now. Move bulky API references, templates, examples, or benchmark prompts into `references/`, `scripts/`, or `assets/` and link to them from the body. Load those files only when the task needs them.

## Category Guidance

- `build`: coding, debugging, tests, plans, skill authoring, integrations.
- `research`: evidence gathering, literature, repo analysis, architecture comparison.
- `design`: UI, brand, accessibility, metadata, motion, images, polish.
- `documents`: README, PDF, Word, slides, spreadsheets.
- `operate`: GitHub, cloud, releases, agent workstreams, and project operations.
- `strategy`: business, product, pricing, customers, marketing, growth.

## Guardrails

- Do not create a new skill when an existing one can absorb the workflow cleanly.
- Do not make broad trigger descriptions that hijack unrelated tasks.
- Do not keep external install/update instructions in owned skills unless the skill's purpose is operating that tool.
- Do not put large copied reference material into `SKILL.md`; link to a reference file when needed.
- Keep eval corpora, generated reports, author biographies, source branding, and repository-specific policy outside the installable Skill package.
- Do not claim a merged skill preserves a source workflow until baseline vs with-skill evidence or content regression tests prove it.
- Do not use evals that only check wording; test the behavior or decision the skill is supposed to change.

## Failure Handling And Checkpoint

| Trigger | First response | Fallback |
|---|---|---|
| Trigger overlaps a sibling or the target outcome is ambiguous | Narrow the public description and compare the sibling routes | Discuss merge versus routing before creating another public Skill identity |
| A reference, test, or runtime-purity check fails | Repair or remove the owning route and rerun the check | Keep the candidate uninstalled and record the unresolved evidence gap externally |
| Treatment changes prose without improving controlled behavior | Reject the change and return to the failed pressure scenario | Preserve the baseline and seek a smaller executable rule rather than adding bulk content |

- Trigger overlaps a sibling Skill: narrow the description or merge the capability before adding a new public identity.
- Referenced file is missing: fail the package check; do not leave a dead progressive-disclosure route.
- Treatment improves prose but not behavior: reject it and revise against the failed pressure scenario.
- Runtime package contains evals, source branding, project policy, or generated reports: move them to the owner repository's quality, docs, or planning surface.
- Capability preservation is uncertain: keep the merge open and run controlled baseline/treatment scenarios.

Before declaring a Skill ready, verify trigger and non-trigger cases, all referenced paths, taxonomy, runtime purity, one behavioral improvement, and one negative scenario.

## Output Contract

When changing skills, report:

- canonical skill chosen;
- sources merged or archived;
- category/subcategory/tags;
- baseline or regression evidence used;
- with-skill result or automated test added;
- verification command and result.

Read [authoring evaluation contract](references/authoring-evaluation.md) when designing or judging a controlled Skill experiment.

```json
{"prompt":"<fixed pressure scenario>","expected":["<observable assertion>"],"forbidden":["<regression>"]}
```
