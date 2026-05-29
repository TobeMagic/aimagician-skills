# Academic Paper Workflow Index

Use this file to route paper tasks. Keep the workflow paper-centered: idea, method, contribution, evidence, venue, writing, submission, revision, and light thesis integration.

## Task Router

If the user is vague, urgent, or asks "流程怎么走":

- read `discuss-driven-router.md`
- output current state, route, missing decisions, next discuss question, and one concrete deliverable

If the user asks for 文献调研, field map, review papers, keywords, datasets, metrics, or "这个方向怎么读":

- read `literature-workflow.md`
- output literature map, keyword dictionary, reading matrix, and field gaps

If the user asks for idea, 选题, 创新点, 快发, 稳妥发表, 发好, high-quality target, or route choice:

- read `idea-selection-workflow.md`
- output idea scorecard, strategy route, and next validation step

If the user asks for baseline, module, method design, model improvement, method synthesis, method transfer, or incremental contribution:

- read `method-synthesis-workflow.md`
- output baseline candidates, module bank, synthesis route, and claim boundaries

If the user asks for contribution, title, abstract, Introduction, Related Work, innovation framing, or manuscript positioning:

- read `contribution-evidence-workflow.md`
- output contribution statement, claim-evidence-limitation map, and section outline

If the user asks for experiments, metrics, SOTA comparison, ablation, case study, robustness, or "实验怎么做":

- read `experiment-workflow.md`
- output experiment matrix, evidence plan, reproducibility log schema, and fairness checks

If the user asks for writing, figures, tables, translation, polishing, similarity, or paper structure:

- read `paper-writing-figures-workflow.md`
- output IMRaD outline, figure/table plan, and writing checklist

If the user asks for SCI, EI, OA, 中文核心, CCF, CSSCI, CSCD, 北核, 普刊, 选刊, 投稿目标, or publication route:

- read `venue-selection-workflow.md`
- output official-check plan, venue ladder, fallback route, and risk notes

If the user asks for submission, author guide, formatting, cover letter, ethics/AI statement, revision, reviewer response, or 返修:

- read `submission-revision-workflow.md`
- for reviews also read `reviewer-response-workflow.md`
- output submission checklist or point-by-point response plan

If the user asks for 学位论文, thesis, chapter structure, blind review, formatting, or similarity checking:

- read `thesis-integration-workflow.md`
- output thesis chapter map, source-output mapping, formatting checklist, and consistency risks

Always keep `integrity-and-risk-controls.md` active. Read it when the request touches integrity-sensitive requests, suspicious venues, third-party manuscript services, selective reporting, baseline manipulation, authorship, AI writing, or unclear ethics.

## Full Deliverable Package

Create only when the user asks for files:

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

Inline advice-only answers should use the same logic without creating files.

## Minimal First Questions

Ask no more than one to three high-impact questions at a time:

- What is the paper target: rapid recognition, steady publication, high-quality target, or fallback/rescue?
- What hard rule must the venue satisfy: SCI/EI/中文核心/CCF/CSSCI/OA/none/unknown?
- What assets already exist: literature, dataset, baseline, code, results, draft, reviews, or thesis template?

If the user says to continue, infer the safest route and state assumptions.
