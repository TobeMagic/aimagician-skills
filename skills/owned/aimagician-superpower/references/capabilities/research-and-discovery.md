# Research And Discovery

Use this module when planning depends on existing implementation, external APIs, packages, current platform behavior, unknown architecture, or unresolved domain facts.

## Evidence Order

Start with local source-of-truth evidence:

- planning artifacts, docs, wiki, ADRs, and recent summaries;
- entry points, tests, fixtures, configs, schemas, and generated types;
- relevant history when it explains current behavior;
- runtime probes that are safe and non-mutating.

Browse current primary sources when package behavior, third-party APIs, platforms, standards, costs, security guidance, or other unstable facts affect correctness.

## Exploration Depth

- Inspect one or two known files directly.
- For broad codebase, document corpus, dependency, architecture, or data-flow exploration, delegate through `cli-agent-orchestrator` when available.
- Give the delegated agent an objective, allowed and forbidden scope, read-only rule, required output structure, and concrete questions.
- Keep the main agent responsible for spot-checking critical claims and reconciling the report with local evidence.

## Code And System Mapping

Map only what the objective needs:

1. user-facing entry and command or request path;
2. key modules, functions, services, schemas, routes, hooks, and tests;
3. control flow, data flow, side effects, external calls, and persisted state;
4. ownership boundaries and existing patterns to preserve;
5. error paths, concurrency, security, compatibility, and migration risks;
6. likely files to change and files that must remain untouched.

## Approach Research

Generate at least two credible approaches when a meaningful tradeoff exists. Compare user fit, complexity, maintainability, compatibility, migration, verification cost, rollback, and residual risk. Do not generate fake alternatives where one option is plainly invalid.

Before adopting a dependency, verify existence, supported runtime, current API, license, maintenance, types, install impact, overlap with existing helpers, and a feasible test path.

## Research Output

Record:

- confirmed local facts with paths;
- confirmed external facts with sources;
- inference separated from fact;
- unresolved unknowns;
- alternatives and tradeoffs;
- dependency and compatibility findings;
- risks and mitigations;
- recommendation and assumptions to re-discuss.

Research ends when enough evidence exists to lock requirements and implementation assumptions. It must not drift into unapproved implementation.
