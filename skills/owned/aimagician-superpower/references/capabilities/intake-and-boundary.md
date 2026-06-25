# Intake And Boundary

Use this module when the request is ambiguous, multi-step, risky, resumable, or likely to affect user-visible behavior.

## Objective

Convert the request into a concrete work unit with explicit success criteria before planning or editing.

## Process

1. Load available context first: current files, docs, issue text, previous planning artifacts, recent summaries, and relevant git state.
2. Restate the target in concrete terms: what will exist, change, or be proven when the work is complete.
3. Define the delivery unit: quick task, phase, milestone, spike, bug fix, review, or follow-up.
4. Capture scope boundaries:
   - in scope;
   - out of scope;
   - explicit non-goals;
   - user preferences;
   - constraints and dependencies;
   - rollback or stop conditions.
5. Identify gray areas that materially change implementation, acceptance, risk, or UX.
6. Ask only the questions that unblock those gray areas. Prefer concrete options with tradeoffs.
7. Record decisions, assumptions, rejected options, and deferred ideas.

## Discussion Rules

- Do not ask questions already answered by local context.
- Do not convert every small request into a heavy process; scale the ceremony to risk.
- If the user says not to write a spec, still produce a concise implementation plan before editing.
- If the request is too broad, split it into independent phases and start with the smallest useful phase.
- Redirect scope creep into deferred items unless the user explicitly changes the current objective.
- If a missing answer changes architecture, data handling, public behavior, cost, or acceptance, discuss before planning.

## Boundary Output

For larger work, preserve this information in a phase context file:

- objective;
- user-visible outcome;
- success criteria;
- acceptance scenarios;
- assumptions;
- constraints;
- non-goals;
- dependencies;
- risk areas;
- deferred items.

For small work, keep the same information inline in the conversation.
