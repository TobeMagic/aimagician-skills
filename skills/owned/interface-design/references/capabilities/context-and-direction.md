# Context And Direction

Use this module at the start of a build, prototype, study, or redesign.

## Preflight Scan

Inspect before proposing style:

- product purpose, target users, routes, primary workflows, and public content;
- current screenshots at representative sizes;
- framework, component library, design tokens, CSS architecture, and icon set;
- local fonts, logos, imagery, product captures, data fixtures, and loading strategy;
- existing `DESIGN.md`, brand rules, accessibility conventions, and tests;
- recent related work so the new direction does not repeat or contradict it.

Separate facts from assumptions. If an official asset or product fact is required and not supplied, obtain it from an authoritative source or use an honest labeled placeholder. Never invent proof.

## Brief Questions

Resolve only decisions that materially change design:

1. Who is the primary user and what must they accomplish?
2. What content or state deserves first attention?
3. What should the experience feel like, and what should it avoid?
4. Which devices, environments, and accessibility level matter?
5. What is fixed: brand, framework, content, deadline, fidelity, or output format?

Record answers in `assets/templates/design-brief.md`. Begin with a junior pass: write assumptions, reasoning, and honest placeholders, show them early, and correct misunderstandings before detailed production. When the user cannot answer, infer from repository and product evidence, label assumptions, and choose conservative defaults.

## Direction Exploration

For a high-impact or open visual brief, create exactly three materially distinct, real previews at the accepted geometry before full implementation. Each preview must differ in at least four dimensions:

- macrostructure and information rhythm;
- typography role and scale;
- palette behavior and accent footprint;
- imagery, data, or product-visual treatment;
- motion grammar and interaction density.

Do not produce superficial color variants of one layout. Present a recommendation with reasons tied to audience, task, content, and implementation constraints.

Do not substitute three text descriptions for previews. Use `assets/starter/design-comparison.jsx` or equivalent source. Skip this gate only when iterating an accepted direction, preserving an established system, fixing a bounded defect, performing a mechanical export, or following an explicit one-pass instruction. Record the exemption so later agents do not reopen settled design.

## Parallel Perspective Exploration

For a broad, high-stakes brief, delegate three to six bounded perspectives through `cli-agent-orchestrator` or another authorized CLI agent. Give every perspective the same verified brief, geometry, constraints, and evaluation rubric, but assign a distinct design thesis, audience emphasis, information rhythm, or motion language. Delegates may inspect and propose; they do not change the product unless write scope is explicitly approved.

The main agent removes duplicates, rejects factually weak or infeasible work, and synthesizes exactly three real previews for user selection. Preserve the strongest mechanism from rejected perspectives in the decision record when useful. Parallel work expands the search space; it does not bypass product truth, accessibility, implementation feasibility, or the three-preview decision gate.

## Study Mode

When learning from a supplied interface, extract transferable decisions: hierarchy, grid, type roles, spacing, surface model, component anatomy, state behavior, motion, and responsive transformation. Distinguish observed facts from interpretation. Recombine the design logic for the current product; do not copy identity, proprietary content, or distinctive assets.
