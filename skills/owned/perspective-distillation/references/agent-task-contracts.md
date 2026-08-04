# Evidence Agent Task Contracts

Use one bounded task per evidence stream. Every task is read-only, persists its result to the assigned file, and returns only a short status summary to the orchestrator.

## Shared Prompt Envelope

Each task receives:

- exact target and lens;
- research depth and source mode;
- assigned evidence stream and output path;
- existing source manifest and cutoff;
- privacy, attribution, quotation, and cost boundaries.

Every task must:

1. inspect the full accessible source rather than rely on snippets;
2. record title, URL or local path, publication date, access date, and source class;
3. distinguish direct evidence, paraphrase, and inference;
4. assign stable evidence IDs;
5. preserve contradictions and failed searches;
6. avoid private data and secret values;
7. stop at the assigned stream boundary.

## Stream Assignments

| Stream | Search and extraction task | Required output |
|---|---|---|
| Authored work | Find recurring arguments, named concepts, and long-form reasoning | Claims, cross-domain recurrence, counterevidence, citations |
| Conversations | Find reasoning under challenge, analogies, changed answers, and refusals | Question, response logic, uncertainty, citations |
| Expression | Analyze representative long and short samples | Measurable style constraints and anti-caricature warnings |
| External views | Collect credible criticism, comparison, and observed blind spots | Attributed agreement, disagreement, and confidence |
| Decisions | Reconstruct consequential decisions from contemporaneous evidence | Context, incentives, action, outcome, hindsight limits |
| Timeline | Track milestones and changes in position | Dated transitions, current cutoff, unresolved gaps |

## Completion Gate

A stream is complete only when its file contains source metadata, evidence IDs, confidence, contradictions, and an explicit coverage gap. A search summary without persisted evidence is incomplete.

The synthesis agent reads all six files only after every stream is complete, blocked with a reason, or explicitly scoped out at a checkpoint.
