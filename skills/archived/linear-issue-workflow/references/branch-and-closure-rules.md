# Branch And Closure Rules

## Branch Base

Resolve the repository's integration branch once per project in this order:

1. contribution and repository documentation;
2. existing project automation and branch protections;
3. GitHub's default branch and recent merged PR conventions;
4. a user decision when the evidence is absent or conflicts.

Do not infer the base from a global convention. Store the confirmed answer in the current task context or project documentation when the project chooses to do so, then reuse it for future work in that project.

## Closure Data

Use one compact Linear summary after delivery rather than a stream of progress comments:

```text
Delivery update
- PR / merge:
- verified behavior and tests:
- status:
- residual risk or follow-up:
```

Add deployment or CI facts only when they are required by the acceptance criteria, branch protection, or a discovered production risk. A reviewer bot and wiki activity record are optional unless the project explicitly mandates them.
