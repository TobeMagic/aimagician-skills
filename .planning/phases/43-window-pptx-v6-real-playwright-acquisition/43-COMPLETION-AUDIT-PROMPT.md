TASK_ID: window-pptx-phase43-completion-audit-20260730
ROLE: auditor
TASK_TYPE: audit
MODALITY: text
OBJECTIVE: Independently decide whether Phase 43 satisfies V6R-ACQ-01 and GOAL-43-01 through GOAL-43-04 at the current uncommitted review point.
DELIVERABLE: Requirement matrix, findings, and APPROVED or NOT_APPROVED decision.
REVIEW_POINT: Current uncommitted diff on feat/window-pptx-v6 after the final real authenticated resume run and focused regression suite.

SOURCE_OF_TRUTH:
- The self-contained FROZEN_EVIDENCE_PACKET at the end of this prompt. It is
  an authorized controller-created audit packet and intentionally replaces
  direct repository inspection for this attempt.

ORIGINAL_REQUESTS:
- USR-V6-11
- USR-V6-12

ACCEPTED_DECISIONS:
- Normal authenticated browser and entitled package links only; no access-control bypass.
- Credentials and commercial bytes remain under ignored .private and are never inspected by this auditor.
- Exact pinned CDN host may be used without cookies; authenticated navigation remains exact-origin.
- Source categories with no actual downloadable package are explicit shortfalls, never invented coverage.

KNOWN_CONTEXT:
- Controller-observed private evidence, sanitized: 32 categories, 6,134 inventory items, 6,086 validated previews, 377 validated package artifacts, 378 artifact item bindings, 372 final selected item IDs, 345 selected IDs bound to artifacts, 24 selected source pages with no direct package link, and three repeated failures terminally marked unavailable.
- All 377 package paths were reconciled by size/hash and remain below the ignored private root.
- No Playwright/Chromium acquisition process remained after the completed run.
- Latest focused acquisition plus private-guard suite at the review point: 56 passed.
- Private bytes, cookie values, private state contents, and source URLs are forbidden to this audit.

REQUIRED_SKILLS:
- cli-agent-delegator: independent audit, severity, model provenance, and evidence discipline.
- aimagician-superpower: phase alignment, request traceability, verification, and closure gate.
- webapp-testing: Playwright lifecycle, browser fixture, resume, and network-boundary assessment.

ALLOWED_SCOPE:
- Load the three required skills, then reason only from the complete frozen
  evidence packet embedded below.
- No repository file read/search is required or allowed in this attempt.

FORBIDDEN_SCOPE:
- Any shell/bash/terminal command, write, network access, real-site browsing,
  or secret/environment inspection.
- Reading any file below skills/owned/window-pptx/.private.
- Listing, finding, statting, checking existence, checking ignore status, or
  otherwise probing any path below skills/owned/window-pptx/.private. The
  sanitized counts in KNOWN_CONTEXT are controller evidence and must not be
  independently re-probed.
- Commit, push, merge, reset, checkout, clean, stash, package installation, or process termination.

PERMISSION_MODE: read-and-run
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: NONE. After loading REQUIRED_SKILLS, do not call any tool:
no bash, terminal, Read, Glob, Grep, search, list, stat, web, task, or write.
The packet below is the entire evidence boundary.
TESTS_AND_EVIDENCE: From the embedded packet only, verify route-aware category identity, preview validation and retry, deterministic diversity, exact-origin and pinned-CDN policy, no-cookie CDN requests, direct-file and OOXML validation, atomic promotion, artifact reconciliation, stable redacted failure codes, bounded smoke, browser cleanup, source shortfall behavior, and secret/private guard coverage.
GIT_POLICY: inspect-only
MODEL_POLICY: DeepSeek reasoning default; Agnes only after explicit DeepSeek usage/quota/rate-limit evidence.
CHILD_AGENT_POLICY: forbidden

STATUS_PROTOCOL: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
FINDING_SEVERITY: Blocker | Important | Nitpick
PROGRESS_PROTOCOL: skill loading, source alignment, diff trace, focused checks, requirement matrix, final decision
STOP_AND_ESCALATE_WHEN: a required source is missing, private/secret access appears necessary, or an allowed command cannot decide a material claim
SESSION_EXPORT: NONE
OUTPUT_FORMAT: Loaded skills; provider/model/attempt chain/session; findings first; one PASS|FAIL|NOT_RUN row for V6R-ACQ-01 and each GOAL-43 criterion; controller-checkable evidence; APPROVED or NOT_APPROVED; final status.

Before substantive work, load every skill named in REQUIRED_SKILLS and report the loaded skill IDs. Apply their workflows and boundaries. You have access to the same installed owned skills as the controller. If any required skill or source of truth cannot be loaded, return NEEDS_CONTEXT with the missing item; do not substitute an improvised workflow.

