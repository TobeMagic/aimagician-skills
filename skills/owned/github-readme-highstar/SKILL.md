---
name: github-readme-highstar
description: |
  生成或重构“高星仓库风格”的 GitHub README，重点是层级分明、视觉元素统一、信息入口明确。
  当用户提到“README 规范化”“高质量项目首页”“万级 star 风格 README”“模板化仓库说明”时触发。
  适用于开源项目 README、合集型 README、个人项目主页 README 的结构升级。
compatibility:
  tools: [bash]
  requires: 仓库至少有可提取的信息源（代码目录、安装命令、示例或文档）
---

# GitHub README Highstar

Reference:

- `https://github.com/shaojintian/Best_README_template`

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

## Workflow

1. 信息盘点
   - 明确项目定位（一句话）
   - 明确目标读者（使用者 / 贡献者 / 面试官）
   - 收集最关键命令（安装、运行、验证）
2. 结构设计
   - 先定目录结构和锚点，再填内容
   - 长文档必须有 TOC（Table of Contents）
3. 视觉统一
   - 仅保留少量高价值徽章（版本、许可证、CI）
   - 用截图、卡片、对照表替代冗长段落
4. 入口优化
   - 顶部给出快速开始路径
   - 中部给出功能与架构入口
   - 尾部给出贡献、许可证、联系方式

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
- 若内容很长，必须有目录与分段锚点。

## Output Contract

交付 README 时，至少满足：

- 有一句话定位
- 有 TOC
- 有快速开始
- 有示例
- 有贡献与许可证
- 链接可点击、命令可复制

## Reusable Guidance

具体模板和结构检查清单见：

- `./references/readme-blueprint.md`
