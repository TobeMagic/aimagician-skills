TASK_ID: window-pptx-phase46-independent-blind-visual-review
ROLE: {{REVIEWER_ROLE}}
TASK_TYPE: visual blind review
MODALITY: attached images only
OBJECTIVE: Judge whether three anonymous presentation decks reach the visual
art-direction level of the attached reference deck. Each candidate is split
across two higher-resolution contact sheets so every page remains inspectable.

CONTEXT_POLICY:
- You are a fresh, independent reviewer.
- Do not inspect the repository, code, prompts, manifests, filenames, or prior
  reviews.
- Do not infer how any candidate was generated.
- Review only the seven attached contact sheets.
- R-000 is the visual-quality reference.
- B-001-A and B-001-B are the first and second halves of candidate B-001.
- B-002-A and B-002-B are the first and second halves of candidate B-002.
- B-003-A and B-003-B are the first and second halves of candidate B-003.
- Bind every observation and score to the ID printed inside that image's top
  banner; do not rely on attachment order.
- The candidates intentionally cover different presentation scenarios. A
  different palette, genre, or subject is not a defect; compare the level of
  art direction, craft, readability, and client readiness rather than visual
  similarity to R-000.
- `reference_parity` means parity with R-000's craft bar, not suitability for
  R-000's corporate subject or audience. It is a protocol error to set
  `reference_parity=false` solely because a candidate is a campus competition,
  academic defense, technical, dark, or otherwise different from R-000.
- If you cannot apply that scenario-neutral craft comparison, return NOT_RUN
  without scores. Do not invent a same-client or same-subject requirement.

IMAGE_PREFLIGHT:
- Before scoring, state one visually observable, concrete feature unique to
  R-000 and one feature from each candidate, citing its A or B sheet.
- If you cannot actually inspect all seven images, return NOT_RUN and no scores.

SCORING:
- Score every candidate from 1.0 to 5.0 on:
  1. hierarchy_readability
  2. composition_craft
  3. art_direction
  4. scenario_specific_visual_storytelling
  5. deck_rhythm
  6. asset_and_data_polish
- `reference_parity` is true only if the candidate feels plausibly directed by
  a senior presentation designer and is client-deliverable beside R-000. It
  need not copy R-000's palette or exact layouts.
- A repeated generic card/process grammar, weak visual anchoring, tiny labels,
  accidental spacing, decorative filler, or visual monotony is Important.
- Any clipping, overlap, illegible text, broken rendering, or non-deck image is
  Blocker.
- `Important` means a real client-delivery defect substantial enough to make
  `reference_parity=false` and the candidate verdict FAIL. A discretionary
  refinement that does not prevent senior-level client delivery is a Nitpick,
  not Important. Do not emit `Important` while also declaring the same
  candidate reference-grade and PASS.
- Findings must name candidate and slide number.

PASS_RULE:
- Candidate mean score must be >= 4.2.
- reference_parity must be true.
- No Blocker or Important finding.
- Overall PASS only if all three candidates pass.

OUTPUT:
Return strict JSON only:
{
  "reviewer_role": "...",
  "fresh_context": true,
  "image_preflight": {
    "R-000": "...",
    "B-001": "...",
    "B-002": "...",
    "B-003": "..."
  },
  "candidates": {
    "B-001": {
      "scores": {
        "hierarchy_readability": 0.0,
        "composition_craft": 0.0,
        "art_direction": 0.0,
        "scenario_specific_visual_storytelling": 0.0,
        "deck_rhythm": 0.0,
        "asset_and_data_polish": 0.0
      },
      "mean_score": 0.0,
      "reference_parity": false,
      "verdict": "PASS|FAIL",
      "findings": [
        {
          "severity": "Blocker|Important|Nitpick",
          "slide": 1,
          "dimension": "...",
          "evidence": "...",
          "repair": "..."
        }
      ]
    },
    "B-002": {},
    "B-003": {}
  },
  "overall_verdict": "PASS|FAIL|NOT_RUN",
  "overall_comment": "..."
}
