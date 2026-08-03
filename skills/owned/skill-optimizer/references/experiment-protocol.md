# Controlled Skill Experiment

## Test Set

Use two or three representative prompts:

- primary happy path;
- difficult or ambiguous path;
- non-trigger or unsafe path when routing matters.

Record the expected observable behaviors before execution. Avoid expectations that only repeat wording from `SKILL.md`.

## Baseline And Treatment

Keep model, task context, repository state, tools, time budget, and output contract constant.

- **Baseline:** execute without loading the target Skill.
- **Treatment:** execute with the target Skill and only the references it routes to.

Save complete outputs. Redact secrets without hiding failures.

## Independent Evaluation

Use a fresh evaluator that did not author the candidate. Hide version labels and alternate response order when practical. The evaluator must:

1. score each predefined assertion;
2. identify factual or executable evidence;
3. list regressions introduced by either response;
4. state uncertainty;
5. choose baseline, treatment, tie, or invalid.

Use a second evaluator when the result is subjective or close. The main agent validates critical file and command claims.

## Validity Gates

- At least one test must exercise real tools or artifacts.
- More than 30% dry runs invalidates the effectiveness claim.
- A changed prompt, model, tool set, repository state, or budget invalidates direct comparison unless separately controlled.
- One excellent sample does not erase a trigger or safety regression.
- If a test cannot run, report `NOT_RUN`; never substitute imagined output.

## Iteration

Change one dimension or tightly coupled workflow cluster per round. Re-run the same test set. Accept only a strict, evidence-backed improvement. Stop after three rounds or two consecutive accepted gains below two weighted points.

## Result Record

For every round record:

```text
skill:
round:
changed_dimension:
files:
baseline_score:
candidate_score:
delta:
eval_mode: full_test | mixed | dry_run | not_run
judge_sessions:
accepted:
reason:
regressions:
```
