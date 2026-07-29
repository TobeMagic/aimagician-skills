# Dynamic OpenCode Routing Audit

**Request:** `USR-20260729-001`
**Task:** `cli-agent-dynamic-routing`
**Review base:** `d1eb7acf0bd5a70bf51d8dc40a2c869e135acb27`
**Canonical skills:** `cli-agent-delegator`, `aimagician-superpower`

## Outcome

The implementation makes OpenCode the default worker for eligible locked short tasks, keeps macro decisions with the controller, routes every non-visual task through DeepSeek first, routes visual work through a verified vision model, and limits automatic Agnes fallback to explicit usage, quota, or rate-limit events.

Completion audits remain fresh, independent, and requirement-by-requirement without being Agnes-only. Historical Agnes audit records remain valid.

## Capability Changes

- Added a trigger-level short-task gate for Git checks, tests, reports, localized low-risk fixes, scoped research, visual inspection, and independent review.
- Added ready-to-fill quick-task recipes and isolated bounded-write constraints.
- Added `scripts/opencode-run.mjs` for cached verbose model discovery, capability filtering, current positional prompt syntax, attached progress streaming, failure classification, quota-only Agnes fallback, and attempt provenance.
- Added a verified Agnes image-input override for incomplete custom-provider metadata.
- Made workflow audit validation model-neutral while preserving legacy Agnes records.
- Updated task and phase audit templates with primary model, final model, attempt chain, and fallback reason.
- Updated README, provider guidance, report templates, evals, and regression tests.

## Verification

| Check | Result |
|---|---|
| Focused implementation tests | PASS, 46/46 |
| All skill tests during independent review | PASS, 50/50 |
| Full repository suite | PASS, 24 files and 135 tests |
| TypeScript typecheck | PASS |
| Production build | PASS |
| Skill taxonomy formatter | PASS, 24 checked, no changes or issues |
| Runner syntax check | PASS |
| Text dry-run | PASS, DeepSeek selected |
| Vision dry-run | PASS, Agnes selected |
| Model-cache reuse | PASS |
| Real quota fallback | PASS, DeepSeek rate limit followed by Agnes after process exit |

The first full-suite run used a temporary `node_modules` symlink and produced four smoke-test timeouts. Replacing it with a normal `npm ci --ignore-scripts` install resolved the environment issue: bootstrap smoke passed 2/2, PTY smoke passed 2/2, and the final full suite passed 135/135. `npm ci` reported two high-severity dependency advisories; no unrelated dependency mutation or `npm audit fix` was performed.

## Synchronization

Skillbird Agent preview selected exactly 24 active owner skills and zero plugins for:

- Codex: `/home/aimagician/.codex/skills`
- OpenCode: `/home/aimagician/.config/opencode/skills`

The apply run reported both targets `synced`. A fresh OpenCode verifier then ran Agent `list` and `doctor`:

- provider: OpenCode
- primary model: `opencode/deepseek-v4-flash-free`
- final model: `agnes/agnes-2.0-flash`
- fallback reason: `explicit-usage-limit`
- attempt chain: DeepSeek `usage-limit` -> Agnes `success`
- session: `ses_051819774ffe4mIPjPrORpCNiZ`
- result: both targets healthy, 24 managed, 24 detected, 0 commands, 0 issues

The controller repeated both checks and compared repository and installed hashes for `aimagician-superpower` and `cli-agent-delegator`; all three copies of each skill matched.

## Independent Review

A pre-commit review used:

- provider: OpenCode
- primary model: `opencode/deepseek-v4-flash-free`
- final model: `agnes/agnes-2.0-flash`
- fallback reason: `explicit-usage-limit`
- session: `ses_05187aad7ffetUEsR7lIpI35Or`

It found no code-level Blocker or Important issue. The controller rejected its initial `REQ-SYNC-002` PASS because synchronization had not yet run; that requirement remained `NOT_RUN` until bootstrap, list, doctor, and hash checks completed. Earlier reviewer sessions that exceeded their command envelope were also rejected and are not completion evidence.

## Final Completion Audit

The fresh completion audit reviewed the implementation and post-sync evidence requirement by requirement:

- provider: OpenCode
- primary model: `opencode/deepseek-v4-flash-free`
- final model: `agnes/agnes-2.0-flash`
- attempt chain: DeepSeek `usage-limit` -> Agnes `success`
- fallback reason: `explicit-usage-limit`
- session: `ses_0517e25f7ffedu0ygnIAJx3HPt`
- review point: base `d1eb7acf0bd5a70bf51d8dc40a2c869e135acb27` plus the complete working tree after synchronization
- requirement matrix: 11 PASS, 0 FAIL, 0 NOT_RUN
- findings: 0 Blocker, 0 Important, 0 Nitpick
- recommendation: DONE

The controller spot-checked the decisive branches and reran Agent list/doctor. No completion-critical auditor claim remained unsupported.

## Residual Risk

- DeepSeek was live in model inventory but rate-limited during real runs, so the documented quota fallback selected Agnes.
- OpenCode reports duplicate skill-name warnings because it discovers equivalent skill copies in multiple CLI homes. Skillbird `list` and `doctor` confirm the managed OpenCode target itself contains exactly the 24 owner skills and no plugins.
- The dependency advisories reported by `npm ci` remain outside this scoped skill-routing change.
