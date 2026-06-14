---
name: academic-paper-workflow
description: Use when the user asks about academic papers, paper ideas,
  literature review, baseline or module design, method synthesis, contribution
  framing, evidence planning, experiments, manuscript structure, journal or
  conference selection, SCI, EI, 中文核心, CCF, CSSCI, OA, submission, revision,
  reviewer response, or light thesis integration.
compatibility:
  tools:
    - bash
    - python
    - git
  requires: Optional network access for live paper, venue, policy, and indexing checks
category: research
subcategory: academic
tags:
  - papers
  - literature
  - experiments
---

# Academic Paper Workflow

Use this skill as a discuss-driven operating system for academic-paper publication. The route is:

```text
paper goal -> field map -> idea selection -> method synthesis -> contribution-evidence map -> experiment plan -> venue ladder -> manuscript package -> submission -> revision
```

The workflow is about publishable papers, not career planning. It supports professional research design by default and a resource-constrained strategy mode when time, budget, data, or venue requirements are tight. Speed, venue level, and evidence depth are strategy tradeoffs; they are never permission to fabricate, hide failures, copy text, manipulate baselines, use unverified third-party manuscript services, or mislead reviewers.

## Discuss-Driven Rule

Start with the smallest useful question and keep the chain moving. Ask only for missing high-impact information; if the user says to proceed, infer conservative defaults and mark assumptions.

Every substantive response should include:

- `Current paper state`
- `Recommended route`
- `Missing decisions`
- `Next discuss question`
- `Concrete deliverable`

If the user only wants advice, answer inline. Write files under `docs/academic_paper_workflow/` only when the user asks for artifacts.

## Method Essence

Translate paper-craft needs into professional academic operations:

| User need | Workflow meaning |
|---|---|
| idea / 选题 | publishable problem choice scored by field fit, novelty room, baseline/data availability, evidence cost, and venue fit |
| method improvement | baseline + modular additions, method transfer, protocol adaptation, or benchmark/resource contribution with traceable sources |
| contribution framing | problem-gap-method-evidence-limitation chain, often using CARS-style introduction logic |
| innovation / 创新点 | novelty + usefulness + evidence + clear boundary, not inflated wording |
| venue selection / 选刊 | scope fit + recognition/indexing + review speed + APC/OA + warning-list risk + fallback ladder |
| revision / 返修 | point-by-point issue triage, added evidence where material, exact manuscript change log |

## Reference Router

Load the smallest relevant reference:

- [`references/workflow-index.md`](./references/workflow-index.md): task router and deliverable map
- [`references/discuss-driven-router.md`](./references/discuss-driven-router.md): exact question chain and strategy modes
- [`references/literature-workflow.md`](./references/literature-workflow.md): search strategy, reading matrix, field map
- [`references/idea-selection-workflow.md`](./references/idea-selection-workflow.md): idea scoring, strategy route, topic rescue
- [`references/method-synthesis-workflow.md`](./references/method-synthesis-workflow.md): baseline choice, modular method design, target-venue adaptation
- [`references/contribution-evidence-workflow.md`](./references/contribution-evidence-workflow.md): contribution framing, CARS, innovation, claim-evidence map
- [`references/experiment-workflow.md`](./references/experiment-workflow.md): comparison, ablation, case study, metrics, reproducibility
- [`references/paper-writing-figures-workflow.md`](./references/paper-writing-figures-workflow.md): IMRaD structure, figures, tables, polishing
- [`references/venue-selection-workflow.md`](./references/venue-selection-workflow.md): SCI/EI/OA/中文核心/CCF/CSSCI venue ladder and official checks
- [`references/submission-revision-workflow.md`](./references/submission-revision-workflow.md): author-guide checklist, submission package, revision handling
- [`references/reviewer-response-workflow.md`](./references/reviewer-response-workflow.md): review triage, response letter, resubmission audit
- [`references/thesis-integration-workflow.md`](./references/thesis-integration-workflow.md): light thesis integration, chapter structure, formatting, similarity checks
- [`references/integrity-and-risk-controls.md`](./references/integrity-and-risk-controls.md): boundaries, risk conversion, venue safety

## Default Deliverables

For a full workflow, produce an adaptive package:

```text
docs/academic_paper_workflow/
  00-context.md
  01-literature-map.md
  02-idea-scorecard.md
  03-method-synthesis-map.md
  04-contribution-evidence-map.md
  05-experiment-plan.md
  06-venue-ladder.md
  07-writing-submission-checklist.md
  08-revision-plan.md
  09-thesis-integration-checklist.md
```

For short tasks, produce only the needed artifact, such as a venue ladder, contribution-evidence map, reviewer response table, or experiment matrix.

## First Discuss Gate

Collect or infer these, in this order:

1. Paper target: rapid recognition, steady publication, high-quality target, or fallback/rescue.
2. Hard constraints: required tier, deadline, recognition rules, APC/OA budget, language, article type.
3. Current assets: idea, keywords, literature, dataset, baseline, code, results, draft, target venue, reviews.
4. Field map: recent papers, datasets, metrics, baselines, accepted venue patterns.
5. Missing bottleneck: idea, method, contribution, evidence, venue, submission, revision, or thesis integration.

If urgent, assume: public data, reproducible baseline, narrow claims, official venue checks, and the lowest venue level that satisfies the stated paper requirement.

## Workflow

1. Route the request with `workflow-index.md` and `discuss-driven-router.md`.
2. Build a context snapshot and identify the next missing decision.
3. If direction is unclear, run literature mapping before recommending a method.
4. If method is unclear, score ideas and build a method synthesis map.
5. If the paper has results, build the contribution-evidence map before venue selection.
6. Select venue ladder before final polishing; venue taste changes contribution scale, length, figures, and experiments.
7. Before submission, verify author guide, ethics/AI/data/code statements, formatting, and duplicate-submission rules.
8. On reviews, triage issues before drafting responses.
9. For thesis work, integrate existing paper outputs into a thesis structure and formatting checklist without turning this skill into career planning.
10. Keep integrity controls active throughout.

## Final Response Format

Use concise Chinese by default, preserving standard English terms. For planning or advice-only work:

- `当前状态`
- `推荐路线`
- `关键缺口`
- `下一步讨论问题`
- `本轮交付`

For file-producing work, include the generated paths and what each file contains.
