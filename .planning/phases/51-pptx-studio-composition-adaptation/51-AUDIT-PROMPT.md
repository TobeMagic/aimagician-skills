# Phase 51 Independent Audit Prompt

Audit Phase 51 as an independent **read-only** reviewer. Do not write, format,
commit, access network/credentials, read any `.private` file, start child
agents or inspect private assets. You may read public code, schemas, tests and
Phase 51 planning/evidence; run focused existing tests and workflow validation.

Review V7-COMPOSE-01 and V7-ADAPT-01 against `51-SPEC.md`. Confirm that:

1. selection supports exact-deck/page/component modes but cannot perform
   filesystem discovery, arbitrary source selection, invalid sequence or
   undeclared style fallback;
2. style signatures are deterministic, catalog-derived and coarse enough for
   real multi-page composition without allowing random art direction;
3. adaptation output is value-free and binds only safe selected IDs, registered
   facts/assets and fixed operations, rejecting raw geometry/style/OOXML;
4. CLI paths are atomic and use supplied compiled JSON only;
5. tests and evidence substantiate the stated failure behavior.

Return only compact Markdown: `Decision: APPROVED` or `Decision: BLOCKED`, a
findings table with `Blocker`/`Important`/`Nitpick`, paths/line references, and
PASS/FAIL rows for both requirements. Do not mention private content, paths,
filenames or credentials.
