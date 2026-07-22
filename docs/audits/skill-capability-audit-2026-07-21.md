# Skill Capability Audit And Integration Validation

Date: 2026-07-21

## 1. Executive Verdict

The owned Skill system now has three distinct layers:

1. **Trigger layer:** concise frontmatter descriptions recognize user intent without requiring the user to name a Skill.
2. **Progressive capability layer:** the main `SKILL.md` selects only the expert modules needed for the current stage.
3. **Evidence layer:** templates, deterministic routers, quality rules, behavior scenarios, tests, and real artifact validation make the method reusable.

The integration is no longer only a file merge. Repository branding, still and motion media, prototypes, UI, HTML presentations, engineering exploration, progressive discovery, design, delivery, debugging, review, and closure each have a callable route and acceptance evidence.

The audit does not claim that static prompts alone guarantee expert output from every model. Controlled weak-model A/B evaluation across many repositories remains a continuous evaluation task. The present result establishes the required architecture, trigger contracts, executable routing, scenario coverage, and one complete real-project validation.

## 2. Audit Basis

### Owned Skills

- `skills/owned/interface-design/`
- `skills/owned/github-readme-highstar/`
- `skills/owned/aimagician-superpower/`
- `skills/owned/pptx/`
- `skills/owned/window-pptx/`
- `skills/owned/webapp-testing/`

### External Method References

External repositories were audited as method sources, not installed or copied into runtime Skills:

| Reference | Audited commit | Primary contribution |
|---|---|---|
| `mattpocock/skills` | `9603c1cc8118d08bc1b3bf34cf714f62178dea3b` | Progressive engineering discovery, domain vocabulary, behavioral tests, vertical slices, prototypes, two-axis review, and context discipline |
| `Nutlope/hallmark` | `aeb42fb354ff4efa36ab475773a082315a3af2ce` | Macrostructure-first web design, visual-system decisions, anti-template critique, and browser quality gates |
| `alchaincyf/huashu-design` | `32cc58127f6074965e72530a2b593dac43572ec6` | Design-context intake, direction divergence, prototypes, CJK typography, HTML presentations, creative coding, motion, and deterministic degradation |

Runtime modules are source-neutral. Third-party identities, installers, hooks, credentials, copied media, and update behavior are excluded.

### Real Project

The visual workflow was validated against YapCLI in an isolated worktree. Product claims were grounded in `AGENTS.md`, `Main.java`, current README documentation, and implementation packages before a visual direction was selected.

## 3. Trigger System Validation

Skill selection is driven by the frontmatter description. The selected Skill then routes to companion Skills only when the artifact boundary requires it.

| User request | Primary trigger | Companion or handoff | Result |
|---|---|---|---|
| Design a GitHub README cover | `interface-design` | `github-readme-highstar` owns Markdown structure and integration | PASS |
| Create a product promotion video | `interface-design` | Image generation may provide a verified ingredient; it does not own composition | PASS |
| Create an app prototype | `interface-design` | `webapp-testing` supplies browser evidence | PASS |
| Modify code to add a feature | `aimagician-superpower` | Domain Skills and CLI agents are selected after scope and exploration | PASS |
| Create a commercial report PPT | `pptx` or `window-pptx` | `interface-design` may explore an HTML direction only when explicitly requested | PASS |

Important boundary rules:

- README document structure and visual production are cooperating capabilities, not duplicate owners.
- A request for a cover is not reduced to one-shot image generation. It requires product understanding, audience, direction, proof, source, rendering, QA, and README integration.
- A request for a native deck, `.pptx`, PowerPoint, commercial report, or editable Office delivery routes to the PPT owner.
- HTML slides and web presentations remain browser-native `interface-design` work.

Automated trigger-contract checks live in `tests/skills/expert-skill-architecture.test.ts`.

## 4. Frontend Capability Audit

### Huashu-Derived Capabilities Now Integrated

