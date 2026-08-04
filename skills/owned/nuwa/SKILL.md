---
name: nuwa
description: Use when distilling a person's, team's, organization's, or school of thought's reasoning patterns into a bounded decision-advisor skill from public or user-provided evidence.
category: research
subcategory: cognitive-distillation
tags:
  - distillation
  - reasoning
  - decision-making
  - perspective
  - research
  - uncertainty
compatibility:
  tools: [bash, python, git]
  requires: A named subject or a clearly scoped reasoning need, evidence sources, and a defined advisory use
---

# Nuwa

Build a bounded reasoning advisor from evidence. Capture how a subject analyzes, decides, explains, and refuses—not a costume, a quotation bank, or an assertion that the subject would know the answer to every question.

## Trigger Boundary

Use this skill when the user asks to distill a person's or group's thinking, create a perspective or decision advisor, compare reasoning styles, or turn a subject's public work into a reusable cognitive framework.

Use `cangjie` when the source is a body of long-form content and the target is its methods rather than a subject's reasoning style. Use ordinary research when the user only wants facts about the subject.

## Intake Gate

Clarify only the decisions that materially change the result:

1. Subject identity and disambiguation.
2. Full perspective or a focused domain.
3. Advisory use: analysis, decision support, writing, teaching, product, or another task.
4. New skill or update to an existing skill.
5. Available first-party material and acceptable secondary sources.

Default to a broad, decision-advisor profile and a standard evidence pass when the user gives a clear subject but no further constraints. Ask before proceeding only when identity, authority, privacy, or source access is materially ambiguous.

## Evidence Workflow

### 1. Define The Lens

Write the target decisions, the subject's relevant time range, and the claims the skill is allowed to make. Separate public evidence from inference and from the user's interpretation.

### 2. Collect Independent Evidence

Use six complementary lanes when evidence supports them:

- written work and long-form arguments;
- interviews and unplanned conversation;
- short-form expression and recurring language;
- external assessments and credible criticism;
- observed decisions and actions;
- chronology and changes over time.

Prefer user-provided and first-party material. Use secondary material to expose context, disagreement, and blind spots, not to replace primary evidence. Record URL or local path, date, source type, and confidence for each material claim.

### 3. Extract Reasoning Patterns

For each candidate pattern, record:

- the situation or input that activates it;
- the mental model or distinction applied;
- the decision heuristic or sequence;
- how the subject expresses or explains it;
- a confirming example and a contradicting or limiting example;
- a confidence level and the evidence supporting it.

Do not mistake repeated slogans for a model. A useful pattern predicts a response to a new but related situation.

### 4. Validate Fidelity

Test the draft against questions the subject has addressed and compare the direction, tradeoffs, and uncertainty to the evidence. Then test a novel question. The advisor must distinguish evidence-backed reasoning from a guess and should decline to impersonate certainty outside its evidence.

Where sources disagree, preserve the tension and explain whether it reflects context, time, audience, or unresolved inconsistency.

## Output Contract

Produce a self-contained advisor Skill with:

- 3–7 high-confidence mental models;
- 5–10 decision heuristics or question sequences;
- expression and explanation patterns only when useful to the requested task;
- anti-patterns and known blind spots;
- explicit limits, confidence labels, and escalation rules;
- positive, negative, neighboring-skill, and novel-question tests.

The Skill's instructions must say when to use the lens, how to apply it to the user's concrete problem, how to show evidence versus inference, and when to refuse a confident answer. Do not include promotional biography, installation guidance, upstream branding, or unrelated personal details.

## Progressive Disclosure

Keep the runtime Skill focused on routing and application. Store detailed research, source excerpts, chronology, and evidence tables under the Skill's `references/` directory. Load them only when a claim or fidelity check requires them.

## Failure Rules

- No source text means no invented profile; request material or narrow the claim.
- A single anecdote cannot establish a stable mental model.
- Do not present a public persona as private belief.
- Do not infer sensitive traits from sparse evidence.
- Do not use the advisor to make high-impact decisions without independent evidence and human judgment.
- If validation is incomplete, label the Skill provisional and do not claim fidelity.
