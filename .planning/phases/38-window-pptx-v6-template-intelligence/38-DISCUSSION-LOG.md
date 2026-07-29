# Phase 38 Discussion Log

## Decisions

| Topic | Considered | Decision | Reason |
|---|---|---|---|
| Reference rights | inspiration only; private source; packaged authorized source | packaged authorized source | source and TemplatePack are SHA-identical and authorization is recorded |
| v1 migration | replace; mutate; adapt | additive adapter | prevents regressions and preserves source integrity |
| Pilot size | all 110; 60–100; commercial-first | balanced 84 | meets the accepted pilot range and covers every family without waiting for auth |
| Complete-work spines | one physical only; wait for downloads; physical plus first-party composition | one physical plus two first-party composition | legal, reproducible, executable, and scenario-complete |
| Model freedom | raw layout design; top candidate selection; no model | stable ID selection plus bindings | uses GPT-5.5 visual judgment without unsafe geometry/code |
| Materialization | HTML; COM; portable native | physical v1 adaptation or registered native composition | preserves editability and portability |
| Visual target | copy pixels; copy logic; generic modernization | copy hierarchy/rhythm/motif logic and improve defects | matches the accepted art direction without inheriting dated flaws |
| Repair | repeated component fixes; bounded alternative; open re-generation | one same-family alternative then `NO_FIT` | prevents repair accumulation |

## Assumptions

- First-party registered compositions are legally distributable.
- The authorized work-report TemplatePack remains immutable and hash-bound.
- Phase 39–40, not Phase 38, own final pixel parity and artifact acceptance.

## Rejected Options

- Treating unverified legacy templates as certified candidates.
- Waiting for authenticated commercial sync before building the legal pilot.
- HTML-to-PPTX as the canonical implementation path.
- Allowing a model to emit coordinates, OOXML, arbitrary styles, or repair
  instructions.

## Deferred Work

- Commercial inventory synchronization and certification after credential
  rotation.
- Cross-source physical OOXML slide import.
- Weak-model decision distillation, owned by v6.1.

## External State

- Commercial acquisition: `NEEDS_AUTH`.
- Phase 38 first-party pilot: not blocked.
- DeepSeek V4 Flash Free: retry once per delegated text task; explicit rate
  limit permits exact-prompt Agnes fallback.
