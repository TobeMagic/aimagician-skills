---
name: repo-interview-playbook
description: |
  Discuss and generate evidence-backed backend interview playbooks, 八股文, project stories, technical highlight maps, question banks, and resume bullets from a real repository plus a project-local LLM-know-how-wiki. Use this skill whenever the user asks to prepare interviews, 简历, 项目介绍, 项目亮点, Java 后端八股文, AI Agent 后端面试, "根据 repo 生成面试题", or wants to turn work repositories into next-job interview material. Default to an interactive discuss-first workflow: evidence scan, candidate highlights, one-highlight-at-a-time polishing, and only write wiki files after explicit confirmation.
metadata:
  related_skills:
    - llm-know-how-wiki
    - code-guidelines
compatibility:
  tools: [bash, python, rg, git]
  requires: Read access to the target repository; write access to the project wiki only when filing the playbook
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

- scenario / problem;
- design choice;
- code evidence;
- tradeoff;
- likely interviewer question;
- 30-second answer;
- 3-5 deep follow-ups;
- basic 八股文 mapping;
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

- update only the confirmed highlight section and supporting evidence map;
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
- `technical_highlights.md`
- `question_bank.md`
- `resume_bullets.md`
- `evidence_map.md`

Each strong highlight should include:

- problem / scenario
- design choice
- code evidence
- tradeoff
- likely interviewer question
- 30-second answer
- deeper follow-up
- basic 八股文 mapping
- boundary: what not to overclaim

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
- Sensitive values are not copied into the playbook.
- If writing into LLM wiki, update `wiki/index.md` and append `wiki/log.md`.

## Common Mistakes

- Producing generic 八股文 with no project linkage.
- Dumping a full playbook before agreeing on the strongest highlights.
- Filing unconfirmed draft material into the wiki.
- Writing "used Redis/Kafka/MySQL" without scenario, failure mode, and tradeoff.
- Turning repository dependencies into user ownership claims.
- Claiming production scale from code alone.
- Ignoring AI backend topics when the project includes Agent, RAG, MCP, embedding, workflow, or tool calling.
