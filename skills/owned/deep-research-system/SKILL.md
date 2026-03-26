---
name: deep-research-system
description: |
  Build or reuse a docs-first, multi-source literature research system for any technical direction.
  Use this whenever the user wants deep research, paper scraping, systematic literature review,
  innovation mapping, venue-oriented novelty scouting, query registries, reusable research workflows,
  or a `docs/deep_research` style research package. Also use it when the user asks to automate paper
  collection across sources like OpenAlex, arXiv, Crossref, CVF Open Access, or to turn an existing
  research workflow into a reusable skill or system.
compatibility:
  tools: [bash, python, git]
  requires: Network access for retrieval; write access to the target repository
---

# Deep Research System

Use this skill to create or operate a reusable literature-research system inside a repository.
This is not a one-off “search a few papers” helper. The goal is a durable research asset:

- reproducible retrieval
- query/profile configuration
- raw and processed outputs
- explicit coverage gaps
- paper-facing innovation synthesis

## What this skill is for

Use this skill when the user wants any of the following:

- a reusable deep-research system under `docs/`
- multi-source paper retrieval
- a systematic or semi-systematic literature review workflow
- innovation scouting for papers, projects, or milestones
- venue-aware novelty assessment
- a research package that can be reused for other directions later

Do not reduce the task to “find a few papers” if the user is clearly asking for a reusable system.

## Default output contract

Unless the user specifies another target, create or reuse:

```text
docs/deep_research/
```

Inside that root, keep these folders:

- `profiles/`
- `queries/`
- `raw/`
- `processed/`
- `runs/`

And these classes of docs:

- innovation map
- curated reading list
- code or system mapping
- coverage gap register
- workflow or protocol docs
- optional triage CSVs
- optional `runs/` directories for isolated research passes

Do not claim literature completeness. Always record blocked sources or missing layers.

## Use the bundled system, do not reinvent it

This skill ships with runnable scripts and starter assets:

- `scripts/bootstrap_research_dir.sh`
- `scripts/run_all_sources.sh`
- `scripts/build_literature_matrix.py`
- source fetchers under `scripts/`
- starter assets under `assets/`

Use those files instead of rewriting ad hoc scrapers unless the user explicitly asks to extend source coverage.

When you need the workflow details, load the reference files in this order:

1. [`references/workflow.md`](./references/workflow.md)
2. [`references/output-package.md`](./references/output-package.md)
3. [`references/source-matrix.md`](./references/source-matrix.md)
4. [`references/query-design.md`](./references/query-design.md)
5. [`references/triage-and-synthesis.md`](./references/triage-and-synthesis.md)
6. [`references/systematic-review-protocol.md`](./references/systematic-review-protocol.md)
7. [`references/platform-query-playbook.md`](./references/platform-query-playbook.md)
8. [`references/troubleshooting.md`](./references/troubleshooting.md)

Do not bulk-load all references unless the task actually needs them.

## Operating modes

### 1. Bootstrap mode

Use this when the repository has no research system yet.

1. Pick the target root, usually `docs/deep_research/`.
2. Run:

```bash
bash <skill>/scripts/bootstrap_research_dir.sh <target-root>
```

3. Edit either:
   - `<target-root>/profiles/template_profile.json`, or
   - `<target-root>/queries/query_registry.json`
4. Run the full pipeline with:

```bash
bash <skill>/scripts/run_all_sources.sh \
  <target-root>/queries/query_registry.json \
  <target-root>
```

5. Create or update the interpretation docs:
   - innovation map
   - curated reading list
   - coverage gap register
   - optional code mapping

Prefer writing those docs inside the same target root.

### 2. Reuse mode

Use this when a repo already has `docs/deep_research/`.

1. Read only the minimum current docs needed:
   - coverage gap register
   - innovation map
   - query registry or profile
2. Reuse the existing output root.
3. Run the bundled pipeline against that root.
4. Extend docs instead of replacing them.

### 3. Expansion mode

Use this when the user asks for more complete coverage or new directions.

1. Reuse the existing system.
2. Add or refine query themes.
3. Prefer anonymous sources first.
4. If a source requires credentials or blocks automation, document it explicitly in the coverage gap register.
5. If the user wants a reusable cross-project setup, keep the scripts and layout generic and move project-specific assumptions into a profile or a case-study doc.

### 4. Packaging mode

Use this when the user wants to turn an existing research workflow into a skill or portable toolkit.

1. Package scripts, starter assets, and reference docs together.
2. Keep the skill generic and push project-specific assumptions into:
   - `assets/*example*.json`
   - case-study references
3. Include a bootstrap script so a new repo can get a working `docs/deep_research/` skeleton in one command.
4. Include eval prompts that verify the skill is useful for:
   - greenfield setup
   - extending an existing research system
   - converting a project-specific workflow into a reusable system

