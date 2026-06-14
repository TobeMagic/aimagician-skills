---
name: skill-creator
description: Use when adding a new SKILL.md, consolidating external skills into owned skills, editing skill triggers/workflows, or updating taxonomy/category frontmatter.
category: build
subcategory: skills
tags:
  - skills
  - authoring
  - taxonomy
metadata:
  merged_from:
    - anthropic-skill-creator
    - writing-skills
    - superpowers-skill-authoring
compatibility:
  tools: [bash]
  requires: Skill goal, target users, and a testable trigger/workflow
---

# Skill Creator

Use this skill to keep owned skills small, triggered correctly, and easy to manage through Skillbird.

## Source Decisions

- Claude's official `skill-creator` provides the authoring loop: clarify intent, draft, test with and without the skill, evaluate, inspect, and iterate.
- Superpowers `writing-skills` provides skill TDD: prove baseline failure before relying on the new instructions.
- Skillbird adds repository ownership: every shipped owned skill must have category metadata and formatter coverage.

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
   - Run `skillbird format-skills --check`.
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
   - For manual evals, use `evals/evals.json` or a phase validation note with prompt, expected behavior, observed behavior, and pass/fail result.
6. Iterate only on observed failures.
   - Tighten descriptions, add guardrails, or move heavy material into references.

## Progressive Disclosure

Keep `SKILL.md` focused on the decision and workflow the agent must follow now. Move bulky API references, templates, examples, or benchmark prompts into `references/`, `scripts/`, or `assets/` and link to them from the body. Load those files only when the task needs them.

## Category Guidance

- `build`: coding, debugging, tests, plans, skill authoring, integrations.
- `research`: evidence gathering, literature, repo analysis, architecture comparison.
- `design`: UI, brand, accessibility, metadata, motion, images, polish.
- `documents`: README, PDF, Word, slides, spreadsheets.
- `operate`: GitHub, Linear, cloud, releases, worktrees, project operations.
- `strategy`: business, product, pricing, customers, marketing, growth.

## Guardrails

- Do not create a new skill when an existing one can absorb the workflow cleanly.
- Do not make broad trigger descriptions that hijack unrelated tasks.
- Do not keep external install/update instructions in owned skills unless the skill's purpose is operating that tool.
- Do not put large copied reference material into `SKILL.md`; link to a reference file when needed.
- Do not claim a merged skill preserves a source workflow until baseline vs with-skill evidence or content regression tests prove it.
- Do not use evals that only check wording; test the behavior or decision the skill is supposed to change.

## Output Contract

When changing skills, report:

- canonical skill chosen;
- sources merged or archived;
- category/subcategory/tags;
- baseline or regression evidence used;
- with-skill result or automated test added;
- verification command and result.
