# Output Contract

Write interview playbooks under:

```text
LLM-know-how-wiki/wiki/interview/<repo_slug>/
```

Use `type: interview` when the wiki schema supports it. Otherwise use `type: digest` and add `tags: [interview, career]`.

Default behavior is discuss-first. Do not write these files during evidence scan or unconfirmed drafting. Write them only after the user confirms a highlight, page, or final playbook should be filed.

## Interactive Delivery Contract

### Stage 1: Evidence Scan Output

Use this inline format before any file writes:

```markdown
## Evidence scan

### Sources
- Wiki:
- Repo:

### Candidate highlights
| ID | Highlight | Interview value | Evidence strength | Needs confirmation |
|---|---|---|---|---|

### Recommended first highlight
<Pick one if the user asked you to choose.>

### Questions before filing
- <Only ownership/impact/target-company questions that cannot be inferred.>
```

### Stage 2: Single-Highlight Draft Output

Use this inline format for one highlight at a time:

```markdown
## Highlight Draft: <name>

### Scenario

### My design

### Code evidence
- `path/to/file`: what it proves

### Tradeoff

### Interviewer likely asks

### 30-second answer

### Deep follow-ups
1. Q:
   A:

### Basic 八股文 mapping
- Topic:
- Why this project proves it:

### Resume phrasing candidate
- <Optional bullet.>

### Do not overclaim

### File status
Not filed. Waiting for user confirmation.
```

### Stage 3: Confirmed Filing

When the user confirms a highlight:

- add or update that highlight in `technical_highlights.md`;
- add related questions to `question_bank.md`;
- add evidence rows to `evidence_map.md`;
- update overview/resume bullets only if the confirmed highlight changes them;
- update index/log if pages are created or substantially changed.

Do not file unrelated unconfirmed highlights.

## overview.md

```markdown
# Interview Overview: <repo>

## 30-second project intro
<One paragraph.>

## 2-minute project story
<Problem, context, architecture, contribution, result, tradeoff.>

## Role ownership
- Confirmed:
- Needs user confirmation:

## Architecture one-liner
<One sentence that sounds natural in an interview.>

## Most valuable talking points
| Priority | Talking point | Why it matters | Evidence |
|---|---|---|---|

## Related
- [[../../service/<repo>.md]]
- [[../../architecture/<flow>.md]]
```

## architecture_story.md

```markdown
# Architecture Story: <repo>

## Problem

## Constraints

## Design

## Data flow

## Failure modes

## Tradeoffs

## What I would improve next

## Evidence
- `path/to/file.py`
```

## technical_highlights.md

```markdown
# Technical Highlights: <repo>

## Draft status
- Confirmed highlights:
- Unconfirmed highlights are not filed here.

## Highlight: <name>

### Scenario

### Design choice

### Code evidence
- `path/to/file.py`: what it proves

### Tradeoff

### Interviewer likely asks

### 30-second answer

### Deep follow-ups
- Q:
  A:

### Basic 八股文 mapping
- Topic:
- Why this project proves it:

### Do not overclaim
```

## question_bank.md

```markdown
# Question Bank: <repo>

## Draft status
- Questions are added from confirmed highlights unless the user asks for a broad practice bank.

## Project deep dive
| Question | Answer outline | Evidence | Risk |
|---|---|---|---|

## Architecture and system design

## Data / cache / MQ

## Java / Spring / backend fundamentals

## AI Agent backend

## Security and reliability

## Company-profile questions
### ByteDance
### Alibaba / Ant
### Meituan
### Tencent
### JD / ecommerce
### Huawei / cloud
```

## resume_bullets.md

```markdown
# Resume Bullets: <repo>

## Conservative bullets
- <Truthful bullet with no invented metric.>

## Stronger bullets requiring confirmation
- <Bullet>  
  Needs confirmation: <metric/ownership/result>.

## English versions
- <Optional English bullet.>
```

## evidence_map.md

```markdown
# Evidence Map: <repo>

| Claim | Evidence path | Confidence | Notes |
|---|---|---|---|
```

Use confidence values:

- `high`: directly supported by source path.
- `medium`: synthesis from multiple source paths.
- `needs-confirmation`: ownership, metric, impact, or production behavior not proven by code/wiki.

## Log Entry

When filing into wiki:

```markdown
- YYYY-MM-DDTHH:MM:SSZ INTERVIEW_PLAYBOOK
  - sources:
    - <repo path>
    - wiki/service/<repo>.md
  - updated:
    - wiki/interview/<repo>/overview.md
    - wiki/interview/<repo>/architecture_story.md
    - wiki/interview/<repo>/technical_highlights.md
    - wiki/interview/<repo>/question_bank.md
    - wiki/interview/<repo>/resume_bullets.md
    - wiki/interview/<repo>/evidence_map.md
    - wiki/index.md
    - wiki/log.md
  - notes: Filed confirmed interview material for <repo>.
```
