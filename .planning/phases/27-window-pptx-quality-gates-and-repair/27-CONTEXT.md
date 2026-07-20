# Phase 27 Context: Quality Gates and Repair

Phase 27 converts the renderer's placeholder inspect/repair hooks into a delivery gate. It must measure the rendered candidate, emit stable evidence, repair only deterministic presentation drift, and refuse changes that worsen weighted defects or any hard gate.

The source deck and final output remain immutable during inspection and repair. Repairs operate only on the in-memory candidate presentation before transactional saving. Package and reopen evidence is finalized from the candidate transaction; real Windows package behavior remains part of Phase 29 acceptance.

The five layers are:

1. package/transaction evidence;
2. COM/native-object/editability evidence;
3. geometric and text-capacity evidence;
4. visual-density and compatibility evidence;
5. deck-level consistency, rhythm, and repetition evidence.

Only page-size drift, governed shape geometry, typography, tags, and similarly reversible structural defects are auto-repairable. Content rewriting, arbitrary font shrinking, asset invention, layout improvisation, and destructive source changes are never repair actions.
