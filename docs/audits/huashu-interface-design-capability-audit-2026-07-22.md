# HTML-Native Design Capability Parity Audit

**Audit date:** 2026-07-22
**Reference snapshot:** `alchaincyf/huashu-design@32cc58127f6074965e72530a2b593dac43572ec6`
**Owned destination:** `skills/owned/interface-design/`

## Verdict

The owned Skill now contains the reusable production methods from the audited snapshot as source-neutral, progressively loaded capabilities. It does not install or execute the source repository. Runtime files contain no source author identity, promotion, watermark, installer, update hook, personal asset index, bundled third-party media, provider credential, or provider-specific TTS implementation.

Capability parity does not mean byte-for-byte copying. A method is accepted only when it has an owned trigger or route plus a usable module, template, starter, script, quality gate, or behavior test. Source-specific noise is documented here and intentionally does not enter the installed Skill.

## Source Capability Inventory

| Source file or group | Reusable capability | Owned destination | Status |
|---|---|---|---|
| `SKILL.md`, `workflow.md`, `design-context.md` | Fact-first intake, context discovery, assumptions, junior checkpoints, variations, graceful fallback | `SKILL.md`, `context-and-direction.md`, `design-brief.md`, `direction-decision.md` | Integrated; exactly three real direction previews are a hard gate with recorded narrow bypasses |
| `content-guidelines.md`, `critique-guide.md` | Anti-template rules, truthful content, scale, hierarchy, craft, function, originality, critique output | `visual-system.md`, `implementation-and-verification.md`, `quality-checks.json`, `visual-qa.md` | Integrated as decision and QA rules |
| `design-styles.md`, `apple-gallery-showcase.md`, showcase families | Broad direction vocabulary, gallery geometry and comparison before commitment | `visual-direction-patterns.json`, `design-comparison.jsx`, `gallery-wall-stage.js`, `direction-comparison-canvas` | Integrated as 40 neutral direction families with HTML implementation scores and resolvable font-stack profiles; source showcases are evidence, not copied runtime designs |
| `typography.md` | Modular type scale, line length/height, open-font selection, CJK and mixed-script rules | `visual-system.md`, `design-system.md`, typography quality gates | Integrated |
| `brand-asset-protocol.md`, `fetch_images.py` | Ask/search/verify/fallback asset flow, real-image preference, provenance, placeholders | `brand-and-product-assets.md`, `asset-manifest.json`, `brand-spec.md`, `fetch-wikimedia-assets.mjs` | Integrated and hardened with bounded queries, a required descriptive User-Agent, content-type checks, license metadata and SHA-256 evidence |
| `react-setup.md`, `app-prototype.md` | Existing-stack preference, prototype architecture, real states, image policy, interaction and click validation | `react-browser-setup.md`, `prototypes-and-data.md`, `components-and-interaction.md`, `prototype-plan.md`, `tweak-panel.jsx`, `webapp-testing` handoff | Integrated with local-first React setup, offline fallback and SSR-safe persisted tweaks |
| `ios_frame.jsx`, `android_frame.jsx`, `macos_window.jsx`, `browser_window.jsx`, `design_canvas.jsx` | Accurate presentation frames, side-by-side design comparison, inspectable variants | Owned source-neutral starter components with corresponding names, plus `design-comparison.jsx` and `tweak-panel` pattern | Integrated; no source branding retained |
| `tweaks-system.md`, variation/review demos | Live design variables, comparison axes, bounded alternatives, explicit selection | `context-and-direction.md`, `visual-system.md`, `design-comparison.jsx`, `tweak-panel` | Integrated |
| `slide-decks.md`, `deck_index.html`, `deck_stage.js` | Multi-file and single-file HTML decks, keyboard/fullscreen/print behavior, speaker notes | `motion-and-html-presentations.md`, `deck-index.html`, `deck-stage.js`, `speaker-notes` pattern | Integrated |
| `export_deck_pdf.mjs`, `export_deck_stage_pdf.mjs`, `gen_deck_thumbs.mjs` | Multi-file and stage PDF export, deck preview/visual QA | `export-html-deck-pdf.mjs`, `export-html-stage-pdf.mjs`, `render-deck-thumbnails.mjs` | Integrated; real two-page outputs and executable thumbnail rendering are covered |
| `editable-pptx.md`, `html2pptx.js`, `export_deck_pptx.mjs` | Explicit HTML-first PowerPoint delivery | `html-first-presentations.md`, `html-to-pptx.cjs`, `export-html-deck-pptx.mjs` | Expanded into mandatory `editable` DOM-to-native and `fidelity` image-slide contracts |
| `animations.md`, `animations.jsx`, `gsap-recipes.md`, `scene-templates.md` | Easing, interpolation, stagger, reusable scenes, Stage/Sprite APIs | `creative-coding-and-motion-media.md`, `motion-rendering-safety.md`, deterministic Stage starters, output contracts and motion recipes | Integrated through vanilla/React primitives plus an optional seek-safe GSAP adapter for projects already using GSAP |
| `animation-best-practices.md`, `animation-pitfalls.md`, `cinematic-patterns.md` | Physical motion, anticipation/follow-through, continuity, pacing, cinematic staging, anti-slop review | Motion capability modules, `director-notes.md`, `motion-storyboard.md`, media quality gates | Integrated |
| `hero-animation-case-study.md`, `multi-perspective-parallel-case-study.md` | Shared elements, one-take and parallel-perspective narrative methods | `creative-coding-and-motion-media.md`, `narration-stage.jsx`, `demo-story-sequence` | Integrated as reusable method, not copied branded examples |
| `video-export.md`, `render-video.js`, `render-video-seek.js`, `convert-formats.sh` | Deterministic timeline capture, arbitrary FPS, MP4, poster, two-pass palette GIF, transparent overlays, PNG sequences, looping and size control | `render-motion-media.mjs` | Integrated and expanded; GIF/MP4/poster/WebM/ProRes/PNG sequence may be selected per distribution context |
| `verification.md`, `verify-video.sh`, `verify.py` | Browser errors, responsive screenshots, frame integrity, codec/duration/size, black-frame detection | `implementation-and-verification.md`, `verify-motion-media.mjs`, `quality-checks.json` | Integrated; representative frame hashes and GIF loop checks added |
| `ai-video-review.md`, `ai-review-video.py` | Objective freeze/silence probes plus optional semantic review of sampled video frames | `prepare-motion-review.mjs`, review checklist | Integrated as a provider-neutral review package; no remote provider is embedded |
| `audio-design-rules.md`, `sfx-library.md`, `launch-film-director-notes.md` | Sound intent, causal effects, cue sheets, pacing, loudness, licensing | `audio-and-narration.md`, `audio-cues.json`, `director-notes.md` | Integrated; licensed project media only |
| `voiceover-pipeline.md`, `narration_stage.jsx`, `narrate-pipeline.mjs`, `render-narration.sh` | Script segmentation, measured timing, captions, continuous narration-led motion | `audio-and-narration.md`, `narration-stage.jsx`, `narration-script.md`, `compile-narration-timeline.mjs`, `render-narration-tts.mjs` | Integrated and provider-neutral; real clip durations drive scene timing and word sidecars enable exact cues |
| `mix-voiceover.sh`, `add-music.sh`, `sfx-cues.sh` | Voice/music/effect mixing, fades, timing, ducking and loudness | `mix-motion-audio.mjs`, `audio-cues.json` | Integrated; tested with three buses, sidechain ducking and 48 kHz AAC output |
| `tts-doubao.mjs` | TTS adapter behavior | `render-narration-tts.mjs` adapter contract | Method integrated; provider identity, endpoint and credentials excluded as noise |
| `hyperframes-backend.md` | Optional advanced-render backend boundary | `render-with-adapter.mjs`, `render-manifest.json` | Integrated as an executable project adapter contract, not a vendor dependency |
| Demos, `test-prompts.json`, sample director notes | Scenario and acceptance ideas | `evals/evals.json`, templates, deterministic tests | Integrated as neutral scenarios; personal examples are not runtime assets |
| Bundled BGM/SFX, showcases, banner, personal asset index | Example media or project identity | None | Noise: not copied because provenance, licensing, identity, or runtime size is not a reusable method |
| `design-gate-hook.sh`, install/update instructions, promotion watermark | Environment mutation or promotion | None | Noise: excluded; the owned Skill enforces gates through instructions, routes and tests |
| README, package metadata, `.env.example`, license | Source operation and provenance | This audit only | Provenance retained outside installed runtime |

