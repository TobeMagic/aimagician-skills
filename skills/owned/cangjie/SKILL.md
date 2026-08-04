---
name: cangjie
description: Use when converting a book, long article, course, interview, podcast, or transcript into a set of executable, reusable skills with traceable evidence, explicit boundaries, and trigger tests.
category: research
subcategory: knowledge-distillation
tags:
  - distillation
  - books
  - methodology
  - extraction
  - skill-authoring
  - evidence
compatibility:
  tools: [bash, python, git]
  requires: Source text or a user-approved local/web corpus, a target output directory, and a testable use case
---

# Cangjie

Convert long-form knowledge into small skills that an agent can apply. The output is an executable knowledge system, not a summary, review, quotation collection, or author role-play.

## Trigger Boundary

Use this skill when the requested source is a book, long article, course, lecture, podcast, interview, transcript, or other substantial body of knowledge and the desired result is one or more reusable skills.

Do not use it for a short summary, a reading note, a bibliography, or a personality/voice simulation. For a person's reasoning style, use the `nuwa` skill. For improving an existing Skill, use the `darwin` skill.

## Intake Gate

Before extraction, record:

1. Source identity, format, date, and access path.
2. The user's intended decisions or tasks that the resulting skills should improve.
3. Whether the source is local-only, local-first with web supplementation, or web-based.
4. Output directory and the expected number of atomic skills.
5. Evidence and copyright constraints. Quote only what is necessary; prefer paraphrase and source pointers.

If no usable source text is available, ask for it or explain the allowed retrieval path. Do not reconstruct a source from memory.

## Extraction Pipeline

### 1. Build The Source Map

Read the source in chunks and write a source map before extracting. Capture its structure, recurring concepts, terminology, claims, examples, counterexamples, and unresolved tensions. Record chapter, page, timestamp, or section references for every candidate.

### 2. Extract In Parallel

Separate extraction by evidence role so one reading does not hide gaps:

- frameworks: decision processes, models, and reusable procedures;
- principles: rules, checklists, constraints, and priorities;
- cases: situations where the source applies the method;
- counterexamples: failure modes, exceptions, and warnings;
- glossary: terms and distinctions needed by the resulting skills.

Parallel execution is optional. If subagents are unavailable, run the same roles serially and save each result immediately.

### 3. Verify Candidates

Keep a candidate only when all three checks pass:

- **cross-evidence:** the idea is supported in at least two independent parts of the source;
- **transfer:** it can guide a new situation, not only restate a passage;
- **distinctiveness:** it is more useful than a generic common-sense instruction.

Record rejected candidates and the reason. Preserve contradictions rather than averaging them away.

### 4. Compile Atomic Skills (RIA)

Each skill should contain the following six parts:

- **Reading:** minimal source evidence and a precise locator;
- **Interpretation:** the method in original, operational language;
- **Past application:** a source-grounded example;
- **Future trigger:** the situation that should activate the skill;
- **Execution:** ordered steps, decisions, and expected artifacts;
- **Boundary:** when it does not apply, known blind spots, and escalation conditions.

Keep one decision or method per skill. Do not produce several nearly identical skills merely to mirror source chapters.

### 5. Link The Skill Set

Create an index containing skill purpose, trigger, non-trigger, inputs, outputs, and relations. Distinguish prerequisites, combinations, and conflicts. Put shared terms in a glossary instead of repeating definitions in every skill.

### 6. Pressure-Test Before Delivery

For every generated skill, create prompts for:

- a clear positive trigger;
- a clear non-trigger;
- a neighboring skill that could be confused with it;
- an incomplete or contradictory input;
- a real transfer problem not stated in the source.

Check that the agent chooses the correct skill, follows the executable steps, cites uncertainty, and respects the boundary. Revise the smallest failing part and retest.

## Output Contract

Deliver a self-contained directory containing, as applicable:

```text
<corpus>/
  SOURCE-MAP.md
  INDEX.md
  GLOSSARY.md
  VERIFIED.md
  candidates/
  rejected/
  <skill-id>/SKILL.md
  <skill-id>/test-prompts.json
```

Each output Skill must have a narrow trigger description, an explicit boundary, source-grounded evidence, executable steps, and at least one positive and one negative test. Keep raw source material outside the runtime Skill unless the user explicitly needs it and it is safe to retain.

## Resume And Failure Rules

- Read the existing state file before restarting; continue from the last completed stage.
- Save each stage result before starting the next stage.
- If a source cannot be accessed, mark the gap and continue only when the remaining evidence supports an honest result.
- If parallel work hangs, downgrade to serial work without changing the output contract.
- If evidence conflicts, keep both claims, identify confidence, and avoid false synthesis.
- Never claim a complete distillation when candidate verification, boundaries, or trigger tests are missing.
