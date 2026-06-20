---
name: repo-interview-playbook
description: >
  Discuss and generate evidence-backed backend interview playbooks, 八股文, project
  stories, technical highlight maps, question banks, and resume bullets from a
  real repository plus a project-local LLM-know-how-wiki. Use this skill
  whenever the user asks to prepare interviews, 简历, 项目介绍, 项目亮点, Java 后端八股文, AI
  Agent 后端面试, "根据 repo 生成面试题", or wants to turn work repositories into next-job
  interview material. Default to an interactive discuss-first workflow: evidence
  scan, candidate highlights, one-highlight-at-a-time polishing, and only write
  wiki files after explicit confirmation.
metadata:
  related_skills:
    - llm-know-how-wiki
compatibility:
  tools:
    - bash
    - python
    - rg
    - git
  requires: Read access to the target repository; write access to the project wiki
    only when filing the playbook
category: research
subcategory: repo-analysis
tags:
  - interview
  - evidence
  - repo
---

# Repo Interview Playbook

Use this skill to turn real engineering work into interview-ready material. The output should be practical: what to say, what code proves it, what interviewers will ask next, and which basic 八股文 each project highlight maps to.

This is not a generic "Java 100 questions" generator. Always start from repository and wiki evidence.

Do not default to one-shot generation. Interview material is usually better after discussion, so the default workflow is phased and conversational.

## Core Positioning

The skill compiles four layers:

1. `Project story`: what problem the repo solves, why it exists, and where the user contributed.
2. `Architecture highlights`: technical decisions, tradeoffs, and production constraints backed by code paths.
3. `Interview question bank`: likely project deep dives and follow-up 八股文.
4. `Resume bullets`: concise, truthful, impact-oriented statements.

Default output mode is Chinese, 面试战斗版.

For each substantial highlight, add a context prefix before the deep dive when it helps readability. The prefix is not a separate mode and not a rigid Part 0/1/2 template. For backend or architecture highlights, prefer a richer prefix that explains the technical stack, selection rationale and alternatives, core abstractions, data structures, key operations, and macro flow before the detailed interview story.

## Default Discuss-First Workflow

Unless the user explicitly says to generate the full playbook in one pass, use this staged workflow.

### Stage 1: Evidence Scan

Read wiki and repo evidence, then output:

- sources inspected or planned;
- current confidence level;
- 5-8 candidate interview highlights;
- what each highlight can prove in interviews;
- missing ownership, metrics, or impact details that need user confirmation.

Do not write files in this stage.

Example candidate highlights for `data-provider`:

- REST / MCP / Celery three-surface exposure.
- Provider routing layer for many cross-platform data APIs.
- FastAPI dynamic routers and Pydantic schema discipline.
- MCP tools exposed to Agent workflows.
- Neo4j + GraphQL ASIN-keyword graph querying.
- Redis / Celery async work and cache boundaries.
- Kubernetes deployment and MCP session affinity.

### Stage 2: Highlight Selection

Ask the user to choose the first 1-2 highlights to polish. If the user says "你觉得哪个合适", pick the strongest one based on:

- code evidence strength;
- interview frequency;
- relevance to target role/company;
- user's likely ownership.

Do not generate all pages yet.

### Stage 3: Single-Highlight Draft

For one selected highlight, produce only that highlight's interview material:

- context prefix when useful;
- technology selection rationale and alternatives when the highlight depends on concrete infrastructure or framework choices;
- scenario / problem;
- design choice;
- code evidence;
- tradeoff;
- interview speech pack: opening hook, 30-second answer, 2-minute walkthrough, and follow-up quick answer when useful;
- 3-5 deep follow-ups;
- basic 八股文 mapping;
- metric / claim boundary table when the user may be asked for impact, scale, latency, recall, or reliability numbers;
- "do not overclaim" boundary;
- suggested resume phrasing if useful.

Stop for user feedback after this draft. Do not move to the next highlight automatically unless the user asked for autonomous continuation.

### Stage 4: Drill And Revise

If the user wants practice, run mock interview mode for the selected highlight:

- ask one realistic interviewer question at a time;
- evaluate the user's answer;
- improve the answer with evidence and clearer tradeoffs;
- record refined phrasing only after the answer is stable.