- Design-context intake with explicit user, artifact, platform, truth, and acceptance questions.
- Exactly three materially different, real visual previews before open-direction commitment, with only recorded narrow bypasses.
- Information architecture, message priority, storytelling sequence, and state inventory before styling.
- Product, web, app, interaction, visual, and integrated-demo prototype modes.
- UI component anatomy, interaction states, user flow, accessibility, and responsive evidence.
- CJK and mixed-script typography rules.
- HTML slides, web presentations, keyboard navigation, and per-frame browser QA.
- Variants, live tweak controls, comparison canvases, and reusable iOS, Android, macOS, and browser frames.
- SVG, Canvas, WebGL, Three.js, Stage/Sprite, timed DOM composition, and creative-coding selection rules.
- Single- and multi-file HTML decks, speaker notes, fullscreen/print, vector PDF, and explicit HTML-first PPTX conversion.
- Storyboards, deterministic time, poster fallback, MP4 and two-pass GIF encoding, frame/loop/black checks, and media contracts.
- Narration-led continuous motion, provider-neutral TTS adapters, captions, music/effect cues, sidechain ducking, loudness, and A/V verification.
- Honest placeholders, claim-to-evidence ledgers, asset provenance, and deterministic degradation.
- Visual critique against hierarchy, density, alignment, typography, color, specificity, and template repetition.

### Capabilities That Were Missing Before This Audit

- Explicit trigger coverage for README covers, repository banners, posters, marketing visuals, product showcases, and demo videos.
- A repository-branding workflow grounded in current code and product truth.
- Reusable repository visual brief, brand specification, and motion storyboard.
- Repository hero, campaign poster, demo sequence, and creative-coding layout routes.
- Project wordmark, terminal proof, capability ribbon, motion scene, and media fallback components.
- Executable deterministic still/video rendering with browser readiness and time contracts.
- Exact-size and downscaled media QA, static fallback, frame integrity, codec, duration, and file-size gates.
- Explicit README/PPT artifact ownership and handoff boundaries.

### Runtime Noise Not Copied

- Vendor-specific TTS endpoints, credentials, personal media indexes, or upload APIs. Their reusable adapter and production methods are integrated without provider lock-in.
- Unlicensed media, remote font dependencies, tracking, watermarks, and fabricated product footage.
- HTML-to-PPTX as the default for ordinary PowerPoint requests. Explicit HTML-first requests are supported through a mandatory editable/fidelity decision.
- Third-party setup scripts, installers, hooks, binaries, and update behavior.
- Source-specific branding or unchanged copies of external templates.

These exclusions are non-capability boundaries. Licensed audio, provider-neutral narration, device/deck/motion scaffolds, GIF export, and HTML-first PPTX are now callable owned capabilities.

### Frontend Skill Capability Matrix

| Capability | Covered | Source in owned architecture | Further enhancement |
|---|---|---|---|
| README Cover | Yes | `repository-branding-and-marketing.md`, `brand-and-product-assets.md`, README collaboration workflow | No blocking gap; continue real-repository regressions |
| Poster Design | Yes | `campaign-poster`, brand brief, still-rendering QA | No blocking gap |
| Video Hero | Yes | deterministic renderer/verifier, motion storyboard, director notes, narration/audio route | No blocking gap |
| Prototype | Yes | `prototypes-and-data.md`, prototype plan, app-shell route | Expand scenario corpus over time |
| UI Design | Yes | information architecture, visual system, components/interactions, quality rules | Expand framework-specific examples only when useful |
| HTML Presentation | Yes | deck starters, notes, fullscreen/print, PDF and explicit editable/fidelity PPTX | Ordinary native PPT remains separate |
| Motion Design | Yes | deterministic clock, Stage/Sprite, scene recipes, MP4/GIF, audio/narration and media gates | No blocking gap |
| Creative Coding | Yes | SVG/Canvas/WebGL/Three.js rules, Stage/Sprite and React motion starters | Add domain-specific starters only after repeated demand |

### Frontend Workflow After Integration

```text
artifact and product truth
  -> audience, message, proof, and acceptance
  -> information architecture or storyboard
  -> multiple visual directions
  -> selected visual system
  -> HTML/CSS/JS implementation
  -> interaction or deterministic media rendering
  -> browser, responsive, accessibility, and frame QA
  -> README integration or final artifact handoff
```

