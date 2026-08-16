# Advanced PowerPoint Production Handbook

Use this handbook when the task is not a simple text replacement, but a designed PowerPoint deliverable.

The goal is to make the agent behave like a production slide designer: plan the system first, build reusable modules, then verify exported visuals.

## 1. Production Principles

- Start from audience, decision, and delivery context before drawing slides.
- Use one core message per slide. Prefer an action title that states the conclusion.
- Build a repeatable visual system: theme colors, fonts, grid, spacing, master elements, and reusable components.
- Put repeated artifacts on Slide Master or Custom Layouts, not on every slide.
- Treat visual style as a controlled palette, not decoration: every color, icon, image, and animation must serve hierarchy or meaning.
- Verify with rendered PNG/PDF outputs because COM object checks cannot prove readability or polish.

## 2. Master and Layout Strategy

Use Slide Master for:

- watermark
- logo
- footer and page number
- common background texture
- recurring decorative lines or corner marks
- default title/body placeholders

Use Custom Layouts for:

- cover
- directory
- section divider
- two-column body
- chart page
- awards page
- team page
- closing page

Do not add repeated watermark text object by object to every slide. Add it to the master or a specific layout so the user can remove or disable it in one place.

Recommended watermark defaults:

- text placed on Slide Master
- low-contrast gray or brand tint
- rotation around -25 to -35 degrees
- behind readable content whenever possible
- do not cover body text
- record the master shape name in the audit log

## 3. Slide Module System

Treat a deck as modules, not individual pages:

- cover: identity, event/project name, mood
- directory: structure and navigation
- section: transition between major ideas
- body: explanation or evidence
- comparison: before/after, option A/B, pros/cons
- timeline/process: sequence and dependencies
- data-chart: one insight per chart
- awards: honor, credibility, ceremonial emphasis
- team: people, roles, contribution
- closing: final call-to-action or thanks

Every module should define:

- purpose
- input assets
- layout pattern
- visual hierarchy
- reusable components
- QA checks

## 4. Universal Layout Rules

- Use a grid. Align left edges, baselines, and image boundaries consistently.
- Leave enough negative space; crowding is the most common sign of weak PPT design.
- Use 2-3 text levels maximum: title, key sentence, supporting details.
- Use contrast intentionally: size, weight, color, spacing, or shape.
- Keep body paragraphs short. If text is long, split into cards, steps, or annotated diagram.
- Do not stretch photos or people. Crop with aspect ratio preserved.
- Use masks and gradients to improve hierarchy, but always export and inspect text readability.

## 5. Typography

Default professional typography policy:

- Chinese display title: use the user's specified display font when available.
- Chinese body: use a stable readable sans-serif such as Source Han Sans / Noto Sans CJK / Microsoft YaHei.
- English: use Arial or the template's theme font.
- Decorative title text can be rasterized or converted to image when font fidelity matters.
- Long body text should use 1.2-1.35 line spacing and avoid trailing orphan fragments.

Large two-character or short Chinese titles often look better with staggered placement, strong scale contrast, and one highlighted keyword.

## 6. Style Directions

### Government / Party Style

- Use red, gold, deep blue, and warm neutral backgrounds carefully.
- Use strong title hierarchy, ceremonial framing, ribbons, stars, subtle light rays, and policy-style grid.
- Avoid uncontrolled gradients and clutter.
- Use master-level watermark or background emblem when repeated.

### Technology Style

- Use dark navy, electric blue, cyan, silver, or black/white contrast.
- Use subtle grids, glow lines, glass panels, code/terminal motifs, circuit textures, and data cards.
- Keep neon accents sparse; one accent color is usually enough.

### Business / Consulting Style

- Use action titles.
- Show evidence in charts, tables, and structured boxes.
- Prefer precise labels over decorative icons.
- Keep chart ink low and insight labels high.

### Education / Training Style

- Use clear modules, progress indicators, examples, exercises, and summaries.
- Visual rhythm matters more than ornament.
- Directory and section pages should make navigation obvious.

### Awards / Honor Style

- Use laurel/wheat, medal, trophy, badge, certificate texture, spotlight, or stage-like framing.
- Use gold sparingly for hierarchy.
- Center the award name, recipient, issuer, date, and achievement.
- Prefer vector-like generated components or native shapes over low-resolution screenshots.

### Team Introduction

- Preserve human proportions.
- Remove backgrounds only when it improves clarity.
- Use consistent image treatment across members.
- Separate person, name, role, and contribution visually.

## 7. Data and Chart Pages

- Title states the finding, not the chart type.
- Directly label important numbers.
- Remove unnecessary gridlines, legends, and 3D effects.
- Use color to highlight the key comparison, not to decorate every series.
- Do not rely only on color; use labels or patterns when distinctions matter.
- Keep data source notes in speaker notes or footer when required.

## 8. Animation and Motion

Use motion only when it clarifies sequence, focus, or transformation.

Common safe uses:

- reveal process steps one by one
- morph between related layouts
- highlight a chart segment
- simulate carousel or reference GIF movement
- transition from overview to detail

Verification requirement:

- export a structured animation effect table
- export static PNG previews
- inspect the deck manually when the motion is central to the requirement

Do not claim completion from animation count alone.

## 9. Asset and Source Discipline

- Prefer source assets extracted from `ppt/media/*` or downloaded into `assets/downloads/`.
- Do not paste screenshots of reference slides as final work unless explicitly requested.
- Do not hotlink remote image URLs in decks.
- Keep a manifest with local path, provider, source URL, author/user, tags, and used slide/module.
- Report remaining source watermarks or low-resolution limitations.

## 10. QA Checklist

Before reporting completion:

- output deck exists
- PNG/PDF previews exist for designed slides
- master watermark is on master/layout, not repeated on each slide
- title and body text are readable
- masks do not cover important text
- people and logos are not distorted
- fonts were audited when fidelity matters
- images have traceable local paths
- animation tables exist for motion-heavy slides
- known limitations are listed

## References Used for This Handbook

- Microsoft Slide Master guidance: https://support.microsoft.com/en-gb/office/what-is-a-slide-master-in-powerpoint-b9abb2a0-7aef-4257-a14e-4329c904da54
- Microsoft watermark guidance: https://support.microsoft.com/en-us/office/add-a-watermark-to-your-slides-1246244d-f465-4e4f-b9f9-49acdae00ff1
- Microsoft PowerPoint accessibility guidance: https://support.microsoft.com/en-us/office/make-your-powerpoint-presentations-accessible-to-people-with-disabilities-6f7772b2-2f33-4bd2-8ca7-dae3b2b3ef25
- Microsoft PowerPoint VBA object model: https://learn.microsoft.com/en-us/office/vba/api/overview/powerpoint
- Duarte slide design guidance: https://www.duarte.com/blog/perfect-your-slide-design/
- Presentation Zen design fundamentals: https://presentationzen.com/blog
- Consulting action-title practice: https://slideworks.io/resources/how-to-write-action-titles-like-mckinsey
