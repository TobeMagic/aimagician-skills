# Venue Selection Workflow

Use this for SCI, EI, OA, 中文核心, CCF, CSSCI, CSCD, CSTPCD, 普刊, journal/conference ranking, publication route choice, and fallback ladders.

## Hard Rules First

Do not select venues before checking:

- required recognition: SCI/SCIE, EI, 中文核心, CCF, CSSCI, CSCD, CSTPCD, school A/B/C/D, or other internal list
- whether conferences count
- whether acceptance, online publication, print publication, or indexing is required
- deadline for each milestone
- article type and language
- OA/APC budget and reimbursement
- school whitelist, blacklist, warning list, coauthor constraints, or project constraints

School or funder recognition overrides generic labels.

## Official Source Checks

Prefer primary sources and record check date.

International:

- journal/conference official website: aims/scope, article type, author guide, fees, review process
- Web of Science Master Journal List for SCIE/SSCI/AHCI indexing: `https://mjl.clarivate.com/`
- Scopus Sources for Scopus/EI-adjacent checks where relevant: `https://www.scopus.com/sources`
- DOAJ for OA journal transparency: `https://doaj.org/`
- Think. Check. Submit. for trusted-journal screening: `https://thinkchecksubmit.org/`
- publisher policy pages for ethics, AI, data, and prior-publication rules

Domestic/China-facing:

- 国家新闻出版署期刊/期刊社查询 for legal Chinese journal identity: `https://www.nppa.gov.cn/bsfw/cyjghcpcx/qkan/index.html`
- 中国科学院期刊分区表 and 国际期刊预警名单 when applicable: `https://www.fenqubiao.com/` and `https://ewl.fenqubiao.com/`; note that the CAS site states it will no longer update/release the partition table from 2026, so verify local recognition rules
- CCF official list for computer science venue recommendation: `https://www.ccf.org.cn/Academic_Evaluation/By_category/2023-03-08/787209.shtml`
- CNKI/official journal pages for Chinese journal scope and recent issues
- 北大核心, CSSCI, CSCD, CSTPCD: use the current official or institution-provided list available to the user; do not rely on random reposts
- school/department recognition files as the final authority

Use second-hand sites only as discovery aids, not final proof.

## Candidate Discovery

Find candidates from:

- venues of recent papers in the exact field
- references and citations of target papers
- target-venue accepted papers
- CNKI and official Chinese journal pages
- official indexing lists
- coauthor, lab, or project publication history if provided

Shortlist schema:

```csv
venue,kind,scope_fit,recognition_rule,indexing,level,oa,apc,review_speed,article_type,format_burden,recent_related_papers,official_check_url,risk,fallback_rank,notes
```

## Venue Labels

Common labels:

- Chinese ordinary journal
- Chinese core: 北大核心, CSSCI, CSCD, CSTPCD, and school-recognized core lists
- SCI/SCIE/SSCI/AHCI
- EI journal or EI-indexed conference proceedings
- CCF A/B/C conference or journal
- school internal A/B/C/D or equivalent
- OA journal

For computer science:

- CCF and SCI measure different things
- CCF is community recommendation by field
- SCI partition is journal-impact oriented
- schools may recognize one more than the other

## Route Choice

Fast + minimum-recognized:

- target the lowest venue level that satisfies the hard rule
- prioritize scope fit, recognition certainty, and realistic review time
- keep claims narrow and evidence clean
- avoid suspicious fast venues

Slow + high-quality:

- target higher-tier journal/conference
- strengthen baselines, ablations, robustness, and contribution framing
- set a fallback date before first submission

Fast + high-quality:

- only realistic if literature, code, data, results, and contribution framing are already strong
- select a venue whose scope fits exactly
- do not compress required evidence

Fallback/rescue:

- reduce scope or venue level
- preserve integrity and recognition checks
- revise based on evidence from rejection or desk-reject

## OA Checks

OA can be legitimate. Check:

- school recognition
- official indexing
- DOAJ or publisher transparency
- APC and payment responsibility
- warning-list status
- editorial board and peer-review description
- recent paper quality
- special issue credibility
- withdrawal policy

Fast APC review is not automatically safe.

## EI Conference Checks

Check:

- whether the institution recognizes EI conferences
- whether acceptance or actual indexing is required
- proceedings publisher
- previous indexing record
- conference history and organizer identity
- topic fit
- fees
- duplicate/predatory warning signs

Acceptance is not the same as indexing.

## Fallback Ladder

Before first submission, define:

| Rank | Venue | Why fit | Required fixes before submit | Max wait | Fallback trigger |
|---:|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

Fallback rules:

- if the paper has long-term value, drop one level at a time
- if deadline dominates, prioritize recognized and fast venues
- if reviews reveal a real flaw, fix evidence before resubmission
- if a venue is not recognized by the user's rule, do not choose it just because it is easy
