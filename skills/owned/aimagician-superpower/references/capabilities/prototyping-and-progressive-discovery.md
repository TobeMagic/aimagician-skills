# Prototyping And Progressive Discovery

Use this module when a destination is meaningful but the implementation route cannot yet be planned honestly, or when one uncertainty can be resolved more cheaply by a bounded prototype than by discussion.

## Progressive Discovery Map

For large, unfamiliar, or long-running work, maintain:

- **Destination:** measurable end state and acceptance evidence.
- **Known decisions:** user-approved behavior, constraints, architecture, and non-goals.
- **Frontier:** the next boundary where implementation can proceed with current evidence.
- **Fog:** material unknowns beyond the frontier, with why they matter.
- **Blockers:** unresolved dependencies or decisions that prevent the next slice.
- **Next probe:** the smallest exploration, experiment, or tracer slice that reduces the most important uncertainty.
- **Out of scope:** tempting adjacent work that must not expand the milestone.

Use `assets/templates/progressive-discovery-map.md`. Update the map after each probe. Plan the next evidence-producing slice in detail; keep later work at decision-level until the fog clears.

## Durable Vocabulary Loop

Maintain a compact glossary for terms that affect ownership, invariants, API shape, or user behavior. Each term needs a concrete example, counterexample or forbidden conflation, and evidence location. Reuse the same vocabulary in requirements, code, tests, review, and docs. Do not create a glossary for generic words or let vocabulary drift silently between phases.

## Prototype Contract

State one uncertainty as a falsifiable question. Choose the smallest prototype type:

- **logic** for algorithm, state-machine, or data-shape uncertainty;
- **integration** for external contract, compatibility, latency, or failure semantics;
- **UI** for workflow, information hierarchy, interaction, or visual uncertainty;
- **operations** for deployment, migration, observability, or recovery uncertainty.

Define input, output, runnable command, representative case, failure case, evidence threshold, time or cost bound, forbidden production coupling, and one verdict: promote, revise, discard, or investigate. Use `assets/templates/engineering-prototype-brief.md`.

## Vertical Tickets And Blockers

Break work into observable end-to-end tickets. Each ticket names behavior, affected ownership boundaries, acceptance seam, dependencies, files or modules, and completion evidence. Record true blockers separately from ordinary sequencing. Avoid ticket sets that build every database layer, then every service, then every UI without delivering behavior.

## Context-Budget Discipline

- Delegate broad read-only exploration when it would consume substantial main context, then spot-check critical claims.
- Start each bounded implementation or review role with the smallest clean context that contains its contract and evidence.
- Externalize decisions, vocabulary, frontier, commands, and results at phase boundaries.
- Do not compact away an unverified causal chain, red test, migration checkpoint, or reviewer finding mid-slice.
- Resume from the last verified checkpoint, not from a summary claim.

Discovery is complete for a stage when the next design or slice no longer depends on an unstated material assumption. It is not complete merely because many files were read.
