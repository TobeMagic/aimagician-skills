# Evaluation And Lifecycle

## Evaluation Matrix

Test:

- normal success;
- ambiguous request;
- conflicting instructions;
- lower-trust instruction injection;
- unauthorized or irreversible tool action;
- malformed tool input and partial tool output;
- search conflict or missing citation;
- memory correction and deletion;
- context compression and resume;
- channel adaptation;
- unavailable capability;
- completion pressure with missing evidence.

Use `../assets/templates/evaluation-matrix.md`.

## Assertions

Prefer observable assertions:

- selected or refused the correct action;
- requested confirmation at the correct boundary;
- did not call a forbidden tool;
- preserved citation and trust labels;
- returned the required schema;
- distinguished failure from missing context;
- retained decisions after compression;
- did not reveal sensitive or hidden content.

Do not evaluate only tone or keyword presence.

## Adversarial Testing

Vary authority language, quoted instructions, encoding, role-play, urgency, long-context placement, tool-result injection, memory poisoning, and multi-step indirection. Test both false negatives and over-refusal.

## Versioning

Record:

- prompt version and runtime/model assumptions;
- requirement IDs and change reason;
- changed modules and expected behavior;
- evaluation baseline and deltas;
- compatibility and migration notes;
- rollout cohort, monitoring signal, rollback threshold, and owner.

## Release Gate

Ship only when:

- required scenarios pass;
- no unresolved high-impact safety or permission regression exists;
- output and tool contracts remain compatible or have migration;
- model/runtime variants in scope are tested;
- the rollback path is executable;
- residual uncertainty is explicit.

After release, sample real failures, add minimal regression cases, and change the smallest responsible rule. Avoid adding broad prose for one isolated failure.

