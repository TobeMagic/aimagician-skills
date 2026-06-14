# Legacy Skillbee V2 — Product Requirements Document

> Legacy note: this V2 PRD is retained as historical product context. Current development, CLI usage, config paths, and acceptance are governed by the v4 Skillbird / `aimagician_superpower` milestone in `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, and the root `README.md`.
>
> 本文档定义 Skillbee（原 AImagician Skills）V2 的产品需求，作为历史功能迭代参照。
>
> 核心理念：以“小蜜蜂”品牌调性为核心，打造一个极致优化视觉、小白化交互、丝滑多 Target 管理的个人技能管理器。核心理念：精致、灵巧、有秩序 —— 将终端工具提升至“家电式”的易用与美观。

---

## 1. 产品愿景与定位

Skillbee V2 是一款面向多 AI CLI 的个人技能配置编排器、分类目录与部署工具。它不仅仅负责“把 Skill 复制到某个目录”，更负责把仓库默认目录、taxonomy、来源配置、用户覆盖 YAML、project/global scope 和 manifest 解析成安全、可预览、可重复执行的目标安装状态。

•目标用户: 专注于个人效率提升的 AI 开发者、研究者及高级终端用户。

•核心场景: 浏览、搜索、分组、按来源启用/禁用、配置 include/exclude、在 project/global 两个独立 scope 中批量同步 Skills 到多个目标 CLI 环境。

•设计原则: 本地优先、离线可用、配置优先、终端原生体验。TUI 是配置编排的前端，所有持久化意图先落到用户覆盖 YAML；只有用户点击安装/同步并确认预览后，Skillbee 才真实修改 CLI skills 目录。

•品牌调性: 🐝 小蜜蜂 —— 勤快、灵巧、有条理，寓意 Skillbee 帮助用户高效“采集”和“管理”技能，让工作井然有序。

### 1.1 配置编排核心模型

Skillbee 的核心产品模型是“声明意图 → 解析期望状态 → 预览同步计划 → 确认执行”。它必须区分四类状态：

1. **仓库默认层**: catalog、taxonomy、source 定义、目标 CLI 路径规范。这一层负责提供可展示、可搜索、可分组的默认事实。
2. **用户覆盖层**: source 启用/禁用、skill include/exclude、归档状态、scope/target 偏好、自定义分组等用户意图。这一层通过 YAML 持久化，TUI 的持久化修改只写这里。
3. **Scope manifest 层**: 记录 Skillbee 在 global 或 project scope 中实际托管安装过的条目，用于安全覆盖、移除和验收。
4. **TUI 会话层**: 焦点、临时筛选、临时多选等界面状态。只有 durable 设置发生变化时才写入用户覆盖 YAML。

关键约束：TUI 不直接修改仓库 catalog 或 taxonomy 默认文件；安装/卸载/清理不因配置编辑自动执行，必须经过用户触发和预览确认。

## 2. 品牌调性与视觉规范：蜂巢美学

Skillbee V2 的 TUI 将突破传统终端界面的限制，通过精心设计的字符艺术和色彩方案，营造出独特的“蜂巢美学”，让用户在终端中也能感受到精致与活力。

### 2.1 配色方案：琥珀与森林

我们采用 ANSI 256 色，确保在现代终端（如 iTerm2, Cursor Terminal, Windows Terminal）中呈现最佳效果，同时保持高对比度与可读性。

| 颜色名称              | ANSI 256 色值 | 十六进制近似值 | 应用场景                                              |
| --------------------- | ------------- | -------------- | ----------------------------------------------------- |
| 琥珀黄 (Amber)        | 214           | #FFD700        | 主色调，用于品牌 Logo、选中项高亮、关键提示、动态反馈 |
| 炭黑 (Carbon)         | 235           | #2C2C2C        | 背景色，或作为面板分隔线，营造深邃感                  |
| 花粉绿 (Pollen Green) | 34            | #00CD00        | “已安装”、“成功”状态、积极反馈                        |
| 蜂刺红 (Stinger Red)  | 160           | #D70000        | “卸载”、“错误”、“警告”状态                            |
| 幽灵白 (Ghost White)  | 252           | #E4E4E4        | 次要文本、非选中项文字，降低视觉压力                  |
| 深灰 (Dim Gray)       | 240           | #585858        | 边框、分隔线、归档状态                                |



### 2.2 视觉元素：字符艺术与动态反馈

•Bee-Art Logo:

•启动画面: 终端启动时，展示一个精致的 ASCII 蜜蜂图案，甚至可以利用 Braille 字符（盲文符号）绘制更细腻的图形，增加艺术感。

•Header Logo: 在 Dashboard 顶部，左侧显示简洁的 🐝 SKILLBEE 字符，🐝 符号使用琥珀黄高亮。

•蜂巢布局:

•面板分隔: 不使用简单的直线，而是通过 ─╮ ╰─ 等字符组合，模拟蜂巢的连接结构，增加视觉上的“收纳”感。

•分组列表: 选中项前缀使用 ▶ (琥珀黄)，未选中项使用 ◦ (幽灵白)，通过缩进和字符错位营造蜂巢壁的视觉效果。

•动态反馈:

•进度条: 安装/卸载时，进度条不再是静态方块，而是一个琥珀黄的 🐝 字符在进度条上“飞行”，例如 [🐝----] -> [-🐝---]，生动形象。

•操作确认: 用户执行安装/卸载等操作后，相关 Skill 行会产生一个短暂的“琥珀黄 -> 花粉绿”或“琥珀黄 -> 蜂刺红”的渐变闪烁效果，提供强烈的视觉反馈。

### 2.3 布局结构：三栏式“蜂巢 Dashboard”

Skillbee V2 TUI 采用经典的三栏式布局，并辅以顶部 Header 和底部动态操作条，确保信息层级清晰，操作直观。

| 区域 | 名称               | 内容                                                         | 视觉特点                                    |
| ---- | ------------------ | ------------------------------------------------------------ | ------------------------------------------- |
| 顶部 | The Crown (蜂冠)   | 🐝 SKILLBEE Logo、当前 Scope、已选 Skills 数量、当前激活的 Target(s) 概览 | 琥珀黄渐变背景，字符艺术 Logo，关键状态信息 |
| 左侧 | The Hive (蜂巢)    | Skill 分组列表、来源分组、taxonomy 分类、归档/启用状态入口，支持多维筛选 | 选中项高亮，字符艺术分隔，提供筛选条件预览  |
| 中间 | The Cells (蜂房)   | Skill 列表，展示 Skill ID、来源、分类、安装资格、安装状态和简要描述 | 状态图标（✔/◦/—）、颜色区分，支持多选       |
| 右侧 | The Nectar (花蜜)  | 选中 Skill 的详细信息：SKILL.md 预览、Target 安装矩阵、来源状态、include/exclude 原因、相关 Skill 推荐、本地路径 | 信息丰富，布局紧凑，可折叠/展开             |
| 底部 | The Guide (导航蜂) | 动态操作条：根据当前焦点、scope、选中状态和预览状态，实时显示最相关的快捷键提示 | 简洁明了，小白友好，降低学习成本            |



## 3. 核心交互原则：小白化的“所见即所得”

Skillbee V2 的交互设计旨在消除用户学习快捷键的负担，通过直观的视觉反馈和焦点驱动的逻辑，让用户“进场即上手”。

### 3.1 导航与选择：方向键与空格键的艺术

•统一导航: 用户仅需使用 ↑↓←→ 方向键即可完成所有面板间的切换和列表内容的浏览。

•←/→: 在 The Hive (分组) -> The Cells (技能列表) -> The Nectar (详情) 之间切换焦点。

•↑/↓: 在当前焦点面板内上下移动，浏览内容。

•空格键：多选与确认:

•在 The Cells (技能列表) 中，Space 用于选中/取消选中单个 Skill。已选中的 Skill 前缀变为 [✔]，并以琥珀黄高亮。

•在 Target 选择面板中，Space 用于勾选/取消勾选单个 Target。

•Enter 键：进入详情/执行:

•在 The Cells (技能列表) 中，Enter 进入选中 Skill 的 The Nectar (详情) 面板。

•在 Target 选择面板中，Enter 确认选择并返回主界面。

### 3.2 动态操作条 (The Guide)：智能提示

底部操作条不再是静态的快捷键列表，而是根据用户当前焦点和选中状态，动态显示最相关的操作提示。例如：

•在技能列表 (The Cells) 且未选中 Skill 时: [Space] 选中 | [Enter] 详情 | [I] 安装 | [U] 卸载 | [X] 归档

•在技能列表 (The Cells) 且选中多个 Skill 时: [Space] 取消选中 | [Enter] 批量详情 | [I] 批量安装 | [U] 批量卸载 | [X] 批量归档

•在 Target 选择面板时: [Space] 勾选 | [A] 全选 | [Shift+A] 反选 | [Enter] 确认

### 3.3 多 Target 选择机制：丝滑的批量管理

为了实现“丝滑的多 Target 管理体验”，我们提供直观且高效的 Target 选择流程。

•入口: 在主界面按 T 键（或通过底部操作条提示）进入 Target 选择面板。

•选择面板:

•以列表形式展示所有可用的 Target CLI，每个 Target 前面带有勾选框：[✔] claude | [ ] opencode | [✔] cursor。

•用户可以使用 ↑↓ 导航，Space 勾选/取消勾选。

•快捷操作: A 键实现“全选所有 Target”，Shift+A 实现“反选所有 Target”。

•视觉反馈: 已勾选的 Target 以琥珀黄高亮显示。

•确认与应用: 按 Enter 键确认选择，返回主界面。此时，The Crown (蜂冠) 区域会清晰显示当前激活的 Target(s) 概览，所有后续的安装/卸载/同步只作用于这些选中的 Target。

### 3.4 Scope 选择机制：global 与 project 双层独立

Skillbee 必须把 global 与 project 视为两套独立编排 scope。

•Global scope: 面向当前用户的各 CLI 用户级 skills 目录，使用 global 覆盖配置和 global manifest。

•Project scope: 面向运行 `skillbee` 时的当前工作目录，按各 CLI 的项目级规范写入，例如 Claude 写入 `<project>/.claude/skills`，使用 project 覆盖配置和 project manifest。

•切换 scope: TUI 切换 scope 后，The Crown、The Hive、The Cells、The Nectar、同步预览和最终报告都必须展示当前 scope 的配置、安装状态和 manifest 结果。

•隔离规则: global 与 project 互不读取、互不覆盖 manifest；同一个 Skill 在两个 scope 中可以有不同安装状态。

## 4. 核心功能模块：技能生命周期管理

Skillbee V2 的核心功能围绕 Skill 的“生命周期”进行设计，从发现到维护，提供一套完整且直观的管理流程。

### 4.1 模块一：发现与聚合 (Discover & Aggregate)

| 功能点   | 描述                                                         | 交互方式                                  | 视觉反馈                                     |
| -------- | ------------------------------------------------------------ | ----------------------------------------- | -------------------------------------------- |
| 智能聚合 | 自动扫描本地 skills 目录、catalog 来源和 taxonomy 元数据，形成统一可浏览目录。 | 启动时自动完成，无需用户干预。            | The Hive (分组/来源) 面板实时更新分类、来源和数量。 |
| 来源展示 | GitHub、命令型、本地 owned skill 等来源均可展示状态；来源可见不等于默认安装。 | 在来源分组或来源开关面板中查看。          | 显示 enabled、disabled、default-disabled、error 等状态。 |
| 快速搜索 | 按 / 键呼出搜索框，支持 Skill ID、描述、标签、来源、分类的模糊匹配。 | 输入关键词实时过滤 The Cells (技能列表)。 | 搜索框高亮，非匹配项变暗，匹配项琥珀黄高亮。 |



### 4.2 模块二：整理与分类 (Organize & Categorize)

| 功能点     | 描述                                                         | 交互方式                                        | 视觉反馈                                           |
| ---------- | ------------------------------------------------------------ | ----------------------------------------------- | -------------------------------------------------- |
| 多维蜂巢   | 支持按 taxonomy 分类、来源、标签、安装状态和自定义分组筛选；taxonomy 负责发现与展示，不单独决定安装资格。 | 在 The Hive (分组/来源) 面板中选择筛选条件。 | 选中条件高亮，The Cells (技能列表) 实时更新。 |
| 自定义分组 | 用户可在 TUI 中创建、编辑、删除自定义 Skill 分组，并持久化到用户覆盖配置。 | 按 C 创建，E 编辑，D 删除。                     | 新分组出现在 The Hive (分组) 面板，以 ◎ 前缀区分。 |
| 来源启用   | 用户可在 TUI 中启用/禁用来源，或保留来源 visible/searchable 但 default-disabled。 | 在来源面板中切换。                             | 来源状态立即写入用户覆盖 YAML，Skill 列表显示安装资格变化。 |
| Include/Exclude | 用户可对单个 Skill 设置 include 或 exclude，用于覆盖来源默认安装策略。 | 在 Skill 操作菜单中切换。                       | The Nectar 显示最终安装资格及原因。 |



### 4.3 模块三：部署与同步 (Deploy & Synchronize)

| 功能点   | 描述                                                         | 交互方式                                         | 视觉反馈                                                     |
| -------- | ------------------------------------------------------------ | ------------------------------------------------ | ------------------------------------------------------------ |
| 一键授粉 | 根据当前 scope、选中 Target、来源状态和 include/exclude 解析 desired state，并批量同步到目标 CLI 路径。 | 在 The Cells (技能列表) 中选中 Skills 或使用当前过滤结果，按 I 键。 | 先弹出同步预览；确认后显示进度条 🐝 飞行动画和安装报告。 |
| 批量清理 | 批量移除选中 Skills 的 Skillbee 托管安装项，但保留 Skill 源文件，并且不触碰手动文件。 | 在 The Cells (技能列表) 中选中 Skills，按 U 键。 | 先弹出移除预览；确认后弹出卸载报告。 |
| 执行前预览 | 在真实写入前展示将新增、覆盖、移除、跳过的 Target × Skill 操作及 skip reason。 | 点击安装/同步后自动进入确认步骤。 | 用户确认前不会修改任何 CLI skills 目录。 |
| 安装报告 | 操作完成后，以清晰的表格形式展示每个 Target × Skill 的操作结果（success/skipped/failed/removed/overwritten）。 | 自动弹出，按任意键关闭。                         | 成功 (花粉绿 ✔)、跳过 (幽灵白 ○)、失败 (蜂刺红 ✗)，并显示失败原因。 |



### 4.4 模块四：维护与健康 (Maintain & Health)

| 功能点       | 描述                                                         | 交互方式                                            | 视觉反馈                                                     |
| ------------ | ------------------------------------------------------------ | --------------------------------------------------- | ------------------------------------------------------------ |
| 健康监测     | 离线监控 Skill 的完整性（如软链接是否断裂、源文件是否存在），并在 TUI 中提示。 | 自动检测，在 The Cells (技能列表) 中显示异常状态。  | 异常 Skill 行显示“破损蜂巢”图标 💔 (蜂刺红)，并提示 [R] 修复。 |
| Skill 归档   | 将不常用但不想删除的 Skill 标记为归档状态，默认隐藏。        | 在 The Cells (技能列表) 中选中 Skill，按 X 键。     | 归档 Skill 变为深灰色，默认隐藏。按 A 键切换显示/隐藏归档 Skill。 |
| 详情面板强化 | The Nectar (详情) 面板展示 Skill 的完整 SKILL.md 预览、在所有 Target 上的安装状态矩阵、相关 Skill 推荐、本地路径等。 | 在 The Cells (技能列表) 中选中 Skill，按 Enter 键。 | 信息丰富，布局紧凑，支持滚动。Target 安装矩阵使用 ✔/◦/— 符号。 |


### 4.5 模块五：配置编排与安全同步 (Orchestrate & Sync)

Skillbee 的安装行为必须是可解释、可预览、可重复的同步流程。

•安装名单裁决优先级:

1. `exclude` 最强：被 exclude 的 Skill 永不安装，即使来源启用或其他规则 include。
2. 显式 `include` 可以安装来自 default-disabled 来源的单个 Skill。
3. enabled/default-enabled 来源贡献 eligible skills，除非单个 Skill 被 exclude。
4. disabled/default-disabled 来源不参与 bulk install，除非单个 Skill 被显式 include。
5. 已安装但后来不再 eligible 的 Skillbee 托管项，会在下一次同步选中 Target 时被移除。
6. 手动文件永不触碰。

•托管项规则: Skillbee 只覆盖或移除 manifest 记录或带 Skillbee 托管标记的安装项。托管项被用户手动修改后，下一次同步以 Skillbee 解析出的 desired state 为准覆盖。

•默认禁用来源: 例如 `slavingia/skill` 这类 business 来源默认 visible/searchable，但 default-disabled，不参与 bulk install；用户可通过 include 安装其中的单个 Skill。

•命令型来源: 命令生成/拉取的来源仅支持 global scope；在 project scope 中必须显示 skip reason。



## 5. 用户场景 (User Scenarios)

以下是 Skillbee V2 旨在解决的核心用户任务流，体现其“小白化”和“丝滑”的体验。

### 5.1 场景一：首次启动与快速概览

•用户目标: 第一次使用 Skillbee，想快速了解所有可用的 Skills 和当前状态。

•操作序列:

1.用户在终端输入 skillbee 并回车。

2.Skillbee V2 启动，显示精致的 Bee-Art Logo，然后进入三栏式 Dashboard。

3.The Crown (蜂冠) 显示 🐝 SKILLBEE 和总览信息。

4.The Hive (分组) 默认选中“所有 Skills”，The Cells (技能列表) 显示所有 Skills，已安装的 Skills 以花粉绿 ✔ 标记。

5.The Nectar (详情) 显示列表第一个 Skill 的详细信息。

6.The Guide (导航蜂) 动态操作条提示 [Space] 选中 | [Enter] 详情 | [I] 安装 等常用操作。

•用户预期: 一眼看清所有 Skills，知道哪些已安装，并能直观地开始操作。

### 5.2 场景二：批量安装新 Skills 到多个 CLI

•用户目标: 获得一批新的 Skills，想一次性安装到所有常用的 AI CLI 环境中。

•操作序列:

1.用户在 The Cells (技能列表) 中，使用 ↑↓ 导航，Space 键选中多个目标 Skills。

2.按 T 键进入 Target 选择面板。

3.在 Target 选择面板中，按 A 键“全选所有 Target”，然后按 Enter 确认。

4.返回主界面，The Crown (蜂冠) 显示所有 Target 已激活。

5.按 I 键进入同步预览。

6.Skillbee 展示当前 scope + 选中 Target 下将新增、覆盖、移除、跳过的 Target × Skill 操作，以及每个 skip reason。

7.用户确认预览后才执行真实安装；The Cells (技能列表) 中被安装的 Skills 产生渐变闪烁，底部进度条 🐝 飞行。

8.安装完成后，弹出 Target × Skill 粒度的安装报告，包含 success、skipped、failed、removed、overwritten。

9.按任意键关闭报告，Skills 列表状态实时更新。

•用户预期: 执行前知道将发生什么，确认后一次完成同步，结果清晰可见。

### 5.3 场景三：整理与归档不常用 Skills

•用户目标: 整理 Skill 列表，将不常用的 Skills 归档，保持界面整洁。

•操作序列:

1.用户在 The Cells (技能列表) 中，使用 ↑↓ 导航，Space 键选中一个或多个不常用的 Skills。

2.按 X 键执行归档操作。

3.被归档的 Skills 变为深灰色，并从默认视图中消失。

4.The Guide (导航蜂) 提示 [A] 显示/隐藏归档。

5.用户按 A 键，归档 Skills 重新显示，再次按 A 键则隐藏。

•用户预期: 界面保持清爽，归档的 Skills 随时可找回，且状态持久化。

### 5.4 场景四：禁用来源并安全同步

•用户目标: 保留 `slavingia/skill` 这类 business 来源用于搜索和按需安装，但不希望它默认批量安装。

•操作序列:

1.用户在 The Hive 的来源视图中找到该来源。

2.将来源设为 default-disabled 或 disabled，TUI 立即写入当前 scope 的用户覆盖 YAML。

3.用户可搜索该来源中的 Skill，并对少数需要的 Skill 设置 include。

4.按 I 进入同步预览。

5.预览显示被 include 的 Skill 将安装；未 include 且此前由 Skillbee 托管安装的 Skill 将被移除；手动文件不在操作列表中。

6.用户确认后执行，报告按 Target × Skill 展示结果。

•用户预期: 来源仍可发现，但默认不会污染安装目录；同步只处理 Skillbee 托管项。

### 5.5 场景五：project/global 独立安装

•用户目标: 在全局 CLI 中保留一套常用 Skills，同时在当前项目目录安装项目专用 Skills。

•操作序列:

1.用户在 The Crown 切换到 project scope。

2.Skillbee 读取 `<project>/.skillbee/config.yaml` 和 `<project>/.skillbee/manifest.yaml`，并按当前 `pwd` 的 CLI 项目级路径显示安装状态。

3.用户选择 Claude target 和项目所需 Skills，按 I 查看预览。

4.预览显示将写入 `<project>/.claude/skills`，不会影响 global manifest 或用户级 CLI skills 目录。

5.用户切回 global scope 时，界面显示 global 配置、global manifest 和用户级安装状态。

•用户预期: project 与 global 完全独立，切换 scope 不会互相覆盖安装状态。


## 6. 非功能性需求

•性能:

•启动速度: TUI 启动时间应在 1 秒内完成（在典型硬件环境下）。

•响应速度: 列表导航、搜索过滤、面板切换等操作应在 50 毫秒内响应。

•资源占用: 运行时 CPU 和内存占用应保持在较低水平，不影响终端其他操作。

•兼容性:

•操作系统: 支持 Linux, macOS, Windows (通过 WSL 或现代终端如 Windows Terminal)。

•终端模拟器: 兼容主流现代终端（iTerm2, Alacritty, Kitty, Windows Terminal, GNOME Terminal, VS Code Integrated Terminal），并针对 256 色和 Unicode 字符进行优化。

•可靠性:

•离线可用: 所有核心功能（浏览、安装、卸载、归档）在无网络连接环境下均可正常使用。

•数据持久化: 用户配置、自定义分组、Skill 归档状态、来源启用状态、include/exclude、scope manifest 等数据应可靠地持久化到本地 YAML 文件。

•安全同步: 清理或同步仅允许修改 Skillbee 托管项；任何不在 manifest 或托管标记内的手动文件必须保留。

•错误处理: 针对文件读写失败、软链接创建失败、命令型来源不可用于 project scope、目标 CLI 路径不可写等异常情况，提供友好的错误提示和恢复机制。

•可维护性:

•代码结构: 采用模块化设计，代码清晰，易于理解和扩展。

•测试覆盖: 核心逻辑应有充分的单元测试和集成测试。

## 7. 技术约束与数据模型

### 7.1 本地文件结构

Skillbee V2 依赖分层 YAML 与 manifest 进行数据管理。

•仓库默认层: repository 内的 catalog、taxonomy、source 定义和目标 CLI 路径规范。TUI 不直接修改这一层。

•Global 覆盖配置: `~/.config/skillbee/global/config.yaml`，记录 global scope 的 source 启用状态、skill include/exclude、归档状态、默认 Target、UI 偏好等。

•Global manifest: `~/.config/skillbee/global/manifest.yaml`，记录 global scope 中 Skillbee 托管安装项的来源、目标、路径和状态。

•Project 覆盖配置: `<project>/.skillbee/config.yaml`，记录当前项目 scope 的覆盖配置。

•Project manifest: `<project>/.skillbee/manifest.yaml`，记录当前项目 scope 中 Skillbee 托管安装项。

•日志目录: `~/.config/skillbee/logs/`，记录同步预览、执行结果和错误信息。

Global 与 project manifest 互不共享；同步时只读取当前 scope 的覆盖配置和 manifest。

### 7.2 Skill 定义

每个 Skill 仍然通过其目录下的 SKILL.md 和 taxonomy.yaml 进行定义，Skillbee V2 将强化对 taxonomy.yaml 中 group、tags、source、description 等字段的解析和利用。

Taxonomy 和 catalog 负责发现、展示、搜索和默认分组；最终安装资格由仓库默认层与用户覆盖层合并后裁决。

### 7.3 Source 与 Eligibility 数据模型

每个 source 至少应能表达以下状态和策略：

•visible/searchable: 是否参与展示与搜索。

•defaultEnabled/defaultDisabled: 是否默认参与 bulk install。

•user enabled/disabled override: 用户覆盖配置中的来源启用状态。

•include/exclude: 用户对单个 Skill 的白名单/黑名单。

•scope support: 来源是否支持 global、project 或二者；命令型来源仅支持 global。

最终 eligibility 必须可解释，TUI 需要能展示“为什么这个 Skill 会安装、跳过或移除”。

### 7.4 Target CLI 管理

Target CLI 的配置将简化为一组按 scope 区分的路径规范。Global scope 写入各 CLI 的用户级 skills 目录；project scope 写入当前 `pwd` 下各 CLI 的项目级 skills 目录，例如 Claude 为 `<project>/.claude/skills`。

Skillbee 负责在这些路径下创建、覆盖、移除 Skillbee 托管项。安装前的清理只清理 manifest 或托管标记识别出的 Skillbee 托管项，不清空用户手动放入的文件。

### 7.5 同步事务模型

每次安装/同步必须按以下步骤执行：

1.加载仓库默认层和当前 scope 的用户覆盖 YAML。
2.解析当前 scope + 选中 Target 的 desired state。
3.检查目标 CLI skills 目录和当前 scope manifest。
4.生成 create、update、overwrite、remove、skip 的同步预览，并显示 skip reason。
5.用户确认后才执行文件系统写入。
6.执行成功后更新当前 scope manifest。
7.生成 Target × Skill 粒度的执行报告。

真实验收可以使用用户当前真实 global CLI skills 目录，但仍必须经过同步预览确认。



## 8. 验收要求

### 8.1 配置编排验收

•默认禁用来源仍可展示和搜索，但不参与 bulk install。

•显式 include 可以安装 default-disabled 来源中的单个 Skill。

•exclude 优先级最高：即使来源启用或 Skill 被 include，也不得安装。

•禁用来源后，下一次同步选中 Target 时，已不再 eligible 的 Skillbee 托管项会被移除。

•TUI 修改来源启用、include/exclude、归档、scope/target 偏好后，立即写入用户覆盖 YAML，不修改仓库默认 catalog/taxonomy。

### 8.2 安全同步验收

•同步只作用于当前 scope 和选中的 CLI Target。

•执行前预览必须准确列出新增、覆盖、移除、跳过及 skip reason。

•用户确认预览前不得修改任何 CLI skills 目录。

•同步只覆盖或移除 Skillbee 托管项；手动文件必须保留。

•托管项被手动修改后，下一次同步以 Skillbee desired state 覆盖。

•最终报告必须按 Target × Skill 展示 success、skipped、failed、removed、overwritten。

### 8.3 Scope 验收

•Global 与 project 使用独立覆盖配置和 manifest，互不干扰。

•Project scope 必须安装到当前 `pwd` 的 CLI 项目级路径，例如 Claude 的 `<project>/.claude/skills`。

•Command-based source 在 project scope 中必须跳过，并给出清晰 skip reason。

•真实 global 目录验收允许操作当前用户的真实 CLI skills 目录，但必须先展示并确认预览。

## 9. 未来展望

Skillbee V2 专注于个人技能管理的核心体验。未来可能的迭代方向包括：

•Skill 版本管理: 支持 Skills 的版本更新与回滚。

•Skill 模板: 提供创建新 Skill 的向导和模板。

•更丰富的 Skill 类型: 支持非 CLI 类型的个人技能管理。


## 10. v3 Acceptance Status

| ID | Status | Evidence |
|----|--------|----------|
| ACC-01 | Covered | Automated tests cover include/exclude priority, default-disabled source behavior, and project/global override isolation in `tests/manager/manager-operations.test.ts` and `tests/config/user-config.test.ts`. |
| ACC-02 | Covered | Automated tests cover selected-target sync, manual-file preservation, stale managed removal, and preview no-write behavior in `tests/bootstrap/direct-target-sync.test.ts`. |
| ACC-03 | Covered | Project-scope manager tests verify installs write into project-local CLI paths such as `<project>/.claude/skills` instead of real global homes. |
| ACC-04 | Gated manual acceptance | Real global-directory acceptance requires preview confirmation and explicit user approval before Skillbee writes to actual current-user CLI skills directories. Automated acceptance uses temporary homes/project directories and must not mutate real user homes. |
| ACC-05 | Covered | This PRD checklist is tracked by `tests/acceptance/v3-acceptance.test.ts` and the Phase 9-13 verification artifacts under `.planning/phases/`. |

Real global verification procedure: run a dry-run or preview first, review the Target × Skill operation list, then proceed only after explicit user approval. Without that approval, verification remains limited to temporary homes and project-scope fixtures.