### Stage 5: Confirmed File Output

Write to `LLM-know-how-wiki/wiki/interview/<repo_slug>/` only when the user confirms the current highlight or asks to file the playbook.

When writing incrementally:

- for substantial confirmed highlights, prefer a standalone page such as `01-<highlight_slug>.md`; keep `technical_highlights.md` as an index/summary unless the user wants a compact single-file playbook;
- update only the confirmed highlight page/section and supporting evidence map;
- update `wiki/index.md` if new interview pages are created;
- append `wiki/log.md`;
- do not file unconfirmed drafts.

## Resolve Inputs

Target repo:

1. Use the explicit repo path if the user gives one.
2. Otherwise infer from the current working directory.
3. If the current directory is the workspace root and the user names a service, find that service directory.

Wiki root:

1. Use the project-local `LLM-know-how-wiki/` if present.
2. Read `SCHEMA.md`, `wiki/index.md`, and recent `wiki/log.md`.
3. Read relevant service, architecture, API, runbook, project, and reference pages.
4. If no wiki exists, operate repo-only and tell the user the output will have lower confidence.

Default destination when writing files:

```text
LLM-know-how-wiki/wiki/interview/<repo_slug>/
```

## Evidence Workflow

1. Orient from wiki first.
2. Run or emulate the bundled collector:

   ```bash
   python <skill>/scripts/collect_repo_evidence.py <repo-path> --wiki-root <wiki-root>
   ```

3. Read only files that matter for the target repo story:
   - README and architecture docs
   - manifests and dependency files
   - server entrypoints
   - routers/controllers
   - service/provider modules
   - persistence, queue, cache, vector, graph, and agent integration code
   - deploy and observability files
4. Separate facts from packaging:
   - `Fact`: proven by source path.
   - `Inference`: reasonable synthesis from multiple facts.
   - `Needs user confirmation`: ownership, impact, metrics, incident details, or business result not in code.

Do not invent QPS, cost reduction, conversion lift, user count, or production incident history.

When using evidence hints from the collector:

- treat dependency, type, function, and pattern matches as hints, not final conclusions;
- cite source paths when naming a library, design pattern, data structure, or key operation;
- write `Unknown from current repo/wiki` when the repo evidence does not support a requested preface section.

## Interview Taxonomy

Use [`references/interview-taxonomy.md`](./references/interview-taxonomy.md) for the frequency model and domestic/overseas big-tech emphasis.

Default priority order:

1. Project story and ownership.
2. Architecture and system design.
3. Production backend: reliability, observability, deployment, failure handling.
4. Data/cache/MQ: MySQL/PostgreSQL, Redis, Kafka/RocketMQ, consistency, idempotency.
5. Java/Spring internals when the repo or target role is Java backend.
6. AI Agent backend: RAG, tool calling, MCP/Skill, evals, guardrails, tracing.
7. Security: API authorization, tenant isolation, sensitive data, prompt/tool injection.
8. Resume bullets and mock Q&A.

## Output Contract

Use [`references/output-contract.md`](./references/output-contract.md) for exact page templates.

When the user confirms filing, create or update:

- `overview.md`
- `architecture_story.md`
- `01-<highlight_slug>.md` style standalone highlight pages for major highlights when useful
- `technical_highlights.md`
- `question_bank.md`
- `resume_bullets.md`
- `evidence_map.md`

Each strong highlight should include:

- context prefix if useful for first-time readers
- technology selection rationale and alternatives
- problem / scenario
- design choice
- code evidence
- tradeoff
- interview speech pack
- deeper follow-up
- basic 八股文 mapping
- metric / claim boundary
- boundary: what not to overclaim

## Playbook Quality Pattern

Use this pattern for high-value backend/architecture playbooks. It is inspired by successful filed playbooks and strengthens the existing workflow; it does not replace the discuss-first flow.

### Standalone Highlight Pages

When a highlight can stand on its own in an interview, file it as a dedicated page:

```text
LLM-know-how-wiki/wiki/interview/<repo_slug>/01-<highlight_slug>.md
```

Use `technical_highlights.md` as a short index linking to the standalone pages, or as a compact fallback when the user asks for a small playbook.

