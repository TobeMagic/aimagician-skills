# HTML Universal Design Capability Upgrade Audit

## Scope And Provenance

This audit records the upgrade of `interface-design` into an HTML/CSS/JS-based design, prototype, implementation, and visual-quality system.

- Owned baseline: `skills/owned/interface-design/` before this upgrade.
- Reference repository: `https://github.com/Nutlope/hallmark`, audited at `aeb42fb354ff4efa36ab475773a082315a3af2ce`.
- Reference repository: `https://github.com/alchaincyf/huashu-design`, audited at `32cc58127f6074965e72530a2b593dac43572ec6`.
- Local mirrors: `skills/owned/interface-design/references/_external_repos/`, ignored by Git and excluded from installation.
- Runtime policy: source-neutral methods only; no source branding, installers, hooks, copied media, API credentials, or external update behavior.

## Baseline Analysis

The previous `interface-design` had useful but narrow guidance:

- domain fit for operational, marketing, and expressive products;
- familiar control selection and stable layout dimensions;
- baseline keyboard, focus, contrast, semantic HTML, and responsive screenshot checks;
- built-in routing across 58 brand `DESIGN.md` references;
- guardrails against nested cards, generic gradient decoration, and accidental design-system replacement.

Its 102-line entry did not provide enough scaffolding for a model with weak visual judgment:

| Gap | Effect |
|---|---|
| No final-artifact router | HTML presentations and native PowerPoint could be conflated. |
| No information-architecture or content model | Styling could begin before user flow and truthful content were settled. |
| No macrostructure and decision library | Page shape depended on model taste and often fell into repeated card grids. |
| No reusable visual-system procedure | Typography, palette, spacing, imagery, and motion could drift component by component. |
| No component state matrix | Loading, empty, error, selected, disabled, focus, and recovery behavior were easy to omit. |
| No app prototype, dashboard, data, or HTML presentation playbooks | Different visual products lacked domain-specific methods. |
| No direction divergence gate | A weak model could commit to the first generic composition. |
| No executable routing or quality data | Rules were prose-only and hard to test. |
| Limited visual critique | Code correctness could be mistaken for design quality. |

## External Analysis

### Hallmark

The audited system contributes a rigorous browser-page design grammar:

- preflight detection of existing typography, palette, spacing, motion, framework, and design docs;
- separate build, audit, redesign, and study verbs;
- macrostructure-first composition with diversification across consecutive outputs;
- 21 page structures and more than 50 component archetypes;
- tokenized color and typography, including perceptual color guidance;
- responsive floors, clickable-text fit, state discipline, and focus behavior;
- a large named anti-pattern and post-emit visual-quality catalog;
- project memory intended to prevent repeated palettes and page shapes.

The strongest transferable idea is not a fixed theme catalog. It is the sequence: inspect context, choose structure, lock a visual system, build, then run an explicit anti-template quality gate.

### Huashu Design

The audited system contributes a broader HTML-native design production workflow:

- user/design-context questions, assumptions, and multi-pass junior-designer support;
- multiple materially different visual directions before commitment;
- truthful placeholder and brand-asset protocols;
- app prototype structure and device/platform considerations;
- detailed CJK and mixed-script typography guidance;
- content, scene, style, motion, critique, and browser-verification methods;
- browser-native presentation architectures and per-frame validation;
- deterministic degradation advice for constrained runtimes;
- extensive export, animation, video, narration, and media tooling.

The most valuable transferable idea is to make design a gated system of content, direction, implementation, and visual evidence rather than a one-pass code generation task.

## Fusion Decisions

### Retained

- Existing product-domain fit and familiar-control rules.
- Stable dimensions, accessibility, responsive verification, and visual screenshot requirements.
- All 58 brand `DESIGN.md` references and the existing routing contract.
- Existing project system and local components as the first implementation choice.

### Strengthened

| Existing Capability | Upgrade |
|---|---|
| Intake | Added explicit final-artifact, user, workflow, content, truth, platform, and acceptance gates. |
| Brand routing | Existing references remain authoritative; verified asset extraction becomes the fallback for unlisted brands. |
| Layout | Added content-signal decision rules and 17 curated macrostructures covering marketing, editorial, operations, data, prototypes, diagrams, presentations, repository branding, posters, motion sequences, and creative-coding stages. |
| Components | Added 23 archetypes with anatomy/use guidance and required state sets, including repository wordmarks, terminal proof, capability ribbons, motion scenes, and media fallbacks. |
| Visual quality | Added semantic token contract, CJK typography, perceptual color, imagery rules, anti-template checks, and evidence-backed critique. |
| Responsive work | Made 320/375/414/768/desktop inspection explicit for general web work and required intentional transformation. |
| Verification | Added functional path, console/network, font/asset readiness, keyboard, state, motion, screenshot, and score-based closure gates. |

### Added

Eleven progressive capability modules:

1. `delivery-routing.md`
2. `context-and-direction.md`
3. `information-architecture.md`
4. `visual-system.md`
5. `components-and-interaction.md`
6. `prototypes-and-data.md`
7. `motion-and-html-presentations.md`
8. `implementation-and-verification.md`

Additional product-asset modules:

9. `brand-and-product-assets.md`
10. `repository-branding-and-marketing.md`
11. `creative-coding-and-motion-media.md`

Four executable data libraries:

- `assets/patterns/layout-patterns.json`
- `assets/patterns/component-patterns.json`
- `assets/patterns/decision-rules.json`
- `assets/patterns/quality-checks.json`

Eight durable templates:

