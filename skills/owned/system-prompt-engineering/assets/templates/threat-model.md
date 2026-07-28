# Prompt Threat Model

## Protected Assets

- Users:
- Data:
- Systems:
- Decisions:

## Trust Boundaries

| Input or boundary | Trust | Threat | Required control | Evidence |
|---|---|---|---|---|
| User request | Task-scoped | TBD | TBD | TBD |
| Retrieved content | Untrusted data | Injection | Treat as data; isolate commands | TBD |
| Tool output | Untrusted evidence | Poisoned result | Validate result and provenance | TBD |

## High-impact Actions

| Action | Permission | Confirmation | Recovery | Audit |
|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD |

## Adversarial Cases

- Authority override.
- Secret exfiltration.
- Tool-result injection.
- Memory poisoning.
- Scope expansion.
- Encoded or indirect instruction.

