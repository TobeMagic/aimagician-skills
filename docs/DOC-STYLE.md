# GitHub 高 Star README 规范（React 风格）

> 目标：采用高 star 开源仓库常见的 README 结构，让仓库首页在 30 秒内回答 4 个问题：  
> 1) 这是啥；2) 我怎么用；3) 我遇到问题去哪；4) 我怎么参与贡献。

---

## 1. 参考基线（直接对齐对象）

本规范优先参考以下高 star 仓库 README 的结构特征：

- React: https://github.com/facebook/react
- TypeScript: https://github.com/microsoft/TypeScript
- Node.js: https://github.com/nodejs/node
- TensorFlow: https://github.com/tensorflow/tensorflow

这些项目共同特征：

- 顶部一句话价值主张（one-line value proposition）
- 明确安装/运行路径
- 文档入口聚合而不是堆满细节
- 社区与贡献路径清晰
- License、Security、Code of Conduct 边界明确

---

## 2. README 顶层结构（推荐顺序）

严格建议按下面顺序组织：

1. 项目名 + 一句话定位  
2. Badges（可选，但建议）  
3. Quick Start（最短可运行路径）  
4. Features / Why（3~7 条）  
5. Installation / Usage（按用户任务拆）  
6. Docs 导航（把长文挪到 docs）  
7. FAQ / Troubleshooting（常见失败）  
8. Contributing / Code of Conduct  
9. Security（若有）  
10. License

不要在 README 首页塞入大段架构细节；细节统一下沉到 `docs/`。

---

## 3. “React 风格”写法要求

### 3.1 顶部必须短

- 第一屏只保留“是什么 + 立即开始”。
- 避免开场长背景故事。
- 一句话长度建议 15~30 个词。

### 3.2 Quick Start 必须可复制

- 至少 1 条“开箱路径”命令块（从 clone 到 first success）。
- 命令必须能直接粘贴执行，禁止伪命令。
- 示例中的 token 一律占位符，不能真实泄露。

### 3.3 文档入口必须有“任务导向”

文档链接按任务分组，而不是按文件名平铺：

- 配置：`catalog` / YAML
- 安装：bootstrap/list/inspect/doctor
- 图像：文生图 / 图生图
- 工作流：GSD / 自动化

### 3.4 贡献入口必须明确

- README 中必须有 Contributing 链接或段落。
- Issue 使用边界要写明（例如：问题反馈 vs feature 请求）。

---

## 4. 中文主文档 + 英文镜像规则

- 根 README 默认中文（Chinese-first）。
- 英文版提供快速镜像：`docs/README.en.md`。
- 两者结构保持同构：章节名字可不同，但信息层次一致。
- 英文镜像可缩短，但 Quick Start/Usage/Docs/License 不能缺。

---

## 5. README 长度与信息密度

- 推荐总长度：150~350 行。
- 单段不超过 6 行。
- 列表优先于大段散文。
- 一个章节只解决一个认知问题，避免混合主题。

---

## 6. 命令与配置示例规范

- 所有命令块必须标注语言：`bash` / `yaml` / `json`。
- 配置片段遵循“最小可运行 + 进阶示例”双档。
- 参数说明按“必填 / 可选 / 默认值”组织。
- 提供验证命令（如 `doctor`）形成闭环。

---

## 7. 图像能力（文生图 / 图生图）展示规范

若仓库提供图像相关能力，README 必须同时展示：

1. 文生图最短命令（text-to-image）
2. 图生图最短命令（image-to-image）
3. 必要环境变量
4. 一条失败排障提示

示例必须可直接执行，不依赖读者猜参数。

---

## 8. Badges 策略（高 star 仓库常见做法）

建议保留 3~6 个高价值 badge，避免“徽章墙”：

- License
- npm/pypi version（如有发布）
- CI status
- Security / Scorecard（可选）
- PR welcome（可选）

不要堆几十个 badge 影响首屏信息读取。

---

## 9. 反模式（必须避免）

- 首屏全是背景和历史，没有可执行路径。
- README 混入机器绝对路径（如 `D:\...`、`/mnt/...`）。
- 配置示例过长且缺字段解释。
- 把未验证功能写成“已支持”。
- 真实 token / cookie 出现在文档或截图中。

---

## 10. 本仓库执行模板（可直接复用）

建议根 README 按以下骨架维护：

```text
项目名 + 一句话定位
英文入口链接

核心能力（3~7条）
Quick Start
常用命令
文生图/图生图
支持矩阵
目录结构
文档导航
用户级安装路径
验证与排障
Contributing
License
```

---

# GitHub High-Star README Style Guide (EN)

This repository follows a high-star README pattern inspired by React/TypeScript/Node/TensorFlow:

- one-line value proposition at the top
- runnable quick start path
- task-oriented docs navigation
- explicit contribution boundaries
- clear license/security/coc links

If a section does not improve first-time adoption, move it from root README into `docs/`.
