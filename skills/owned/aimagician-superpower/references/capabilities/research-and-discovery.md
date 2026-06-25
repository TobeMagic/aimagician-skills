# Research And Discovery

Use this module before planning when implementation depends on existing code, external APIs, packages, current behavior, unknown architecture, or uncertain requirements.

## Local Discovery

Start with local evidence:

- repository structure;
- README and docs;
- tests and fixtures;
- config files;
- schemas and generated types;
- command surfaces and scripts;
- previous planning artifacts;
- recent commits if they explain current behavior.

Map only the code needed for the current objective. Avoid broad cataloging when a narrow path is enough.

## Research Triggers

Use web research when information may have changed or is external to the repo:

- package behavior or versions;
- third-party API behavior;
- browser, cloud, platform, or CLI rules;
- legal, financial, medical, or security-sensitive facts;
- product recommendations or cost tradeoffs;
- current documentation needed for correctness.

Prefer primary documentation, source repositories, release notes, or official standards for technical claims.

## Discovery Outputs

Capture research as planning input:

- facts confirmed locally;
- facts confirmed externally;
- assumptions;
- unknowns;
- credible approaches;
- dependency and compatibility checks;
- risks and mitigations;
- recommendation.

Separate facts from inference. If evidence is inconclusive, say what was checked and choose the safest next step or ask for the targeted decision.

## Codebase Mapping

When mapping code:

1. Identify entry points and user-facing flows.
2. Trace data flow and side effects.
3. Locate existing helpers, patterns, and tests.
4. Identify ownership boundaries and files that must not be touched.
5. Note integration points, environment variables, generated assets, and hidden state.

## Dependency Checks

Before adopting or changing a dependency, verify:

- it exists and supports the target runtime;
- license and install method are acceptable for the repo;
- type definitions or SDK support are adequate;
- maintenance status is acceptable;
- it does not duplicate an existing local solution;
- verification can prove the integration works.
