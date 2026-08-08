TASK_ID: window-pptx-phase46-independent-pair-visual-review
ROLE: {{REVIEWER_ROLE}}
TASK_TYPE: visual blind review
MODALITY: attached images only
OBJECTIVE: Judge whether anonymous candidate {{CANDIDATE_ID}} reaches the
visual art-direction and client-delivery craft level of reference R-000.

CONTEXT_POLICY:
- You are a fresh, independent reviewer.
- Do not inspect repositories, code, prompts, manifests, filenames, or prior
  reviews.
- Review only the three attached images.
- R-000 is the visual-quality reference.
- {{CANDIDATE_ID}}-A and {{CANDIDATE_ID}}-B are the first and second halves of
  one anonymous candidate deck; assess them as one complete work.
- Bind observations to the ID printed inside each image's top banner.
- The candidate may intentionally serve a different presentation scenario.
  Different palette, genre, subject, or audience is not a defect.
- `reference_parity` means parity with R-000's craft bar, not visual
  similarity or suitability for R-000's subject.
- If you cannot apply scenario-neutral comparison, return NOT_RUN without
  scores.

IMAGE_PREFLIGHT:
- Before scoring, state one concrete visible feature of R-000, one from
  {{CANDIDATE_ID}}-A, and one from {{CANDIDATE_ID}}-B.
- If you cannot inspect all three images, return NOT_RUN and no scores.

SCORING:
- Score from 1.0 to 5.0 on:
  1. hierarchy_readability
  2. composition_craft
  3. art_direction
  4. scenario_specific_visual_storytelling
  5. deck_rhythm
  6. asset_and_data_polish
- `reference_parity=true` only when the full candidate plausibly reflects
  senior presentation direction and is client-deliverable beside R-000.
- Any clipping, overlap, illegible text, broken rendering, or non-deck image
  is Blocker.
- Important means a real delivery defect substantial enough to force
  `reference_parity=false` and FAIL.
- A discretionary refinement that does not prevent delivery is Nitpick.
- Never emit Important while declaring PASS or `reference_parity=true`.
- Findings must cite an actual slide number visible in A or B.

PASS_RULE:
- mean_score >= 4.2
- reference_parity is true
- no Blocker or Important finding

OUTPUT:
Return strict JSON only:
{
  "reviewer_role": "...",
  "fresh_context": true,
  "candidate_id": "{{CANDIDATE_ID}}",
  "image_preflight": {
    "R-000": "...",
    "{{CANDIDATE_ID}}-A": "...",
    "{{CANDIDATE_ID}}-B": "..."
  },
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
  "verdict": "PASS|FAIL|NOT_RUN",
  "findings": [
    {
      "severity": "Blocker|Important|Nitpick",
      "slide": 1,
      "dimension": "...",
      "evidence": "...",
      "repair": "..."
    }
  ],
  "comment": "..."
}
