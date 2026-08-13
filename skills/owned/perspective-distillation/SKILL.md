---
name: perspective-distillation
description: Use when researching and building or updating an evidence-backed person or topic perspective Skill from public or user-provided material. Trigger for "distill this person's thinking", "create a perspective skill", "XX 的思维方式", "女娲", "造一个视角 skill", or requests for a reusable cognitive advisor. Do not use for biography summaries, impersonation for deception, or extracting methods from one book or course.
category: research
subcategory: perspective-distillation
tags:
  - perspective
  - research
  - knowledge-distillation
  - skill-generation
  - multi-agent
  - on-demand
metadata:
  capability_modules:
    - references/research-and-synthesis.md
    - references/agent-task-contracts.md
    - references/perspective-skill-contract.md
    - references/validation-and-update.md
  preferred_companions:
    - deep-research-system
    - skill-creator
    - skill-optimizer
compatibility:
  tools: [bash, file, web, agent]
  requires: A named person or bounded topic, permitted evidence, intended use, and a writable output directory
---

# Perspective Distillation

Build a runnable perspective from evidence about how a person or school of thought frames problems, makes decisions, communicates, changes position, and exposes uncertainty. The result must be a transparent model, not a claim to reproduce the actual person.

This is an on-demand synthesis workflow. Do not load it for ordinary technical research, product decisions, or implementation unless the requested artifact is a reusable evidence-backed perspective.

## Boundary And Ethics

- Public figures: use attributable public evidence and record a cutoff date.
- Private or non-public people: use only user-provided material with confirmed permission; do not search for private data.
- Never generate identity fraud, fabricated quotations, endorsements, private beliefs, or certainty about unseen decisions.
- Route a single long-form source's methods to `knowledge-distillation`.
- Route general domain-method synthesis to a topic perspective without imitating one person's voice.

## Entry Routing

### Named Target

Lock:

1. exact person or topic;
2. broad or focused lens;
3. intended use and excluded uses;
4. new build or evidence update;
5. local-source-only, local-first, or public-web mode;
6. research depth: quick, standard, or deep.

Defaults are broad lens, decision support, standard depth, and local-first when material exists.

### Need Without A Target

Diagnose the user's decision problem with at most two material questions. Return no more than three differentiated candidates, each with:

- useful lens;
- direct match to the need;
- evidence availability;
- blind spot;
- existing Skill or new research requirement.

Do not start expensive research before the user selects a target.

## Canonical Pipeline

### 0. Workspace And Existing State

Create or resume the structure in `references/perspective-skill-contract.md`. Preserve raw evidence, synthesized findings, decisions, tests, and cutoff dates. Existing Skills use incremental update mode unless their contract is structurally invalid.

### 1. Six-Stream Evidence Collection

Collect independent evidence streams:

1. authored work and formal arguments;
2. long conversations and spontaneous reasoning;
3. expression patterns;
4. external criticism and comparison;
5. consequential decisions and behavior;
6. timeline and changes in position.

Use `references/research-and-synthesis.md` and dispatch each stream with `references/agent-task-contracts.md`. Mark primary, secondary, and inferred claims separately. Local primary material outranks summaries.

If parallel agents are unavailable, execute the same six contracts sequentially and persist each result before continuing.

For permitted video evidence, use the shipped acquisition path instead of relying on search snippets:

```bash
bash scripts/download_subtitles.sh <video-url> <sources/transcripts>
python3 scripts/srt_to_transcript.py <input.srt-or-vtt> <output.txt>
```

The downloader never installs dependencies and prefers available human subtitles before automatic captions. Preserve the original subtitle beside the cleaned transcript.

**CHECKPOINT:** show coverage, source quality, contradictions, missing dimensions, and cost incurred before synthesis.

### 2. Cognitive Synthesis

Extract:

- 3-7 mental models that pass cross-domain recurrence, generativity, and distinctiveness;
- 5-10 decision heuristics with triggering conditions and evidence;
- expression DNA as bounded style rules, not catchphrase imitation;
- values, anti-patterns, intellectual lineage, and at least two meaningful tensions when evidence supports them;
- honest boundaries and evidence cutoff.

Downgrade weak candidates to hypotheses or reject them. Preserve changes over time rather than forcing consistency.

**CHECKPOINT:** confirm the model set, tensions, and boundaries before writing the runtime Skill.

### 3. Runtime Skill Construction

Use `references/perspective-skill-contract.md`. The generated Skill must:

- classify factual, framework, and mixed questions;
- research current facts before applying a perspective when freshness matters;
- select relevant models rather than dumping all models;
- distinguish evidence, interpretation, and speculation;
- express uncertainty and cite the evidence package;
- resist drift into generic assistant prose or theatrical imitation.

Do not add creator attribution, promotional links, installation commands, or personal branding to generated Skills.

### 4. Independent Validation

Run:

1. three known-position tests;
2. one edge inference on an unaddressed but related question;
3. one voice test;
4. one contradiction or position-change test;
5. one non-trigger or unsafe-use test.

Use fresh evaluators when available. Run:

```bash
python3 scripts/quality_check.py <generated-skill/SKILL.md>
python3 scripts/merge_research.py <generated-skill-root>
```

One weak evaluation does not justify invented evidence. After two synthesis revisions, deliver the best honest version with unresolved gaps.

### 5. Update Mode

For an existing Skill, refresh conversations, decisions, and timeline first. Compare new evidence against existing models:

- reinforcing evidence adds examples;
- contradictory evidence updates the timeline or scope;
- a genuinely new recurring model triggers synthesis review;
- stale phrasing is revised without rewriting stable evidence.

### 6. Independent Refinement

After validation passes, run two fresh, read-only reviews when agent delegation is available:

1. a Skill-contract reviewer checks trigger precision, progressive loading, missing branches, and runtime neutrality;
2. an evidence-fidelity reviewer checks model-to-evidence links, unsupported certainty, contradictions, and weak coverage.

Neither reviewer edits files. Reconcile their proposals against the evidence package, accept only changes that preserve or improve the validation matrix, then rerun affected tests. If delegation is unavailable, run the same two review contracts sequentially and label the review as non-independent.

**CHECKPOINT:** Before delivery, reconcile evidence cutoff, source coverage, contradictions, private-person permission boundary, validation results, and unresolved uncertainty; a fluent voice is not proof of a valid perspective model.

## Failure Handling

| Trigger | First response | Fallback |
|---|---|---|
| Fewer than ten useful sources | Reduce model count and confidence | Ask for primary material or stop with a research package |
| Search or agent unavailable | Use available equivalent tools | Switch to local-only mode and expose coverage gaps |
| Source conflict | Keep dated or domain-specific variants | Record an unresolved tension |
| Cost or context pressure | Finish the current persisted evidence stream | Resume in separate phases from saved artifacts |
| Private-person request lacks permission | Stop external collection | Accept only authorized user-provided material |
| Validation resembles generic advice | Strengthen model selection and evidence links | Remove unsupported voice simulation |
| Refinement proposal lacks evidence | Reject the proposal | Record it as an unresolved suggestion |

## Completion Contract

Completion requires a self-contained evidence package, a runtime-neutral Skill, cutoff and uncertainty disclosure, independent validation results, and explicit unresolved gaps. A polished voice without evidence is a failure.
