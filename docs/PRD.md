# Skillbee V2 — Product Requirements Document

> 本文档定义 Skillbee（原 AImagician Skills）V2 的产品需求，作为后续所有功能迭代的核心参照。
>
> 核心理念：**功能深化** —— 在已有 7 个完成 Phase 的基础上，聚焦安装体验、资产管理效率和 TUI 品质，不做平台化或商业化转型。

---

## 1. 产品定位

**Skillbee** 是一个面向多 AI CLI 的个人技能管理器、分类目录与部署工具。

- **目标用户**：你（单人工具）
- **核心场景**：浏览、搜索、分组、批量安装/卸载 skills 到 7 个目标 CLI
- **设计原则**：本地优先、离线可用、终端原生体验
- **品牌调性**：🐝 小蜜蜂 —— 勤快、灵巧、有条理

---

## 2. 功能需求

### F1 — TUI 品牌重塑

| 属性 | 说明 |
|------|------|
| 优先级 | P0 |
| 描述 | 以 🐝 小蜜蜂为核心视觉元素重新设计 TUI，改变当前纯文字单调风格 |
| 验收标准 | 1. Dashboard 顶部显示蜜蜂主题 Banner/Header<br>2. 主色调采用活泼明亮的配色方案<br>3. 选中/安装/卸载等状态有对应的视觉反馈<br>4. 整体信息密度和可读性不低于当前版本 |

**细节要求**：
- Header 区域展示蜜蜂 ASCII art 或字符画 Logo
- 分组列表、技能列表、详情面板使用统一配色
- 已安装技能用绿色高亮标识，未安装用默认色，归档用灰色
- 安装/卸载时状态栏有进度反馈

### F2 — 多 Target 多选操作

| 属性 | 说明 |
|------|------|
| 优先级 | P0 |
| 描述 | 当前 TUI 只能通过 `tab` 在 target 之间切换，改为可直接勾选多个 target |
| 验收标准 | 1. TUI 中 target 切换区域支持多选（checkbox 模式）<br>2. 支持「全选所有 target」和「反选」快捷键<br>3. 当前选中的 targets 在 header 区清晰展示<br>4. 所有操作（安装/卸载/查看）基于所选 targets 生效 |

**交互方式**：
- 数字键 `1`-`7` 或 `t` 进入 target 选择模式
- 空格键切换单个 target 的勾选状态
- `a` 全选所有 target
- `A`（Shift+a）反选
- 已选 targets 在 Header 区域用不同颜色/符号标记

### F3 — 批量安装/卸载

| 属性 | 说明 |
|------|------|
| 优先级 | P0 |
| 描述 | 当前 `i`/`u` 只对当前选中 target 操作，改为对所有已选 targets 同时操作 |
| 验收标准 | 1. 选中多个技能 + 多个 target → 一键安装到所有选中 targets<br>2. 操作完成后展示跨 target 的结果汇总<br>3. 每个 target 独立报告成功/失败/已存在状态<br>4. 当前 TUI 的单 target 模式仍然保留兼容 |

**流程**：
1. 在技能列表中多选 skills（空格）
2. 选择要操作的 targets（F2 的 target 选择机制）
3. 按 `i` 安装 → 在所有已选 targets 上同时安装
4. 按 `u` 卸载 → 从所有已选 targets 上同时移除

### F4 — 标签式分组系统

| 属性 | 说明 |
|------|------|
| 优先级 | P1 |
| 描述 | 当前分组基于 taxonomy.yaml 的 `group` 单层结构，改为支持多标签（tag）系统，一个 skill 可属于多个分组 |
| 验收标准 | 1. taxonomy.yaml 中的 `tags` 字段作为主要分组依据<br>2. 分组列表展示来自 tags 的聚合视图<br>3. 选中一个 tag 展示该 tag 下所有 skills<br>4. 支持「与」和「或」逻辑组合多个 tag 筛选 |

**数据模型变更**：
- Taxonomy 的 `group` / `subgroup` 保持向后兼容
- 新增 `primaryTag?: string` 用于分组列表展示
- TUI 分组列表默认展示所有不重复的 tags

### F5 — 自定义分组持久化

