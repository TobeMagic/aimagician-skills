# Plain Repo Mode

这份参考文件说明：如果目标仓库没有 `.planning`，`parallel-worktree-pr-flow` 也必须能独立运行，不依赖 GSD。

## 核心原则

- 不要为了并行流强行给普通仓库塞一套假的 `.planning`
- 普通仓库也必须有真相源，只是这个真相源应落在 repo-local 并行目录
- `integration` 分支仍然是共享面、验收与合并中心

## 默认目录

推荐使用：

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

## 普通仓库的最小真相源

至少要保证这些文件存在：

- `PROVIDER_PROTOCOL.md`
- `PARALLEL_WORKTREE.md`
- `provider_workstreams.json`

推荐再补一份：

- `STATUS.md` 或 `INTEGRATION_NOTES.md`

用途分别是：

- `PROVIDER_PROTOCOL.md`：边界、shared surfaces、merge 规则
- `PARALLEL_WORKTREE.md`：分波次策略、启动方式、验收顺序
- `provider_workstreams.json`：执行层真相
- `STATUS.md / INTEGRATION_NOTES.md`：给人看的最新进度摘要

## 普通仓库的执行顺序

1. 建立 baseline commit
2. 写 registry
3. 校验 `write_scope`
4. 创建 worktree
5. 启动 provider lane
6. integration 做验收
7. 开 PR 到 integration
8. 合并 PR
9. 更新 `provider_workstreams.json` 和 `STATUS.md`
10. 最后把 integration 合回主分支

## shared surfaces 建议

普通仓库默认可把这些视为 shared surfaces：

- 根级 `README.md`
- 全局 `docs/`
- 根级配置文件
- CI / smoke test / 发布脚本
- 全局 router / registry / app wiring

provider lane 默认不要直接改这些文件。

## 推荐状态流转

普通仓库没有 GSD phase，可以直接用 registry 作为主状态机：

`planned -> running -> ready_for_review -> opened_pr -> merged`

如果还要有更人类可读的摘要，就把这些状态聚合进 `STATUS.md`。

## 何时更新状态

至少在这些节点更新：

- 启动一批 worker 前
- 一批 lane 进入 `running` 后
- 有 lane ready for review 时
- PR 合并后
- integration 完成一轮 smoke test 后

## 最小准则

如果仓库没有 `.planning`，也必须做到：

> 任意时刻只看 `.codex_parallel/`，就能知道有哪些 lane、谁在运行、谁已合并、下一步该收哪一批。
