# Debugger Prompt

Investigate a failure without speculative patching.

## Inputs

- Expected and actual behavior: `<FAILURE>`
- Reproduction and evidence: `<EVIDENCE>`
- Allowed scope and commands: `<SCOPE>`

## Investigate

Reproduce, minimize, classify determinism, trace backward to the first incorrect state, compare working and failing cases, form one falsifiable hypothesis at a time, and design a discriminating probe. Preserve evidence and secret safety.

Do not modify implementation unless the task explicitly authorizes a repair after root cause is supported.

## Return

Use the common status contract. Report reproduction, causal chain, evidence, ruled-out hypotheses, root cause confidence, smallest repair, regression test, and residual uncertainty.
