# GSD Integration

这个参考文件说明：当仓库已经由 GSD 管理时，`parallel-worktree-pr-flow` 应该如何嵌进当前 milestone / phase，而不是脱离 `.planning` 自行生长。

## 核心原则

- 并行流是 `execution strategy`，不是第二套项目管理系统。
- `.planning` 是项目真相源；registry 只是执行编排层。
- integration worktree 负责把并行结果回写到 GSD 文档。

## 先判断当前工作属于哪一类

### 1. 已有 active phase，只是要并行执行

这是最常见情况。

做法：

- 保持当前 milestone / phase 不变
- 把各 lane 当成该 phase 的执行波次
- registry 中的 `group / priority / write_scope / status` 为执行层真相
- `.planning/STATE.md` 仍记录项目级状态

### 2. 用户要做的内容超出当前 phase

这时不要直接开并行 lane。

先补 GSD planning，再并行：

- 新 milestone：`gsd-new-milestone`
- 新 phase：`gsd-add-phase`
- 急插 phase：`gsd-insert-phase`
- 详细计划：`gsd-plan-phase`

只有 phase 定义清楚后，再把 lane 映射到 registry。

## 建议的 GSD 对接顺序

1. 读 `.planning/PROJECT.md`
2. 读 `.planning/ROADMAP.md`
3. 读 `.planning/STATE.md`
4. 明确当前 active milestone / phase
5. 判断是否要新增 phase
6. 再定义并行 lane
7. 完成后回写 `.planning`

## integration 必须回写的文件

在 GSD 仓库里，integration 至少要更新：

- `PROJECT.md`
- `ROADMAP.md`
- `STATE.md`
- 当前 phase 的 `SUMMARY.md`

必要时再更新：

- `REQUIREMENTS.md`
- 当前 milestone audit / archive 文档

## lane 与 phase 的映射建议

### 适合并行 lane 的工作

- provider/platform adapter
- datasource/provider promotion
- queue / cron 单元
- 质量验证矩阵
- 指标扩展矩阵

### 不适合 provider lane 直接修改的工作

- `.planning` 主文档
- 全局 router / config 注册
- 跨 lane 共享 smoke test
- milestone audit / archive

这些应该由 integration 统一完成。

## 推荐状态流转

GSD 视角：

`planned -> in_progress -> completed`

并行 registry 视角：

`planned -> running -> ready_for_review -> opened_pr -> merged`

两者不要混用，但要同步。

推荐做法：

- lane 进入 `running` 时，`STATE.md` 仍保持 phase `in_progress`
- integration 合完足够多 lane、满足 success criteria 后，再把 phase 标为 `completed`

## 何时更新 planning

至少在这些节点更新一次：

- 开始并行之前
- 一批 lane 合并完成后
- phase success criteria 已满足时
- milestone closeout 前

## 常见失配

- registry 已 merged，但 `.planning/STATE.md` 还写着旧 phase
- worker 已完成，但 phase summary 没补
- provider lane 改了共享文件，integration 不知道怎么收
- 用户以为“开了很多 worktree = phase 完成”，但实际上没有任何 GSD 回写

## 最小准则

如果你只做一件事，也要做到：

> 每次并行执行结束后，integration 必须让 `.planning` 能准确描述“已经完成了什么、还剩什么、下一步是什么”。
