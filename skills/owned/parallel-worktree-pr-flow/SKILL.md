---
name: parallel-worktree-pr-flow
description: |
  设计、启动、巡检和收口多 worktree 并行开发 + integration 分支验收 + PR 合并的完整工作流。
  当用户提到“多 worktree 并行开发”“多个 Codex/agent 同时干活”“integration 分支”“批量开 PR”“后台跑 worker”“write_scope / manifest / registry”“统一验收合并”“并行 provider/platform lane”“repo 级协作协议”时，必须使用这个 skill。
  这个 skill必须同时支持两种仓库：有 `.planning` 的 GSD 管理仓库，以及没有 `.planning` 的普通仓库。
  在 GSD 管理的仓库中，必须用它把并行执行挂到当前 milestone/phase；在普通仓库中，也必须能独立完成 registry、worktree、PR、验收与集成闭环。不要把这套协议写进产品运行时目录或应用本身的 skills/runtime。
compatibility:
  tools: [bash, git, python]
  requires: git 仓库、可创建 git worktree、最好有 GitHub CLI 或 API token
---

# Parallel Worktree PR Flow

这个 skill 负责把“很多条 lane 并行做”变成一个可控的仓库级工程流程，而不是临时口头协作。

它解决的不是产品功能，而是开发编排：

- 如何安全地同时开很多 worktree
- 如何约束每个 lane 只动自己的低耦合区域
- 如何用 `integration` 分支承接共享面、验收、PR 与合并
- 如何把并行执行和 GSD 的 milestone / phase / state 对齐

## 何时使用

遇到这些任务时直接触发：

- 用户要“开多个 worktree 并行做 provider / 平台 / 数据源 / 队列 / 质量矩阵”
- 用户要“后台同时跑多个 Codex / agent / worker”
- 用户要“先在各自分支完成，再统一开 PR 和验收”
- 用户要“把共享文件冲突降到最低”
- 用户要“设计 manifest / registry / write_scope 协议”
- 用户要“让并行执行和 `.planning` / GSD 进度联动”

不要把这套流程误写进产品本身的运行时目录。
这是一套仓库开发协作协议，默认应放在仓库级规划目录、工程目录或独立 skills 仓库里。

## 核心原则

1. 固定一个 `integration` worktree 负责共享面。
2. 其它 worktree 只改自己的 `write_scope`。
3. 每个 lane 必须交 `manifest / 验证命令 / blocker / 交付说明`。
4. provider PR 先合到 `integration`，不要直接互撞 `master`。
5. integration 先验收 provider，再做共享面注册、planning 回写和总 smoke test。
6. 在 GSD 仓库里，并行流是 `phase execution strategy`，不是平行于 GSD 的另一套项目管理。

## 先判断：仓库属于哪条路径

