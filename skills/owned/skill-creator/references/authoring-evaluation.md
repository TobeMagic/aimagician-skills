# Authoring Evaluation Contract

Use one happy-path prompt, one ambiguity or negative prompt, and one real tool
or artifact assertion. Keep model, tools, repository state, and budget equal
between baseline and treatment. A fresh judge checks only predeclared
assertions, lists regressions, and marks incomparable runs invalid.

Store prompts, redacted outputs, command evidence, and verdicts under the
owner repository's `quality/skill-evals/<skill-id>/`; never place an evaluation
corpus inside an installable Skill directory. A static score can identify a
gap, but it cannot replace behavior evidence.
