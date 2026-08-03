# Output Contract

## Directory

```text
<root>/
├── PIPELINE_STATE.md
├── distillation-manifest.json
├── SOURCE_OVERVIEW.md
├── verified.md
├── rejected/
├── candidates/
├── INDEX.md
├── GLOSSARY.md
├── DIGEST.md
└── skills/
    └── <skill-id>/
        ├── SKILL.md
        ├── test-prompts.json
        └── test-results.md
```

## Manifest

```json
{
  "source": {
    "title": "",
    "creator": "",
    "published": "",
    "type": "book|article-collection|course|interview|podcast|video",
    "language": "",
    "locations": []
  },
  "status": "in_progress|validated|blocked",
  "skills": [
    {
      "id": "skill-id",
      "path": "skills/skill-id",
      "status": "draft|tested|accepted"
    }
  ]
}
```

## Generated SKILL.md

Every generated Skill contains:

1. narrow trigger description and explicit non-trigger;
2. inputs and preconditions;
3. source-grounded decision or procedure;
4. failure branches;
5. observable output contract;
6. limitations and escalation;
7. sibling routing;
8. evidence identifiers, with raw evidence kept outside the runtime prompt when possible.

## Test Prompts

```json
{
  "scenarios": [
    {
      "id": "happy-path",
      "kind": "should-trigger",
      "prompt": "",
      "expected": []
    },
    {
      "id": "sibling-confusion",
      "kind": "should-not-trigger",
      "prompt": "",
      "expected_owner": ""
    }
  ]
}
```

The result file records evaluator identity, evaluation mode, observed behavior, pass/fail, and remediation.
