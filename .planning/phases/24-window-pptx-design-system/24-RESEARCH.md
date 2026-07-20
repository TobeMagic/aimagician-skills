# Phase 24 Research: Raising the Visual Quality Floor

## Governed Foundations

- 12-column normalized grid; 0.5-inch horizontal and 0.4-inch vertical 16:9 safe margins with proportional custom-size scaling.
- 8pt spacing scale, explicit type hierarchy, body text at least 16pt, labels/footnotes at least 11pt, and a hard error below 10pt.
- Semantic color roles, contrast pairs, border/radius/shadow/decoration tokens, and deterministic light/dark behavior.
- Brand overrides may replace approved semantic tokens only; every override and fallback is reported.
- Font resolution uses ordered installed-font fallbacks and never silently substitutes.

## Page Families

The governed set is cover, section, agenda, executive-summary, focal-statement, big-number, text-media, cards, timeline, process, comparison, matrix, quadrant, funnel, roadmap, data-chart, table, product-showcase, case-study, team, risk-recommendation, summary, CTA, and image-story. Each family needs at least three capacity-declared variants.

Phase 23 forms such as line-chart, area-chart, composition-chart, distribution-chart, scatter-plot, KPI dashboard, modular grid, and structured content resolve through registered aliases rather than model improvisation.

## Asset Policy

Images crop to governed frames and never stretch. Icons use one declared family per deck. Every external asset requires source, license/provenance state, and intended use. Missing assets fall back to editable native composition or an explicit asset-needed finding; low-quality placeholders and unverified legacy templates are never auto-selected.