### Context Prefix Plus

For each major highlight, include the prefix sections that are supported by repo/wiki evidence:

- technical stack and dependencies;
- technology selection rationale and alternatives, including "why not X";
- core abstractions / engineering structures;
- core data structures;
- key operation chain;
- macro flow from input to output.

If a subsection is unsupported, write `Unknown from current repo/wiki` or mark it as an inference. Do not fill gaps with generic best practices.

### Interview Speech Pack

Generate speech-ready material, not only analysis:

- opening hook for "tell me about this project";
- 30-second answer;
- 2-minute walkthrough;
- follow-up quick answer for the most likely interviewer challenge;
- resume phrasing with conservative and confirmation-needed variants.

### Question Bank Taxonomy

When producing a full `question_bank.md`, organize questions by:

- project global / architecture story;
- each confirmed highlight;
- high-frequency 八股文 direct hits;
- system design and open-ended extensions;
- code-level follow-ups;
- incident/debugging or production-risk walkthroughs;
- a final type index mapping topics to question numbers.

### Consistency Pass

Before filing or updating multiple interview pages, check for cross-document drift:

- the same technology, key name, status machine, transaction guarantee, metric, and fallback behavior must use one consistent explanation;
- anything not proven by code/wiki must be marked as inference or needs user confirmation;
- question-bank answers must not introduce new implementation claims missing from highlight pages or `evidence_map.md`;
- resume bullets must not be stronger than the confirmed evidence and metric boundaries.

## Company Profiles

When the user gives a target company, bias the question bank:

- `bytedance`: coding, algorithms, CS fundamentals, high concurrency, project depth.
- `alibaba` / `ant`: project and principle depth, middleware, distributed systems, transactions, MQ/RocketMQ, cloud architecture.
- `meituan`: Java fundamentals, MySQL/Redis/Queue, local-life/order/coupon/scenario system design, correctness under high concurrency.
- `tencent`: fundamentals, networking, large-scale service reliability, product/business integration.
- `jd`: ecommerce/order/inventory/payment scenarios, MySQL/Redis/MQ/ES, task scheduling.
- `huawei`: engineering rigor, reliability, OS/network/storage fundamentals, enterprise/cloud/AI platform thinking.
- `ai-agent-backend`: RAG, workflow, tool permission, MCP, evals, guardrails, tracing, sandboxing.

If no target is given, use `domestic-big-tech + ai-agent-backend` for Chinese interview prep.

## Quality Gates

Before filing output:

- The user has confirmed the current highlight, page, or final playbook should be written.
- Every project claim has a source path or is marked as inference.
- Every resume bullet is truthful and avoids fake metrics.
- Every question bank item ties back to either a project highlight or a high-frequency backend topic.
- Multi-page playbooks have passed a consistency pass across highlight pages, question bank, resume bullets, and evidence map.
- Metric/scale/latency/recall/reliability claims are either source-backed, user-confirmed, or phrased as safe boundaries.
- Sensitive values are not copied into the playbook.
- If writing into LLM wiki, update `wiki/index.md` and append `wiki/log.md`.

## Common Mistakes

- Producing generic 八股文 with no project linkage.
- Dumping a full playbook before agreeing on the strongest highlights.
- Filing unconfirmed draft material into the wiki.
- Forcing a rigid Part 0/1/2 outline when a lighter context prefix is enough.
- Naming design patterns, data structures, or libraries without source evidence.
- Collapsing every strong highlight into one giant `technical_highlights.md` when standalone pages would be easier to review and rehearse.
- Listing "used Redis/Kafka/ES" without explaining the rejected alternatives and why the tradeoff fits this repo.
- Writing a question bank that is only a list of questions, without answers, evidence links, topic categories, or code-level follow-ups.
- Letting the question bank, resume bullets, and highlight pages drift into different claims about the same implementation detail.
- Writing "used Redis/Kafka/MySQL" without scenario, failure mode, and tradeoff.
- Turning repository dependencies into user ownership claims.
- Claiming production scale from code alone.
- Ignoring AI backend topics when the project includes Agent, RAG, MCP, embedding, workflow, or tool calling.
