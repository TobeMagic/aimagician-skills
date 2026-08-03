---
name: knowledge-distillation
description: Use when turning a book, long-form article collection, course, interview, podcast transcript, or video transcript into a traceable set of executable Agent Skills. Trigger for "distill this book/content", "拆书", "知识蒸馏", "把这本书/课程/视频做成 skill", or requests for reusable frameworks rather than a summary. Do not use for simple summaries, reviews, or a person's simulated perspective.
category: research
subcategory: knowledge-distillation
tags:
  - knowledge-distillation
  - long-form
  - skill-generation
  - evidence
  - multi-agent
metadata:
  capability_modules:
    - references/distillation-method.md
    - references/extractor-contracts.md
    - references/output-contract.md
    - assets/templates/source-overview.md
    - assets/templates/generated-skill.md
    - assets/templates/test-prompts.json
  preferred_companions:
    - deep-research-system
    - skill-creator
    - skill-optimizer
compatibility:
  tools: [bash, file, web, agent]
  requires: Source text or transcripts, source metadata, and a writable output directory
---

# Knowledge Distillation

Convert long-form source material into a coherent, evidence-backed skill system that an agent can invoke in real situations. The output is not a summary. It is a set of atomic decisions, procedures, checks, and boundaries tied back to source evidence.

## Routing Boundary

Use this skill for methods embedded in long-form content. Route requests to:

- `perspective-distillation` when the target is how a person thinks, decides, or communicates;
- `skill-optimizer` when the target is improving an existing Skill;
- a summarization workflow when the user wants notes, a review, or a digest without executable skills.

## Start Gate

Before extraction:

1. Obtain the actual source text, transcript, or readable files. Never distill from model memory.
2. Record title, creator, publication date, source type, language, and source paths or URLs.
3. Lock the intended users, decisions the output should improve, desired granularity, and output root.
4. Check for an existing `PIPELINE_STATE.md` and resume from its latest completed gate.
5. Pilot one source before a batch unless the user explicitly accepts batch risk.

If source access, licensing, or intended use is unclear, stop before copying or extracting protected material. Prefer paraphrased methods and short evidence excerpts.

## Canonical Pipeline

### 0. Source Map

Read the complete source at an appropriate level, then create `SOURCE_OVERVIEW.md` with its thesis, structure, vocabulary, assumptions, contradictions, evidence quality, and likely applications. Use `references/distillation-method.md` and `assets/templates/source-overview.md`.

**CHECKPOINT:** confirm the source map and target emphasis before expensive extraction.

### 1. Independent Extraction

Run five bounded extractor roles from `references/extractor-contracts.md`:

1. frameworks and decision models;
2. principles, rules, and checklists;
3. cases and worked examples;
4. counterexamples, failure modes, and limits;
5. terminology and concept relationships.

Parallel roles must write separate evidence files. If parallel agents are unavailable, run the same contracts sequentially without changing the output schema.

### 2. Triple Verification

For every candidate, test:

- **recurrence:** supported by at least two independent source locations or one explicit formal definition plus application;
- **generativity:** can guide a new situation not copied from the source;
- **distinctiveness:** adds more than generic competent advice.

Pass all three for a framework. Downgrade partial candidates to supporting heuristics or reject them with a reason. Preserve accepted and rejected evidence.

**CHECKPOINT:** show accepted, downgraded, and rejected candidates before generating Skills.

### 3. Executable Skill Construction

Build each accepted unit with:

- source reading and evidence identifiers;
- interpretation in original wording;
- past application from the source;
- future trigger and non-trigger;
- numbered execution procedure;
- failure branches and recovery;
- boundary, limitations, and neighboring-skill distinction.

Use `references/output-contract.md` and `assets/templates/generated-skill.md`. Keep one user outcome per Skill; combine units only when they share the same trigger and execution loop.

### 4. Skill-System Linking

Create a shared glossary and an index that records prerequisite, contrast, composition, and escalation relationships. Update each Skill's routing section from this graph. Do not create circular mandatory dependencies.

### 5. Pressure Testing

Create 5-10 prompts per generated Skill from `assets/templates/test-prompts.json`:

- expected trigger;
- expected non-trigger;
- ambiguous boundary;
- sibling-skill confusion;
- evidence-poor or unsafe case.

Use fresh evaluators when available. A failed test returns the unit to construction or verification; do not patch only the expected wording.

### 6. Delivery And Resume State

Generate the manifest, index, glossary, digest, test evidence, and final state. Run:

```bash
node scripts/validate-distillation.mjs --root <distillation-root> --format json
```

Install or sync generated Skills only through the repository's owned-skill manager and only when the user requests installation.

## Failure Handling

| Trigger | First response | Fallback |
|---|---|---|
| Source exceeds agent context | Segment by structural units with stable evidence IDs | Process in resumable waves and synthesize only from written evidence |
| Parallel agents unavailable | Run extractor contracts sequentially | Reduce scope but preserve all five evidence dimensions |
| Candidate lacks recurrence | Downgrade to a heuristic | Reject and retain the reason |
| Source contains contradictions | Preserve dated or contextual variants | Expose the unresolved tension as a boundary |
| Generated Skills overlap | Recompute trigger and sibling routing | Merge only if execution loops are materially identical |
| Evaluation cannot run | Record a dry-run and missing evidence | Do not claim validated effectiveness |

## Completion Contract

Completion requires:

- an explicit source manifest and resumable state;
- traceable accepted and rejected candidates;
- generated Skills with executable procedures and boundaries;
- an index and glossary;
- trigger, non-trigger, ambiguity, and sibling-confusion tests;
- validator success and a report of any evaluation that remained dry-run.

Do not claim completeness from source coverage alone. The generated Skill system must prove that agents can route and apply the distilled methods.
