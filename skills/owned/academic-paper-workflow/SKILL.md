---
name: academic-paper-workflow
description: |
  Build an end-to-end academic paper workflow for graduate students: literature search and reading, topic positioning, baseline/model or method selection, experiment planning, comparison/ablation/case-study design, paper story and figure planning, journal/conference selection, submission checklist, and revision response. Use this skill whenever the user mentions 学术论文, 小论文, SCI, EI, 中文核心, 选刊, 投稿, 返修, 文献调研, 做实验, baseline, 消融实验, 开题, 研究生论文, or asks how to turn research work into a publishable paper. This skill should also trigger when the user wants a pragmatic graduate-paper survival plan, even if they only mention one part such as “帮我选期刊” or “实验怎么设计”.
compatibility:
  tools: [bash, python, git]
  requires: Optional network access for live journal/paper lookup; optional use of deep-research-system for large-scale retrieval
---

# Academic Paper Workflow

Use this skill as a standalone operating system for academic-paper work. It provides reusable workflows, reference checklists, and decision routes for:

- literature search and reading
- topic positioning
- baseline and method construction
- experiment design
- paper story and figures
- journal/conference selection
- submission and revision

Do not help fabricate results, misrepresent baselines, hide material failures, plagiarize text, use paper mills, or game review dishonestly. When the user needs speed or graduation safety, reduce venue ambition or scope instead of weakening academic integrity.

## Reference Router

Choose the smallest reference set needed:

- [`references/workflow-index.md`](./references/workflow-index.md): route the task and decide deliverables
- [`references/literature-workflow.md`](./references/literature-workflow.md): search, access, review papers, reading matrix
- [`references/topic-baseline-module-workflow.md`](./references/topic-baseline-module-workflow.md): topic positioning, baseline choice, module bank, method rationale
- [`references/experiment-workflow.md`](./references/experiment-workflow.md): comparison, ablation, case study, metrics, experiment logs
- [`references/paper-writing-figures-workflow.md`](./references/paper-writing-figures-workflow.md): paper story, structure imitation, three core figures, polish
- [`references/venue-selection-workflow.md`](./references/venue-selection-workflow.md): journal/conference ranking, SCI/EI/Chinese core/CCF/OA, fallback ladder
- [`references/submission-revision-workflow.md`](./references/submission-revision-workflow.md): author guideline checklist, submission package, reviewer response
- [`references/reviewer-response-workflow.md`](./references/reviewer-response-workflow.md): post-review triage, manuscript self-audit, point-by-point response, 10 most dangerous review issues
- [`references/integrity-and-risk-controls.md`](./references/integrity-and-risk-controls.md): academic integrity, predatory venue checks, paper-mill refusal

If the user needs real paper retrieval or a reusable literature system, also use the `deep-research-system` skill if available.

## Default Output Contract

Unless the user requests another location, create or update:

```text
docs/academic_paper_workflow/
  00-context.md
  01-literature-map.md
  02-reading-matrix.csv
  03-baseline-and-module-map.md
  04-experiment-plan.md
  05-paper-story-and-figures.md
  06-journal-shortlist.csv
  07-submission-checklist.md
  08-revision-response-plan.md
```

If the task is only advisory, return the same structure inline.

## Discuss Gate

Before building a full plan, collect or infer these items. Ask only for missing high-impact items:

- field and topic keywords
- degree/graduation requirement: no paper, EI conference, Chinese core, SCI, CCF, school-specific A/B/C/D, or unknown
- goal: graduate, job-oriented, PhD/academic track, award/scholarship, or uncertain
- time budget: months until submission or graduation
- current assets: dataset, code, baseline, preliminary results, draft, target journal, advisor requirement
- constraints: budget/APC, open access allowed or not, warning list, school recognition rules
- integrity stance: reproducible experiments and truthful reporting

If the user is urgent and says to proceed, assume:

- prioritize graduation and time safety
- use public literature and reproducible baselines
- target the lowest journal/conference level that satisfies the hard requirement unless the user says they want PhD/top-tier outcomes

## Workflow

1. Route the task with `workflow-index.md`.
2. Build or update the context file.
3. Run literature workflow if the direction is not already mapped.
4. Build baseline/module map if method is unclear.
5. Build experiment matrix before writing claims.
6. Build paper story and figure/table plan.
7. Select target venue and fallback ladder before final writing.
8. Prepare submission checklist.
9. On revision, prepare point-by-point response and marked manuscript plan.
10. Keep integrity and risk controls active throughout.

## Final Response Format

For planning tasks, return:

- `Current state`
- `Recommended route`
- `Literature plan`
- `Baseline/method plan`
- `Experiment plan`
- `Paper story and figures`
- `Journal/conference ladder`
- `Submission/revision actions`
- `Risks and next actions`

For file-producing tasks, include generated paths and what each file contains.
