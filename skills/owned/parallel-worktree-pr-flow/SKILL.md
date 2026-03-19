---
name: parallel-worktree-pr-flow
description: |
  设计和执行多 worktree 并行开发 + 分支验收 + PR 合并的完整工作流。
  当用户提到“多 worktree 并行开发”“多个 Codex/agent 同时干活”“integration 分支”“批量开 PR”“避免共享文件冲突”“write_scope / manifest / registry”“后台跑 worker 然后集中验收合并”时，必须使用这个 skill。
  这个 skill 适合仓库级开发协作编排，不是产品运行时能力，不要把这套协议塞进应用本身的 runtime/skills 目录。
compatibility:
  tools: [bash, git, python]
  requires: git 仓库、可创建 git worktree、最好有 GitHub CLI 或 API token
---

# Parallel Worktree PR Flow

这个 skill 的目标很简单：

- 让一个仓库可以安全地同时开很多个 worktree
- 让每个 worktree 只做自己的低耦合工作面
- 让 integration 分支负责共享面、验收、PR 和最终合并

## 何时使用

遇到这些任务时直接触发：

- 用户要“开多个 worktree 并行做 provider / 平台 / 数据源 / 队列”
- 用户要“后台同时跑多个 Codex / agent / worker”
- 用户要“先在各自分支完成，再统一开 PR 和验收”
- 用户要“把共享文件冲突降到最低”
- 用户要“设计 manifest / registry / write_scope 协议”

不要把这套流程误写进产品本身的运行时目录。
这是一套仓库开发协作协议，默认应该放在仓库级规划目录、工程目录或独立 skill 仓库里。

## 核心原则

1. 固定一个 `integration` worktree 负责共享面。
2. 其它 worktree 只改自己的 `write_scope`。
3. 每个 lane 必须交 manifest、验证命令和阻塞说明。
4. PR 先合到 `integration`，不是直接互相撞 `master`。
5. integration 先验收 provider，再做共享面注册和总 smoke test。

## 最小文件集

真正要落地这套流程，至少需要这几类文件：

- `parallel registry`
  用来声明所有并行 lane、branch、worktree、write_scope、priority、status。
- `provider/workstream manifest template`
  约束每条 lane 必须交什么。
- `protocol doc`
  明确共享面、私有面、合并顺序和冲突边界。
- `worktree bootstrap script`
  从 registry 开 worktree。
- `status/acceptance script`
  统一查看 branch/worktree/manifest 状态。

## 使用顺序

### 1. 先读工作流

先读：

- `references/workflow.md`

如果任务是“先设计协议，后开工”，再读：

- `references/conflict-control.md`
- `references/pr-lifecycle.md`

### 2. 初始化文档与模板

优先复用这个 skill 附带的模板：

- `assets/provider_manifest.template.json`
- `assets/parallel_workstreams.template.json`

把它们放进目标仓库自己的规划目录，例如：

```text
.planning/dev_parallel/
```

### 3. 开工前先定义 shared surfaces

不要一上来就开 10 个 worktree。

先在目标仓库里明确：

- 哪些文件是共享面，只允许 integration 改
- 哪些目录可以按 lane 隔离
- 哪些 lane 值得单独 worktree

如果用户没给，就根据仓库结构自己拟一个最小共享面清单。

### 4. 校验 registry

用 `scripts/bootstrap_parallel_worktrees.py`：

- `--validate` 先查重、查 write_scope 冲突、查 manifest 冲突
- `--list` 看首批要开的 lane
- `--execute` 真正创建 worktree
- 如果 registry 不在目标仓库内，再补 `--repo-root <repo-root>`

### 5. 启动并行 lane

每个 provider/workstream 只做：

- 自己的实现
- 自己的 manifest
- 自己的最小验证命令
- 自己的 blocker 说明

不要让 provider 分支直接改共享文件。

### 6. integration 做验收与合并

integration 的固定节奏：

1. `fetch` provider 分支
2. 检查 diff 是否只落在 write_scope
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

### 7. 用状态脚本持续巡检

用 `scripts/inspect_parallel_status.py`：

- 看哪些 branch 还没创建
- 看哪些 worktree 缺失
- 看哪些 worktree 脏了
- 看哪些 branch 还没 push
- 看哪些 manifest 丢了
- 如果 registry 放在仓库外，也补 `--repo-root <repo-root>`

## 输出要求

当你用这个 skill 帮用户落地并行工作流时，输出至少要覆盖：

- 当前推荐拓扑
- integration 与 execution/provider 的职责边界
- 共享面列表
- 需要落地的文档与脚本
- 第一波 worktree 建议
- PR 合并顺序
- 当前风险点或冲突点

## 参考文件

- `references/workflow.md`
- `references/conflict-control.md`
- `references/pr-lifecycle.md`

## 附带脚本

- `scripts/bootstrap_parallel_worktrees.py`
- `scripts/inspect_parallel_status.py`
- `scripts/github_pr_flow.py`

## 附带模板

- `assets/provider_manifest.template.json`
- `assets/parallel_workstreams.template.json`
