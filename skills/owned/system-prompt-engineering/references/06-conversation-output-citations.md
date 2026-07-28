# Conversation, Output, And Citations

## Conversation State

Define states such as intake, clarification, action, waiting, recovery, review, and completion. State transitions need observable triggers and stop conditions.

Ask only questions that materially affect behavior, scope, risk, data, cost, or acceptance. Do not repeat resolved questions. When assumptions are safe, state them and proceed.

## Output Contract

Specify:

- intended audience and decision;
- required fields or schema;
- ordering and length constraints;
- uncertainty and missing-evidence notation;
- error and partial-result shape;
- channel-specific formatting;
- forbidden internal or sensitive content.

Structured output must define invalid-output recovery. Human-readable output should lead with the result, then evidence and next action.

## Citation Contract

When external sources affect factual claims:

- define one citation syntax;
- cite the source, not the tool invocation;
- preserve citations during summary, translation, and rewriting;
- verify the cited location exists and supports the claim;
- distinguish sourced fact from model inference;
- never fabricate a citation when evidence is absent.

Avoid citation clutter for common reasoning or clearly labeled opinion. Use source-level or claim-level granularity based on audit needs.

## Failure Responses

Separate:

- `NEEDS_CONTEXT`: a required source or decision is missing;
- `BLOCKED`: external state prevents progress;
- `PARTIAL`: useful work exists but accepted coverage is incomplete;
- `FAILED`: attempted operation did not meet its contract;
- `COMPLETE`: every accepted requirement has evidence.

