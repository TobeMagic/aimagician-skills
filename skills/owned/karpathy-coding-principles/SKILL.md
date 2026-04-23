---
name: karpathy-coding-principles
description: |
  用 Karpathy 风格的四条工程原则执行编码任务：Think Before Coding、Simplicity First、Surgical Changes、Goal-Driven Execution。
  当用户要求“先想清楚再改代码”“最小改动修问题”“不要过度工程化”“测试驱动达成目标”时触发。
  适用于需求实现、缺陷修复、重构约束、评审整改。
compatibility:
  tools: [bash, git]
  requires: 建议有可运行测试或可验证命令
---

# Karpathy Coding Principles

Reference:

- `https://github.com/forrestchang/andrej-karpathy-skills`

## The 4 Principles

1. Think Before Coding
   - 先写清楚假设、歧义、约束、tradeoff。
   - 若存在关键不确定项，先对齐再改代码。
2. Simplicity First
   - 优先最小可行实现（MVP implementation）。
   - 不做预支抽象，不提前引入复杂配置层。
3. Surgical Changes
   - 修改旧代码时只动必要行。
   - 不顺手做无关重构、格式化、风格迁移。
4. Goal-Driven Execution
   - 将“做 X”改写为“可验证目标”。
   - 最佳实践是先写复现测试，再让测试通过。

## Execution Loop

1. 定义目标
   - 写出验收标准：输入、输出、边界、失败条件。
2. 建立证据
   - 添加或运行复现用例，确认当前失败点。
3. 最小改动实现
   - 只改当前问题需要的代码路径。
4. 验证
   - 运行测试或验证命令，记录结果。
5. 收口
   - 若通过，保留改动并总结。
   - 若不通过，继续小步迭代，不扩大修改面。

## Change Boundaries

- 优先单一职责的补丁，不混入 unrelated cleanup。
- 每次改动必须解释“为什么这几行足够解决问题”。
- 如果必须扩大改动范围，先给出技术理由再执行。

## Output Contract

每次交付至少包括：

- 目标与约束（本次解决什么，不解决什么）
- 关键改动说明（最小必要改动）
- 验证结果（跑了什么命令，结果如何）

## Anti-patterns

- 还没确认需求就开始写代码。
- 为“未来可能需求”做大抽象。
- 小问题触发大面积重构。
- 没有验证闭环，仅凭主观判断“应该好了”。

## Companion Notes

详细执行清单见：

- `./references/principles-checklist.md`
