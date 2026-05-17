# Reviewer Response and Manuscript Self-Audit Workflow

Use this workflow after receiving a manuscript review (desk reject, reject, or revision) to: (1) triage issues by severity, (2) build a structured response plan, (3) self-audit the manuscript before resubmission. This reference encodes hard-won lessons from RA-L/robotics journal review cycles.

## Triage: Classify Issues by Severity

Do not treat all reviewer comments equally. Classify every issue before responding:

| Class | Meaning | Response Strategy |
|---|---|---|
| **阻断 (Blocking)** | Would cause desk-reject or hard reject if unaddressed | Fix before anything else; must have concrete evidence |
| **实质 (Substantive)** | Weakens the paper's evidence or contribution | Address with additional experiment, analysis, or rewording |
| **格式 (Formatting)** | Stylistic, minor, or preference-based | Adjust politely if reasonable, or explain why not |
| **误解 (Misreading)** | Reviewer misunderstood the manuscript | Clarify without being condescending |
| **不可操作 (Infeasible)** | Requires impossible data or experiment | Explain constraints honestly; offer alternative evidence |

**Rule:** Always fix blocking issues first. Substantive issues need evidence. Never dismiss a substantive issue as "misunderstanding" without re-reading the manuscript carefully first.

## The 10 Most Dangerous Review Issues in Robotics/RA-L Papers

These issues appear repeatedly and cause hard rejects. Self-audit for all before submission:

### 1. Artifact Integrity (Blocking)

- [ ] PDF has a correct title on page 1
- [ ] PDF has author block or anonymous block correctly placed
- [ ] No author names, affiliations, or acknowledgments appear in the submitted PDF
- [ ] All figures are embedded (not placeholder references)
- [ ] All tables total correctly (sums match stated totals)
- [ ] Cross-references (Figure X, Table Y, Equation Z) are correct

**Why it matters:** Artifact-level issues cause desk-reject before any technical review.

### 2. Statistical Self-Consistency (Blocking)

- [ ] Every number in every figure, table, and caption matches the text
- [ ] Episode counts are internally consistent (e.g., if Table II says 212 total, no other section says 250)
- [ ] Every statistical test is reproducible from the numbers reported
- [ ] **Critical check:** If you report p = X, the paired counts or raw data must yield that exact p-value
- [ ] If you use McNemar's test, report the exact discordant pair counts (a, b, c, d table)
- [ ] If you use bootstrap, report the number of resamples and the CI width
- [ ] If results come from multiple seeds or splits, every table shows the correct N per condition

**Why it matters:** Inconsistency between text/table/figure/statistical claim signals unreliability to reviewers. A single mismatch can destroy trust in all results.

**Common trap:** Copying numbers between drafts without updating all references. Keep one master data file (CSV/JSON) and auto-generate tables from it.

### 3. Methodological Fairness (Blocking in Robotics)

- [ ] Every candidate viewpoint or action in AVS/BN is reachable through the standard action space
- [ ] No privileged simulator state (oracle position, true object location, true heading) is used in decision-making
- [ ] If any oracle/ablation uses privileged info, it is clearly labeled as "oracle ablation" and not mixed with main results
- [ ] The success criterion matches the standard definition for the task (e.g., for ObjectNav: distance < 1.0m AND oracle-visible-from-stop)
- [ ] If a custom metric is used, the standard metric is also reported

**Why it matters:** Using privileged information is the fastest way to a hard reject in robotics. Reviewers check this carefully.

### 4. Citation Integrity (Blocking)

- [ ] Every cited paper is verifiable: real arXiv ID, real DOI, real conference, real year
- [ ] No placeholder arXiv IDs (e.g., arXiv:2403.00000, arXiv:2603.26788)
- [ ] No placeholder author lists (e.g., "et al.", "and others") when actual authors are known
- [ ] Titles match the official record exactly (not paraphrased or shortened)
- [ ] Author names are spelled correctly (check BLIP-2: Li, Junnan not "H. Lee, S. Sang")
- [ ] Venue (conference/journal) is specified for every entry
- [ ] No duplicate entries for the same reference
- [ ] Use Crossref/IEEE Xplore/official proceedings, not second-hand citations

