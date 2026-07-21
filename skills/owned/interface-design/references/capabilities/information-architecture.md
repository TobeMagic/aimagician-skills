# Information Architecture And Content

Use this module before layout and visual styling. Good visuals cannot rescue the wrong content model or workflow.

## Workflow Model

For product surfaces, define:

- actor, goal, entry state, primary action, decision points, result, and recovery;
- navigation depth, return path, and context that must remain visible;
- permissions, destructive actions, irreversible steps, and trust cues;
- default, loading, empty, partial, error, offline, success, and stale states.

Optimize frequent work for scanning and repeated action. Keep controls near the objects they affect, preserve position through state changes, and prefer undo for reversible actions over repeated confirmation dialogs.

## Content Model

Inventory real content by type, priority, length, source, freshness, and optionality. Use representative long labels, large numbers, localization expansion, missing images, and zero-data cases while designing.

Do not add filler paragraphs, fictional metrics, synthetic social proof, or decorative labels to make a composition look full. A truthful placeholder names the missing information and preserves the intended structure without pretending it exists.

## Hierarchy

Each page or screen should answer:

1. Where am I?
2. What matters now?
3. What can I do?
4. What changed or needs attention?
5. How do I recover or go deeper?

Create hierarchy through order, grouping, scale, contrast, whitespace, and disclosure. Do not make every heading, metric, card, or section equally prominent.

## Macrostructure Selection

Read `assets/patterns/decision-rules.json` and `layout-patterns.json`. Match content and workflow signals rather than choosing a fashionable page shape.

- Trends over time: time-series chart, annotated timeline, or metric-to-detail sequence.
- Many comparable records: table, list, matrix, or catalogue with filters.
- Repeated operational action: workbench with persistent context and compact controls.
- Product explanation: product-first hero followed by mechanism, evidence, and decision path.
- Narrative or research: editorial sequence with evidence anchors.
- Sequential process: timeline, staged diagram, or progress structure.
- Competing options: comparison matrix or split contrast, not duplicated marketing cards.

Document the selected macrostructure, section or screen sequence, and responsive collapse in `assets/templates/prototype-plan.md` or the project design brief.

## Copy Discipline

Use concrete nouns and verbs. Buttons name actions; headings describe the content or decision; error messages explain what happened, what remains safe, and the next recovery action. Avoid feature narration, vague superlatives, repeated eyebrows, and instructional copy that compensates for an unclear interface.
