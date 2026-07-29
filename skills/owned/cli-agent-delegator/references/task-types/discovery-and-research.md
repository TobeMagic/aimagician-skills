# Discovery, Research, And Visual Inspection

Use this task family for broad context gathering that would otherwise consume the main Agent's context window. Sources may include repositories, documents, issues, logs, APIs, schemas, cloud inventories, websites, papers, screenshots, diagrams, or other explicitly allowed material.

## Route By Need

- **Repository or system discovery:** map relevant entry points, ownership boundaries, dependencies, representative data/control flow, existing patterns, risks, likely change locations, tests, and open questions.
- **Deep web research:** search current sources, favor primary and authoritative material, record dates, distinguish evidence from inference, compare alternatives, and return citations suitable for controller verification.
- **Cross-source comparison:** use one comparison frame and expose incompatible assumptions rather than flattening differences.
- **Visual or image inspection:** use `agnes/agnes-2.0-flash`, attach the exact image with the supported OpenCode file option, and report observable evidence separately from interpretation.

Use DeepSeek V4 Flash Free for ordinary non-visual discovery and research. If DeepSeek is absent, return the live free candidates for controller selection. Use Agnes when pixels must be understood or after an explicit usage, quota, or rate-limit failure. Do not convert authentication, network, permission, syntax, or generic worker failures into an Agnes fallback. Do not send an image task to a text-only model.

## Discovery Questions

Select only objective-relevant dimensions:

1. relevant sources, files, directories, documents, endpoints, issues, or entry points;
2. current architecture and ownership;
3. key functions, classes, components, routes, schemas, hooks, tests, configs, dependencies, and integrations;
4. representative data, control, decision, or operational flow;
5. established patterns and constraints to preserve;
6. risks, edge cases, implicit coupling, migration concerns, security boundaries, and hidden assumptions;
7. likely follow-up change locations and explicit no-touch areas;
8. missing evidence and assumptions requiring controller or user confirmation;
9. viable options and a recommendation with tradeoffs;
10. validation commands or probes.

Do not ask the worker to read the whole repository without a question. Give it a relevance filter and stop condition. Broad does not mean unbounded.

## Web Research Additions

Include:

- research question and decision it will inform;
- recency requirements and current date;
- allowed domains or source classes when needed;
- required research skill;
- primary-source preference and citation format;
- conflicting evidence policy;
- claims the controller must independently verify.

The worker must not treat search snippets, generated summaries, or an uncited model statement as evidence.

## Visual Inspection Additions

Include:

- exact image paths and permission to read them;
- what to inspect: layout, text, hierarchy, state, defect, comparison, accessibility, pixel behavior, or other concrete question;
- whether OCR-like transcription is needed;
- required visual or domain skill;
- required output evidence, such as region descriptions, dimensions, or comparison table.

If an image cannot be loaded, return `NEEDS_CONTEXT`; do not infer its contents from a filename.

## Handoff

Use `../report-templates/delegation-report.md`. The controller spot-checks every claim that changes scope, architecture, risk, or implementation location, plus at least one representative flow and any “not found” claim.
