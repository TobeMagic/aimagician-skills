# Report Format

Use this reference for the architecture comparison report shape.

## Object Inclusion Rules

Apply these per module, not just per project:

- **Detailed**: enough repo/docs evidence exists. Include in comparison tables.
- **Brief mention**: limited but useful signal exists. Mention in supplemental notes, not the main table.
- **No material**: no useful evidence for this module. Mention once if relevant; do not include in the table.
- **Module-dependent**: decide separately for each module.

## Recommended Directory

```text
LLM-know-how-wiki/wiki/reference/<feature_slug>/
  overview.md
  00_scope_and_taxonomy.md
  01_connection_layer.md
  02_message_layer.md
  final_synthesis.md
```

Use stable lowercase slugs. Large comparisons should be split by layer instead of becoming one oversized Markdown file.

## `overview.md`

```markdown
# <Feature> Open Source Architecture Comparison

## Summary

## Research objects

| Project | Repo/docs | Role in research | Material level | Notes |
| --- | --- | --- | --- | --- |

## Deliverables

- [[00_scope_and_taxonomy.md]]
- [[01_connection_layer.md]]
- [[final_synthesis.md]]

## Current status

## Sources
```

## `00_scope_and_taxonomy.md`

````markdown
# Scope and Taxonomy

## Research question

## Decision context

## Research objects

## Inclusion rules

## Module taxonomy

```text
1. Connection layer
  1.1 IM platform adapters
  1.2 Connection protocol and keepalive
  1.3 Multi-entry unified ingress
2. Message layer
  2.1 Message ingress
  2.2 Message egress
```

## Global heatmap

| Project | 1.1 IM platform adapters | 1.2 Connection protocol and keepalive | 1.3 Multi-entry unified ingress |
| --- | --- | --- | --- |

Legend: `strong`, `partial`, `weak`, `none`, `unknown`.

## Open questions

## Sources
````

## Layer File

Each major layer file should use this structure:

```markdown
# 1. Connection Layer

## Layer summary

## Layer summary table

| Project | Overall approach | Strength | Weakness | Evidence |
| --- | --- | --- | --- | --- |

## 1.1 IM platform adapters

### Fine-grained comparison

| Project | Adapter boundary | Platform capability model | Extension mechanism | Evidence |
| --- | --- | --- | --- | --- |

### Supplemental references

- Brief/no-material project notes.
- Related patterns that do not fit the table.

### Difference summary

Synthesize the detailed table plus supplemental references.

## 1.2 Connection protocol and keepalive

...

## Transferable ideas

## Non-transferable risks

## Sources
```

## Table Rules

- Use full project names in table column or row labels.
- Include all detailed projects in fine-grained comparison tables for that module.
- Do not include no-material projects in detailed tables.
- Keep cells concise. Put long explanations under supplemental references or difference summary.
- Evidence cells should point to files, docs, commit/ref, or explicit source notes.

## Batch Delivery Rule

Deliver in this order unless the user changes it:

1. `overview.md` and `00_scope_and_taxonomy.md`.
2. First major layer, fully written.
3. Subsequent layers one by one.
4. `final_synthesis.md`.

After each major layer, ask for confirmation or adjustment before continuing unless the user explicitly asked for autonomous completion.

## Final Synthesis

```markdown
# Final Synthesis

## Executive read

## Global heatmap recap

## Best reusable patterns

## Gaps in current project

## Non-transferable parts

## License and ecosystem risks

## Architecture recommendations

## Suggested wiki follow-ups

- Potential `wiki/architecture/` updates
- Potential `wiki/decision/` records

## Sources
```

## Evidence Standard

Prefer source-backed statements:

- repo file path and line/section when practical;
- docs path or URL;
- commit/ref or tag;
- explicit "unknown from current evidence" when not found.

Avoid broad claims like "project X supports enterprise-grade messaging" unless the evidence directly supports the claim.
