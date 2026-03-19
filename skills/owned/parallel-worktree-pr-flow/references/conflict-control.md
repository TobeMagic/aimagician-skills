# Conflict Control

这份文档只回答一个问题：

怎么避免多 worktree 并行开发把仓库改成冲突地狱。

## 1. 真正的冲突来源

冲突通常不是来自“同时开太多人”，而是来自“所有人都在改同一批共享文件”。

最常见的高耦合面有：

- 路由/意图注册
- 顶层配置
- `.env.example`
- README 和部署文档
- planning / roadmap / state
- 跨平台汇总逻辑

这些文件一旦允许所有 provider 分支都改，merge 成本会高于实现本身。

## 2. 必须建立 shared surfaces

在真正开 worktree 之前，先列一份共享面清单。

规则很简单：

- 共享面只允许 integration 改
- provider 分支只能通过 manifest 提出“我需要被接入哪些共享面”

推荐字段名：

```json
"shared_surfaces": [
  "config/router.json",
  ".env.example",
  "README.md",
  "docs/SETUP.md"
]
```

## 3. write_scope 必须足够窄

每条 lane 的 `write_scope` 应该只覆盖自己的实现边界。

好例子：

- `skills/publish/scripts/platforms/publish_xxx.py`
- `skills/publish/references/platforms/xxx.md`
- `scripts/publish_xxx.py`

坏例子：

- `skills/publish/**`
- `docs/**`
- `config/**`

如果 write_scope 用通配太大，等于没有隔离。

## 4. provider manifest 不能省

manifest 的意义不是“多写一份 JSON”，而是让 integration 能明确知道：

- 这个 lane 谁负责
- 允许改哪些文件
- 需要哪些 env
- 入口脚本是什么
- 最小验证命令是什么
- live 没打通时卡在哪

没有 manifest，就不应该让它进入共享注册阶段。

## 5. integration touchpoints 要分离

provider 分支可以在 manifest 里声明：

```json
"integration_touchpoints_requested": [
  "config/operator_intents.json",
  ".env.example",
  "docs/SETUP.md"
]
```

但 provider 分支自己不要去改这些文件。

这条规则非常关键。

## 6. 共享文档要延后

很多人并行开发时喜欢“做一点顺手把 README 一起改了”。

这正是冲突来源。

更稳的节奏是：

1. provider 先把局部实现做完
2. integration 验收通过
3. integration 再统一补 README / env / setup / troubleshooting

## 7. 波次切分建议

先做低耦合 lane：

- 独立平台 adapter
- 独立 datasource provider
- 独立 browser helper

后做高耦合 lane：

- review/compliance
- evidence aggregation
- finance monitor
- 统一文档与共享路由

## 8. 冲突前置检查

每次扩 wave 之前，先跑：

```bash
python scripts/bootstrap_parallel_worktrees.py --registry-file <path> --validate
python scripts/inspect_parallel_status.py --registry-file <path>
```

重点看：

- write_scope collision
- shared surface overlap
- duplicate branch
- duplicate worktree
- duplicate manifest path

## 9. 冲突处理原则

### provider 分支之间冲突

优先通过缩窄 write_scope 解决。
不要靠“谁先 merge 谁赢”。

### provider 与 integration 冲突

integration 保持权威。
provider 只保留局部实现，重新提交 integration touchpoints 请求。

### 文档冲突

默认由 integration 统一重写，不要多分支反复 cherry-pick。
