# Workflow

这份文档描述的是“多 worktree 并行开发 + 集成验收 + PR 合并”的标准执行流。

## 1. 角色划分

### integration worktree

它只负责：

- 共享文件
- registry/manifest 审查
- provider 验收
- PR 合并
- 集成 smoke test
- 最终把 integration 合回主分支

### provider / execution worktree

它只负责：

- 自己的实现
- 自己的验证命令
- 自己的 manifest
- 自己的 blocker 说明

不要让 provider/workstream 分支顺手去改 README、env、router、roadmap 这类共享面。

## 2. 标准目录

推荐在目标仓库落这些文件。注意分两种模式：

- GSD 仓库：放 `.planning/dev_parallel/`
- 普通仓库：放 `.codex_parallel/`

```text
<parallel-root>/
├── PROVIDER_PROTOCOL.md
├── PARALLEL_WORKTREE.md
├── provider_workstreams.json
├── provider_manifests/
│   └── *.json
```

其中：

- `PROVIDER_PROTOCOL.md` 写边界
- `PARALLEL_WORKTREE.md` 写怎么开、怎么分波次
- `provider_workstreams.json` 写 registry
- `provider_manifests/*.json` 写每条 lane 的交付契约

## 3. 开工顺序

### Step 1. baseline

先把当前仓库收敛成一个 baseline：

```bash
git add -A
git commit -m "chore: baseline before parallel worktrees"
git push origin <base-branch>
```

### Step 2. 先识别仓库模式，再写 registry

如果仓库有 `.planning`：

- 本次并行应挂到当前 GSD milestone / phase
- 并行目录放 `.planning/dev_parallel/`

如果仓库没有 `.planning`：

- 不要强行引入 GSD
- 并行目录放 `.codex_parallel/`
- 由 integration 分支和 registry 充当状态真相源

先不要追求“列全所有想法”，而是先列第一波值得启动的 lane。

每条 lane 至少要有：

- `id`
- `label`
- `group`
- `branch`
- `worktree`
- `status`
- `write_scope`
- `manifest_path`

### Step 3. validate

```bash
python scripts/bootstrap_parallel_worktrees.py --registry-file <path> --validate
```

如果 registry 文件不在目标仓库里，再补：

```bash
python scripts/bootstrap_parallel_worktrees.py --registry-file <path> --repo-root <repo-root> --validate
```

必须先过：

- branch 不重复
- worktree 不重复
- manifest_path 不重复
- write_scope 不重叠
- write_scope 不碰 shared surfaces

### Step 4. bootstrap

```bash
python scripts/bootstrap_parallel_worktrees.py --registry-file <path> --group <group> --limit 3 --execute
```

### Step 5. execution

每个 provider/workstream worktree：

- 只改自己的 write_scope
- 写 manifest
- 交最小验证命令
- 如果没 live 打通，明确 blocker

### Step 6. integration acceptance

integration worktree 做：

1. `git fetch`
2. 看 branch 是否落后 integration
3. 必要时要求 rebase 或自己 rebase
4. 看 diff 是否干净
5. 跑验证命令
6. 开 PR 到 integration
7. 合并 PR

### Step 7. shared-surface registration

当 provider branch 已合到 integration 后，integration 才去碰：

- router / intents
- shared docs
- `.env.example`
- planning / roadmap

### Step 8. final promotion

integration 整体稳定后：

1. 跑总 smoke test
2. 再开 integration -> main 的汇总 PR
3. 合并回主分支

## 4. 推荐节奏

不要一次开到极限。

更稳的做法是 wave 推进：

- Wave 1: 3-4 个低耦合 lane
- Wave 2: 再补 3-4 个
- Wave 3: 最后补共享面更强的 ops/editorial lane

## 5. 什么时候继续扩容

满足这些条件再继续加 worktree：

- integration 的验收速度还能跟上
- 当前 lane 的 write_scope 足够干净
- provider manifest 都写规范了
- PR 合并没有频繁出现共享面冲突

如果这些没满足，先收口当前 wave，不要盲目扩到 20 个。
