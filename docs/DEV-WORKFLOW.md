# Legacy Skillbee V2 开发工作流

> Legacy note: this workflow is retained for v2 history. Current milestone execution uses Skillbird / `aimagician_superpower` planning under `.planning/` and the root `README.md`.
>
> 本文档定义基于 GSD 的历史开发流程、验收标准和进度管理规则。
> v2 历史功能迭代以 [PRD.md](./PRD.md) 为参照。

---

## 1. Milestone 管理

### Milestone: v2.0

基于 PRD 的 10 个 Feature，拆分为 5 个 Phase：

| Phase | 聚焦 | 对应 PRD Feature |
|-------|------|-----------------|
| 1 | 数据模型与配置基建 | F4 (数据层), F5 (持久化), F9 (archive) |
| 2 | TUI 品牌重塑 | F1 (蜜蜂主题), F8 (详情面板) |
| 3 | 多选与筛选 | F2 (多 target 选择), F6 (多维筛选) |
| 4 | 批量操作与报告 | F3 (批量安装/卸载), F10 (安装报告) |
| 5 | 概览与打磨 | F7 (安装概览), P2 (多主题) |

### 执行顺序

严格按 Phase 1 → 2 → 3 → 4 → 5 顺序执行，每个 Phase 依赖前置 Phase 完成。

---

## 2. 每个 Phase 的执行流程

采用 **Batch 模式** — 一个 Phase 一次性做完，中间不中断。

### 2.1 启动前

1. 确认当前 Phase 的前置 Phase 已完成
2. 确认 `.planning/STATE.md` 中的 `current_phase` 正确

### 2.2 执行过程

```
Step 1: 回顾 PRD Feature 定义
        → 确认本 Phase 涉及的所有 Feature 的验收标准

Step 2: 阅读相关源码
        → 了解需要修改的接口和数据模型

Step 3: 实现
        → 按依赖顺序逐个实现 Feature

Step 4: 验证
        → npm test (测试全部通过)
        → npm run build (构建无错误)
        → 对照 PRD 验收标准逐条检查
```

### 2.3 完成后

1. 更新 `.planning/STATE.md` — 更新 `current_phase`、`last_activity`、`progress`
2. 更新 `.planning/ROADMAP.md` — 标记 Phase 完成
3. 如需更新 `.planning/REQUIREMENTS.md` — 添加新的 requirement ID 并映射

---

## 3. 验收标准

每个 Task/Phase 完成后必须满足**标准三件套**：

| # | 检查项 | 命令 | 说明 |
|---|--------|------|------|
| 1 | PRD 验收条款 | 人工对照 | 该 Phase 涉及的所有 PRD Feature 验收标准逐条通过 |
| 2 | 测试通过 | `npm test` | 所有 tests pass，不破坏现有测试 |
| 3 | 构建通过 | `npm run build` | TypeScript 编译无错误 |

---

## 4. 进度跟踪

- **Phase 级更新**：每个 Phase 开始前和完成后各更新一次
- **STATE.md**：记录 `current_phase`、`last_activity`、关键决策
- **PRD.md**：Feature 完成后标记 `[x]` 状态

---

## 5. 分支策略

- 每个 Phase 在一个独立的分支上开发
- 命名规则：`v2-phase-<N>-<short-name>`
- 完成验证后合并到主分支

---

## 6. 变更管理

- **PRD 变更**：如需修改 PRD Feature 定义，必须先讨论确认再改
- **Scope 变更**：新增功能需评估是否纳入当前 Phase 或推迟到后续 Phase
- **Bug 修复**：开发中发现的已有 bug，优先级高于当前 Feature 开发

---

## 7. 决策记录

关键决策记录在 STATE.md 的 `Decisions` 章节，格式：

```
- [Phase N]: 决策内容
```

---

*定义日期: 2026-05-27*
