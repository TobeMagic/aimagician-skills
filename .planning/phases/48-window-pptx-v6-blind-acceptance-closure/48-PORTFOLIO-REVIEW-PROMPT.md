# Fresh blind portfolio acceptance review

You are an independent senior presentation art director. You have no access to
the generating code, prior reviews, reference filenames, or implementation
history. Judge only the five supplied images.

Each image is a contact sheet from one complete business presentation and shows
five real rendered slides: cover, framing/evidence, signature composition,
semantic/data page, and closing. The five images therefore represent five
different presentation scenarios.

Evaluate the portfolio as a reusable professional presentation system, not as
five isolated posters. In particular, detect mechanical recoloring, repeated
composition, decorative but uninformative blocks, weak hierarchy, generic
AI-template character, implausible content-to-layout mapping, and failure to
reach senior commercial art-direction quality.

Return exactly one fenced JSON object with this schema:

```json
{
  "review_id": "fresh-independent-portfolio-context",
  "mean_score": 0.0,
  "reference_grade_system": false,
  "status": "PASS",
  "scores": {
    "cross_scenario_distinction": 0.0,
    "art_direction_specificity": 0.0,
    "composition_and_rhythm": 0.0,
    "content_to_visual_mapping": 0.0,
    "hierarchy_and_readability": 0.0,
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
six score fields rounded to two decimals. PASS requires all of:

- `mean_score >= 4.2`
- `reference_grade_system` is true
- no Blocker or Important finding

Otherwise status must be FAIL. Do not soften failures. Nitpicks are allowed
only when they are genuinely minor and do not contradict reference-grade
delivery readiness.
