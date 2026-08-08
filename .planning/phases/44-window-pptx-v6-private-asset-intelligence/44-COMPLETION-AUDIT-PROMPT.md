TASK_ID: window-pptx-phase44-completion-audit-20260730
ROLE: independent completion auditor
TASK_TYPE: audit
MODALITY: text
OBJECTIVE: Decide whether Phase 44 satisfies V6R-MINE-01 and GOAL-44-01
through GOAL-44-04 from the frozen sanitized evidence packet below.
DELIVERABLE: Findings first, exact requirement matrix, APPROVED or
NOT_APPROVED, and DONE or DONE_WITH_CONCERNS.

SOURCE_OF_TRUTH:
- The self-contained FROZEN_EVIDENCE_PACKET below. It replaces direct
  repository/private inspection for this audit.

REQUIRED_SKILLS:
- cli-agent-delegator
- aimagician-superpower

PERMISSION_MODE: evidence-only
WRITE_SCOPE: NONE
ALLOWED_COMMANDS: NONE. Load the two required skills, then call no tool: no
bash, Read, search, list, stat, web, write, or task. Do not probe `.private`.
CHILD_AGENT_POLICY: forbidden
MODEL_POLICY: DeepSeek reasoning default; Agnes only after explicit DeepSeek
usage/quota/rate-limit evidence.
FINDING_SEVERITY: Blocker | Important | Nitpick

EXACT_GOALS:
- V6R-MINE-01: Real private packages are passively quarantined, rendered,
  page-inventoried, deduplicated, classified, and a rights-bound 300–500-page
  core is certified.
- GOAL-44-01: Every acquired package has terminal passive quarantine and
  structural inspection; every accepted editable package renders every slide
  into hash-bound normalized evidence.
- GOAL-44-02: Every candidate page receives exactly one full-coverage rendered
  pixel disposition: complete layout, named support/specialty pool, or excluded
  with Blocker/Important reason. Mixed-pool certification is forbidden.
- GOAL-44-03: Cross-package and cross-pool exact/near duplicates have one
  deterministic canonical and aliases; every certified page has provenance,
  private-use rights, structure, render, role/pool, and visual fingerprint.
- GOAL-44-04: Final usable core contains 300–500 pages or exhausts every valid
  candidate with an explicit quality shortfall; full-coverage contact sheets
  and fresh independent visual review have no unresolved Blocker or Important.

FROZEN_EVIDENCE_PACKET:

- Phase 43 produced 377 content-hash-unique validated package artifacts.
- Passive intelligence records all 377: 356 ACCEPTED/render PASS packages with
  620 rendered slides, 17 QUARANTINED/not rendered, and four REJECTED/not
  rendered. Unsafe packages never reach certification.
- OOXML inspection binds slide count/size, masters, layouts, themes, media,
  charts, diagrams, shapes, text, tables, fonts, structural SHA-256, and
  editability. XML member limits and DTD/entity rejection are fail closed.
- The preliminary q0.75 page order contains 312 pages. A full-coverage
  independent rendered-pixel review partitions exactly 136 keep, 103 reroute,
  73 deny. The partition is bound to page count plus ordered page-ID SHA-256.
- The complete half-open q0.65–0.75 supplement contains 79 pages. A first Agnes
  report was rejected because it misread contact-sheet labels and failed exact
  coverage. A second independent local pixel context partitions exactly 32
  keep, 42 reroute, five deny; its ordered page-ID SHA-256 is independently
  bound.
- A first final merged review inspected 16/16 sheets and returned NO_GO with
  three Important findings: one same-package visible duplicate, one broken
  THANK/S line wrap, and one non-generic supplier mark. All three were added as
  explicit deny entries. A new same-package near-duplicate rule uses a tighter
  deterministic threshold and has a focused regression test.
- A second fresh 310-page review found five supplier/contact identity Blockers,
  seven crop/wrap/contrast Important failures, and 37 branded/IP examples that
  must never materialize directly. A digest-bound final override registry
  denies the 12 defective/identity pages and routes all 37 examples into
  `reference-only/*`.
- Final certified-core v2 is PASS: all 391 candidates at or above the 0.65
  quality floor were dispositioned; 288 canonical pages remain, with an
  explicit 12-page quality shortfall instead of low-quality backfill. The
  pool contains 129 direct-use pages, 159 isolated reference-only pages,
  103 denied pages, zero current alias, zero current exact duplicate,
  and zero current near duplicate.
- Every 288 canonical page has `certified-private`, rights scope
  `private-user-authorized`, redistribution false, package/slide/category
  provenance, structurally editable evidence, render PASS, role, pool, SHA-256,
  and deterministic visual fingerprint.
- Every one of 159 reference-only pages has `auto_materialize=false`, `direct_use=false`,
  and `requires_content_replacement=true`.
- Final full-coverage evidence is 15 contact sheets with 288 source IDs and
  288 covered IDs exactly once. Direct-use evidence is seven sheets with 129
  source IDs and 129 covered IDs exactly once.
- FINAL_VISUAL_RESULT: Fresh independent context `phase44_direct129_blind`
  inspected 7/7 direct-use sheets and 129/129 pages. It returned GO with zero
  Blocker, zero Important, and five non-blocking Nitpicks. It found no
  unresolved supplier/brand/contact/QR leakage, completed-case/poster
  misrouting, serious word break, collision, clipping, low contrast,
  duplicate, or pool mismatch. Generic editable placeholders were correctly
  treated as materialization slots.
- Verification at the review point: Python compilation PASS; focused
  final override/disposition/dedupe/contact-sheet tests 6 passed, 51
  deselected; full acquisition/catalog file 57 passed; related
  acquisition/private-guard shard 38 passed, 21
  deselected; Phase 44 workflow execute gate PASS; git diff check PASS.
- Private credentials, source URLs, package bytes, rendered images, and state
  contents are absent from this packet and remain below the ignored private
  boundary. Only sanitized counts, digests in tracked disposition metadata,
  and independent findings are available to this audit.

OUTPUT_FORMAT:
1. Loaded skill IDs and provider/model/session/attempt chain.
2. Findings first, with Blocker/Important/Nitpick. Do not invent a finding
   because unsafe packages were correctly quarantined or serious pages were
   correctly denied.
3. Exactly one PASS|FAIL|NOT_RUN row for V6R-MINE-01 and GOAL-44-01..04 using
   the exact definitions above.
4. APPROVED or NOT_APPROVED.
5. DONE or DONE_WITH_CONCERNS.

After loading REQUIRED_SKILLS, reason only from this packet. If
FINAL_VISUAL_RESULT still says TO_BE_REPLACED, return NEEDS_CONTEXT without
calling a tool.
