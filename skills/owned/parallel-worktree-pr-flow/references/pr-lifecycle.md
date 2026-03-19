# PR Lifecycle

这份文档定义一条 lane 从完成到并入 integration 的标准节奏。

## 1. provider lane 完成时必须具备

一个可以提交 PR 的 provider/workstream，至少应具备：

- 局部实现代码
- provider manifest
- 至少一条验证命令
- 明确 blocker 或 live 结果
- 干净 diff

如果只写了代码，没有 manifest 和验证命令，不要开 PR。

## 2. integration 收件顺序

integration 不要无脑合并。

先做这几步：

1. `fetch` 远端分支
2. 检查这个 branch 是否基于过旧 integration
3. 查看 diff 是否只覆盖 write_scope
4. 跑 manifest 里的验证命令
5. 通过后再开 PR

## 3. diff 审查标准

integration 重点看这些点：

- 是否改到了共享面
- 是否改到了别人的 write_scope
- 是否顺手夹带不相关改动
- 是否把 blocker 写清楚

如果 diff 里混进了大量旧基线变更，先 rebase，再开 PR。

## 4. 建议的 PR 目标分支

provider PR 默认先指向：

```text
parallel/provider-integration
```

不要直接全都怼到 `master`。

如果要自动开 PR，建议统一走脚本而不是手动点网页：

```bash
export GITHUB_TOKEN=ghp_xxx
python scripts/github_pr_flow.py \
  --repo-root <repo-root> \
  --head feat/example-lane \
  --base parallel/provider-integration \
  --title "feat: add example lane"
```

提醒：

- PAT 只放环境变量，不要写入 `.env.example`、README 或仓库脚本
- 至少需要 `pull requests` 和 `contents` 的读写权限
- fine-grained PAT 也可以，但权限要覆盖目标仓库

## 5. merge 前检查单

每个 PR 合并前，integration 至少过这张检查单：

- branch 已 push 到远端
- worktree 是干净的
- diff 只覆盖允许范围
- 验证命令已跑
- blocker 已写清楚
- manifest 与 registry 一致

## 6. merge 后 integration 要做什么

provider branch 合入 integration 后，integration 再做：

- shared surface 注册
- `.env.example` 补变量
- README / SETUP / TROUBLESHOOTING 更新
- 总 smoke test

provider 分支本身不负责这些。

## 7. integration -> main 的汇总 PR

推荐节奏：

1. 一批 provider PR 合入 integration
2. integration 统一补共享面
3. integration 跑总 smoke test
4. integration 再提一个汇总 PR 到主分支

这能把“局部实现验收”和“共享面接入”分成两个层次，风险更低。

## 8. 常见异常

### 本地分支完成了，但远端没 push

先补 push，再开 PR。

### 远端分支存在，但 diff 带了旧基线污染

先 rebase integration，再 force-push。

### 验证命令只在本地某个 profile 下能跑

在 manifest 里写清楚凭证/会话边界，不要伪装成 live ready。

### PR 已合，但 integration 没 pull 最新

先快进 integration，再继续下一批验收。
