---
phase: 7
phase_name: Bootstrap copilot fix and multi-target skill audit
status: completed
created: 2026-05-11
---

# Phase 7 Context

## 问题描述
copilot 目标 bootstrap 安装不完整：只同步了 owned skills，缺了45个 catalog 技能。

## 根因
`src/bootstrap/source-resolution.ts:264` 的 `resolveSkillInstallDestination` switch 缺少 `case "copilot"`：
```typescript
// 修复前: copilot 掉进 default 返回 null
switch (target) {
  case "gemini": ...
  default: return null
}
```

## 修复
添加了 `case "copilot"` 分支（与 codex/claude/opencode 相同逻辑）。

## 技能安装现状（2026-05-11）

| Target | 总数 | Bootstrap管理 | 历史遗留 | 说明 |
|--------|------|-------------|----------|------|
| codex | 93 | 56 | 37 | GSD×36 + 系统×1 |
| claude | 80 | 56 | 24 | Lark×24 |
| opencode | 56 | 56 | 0 | ✅ |
| gemini | 56 | 56 | 0 | ✅ |
| copilot | 92 | 56 | 36 | GSD×36（修复后） |
| hermes | 107 | 56 | 51 | Lark×24 + 系统×2 + 内置×25 |
| cursor | 56 | 56 | 0 | ✅ |

## 历史遗留技能明细

| 来源 | 数量 | 说明 |
|------|------|------|
| GSD工作流 | 72 (36×2目标) | `npx get-shit-done-cc --all --global` 安装 |
| Lark技能 | 48 (24×2目标) | 手动安装，feishu-lark-sources 默认禁用 |
| hermes内置 | 25 | Hermes bundled manifest 内置 |
| 系统文件 | 3 | .system, .bundled_manifest, .hub |

## 决策记录

- ✅ copilot bootstrap 修复 — 添加了 `case "copilot"` 分支，copilot 现可完整同步 bootstrap 计划的56个技能
- ✅ 飞书技能来源确认 — 使用 `larksuite/lark-cli` 仓库，默认禁用
- ✅ 插件安装逻辑保留（用户要求）
- ⏸️ 历史遗留暂不清理

## 修改的文件

1. `src/bootstrap/source-resolution.ts` — 添加 copilot case 分支
2. `catalog/skills/feishu-lark-sources.yaml` — id 改为 `feishu-lark-cli`，repo 改为 `larksuite/lark-cli`

## 待办

- [ ] 考虑将 GSD 命令源从"1个asset"改为逐条追踪36个 gsd-* 技能
- [ ] 考虑将 Lark 技能来源的 targets.include 扩展到其他目标
- [ ] 清理 hermes 的25个内置默认技能（如果不需要）