| 属性 | 说明 |
|------|------|
| 优先级 | P1 |
| 描述 | 用户可以在 TUI 中创建和管理自定义分组，分组定义保存到本地文件 |
| 验收标准 | 1. TUI 中有创建/编辑/删除自定义分组的入口<br>2. 自定义分组支持添加/移除 skill<br>3. 分组定义持久化到 `~/.config/skillbee/user-groups.yaml`<br>4. 重新启动 TUI 后自定义分组仍然可用 |

**存储格式**：
```yaml
# ~/.config/skillbee/user-groups.yaml
groups:
  - name: my-workflow
    label: 我的工作流
    skills:
      - academic-paper-workflow
      - deep-research-system
      - llm-know-how-wiki
  - name: daily-dev
    label: 日常开发
    skills:
      - code-guidelines
      - systematic-debugging
      - using-git-worktrees
```

### F6 — 多维筛选器

| 属性 | 说明 |
|------|------|
| 优先级 | P1 |
| 描述 | 当前只支持按 group 筛选和文本搜索，改为组合筛选：安装状态 + target + tag + 文本 |
| 验收标准 | 1. 筛选面板支持以下维度组合：<br>   - 安装状态：全部 / 已安装 / 未安装<br>   - Target：筛选在某个 target 上已安装/未安装的 skills<br>   - Tag：按标签筛选<br>   - 文本搜索（已有）<br>2. 筛选条件变更时技能列表实时更新<br>3. 当前激活的筛选条件在 header 中清晰展示 |

**交互方式**：
- `f` 键打开筛选面板
- 各维度上下选择 + 空格切换
- 支持多选筛选条件

### F7 — 安装概览视图

| 属性 | 说明 |
|------|------|
| 优先级 | P1 |
| 描述 | 新增一个总览视图，跨 target 展示 skills 的安装状态 |
| 验收标准 | 1. 按 `v` 切换列表/概览视图模式<br>2. 概览视图以表格形式展示：横轴为 targets，纵轴为 skills<br>3. 每个单元格标记 ✓（已安装）或 ○（未安装）<br>4. 可排序：按 target 安装数量、按 skill 覆盖度排序<br>5. 概览中可直接勾选并批量操作 |

**视图示意**：
```
Skill          │ claude │ opencode │ cursor │ codex
───────────────┼────────┼──────────┼────────┼──────
code-guidelines│   ✓    │    ✓     │   ✓    │   ○
debugging      │   ✓    │    ○     │   ○    │   ○
paper-workflow │   ✓    │    ✓     │   ✓    │   ✓
```

### F8 — Skill 详情面板强化

| 属性 | 说明 |
|------|------|
| 优先级 | P1 |
| 描述 | 当前详情面板只展示基本元信息，改为展示更丰富的内容 |
| 验收标准 | 1. 展示 SKILL.md 的内容预览（前 20 行或摘要）<br>2. 展示 skill 在所有 target 上的安装状态矩阵<br>3. 展示同 tag 的相关 skill 推荐<br>4. 展示来源（owned / GitHub 源地址 / command）<br>5. 支持在详情面板中直接操作（安装/卸载/归档） |

### F9 — TUI 归档/取消归档

| 属性 | 说明 |
|------|------|
| 优先级 | P1 |
| 描述 | 在 Dashboard 中可以直接将 skill 标记为 archived 或恢复 |
| 验收标准 | 1. 选中 skill 后按 `x` 键归档/取消归档<br>2. 归档操作记录到 manifest，重启 TUI 后状态保持<br>3. 归档的 skill 默认隐藏（由 `a` 键控制显隐，已有）<br>4. 归档时确认提示，防止误操作 |

### F10 — 安装报告

| 属性 | 说明 |
|------|------|
| 优先级 | P1 |
| 描述 | 安装/卸载操作完成后展示结构化的结果报告 |
| 验收标准 | 1. 报告展示：每个 target × 每个 skill 的操作结果（成功/跳过/失败）<br>2. 报告按 target 分组展示<br>3. 失败的条目显示原因<br>4. 报告可关闭（按任意键返回）或保存到文件 |

