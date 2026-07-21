# Engineering Capability Upgrade Audit

## Scope And Provenance

This audit records the engineering-method integration completed for `aimagician-superpower`. Runtime skill files remain source-neutral; source names and repository-specific decisions live only in this document.

- Owned baseline: `skills/owned/aimagician-superpower/` before this upgrade.
- Reference repository: `https://github.com/mattpocock/skills`.
- Audited reference commit: `9603c1cc8118d08bc1b3bf34cf714f62178dea3b` (2026-07-16 commit date in the local mirror).
- Local audit mirror: `skills/owned/aimagician-superpower/references/_external_repos/mattpocock_skills/`.
- Mirror policy: complete local reference, ignored by Git, never installed as runtime content.

## Baseline Analysis

### Existing Strengths

Before this upgrade, `aimagician-superpower` already provided:

- mandatory start/resume recovery from planning, project docs, wiki, and git state;
- risk-scaled lightweight versus formal specification routing;
- target and boundary discussion, research, second discussion, lock, plan, execution, verification, audit, handoff, and completion;
- requirement ambiguity scoring and requirement-to-plan-to-evidence traceability;
- provider-neutral delegated roles with specification review before quality review;
- multi-agent, parallel worktree, debugging, condition-based waiting, state-pollution isolation, UAT, and domain gates;
- a dependency-free workflow runtime plus planning templates and behavior scenarios.

These are retained as the control plane. They are stronger than a task-local coding recipe because they preserve state, decisions, evidence, and completion across long milestones.

### Baseline Gaps

The control plane named engineering stages but left too much expert judgment implicit:

| Gap | Consequence For A Weaker Model |
|---|---|
| No explicit repository exploration artifact | It could list files without explaining ownership, flows, contracts, or blast radius. |
| Limited architecture vocabulary | It lacked repeatable tests for module depth, interface size, locality, leverage, and dependency direction. |
| No design-twice contract | It could settle on the first plausible implementation and invent architecture during coding. |
| Generic test-first guidance | It did not sufficiently distinguish behavioral seams from private implementation tests, tautologies, or horizontal-only tests. |
| No task-type delivery playbooks | Feature, refactor, performance, architecture, prototype, and merge-conflict work relied on model experience. |
| Review was procedural but not technically exhaustive | Correctness, concurrency, security, operability, compatibility, and diff hygiene were not one explicit reusable axis set. |
| Debugging used one hypothesis too early | Complex failures benefited from ranked alternatives and deliberate distinguishing instrumentation. |
| Plans did not require tracer slices or expand-contract | A weak model could plan by layers or hide a flag-day migration inside one task. |

The baseline therefore had low dependence on model memory for workflow order, but medium-to-high dependence on model experience for codebase design, test placement, migration shape, and technical review depth.

## Reference Capability Inventory

The stable engineering and productivity skills in the audited repository contributed these reusable methods:

| Reference Area | Reusable Method |
|---|---|
| `ask-matt`, `wayfinder` | Route by current context, task frontier, and remaining uncertainty instead of treating every request alike. |
| `grill-with-docs`, `grilling` | Inspect facts before asking; ask one decision-changing question with a recommended default. |
| `domain-modeling` | Maintain a shared glossary, sharpen fuzzy terms with concrete scenarios, and record durable architecture decisions sparingly. |
| `to-spec` | Define behavior, boundaries, acceptance, and test seams before implementation. |
| `to-tickets` | Create vertical tracer slices with explicit blockers; use staged migration for broad refactors. |
| `implement` | Separate implementation context from fresh specification and quality review contexts. |
| `tdd` | Put tests on observable seams; reject implementation-coupled, tautological, and disconnected horizontal tests. |
| `code-review` | Review specification compliance and engineering standards as two distinct axes. |
| `diagnosing-bugs` | Build the feedback loop first, minimize the reproduction, rank hypotheses, instrument deliberately, clean up, and capture prevention learning. |
| `codebase-design` | Reason with module, interface, seam, depth, leverage, locality, and dependency relationships; design for testability. |
| `improve-codebase-architecture` | Make scoped, evidence-backed architecture recommendations and retain no-change/YAGNI as a valid decision. |
| `prototype` | Separate logic and UI uncertainty, make the experiment runnable, time/evidence bound it, and capture a promote/revise/discard verdict. |
| `research` | Delegate bounded evidence gathering and prefer primary sources for unstable external facts. |
| `resolving-merge-conflicts` | Resolve by behavioral intent and verify both sides rather than selecting text mechanically. |
| `handoff` | Preserve exact continuation context, redact sensitive values, and name useful follow-on capabilities without duplicating discovery. |

Deprecated, in-progress, personal, article-writing, setup, migration, hook, and repository-specific skills were inventoried but not promoted into runtime.

## Fusion Decisions

