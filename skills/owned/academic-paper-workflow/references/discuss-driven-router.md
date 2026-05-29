# Discuss-Driven Router

Use this when the paper state is unclear or the user wants a full workflow. Keep one live decision chain instead of dumping a generic checklist.

## State Machine

Route through these gates. Stop at the first gate that lacks enough information to act, ask the next question, and provide a concrete interim deliverable.

| Gate | Need to Know | Next Question | Output |
|---|---|---|---|
| 0. Task state | idea / literature / method / contribution / experiment / venue / submission / revision / thesis | "你现在卡在哪一环？" | route label |
| 1. Paper strategy | rapid recognition / steady publication / high-quality target / fallback-rescue | "这篇论文更偏快速认可、稳妥发表、冲高质量，还是兜底补救？" | strategy matrix |
| 2. Hard constraints | tier, deadline, budget/APC, language, recognition list | "必须满足哪个期刊/会议认定规则？" | constraint ledger |
| 3. Assets | keywords, papers, dataset, baseline, code, results, draft, reviews, thesis template | "你已有哪类材料？" | asset inventory |
| 4. Field map | task, datasets, metrics, venue patterns | "这个方向最近论文主要在哪些任务/数据/指标上发？" | field map |
| 5. Idea choice | candidate problems and execution risk | "候选 idea 里哪一个最可证、最可做、最适配目标？" | idea scorecard |
| 6. Method route | reproduce, adapt, synthesize, review/survey | "是基于 baseline 加模块，迁移方法，还是写综述/应用型论文？" | method route |
| 7. Contribution route | gap, contribution, evidence, limitation | "一句话 take-home message 是什么？" | contribution-evidence map |
| 8. Evidence route | comparison, ablation, cases, robustness | "哪个实验能支撑最核心的 claim？" | experiment plan |
| 9. Venue route | scope, indexing, recognition, speed, cost, risk | "先投哪个层级，失败后怎么降级？" | venue ladder |
| 10. Submission/revision | author guide, statements, review points | "当前是投稿前检查，还是已收到审稿意见？" | checklist/response plan |
| 11. Thesis integration | chapters, template, source papers, similarity rules | "需要整合哪些论文输出或实验结果？" | thesis integration checklist |

## Strategy Matrix

Use this to discuss publication tradeoffs clearly:

| Route | When It Fits | Requirements | Warning |
|---|---|---|---|
| Rapid recognition | hard deadline, clear requirement, limited assets | reproducible baseline, narrow claims, official venue check | avoid suspicious fast venues |
| Steady publication | moderate time, usable assets, realistic venue | clean method synthesis, fair comparisons, complete checklist | define fallback trigger early |
| High-quality target | enough time, strong assets, higher target | deeper literature, stronger comparisons, polished contribution narrative | needs fallback deadline |
| Fallback/rescue | late-stage risk, rejection, weak evidence, venue mismatch | reduce scope, repair evidence, change venue tier | preserve integrity and recognition checks |

## Discussion Style

- Ask the next missing decision, not every possible question.
- If the user provides a PDF, draft, reviews, or venue list, extract state first.
- If the user is urgent, propose a conservative route and explain the tradeoff.
- If the user asks for method packaging or manuscript positioning, translate it into method synthesis and claim-evidence design.
- End each answer with one actionable next step.

## Default Assumptions

When the user says "继续" or "你来定":

- prioritize official recognition and scope fit
- use public data and reproducible baselines
- keep claims narrow until experiments prove more
- build a fallback venue ladder early
- disclose assumptions and unresolved risks
