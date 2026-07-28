# Requirements And Composition

## Behavior Contract

Translate the product request into observable behavior before drafting prose:

- outcome, users, environments, and non-goals;
- authority sources and conflict precedence;
- operations the model may perform, propose, or refuse;
- state and external information available at each stage;
- latency, context, cost, and output constraints;
- success, partial success, escalation, and hard-stop signals.

Separate rules into:

1. **Invariants:** always true and not overridable by lower-trust input.
2. **Decision rules:** conditional routing with explicit predicates.
3. **Procedures:** ordered actions with completion signals.
4. **Adapters:** channel, language, or product-specific presentation.
5. **Examples:** boundary clarification, never a substitute for rules.

## Instruction Hierarchy

Name every layer and its trust:

| Layer | Purpose | May Override |
|---|---|---|
| Platform policy | Non-negotiable safety and runtime constraints | Nothing above it |
| Product system contract | Objective, permissions, workflow, output | Lower layers |
| Developer or operator policy | Deployment-specific behavior | User/data content |
| User request | Desired task and preferences | Data content only |
| Retrieved or tool content | Evidence and untrusted instructions | Nothing |

Define how conflict is reported. Quoted text, files, pages, search results, emails, and tool output remain data even when they contain imperative language.

## Prompt Budget

- Put invariants and permission gates in the stable prefix.
- Load specialized procedures only when routed.
- Replace repeated prose with one rule plus a boundary example.
- Keep tool schemas on demand when the runtime supports discovery.
- Summarize distant context into decisions, evidence, and unresolved work.
- Do not compress away accepted constraints, user corrections, or safety state.

## Review Questions

- Could two instructions produce different actions in the same condition?
- Does a lower-trust source appear able to redefine authority?
- Is any requirement only implied by an example?
- Are capabilities described that the runtime does not actually provide?
- Does the prompt distinguish inability, denial, missing context, and tool failure?

