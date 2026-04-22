---
name: design-md-brand-router
description: |
  管理并应用品牌化 DESIGN.md 风格规范，支持从 awesome-design-md 对应品牌源批量或按需拉取 DESIGN.md，并用于指导项目 UI 产出。
  当用户提到 DESIGN.md、brand style、品牌化 UI、按某公司风格出界面、选择多个品牌融合时必须触发。
  该技能包含强制 discuss：先确定品牌和融合策略，再落地文件。
compatibility:
  tools: [bash, python]
  requires: Python 3
---

# Design.md Brand Router

Reference:

- `https://github.com/VoltAgent/awesome-design-md`

This skill routes brand design specifications into your project as `DESIGN.md` inputs.

## Mandatory Discuss (Do Not Skip)

执行前先和用户确认：

1. 目标品牌
   - 单品牌还是多品牌混合？
2. 落地方式
   - 覆盖根目录 `./DESIGN.md` 还是保存到目录做候选集？
3. 融合策略
   - 主品牌 + 辅助品牌，还是多品牌平权拼合？
4. 输出目标
   - 落地页、后台、组件库、营销页，优先哪个场景？
5. 约束项
   - 字体可替换范围、动效强度、响应式优先级、品牌禁用色。

未确认前，不要直接覆盖已有 `DESIGN.md`。

## Available Brand Catalog

Brand ids are maintained in:

- `./assets/brands.json`

Use script for discovery:

```bash
python ~/.codex/skills/design-md-brand-router/scripts/fetch_design_md.py --list
```

## Fetch Commands

Single brand to project root:

```bash
python ~/.codex/skills/design-md-brand-router/scripts/fetch_design_md.py \
  --brand claude \
  --output ./DESIGN.md
```

Single brand to custom file:

```bash
python ~/.codex/skills/design-md-brand-router/scripts/fetch_design_md.py \
  --brand cursor \
  --output ./design/brands/cursor.DESIGN.md
```

Multiple brands to directory:

```bash
python ~/.codex/skills/design-md-brand-router/scripts/fetch_design_md.py \
  --brand claude \
  --brand vercel \
  --brand stripe \
  --dest-dir ./design/brands
```

Fetch all known brands:

```bash
python ~/.codex/skills/design-md-brand-router/scripts/fetch_design_md.py \
  --all \
  --dest-dir ./design/brands
```

Preview without download:

```bash
python ~/.codex/skills/design-md-brand-router/scripts/fetch_design_md.py \
  --brand claude \
  --brand cursor \
  --dry-run
```

## Recommended Integration Pattern

1. 拉取候选品牌文件到 `./design/brands/`
2. 和用户确认主品牌与辅品牌
3. 生成最终 `./DESIGN.md`（可只保留一份最终版）
4. 再让前端生成任务读取该 `DESIGN.md`

## Guardrails

- 不要把多品牌风格盲目叠加到不可读。
- 若用户未指定，优先单品牌强一致，而不是平均混合。
- 当产品已有设计系统时，此技能只做增量对齐，不做大范围破坏式替换。
