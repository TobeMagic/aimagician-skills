# AImagician Control-Plane Darwin Report

## Target and Scope

Target: `skills/owned/aimagician-superpower`.

This experiment measured the lightweight control plane, not general model
intelligence. It used isolated fixture repositories so baseline and treatment
could perform actual file mutations and execute acceptance commands without
touching the working tree.

## Iterations

| Round | Change | Result |
|---|---|---|
| Baseline | No target Skill loaded | Established behavior under identical actor model and fixture controls. |
| 1 | Lightweight control plane and capability index | Three treatment runs completed; Standard incorrectly called an additive callable contract `Quick`. |
| 2 | Require `Standard` at minimum for a new or changed callable/API contract | All treatment runs passed; Standard selected `Standard`, Quick remained compact, and High remained blocked before unsafe mutation. |

## Controlled Evidence

- Actor: `opencode/deepseek-v4-flash-free`, `high` variant for both baseline
  and treatment.
- Full tests: two isolated write-and-test fixtures and one read-only
  public-contract hold gate. This is `full_test`, not a dry run.
- Oracles: `node check.mjs`, `node test.mjs`, and byte-identical no-mutation
  High fixture copies.
- Outputs: `runs/*-baseline.txt` and `runs/*-treatment-r2.txt`.
- Judges: anonymized A/B packets. `opencode/hy3-free` performed a valid
  blind textual comparison. `opencode/big-pickle` also executed all four
  fixture acceptance commands and inspected final artifacts. The initial
  `opencode/laguna-s-2.1-free` session lacked source evidence and was stopped
  as invalid rather than counted.

## Scores

| Measure | Baseline | Treatment |
|---|---:|---:|
| Mean blind behavior score | 9.83 / 10 | 10.00 / 10 |
| Static weighted score | N/A | 75.2 / 77 |
| Darwin total | N/A | 98.2 / 100 |

The treatment's effective score is `10/10`. The relative gain is modest
because the baseline actor was already strong on these controlled tasks. The
claim is therefore limited to the tested routes: no demonstrated universal
improvement is implied.

## Validity and Residual Risk

- Both write fixtures reached their acceptance command; no test was simulated.
- The High fixture remained unchanged and correctly blocked an undecided,
  released public-contract migration.
- All valid judges found no regression. The artifact-executing judge preferred
  treatment in the High case because it cited the governing source line
  precisely.
- The scenario set is small. Future Darwin rounds should add a real
  multi-module repository task and another ambiguity case before changing the
  workflow again.
