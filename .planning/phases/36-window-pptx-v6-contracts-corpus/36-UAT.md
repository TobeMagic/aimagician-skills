# Phase 36: v6 Contracts and Realistic Corpus - UAT

**Updated:** 2026-07-29

## Scenarios

### UAT-01: Unresolved Real Brief

- **Starting state:** A request lacks audience decision, source rights, page
  budget, and acceptance rubric.
- **Action:** Validate the Draft/NeedsDiscussion ProjectBriefPack.
- **Expected visible result:** Structured missing-field questions and
  `formal_ready=false`.
- **Expected side effect:** No NarrativePlan or PPTX is created.
- **Result:** PASS
- **Evidence:** `test_draft_and_needs_discussion_cannot_enter_formal_generation`
  and `test_incomplete_pack_returns_structured_questions_and_cannot_lock`.

### UAT-02: Complete Locked Brief

- **Starting state:** A complete brief contains facts, sources, rights,
  audience, decision, timing, anatomy, prohibitions, and rubric.
- **Action:** Lock it and run the formal check.
- **Expected visible result:** `LOCKED` and `formal_ready=true` with a stable
  SHA-256 digest.
- **Expected side effect:** Any authoritative mutation invalidates the lock.
- **Result:** PASS
- **Evidence:** `test_complete_pack_locks_with_stable_digest_and_is_formal_ready`,
  `test_authoritative_change_invalidates_locked_digest`, and the corpus schema
  test.

### UAT-03: Private Credential Or Binary

- **Starting state:** A private path, cookie signature, key, or unapproved PPTX
  is presented to the staged-index guard.
- **Action:** Inspect the staged repository.
- **Expected visible result:** A fail-closed machine-readable finding without
  the matched value.
- **Expected side effect:** Unsafe content cannot pass the commit boundary.
- **Result:** PASS
- **Evidence:** Six private-guard tests and the clean staged smoke before
  commits `072e8a7`, `8c579cf`, and `95adf29`.

### UAT-04: Quality-First Skill Routing

- **Starting state:** A user requests a new real business deck or asks to
  release with only two reviewers.
- **Action:** Apply the Window-PPTX Skill and behavior eval contract.
- **Expected visible result:** The Skill requires a Locked ProjectBriefPack,
  uses the capable v6.0 author route, and returns `NOT_RUN` when three reviewers
  are unavailable.
- **Expected side effect:** It never restores the v5 weak-model default,
  accepts a human override, or invokes the invalid Python `--doctor` command.
- **Result:** PASS
- **Evidence:** Three Skill-contract tests, five v6 behavior scenarios, and
  `node dist/cli/index.js format-skills --check` with 23/23 checked.

## UAT Decision

**Status:** PASS
**Residual risk:** This UAT covers the Phase 36 user-visible intake and safety
contract. It does not score flagship visuals; v6 visual reference parity
remains a Phase 41 `NOT_RUN` gate until exact flagship packets exist.
