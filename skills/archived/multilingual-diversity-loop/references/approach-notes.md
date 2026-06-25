# Multilingual Diversity Approach Notes

This note captures the distilled operational idea from:

- `https://www.techwalker.com/2026/0120/3177307.shtml`

Article-level takeaways used by this skill:

1. Different thought languages can induce different reasoning paths.
2. Language distance from English was reported to correlate with output diversity in that article summary.
3. Mixed-language sampling can outperform single-language repeated sampling in diversity coverage.
4. The practical workflow does not require model retraining, only inference-time prompting strategy changes.

Engineering interpretation for this repo:

- Treat the method as an inference-time ensemble strategy.
- Keep final user-facing language fixed.
- Use multi-candidate scoring to avoid quality collapse.

Known limitations:

- This is a prompting strategy, not a guarantee of novelty quality.
- Domain correctness constraints still dominate in high-stakes tasks.
- Language choice may have uneven effect across models.
