# Template Library Recommendation and Intake Workflow

Use this workflow when selecting reusable slide templates from the `window-pptx` skill's built-in template library.

## Scope

V1 established the documentation and XLSX review workstation. V2 adds automated intake for the skill-local template library: scanning category PPTX files, exporting slide previews, extracting objective slide metadata, and merging AI-initial recommendation fields into the workbook `Library` sheet.

The workflow still does not run Excel macros, add workbook buttons, automatically compose final PowerPoint decks, or depend on external template folders at runtime.

## Core Decisions

- Recommendation unit: one slide, not one deck.
- Organization: one category PPTX contains 3-5 representative single-slide templates.
- Built-in category decks: `templates/template-library/reference/`.
- Generated previews: `templates/template-library/previews/`.
- Review workbook: `templates/template-library/template-library-review.xlsx`.
- Intake command: `--intake-template-library` in `scripts/window_pptx_automation.py`.
- AI-initial recommendation fields live in `Library`; no separate `AIIntake` or `AutoTags` sheet is used.
- Output: Top 5 recommendations in chat and in the workbook `Recommendations` sheet.

## V1 Categories

Allowed seed categories:

- 封面模板
- 一段内容
- 人物介绍
- 六段内容

Future categories should come from the core template taxonomy only: cover/directory/section/title/ending, content-count pages, business expression scenes, and table/chart or image-text layout classes.

Do not add these as V1 categories: 素材图片, 实用素材, 风格配色, 专题模板, 数据基座, 文本组件, 装饰形状, 优秀作品, 发布会. Images and icons belong to the asset workflows; style and component labels can be notes later, but should not pollute V1 retrieval categories.

## Built-in Sample Library

The V1 sample templates live under:

```text
templates/template-library/reference/
  封面模板.pptx
  一段内容.pptx
  人物介绍.pptx
  六段内容.pptx
```

Each PPTX is a category container. Each slide inside it is one reusable template candidate.

## Stable IDs

Use stable slide IDs independent of filename details and review notes:

```text
<category>::S###
```

Examples:

- `封面模板::S001`
- `一段内容::S001`
- `人物介绍::S001`
- `六段内容::S001`

If slide order changes later, update `SlideNo` in the workbook while preserving `TemplateID` when the template identity remains the same.

## Workbook Source of Truth

`template-library-review.xlsx` is the review and recommendation source of truth. PPTX files hold visual templates; workbook rows hold metadata, status, scores, and recommendation history.

Required sheets:

- `Library`: one row per slide template.
- `Recommendations`: Top 5 recommendation records.
- `ControlledVocabulary`: dropdown source values.
- `ChangeLog`: review and vocabulary change history.

Only rows with `ReviewStatus = 已通过` are production-ready recommendations.

## V2 Automated Intake

Run intake from native Windows PowerShell/CMD because it uses PowerPoint COM:

```powershell
py D:\Growth_up_youth\repo\skills\skills\owned\window-pptx\scripts\window_pptx_automation.py --project-dir D:\Growth_up_youth\repo\skills\skills\owned\window-pptx --intake-template-library --no-save --json
```

Default paths are derived from the skill directory:

- reference decks: `templates/template-library/reference/*.pptx`
- workbook: `templates/template-library/template-library-review.xlsx`
- previews: `templates/template-library/previews/`

The command opens each category PPTX, treats every slide as one template candidate, generates the stable ID `<Category>::S###`, exports a 1600×900 PNG preview, reads visible text and object counts, and updates the workbook `Library` sheet.

V2 writes these intake fields into `Library`:

- objective fields: `PreviewUpdatedAt`, `ShapeCount`, `ImageCount`, `TableCount`, `ChartCount`, `IngestStatus`, `IngestIssue`, `LastAutoIngestedAt`
- recommendation fields: `VisualLayoutSummary`, `MatchKeywords`, `AIRecommendationReason`, `SuggestedAdaptation`, `RequiredInputs`, `RiskNotes`, `AIQualityReason`, `AutoRecommendStatus`, `ManualLock`

Existing fields such as `ContentSlots`, `StructureTag`, `AIInitialTags`, `BestFor`, `AvoidFor`, `QualityScore`, `ReuseComplexity`, `EditabilityRisk`, and `CompositeScore` may be refreshed for unlocked rows.

Preservation rules:

- Always preserve human fields on existing rows: `HumanReviewedTags`, `ReviewStatus`, `Reviewer`, `LastReviewedDate`, and `Notes`.
- Always preserve usage and outcome fields such as use counts, selected/final-used counts, rates, and feedback.
- If `ManualLock` is `yes`, `是`, `true`, `1`, or `locked`, refresh only objective fields and preview timestamps; do not overwrite AI/recommendation fields.
- Successful intake defaults to `AutoRecommendStatus = AutoRecommendable`; per-slide issues use `NeedsReview` and record the issue in `RiskNotes` / `IngestIssue`.

The V2 script generates deterministic AI-initial metadata from category, extracted text, object counts, and preview paths. It does not perform full pixel-level visual reasoning inside the script; use preview PNGs for human or future multimodal review.

## Human Review

For each template row, the reviewer confirms:

- category
- structure tag
- human-reviewed tags
- best-fit and avoid-fit notes
- quality score
- reuse complexity
- editability risk
- review status

AI-generated tags stay in `AIInitialTags` until a human writes approved values into `HumanReviewedTags` and marks the row `已通过`.

## Recommendation Method

Filter and score candidates with content-first logic:

1. Match requested category/content structure.
2. Prefer rows with `ReviewStatus = 已通过`.
3. Rank by category fit, structure fit, human score, reuse simplicity, and prior usage success.
4. Exclude `停用` rows.
5. If fewer than five reviewed candidates exist, state the smaller available count.

Suggested scoring:

| Dimension | Weight |
|---|---:|
| Core category match | 40 |
| Content/structure match | 25 |
| Page-role match | 15 |
| Human quality score | 10 |
| Lightweight usage feedback | 10 |

## Chat Output Format

Use a concise decision-oriented format:

```text
需求解析：
- 核心分类：一段内容
- 内容结构：单段正文

Top 推荐：
1. 一段内容.pptx / 第 1 页 / score 86
   原因：核心分类和单段正文结构匹配。
   改造：替换标题和正文，统一当前 deck 主色。
   风险：正文超过 120 字时版面可能偏挤。
```

Each candidate should include source, score, reason, one-sentence adaptation, and one caveat.

## Workbook Output

Record the same recommendation set in the workbook `Recommendations` sheet with `RequestID`, request text, rank, score, template ID, source PPTX, slide number, match reason, adaptation suggestion, caveats, selected status, final used status, and user feedback.

## V1 Validation Prompts

- “帮我找一个封面页模板。” → should recommend `封面模板::S001` first.
- “我要做一页只有一段正文的介绍页。” → should recommend `一段内容::S001` first.
- “我要做一页个人介绍/人物介绍。” → should recommend `人物介绍::S001` first.
- “我要做一页 6 个要点/6 个模块的内容页。” → should recommend `六段内容::S001` first.

If the user asks for Top 5 while only four reviewed templates exist, say that only four reviewed candidates are currently available.
