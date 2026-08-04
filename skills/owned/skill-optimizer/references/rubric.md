# Skill Quality Rubric

Score each dimension from 0 to 10, then multiply by its weight. The final score is the weighted sum divided by 10. Do not calculate a final score while effectiveness is `NOT_RUN`.

| # | Dimension | Weight | Full-score evidence |
|---|---|---:|---|
| 1 | Frontmatter and trigger quality | 7 | Valid identity and taxonomy; description says when to trigger and when not to trigger; no vague catch-all. |
| 2 | Workflow clarity | 12 | Ordered stages have explicit inputs, actions, outputs, and completion conditions. |
| 3 | Failure-mode encoding | 12 | Material failures use trigger, first response, and fallback branches. |
| 4 | Checkpoints | 6 | Expensive, ambiguous, destructive, or irreversible decisions stop for confirmation. |
| 5 | Actionable specificity | 18 | Commands, schemas, thresholds, examples, and decision rules can be executed without invention. |
| 6 | Resource integration | 4 | Every referenced file exists, is loaded only when needed, and materially improves execution. |
| 7 | Architecture and clarity | 12 | One outcome, progressive disclosure, low duplication, explicit sibling routing, proportionate size. |
| 8 | Real task effectiveness | 23 | Controlled prompts prove improved correctness, completeness, efficiency, safety, and routing. |
| 9 | Anti-pattern and risk guardrails | 6 | Explicit non-triggers, prohibited actions, and dangerous-action boundaries prevent predictable misuse. |

## Scoring Rules

- Cite a section, file, command output, or test result for every score.
- Penalize absence, not wording style. A table and a concise branch are equivalent if both are executable.
- Use weighted gap `(10 - score) * weight / 10` to select the next improvement.
- Treat dimensions 2, 3, and 4 as a related workflow cluster; one precise branch can improve all three.
- A runtime-neutrality failure blocks release even when the numeric score is high.
- A missing or invalid behavioral test leaves dimension 8 as `NOT_RUN`.
- Scores are diagnostic. Acceptance still requires concrete behavior evidence and human review for subjective outcomes.

## Effectiveness Criteria

Judge each response against task-specific assertions, then consider:

1. Did it satisfy the actual user outcome?
2. Did it trigger or abstain correctly?
3. Did it produce verifiable artifacts or decisions?
4. Did it avoid new risk, delay, verbosity, or inappropriate process?
5. Is the improvement attributable to the Skill rather than changed tools or context?

Use at least one negative or ambiguity prompt to catch over-triggering.
