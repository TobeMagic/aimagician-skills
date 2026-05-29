# Interview Taxonomy

Use this taxonomy to decide what the playbook should emphasize. It combines overseas big-tech interview structure, domestic Java/backend interview patterns, and AI Agent backend production topics.

Treat community 面经 as directional evidence, not as official company policy.

## Frequency Model

### P0: Almost Always Useful

- Project story and ownership: what problem, what constraints, what you owned, what tradeoff.
- System design: API shape, data model, scale, failure modes, observability, cost, reliability.
- Data/cache/MQ: MySQL/PostgreSQL indexing and transactions, Redis cache and locks, Kafka/RocketMQ semantics, idempotency, consistency.
- Java/Spring fundamentals for Java roles: collections, concurrency, JVM/GC, Spring IoC/AOP/transactions, thread pools.
- Scenario questions: seckill/coupon/order/payment/inventory, high concurrency, cache breakdown, duplicate requests, delayed processing.

### P1: Strong Differentiators

- Production readiness: deployment, health checks, logs, metrics, tracing, rollback, incident handling.
- Distributed architecture: service boundaries, retry, timeout, circuit breaking, rate limiting, eventual consistency, Saga/Outbox.
- Security: authentication, authorization, tenant isolation, resource exhaustion, sensitive data protection.
- AI backend: RAG, embedding/vector DB, MCP/Skill/tool calling, agent runtime, streaming, evals, guardrails, tracing.

### P2: Situational

- Deep JVM tuning unless the role is senior Java/infrastructure.
- Kubernetes/cloud internals unless the repo or target role includes platform/infra.
- Algorithms beyond coding screen unless targeting ByteDance/Google-style loops or fresh graduate roles.
- Framework source code beyond key mechanisms unless the role or interviewer pushes deep.

## Domestic Big-Tech Profiles

### ByteDance

Bias:

- Coding and algorithms.
- CS fundamentals: OS, network, database, concurrency.
- Project depth but often after coding/fundamentals.
- High-concurrency scenario design and practical engineering tradeoffs.

Playbook emphasis:

- Add coding-ready explanations for data structures used in the repo.
- Prepare "why this design under high traffic" and "how to degrade/retry/rate-limit".
- Keep project answers crisp; expect fast follow-ups.

### Alibaba / Ant / Alibaba Cloud

Bias:

- Project and principle depth.
- Middleware, MQ/RocketMQ, distributed transactions, cloud service architecture.
- "Technical thinking": why this design, what alternatives, where are boundaries.
- For AI/cloud roles, event-driven Agent infrastructure and real-time context are increasingly relevant.

Playbook emphasis:

- Highlight architecture decisions, consistency, data flow, and middleware choices.
- Prepare comparisons: Kafka vs RocketMQ, Redis vs DB, sync vs async, REST vs MCP, vector vs graph.

### Meituan

Bias:

- Java fundamentals, Spring, MySQL, Redis, Queue.
- Local-life business scenarios: order, coupon, inventory, merchant ranking, delivery, correctness.
- Practical distributed web systems and performance optimization.

Playbook emphasis:

- Convert each repo highlight into a business scenario.
- Prepare seckill/coupon/order-style correctness questions even if the repo is not ecommerce.
- Explain cache + DB + MQ consistency and idempotency.

### Tencent

Bias:

- Fundamentals and communication clarity.
- Networking, backend reliability, large-scale product integration.
- Go/Java/C++ depending on group; backend fundamentals remain common.

Playbook emphasis:

- Prepare OS/network/database basics and reliability stories.
- Explain how backend design supports product workflows.

### JD / Retail / Ecommerce

Bias:

- Order, inventory, payment, search, recommendation, scheduling.
- MySQL, Redis, MQ, ES, task orchestration.
- From 0-to-1 ownership and lifecycle delivery.

Playbook emphasis:

- Convert repo features into order-like lifecycle, status machine, idempotency, and reconciliation stories.
- Prepare query performance and data correctness topics.

### Huawei / Cloud / Enterprise

Bias:

- Engineering rigor, reliability, OS/network/storage fundamentals.
- Enterprise cloud, AI platform, deployment, security, compliance.

Playbook emphasis:

- Stronger focus on reliability, safety, observability, operational controls, and cloud architecture.

## AI Agent Backend Topics

Use this when the repo includes Agent, RAG, MCP, Skill, embedding, vector DB, tool calling, workflow, chat runtime, or LLM integration.

High-frequency topics:

- RAG pipeline: chunking, embedding, vector DB, hybrid search, rerank, freshness, evaluation.
- Agent runtime: loop, planning, memory, tool calling, handoff, cancellation, timeout, streaming.
- MCP/Skill/tool safety: schema, permission, resource scope, secret handling, prompt/tool injection.
- Evals: golden sets, regression evals, LLM-as-judge limits, production feedback, trace-based debugging.
- Observability: trace LLM call, tool call, handoff, guardrail, token/cost/latency.

## Source Notes

- Atlassian engineering interview guide emphasizes broad distributed engineering, coding, code design, system design, reliability, cost, and learning agility: https://www.atlassian.com/company/careers/resources/interviewing/engineering
- JavaGuide backend interview plan ranks MySQL + Redis, Java core/collections/concurrency, and framework knowledge as major backend priorities: https://javaguide.cn/interview-preparation/backend-interview-plan.html
- JavaGuide notes company differences such as Alibaba project/principle depth and ByteDance coding/fundamentals emphasis: https://javaguide.cn/interview-preparation/key-points-of-interview.html
- 小林 coding maintains a large company 面经 index covering Tencent, ByteDance, Alibaba Cloud, Meituan, JD, Baidu, Huawei and others: https://www.xiaolincoding.com/backend_interview/
- Nowcoder 2026 Java/backend + AI engineering thread lists project relevance, Java basics, Redis, RAG, Agent, Skill/OpenClaw as interview topics: https://www.nowcoder.com/discuss/864594486704291840
- Meituan official job page emphasizes Java, open-source framework internals, MySQL, NoSQL, Queue, HTTP, cache, JVM tuning, serialization, NIO, RPC, and large distributed web systems: https://waimai.meituan.com/help/job
- Alibaba Cloud MQ role description mentions RocketMQ/Kafka/EventBridge and event-driven AI Agent infrastructure / real-time AI Context: https://www.nowcoder.com/jobs/detail/436256
- AgentScope Runtime positions production Agent apps around tool sandbox isolation, Agent-as-a-Service API, scalable deployment, and observability: https://runtime.agentscope.io/zh/intro.html
- Tencent Cloud AI docs describe unified model access and Agent development with LangChain/LangGraph/CrewAI integration: https://docs.cloudbase.net/ai/introduce
- Huawei Cloud Pangu Agent platform docs emphasize workflow-style Agent construction, plugins, and custom API tools: https://support.huaweicloud.com/intl/zh-cn/usermanual-pangulm/pangulm_04_0422.html
- OpenAI Agents SDK docs emphasize tools, handoffs, streaming, tracing, and guardrails: https://platform.openai.com/docs/guides/agents-sdk/
- OpenAI evaluation docs emphasize building evals for LLM applications and Q&A over docs: https://platform.openai.com/docs/guides/evaluation-best-practices
- MCP tools specification covers tool exposure, authorization-dependent tool lists, deterministic ordering, and caching considerations: https://modelcontextprotocol.io/specification/draft/server/tools
- OWASP LLM Top 10 tracks prompt injection, sensitive information disclosure, vector/embedding weaknesses, excessive agency, and related production AI risks: https://owasp.org/www-project-top-10-for-large-language-model-applications/