### Retained

- The complete ten-stage owned workflow and mandatory resume gate.
- Formal SDD, ambiguity lock, milestone state, traceability, UAT, audit, and completion evidence.
- Existing delegated role separation, parallel execution, waiting, pollution, and domain gates.
- Source-neutral runtime language and owned-skill-first routing.

### Strengthened

| Existing Capability | Upgrade |
|---|---|
| Research and discovery | Added objective-sized context maps, representative happy/failure flow tracing, caller/consumer inspection, explicit blast radius, and a stop condition. |
| Planning | Added vertical tracer slices, blocking edges, observable test seams, and explicit expand-contract phases. |
| Debugging | Upgraded to a six-stage loop with red feedback loop, minimization, three-to-five ranked hypotheses, distinguishing instrumentation, cleanup, and prevention note. |
| Execution | Added task-specific playbooks and end-to-end slice discipline. |
| Review | Added fixed review point, specification-first and quality-second passes, technical axis checklist, severity and remediation contract. |
| Handoff | Added suggested companion skills and durable engineering artifacts. |

### Added

Four progressive capability modules:

- `references/capabilities/engineering-exploration.md`
- `references/capabilities/engineering-design.md`
- `references/capabilities/engineering-delivery.md`
- `references/capabilities/engineering-review.md`

Four reusable artifacts:

- `assets/templates/engineering-context-map.md`
- `assets/templates/engineering-design-record.md`
- `assets/templates/engineering-change-brief.md`
- `assets/templates/engineering-review.md`

One deterministic advisor:

- `scripts/engineering-route.mjs`

It routes `analysis`, `feature`, `bug`, `refactor`, `performance`, and `architecture` work to the minimum stages, artifacts, checks, and independent review depth without editing a project.

Four acceptance scenarios were added for codebase analysis, cross-layer feature delivery, root-cause bug repair, and wide compatible refactoring.

### Rejected Or Replaced

| Content | Decision | Reason |
|---|---|---|
| Setup, plugin, hook, and pre-commit installers | Reject | Environment mutation is not professional task guidance and is already owned by Skillbird/project tooling. |
| Personal voice and source-specific router identity | Reject | Runtime must remain portable and source-neutral. |
| Skill-writing methodology | Route to `skill-creator` | Avoid duplicate ownership. |
| Article, vault, exercise, and unrelated productivity workflows | Reject | Outside engineering delivery scope. |
| Deprecated and in-progress experiments | Audit only | Unstable behavior is not promoted into the default runtime. |
| A second independent milestone framework | Replace with existing workflow state | Duplicate lifecycle state would conflict with the owned control plane. |
| Blind copying of prompts or source file structure | Reject | Methods were normalized into the existing capability architecture. |

## Resulting Architecture

```text
request / resumed work
  -> target, boundary, specification and discussion
  -> objective-sized engineering context map
  -> domain model, invariants, interfaces, test seams and alternatives
  -> reviewed vertical-slice change brief
  -> task-specific delivery playbook
  -> specification review
  -> engineering quality review
  -> verification, UAT, audit, handoff and closure
```

This creates a layered system rather than one oversized prompt. The main `SKILL.md` routes the stage; capability modules hold expert decision procedures; templates externalize context; scripts make task routing deterministic; evals test expected and forbidden behavior.

## Why The Fusion Is Stronger

The previous owned workflow controlled lifecycle and evidence but assumed the model knew how a senior engineer explores, designs, slices, tests, migrates, and reviews. The integrated skill now encodes those decisions explicitly while retaining the stronger milestone, resume, ambiguity, orchestration, verification, and completion system.

The combination is additive:

- lifecycle rigor now contains concrete engineering technique;
- engineering technique now inherits durable state, risk scaling, independent review, traceability, and completion proof;
- a weak model can select a task route and fill structured artifacts instead of inventing a process;
- a strong model can progressively load only the modules that reduce uncertainty.

## Acceptance Matrix

| Engineering Scenario | Required Evidence |
|---|---|
| Project analysis | Representative flow, ownership, contracts, dependency/data/control map, blast radius, facts versus inference. |
| Feature development | Behavior contract, two designs when meaningful, test seams, tracer slice, boundary states, integration proof. |
| Bug repair | Red loop, minimized reproduction, ranked hypotheses, distinguishing probe, root-cause fix, regression, cleanup. |
| Refactor | Characterization baseline, caller map, target design, expand-contract batches, old-path removal proof. |
| Performance | Equivalent baseline and benchmark, proven bottleneck, correctness under load, regression signal. |
| Architecture | Domain model, no-change plus two designs, reversible migration, compatibility, observability, rollback. |

Automated checks live in `tests/skills/expert-skill-architecture.test.ts`; complete command evidence is recorded in the implementation summary and commit history.
