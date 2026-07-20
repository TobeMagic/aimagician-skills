# Intake And Boundary

Use this module to convert an ambiguous or substantial request into a bounded delivery unit before research, specification, planning, or edits.

## Ground First

Read existing files, planning state, docs, knowledge base, tests, recent summaries, and git status before asking the user. Separate discoverable facts from preferences that require a decision.

## Intake Sequence

1. State what will exist, change, or be proven at completion.
2. Identify the user or system affected and the observable outcome.
3. Choose the delivery unit: quick task, phase, milestone, spike, repair, review, or follow-up.
4. Record in scope, out of scope, constraints, dependencies, compatibility, stop conditions, rollback, and required evidence.
5. Identify gray areas that materially alter architecture, behavior, UX, data, security, cost, schedule, or acceptance.
6. Ask only questions that cannot be answered from available evidence. Offer concrete choices and tradeoffs when possible.
7. Capture decisions, assumptions, rejected options, and deferred work in durable context for resumable tasks.

## Risk Classification

Classify the task before choosing process depth.

- **Low:** at most two known files, reversible, no public contract or data impact, no unresolved decision, one direct verification.
- **Medium:** several files or one integration boundary, visible behavior, compatibility concerns, or multiple verification layers.
- **High:** public API, schema or migration, credentials or permissions, production state, destructive action, installation path, cross-module architecture, multiple agents, or hard-to-reverse effects.

Low-risk work may use an inline target and acceptance check. Medium- and high-risk work requires a formal phase specification. When uncertain, use the higher class until evidence lowers it.

## Discussion Contract

- Discuss WHAT and WHY before HOW.
- Do not re-ask facts already established by source-of-truth files.
- Do not turn a small reversible edit into a milestone.
- Do not let scope expand silently; move adjacent ideas to an explicit deferred list.
- Do not infer a decision that changes public behavior, data, security, cost, or acceptance.
- If the user requests immediate execution but a blocking ambiguity remains, state the exact ambiguity and resolve it first.

## Boundary Output

For formal work, preserve:

- objective and user-visible outcome;
- measurable success and completion evidence;
- in-scope deliverables and explicit non-goals;
- risk class and reasons;
- assumptions and unresolved questions;
- dependencies and compatibility constraints;
- rollback, stop, and escalation conditions;
- deferred ideas with rationale.
