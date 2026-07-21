---
name: interface-design
description: Use for any HTML/CSS/JS-driven visual design or rendered product asset, including README covers and GitHub project branding, posters, banners, product showcases, demo videos, creative coding, SVG or canvas visuals, product and app prototypes, web UI, dashboards, design systems, landing or campaign pages, interactive reports, data visualization, HTML presentations, motion, visual audits, redesigns, accessibility, responsive behavior, and brand DESIGN.md routing. Route native PowerPoint delivery to the PPT skill instead.
category: design
subcategory: interface
tags:
  - ui
  - frontend
  - brand
  - design-md
  - accessibility
  - polish
  - repository-branding
  - poster
  - motion-media
  - creative-coding
metadata:
  capability_modules:
    - references/capabilities/delivery-routing.md
    - references/capabilities/context-and-direction.md
    - references/capabilities/information-architecture.md
    - references/capabilities/visual-system.md
    - references/capabilities/components-and-interaction.md
    - references/capabilities/prototypes-and-data.md
    - references/capabilities/motion-and-html-presentations.md
    - references/capabilities/brand-and-product-assets.md
    - references/capabilities/repository-branding-and-marketing.md
    - references/capabilities/creative-coding-and-motion-media.md
    - references/capabilities/implementation-and-verification.md
  decision_assets:
    - assets/patterns/layout-patterns.json
    - assets/patterns/component-patterns.json
    - assets/patterns/decision-rules.json
    - assets/patterns/quality-checks.json
compatibility:
  tools: [bash, browser, playwright]
  requires: Existing app, visual source material, or a concrete design brief
---

# HTML Based Universal Design

Use this skill as a design, prototype, implementation, and visual-quality system for browser-native work. The output may be a production interface, an interactive prototype, a marketing experience, a data product, a component, or an HTML presentation. Design decisions must come from content, users, workflow, and evidence rather than a generic visual template.

## Delivery Boundary

Route by the required final artifact before designing:

| Deliverable | Owner | Rule |
|---|---|---|
| HTML/CSS/JS page, app, prototype, dashboard, report, visualization, or browser presentation | `interface-design` | This skill owns design and implementation. |
| README cover, repository banner, poster, product showcase, social image, or other rendered still | `interface-design` | This skill owns product understanding, art direction, source composition, rendering, and visual QA. Image generation may supply a truthful ingredient, but it does not replace the design workflow. |
| Product demo, motion hero, launch loop, or other browser-rendered video | `interface-design` | This skill owns storyboard, deterministic HTML/canvas source, poster fallback, rendering, encoding, and frame QA. |
| Native editable `.pptx`, PowerPoint template, slide master, or Office-compatible deck | `pptx` or `window-pptx` | The PPT skill owns generation, editing, rendering, and Office QA. |
| HTML visual exploration followed by native PowerPoint | `interface-design`, then PPT owner | Produce a design brief and handoff contract; rebuild natively. Do not present an HTML conversion as equivalent to native PowerPoint. |

When “presentation” is ambiguous and the final format changes the architecture, confirm HTML presentation versus native `.pptx`. Read `references/capabilities/delivery-routing.md` for the full contract.

## Operating Modes

- **Build:** create a new browser-native experience from an accepted brief.
- **Prototype:** test product structure, interaction, or visual direction at deliberate fidelity.
- **Study:** extract reusable design decisions from supplied interfaces or references without copying protected identity or content.
- **Audit:** inspect an existing implementation and report evidence-backed defects before changing code.
- **Redesign:** preserve required behavior and content while correcting information, interaction, and visual structure.
- **Asset:** design a repository, brand, campaign, product-proof, or motion deliverable from verified product facts and reproducible source.

## Capability Routing

Load only the modules needed for the current stage.

