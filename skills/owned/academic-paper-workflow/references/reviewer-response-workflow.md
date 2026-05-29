# Reviewer Response and Manuscript Self-Audit Workflow

Use this after desk reject, reject, major revision, minor revision, or reviewer feedback. The goal is to triage risk, revise evidence, and answer point by point.

## Triage by Severity

Classify every issue before responding:

| Class | Meaning | Response Strategy |
|---|---|---|
| Blocking | causes desk reject or hard reject if unresolved | fix first with concrete evidence |
| Substantive | weakens evidence, novelty, method, or contribution | add experiment, analysis, citation, or reframe claim |
| Formatting | style, template, presentation, minor detail | adjust directly when reasonable |
| Misreading | reviewer misunderstood because manuscript was unclear | clarify politely and revise text |
| Infeasible | request cannot be completed under real constraints | explain constraints and offer alternative evidence |

Do not label a substantive issue as "misreading" until re-reading the manuscript from the reviewer's perspective.

## Common Dangerous Issues

Self-audit for:

1. Artifact integrity
   - title, author/anonymity, figures, tables, cross-references, supplementary files

2. Number consistency
   - every number in text, table, figure, caption, and response letter matches the source log

3. Method fairness
   - no privileged information, unfair tuning, hidden data leakage, or asymmetric baseline treatment

4. Citation integrity
   - real DOI/arXiv/proceedings, correct titles, authors, venue, year, no duplicate bib entries

5. Overclaiming
   - "first", "SOTA", "universal", "root cause", "significant" only when evidence supports it

6. Evaluation protocol transparency
   - dataset, split, N, seed, metrics, hyperparameters, tuning/evaluation separation

7. Reproducibility package
   - code/data availability, configs, commands, model versions, environment, random seeds where relevant

8. Baseline adequacy
   - comparison set fits the claim and venue tier

9. Caption accuracy
   - captions say exactly what figures/tables show

10. Limitation honesty
   - scope boundaries are stated near the claims they qualify

## Response Letter Template

```markdown
### [Reviewer point number]

> [Exact quote or close paraphrase]

**Response:**
[Answer directly.]

**Action taken:**
- Changed [Section X, Page Y, Lines Z-Z]
- Added/removed/rewrote [specific content]

**Evidence added:**
- [New experiment/analysis/citation, if any]
```

## Handling Reviewer Patterns

| Reviewer Pattern | Likely Meaning | Response |
|---|---|---|
| "Novelty is unclear" | contribution framing is weak | state one core addition and distinguish from closest work |
| "Why not compare with X?" | baseline set may be incomplete | add if feasible or justify exclusion criteria |
| "Improvement is small" | effect size or framing problem | contextualize, add subgroup/error analysis, narrow claim |
| "Not statistically significant" | evidence is insufficient for the claim | increase evaluation if possible or reduce claim strength |
| "Cannot reproduce" | details are missing | add configs, data/split, code, seed, command, environment |
| "References are wrong" | scholarship trust risk | rebuild bibliography from official records |
| "Scope mismatch" | venue fit problem | revise framing or change target venue after rejection |

## Resubmission Decision

After rejection:

- desk reject for scope: change venue or framing quickly
- reject for evidence: fix experiments before resubmission
- reject for novelty: rework contribution framing or lower venue
- reject for presentation: repair structure, figures, and claims
- conflicting reviews: identify editor's decision rationale first

Do not resubmit the same paper unchanged unless the rejection was purely scope-based and the new venue clearly fits.

## Single Source of Truth

Every manuscript number should come from one data file, log, or script output. Manual number copying creates contradictions during revision.