Four previous audit attempts are invalid: one fallback worker enumerated
private filenames; another changed an exact pytest command by appending an
uninstalled `--timeout` flag and piping through `head`; the third changed the
exact git-status command; the fourth used `ls` after a file-read schema error.
Do not repeat or rely on those sessions. This fresh audit must execute no tool
after the three skill loads. Any attempted repository or private-path probe
requires immediate `BLOCKED` without executing it.

FROZEN_EVIDENCE_PACKET:

- Traceability: USR-V6-11 requires normal authenticated Playwright acquisition
  with all credentials and commercial bytes below ignored `.private`.
  USR-V6-12 requires all 32 real template categories to be inventoried and a
  deterministic, visually diverse, reusable subset selected rather than first-N.
  V6R-ACQ-01 and GOAL-43-01..04 exactly encode those requests.
- Locked architecture: category identity is `(route_path, category_id)`;
  only nonzero `products.aspx` routes form the template taxonomy. Category,
  pagination, and detail navigation are exact-origin. The single pinned HTTPS
  asset host may carry preview/direct-package bytes, never Cookie; legacy HTTP
  is upgraded only for that exact host.
- Implementation anchors in `gaojie_playwright.py`: `_extract_cookie_value`
  accepts raw Cookie, `Cookie:` header, or copied alternating request-header
  lines and fails on ambiguity; `parse_cookie_header` never logs values;
  `_category_key` and `_category_state_key` preserve route-aware identity;
  `_allowed_asset_url` and `_normalize_asset_url` implement exact-origin plus
  pinned-CDN policy; `_download_preview` separates same-origin browser requests
  from cookie-free short CDN requests; `_download_preview_with_retry` plus
  `_retry_failed_previews` provide bounded retry and revisit; `_valid_powerpoint`
  checks direct suffix, ZIP signature, `[Content_Types].xml`, and
  `ppt/presentation.xml`; `_atomic_bytes` promotes atomically;
  `_reconcile_artifacts` rechecks path, size, mtime, and SHA-256 and restores
  artifact-backed item status to PASS; `_download_selected` records `NO_LINK`
  and terminal `UNAVAILABLE`; `_sync_gaojie_impl` owns browser context cleanup
  and a real `maximum_items` smoke path; `sync_gaojie` persists stable
  `GAOJIE_SYNC_CRASHED` rather than exception text.
- Diversity anchors in `gaojie_diversity.py`: validated image decode, SHA-256,
  dHash, color histogram, entropy, edge density, dimensions, aspect ratio;
  deterministic exact-deduplication, near-duplicate suppression, farthest-first
  traversal, and first-N versus selected median-nearest-neighbor evidence.
- Test-source coverage: 18 Gaojie-focused tests cover valid/invalid preview
  fingerprints; cookie-free pinned CDN; exact HTTP upgrade allowlist;
  deterministic diversity beating first-N; secret-free private contact sheets;
  OOXML inspection; Cookie forms/ambiguity; authenticated resumable deduplicated
  fixture sync including restoration of artifact-backed PASS statuses; bounded
  smoke; transient preview retry; rejected login; incomplete taxonomy; CLI
  secret-free wiring; explicit download failure; file/disk caps; and redacted
  stable crash code. The related acquisition/private-guard shard covers 38 more
  tests for redirect auth stripping, private credential boundaries, quarantine,
  rights, atomic resume, catalog/CLI guards, and secret-free output.
- Controller verification at this exact review point:
  `python -m py_compile` passed; Gaojie shard `18 passed, 32 deselected`;
  related acquisition/private-guard shard `38 passed, 18 deselected`; focused
  resume/redacted-crash regression `2 passed`; workflow Phase-43 alignment
  passed. A monolithic invocation was externally terminated after 120 seconds,
  but the two exhaustive disjoint shards cover all 56 relevant tests.
- Sanitized real authenticated evidence: final state and public manifest both
  PASS with `download_pass_completed=true`; exactly 32 route-aware categories;
  6,134 inventory items; 6,086 validated previews and 48 explicit preview
  failures; 372 final selected item IDs; 377 content-hash-unique validated
  PowerPoint package artifacts with 378 item bindings; selected outcomes
  345 PASS, 24 NO_LINK, 3 UNAVAILABLE; three explicit diversity shortfalls;
  no acquisition/browser process remained.
- Secret/private boundary evidence: credential values, Cookie text, private
  source URLs, package bytes, and private state contents were not provided to
  this reviewer. Controller confirmed `.private` is ignored and no private byte
  is tracked. This audit must assess the code/test boundary and accept the
  sanitized real counts as controller UAT evidence rather than re-probe them.
- Known residuals are source facts, not hidden success: some preview-only
  categories expose no editable package, 24 selected pages have no direct link,
  three repeated detail/network failures are terminal, and three categories
  cannot reach the diversity floor. The implementation records rather than
  invents that coverage.

Audit question: Does this frozen packet provide sufficient, internally
consistent evidence that Phase 43 meets V6R-ACQ-01 and GOAL-43-01..04? Report
any unsupported inference as a severity-ranked finding. Do not demand visual
quality or downstream template mining here; those belong to Phase 44.
