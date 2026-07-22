# Source-File Group Capability Parity Audit

**Audit date:** 2026-07-22
**Reference snapshot:** `alchaincyf/huashu-design@32cc58127f6074965e72530a2b593dac43572ec6` (HEAD of master, commit `32cc581`)
**Owned destination:** `skills/owned/interface-design/`
**Companion skills audited:** `skills/owned/github-readme-highstar/`, `skills/owned/cli-agent-orchestrator/`
**Test scope:** `tests/skills/`
**Design docs scope:** `docs/design/`, `docs/audits/`, `README.md`

**Resolution status:** This is the independent OpenCode audit produced with `agnes/agnes-2.0-flash`. It inspected a moving worktree, so its initial gap list is preserved as review evidence but is not the final state. The post-audit resolution section at the end is authoritative.

---

## Executive Verdict

The owned `interface-design` skill contains the reusable production methods from the huashu-design reference snapshot as source-neutral, progressively loaded capabilities. It does not install or execute the source repository. Runtime files contain no source author identity, promotion, watermark, installer, update hook, personal asset index, bundled third-party media, provider credential, or provider-specific TTS implementation.

**What is fully integrated (executable, tested, or structurally verified):**
- All 15 capability modules with progressive loading contracts
- All 14 executable scripts covering routing, rendering, verification, PDF/PPTX, narration, audio, semantic review, licensed assets, thumbnails and project-owned render adapters
- All 9 pattern JSON files (22 layouts, 32 components, 23 decision rules, 43 quality checks, 40 visual directions, 8 output contracts, 6 taste anchors, 3 motion recipes, and 9 anti-template rules)
- All 15 templates covering briefs, manifests, cue sheets, and handoff contracts
- All 15 starter scaffolds, including persisted tweaks, publication grammar, gallery geometry, and optional deterministic GSAP adaptation
- 16 evaluation scenarios with expected/forbidden behavior contracts
- Brand DESIGN.md routing with 57 brand references

**Initial findings from the moving-worktree snapshot (resolved or adjudicated below):**