**报告样式**：
```
═══ 安装完成 ═══

claude  (3/3 成功)
  ✓ code-guidelines
  ✓ systematic-debugging
  ✓ verification-before-completion

opencode  (2/3 成功, 1 跳过)
  ✓ code-guidelines
  ✓ systematic-debugging
  ○ verification-before-completion → 已存在, 跳过

cursor  (0/3 成功)
  ✗ code-guidelines → target 不可达
```

---

## 3. 用户交互场景

### 场景设计原则

- 每个场景是一条完整的**用户任务流**，描述从触发到完成的连贯操作
- 快捷键设计原则：常用操作（安装/卸载/浏览）单键直达；进阶操作（筛选/分组管理/命令面板）用 `Ctrl+/` 或 `?` 调出帮助后引导
- Group 和 Tag 在 TUI 中统一为「分组/标签」面板，不做概念区分

### 键盘全景图

```
底层常驻（底部状态栏提示）:
  ↑/↓       导航技能列表
  space     多选/取消选
  i         安装选中 skills → 当前 targets
  u         卸载选中 skills → 当前 targets
  q         退出

中层常用（底部状态栏提示）:
  tab       切换当前操作的 target（单 target 模式）
  /         搜索
  g         切换 global/project scope
  a         切换显示/隐藏 archived skills

进阶操作（按 ? 或 Ctrl+/ 调出命令面板查看）:
  x         归档/取消归档选中 skill
  t         打开 target 多选面板
  f         打开多维筛选面板
  v         切换列表/概览矩阵视图
  c         创建自定义分组
  E         编辑自定义分组
  D         删除自定义分组
  r         重置 Cursor（确认后执行）
```

---

### S1: 启动与初始界面

| 属性 | 说明 |
|------|------|
| 前置条件 | 已安装 skillbee，终端支持 TTY |
| 触发方式 | 执行 `skillbee`（无参数） |
| 涉及 Feature | F1, F4 |

**操作序列**：
1. 终端清屏，显示 Dashboard 布局
2. Header 区：🐝 Logo 居左 + scope / 当前 target / selected 数量 / 查询状态 展示在顶部
3. Groups 面板（左侧）：列出 `all` + taxonomy groups + 自定义分组（`@` 前缀），当前选中高亮
4. Skills 面板（中间）：展示全量 skills（按组排序），每行格式 `[ ] skill-id (installed/available)`
5. Detail 面板（右侧）：展示 skills 列表中第一个 skill 的详细信息
6. Status 栏（底部）：展示当前 scope、visible 数量、常用快捷键提示

**用户预期**：
- 一眼看到自己的 skills 总量和分组结构
- 知道当前在哪个 scope、哪个 target 下
- 底部提示让用户知道按什么键可以做什么

---

### S2: 浏览与发现 Skills

| 属性 | 说明 |
|------|------|
| 前置条件 | 已进入 Dashboard |
| 触发方式 | 进入后默认处于浏览状态 |
| 涉及 Feature | F4, F6 |

**操作序列**：
1. **按分组浏览**：在 Groups 面板上下选择，Skills 面板实时过滤
   - `all`：显示所有 skills
   - 点击某个 group/tag：只显示该组下的 skills
   - 点击某个自定义分组（`@` 前缀）：只显示该分组中包含的 skills
2. **搜索**：按 `/` 弹出搜索输入框，输入关键词后 Skills 列表实时过滤（匹配 id/description/tags/customTags）
3. **多维筛选**：按 `f` 打开筛选面板，可组合条件：
   - 安装状态：全部 / 已安装 / 未安装
   - Target：按在某个 target 上的安装状态筛选
   - Tag：按标签筛选
4. 查看详情：↑/↓ 导航 Skills 列表，右侧 Detail 面板自动更新

**用户预期**：
- 知道当前在哪个分组下（Groups 面板中高亮）
- 筛选和搜索叠加生效，结果实时更新
- 筛选激活时 Header 有标识提示

---

### S3: 安装 Skills 到 CLI

| 属性 | 说明 |
|------|------|
| 前置条件 | 已有目标 skills 被选中的 targets |
| 涉及 Feature | F1, F2, F3, F10 |