| Need | Module |
|---|---|
| Artifact ownership, HTML/PPT boundary, hybrid handoff | `references/capabilities/delivery-routing.md` |
| Existing-system scan, audience, intent, references, direction exploration | `references/capabilities/context-and-direction.md` |
| User flow, content model, hierarchy, page plan, copy and states | `references/capabilities/information-architecture.md` |
| Art direction, typography, color, spacing, grids, imagery, design tokens | `references/capabilities/visual-system.md` |
| Controls, navigation, forms, tables, cards, state matrix, accessibility | `references/capabilities/components-and-interaction.md` |
| App prototypes, dashboards, reports, charts, data and fidelity decisions | `references/capabilities/prototypes-and-data.md` |
| Motion grammar and browser-native slide narratives | `references/capabilities/motion-and-html-presentations.md` |
| Covers, banners, posters, product showcases, brand assets, and still rendering | `references/capabilities/brand-and-product-assets.md` |
| README and repository branding, developer-product proof, and marketing integration | `references/capabilities/repository-branding-and-marketing.md` |
| SVG, canvas, deterministic animation, storyboards, poster fallbacks, and encoded media | `references/capabilities/creative-coding-and-motion-media.md` |
| Framework fit, responsive implementation, browser testing and critique | `references/capabilities/implementation-and-verification.md` |

Decision rules and reusable patterns live under `assets/patterns/`. Durable brief, system, prototype, repository-visual, motion-storyboard, QA, and presentation-handoff templates live under `assets/templates/`. Reusable source scaffolds live under `assets/starter/`.

## Canonical Design Loop

### 1. Route The Deliverable

Name the final artifact, runtime, editability requirement, target devices or frame geometry, distribution surface, static fallback, and acceptance method. Do not start HTML when the accepted deliverable is native PowerPoint.

### 2. Recover Design Context

Read the existing product, routes, tokens, components, fonts, icons, assets, content, screenshots, tests, and project `DESIGN.md`. For repository branding, read the code-backed product entry point, current version, real commands, capability boundaries, README, and existing media. Inspect the first viewport and representative dense, empty, loading, error, and mobile states. Preserve established interaction behavior unless the request changes it.

### 3. Understand Users And Content

Define the primary user, job, environment, critical action, content priority, trust requirements, and success signal. Build information architecture and a state inventory before styling. For a visual asset, create a claim-to-evidence ledger and identify the one product proof that must remain legible at final display size. Never invent metrics, testimonials, customer names, product behavior, terminal output, or product facts to fill a layout.

### 4. Choose Structure Before Decoration

Use `assets/patterns/decision-rules.json` to map content signals to a macrostructure. Select the page, screen, still-frame, or timed-sequence shape and component roles before choosing visual effects. An operational tool should optimize scanning and repeated action; a marketing or repository asset should reveal the actual product and audience immediately; a presentation or demo sequence should carry one argument per frame or scene.

### 5. Establish Direction And System

For a visually open greenfield brief, produce two or three materially different direction previews that vary composition, type, color behavior, imagery, and motion, then obtain a decision before full build. Record what each direction emphasizes and why the selected direction fits the audience. Skip divergence for a small correction, a locked brand system, a specified direction, or an explicit one-pass request.

Lock semantic tokens for surfaces, text, borders, accents, state, spacing, type, radius, shadow, and motion. Use `oklch()` when the project supports it, with fallbacks when compatibility requires them. Color and typography must support hierarchy, not replace it.

### 6. Build A Real Slice

Implement the primary workflow or product story end to end with real or structurally honest content. Reuse the local framework and components. Build feature-complete controls and their default, hover, focus-visible, active, disabled, loading, empty, error, success, and selected states as applicable. For still or motion assets, preserve editable HTML/CSS/JS source and expose a deterministic time setter before rendering.

### 7. Expand Deliberately

Add secondary paths, responsive transformations, data states, and motion only after the primary slice works. Keep content density appropriate to the task. Use visual assets that reveal the real product, object, place, data, or state when inspection matters.

### 8. Verify In A Browser

Run functional checks and inspect screenshots at the actual target sizes. For responsive web work, include 320, 375, 414, 768, and a representative desktop width unless the product contract specifies different devices. For fixed media, inspect the exact output geometry plus a downscaled GitHub or distribution preview. Check console and network errors, keyboard flow, focus, contrast, overflow, text fit, touch targets, reduced motion, loading stability, image/font completion, nonblank canvas pixels, poster fallback, frame continuity, duration, codec, and file size as applicable.

