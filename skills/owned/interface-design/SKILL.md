---
name: interface-design
description: Consolidated UI and frontend design workflow. Use when building, refactoring, auditing, or polishing interfaces, including frontend design, brand DESIGN.md routing, baseline UI quality, accessibility, metadata, motion performance, design variation, polish, and interaction feel.
category: design
subcategory: interface
tags:
  - ui
  - frontend
  - brand
  - design-md
  - accessibility
  - polish
compatibility:
  tools: [bash, browser, playwright]
  requires: Existing app or a concrete interface brief
---

# Interface Design

Use this skill for product interfaces, web apps, dashboards, tools, and UI polish. It replaces the default need to install several overlapping external UI skills.

## Design Priorities

1. Fit the product domain
   - Operational tools should be quiet, dense, scannable, and efficient.
   - Marketing pages should make the product or offer visible in the first viewport.
   - Games and expressive tools can be more visual and animated.
2. Use familiar controls
   - Icons for tool actions.
   - Toggles and checkboxes for binary state.
   - Segmented controls for modes.
   - Sliders, steppers, or inputs for numbers.
   - Tables, lists, and tabs for work-heavy surfaces.
3. Keep layout stable
   - Define dimensions for toolbars, boards, controls, counters, grids, and cards.
   - Prevent hover, labels, loading text, and dynamic values from shifting the layout.
4. Make accessibility part of implementation
   - Keyboard access, focus state, labels, contrast, semantic HTML, and error messages are acceptance criteria.
5. Verify visually
   - Use Playwright screenshots for meaningful frontend changes.
   - Check mobile and desktop breakpoints.

## Workflow

1. Read the existing UI conventions, design tokens, component APIs, and routing.
2. Identify the target workflow the screen must support.
3. Decide the information hierarchy before styling.
4. Implement with local components and existing design system patterns.
5. Audit:
   - text fit and overflow;
   - contrast and focus visibility;
   - responsive behavior;
   - motion performance;
   - metadata when the page is public.
6. Verify with tests, screenshots, or manual browser checks.

## Brand DESIGN.md Routing

Use this section when the user asks for a brand style, a `DESIGN.md`, a named company/product visual language, or a brand-inspired UI direction.

Built-in brand assets live here:

- `references/brand-design-md/brands.json`
- `references/brand-design-md/design-md/*.DESIGN.md`

Process:

1. Match the requested brand against `brands.json` and available `*.DESIGN.md` files.
2. If the user did not specify a brand, ask for the target brand or offer two or three relevant options.
3. Confirm:
   - single brand or blended brands;
   - whether to write root `./DESIGN.md` or keep candidates in a project docs folder;
   - target surface such as dashboard, landing page, component library, app shell, or marketing page;
   - constraints on fonts, colors, motion, accessibility, and existing design tokens.
4. Read the selected brand file before designing.
5. Treat the brand file as alignment input, not a destructive override of the existing product system.
6. During implementation, read the project `DESIGN.md`, local tokens, components, and previous UI before editing.

Guardrails:

- Do not blindly combine multiple brands into an unreadable style.
- If the product already has a design system, preserve its interaction patterns and adapt only the visual language that improves the task.
- Do not copy brand names into user-facing UI unless the user explicitly wants that.
- Keep accessibility and responsive behavior above brand mimicry.

## Guardrails

- Do not build a landing page when the user asked for an app or tool.
- Do not put cards inside cards.
- Do not use decorative gradient blobs or generic SVG hero art as a substitute for meaningful product visuals.
- Do not introduce a new design system unless the repo already expects it or the request explicitly asks for it.
- Do not let UI text overlap or overflow its controls.

## Output Contract

Report:

- UX workflow addressed;
- brand/design reference used when applicable;
- key files changed;
- desktop/mobile verification performed;
- known design tradeoffs.