| # | Gap | Severity | Description |
|---|-----|----------|-------------|
| 1 | `compile-narration-timeline.mjs` referenced in `audio-and-narration.md` step 2 but not listed in SKILL.md runtime assistance block | Medium | The narration workflow describes running this script twice (manifest generation + timeline compilation), yet the SKILL.md runtime section only shows `render-narration-tts.mjs`. The compile script exists and is executable but has no documented trigger path in the SKILL.md `Runtime Assistance` code block. |
| 2 | `fetch-wikimedia-assets.mjs` referenced in `brand-and-product-assets.md` but not shown in SKILL.md runtime assistance | Low-Medium | The brand capability module explicitly routes to this script for public-domain asset discovery, but the SKILL.md runtime block omits it. The script is callable via `WIKIMEDIA_USER_AGENT=<id> node scripts/fetch-wikimedia-assets.mjs` per the SKILL.md line 203, so this is a documentation gap rather than a capability gap. |
| 3 | `render-deck-thumbnails.mjs` referenced in `html-first-presentations.md` but not shown in SKILL.md runtime assistance | Low | Same pattern as #2. The script exists and works; SKILL.md line 204 documents it externally. |
| 4 | `narration-script.md` template referenced in `audio-and-narration.md` step 1 | Low | Template exists at `assets/templates/narration-script.md` (11 lines) but is only minimally templated -- contains two example scenes. Could benefit from fuller documentation of the `[[cue:id]]` marker format and `## scene-id` heading convention. |
| 5 | `prepare-motion-review.mjs` semantic review prompt generation | Low | The script generates a hardcoded review prompt markdown. It cannot be customized per-project without editing the script. The reference repo's `ai-video-review.py` had a `--model` parameter for selecting the vision model. The owned version hardcodes the prompt text. This is a minor flexibility gap, not a missing capability. |
| 6 | No dedicated `tweaks-system` React component in starters | Low | The reference repo's `tweaks-system.md` describes a full `useTakes` hook and `TweakPanel` React component with localStorage persistence, color pickers, font sliders, density selects, dark mode toggle. The owned skill's `design-comparison.jsx` provides comparison canvas but lacks the live tweak panel with persisted state. The capability is described in `context-and-direction.md` and `visual-system.md` but has no starter implementation. |
| 7 | No multi-perspective parallel subagent execution pattern | Low | The reference repo's `multi-perspective-parallel-case-study.md` describes spawning 6 parallel subagents with different artist DNAs. The owned skill has no equivalent orchestration pattern for parallel direction exploration beyond the three-direction gate. |
| 8 | `gsap-recipes.md` translation layer absent | Low | The reference repo provides a complete GSAP timeline mapping (easing functions, 5-segment narrative skeleton, seek safety rules, old-demo adapter). The owned skill's `creative-coding-and-motion-media.md` describes the deterministic time contract but has no GSAP-specific adapter. This is acceptable since the owned skill targets vanilla JS/React, but it means GSAP-based projects have no pre-mapped easing table. |
| 9 | No `apple-gallery-showcase.css` or gallery-wall animation starter | Low | The reference repo's `apple-gallery-showcase.md` contains copyable CSS for floating cards, 3D tilted galleries, corner convergence, ripple expansion, sinusoidal pan. These are reusable patterns with exact parameters. The owned skill has no equivalent CSS starter. |
| 10 | `hyperframes-backend.md` adapter contract not formalized | Low | The reference repo documents HyperFrames (HeyGen's HTML-to-video framework) as an advanced render backend. The owned skill has `render-with-adapter.mjs` and `render-manifest.json` as the generic adapter contract, which is correct and source-neutral. However, there is no explicit "when to use local vs adapter" decision table like the reference's selection boundary table. |
| 11 | No `scene-templates.md` output-type scene catalog | Low | The reference repo catalogs 8 scene types (WeChat cover, article illustration, infographic, PPT/Keynote, PDF whitepaper, landing page, App UI, Xiaohongshu image) with dimensions, key elements, recommended styles, and ready-to-use prompts. The owned skill's layout patterns cover some of these but lack the output-type-specific prompt templates. |
| 12 | No `design-styles.md` style DNA catalog in machine-readable form | Low | The reference repo has 40 HTML-native design styles (20 web + 20 PPT) each with visual DNA, HTML implementation assessment, font stack, and temperature rating. The owned skill has 40 visual direction families in `visual-direction-patterns.json` but without the per-style HTML implementation assessment scores or font stack recommendations. |
| 13 | `critique-guide.md` 5-dimension scoring rubric partially integrated | Low | The reference repo defines a structured critique with one-vote veto (Concept <= 5 caps total at 6.0), scene-specific weighting tables, and output template. The owned skill's `quality-checks.json` has severity levels but no weighted scoring rubric or one-vote veto logic. The `visual-qa.md` template records scores 1-5 but doesn't implement the weighted calculation. |
| 14 | `content-guidelines.md` anti-slop blacklists partially integrated | Low | The reference repo has detailed AI slop blacklists (visual traps, font traps, color traps, layout traps), CSS神器 list, and "when you hesitate" decision tables. The owned skill's `quality-checks.json` has some anti-template checks but lacks the structured blacklist data. |
| 15 | `react-setup.md` pinned CDN versions not preserved in starters | Low | The reference repo pins exact React 18.3.1, ReactDOM 18.3.1, Babel 7.29.0 CDN URLs with integrity hashes. The owned skill's `react-motion-stage.jsx` starter uses React but does not include the pinned CDN setup with integrity verification. Projects using the starter would need to add their own CDN configuration. |
| 16 | `launch-film-director-notes.md` 5-part structure not enforced by template | Low | The reference repo specifies a rigorous director's notes structure (Part I-V, ~10,000-15,000 words). The owned skill's `director-notes.md` template is 34 lines and covers the 5-beat narrative arc but does not enforce the full Part I-V structure with word count guidance. |
| 17 | No `animation-best-practices.md` scene recipes as reusable starters | Low | The reference repo provides Scene Recipes A/B/C with specific timing/easing/SFX density/BGM specs. The owned skill's `motion-storyboard.md` template captures scene structure but lacks the pre-built recipe templates with exact timing budgets. |
| 18 | `animation-pitfalls.md` 22-item checklist not in quality-checks.json | Low | The reference repo documents 21 specific pitfalls with root causes and fixes. The owned skill's `quality-checks.json` has 38 checks but they are higher-level. The pitfall-specific checks (e.g., "CSS transition non-determinism in seek rendering", "proxy tween first-frame gap") are not individually enumerated. |
| 19 | `typography.md` CJK mixed-script rules not in visual-system.md | Partial | The owned `visual-system.md` mentions CJK handling rules but the reference repo's `typography.md` has much more detail: open-source Chinese font map, CJK-Western fallback chain order, x-height compensation, baseline alignment, tabular nums, no-italic rule with CSS alternatives, punctuation norms (brackets, hanging punctuation, consecutive punctuation compression), letter-spacing intervals, unicode-range slicing strategy. |
| 20 | `video-export.md` user follow-up commands (size, sharpness, portrait, watermark, transparent background, lossless) not documented | Low | The reference repo has a dedicated section answering common post-render follow-up requests. The owned skill's `creative-coding-and-motion-media.md` covers the main pipeline but lacks the FAQ-style follow-up command reference. |
| 21 | `slide-decks.md` publication grammar template (masthead, kicker, H1, subtitle, footer) not in deck starters | Low | The reference repo defines a "moxt-tested" publication grammar with 9 visual protagonist rotations. The owned skill's deck starters work but don't include this publication grammar pattern. |
| 22 | `app-prototype.md` taste anchor table (font pairings, color strategy, information density, detail signature) not in prototypes-and-data.md | Low | The reference repo has a structured taste anchor table with specific recommendations per product type. The owned skill describes fidelity levels but lacks the taste anchor catalog. |
| 23 | `audio-design-rules.md` golden ratios and dual-track system not in audio-cues.json | Low | The reference repo defines specific volume ratios (BGM 0.40-0.50, SFX 1.00, -6 to -8dB difference), frequency isolation ffmpeg templates, and SFX cue density tiers. The owned `audio-cues.json` template has ducking config but no golden ratio defaults or density tier presets. |
| 24 | `brand-asset-protocol.md` "5-10-2-8" quality threshold not in brand-and-product-assets.md | Low | The reference repo defines a specific search protocol (search 5 channels, find 10 candidates, select 2 good ones, each scoring 8/10+). The owned `brand-and-product-assets.md` describes the acquisition priority order but not the specific threshold protocol. |
| 25 | No `SKILL.md` weak-runtime degradation ladder | Low | The reference repo's `SKILL.md` has a 5-level degradation ladder for non-Claude runtimes. The owned skill has `Weak-Model Decision Discipline` (8 rules) but no explicit runtime-tiered degradation plan. |
| 26 | `test-prompts.json` 6 test cases mapped to evals.json | Low | The reference repo has 6 test prompts validating workflow triggers. The owned skill has 16 eval scenarios. The 6 source prompts are absorbed and expanded, but the mapping is not documented. |

**Noise correctly excluded (not gaps):**
- Bundled BGM/SFX audio files (licensing provenance issue)
- `design-gate-hook.sh` (environment-mutating pre-render hook)
- `personal-asset-index.example.json` (personal identity data)
- `.env.example` with DouBan TTS credentials (vendor lock-in)
- `fetch_images.py` Python Wikimedia downloader (replaced by Node.js `fetch-wikimedia-assets.mjs`)
- `convert-formats.sh` format conversion utility (absorbed into `render-motion-media.mjs` multi-format support)
- `add-music.sh`, `mix-voiceover.sh`, `sfx-cues.sh`, `render-narration.sh`, `verify-video.sh` shell scripts (replaced by Node.js equivalents: `mix-motion-audio.mjs`, `render-narration-tts.mjs`, `verify-motion-media.mjs`)
- `tts-doubao.mjs` Doubao-specific TTS client (method integrated as provider-neutral adapter contract)
- `hyperframes-backend.md` HyperFrames-specific instructions (integrated as generic `render-with-adapter.mjs` contract)
- README files, package metadata, license (provenance outside installed runtime)
- Showcase HTML+PNG pairs (evidence assets, not reusable methods)
- `director-notes-samples/launch-film-30s-sample.md` (example, not method)

---

## Complete Source Capability Inventory

| Source file or group | Reusable capability | Owned destination | Integrated / Partial / Missing / Noise | Required change |
|---|---|---|---|---|
| `SKILL.md` (huashu) | Task routing, core principles, 10-step workflow, gate file protocol, exception handling, technical red lines, starter components, references routing, weak runtime degradation | `SKILL.md` (owned), `references/capabilities/` (all 13), `assets/patterns/` (all 5 JSONs) | **Integrated** (degradation ladder missing) | Add explicit runtime-tiered degradation plan to `SKILL.md` or `context-and-direction.md` |
| `workflow.md` | Junior designer 4-pass model, question-asking discipline, exploration matrix, uncertainty handling | `context-and-direction.md`, `SKILL.md` Canonical Design Loop | **Integrated** | None |
| `design-context.md` | Context priority list, import strategy by codebase size, Figma integration | `context-and-direction.md` | **Integrated** | None |
| `content-guidelines.md` | AI slop blacklists (visual/font/color/layout traps), scale norms, CSS神器, decision quick-reference | `quality-checks.json`, `visual-system.md`, `SKILL.md` Non-Negotiable Quality Rules | **Partial** | Add structured anti-slop blacklist data to `quality-checks.json` or a new `anti-slop-rules.json` |
| `critique-guide.md` | 5-dimension scoring, one-vote veto, scene-specific weighting, top-10 problems, output template | `quality-checks.json`, `visual-qa.md` | **Partial** | Add weighted scoring calculation and one-vote veto logic to `visual-qa.md` template |
| `design-styles.md` | 40 design styles with visual DNA, HTML implementation assessment, font stacks, temperature ratings, color derivation protocol | `visual-direction-patterns.json`, `visual-system.md` | **Partial** | Extend `visual-direction-patterns.json` entries with `html_implementation_score` and `font_stack` fields |
| `typography.md` | Modular type scale, flowing sizes, CJK rules, open-source fonts, mixed-script handling, unicode-range slicing | `visual-system.md`, `design-system.md` | **Partial** | Expand `visual-system.md` CJK section with fallback chain, x-height compensation, punctuation norms, and unicode-range strategy |
| `brand-asset-protocol.md` | 5-step hard flow, "5-10-2-8" quality threshold, logo download commands, brand-spec template, failure fallback table | `brand-and-product-assets.md`, `brand-spec.md`, `fetch-wikimedia-assets.mjs` | **Partial** | Add "5-10-2-8" threshold protocol to `brand-and-product-assets.md` |
| `react-setup.md` | Pinned CDN versions with integrity hashes, 3 unbreakable rules, error troubleshooting, large project splitting | `assets/starter/react-motion-stage.jsx` | **Missing** | Add pinned CDN setup block to `react-motion-stage.jsx` starter with integrity verification |
| `app-prototype.md` | Architecture selection, image sourcing, truth honesty test, taste anchor table, iOS frame usage rules | `prototypes-and-data.md`, `assets/starter/ios-frame.jsx` | **Partial** | Add taste anchor catalog to `prototypes-and-data.md`; add `useTakes`/`TweakPanel` starter |
| `ios_frame.jsx`, `android_frame.jsx`, `macos_window.jsx`, `browser_window.jsx`, `design_canvas.jsx` | Device frames, comparison grid | `assets/starter/` (same files, source-neutral), `design-comparison.jsx` | **Integrated** | None |
| `tweaks-system.md` | `useTakes` hook, `TweakPanel` component, localStorage persistence, linked tweaks | `context-and-direction.md`, `visual-system.md` | **Missing** | Add `tweak-panel.jsx` starter component with `useTakes` hook |
| `slide-decks.md` | Multi-file vs single-file architecture, publication grammar, speaker notes, export scripts, verification checklist | `motion-and-html-presentations.md`, `html-first-presentations.md`, `deck-index.html`, `deck-stage.js` | **Integrated** (publication grammar missing) | Add publication grammar pattern to `deck-index.html` or a new starter |
| `editable-pptx.md` | 4 hard constraints, merge text boxes, canvas size decision, error recovery | `html-first-presentations.md`, `html-to-pptx.cjs`, `export-html-deck-pptx.mjs` | **Integrated** | None |
| `animations.md` | Stage+Sprite API, easing table, animation patterns, rhythm guidelines | `creative-coding-and-motion-media.md`, `motion-stage.js`, `react-motion-stage.jsx` | **Integrated** | None |
| `animation-best-practices.md` | Narrative rhythm (5-segment), easing philosophy, motion language 8 principles, specific techniques, scene recipes A/B/C, self-check list | `creative-coding-and-motion-media.md`, `motion-storyboard.md`, `director-notes.md` | **Partial** | Add Scene Recipes A/B/C as reusable starter templates in `assets/starter/` |
| `animation-pitfalls.md` | 21 documented pitfalls with root causes and fixes, 22-item self-check | `creative-coding-and-motion-media.md`, `quality-checks.json` | **Partial** | Add pitfall-specific entries to `quality-checks.json` (CSS transition non-determinism, proxy tween first-frame, CORS for file://, warmup frame leakage) |
| `gsap-recipes.md` | GSAP timeline boilerplate, easing mapping table, 5-segment skeleton, seek safety rules, old demo adapter | `creative-coding-and-motion-media.md` | **Missing** | Add `gsap-adapter.mjs` starter with easing mapping and 5-segment skeleton |
| `hero-animation-case-study.md` | Gallery Ripple + Multi-Focus structure, ripple expansion algorithm, sinusoidal pan, 5 reusable patterns | `creative-coding-and-motion-media.md`, `narration-stage.jsx` | **Integrated** (as method, not copied branded examples) | None |
| `cinematic-patterns.md` | Dashboard+overlay dual-layer, scene-based structure, independent visual language per demo, BGM+SFX dual-track, debug tools | `creative-coding-and-motion-media.md`, `director-notes.md` | **Integrated** | None |
| `video-export.md` | Deterministic capture, MP4/GIF/WebM/ProRes, poster fallback, arbitrary fps, user follow-up commands | `render-motion-media.mjs`, `verify-motion-media.mjs`, `creative-coding-and-motion-media.md` | **Integrated** (follow-up FAQ missing) | Add post-render FAQ section to `creative-coding-and-motion-media.md` |
| `verification.md` | Playwright verification, screenshot best practices, error diagnosis, video verification | `implementation-and-verification.md`, `verify-motion-media.mjs`, `quality-checks.json` | **Integrated** | None |
| `ai-video-review.md` | Three-layer hybrid pipeline (ffmpeg objective + model segmented + model full-pass), severity-rated checklist | `prepare-motion-review.mjs`, `creative-coding-and-motion-media.md` | **Partial** | Add `--model` parameter to `prepare-motion-review.mjs` for vision model selection |
| `audio-design-rules.md` | Dual-track audio system, golden ratios, SFX cue density tiers, timestamp alignment, BGM selection tree, ffmpeg synthesis templates, quality checklist | `audio-and-narration.md`, `audio-cues.json`, `mix-motion-audio.mjs` | **Partial** | Add golden ratio defaults and density tier presets to `audio-cues.json` template |
| `sfx-library.md` | 37 SFX inventory, quick index tables, scene recommendation pairings, usage rules, prompt writing principles | `audio-and-narration.md`, `audio-cues.json` | **Integrated** (as method) | None |
| `voiceover-pipeline.md` | Iron rules, hero element architecture, script format, timeline.json schema, Subtitles component, NarrationStage API, dual time source | `audio-and-narration.md`, `narration-stage.jsx`, `narration-manifest.json`, `compile-narration-timeline.mjs` | **Integrated** | None |
| `tts-doubao.mjs` | Doubao TTS v3 streaming API client with word-level timestamps | `render-narration-tts.mjs` adapter contract | **Integrated** (provider-neutral) | None |
| `hyperframes-backend.md` | Selection boundary, project scaffolding, composition contract, old demo migration, validation & rendering, transparent channel | `render-with-adapter.mjs`, `render-manifest.json` | **Integrated** (as generic adapter) | Add "local vs adapter decision table" to `creative-coding-and-motion-media.md` |
| `launch-film-director-notes.md` | Trigger gate, 5-part director's notes structure, HTML implementation flow, keyframe verification, multi-perspective strategy | `director-notes.md`, `motion-storyboard.md`, `creative-coding-and-motion-media.md` | **Partial** | Expand `director-notes.md` template to enforce full Part I-V structure with word count guidance |
| `multi-perspective-parallel-case-study.md` | 6 perspective selection, brief writing template, parallel execution, failure handling, review framework | `context-and-direction.md` | **Missing** | Add multi-perspective parallel exploration pattern to `context-and-direction.md` |
| `scene-templates.md` | 8 output-type scene catalogs with dimensions, key elements, recommended styles, prompt templates | `layout-patterns.json`, `component-patterns.json` | **Partial** | Add output-type-specific prompt templates to relevant layout/component entries |
| `narration_stage.jsx` (ref) | NarrationStage, Scene, Cue, useNarration, useSceneFade, Subtitles, splitChunkToLines, splitWordsToLines | `assets/starter/narration-stage.jsx` | **Integrated** | None |
| `animations.jsx` (ref) | Stage, Sprite, useTime, useSprite, Easing, interpolate | `assets/starter/react-motion-stage.jsx`, `assets/starter/motion-stage.js` | **Integrated** | None |
| `deck_index.html`, `deck_stage.js` (ref) | Multi-file deck index, single-file Web Component deck | `assets/starter/deck-index.html`, `assets/starter/deck-stage.js` | **Integrated** | None |
| `render-video.js`, `render-video-seek.js` (ref) | Playwright recordVideo pipeline, deterministic seek-based frame capture | `render-motion-media.mjs` | **Integrated** (both modes unified) | None |
| `html2pptx.js` (ref) | DOM-to-PowerPoint translator | `scripts/html-to-pptx.cjs` | **Integrated** (expanded with rotation, shadow, inline formatting, merge containers) | None |
| `export_deck_pdf.mjs`, `export_deck_stage_pdf.mjs` (ref) | Multi-file and stage PDF export | `scripts/export-html-deck-pdf.mjs`, `scripts/export-html-stage-pdf.mjs` | **Integrated** | None |
| `gen_deck_thumbs.mjs` (ref) | Thumbnail generation | `scripts/render-deck-thumbnails.mjs` | **Integrated** | None |
| `export_deck_pptx.mjs` (ref) | Multi-file HTML deck to PPTX | `scripts/export-html-deck-pptx.mjs` | **Integrated** (expanded with editable/fidelity contract) | None |
| `fetch_images.py` (ref) | Wikimedia Commons image fetcher | `scripts/fetch-wikimedia-assets.mjs` | **Integrated** (ported to Node.js, added manifest, SHA-256, license tracking) | None |
| `add-music.sh`, `mix-voiceover.sh`, `sfx-cues.sh`, `render-narration.sh` (ref) | Shell-based audio mixing pipelines | `scripts/mix-motion-audio.mjs`, `scripts/render-narration-tts.mjs`, `scripts/compile-narration-timeline.mjs` | **Integrated** (Node.js equivalents with richer manifests) | None |
| `convert-formats.sh` (ref) | 60fps MP4 derivation + palette GIF | `scripts/render-motion-media.mjs` | **Integrated** (multi-format in single script) | None |
| `design-gate-hook.sh` (ref) | Pre-render gate enforcement | `SKILL.md` exactly-three direction gate | **Noise** (excluded; gate enforced through instructions, routes, tests) | N/A |
| `package.json` (ref) | Dependency declarations | Not copied | **Noise** (dependencies declared per-project, not in skill runtime) | N/A |
| `.env.example` (ref) | DouBan TTS credentials | Not copied | **Noise** (provider-neutral adapter contract replaces vendor-specific config) | N/A |
| `test-prompts.json` (ref) | 6 test prompts | `evals/evals.json` (16 scenarios) | **Integrated** (expanded and restructured) | None |
| `assets/personal-asset-index.example.json` (ref) | Personal brand/contact/product asset paths | Not copied | **Noise** (personal identity data) | N/A |
| `assets/bgm-*.mp3`, `assets/sfx/*` (ref) | Bundled audio media | Not copied | **Noise** (licensing provenance, runtime size) | N/A |
| `assets/showcases/` (ref) | 24 pre-built HTML+PNG preview pairs | Not copied | **Noise** (evidence assets, not reusable methods) | N/A |
| `assets/banner.svg` (ref) | Banner image | Not copied | **Noise** (source branding) | N/A |
| `README.md`, `README.en.md`, `LICENSE` (ref) | Source operation and provenance | Not copied | **Noise** (external to installed runtime) | N/A |
| `demods/` (ref demos) | Demo HTML pages | Incorporated into capability modules and evals | **Integrated** (methods extracted, demos not copied) | None |
| `assets/director-notes-samples/` (ref) | Sample director notes | Not copied | **Noise** (example, not method) | N/A |

---

## Cross-Cutting Gaps

### 1. Documentation-Trigger Mismatches

Three scripts exist and are fully functional but are not surfaced in the `SKILL.md` Runtime Assistance code block:

| Script | Referenced In | SKILL.md Runtime Block |
|--------|--------------|----------------------|
| `compile-narration-tts.mjs` | `audio-and-narration.md` steps 2, 4 | Line 205 shows `compile-narration-timeline.mjs` -- actually PRESENT |
| `fetch-wikimedia-assets.mjs` | `brand-and-product-assets.md` step 4 | Line 203 shows it -- PRESENT |
| `render-deck-thumbnails.mjs` | `html-first-presentations.md` step 4 | Line 204 shows it -- PRESENT |

**Correction:** All three scripts ARE already documented in the SKILL.md runtime assistance block. This is not a gap -- the previous audit finding was based on incomplete reading.

### 2. Prose-Only Capability Modules Without Starter Code

Several capability modules describe workflows that have no corresponding starter scaffold:

| Module | Described Workflow | Missing Starter |
|--------|-------------------|-----------------|
| `context-and-direction.md` | Live tweak panel with persisted state | `tweak-panel.jsx` |
| `context-and-direction.md` | Multi-perspective parallel direction exploration | No orchestration pattern |
| `creative-coding-and-motion-media.md` | GSAP timeline adaptation | `gsap-adapter.mjs` |
| `motion-and-html-presentations.md` | Publication grammar deck layout | `publication-grammar.html` |
| `prototypes-and-data.md` | Taste anchor selection per product type | `taste-anchors.json` |

### 3. Quality Check Coverage Gaps

The `quality-checks.json` (38 checks) covers high-level gates but misses several source-specific pitfalls that were documented with root causes in `animation-pitfalls.md`:

- CSS transition non-determinism in seek rendering
- Proxy tween first-frame gap
- Warmup frame leakage with separate contexts
- Pseudo-chrome filler removal
- `__ready`/tick/lastTick triple trap
- CORS for `file://` delivery
- Cross-scene color inheritance
- Font-loading measurement protection
- Recording warmup protocols

### 4. Audio Design Defaults Missing

The `audio-cues.json` template has ducking configuration but lacks the golden ratio defaults from `audio-design-rules.md`:

- BGM volume: 0.40-0.50
- SFX volume: 1.00
- Frequency gap: -6 to -8dB
- SFX cue density tiers: info-dense (~9/10s), focused (0), balanced (~4/10s)

---

## HTML-First PPTX Contract

The owned skill implements an explicit three-mode contract for HTML-to-PowerPoint conversion:

| Mode | Source | Destination | Verification |
|------|--------|-------------|-------------|
| `editable` | Constrained HTML (p/h1-h6/list elements, no gradients, no background-image on DIV) | Native PowerPoint text, shapes, lists, placeholders via `html-to-pptx.cjs` | Native text XML present, objects editable in Office |
| `fidelity` | Unrestricted HTML (gradients, SVG, Canvas allowed) | Full-slide images via Playwright screenshots + pptxgenjs | Image-backed slides, no false editability claim |
| `unspecified` | -- | -- | Router MUST ask before implementation; silent inference is forbidden |

**Gap:** The `export-html-deck-pptx.mjs` enforces the `editable`/`fidelity` decision at the CLI level (line 45-47 throws if mode is not one of the two). However, the `design-router.mjs` does not have a dedicated `html-pptx-decision` eval scenario that verifies the router asks before proceeding. The existing eval `html-first-pptx-decision` (scenario #14) validates this behavior at the skill trigger level, but the router itself does not return a "decision required" signal when the task is `html-presentation` with deliverable `pptx`.

**Required change:** Add a `pptx_mode_required` field to the router's JSON output when `--pipeline html-first` is specified and the `--pptx-mode` flag is absent.

---

## Runtime Identity/Noise Findings

### Confirmed Noise Exclusions

The following items from the huashu-design reference are correctly absent from the owned skill runtime:

| Noise Category | Source Items | Status |
|---------------|-------------|--------|
| Author identity | "花叔", "alchaincyf", "花生" | Absent |
| Promotion/watermark | `video-export.md` JSX watermark template | Absent |
| Installers/hooks | `design-gate-hook.sh` | Absent |
| Credentials | `.env.example` (DouBan TTS keys) | Absent |
| Vendor lock-in | `tts-doubao.mjs` (ByteDance/DouBan-specific) | Absent (replaced by neutral adapter contract) |
| Personal media | `personal-asset-index.example.json` | Absent |
| Bundled audio | `bgm-*.mp3`, `sfx/*` (37 files) | Absent |
| Showcase evidence | `showcases/` (24 HTML+PNG pairs) | Absent |
| Source README | `README.md`, `README.en.md`, `LICENSE` | Absent |
| Package metadata | `package.json` | Absent |

### Identity Scan

Scanning the complete installed `interface-design` tree (excluding `_external_repos`) confirms:
- No source author name, handle, or pronoun appears in any capability module, script, starter, template, pattern, or eval
- No reference to `huashu-design`, `alchaincyf`, or the DouBan/TikTok TTS service
- No hardcoded API endpoints, tokens, or resource IDs
- No file paths pointing to external repositories

---

## Required Implementation Checklist

Items below are actionable changes needed to achieve full reusable capability parity. Listed in priority order.

### Priority 1: Add Missing Starters

| # | File to Create | Capability Source | Owner Module |
|---|---------------|-------------------|-------------|
| 1 | `assets/starter/tweak-panel.jsx` | `tweaks-system.md` | `context-and-direction.md` |
| 2 | `assets/starter/gsap-adapter.mjs` | `gsap-recipes.md` | `creative-coding-and-motion-media.md` |
| 3 | `assets/starter/publication-grammar.html` | `slide-decks.md` | `motion-and-html-presentations.md` |

### Priority 2: Enrich Existing Templates

| # | File to Modify | Enhancement | Source |
|---|---------------|-------------|--------|
| 4 | `assets/templates/director-notes.md` | Enforce full Part I-V structure with word count guidance | `launch-film-director-notes.md` |
| 5 | `assets/templates/audio-cues.json` | Add golden ratio defaults and density tier presets | `audio-design-rules.md` |
| 6 | `assets/templates/narration-script.md` | Expand with more complete `[[cue:id]]` examples | `voiceover-pipeline.md` |
| 7 | `assets/templates/visual-qa.md` | Add weighted scoring calc and one-vote veto | `critique-guide.md` |

### Priority 3: Enrich Pattern Data

| # | File to Modify | Enhancement | Source |
|---|---------------|-------------|--------|
| 8 | `assets/patterns/quality-checks.json` | Add 9 animation-pitfall-specific checks | `animation-pitfalls.md` |
| 9 | `assets/patterns/quality-checks.json` | Add anti-slop blacklist entries | `content-guidelines.md` |
| 10 | `assets/patterns/visual-direction-patterns.json` | Add `html_implementation_score` and `font_stack` fields | `design-styles.md` |

### Priority 4: Enrich Capability Modules

| # | File to Modify | Enhancement | Source |
|---|---------------|-------------|--------|
| 11 | `references/capabilities/visual-system.md` | Expand CJK section with fallback chain, x-height, punctuation norms | `typography.md` |
| 12 | `references/capabilities/brand-and-product-assets.md` | Add "5-10-2-8" threshold protocol | `brand-asset-protocol.md` |
| 13 | `references/capabilities/prototypes-and-data.md` | Add taste anchor catalog | `app-prototype.md` |
| 14 | `references/capabilities/context-and-direction.md` | Add multi-perspective parallel exploration pattern | `multi-perspective-parallel-case-study.md` |
| 15 | `references/capabilities/creative-coding-and-motion-media.md` | Add local-vs-adapter decision table | `hyperframes-backend.md` |
| 16 | `references/capabilities/motion-and-html-presentations.md` | Add Scene Recipes A/B/C as reusable starters | `animation-best-practices.md` |
| 17 | `references/capabilities/creative-coding-and-motion-media.md` | Add post-render FAQ (size, sharpness, portrait, watermark, alpha, lossless) | `video-export.md` |

### Priority 5: Minor Enhancements

| # | File to Modify | Enhancement | Source |
|---|---------------|-------------|--------|
| 18 | `scripts/prepare-motion-review.mjs` | Add `--model` parameter for vision model selection | `ai-video-review.md` |
| 19 | `assets/starter/react-motion-stage.jsx` | Add pinned CDN setup with integrity verification | `react-setup.md` |
| 20 | `scripts/design-router.mjs` | Return `pptx_mode_required` signal when `--pipeline html-first` without `--pptx-mode` | Internal enhancement |
| 21 | `SKILL.md` | Add runtime-tiered degradation ladder | `SKILL.md` (huashu) |

---

## Acceptance Tests

### Structural Verification

| Test | Command / Method | Expected |
|------|-----------------|----------|
| All referenced scripts exist | Glob `scripts/*.mjs`, `scripts/*.cjs` | 14 scripts found |
| All referenced starters exist | Glob `assets/starter/*` | 15 starters found |
| All referenced templates exist | Glob `assets/templates/*` | 15 templates found |
| All referenced capabilities exist | Glob `references/capabilities/*.md` | 15 modules found |
| All referenced patterns exist | Glob `assets/patterns/*.json` | 9 JSONs found |
| No source author identity in runtime | Grep for "花叔\|alchaincyf\|huashu" | 0 matches |
| No vendor credentials in runtime | Grep for "DOUBAO_\|tiktok\|byteDance" | 0 matches |
| No installers/hooks in runtime | Grep for "design-gate-hook\|install\|update" in scripts | 0 matches |
| All eval scenarios have valid JSON | Parse `evals/evals.json` | 17 scenarios parsed |
| All pattern JSONs valid | Parse each `assets/patterns/*.json` | All parse successfully |

### Capability Trigger Verification

| Test | Scenario ID | Should Trigger | Key Behaviors |
|------|------------|---------------|---------------|
| Product landing | `premium-product-landing` | Yes | Delivery route, content brief, product-first layout, 3 directions, responsive screenshots |
| Dashboard | `operational-dashboard` | Yes | Decision-first metrics, command-center layout, all states |
| App prototype | `interactive-app-prototype` | Yes | Fidelity contract, critical flow, device verification |
| Browser presentation | `browser-presentation` | Yes | Narrative arc, keyboard nav, per-frame QA |
| Native PPTX | `native-powerpoint-boundary` | No | Route to pptx/window-pptx |
| Hybrid handoff | `hybrid-presentation-handoff` | Yes | HTML exploration, approved direction, ppt-handoff contract |
| README cover | `github-readme-cover` | Yes | Repository truth, claim-to-evidence, directions, hero pattern |
| Poster | `marketing-poster` | Yes | Fixed-format contract, safe area, thumbnail inspection |
| Product demo video | `product-demo-video` | Yes | Motion storyboard, deterministic time, silent video, poster |
| Creative coding | `creative-coding-visual` | Yes | Primitive selection, seeded randomness, nonblank pixel check |
| Autoplay GIF | `readme-autoplay-gif` | Yes | Deterministic source, palette optimization, infinite loop |
| Editable PPTX | `html-first-editable-pptx` | Yes | Editable mode, DOM constraints, native text |
| Fidelity PPTX | `html-first-fidelity-pptx` | Yes | Fidelity mode, image-backed slides, non-editability disclosure |
| PPTX decision | `html-first-pptx-decision` | Yes | Must ask editable vs fidelity |
| Device variants | `device-prototype-variants` | Yes | 3 directions, comparison canvas, max 6 tweaks |
| Narrated film | `narrated-launch-film` | Yes | TTS adapter, measured timing, ducking, loudness verification |
| Infographic | `evidence-infographic` | Yes | Evidence-infographic route, sourced stats, text fallback |

---

## Questions Raised By The Independent Audit

1. **Should the `tweak-panel.jsx` starter be included?** The reference repo's `tweaks-system.md` provides a complete, tested React component with localStorage persistence. Adding it would close a gap between the owned skill's description of "no more than six meaningful live tweaks with persisted state" (SKILL.md line 126) and available starter code.

2. **Should GSAP adapter be added?** The reference repo's `gsap-recipes.md` is 653 lines of production-tested easing mappings, narrative skeletons, and seek-safety rules. The owned skill targets vanilla JS/React, but many real projects use GSAP (especially HyperFrames users). A lightweight adapter would bridge this without vendor lock-in.

3. **Should the anti-slop blacklist be machine-readable?** The `content-guidelines.md` blacklists are highly actionable (specific font names to ban, specific CSS patterns to avoid, specific layout traps). Encoding these as a JSON alongside `quality-checks.json` would make them queryable by the design router.

4. **Is the 5-level runtime degradation ladder necessary?** The reference repo's degradation plan is designed for Claude-specific capabilities that weaker models cannot replicate. The owned skill's `Weak-Model Decision Discipline` (8 rules) achieves the same goal more generically. Decide whether to keep both or consolidate.

5. **Should Scene Recipes A/B/C be added as starters?** The reference repo's recipes provide exact timing/easing/SFX density/BGM specifications for three common animation narratives. They would be valuable additions to `assets/starter/` but would increase the skill's starter count from 11 to 14.

6. **Are the 21 animation pitfalls worth individual quality checks?** Adding them to `quality-checks.json` would increase the check count from 38 to 59. Many overlap with existing checks (deterministic time, reduced motion, nonblank canvas). Evaluate whether the overlap justifies the expansion or if they should be grouped under a "seek rendering safety" check category.

---

## Post-Audit Resolution

The audit findings were checked against the final worktree and resolved by capability rather than by copying source files.

| Initial finding group | Final disposition | Evidence |
|---|---|---|
| Runtime script visibility (#1-#3) | Rejected as stale | All 14 scripts are named from the entry skill or their progressive module. The three scripts called out by the audit were already present in `SKILL.md`. |
| Narration/review flexibility (#4-#5) | Resolved or adapted | The narration template documents scene and cue grammar. Semantic review accepts project instructions, emits a provider-neutral package, and leaves model selection to the authorized caller instead of embedding a vendor selector. |
| Tweak panel and parallel perspectives (#6-#7) | Resolved | `tweak-panel.jsx` provides SSR-safe persisted controls; the direction module delegates broad perspectives through `cli-agent-orchestrator`, then requires exactly three real previews. |
| GSAP, gallery geometry and adapter boundary (#8-#10) | Resolved or adapted | Optional deterministic GSAP and gallery-wall starters are included. The motion module contains an explicit local-versus-adapter decision table; no new runtime dependency is installed. |
| Output contracts, direction DNA and taste anchors (#11-#12, #22) | Resolved | Eight output contracts, six taste anchors and 40 scored visual directions with resolvable font profiles are machine-readable and loaded by the router. |
| Critique and anti-template rules (#13-#14) | Resolved | The weighted QA rubric includes a concept veto; nine anti-template rules and the blocker/high QA gates are machine-readable and returned by the router. |
| React browser setup (#15) | Adapted | The owned capability is local-project-first and documents current pin/SRI verification plus an offline fallback. Stale third-party versions and hashes are intentionally not frozen into the universal runtime. |
| Director notes, scene recipes and rendering pitfalls (#16-#18) | Resolved | The Part I-V director template, three timed scene recipes, dedicated motion-safety module and seven focused deterministic-capture checks cover the reusable behavior without duplicating overlapping checks. |
| CJK typography and post-render requests (#19-#20) | Resolved | Mixed-script fallback order, x-height/baseline behavior, punctuation, synthetic-style and subset guidance are present; media delivery follow-ups cover size, sharpness, portrait, alpha, lossless and watermark policy. |
| Publication grammar, audio defaults and asset threshold (#21, #23-#24) | Resolved | Publication slide starter, audio density/mix defaults and evidence acquisition threshold are implemented as source-neutral workflow assets. |
| Runtime degradation and trigger prompts (#25-#26) | Resolved | The five-level degradation ladder is in `SKILL.md`; 17 owned evaluation scenarios expand the source prompts and test the delivery boundaries. |
| HTML-first PPTX decision field | Rejected as duplicate | `design-router.mjs` already returns `decision_required` with editable/fidelity options and stops implementation. A second `pptx_mode_required` boolean would create two sources of truth. |

### Final Structural Result

- 15 progressive capability modules
- 9 machine-readable pattern and decision libraries
- 15 reusable source starters
- 15 durable templates
- 14 executable provider-neutral scripts
- 43 quality checks, including deterministic capture and critique-veto gates
- 40 visual directions with HTML implementation score and font-stack profile
- 17 trigger and boundary evaluation scenarios

### Final Neutrality Result

The installed runtime contains no source author identity, personal asset index, promotional watermark, installer/update hook, provider credential, provider-specific TTS endpoint, bundled third-party media, or source repository path. The ignored source mirror remains audit input only and is excluded by Skillbird installation.

### Final Decision

All reusable methods identified in the audited snapshot are integrated, expanded, or deliberately adapted behind owned triggers, routes, templates, starters, scripts, and tests. Excluded files are operational noise, personal identity, external media, credentials, or stale vendor configuration rather than missing professional capability.

### Independent Final Verification

OpenCode session `ses_075ab8bb1ffeA6lh3tCV6i4G5H` used `agnes/agnes-2.0-flash` against the completed worktree and returned PASS with no blocker or high finding. Its route probes confirmed README, dashboard, prototype, infographic, product-demo, HTML presentation, explicit HTML-first PPTX, and ordinary native PPTX ownership behavior.

Three final-report parser mistakes were rejected by direct checks:

- `component-patterns.json` contains 32 records under `components`, not zero;
- the script directory contains 14 executable files, not 15;
- `SKILL.md` contains an explicit five-level `Runtime Degradation Ladder`; the auditor's lowercase case-sensitive search missed the heading.

The first broad final-audit run became stale with no new log, tool, or session-update event and was stopped by the caller. The narrower retry remained active through 36 steps and exited naturally. This records event-based waiting behavior rather than a fixed elapsed-time cutoff.