## Owned Runtime Architecture

```text
SKILL.md
  -> task and artifact route
  -> progressive capability module
  -> pattern/decision/quality library
  -> template or starter
  -> executable renderer/exporter/verifier when needed
  -> browser/media/package evidence
```

The installed runtime includes 15 capability modules, 9 machine-readable decision libraries, 22 layout patterns, 32 component patterns, 23 decision rules, 43 quality checks, 40 visual direction families, 15 source starters, 15 durable templates, and 14 provider-neutral routing, export, review, adapter, asset, narration, and audio scripts.

The router loads all nine decision libraries. A route can therefore return output contracts, taste anchors, motion recipes, anti-template rules, layouts, components, and risk-scaled quality gates instead of leaving those methods as passive prose.

## HTML-First Presentation Contract

Ordinary `.pptx`, PowerPoint, business deck, or Office-native requests remain owned by `pptx` or `window-pptx`. `interface-design` owns PowerPoint output only when the user explicitly asks for an HTML-first workflow.

- `editable`: constrained HTML is translated into native PowerPoint text, shape, image, table, chart, and placeholder objects. Unsupported DOM/CSS fails closed before output.
- `fidelity`: unrestricted HTML is rendered to full-slide images. Visual fidelity is retained, but slide objects are explicitly non-editable.
- `unspecified`: the router requires the editability decision. It must not infer the tradeoff.