- design brief;
- visual system;
- prototype plan;
- visual QA report;
- HTML-to-native-PowerPoint handoff.
- brand specification;
- repository visual brief;
- deterministic motion storyboard.

Reusable source and rendering assets:

- fixed-format repository hero scaffold;
- deterministic browser-time scaffold;
- Playwright frame capture and ffmpeg poster/MP4 renderer.

One dependency-free route advisor:

- `scripts/design-router.mjs`

It routes landing, dashboard, app prototype, component, audit, redesign, HTML presentation, README cover, poster, product demo, and creative-coding work; combines content signals with layout/component patterns; returns relevant quality gates; and enforces HTML, image, video, native PPTX, or hybrid ownership.

### Rejected Or Adapted

| Source Content | Decision | Reason |
|---|---|---|
| Full fixed theme catalog | Adapt to semantic visual-system rules | A universal owned skill should derive brand and domain fit, not force source themes. |
| All source macrostructures and component files | Curate into 17 layouts and 23 components | Keeps progressive loading practical while preserving decision coverage. |
| Hidden project memory or source-specific log | Replace with explicit brief/system/QA artifacts | Durable project-owned evidence is easier to inspect and resume. |
| Mandatory three drafts for every task | Apply only to open, high-visual briefs | Locked systems, small fixes, and explicit one-pass work should not incur needless friction. |
| HTML-to-PPTX as default PowerPoint delivery | Reject | Native PowerPoint has different editability, master, chart, note, and Office QA requirements. |
| Copied device frames, stage engines, media, and demo binaries | Reject | Original, source-neutral scaffolds retain the useful method without runtime licensing burden. |
| Voice, SFX, TTS, and vendor media pipelines | Reject from universal core | Audio and vendor-specific production remain specialized and must be explicitly licensed. |
| Deterministic browser-rendered product loops | Add in bounded form | README heroes and product showcases require a repeatable HTML/Canvas-to-poster/MP4 path with frame validation and no external service dependency. |
| Source-specific hooks, gate scripts, watermarks, installers, and promotion | Reject | They do not improve the professional design method and mutate or brand the runtime. |
| Framework-specific setup as a global rule | Adapt to local-framework-first | The owned skill must work across HTML, CSS, JavaScript, and existing frontend stacks. |

## Final Architecture

```text
user requirement
  -> final artifact owner: HTML | native PPTX | hybrid
  -> existing context and truthful content
  -> user flow, information architecture and state inventory
  -> macrostructure selected from content signals
  -> direction exploration when genuinely open
  -> semantic visual system
  -> component/state implementation
  -> responsive browser evidence
  -> critique, refinement and delivery
```

The main `SKILL.md` is a router and non-negotiable contract. Capability modules carry expert methods. JSON libraries make choices and checks inspectable. Templates externalize design memory. The route script turns deterministic rules into testable outputs.

## Capability Boundary

### `interface-design` Owns

- product, web, mobile, app, and SaaS prototypes implemented with HTML/CSS/JS;
- UI/UX, dashboards, design systems, component and interaction demos;
- landing, campaign, launch, brand-experience, and product pages;
- README covers, repository branding, posters, product showcases, and supplemental demo loops;
- SVG, Canvas, deterministic motion, and creative-coding visuals;
- interactive reports, charts, data visualization, and process diagrams;
- HTML slides, browser presentations, visual exploration, and presentation prototypes;
- study, audit, redesign, browser QA, accessibility, responsive and motion quality.

### PPT Skills Own

- final editable `.pptx` files;
- slide masters, native text/shapes/charts/tables/media, notes, and templates;
- PowerPoint/Office compatibility, rendering, overlap inspection, and native editability;
- Windows automation and add-in workflows when `window-pptx` is selected.

### Hybrid Rule

HTML may establish and validate a visual direction. `ppt-handoff.md` transfers narrative, tokens, assets, frame inventory, screenshots, and reconstruction constraints. The PPT owner then rebuilds and verifies the native deck. Ownership is sequential and explicit.

## Weak-Model Enhancement Strategy

The runtime now reduces reliance on invention:

1. route the artifact before choosing technology;
2. preserve existing product and brand context;
3. map real content and user states before styling;
4. select a macrostructure from explicit signals;
5. lock semantic tokens and component states;
6. use task-specific prototype, data, motion, or presentation methods;
7. run deterministic quality gates and browser screenshots;
8. require fixes or accepted tradeoffs for weak critique scores.

This does not guarantee taste from prose alone. It makes the design process observable, repeatable, and correctable, which is the practical route for weaker models to approach senior design-engineering output.

## Acceptance Matrix

| Scenario | Expected Route And Evidence |
|---|---|
| Landing page | Product-first signal, truthful proof, coherent visual system, responsive browser screenshots, anti-template critique. |
| Dashboard | Decision-first metrics, workbench or command center, table/chart semantics, full data state matrix, keyboard/mobile evidence. |
| App prototype | Fidelity contract, connected critical flow, state transitions, honest simulation, target-platform verification. |
| HTML presentation | Browser-native owner, narrative arc, varied frames, keyboard/full-screen behavior, per-frame QA. |
| Native PowerPoint | Immediate route to `pptx` or `window-pptx`; no HTML final artifact. |
| Hybrid presentation | HTML direction plus structured handoff, followed by separate native reconstruction and QA. |
| README cover | Repository truth pass, claim ledger, selected visual direction, editable source, static hero, downscaled QA, and README integration. |
| Product demo video | Storyboard, deterministic clock, poster fallback, encoded media, frame inspection, and codec/duration/size evidence. |

Automated architecture and route tests live in `tests/skills/expert-skill-architecture.test.ts`.