**Why it matters:** Broken citations signal poor scholarship. Reviewers spot-check references. Unverifiable citations cause rejection.

### 5. Over-Claiming in Introduction (Substantive)

- [ ] "Root cause" is used only when causal evidence is provided (not just correlation or association)
- [ ] Words like "first," "novel," "state-of-the-art," "significant" are backed by evidence
- [ ] The contribution list matches what the paper actually delivers
- [ ] Claims about zero-shot, general, universal, or any-category are qualified if only evaluated on a subset

**Safe conversion:** "root cause" → "strongly associated with"; "SOTA" → "competitive with"; "novel" → "we propose"; "significant" → "notable" or use p-values.

### 6. Evaluation Protocol Transparency (Substantive)

- [ ] Dataset, split, and episode count are specified exactly
- [ ] Paired evaluation (same episodes compared across methods) is explicitly stated with the seed
- [ ] If routing rules or hyperparameters were tuned on the same evaluation set, this is disclosed
- [ ] If the routing set was determined empirically, it is called "empirically determined on val" not presented as theory
- [ ] The evaluation protocol distinguishes between "tuning set" and "held-out evaluation set"

**Critical:** Tuning and evaluation on the same data is the most common post-hoc bias trap. Disclose it explicitly. If possible, use a nested split: tune on one subset, evaluate on a held-out subset.

### 7. Reproducibility Package (Substantive for Top Venues, Optional for Lower Tiers)

- [ ] Model versions: CLIP version, BLIP-2 checkpoint, any frozen model hashes
- [ ] Hyperparameters: all thresholds, K values, offset distances, λ weights (even if defaults are used)
- [ ] Episode IDs: exact list of scenes and episodes used
- [ ] Evaluation command and environment (GPU, Habitat version, Habitat-Matterport 3D version)
- [ ] Random seed and cuDNN settings
- [ ] If available, link to code repository or supplementary materials

**Minimum for RA-L/IROS/ICRA:** At minimum, the paper text itself must contain: dataset, split, episode count, seed, all hyperparameters, model checkpoints (by name/version), and the metric definitions.

### 8. Baseline Comparison Adequacy (Substantive)

- [ ] The comparison set includes at least one strong published baseline (not only your own ablation)
- [ ] Ablation covers each component independently
- [ ] The paper does not imply "comprehensive comparison" when only one main baseline is used
- [ ] If a method claims to improve on a category, ablation validates which component does the improvement

**Rule:** At minimum for RA-L: report VLFM baseline (the method you build on) + ablation + proposed. For stronger venues: add ApexNav, SG-Nav, LOAT, or equivalent contemporaries.

### 9. Figure and Table Caption Accuracy (Substantive)

- [ ] Every caption says exactly what the figure shows — no more, no less
- [ ] Numbers in captions match the figures
- [ ] Error bars are explained (std, CI, bootstrap, or none)
- [ ] The "shared / unique" breakdown in Venn-style figures uses exact counts
- [ ] If a figure is described as "reducing X", the numbers must show reduction

**Common trap:** Updating a figure but forgetting to update the caption. The caption is a legal document — what it says, the paper commits to.

### 10. Limitation Honesty (Substantive)

- [ ] Limitations section exists and is specific (not generic "more experiments needed")
- [ ] Every claim's limitation is stated near where it is made, not only in the conclusion
- [ ] The routing rule's generalization boundary is stated (e.g., "determined empirically on HM3D val, may not transfer")
- [ ] Statistical limitations are quantified (e.g., "p = 0.07 indicates marginal significance, larger evaluation needed")

## Self-Audit Checklist Before Resubmission