## 5. Engineering Capability Audit

### Capabilities Already Retained

- Mandatory start/resume recovery from the controlling Skill, planning state, project docs, wiki, and git context.
- Objective, boundary, assumptions, constraints, non-goals, risk, rollback, and acceptance discussion.
- Local and external research followed by a second boundary and assumption discussion.
- Risk-scaled specification, ambiguity lock, requirement IDs, plan acceptance, and evidence traceability.
- Atomic execution, multi-agent roles, independent plan review, specification review, quality review, verification, UAT, audit, handoff, and completion.
- Root-cause debugging, condition-based waiting, state-pollution isolation, worktree and PR routing, and domain-specific gates.

### Capabilities Added Or Strengthened

- Objective-sized repository maps with entry points, ownership, contracts, dependencies, data/control flow, state, side effects, and blast radius.
- Progressive discovery maps that separate destination, known decisions, current frontier, fog, and the smallest distinguishing probe.
- Durable domain vocabulary shared across requirements, implementation, tests, and review.
- At least two materially different designs when real tradeoffs exist.
- Public practical test seams, intended red failures, and end-to-end tracer slices.
- Rejection of tautological tests, mock-return replay tests, private-only tests, and disconnected horizontal implementation.
- Expand-contract migration for wide refactors and bounded, disposable prototypes for material uncertainty.
- Ranked hypotheses and distinguishing instrumentation for debugging.
- Fixed review points plus independent specification-compliance and engineering-standards passes.
- Explicit correctness, concurrency, security, data, compatibility, maintainability, extensibility, performance, operability, and diff-hygiene review axes.
- Clean implementation contexts, durable handoffs, and protection against compaction that loses causal evidence mid-slice.

### Engineering Skill Capability Matrix

| Capability | Covered | Source in owned architecture | Further enhancement |
|---|---|---|---|
| Repo Analysis | Yes | exploration module, context map, progressive discovery, CLI-agent delegation | Continue large-repository scenario evaluation |
| Planning | Yes | specification workflow, design record, vertical slices, plan review | No blocking gap |
| Coding | Yes | feature playbook, tracer slices, task contexts, domain gates | Add language-specific modules only when repeated need proves value |
| Debug | Yes | red loop, minimization, ranked hypotheses, probes, regression and prevention | Expand flaky/distributed examples over time |
| Review | Yes | fixed review point and two independent review axes | Continue security/data specialist evals |
| Refactor | Yes | characterization, caller map, expand-contract, compatibility and removal proof | No blocking gap |
| Testing | Yes | highest observable seam, red-green-refactor, breadth by blast radius, UAT | Controlled weak-model A/B benchmark remains |

### Remaining Engineering Evaluation Gap

The repository contains behavior scenarios for project analysis, cross-layer features, root-cause bug repair, wide refactoring, progressive discovery, and bounded prototypes. Deterministic tests verify that every route selects the required stages, artifacts, seams, and review axes. A future evaluation package should repeatedly run the same tasks with and without the Skill against several weaker models and score requirement coverage, unnecessary edits, test quality, regressions, and review findings. That empirical benchmark is necessary before making a universal quantitative "expert-level" claim.

## 6. YapCLI Real-Project Validation

### Product Understanding

The visual design uses current product facts:

- Product: YapCLI.
- Position: Terminal-First Java Agent IDE.
- Current displayed version: `v16.1.0`.
- Product surface: terminal launcher, command entry, plan/review/verify flow, status dock.
- Relevant capabilities: ReAct, Plan, MCP, Browser, Image, Tools, Memory, RAG, HITL review, and Side-Git snapshots.
- Audience: developers evaluating an open-source terminal agent.

Demonstration traces are labeled as demonstrations and do not claim to be literal recordings.

### Direction Decision

Three directions were considered: Terminal Signal, Compiler Blueprint, and Agent Control Room. Terminal Signal was selected because it exposes the actual product surface and workflow proof instead of relying on generic AI imagery.

### Delivered Artifacts

