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

### Context prefix
Use this section when it helps first-time readers. Keep it evidence-backed and flexible.

#### Technical stack and dependencies
- Language/runtime:
- Frameworks/libraries:
- Build/deploy:

#### Technology selection and alternatives
| Decision | Selected | Alternatives rejected | Why acceptable |
|---|---|---|---|

#### Core abstractions / engineering structures
- <Only name patterns or abstractions supported by source evidence.>

#### Core data structures
- <Types, models, state objects, context/config objects.>

#### Key operations
- <Entrypoints and cross-module operations such as route, dispatch, execute, persist, validate, compact, sync.>

#### Macro flow
<Short prose or ASCII flow from input to output.>

### Scenario

### My design

### Interview speech pack
#### Opening hook

#### 30-second version

#### 2-minute walkthrough

#### Follow-up quick answer

### Code evidence
- `path/to/file`: what it proves

### Tradeoff

### Interviewer likely asks

### Follow-up quick answer

### Deep follow-ups
1. Q:
   A:

### Basic 八股文 mapping
- Topic:
- Why this project proves it:

### Resume phrasing candidate
- <Optional bullet.>

### Metric / claim boundary
| Interviewer asks | Safe answer |
|---|---|

### Do not overclaim

### File status
Not filed. Waiting for user confirmation.
```

If a context subsection is unsupported by the current repo/wiki, write `Unknown from current repo/wiki` instead of guessing. The section is a readability prefix, not a mandatory rigid outline.

### Stage 3: Confirmed Filing

When the user confirms a highlight:

- for substantial highlights, add or update a standalone page named `01-<highlight_slug>.md`, `02-<highlight_slug>.md`, etc.;
- keep `technical_highlights.md` as a compact index/summary linking to standalone pages unless the user requested a single-file playbook;
- add related questions to `question_bank.md`;
- add evidence rows to `evidence_map.md`;
- update overview/resume bullets only if the confirmed highlight changes them;
- update index/log if pages are created or substantially changed.

Do not file unrelated unconfirmed highlights.

Before writing multiple pages, perform a consistency pass: repeated claims about technologies, key names, state transitions, transaction guarantees, fallbacks, metrics, and known weaknesses must match across highlight pages, question bank, resume bullets, and evidence map.

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

## Highlights index
| ID | Highlight | Why it matters | Page | Evidence strength |
|---|---|---|---|---|

## Highlight: <name>

Use this inline section only for compact playbooks. For substantial highlights, create a standalone page with the template below and link it from `Highlights index`.
```

## Standalone highlight page: `01-<highlight_slug>.md`

````markdown
# Highlight <n>: <name>

### Context prefix

#### Technical stack and dependencies
| Layer | Technology | Purpose | Evidence |
|---|---|---|---|

#### Technology selection and alternatives
| Decision | Selected | Alternatives rejected | Why acceptable | Would choose again? |
|---|---|---|---|---|

##### <Selected technology or design>
<Short evidence-backed rationale. Include "why not X" for 2-3 realistic alternatives when evidence and repo context support it.>

#### Core abstractions / engineering structures
- <Abstraction or pattern>: <what it does> (`path:line`)

#### Core data structures
- <Type/model/state/config object>: <what it carries> (`path:line`)

#### Key operation chain
```text
<operationA>() -> <operationB>() -> <operationC>() -> <result>
```

## Interview speech pack

### Opening hook
<How to introduce this highlight when the interviewer says "tell me about your project".>

### 30-second version
<Concise answer.>

### 2-minute walkthrough
<Longer narrative with scenario, design, and tradeoff.>

## Macro flow
```text
<Input> -> <service/component> -> <data store/queue/API> -> <output>
```

### Scenario

### Design choice

### Code evidence
| File | Lines | Proves |
|---|---|---|

### Tradeoff
| Decision | Chose | Gave up | Why acceptable |
|---|---|---|---|

### Interviewer likely asks

### Follow-up quick answer

### Deep follow-ups
- Q:
  A:

### Basic 八股文 mapping
| Topic | Project proof |
|---|---|

### Resume phrasing

#### Conservative version
- <Safe bullet.>

#### Stronger version requiring confirmation
- <Bullet with impact/scale phrasing.>
  Needs confirmation: <metric/ownership/result>.

### Metric / claim boundary
| Interviewer asks | Safe answer |
|---|---|

### Do not overclaim
- <Claim that is unsafe and why.>

### File status
Draft / Active / Confirmed
````

## question_bank.md

```markdown
# Question Bank: <repo>

## Draft status
- Questions are added from confirmed highlights unless the user asks for a broad practice bank.

## 1. Project global / architecture story
### Q1: <Question>
> <Speech-ready answer.>

## 2. Highlight deep dives
### <Highlight name>
### Q<n>: <Question>
> <Answer grounded in the highlight page and evidence map.>

## 3. High-frequency 八股文 direct hits
### Q<n>: <Question>
> <Answer that connects the CS/backend concept to this repo.>

## 4. System design and open-ended extensions

## 5. Code-level follow-ups

## 6. Incident / debugging / production-risk walkthroughs

## Topic index
| Topic | Question numbers |
|---|---|

## Company-profile questions
Only include these when useful for the user's target company.

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

## Metric statement boundary
| Asked about | Safe phrasing |
|---|---|

## English versions
- <Optional English bullet.>
```

## evidence_map.md

```markdown
# Evidence Map: <repo>

| Claim | Evidence path | Confidence | Notes |
|---|---|---|---|

## Highlight coverage
| Highlight | Evidence file | Lines | Proves |
|---|---|---|---|

## Topic coverage
| Interview topic | Highlight evidence | Question bank coverage |
|---|---|---|
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
