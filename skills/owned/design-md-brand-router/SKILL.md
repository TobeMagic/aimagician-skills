---
name: design-md-brand-router
description: |
  管理并应用品牌化 DESIGN.md 风格规范。该 skill 内置全量品牌 DESIGN.md 资产，开箱即可按品牌选择前端风格。
  当用户提到“请帮我前端风格设计”“用 Apple 风格做页面”“按某品牌做 UI”“DESIGN.md”“brand style”时必须触发。
  默认行为是从 skill 的 references 中直接选品牌文件，不使用任何下载脚本或在线更新流程。
compatibility:
  tools: [bash]
  requires: 无额外依赖
---

# Design.md Brand Router

Reference:

- `https://github.com/VoltAgent/awesome-design-md`

This skill routes brand design specifications into your project as `DESIGN.md` inputs.
It is primarily for frontend visual style decision and brand-style alignment.

## Built-in Asset Pack (No Script)

本 skill 已包含全量品牌 DESIGN.md，位于：

- `./references/design-md/*.DESIGN.md`
- `./references/brands.json`

因此日常使用不需要先联网下载，不需要脚本更新。

## 保留的交互逻辑（先确认再落地）

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

## Recommended Integration Pattern

1. 用户点名品牌（例如 `apple` / `vercel` / `stripe`）
2. 从 `./references/design-md/<brand>.DESIGN.md` 选择对应文件
3. 复制到项目根 `./DESIGN.md`
4. 前端实现阶段强制读取该 `DESIGN.md`

例子：

```bash
cp ./skills/owned/design-md-brand-router/references/design-md/apple.DESIGN.md ./DESIGN.md
```

## Guardrails

- 不要把多品牌风格盲目叠加到不可读。
- 若用户未指定，优先单品牌强一致，而不是平均混合。
- 当产品已有设计系统时，此技能只做增量对齐，不做大范围破坏式替换。
