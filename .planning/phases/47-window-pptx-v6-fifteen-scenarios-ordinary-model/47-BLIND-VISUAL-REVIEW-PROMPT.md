# Independent blind visual review

You are the sole reviewer in a fresh context. Review only the supplied visual
evidence. Do not inspect repository implementation, planning reports, source
code, prior reviews, filenames outside the visual report, or other candidates.

The first image is the fixed supplied customer reference. The second image is
one anonymous complete candidate deck contact sheet. Judge whether the
candidate reaches the reference's art-direction discipline while remaining
appropriate for its own visible business scenario. Do not require identical
colors or motifs.

Inspect every candidate slide. Score from 1.0 to 5.0:

- narrative and complete-deck anatomy;
- art direction and scenario specificity;
- hierarchy, typography, spacing, and readability;
- composition variety and cross-page rhythm;
- data/table/diagram appropriateness;
- consistency and customer-delivery readiness.

Look specifically for missing cover/directory/section/decision/appendix/closing
anatomy, mechanical recoloring, one repeated layout sequence, generic cards,
weak or decorative-only scenario visuals, overflow, tiny text, collisions,
poor contrast, raw placeholders, distorted images, or inconsistent style.

Severity:

- Blocker: unusable, materially misleading, broken, or clearly not
  customer-deliverable.
- Important: visible professional-quality gap that requires another
  iteration.
- Nitpick: bounded polish issue.

PASS requires mean score at least 4.2, reference-parity true, and zero Blocker
or Important. Output one JSON object only:

```json
{
  "review_id": "fresh-independent-context",
  "mean_score": 0.0,
  "reference_parity": false,
  "status": "PASS|FAIL",
  "scores": {
    "narrative_anatomy": 0.0,
    "art_direction_specificity": 0.0,
    "hierarchy_readability": 0.0,
    "composition_rhythm": 0.0,
    "data_diagram_fitness": 0.0,
    "delivery_readiness": 0.0
  },
  "findings": [
    {"severity": "Blocker|Important|Nitpick", "slide": "number or unknown", "issue": "specific visible issue"}
  ],
  "verdict": "one concise sentence"
}
```