优先检查仓库里是否存在：

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`

如果存在，就按 `GSD-managed repo` 处理。不要跳过这一步。

如果不存在，就按 `plain repo` 处理。

这一步不是可选项。你必须先分流，再决定目录、planning 约束和回写方式。

在 GSD 仓库里，你的默认动作应该是：

1. 先识别当前 active milestone / phase / plan
2. 再决定哪些 lane 值得并行
3. 并行完成后把结果写回 `.planning`

GSD 结合方式见：

- `references/gsd-integration.md`

普通仓库的独立运行方式见：

- `references/plain-repo-mode.md`

## 双路径启动规则

### Path A: GSD-managed repo

适用条件：

- 仓库存在 `.planning/PROJECT.md`
- 并且通常也有 `.planning/ROADMAP.md`、`.planning/STATE.md`

此时：

- 并行流是当前 phase 的执行策略
- integration 需要回写 `.planning`
- `.planning/**` 默认属于 shared surfaces
- provider lane 不应直接改 GSD 主文档

### Path B: plain repo

适用条件：

- 仓库没有 `.planning`
- 或用户明确不想引入 GSD

此时：

- 并行流独立运行，不依赖 milestone / phase
- 仍然要有 registry / protocol / manifest / integration 分支
- 只是不需要 `.planning` 回写
- 必须改用 repo-local 的并行工作目录保存协议与状态

普通仓库推荐目录：

```text
.codex_parallel/
├── PROVIDER_PROTOCOL.md
├── PARALLEL_WORKTREE.md
├── provider_workstreams.json
├── provider_manifests/
│   └── provider_manifest.template.json
├── runlogs/
└── scripts/
```

## integration 与 provider 的职责边界

### integration worktree 负责

- 共享面文件
- provider 验收
- PR 创建 / 合并
- planning / roadmap / state 回写
- 总 smoke test
- 最终把 `integration` 合回主分支

### provider / execution worktree 负责

- 自己的实现
- 自己的验证
- 自己的 blocker 与结果说明
- 自己的 branch push

默认不要让 provider 直接改共享文件。

## shared surfaces 的默认定义

如果用户没有明确给共享面，就先按下面的最小集合起步：

- `.planning/**`
- 根级 `README.md`
- 全局 `docs/` 总览文档
- 统一 router / registry / config
- 统一 smoke test / CI 配置

在 GSD 仓库里，尤其优先把这些视为 integration-only：

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/REQUIREMENTS.md`

如果某条 lane 必须触碰共享面，不要默默修改。要么：

- 明确把它升级为 integration 任务
- 要么让 provider lane 在最终说明里列出所需 integration touchpoints

## 最小文件集

真正落地这套流程，至少需要这些文件：

- `parallel registry`
  声明所有并行 lane、branch、worktree、write_scope、priority、status。
- `provider/workstream manifest template`
  约束每条 lane 必须交什么。
- `protocol doc`
  明确共享面、私有面、合并顺序和冲突边界。
- `worktree bootstrap script`
  从 registry 创建 worktree。
- `status / acceptance script`
  统一查看 branch / worktree / manifest 状态。

GSD 仓库推荐放在：

```text
.planning/dev_parallel/
```

普通仓库推荐放在：

```text
.codex_parallel/
```

## 推荐目录

GSD 仓库：

```text
.planning/dev_parallel/
├── PROVIDER_PROTOCOL.md
├── PARALLEL_WORKTREE.md
├── provider_workstreams.json
├── provider_manifests/
│   └── provider_manifest.template.json
├── runlogs/
└── scripts/
```

普通仓库：

```text
.codex_parallel/
├── PROVIDER_PROTOCOL.md
├── PARALLEL_WORKTREE.md
├── provider_workstreams.json
├── provider_manifests/
│   └── provider_manifest.template.json
├── runlogs/
└── scripts/
```

## 使用顺序

### 1. 先读工作流

先读：

- `references/workflow.md`

如果任务是“先设计协议，后开工”，再读：

- `references/conflict-control.md`
- `references/pr-lifecycle.md`
- `references/gsd-integration.md`
- `references/plain-repo-mode.md`

### 2. 选择执行路径

如果仓库是 GSD 管理的：

- 确认当前 active milestone / phase
- 判断本次并行是：
  - 当前 phase 的执行波次
  - 还是一个需要新增 / 插入的 phase

如果用户要并行做的内容超出当前 phase，先让 integration 补 planning：

- 新 milestone：`gsd-new-milestone`
- 新 phase：`gsd-add-phase`
- 急插 phase：`gsd-insert-phase`
- 详细计划：`gsd-plan-phase`

只有 phase 定义清楚后，再把 lane 映射到 registry。

如果仓库不是 GSD 管理的：

- 不要硬造 `.planning`
- 直接在 `.codex_parallel/` 下落 registry / protocol / manifests
- 用 integration 分支承担状态真相
- 用 registry + runlogs + integration README/STATUS 文档代替 `.planning` 回写

### 3. 初始化文档与模板

优先复用这个 skill 附带的模板：

- `assets/provider_manifest.template.json`
- `assets/parallel_workstreams.template.json`

放到目标仓库自己的并行工作目录中：

- GSD 仓库：`.planning/dev_parallel/`
- 普通仓库：`.codex_parallel/`

### 4. 开工前先定义 shared surfaces

不要一上来就开 `10+` 个 worktree。

先明确：

- 哪些文件只允许 integration 改
- 哪些目录可以按 lane 隔离
- 哪些 lane 真值得单独 worktree

如果用户没给，就根据仓库结构先拟一个最小共享面清单。

### 5. 校验 registry

用 `scripts/bootstrap_parallel_worktrees.py`：

- `--validate`：查重、查 write_scope 冲突、查 manifest 冲突
- `--list`：看首批要开的 lane
- `--execute`：真正创建 worktree

如果 registry 不在目标仓库内，再补：

- `--repo-root <repo-root>`

对于普通仓库，这通常是默认路径，不需要强行创建 `.planning`。

### 6. 启动并行 lane

每个 provider / workstream 只做：

- 自己的实现
- 自己的 manifest
- 自己的最小验证命令
- 自己的 blocker 说明
- 自己的 commit / push

不要让 provider 分支直接改共享文件。

如果用户要后台批量启动 Codex/agent：

- 优先把日志落到 repo 内固定目录
- 在 registry 里维护 `status / pid / log_path / launched_at`
- 让 integration 定期巡检，而不是靠口头记忆

### 7. integration 做验收与合并

integration 的固定节奏：

1. `fetch` provider 分支
2. 检查 diff 是否只落在 `write_scope`
3. 运行 manifest 里的验证命令
4. 必要时先 rebase 到 integration
5. 开 PR 到 integration
6. 合并 PR
7. 集成共享面变更
8. 跑总 smoke test
9. 最后再把 integration 合到主分支

如果用户希望直接从命令行创建或合并 GitHub PR，优先用：

- `scripts/github_pr_flow.py`

这个脚本只从环境变量读取 PAT，不要把 token 写进仓库。
优先使用：

- `GITHUB_TOKEN`
- `GH_TOKEN`

### 8. 回写 GSD

这是很多并行流最容易漏掉的部分。

如果仓库是 GSD 管理的，并行执行完成后，integration 必须回写：

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- 当前 phase 的 `SUMMARY.md`
- 必要时更新 `REQUIREMENTS.md`

不要让实际完成情况和 `.planning` 长期分叉。

如果仓库不是 GSD 管理的，integration 至少要维护：

- `PROVIDER_PROTOCOL.md`
- `PARALLEL_WORKTREE.md`
- `provider_workstreams.json`
- 一份当前批次状态文档，例如 `STATUS.md` 或 `INTEGRATION_NOTES.md`

普通仓库也必须有真相源，只是这个真相源不是 `.planning`。

### 9. 用状态脚本持续巡检

用 `scripts/inspect_parallel_status.py`：

- 看哪些 branch 还没创建
- 看哪些 worktree 缺失
- 看哪些 worktree 脏了
- 看哪些 branch 还没 push
- 看哪些 manifest 丢了
- 看哪些 lane 卡在 `running` 太久
- 看哪些 lane 已 ready 但还没开 PR

如果 registry 放在仓库外，也补：

- `--repo-root <repo-root>`

## 默认输出要求

当你用这个 skill 帮用户落地并行工作流时，输出至少要覆盖：

- 当前推荐拓扑
- 当前命中的仓库模式：`GSD-managed` 或 `plain repo`
- integration 与 provider 的职责边界
- 共享面列表
- 需要落地的文档与脚本
- 第一波 worktree 建议
- PR 合并顺序
- 当前风险点或冲突点
- 如果是 GSD 仓库：本次并行与哪个 milestone / phase 对齐
- 如果是普通仓库：当前 registry / integration 分支如何充当状态真相源

## 常见错误

- 把并行开发协议写进产品 runtime/skills
- 没识别仓库模式，就默认要求 `.planning`
- 让 provider 分支直接改 `.planning`
- 没有 registry / manifest 就盲目开 worktree
- provider 完成后不回写状态，导致 integration 不知道谁 ready
- 只开 worktree，不做验收、PR、merge 节奏
- 在 GSD 仓库里做完很多事，却不更新 `PROJECT / ROADMAP / STATE`

## 参考文件

- `references/workflow.md`
- `references/conflict-control.md`
- `references/pr-lifecycle.md`
- `references/gsd-integration.md`
- `references/plain-repo-mode.md`

## 附带脚本

- `scripts/bootstrap_parallel_worktrees.py`
- `scripts/inspect_parallel_status.py`
- `scripts/github_pr_flow.py`

## 附带模板

- `assets/provider_manifest.template.json`
- `assets/parallel_workstreams.template.json`
