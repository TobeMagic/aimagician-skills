# Validation And Update

## Validation Matrix

| Test | Input | Pass |
|---|---|---|
| Known position | Three documented questions | Direction and reasoning align with cited evidence |
| Edge inference | Related question without a known answer | Output is model-grounded and explicitly uncertain |
| Voice | One short analysis | Distinctive constraints are present without catchphrase imitation |
| Contradiction | A changed or domain-dependent position | Correct dated or contextual view is selected |
| Non-trigger | Biography, generic summary, deceptive imitation, or unrelated advice | Skill declines or routes correctly |

Use at least two independent evaluators for important published Skills. Evaluators receive evidence IDs but not the synthesis rationale that could anchor their judgment.

## Quality Gates

- 3-7 mental models with evidence and failure conditions;
- at least three concrete honest boundaries;
- expression DNA covers at least three measurable dimensions;
- source quality and cutoff are explicit;
- current facts are researched before use;
- no fabricated quotations or private beliefs;
- no creator attribution or runtime-specific installation noise.

## Update Procedure

1. Read the existing cutoff and weak dimensions.
2. Refresh conversations, decisions, and timeline after the cutoff.
3. Classify new evidence as reinforcing, narrowing, contradicting, or novel.
4. Update only affected models and tests.
5. Re-run contradiction, edge, and non-trigger tests.
6. Preserve old evidence and record why a model changed.