**操作序列（快捷路径）**：
1. 在 Skills 面板导航到目标 skill（↑/↓）
2. 按 `space` 选中（可连续多选，Header 显示 selected 计数）
3. 确认 target：底部当前 target 高亮显示
4. 按 `i` 执行安装
5. 安装完成后弹出**安装报告**（F10 样式），展示每个 target × skill 的结果
6. 按任意键关闭报告，返回 Dashboard

**操作序列（多 target 路径）**：
1. 按 `t` 进入 target 多选模式
2. 面板列出所有 7 个 CLI：`[x] claude [ ] opencode [x] cursor ...`
3. space 切换勾选，`a` 全选，`A` 反选
4. 确认后返回 Dashboard，Header 展示已选 targets
5. 在 Skills 面板选择 skills → 按 `i` 安装到所有已选 targets
6. 弹出安装报告

**用户预期**：
- 安装前知道「哪些 skills → 哪些 targets」
- 安装后立即看到结果，不用自己去翻目录验证
- 报告按 target 分组，成功/失败一目了然

---

### S4: 卸载清理

| 属性 | 说明 |
|------|------|
| 前置条件 | 目标 skills 已安装在选中的 targets 上 |
| 涉及 Feature | F2, F3, F10 |

**操作序列**：
1. 在 Skills 列表中选中需要卸载的 skills（`space` 多选）
2. 确认 target（单 target 或 `t` 多选）
3. 按 `u` 执行卸载
4. 弹出卸载报告，展示每个 target 上哪些 skills 被移除、哪些跳过（非 managed）

**用户预期**：
- 只删除 Skillbee 管理的 skills，手写的 skill 不受影响
- 卸载后技能列表立即刷新，状态从 installed 变为 available

---

### S5: 归档/取消归档

| 属性 | 说明 |
|------|------|
| 前置条件 | 选中一个或多个 skills |
| 涉及 Feature | F9 |

**操作序列**：
1. 在 Skills 面板导航到目标 skill（或 space 多选）
2. 按 `x` 执行归档切换
   - 如果 skill 当前未归档 → 标记为 archived
   - 如果已归档 → 取消归档
3. Status 栏显示操作结果
4. 默认 `a` 为隐藏 archived（按 `a` 切换显隐）

**用户预期**：
- 归档的 skill 不消失，只是默认隐藏
- `a` 键可以随时查看/恢复归档的 skills
- 归档状态持久化，重启 TUI 后仍在

---

### S6: 自定义分组管理

| 属性 | 说明 |
|------|------|
| 前置条件 | 已在 Dashboard 中 |
| 涉及 Feature | F5 |

**操作序列（创建分组）**：
1. 按 `c` 创建自定义分组
2. 弹出输入框：输入分组名称（name，用作标识符）
3. 弹出输入框：输入分组标签（label，显示名称）
4. 进入编辑模式：上下选择 skills，space 添加到分组
5. 完成后新分组出现在 Groups 面板（`@ 分组名`）

**操作序列（编辑分组）**：
1. 在 Groups 面板选中要编辑的自定义分组
2. 按 `E`（Shift+e）进入编辑
3. 调整分组中的 skills（space 切换包含/排除）
4. 保存更新

**操作序列（删除分组）**：
1. 在 Groups 面板选中要删除的自定义分组
2. 按 `D`（Shift+d）删除
3. 确认提示，确认后分组从 Groups 面板消失

**用户预期**：
- 自定义分组在 Groups 面板中以 `@ 名称` 形式出现
- 分组的 skills 列表可选自任意来源（owned / external）
- 分组持久化，重启后仍在

---

### S7: 安装概览矩阵

| 属性 | 说明 |
|------|------|
| 前置条件 | 已在 Dashboard 中 |
| 涉及 Feature | F7, F8 |

**操作序列**：
1. 按 `v` 切换视图模式（列表 ↔ 矩阵）
2. 矩阵视图：横轴为 targets，纵轴为 skills
3. 每个单元格：✓ 已安装 / ○ 未安装 / — 不支持
4. 在矩阵中可以直接用 space 选中 skills，按 `i`/`u` 批量操作
5. 在某个 skill 行上按 Enter：Detail 面板展示该 skill 的跨 target 安装状态矩阵
6. 按 `v` 切回列表视图