Run through this checklist before submitting:

```text
Artifact
  [ ] PDF title correct and on page 1
  [ ] Author block correct (anonymous or named per venue)
  [ ] All tables sum correctly
  [ ] All figure numbers consistent with captions

Consistency
  [ ] Every number appears in exactly one place; no copy-paste contradictions
  [ ] Episode counts: exact N reported everywhere (250 episodes? Then every table shows 250)
  [ ] p-value matches the statistical test implied by the reported counts
  [ ] Results caption mentions: N, seed, metric, and significance test

Method
  [ ] No privileged simulator state in agent decisions
  [ ] Success criterion matches Habitat/objectnav standard
  [ ] AVS/BN viewpoints reachable via standard actions only

References
  [ ] Zero placeholder arXiv IDs
  [ ] All titles match official records exactly
  [ ] All authors verified
  [ ] All venues specified
  [ ] Zero duplicate entries

Claims
  [ ] No "root cause" without causal evidence
  [ ] No "SOTA" without comprehensive comparison
  [ ] "Zero-shot" qualified if evaluation is partial
  [ ] Contribution list matches actual paper content

Reproducibility
  [ ] All hyperparameters in text or supplementary
  [ ] Model versions named
  [ ] Episode IDs (or seed) stated
  [ ] Statistical test named and applied correctly
```

## Response Structure for Revision

### Per-Comment Response Template

```markdown
### [Reviewer point number]

> [Exact quote or close paraphrase of the reviewer's comment]

**Response:**
[Answer the question directly. Do not repeat the comment back as a question.]

**Action taken:**
- What was changed in the manuscript
- Where: Section X, Page Y, Lines Z-Z
- If no change was made: why it was not changed and what evidence already supports the original claim

**Evidence added:**
- New experiments: describe setup, N, metrics, results
- New analysis: describe methodology and conclusion
- New citations: what was added and why
```

### Rules for the Response Letter

1. **Answer every point.** Even if you disagree, acknowledge the concern.
2. **Be specific about what changed.** "We revised Section III" is not enough. Say "Section III, paragraph 2, sentence 4."
3. **Do not be defensive.** "We thank the reviewer for this comment" is polite, not submissive.
4. **Do not make excuses.** Say what was wrong and what you did.
5. **Add new evidence when possible.** A new experiment beats a paragraph of explanation.
6. **If you cannot do the requested experiment,** explain constraints honestly and offer an alternative.
7. **Keep a change log.** Track every modification so you can report it accurately.

## Common Reviewer Traps and How to Handle Them

| Reviewer Pattern | Interpretation | Response |
|---|---|---|
| "Why not compare with X?" | You may be missing a key baseline | Add if feasible; explain exclusion criteria if not |
| "The improvement is small" | May be a framing problem, not a magnitude problem | Put the improvement in context; show per-category breakdown |
| "Not statistically significant" | You need a larger evaluation or narrower claim | Either run more episodes or narrow the claim |
| "Novelty is unclear" | The contribution structure is not clear | Reframe: what is the ONE thing you add that others don't |
| "Cannot reproduce" | Reproducibility package is missing | Provide episode IDs, configs, and code link |
| "References are wrong" | Citations were not checked | Rebuild the bib from official sources |
| "Method uses oracle state" | Either you did or the description is ambiguous | Clarify decision flow; add ablation separating oracle parts |
| "Same dataset for tuning and testing" | Post-hoc bias risk | Acknowledge and suggest nested evaluation as future work |

## The Single Most Important Rule

**Every number in the manuscript must come from a single source of truth (one data file or log) that you can re-run to reproduce.** Build this habit from the first experiment, not after the review arrives.

If the review says "Table II sums to 212 but you say 250 episodes everywhere," you should be able to say: "We ran `scripts/analyze_paired_results.py` with seed=42 and got these numbers." The manuscript numbers should be copy-pasted from the output of this script, not typed manually.

