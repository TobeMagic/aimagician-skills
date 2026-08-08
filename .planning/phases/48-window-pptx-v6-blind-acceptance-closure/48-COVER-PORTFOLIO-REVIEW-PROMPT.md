# Fresh blind cross-scenario cover review

You are an independent senior presentation art director in a fresh context.
The five supplied images are the five real cover slides of five different
professional presentation scenarios, ordered DECK 1 through DECK 5. Judge only
the visible pixels. Do not inspect repository files, prior reviews, code, or
implementation history.

Evaluate whether the cover system achieves both family consistency and
scenario-specific art direction. Check visual identity, imagery relevance,
title hierarchy, contrast, projection readability, composition variety,
brand credibility, and whether the five covers are merely recolored copies.
Do not judge unseen body slides and do not invent missing decks: exactly five
cover images are supplied.

The dark portfolio banner, gray gutters, and `Slide NN` captions are review
metadata outside the cover frames. Do not report them as presentation content.
Composition variety is an explicit requirement: a centered launch cover, a
split technical cover, an image-led brand cover, and a typographic proposal
cover should not share identical geometry. Different compositions or
scenario-appropriate palettes are not a consistency defect when typography,
spacing discipline, and professional finish visibly form a family.

Severity must be evidence-bound. A Blocker or Important requires a concrete
visible delivery defect inside a named cover frame. Do not infer low contrast
merely because a photograph exists; identify the actual foreground text and
background area that are unreadable. A preference for one common palette,
identical cover geometry, or more/less imagery is at most a Nitpick when the
five covers remain legible and professionally related.

Return one syntactically valid JSON object only:

```json
{
  "review_id": "fresh-independent-cover-portfolio",
  "mean_score": 0.0,
  "reference_grade_system": false,
  "status": "PASS|FAIL",
  "scores": {
    "cross_scenario_distinction": 0.0,
    "scenario_image_relevance": 0.0,
    "title_hierarchy": 0.0,
    "contrast_readability": 0.0,
    "family_consistency": 0.0,
    "client_delivery_readiness": 0.0
  },
  "findings": [
    {
      "severity": "Blocker|Important|Nitpick",
      "deck": "DECK 1|DECK 2|DECK 3|DECK 4|DECK 5|portfolio",
      "issue": "specific visible issue"
    }
  ],
  "verdict": "one concise evidence-based verdict"
}
```

Use scores from 1.0 to 5.0. `mean_score` must equal the arithmetic mean of the
six fields rounded to two decimals. PASS requires mean >=4.2,
`reference_grade_system=true`, and zero Blocker/Important. Otherwise status
must be FAIL. Never return PASS with `reference_grade_system=false`, and never
set it false when the only findings are Nitpicks and the six scores describe
reference-grade delivery. A coherent shared type system is not mechanical
recoloring when imagery, composition, palette, and scenario cues are visibly
distinct.
