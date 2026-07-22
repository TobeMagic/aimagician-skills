---
name: github-readme-highstar
description: |
  生成或重构“高星仓库风格”的 GitHub README，重点是层级分明、视觉元素统一、信息入口明确。
  当用户提到“README 规范化”“高质量项目首页”“万级 star 风格 README”“模板化仓库说明”、
  “README 封面 / Banner / Hero”“Github 项目品牌视觉”“产品展示”“README Demo 视频 / GIF 动态封面”时触发。
  适用于开源项目 README、合集型 README、个人项目主页，以及仓库首屏视觉与产品媒体集成。
compatibility:
  tools:
    - bash
    - browser
    - playwright
  requires: 仓库至少有可提取的信息源（代码目录、安装命令、示例或文档）
category: documents
subcategory: readme
tags:
  - readme
  - docs
  - github
  - cover
  - project-branding
metadata:
  preferred_companions:
    - interface-design
---

# GitHub README Highstar

## Core Objective

这类 README 不是“堆字数”，而是控制阅读成本：

1. 层级分明
2. 视觉元素统一
3. 信息入口明确

## Trigger Scenarios

- 用户要求“把 README 做成高 star 仓库风格”
- 用户要求“重写项目首页，支持目录锚点和跳转”
- 用户要求“中英文 README 统一样式”
- 用户要求“补充徽章、截图、贡献流程、许可证”
- 用户要求“README 封面图 / hero cover / 首屏视觉图”
- 用户要求“Github 项目品牌视觉 / 产品展示 / Launcher Screens”
- 用户要求“README 产品 Demo / 动态封面 / 自动播放 GIF / 宣传视频”

用户不需要显式指定 `interface-design`。只要请求包含封面、Banner、Hero、海报、产品展示、Launcher Screens、Demo 视频或仓库品牌视觉，就先路由视觉工作给 `interface-design`，再由本 Skill 完成 README 信息结构与集成。

## Capability Boundary

| Work | Owner |
|---|---|
| 项目定位、README 结构、标题层级、徽章、TOC、文案、链接、Markdown 集成 | `github-readme-highstar` |
| 封面、Banner、海报、产品展示、Launcher 图、视觉方向、HTML/Canvas 源、Poster、GIF、MP4 与视觉 QA | `interface-design` |
| 真实主题图片或质感素材 | 可由已启用的图像 Skill 提供素材，但不能替代产品理解、排版、产品证明和 README 集成 |

两个 Skill 共用同一份产品事实与视觉 brief，不能分别编造产品故事。

## Workflow

1. 信息盘点
   - 明确项目定位（一句话）
   - 明确目标读者（使用者 / 贡献者 / 面试官）
   - 收集最关键命令（安装、运行、验证）
   - 从代码、测试和当前文档核对产品名、版本、能力、Launcher、链接与已交付边界
2. 结构设计
   - 先定目录结构和锚点，再填内容
   - 长文档必须有 TOC（Table of Contents）
3. 视觉统一
   - 顶部优先放经过产品理解和视觉验证的封面图
   - 仅保留少量高价值徽章（版本、许可证、CI）
   - 用真实截图、流程、表格或对照替代冗长段落
4. 入口优化
   - 顶部给出快速开始路径
   - 中部给出功能与架构入口
   - 尾部给出贡献、许可证、联系方式

## Repository Visual Workflow

当请求涉及封面、Banner、Hero、Poster、Launcher 或 Demo 时，执行完整视觉链路，而不是把需求降级为“生成一张图”：

1. **项目理解**：读取代码入口、当前 README、项目文档、真实 Launcher、版本与产品资产，区分已交付、计划中和过时内容。
2. **定位与受众**：明确产品类别、用户、首屏要支持的决策，以及一个主信息和一个真实产品证明。
3. **视觉方向**：由 `interface-design` 产出恰好 3 个构图、字体、颜色、产品证明和动效均有实质差异的真实方向；锁定方向后再完整制作。只有已接受方向、小修或机械导出可记录原因后跳过。
4. **素材与源文件**：优先使用真实产品 UI、终端、工作流、对象或数据。保留可编辑 HTML/CSS/JS、SVG 或 Canvas 源，不把整套设计交给一次性图片 Prompt。
5. **资产渲染**：建议 README Hero 使用项目确认的宽屏尺寸；Launcher 图使用稳定统一的比例。短、静音、循环的仓库首屏优先导出体积受控的 GIF；长、高清或含音频的演示使用 MP4 与静态 Poster。
6. **README 集成**：可将仓库内相对路径 GIF 作为自动播放首屏。不要依赖 GitHub user-attachment URL 作为可复现源。MP4 作为补充渠道，静态内容与 alt 文本必须让 README 在动效不可用时仍可理解。
7. **验收**：检查全尺寸与 README 缩放尺寸、浅色/深色背景、alt 文本、相对路径、文件大小、事实一致性、浏览器错误和媒体参数。

详细协作与验收协议见 `references/readme-visual-integration.md`。

## Recommended Section Order

1. 项目标题 + 一句话定位
2. 徽章（适量）
3. 目录（TOC + anchors）
4. 快速开始（3-5 条命令内可跑通）
5. 功能亮点 / 特性
6. 使用示例（代码块 + 结果）
7. 项目结构
8. 配置说明
9. 常见问题（可选）
10. 贡献指南
11. 许可证
12. 联系方式 / 致谢

## Guardrails

- 不要堆过多徽章，避免“视觉噪音”。
- 不要让“安装”和“第一条可运行命令”超过首屏太远。
- 避免无信息增量的营销词。
- 不要使用过时版本、旧品牌名、伪造终端输出、虚构指标或未交付功能填充视觉。
- 不要把通用 AI 插画当作产品证明；开发者工具优先展示真实终端、编辑器、Diff、构建、测试或数据流。
- 不要让动态媒体成为唯一信息来源；GIF 首帧、alt 文本和后续静态产品图必须让核心信息可理解。
- 若内容很长，必须有目录与分段锚点。

## Output Contract

交付 README 时，至少满足：

- 有经过产品事实核对和最终尺寸验证的封面图（如用户未禁用视觉元素）
- 有一句话定位
- 有 TOC
- 有快速开始
- 有示例
- 有贡献与许可证
- 链接可点击、命令可复制
- 动态媒体使用仓库内相对路径，满足循环与文件预算，并有独立可理解的静态 README 内容

## Reusable Guidance

具体模板和结构检查清单见：

- `./references/readme-blueprint.md`
- `./references/readme-visual-integration.md`
