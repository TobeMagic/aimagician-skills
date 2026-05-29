---
name: opensource-architecture-research
description: |
  Use when the user wants deep open-source architecture comparison for a feature, subsystem, or product capability, especially when they mention open-source reference projects, architecture comparison, module taxonomy, heatmaps, horizontal comparison tables, phased delivery, or storing the result in LLM-know-how-wiki/wiki/reference. This skill is for workflows such as researching multi-agent workspace IM, agent platform architecture, chat/IM adapters, orchestration, runtime, memory, tool systems, or other engineering features across multiple repositories.
metadata:
  related_skills:
    - llm-know-how-wiki
    - deep-research-system
compatibility:
  tools: [bash, git, rg, python]
  requires: Candidate open-source repositories or docs; optional project-local LLM-know-how-wiki for storage
---

# Open Source Architecture Research

Use this skill to run a phased, evidence-backed architecture comparison across open-source projects.

This is not general web research and not normal wiki ingest. The goal is to produce a durable comparison report that helps engineering decisions while keeping open-source references separate from project facts.

## Core Rules

- Do not start the full report immediately.
- First confirm the research feature, research objects, and module taxonomy.
- Deliver in batches. Start with the global structure and the first major layer; continue only after direction and quality are accepted.
- Treat each project as module-dependent: a project can be detailed for one module and "no material" for another.
- Put cloned/reference repositories under `LLM-know-how-wiki/external_reference_repos/open_source/`.
- Put curated reports under `LLM-know-how-wiki/wiki/reference/<feature_slug>/`, not under `external_reference_repos/`.
- Do not turn open-source findings into project architecture facts unless the user explicitly asks to adopt them into `wiki/architecture/` or `wiki/decision/`.
- Every substantial conclusion should cite a repo file path, documentation path, commit/ref, or explicit source note.

## First Reads

- If a project-local wiki exists, use `llm-know-how-wiki` to resolve it and read `SCHEMA.md`, `wiki/index.md`, and relevant `wiki/reference/` pages.
- For report layout and table rules, read [`references/report-format.md`](./references/report-format.md).
- If the user needs large-scale paper/literature retrieval, use the related `deep-research-system`; otherwise keep this workflow focused on repositories, docs, and code.

## Workflow

1. **Research Setup**
   - Confirm the feature or capability being researched.
   - Clarify the decision context: architecture design, feature planning, implementation reference, or competitive/open-source scan.
   - Confirm expected depth: quick scan, medium comparison, or deep architecture comparison.
   - Confirm output root. Default: `LLM-know-how-wiki/wiki/reference/<feature_slug>/`.

2. **Research Objects**
   - Propose or accept candidate open-source projects.
   - For each object, capture repo URL, docs URL if any, local path if already cloned, license signal, and expected relevance.
   - Ask the user to confirm the final research object list before deep analysis.
   - Classify availability per object as detailed, brief mention, or module-dependent.

3. **Taxonomy Draft**
   - Draft the major layers and modules before writing content.
   - Use the user's target feature to create a tree, for example:
     ```text
     1. Connection layer
       1.1 IM platform adapters
       1.2 Connection protocol and keepalive
       1.3 Multi-entry unified ingress
     2. Message layer
       2.1 Message ingress
       2.2 Message egress
     ```
   - Discuss and revise the taxonomy until the user accepts it.

4. **Evidence Pass**
   - Inspect only the needed repo/docs paths for the current batch.
   - Capture evidence notes with project, path, module, and short finding.
   - Mark missing or weak evidence explicitly instead of filling gaps with generic claims.

5. **Batch Delivery**
   - Deliver `00_scope_and_taxonomy.md` plus the first major layer first.
   - Each layer should include a summary table, fine-grained comparison tables, supplemental reference blocks, and synthesis.
   - Stop after each major layer for review unless the user has already approved autonomous continuation.

6. **Final Synthesis**
   - Create or update `overview.md` and `final_synthesis.md`.
   - Summarize reusable ideas, non-transferable parts, license/ecosystem risks, architecture recommendations, and open questions.
   - If a finding should become a project decision, propose a separate `wiki/decision/` or `wiki/architecture/` update.

## Output Location

Default directory:

```text
LLM-know-how-wiki/wiki/reference/<feature_slug>/
  overview.md
  00_scope_and_taxonomy.md
  01_<layer_slug>.md
  02_<layer_slug>.md
  final_synthesis.md
```

Do not store report Markdown directly under `external_reference_repos/`; that area is for third-party source checkouts and manifests.

## Quality Gates

Before writing a batch:

- research objects confirmed;
- taxonomy confirmed or clearly marked draft;
- target output path confirmed;
- evidence sources available for the current layer.

Before finalizing:

- global heatmap exists;
- detailed tables include only material projects for that module;
- no-material projects are briefly mentioned outside the main table;
- major claims cite source paths;
- report separates open-source reference from project decisions;
- `wiki/index.md` and `wiki/log.md` are updated when writing into LLM wiki.

## Common Mistakes

- Writing a large final report before agreeing on taxonomy.
- Putting reports under `external_reference_repos/`.
- Treating open-source architecture as company architecture.
- Forcing every project into every table even when it has no relevant material.
- Summarizing from reputation instead of repo/docs evidence.
- Skipping license, ecosystem lock-in, or non-transferable constraints.
