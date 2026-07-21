# Engineering Exploration

Use this module before designing a change in an unfamiliar area or whenever ownership, dependencies, state, or blast radius are uncertain. The goal is an objective-sized map, not a repository encyclopedia.

## Exploration Questions

Answer these from evidence:

1. Where does the user, request, command, event, or scheduled job enter?
2. Which modules own policy, orchestration, domain logic, I/O, and presentation?
3. How do data and control move through the path, including async boundaries and side effects?
4. Which contracts cross module or process boundaries: types, schemas, APIs, events, files, flags, or environment values?
5. Where is state created, transformed, cached, persisted, invalidated, and observed?
6. Which existing implementation and test patterns should the change follow?
7. What depends on the proposed change, and what can fail if its contract moves?

## Evidence-First Procedure

1. Read current planning, project docs, architecture records, wiki, and git state.
2. Locate entry points through routes, commands, package exports, event registration, manifests, or tests.
3. Trace one representative happy path end to end before cataloging variants.
4. Trace one failure or boundary path to reveal error ownership and cleanup.
5. Inspect callers and consumers in both dependency directions.
6. Read tests beside the implementation to learn observable contracts and intended seams.
7. Use history only when it resolves why a surprising constraint exists.
8. Run safe probes when static reading cannot settle runtime wiring.

For broad exploration, delegate a bounded read-only brief through `cli-agent-orchestrator`. Require concrete paths, symbols, flows, uncertainties, and likely change locations. Spot-check every claim that affects the design.

## Context Map

Use `assets/templates/engineering-context-map.md` when the map must survive the current context. Keep these sections:

- **Facts:** path, symbol, command, test, schema, or runtime evidence.
- **Flow:** numbered control path and data transformations.
- **Boundaries:** owner, input, output, side effects, errors, and stability.
- **Blast radius:** direct callers, indirect consumers, persisted data, deployments, and user workflows.
- **Unknowns:** what is missing, why it matters, and the smallest probe that resolves it.
- **Change candidates:** likely files and files that should remain untouched.

## Stop Condition

Exploration is sufficient when the agent can explain the current behavior, identify the owning boundary, predict affected contracts, name the test seams, and distinguish facts from assumptions. Stop scanning when new files no longer change those answers.

Do not infer architecture from directory names alone, list files without explaining relevance, or let delegated output replace direct verification of critical paths.
