---
name: multilingual-diversity-loop
description: |
  使用“多语言思维采样 + 统一输出语言”的方式提升 Agent 输出多样性，减少同质化答案。
  当用户提到“提高输出多样性”“避免千篇一律”“多角度方案”“多语言思考”“creative expansion”时必须触发。
  该技能包含强制 discuss 步骤：在参数确认前，不得直接开始批量生成。
compatibility:
  tools: [bash, python]
  requires: 无强制依赖；可在任意文本任务中使用
---

# Multilingual Diversity Loop

Reference signal:

- TechWalker article: `https://www.techwalker.com/2026/0120/3177307.shtml`
- Article references arXiv preprint id: `2601.11227v1`

Core idea:

- 用不同语言进行中间推理（thought language），但最终统一为用户要求语言输出。
- 通过多语言采样和合并，提高候选方案覆盖度与差异度。

## Mandatory Discuss (Do Not Skip)

在执行前，先与用户确认以下参数并写入 `diversity-plan.md`：

1. 任务目标
   - 要提升的是“创意数量”还是“策略差异度”还是“文化视角覆盖”？
2. 输出语言
   - 最终输出语言（例如中文）。
3. 质量下限
   - 事实准确性、可执行性、风格约束是否必须保持。
4. 采样预算
   - 总候选数量、最大轮次、时间预算。
5. 语言池
   - 使用哪些思维语言；是否限定中英双语，还是多语混合。
6. 融合方式
   - 是“保留多候选并列”还是“合并成一个最终版”。

若任何一项未确认，先继续 discuss，不进入生成循环。

## Default Strategy

当用户未指定参数时，默认：

- final output language: `中文`
- language pool:
  - `zh`, `en`, `de`, `fr`, `es`, `tl`, `he`, `no`
- per-language samples: `2`
- total candidates: `16`
- keep top: `5`

## Execution Workflow

1. Baseline
   - 先做 1 份“单语言常规回答”作为基线。
2. Single-language sampling
   - 对每个思维语言独立生成多个候选，统一翻译/改写到目标输出语言。
3. Mixed-language sampling
   - 额外做一轮“语言混合思维”候选（同任务多轮不同思维语言）。
4. Diversity scoring
   - 对候选按“信息增量、方法差异、可执行性、风险”打分。
5. Merge or present
   - 用户要并列结果就输出 Top-N。
   - 用户要单一结果就输出融合稿，并附保留与舍弃理由。

## Output Contract

至少包含：

- `baseline`
- `candidate_set`
- `top_candidates`
- `final_output`
- `why_not_selected`（简短说明低分候选被淘汰原因）

## Quality Guardrails

- 不要为了多样性牺牲硬性事实正确性。
- 涉及高风险领域（医疗、法律、金融）时，把多样性用于“方案角度”，不是“事实猜测”。
- 明确区分“创意建议”与“可直接执行指令”。

## Lightweight Template

将确认参数写入 `diversity-plan.md`：

```md
# diversity-plan

objective:
output_language:
quality_floor:
budget:
language_pool:
merge_mode: [top-n | merged-single]
```