**用户预期**：
- 一眼看出哪个 target 装得多、哪些 skills 覆盖面广
- 矩阵中可以直接操作，不需要切回列表

---

### S8: 命令面板

| 属性 | 说明 |
|------|------|
| 前置条件 | 已在 Dashboard 中 |
| 触发方式 | 按 `?` 或 `Ctrl+/` |
| 涉及 Feature | F1 |

**操作序列**：
1. 按 `?` 或 `Ctrl+/` 打开命令面板（覆盖在当前界面上的半透明浮层）
2. 面板展示所有可用快捷键及其功能说明，按功能分组：
   - **浏览**：↑/↓, /, f, v
   - **选择**：space, t, a(全选)
   - **操作**：i, u, x
   - **管理**：c, E, D, g, a(归档切换)
   - **系统**：q, r, ?
3. 按任意键关闭面板

**用户预期**：
- 忘记快捷键时随时 `?` 查看
- 不用记所有键，常用键在底部提示，生僻键在面板里

---

## 4. 数据模型变更

### 4.1 ManagerSkillRecord 扩展

```typescript
interface ManagerSkillRecord {
  // ... 现有字段保持不变 ...
  
  // 新增：
  customTags: string[];         // 用户自定义标签
  installMatrix: Record<        // 跨 target 安装状态矩阵
    SupportedTarget,
    "installed" | "available" | "unsupported"
  >;
}
```

### 4.2 新增配置：user-config.yaml

```typescript
interface UserSkillConfig {
  version: 1;
  groups: UserDefinedGroup[];   // 自定义分组
  preferences: {
    defaultTargets: SupportedTarget[];  // 默认选中的 targets
    theme: string;                      // 主题名称
    archivedIds: string[];              // 用户归档的 skill id 列表
  };
}
```

### 4.3 TUI 组件模型

- `App` — TUI 根组件，负责主题/布局/事件分发
- `Header` — 蜜蜂品牌 Header，展示目标信息
- `GroupPanel` — 分组/标签列表（支持 tag 多选）
- `SkillPanel` — 技能列表（支持多维筛选 + 多选）
- `DetailPanel` — Skill 详情展示（强化版）
- `MatrixView` — 安装概览矩阵（F7）
- `TargetSelector` — Target 多选组件（F2）
- `FilterBar` — 多维筛选组件（F6）
- `ReportPanel` — 安装报告展示（F10）

---

## 5. 非功能性需求

| 编号 | 需求 | 说明 |
|------|------|------|
| NFR1 | 向后兼容 | 所有新增功能不能破坏现有 CLI 命令（search/install/uninstall/reset/bootstrap/list/inspect/doctor） |
| NFR2 | 本地优先 | 所有用户配置存储在本地文件系统，无需网络 |
| NFR3 | 跨平台 | Linux/Windows 行为一致，路径处理沿用现有 `shared/paths.ts` + `shared/platform.ts` |
| NFR4 | 性能 | TUI 列表渲染在 56+ skills 下无卡顿 |
| NFR5 | 数据安全 | 归档/自定义分组数据与 manifest 一致，不会出现孤立的配置引用 |

---

## 6. 不做范围（Out of Scope）

| 特性 | 原因 |
|------|------|
| Skill 版本管理 | 当前不需要 track 版本升级/回滚 |
| Skill 依赖管理 | 单用户场景不构成问题 |
| link mode / dry-run | 用户明确不关心 |
| 源锁定 / 缓存 (SRC-05/06) | 用户明确不关心 |
| 托管市场 / Web UI | 保持本地 CLI 工具定位 |
| 多用户 / 团队协作 | 单人工具 |

---

## 7. 成功指标

- 所有 F1-F10 验收标准通过
- 现有测试套件全部通过（`npm test`）
- 构建无错误（`npm run build`）

---

## 8. 附录

### 关联文件

- [CATALOG-CONFIG.md](./CATALOG-CONFIG.md) — 外部源配置说明
- [taxonomy.yaml](../catalog/taxonomy.yaml) — 全局分组/标签定义
- [dashboard.ts](../src/tui/dashboard.ts) — 当前 TUI 实现（V2 将重构）

### 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0 | 2026-05-27 | 初版，基于讨论形成的 10 个 Feature |
