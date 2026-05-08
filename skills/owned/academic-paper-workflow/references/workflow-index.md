# Academic Paper Workflow Index

Use this file to route academic-paper tasks as a standalone academic workflow.

## Task Router

If the user asks for literature search, paper reading, field mapping, review papers, or “我不知道这个方向怎么读文献”:

- read `literature-workflow.md`
- optionally use `deep-research-system` for real retrieval
- output a literature map and reading matrix

If the user asks for topic positioning, baseline, model choice, method design, module selection, or “怎么做出一个方法”:

- read `topic-baseline-module-workflow.md`
- output baseline candidates, module bank, and method rationale

If the user asks for experiments, metrics, SOTA comparison, ablation, case study, or “实验怎么做”:

- read `experiment-workflow.md`
- output an experiment matrix and evidence plan

If the user asks for writing, paper structure, figures, story, title, abstract, related work, or “小论文怎么写”:

- read `paper-writing-figures-workflow.md`
- output paper outline, story chain, figure/table plan, and section checklist

If the user asks for SCI/EI/中文核心/CCF/OA/期刊会议选择/毕业要求:

- read `venue-selection-workflow.md`
- output a venue ladder and shortlist table

If the user asks for submission, author guide, formatting, revision, reviewer response, or “返修怎么回”:

- read `submission-revision-workflow.md`
- output submission checklist or point-by-point response plan

Always keep `integrity-and-risk-controls.md` in mind. Read it when a request touches shortcuts, suspicious venues, paper services, baseline manipulation, selective reporting, author changes, or unclear ethics.

## Default Deliverable Package

For a full workflow, create:

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

If the user only needs advice, return these sections inline:

- Current state
- Route choice
- Literature plan
- Method/baseline plan
- Experiment plan
- Venue ladder
- Writing/submission actions
- Risks

## First-Pass Questions

Ask only what is missing and necessary:

- What is the field/topic?
- What is the hard graduation or evaluation requirement?
- What is the goal: graduate, job, PhD, scholarship, or publication quality?
- How much time remains?
- What assets exist: dataset, code, baseline, draft, results, advisor target?
- What constraints exist: budget/APC, school whitelist/blacklist, language, compute?

If the user wants autonomous defaults, assume graduation-safe, time-aware, reproducible, and conservative venue ambition.
