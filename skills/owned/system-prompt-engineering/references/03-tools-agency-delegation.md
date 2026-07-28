# Tools, Agency, And Delegation

## Tool Contract

For each tool or namespace define:

- discovery trigger and selection criteria;
- input schema and validation;
- output meaning and provenance;
- side effects and reversibility;
- permission tier;
- timeout, retry, idempotency, and duplicate-call behavior;
- partial result, failure, and fallback behavior;
- sensitive fields that must not be printed or persisted.

Prefer schema-on-demand or service-scoped discovery when a complete tool catalog would consume material context.

## Permission Tiers

Use at least:

1. **Prohibited:** never execute.
2. **Explicit confirmation:** irreversible, external, financial, privileged, destructive, or identity-affecting action.
3. **Bounded automatic:** reversible action inside the accepted scope.
4. **Read-only:** observation without mutation.

Global tool permission does not override the task scope. Confirmation must name the exact action, target, effect, and recovery limit.

Use `../assets/templates/tool-permission-matrix.md`.

## Action Loop

1. Select the narrowest capable tool.
2. Validate arguments against current evidence.
3. Check authority and permission immediately before the call.
4. Execute once unless idempotent retry is defined.
5. Validate the result rather than trusting a success-shaped response.
6. Reconcile partial results and side effects.
7. Stop or escalate when the recovery contract is exhausted.

## Delegation

The controller retains requirement interpretation, architecture decisions, risk acceptance, and final completion judgment.

A worker brief includes objective, source of truth, known decisions, required skills, allowed and forbidden scope, permission mode, deliverable, evidence, status protocol, and stop conditions. Child delegation inherits the same contract unless explicitly prohibited.

Validate material worker claims against primary evidence. Separate worker facts, inferences, and controller-confirmed conclusions.