Both modes preserve filename order and optional speaker notes. Real smoke tests produced two-slide packages; the editable package contained native text XML, while the fidelity package contained image-backed slides without native text.

## Runtime Neutrality

Automated scans cover the complete installed `interface-design` tree while excluding ignored `_external_repos`. Forbidden source identity, promotion, installer/hook names, and provider-specific TTS markers are absent. The external snapshot is Git-ignored and the Skillbird copy filter excludes it from every target installation.

## Validation Evidence

- Multi-file HTML to PDF: 2 pages, vector text, 32,605 bytes.
- Single-file `<deck-stage>` to PDF: 2 pages, vector text, 14,769 bytes.
- HTML-first editable PPTX: 2 slides, native text objects and speaker notes.
- HTML-first fidelity PPTX: 2 image-backed slides, speaker notes, no false editability claim.
- Deterministic media: poster, H.264 MP4 and infinite-loop two-pass GIF with representative-frame and black-frame checks.
- Narration adapter: manifest-driven WAV production through a project-local adapter.
- Narration compiler: two measured clips became a 2.25-second continuous 48 kHz WAV timeline through the ffmpeg-only probe fallback; cue estimates remain labeled when word timing is absent.
- Deck thumbnails: 3/3 HTML showcase slides rendered to a manifest-driven JPEG preview set.
- Asset acquisition: a bounded Commons query downloaded 1/1 image with source, author, license, dimensions and SHA-256 evidence.
- Audio mix: voice, music and effect buses; sidechain ducking; integrated loudness target; 4-second H.264/AAC output at 48 kHz.
- Behavior tests cover triggers, routes, artifacts, dual PPTX contracts, GIF, devices/variants, narration, and source neutrality.
- Focused architecture tests: 20/20 passed after the final routing and pattern integration.
- Full repository tests before final synchronization: 108/108 passed; the final gate reruns this suite after documentation and installation changes.
- Independent final OpenCode verification: `agnes/agnes-2.0-flash`, session `ses_075ab8bb1ffeA6lh3tCV6i4G5H`, verdict PASS with no blocker or high finding. Main-agent spot checks corrected three auditor parsing errors: 32 component records, 14 scripts, and an explicit five-level Runtime Degradation Ladder at `SKILL.md`.

## Remaining Boundaries

No reusable source capability is intentionally omitted. The excluded items are non-capabilities: source identity, promotional output, personal media/indexes, bundled media with external provenance, environment-mutating hooks, installer/update behavior, and provider-specific credentials. New providers, media libraries, or remote renderers must be project-owned adapters with explicit authorization and provenance.