### 9. Critique And Refine

Score concept fit, hierarchy, craft, functionality, specificity, restraint, responsiveness, and accessibility. Fix the highest-impact structural problem before polishing details. Compare the final result with the brief and existing system, not with the agent’s own intent.

### 10. Deliver Evidence

Report the user flow or story, selected direction, changed files, target viewports or media geometry, interactions exercised, screenshots or tests, accessibility result, media validation, known tradeoffs, source path, and final artifact path. For a hybrid presentation, emit `assets/templates/ppt-handoff.md` and route native production to the PPT owner.

## Weak-Model Decision Discipline

When judgment is limited, follow these rules in order:

1. Preserve the existing design system and real content.
2. Choose a known macrostructure from the pattern library based on content signals.
3. Use one display face, one body face, and optional mono only when data or code needs it.
4. Use semantic tokens; do not improvise colors, spacing, shadows, or radii component by component.
5. Prefer one strong visual idea and one accent behavior over many decorations.
6. Implement the complete primary workflow and state matrix before adding novelty.
7. For motion, storyboard first, use deterministic time, and require a static poster fallback.
8. Run the quality checklist and browser evidence loop; do not claim visual quality from code inspection.

If context is constrained, load in this order: delivery route, context and content, chosen pattern, visual system, relevant component module, verification. Never drop artifact routing, content truth, accessibility, responsive behavior, or final verification.

## Brand DESIGN.md Routing

Built-in brand references live at:

- `references/brand-design-md/brands.json`
- `references/brand-design-md/design-md/*.DESIGN.md`

Match a named brand against the index and read the selected file before designing. Treat it as alignment input, not permission to copy identity into unrelated user-facing content or overwrite a working product system. If no built-in reference exists, derive a compact brand brief from official user-provided or verified assets, then record tokens and usage constraints in the project design system template.

When blending directions, name which decision comes from which direction and prevent conflicting type, spacing, icon, or motion systems. Accessibility and product usability outrank mimicry.

## Non-Negotiable Quality Rules

- Do not substitute a landing page for an app, tool, dashboard, or prototype.
- Do not default to a centered full-viewport hero, three identical feature cards, nested cards, gradient headline, purple-blue glow, decorative orbs, generic browser chrome, or filler copy.
- Do not make every section share the same alignment, spacing, surface, and visual weight.
- Do not use cards where a table, list, timeline, chart, comparison, or unframed section communicates better.
- Do not invent product evidence or hide missing content behind polish.
- Do not treat “make a cover” as an image-generation prompt. Understand the product, audience, proof, distribution surface, and fallback before creating media.
- Do not use hover-only affordances, `transition: all`, autoplay sound, unpausable motion, or animation that shifts layout.
- Do not render an MP4 from wall-clock animation, omit its poster fallback, or accept black, duplicated, clipped, or unreadable frames.
- Do not allow clickable labels, controls, metrics, or headings to overflow or collide at any target width.
- Do not create an SVG illustration when a real or generated bitmap, actual product view, chart, or code-native visual better communicates the subject.
- Do not add a new component library or visual framework unless the accepted design and repository justify it.

## Runtime Assistance

From the installed skill directory:

```bash
node scripts/design-router.mjs --task dashboard --deliverable html --signals trends,comparison --format json
node scripts/design-router.mjs --task html-presentation --deliverable hybrid --platform windows
node scripts/design-router.mjs --task readme-cover --deliverable image --signals developer-tool,terminal --format json
node scripts/design-router.mjs --task product-demo --deliverable video --signals workflow,product-proof
NODE_PATH=<playwright-node-modules> node scripts/render-motion-media.mjs --input <source.html> --output-dir <assets-dir> --name product-loop
```

The router returns artifact ownership, operating mode, suggested macrostructures, components, and required quality gates. It is advisory and read-only; repository evidence and accepted user decisions remain authoritative.