| Artifact | Purpose |
|---|---|
| `docs/assets/readme-cover.webp` | Static README hero |
| `docs/assets/yapcli-launcher.webp` | Current launcher ready state |
| `docs/assets/yapcli-agent-flow.webp` | Intent-to-evidence workflow view |
| `docs/assets/yapcli-product-loop-poster.webp` | Video fallback poster |
| `docs/assets/yapcli-product-loop.mp4` | Eight-second deterministic product loop |
| `docs/assets/readme-visual/index.html` | Editable source for hero, launcher, and flow scenes |

### Validation Evidence

- Browser scenes tested at 1600x900, 800x450, and 390x219.
- Every scene remained inside the fitted frame at all three sizes.
- Browser console and page errors: zero.
- Canvas progress trace: nonblank pixel evidence present.
- MP4: 1600x900, 24 fps, 8 seconds, H.264 High, `yuv420p`, silent.
- Captured frames: 192 with distinct start, middle, poster, and final hashes.
- Black-frame detection: no black intervals.
- Static fallback and README-relative paths: present.
- GitHub README embeds static WebP assets and links the MP4 because README autoplay is not a reliable platform contract.

## 7. Implemented Changes

### Skill And Prompt Changes

- Expanded `interface-design` triggers and delivery ownership for still and motion product assets.
- Added repository branding, brand/product asset, and creative-coding/motion modules.
- Expanded `github-readme-highstar` triggers and established a shared product brief with clear artifact ownership.
- Added progressive discovery and prototype routing to `aimagician-superpower`.
- Strengthened engineering delivery and review prompts around observable seams and independent review axes.

### Templates And Components

- Added brand specification, repository visual brief, and motion storyboard templates.
- Added engineering prototype brief and progressive discovery map.
- Added repository hero, device/browser frame, comparison, deck, Stage/Sprite, React motion and narration scaffolds.
- Added direction, asset provenance, director notes, narration and audio-cue templates.
- Added repository wordmark, terminal proof, capability ribbon, tweak/device/narration components, motion scene, and media fallback patterns.
- Expanded the library to 22 layouts, 32 components, 23 decision rules, 36 quality checks and 40 visual direction families.

### Executable Workflow

- Added HTML, image, video, GIF, PDF, ordinary native PPTX, explicit HTML-first PPTX and hybrid routes to `design-router.mjs`.
- Added discovery and prototype routes to `engineering-route.mjs`.
- Added deterministic Playwright/ffmpeg poster, H.264 MP4 and two-pass GIF rendering plus frame/loop/black/media verification.
- Added multi-file and stage vector PDF exporters, dual-mode HTML-first PPTX, provider-neutral narration, and voice/music/effect mixing with ducking.
- Added behavior scenarios for repository covers, GIF heroes, posters, product video, editable/fidelity HTML-first PPTX, devices/variants, narration, creative coding, progressive discovery, and prototypes.
- Expanded architecture and trigger tests.

## 8. Verification Record

- `npm run build`: PASS.
- `npm run typecheck`: PASS.
- All 21 TypeScript test files were run in isolated single-worker invocations: 105 tests PASS.
- `tests/skills/expert-skill-architecture.test.ts`: 10/10 PASS after final edits.
- `node dist/cli/index.js format-skills --check`: 23 owned Skills checked, no issues.
- Edited Skill JSON files: eight parsed successfully.
- Runtime source-identity scan: no third-party repository identity or URL in the merged runtime entry/modules.
- YapCLI browser and media checks: PASS as recorded in section 6.

The all-files Vitest process was also attempted, but the shared workspace already had an unrelated 24-worker Vitest job. Long aggregate processes were terminated externally, so every test file was rerun separately to obtain explicit exit codes without resource accumulation.

OpenCode completed the pre-implementation repository exploration with `opencode/deepseek-v4-flash-free`. A post-change independent review was attempted twice; both processes were terminated externally before a final review report. No OpenCode review conclusion is claimed or treated as acceptance evidence.

## 9. Final Assessment

The owned system now supports automatic intent routing and progressive expert guidance without requiring users to name Skills. The main remaining work is continuous evaluation, not another broad merge: collect repeated weak-model outcomes, score them against the existing scenario contracts, and add a rule, template, or module only when observed failures reveal a reusable gap.
