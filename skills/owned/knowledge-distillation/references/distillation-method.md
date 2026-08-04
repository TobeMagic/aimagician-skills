# Distillation Method

## Stage 0: Source Understanding

Use four passes:

1. **Structure:** identify the source's problem, major parts, progression, and evidence types.
2. **Interpretation:** define the author's terms and reconstruct the main arguments.
3. **Critique:** identify assumptions, counterevidence, internal tensions, and scope limits.
4. **Application:** map claims to decisions or tasks where an agent could act differently.

Assign stable evidence IDs such as `CH03-P014`, `EP02-00:18:20`, or `LECTURE-04-S07`. Every candidate and generated Skill must reference these IDs.

## Stage 1: Segmented Extraction

When the source is large:

- segment by chapters, episodes, lectures, or semantic sections rather than arbitrary token windows;
- give every extractor the source map, vocabulary, evidence-ID convention, and output schema;
- keep raw evidence separate from synthesis;
- record missing or unreadable segments explicitly.

Each extractor returns candidate ID, claim, evidence IDs, confidence, proposed trigger, application, and limitations.

## Stage 2: Verification

Score each candidate:

| Test | Pass condition |
|---|---|
| Recurrence | Two independent evidence locations, or one formal definition plus a worked application |
| Generativity | Produces a defensible action or prediction for a new case |
| Distinctiveness | Cannot be replaced by generic advice without losing decision value |

Classify candidates as `framework`, `heuristic`, `supporting-concept`, or `rejected`. Do not inflate every insight into a separate Skill.

## Stage 3: Executable Construction

Use the R-I-A-T-E-B structure:

- **Reading:** short evidence excerpts and IDs;
- **Interpretation:** source-neutral explanation;
- **Application:** observed source case;
- **Trigger:** future use and non-use conditions;
- **Execution:** ordered decisions, inputs, outputs, and fallback paths;
- **Boundary:** blind spots, conflicts, ethics, and neighboring capabilities.

Generated text should paraphrase the source. Keep quotations short and within applicable copyright limits.

## Stage 4: Relationships

Use four relationship types:

- `requires`: one Skill depends on another result;
- `contrasts`: two Skills offer competing choices;
- `combines-with`: outputs can be composed;
- `escalates-to`: one Skill hands off a higher-risk case.

The index is a routing map, not a promotional catalog.

## Stage 5: Evaluation

Evaluate routing before prose quality:

1. Does the description trigger on the intended user wording?
2. Does it avoid summary, role-play, and sibling-skill prompts?
3. Does execution use source-grounded decisions rather than generic advice?
4. Are uncertainty and missing evidence visible?
5. Can another agent reproduce the result from artifacts alone?
