# Engineering Design

Use this module after exploration and before planning a feature, refactor, performance change, migration, or architecture adjustment.

## Design Vocabulary

- **Module:** an owner of a coherent decision or capability.
- **Interface:** the smallest stable surface another module must understand.
- **Invariant:** a property that must remain true across all valid states.
- **Seam:** an observable boundary where behavior can be substituted, tested, or measured.
- **Depth:** useful behavior hidden behind a smaller interface.
- **Leverage:** how much repeated complexity one decision or abstraction removes.
- **Locality:** how few places must change to understand or modify one behavior.
- **Policy:** what the system decides; keep it separate from transport and mechanism when that separation reduces coupling.

Prefer deep modules, explicit dependency direction, and domain language shared by requirements, code, and tests. Reject an abstraction that only renames one call, predicts speculative reuse, or forces callers to know its internals.

## Design Procedure

1. Restate observable behavior and non-goals.
2. Define domain terms, states, transitions, invariants, ownership, and failure semantics.
3. Mark stable and unstable boundaries. Identify the interface each neighbor should see.
4. Choose test seams before implementation details. A seam should expose behavior without binding tests to private structure.
5. Design at least two materially different solutions when a real tradeoff exists. Vary ownership, data shape, synchronization, or migration strategy rather than names.
6. Compare options on correctness, complexity, locality, compatibility, migration, rollback, security, performance, operability, and verification cost.
7. Select the smallest design that handles accepted requirements and credible near-term change.
8. Record rejected options and the evidence that would justify revisiting them.

## Cross-Cutting Contract

For substantial changes, answer every applicable item:

- **API and compatibility:** inputs, outputs, versioning, defaults, deprecation, consumer impact.
- **Data:** schema, validation, identity, lifecycle, migration, backfill, retention, and rollback.
- **Errors:** ownership, classification, retry, idempotency, partial failure, and user-visible behavior.
- **Concurrency:** ordering, races, cancellation, locking, duplicate delivery, and consistency model.
- **Security:** trust boundary, authorization, injection, secret handling, abuse, and auditability.
- **Performance:** expected scale, critical path, budgets, measurement, caching, and degradation.
- **Operations:** configuration, feature flags, logs, metrics, traces, rollout, rollback, and support diagnosis.
- **Accessibility and UX:** state, focus, keyboard, loading, empty, failure, and recovery when user-facing.

## Test-Seam Design

Tests should fail because observable behavior is wrong. Prefer public boundaries, pure domain transitions, adapters, and deterministic clocks or ports. Avoid tests that mirror private implementation, assert that a mock returns what it was configured to return, or split one user behavior into disconnected horizontal layers with no end-to-end proof.

Use `assets/templates/engineering-design-record.md` for durable decisions. A design is ready only when its behavior, invariants, ownership, seams, migration, rollback, and evidence path are explicit enough for another engineer to implement without inventing architecture.