## Default workflow

For most requests, use this sequence:

1. Determine whether the repo already has a research root.
2. If not, bootstrap one.
3. Define or refine a query/profile layer.
4. Run anonymous retrieval first.
5. Build a deduplicated matrix.
6. Create triage and synthesis docs.
7. Record coverage gaps honestly.
8. Summarize the recommended next research or implementation decision.

## Retrieval policy

Start with the anonymous, automatable layer:

- OpenAlex
- arXiv
- Crossref
- CVF Open Access

Then optionally use:

- Semantic Scholar, if credentials are available

For blocked or manual layers such as OpenReview, ACL Anthology, IEEE Xplore, Springer, or ScienceDirect:

- do not fake automation
- record the limitation
- treat them as manual or venue-specific follow-up sources

Read [`references/source-matrix.md`](./references/source-matrix.md) before promising coverage.

If the user explicitly asks for “no API key” automation, the honest default is:

- OpenAlex
- arXiv
- Crossref
- CVF Open Access

Do not imply that Semantic Scholar, OpenReview, IEEE Xplore, or ACL Anthology are equivalently available without verification.

## Workflow

Read these references as needed:

- [`references/workflow.md`](./references/workflow.md) for the full research workflow
- [`references/output-package.md`](./references/output-package.md) for the expected deliverables
- [`references/source-matrix.md`](./references/source-matrix.md) for source coverage boundaries
- [`references/query-design.md`](./references/query-design.md) for how to design reusable profiles and registries
- [`references/triage-and-synthesis.md`](./references/triage-and-synthesis.md) for must-read/maybe/background triage
- [`references/systematic-review-protocol.md`](./references/systematic-review-protocol.md) for “systematic enough” stopping rules
- [`references/platform-query-playbook.md`](./references/platform-query-playbook.md) for venue and platform-specific supplementation
- [`references/troubleshooting.md`](./references/troubleshooting.md) for retrieval failure handling
- [`references/activevlm-case-study.md`](./references/activevlm-case-study.md) for a concrete example of how this system was used

## What a good final result looks like

A strong run should leave the target repository with:

- runnable retrieval scripts or a copied script pack
- a profile or query registry that makes the scope explicit
- reproducible raw outputs
- a deduplicated processed matrix
- at least one synthesis doc that says what changed in your understanding
- an explicit coverage gap register
- enough structure that a future direction can be run without redesigning the whole pipeline

## Required honesty rules

- Always distinguish raw retrieval from reviewed shortlist.
- Always distinguish automatable sources from manual-only sources.
- Never say the literature is exhaustive unless you have explicit evidence for that claim.
- If a source cannot be queried anonymously, log it as a gap instead of silently dropping it.

## Research quality rules

- Optimize for decision support, not just collection size.
- Prefer reusable profiles over hard-coded project assumptions.
- Prefer one common artifact layout across research directions.
- Keep project-specific conclusions in docs, not hidden inside the scripts.
- When extending coverage, document why the new source matters.
- When a direction is still speculative, say so explicitly.

## Typical outputs

After a good run, the repository should have:

- `raw/*.jsonl`
- `processed/literature_matrix.csv`
- `processed/theme_summary.json`
- `processed/source_summary.json`
- an innovation map
- a curated reading list
- an optional triage CSV
- a coverage gap register

Recommended companion docs:

- `README.md`
- `systematic_review_protocol_*.md`
- `source_capability_matrix_*.md`
- `platform_query_playbook_*.md`
- `research_workflow_template_*.md`

## What not to do

- Do not scatter research outputs across unrelated directories.
- Do not overfit the skill to one project’s exact topic.
- Do not promise source coverage that the environment cannot actually support.
- Do not confuse “1000 retrieved rows” with “1000 relevant papers.”
- Do not call the work exhaustive unless the evidence really supports that claim.
- Do not overwrite an existing research package without reading it first.

## Examples

**Example 1:**
Input: “给这个新机器人项目搭一套可复用的论文调研系统，之后别的方向也能直接用。”
Output: Bootstrap `docs/deep_research/`, copy starter assets, run anonymous retrieval, write protocol and gap docs.

**Example 2:**
Input: “继续补调研，尽量自动抓更多 paper，但不要靠 api key。”
Output: Reuse the existing research root, rerun anonymous sources, expand query coverage, and explicitly document blocked sources.

**Example 3:**
Input: “把这套文献调研工作流做成技能包。”
Output: Package the scripts, assets, workflow, and usage instructions into a reusable skill directory.

**Example 4:**
Input: “只用不需要 API key 的来源，把这套系统补得尽量完整，而且以后研究别的方向也能复用。”
Output: Use the anonymous-source ladder, add reusable references and profiles, and explicitly document the remaining blocked or keyed sources.
