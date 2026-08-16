# Window-PPTX v6 realistic brief corpus

This corpus is built deterministically by
`scripts/window_pptx/project_brief_corpus.py`. It contains fifteen locked
ProjectBriefPack v1 scenarios:

- full flagships: annual work report, campus competition defense, and academic
  thesis defense;
- realistic skeletons: business/operations review, project proposal, product
  launch, market analysis, sales proposal, investor pitch, strategy planning,
  data analysis, training, brand/company introduction, project kickoff, and
  ecommerce marketing.

Each pack contains an audience, decision, presentation timing, slide budget,
cover/directory/section/body/decision/closing/appendix anatomy, source-bound
facts, mandatory asset roles, brand constraints, prohibitions, rubric, and
stable discussion lock. The skeleton label describes maturity of copy and
visual direction, not a shallow brief: every skeleton still has at least eight
quantitative facts and three required material roles.

All client and experiment data are standardized synthetic evaluation data.
Academic dataset metadata cites the public DCRNN paper at
`https://arxiv.org/abs/1707.01926`; the MDGFormer comparison, ablation,
robustness, variance, and efficiency values are explicitly labeled synthetic
experiment-log results. No corpus item is a customer fact, published-result
claim, or commercial-template license.

Materialize reviewable JSON copies outside the tracked corpus:

```bash
python skills/owned/pptx-studio/scripts/export_window_pptx_brief_corpus.py \
  --output-dir /tmp/pptx-studio-v6-briefs
```

The exporter refuses existing scenario files unless `--replace` is provided.
Exported JSON files remain locked and can be revalidated with
`manage_window_pptx_project_brief.py formal-check`.
