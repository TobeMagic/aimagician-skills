# Catalog YAML 配置说明

这份文档专门解释 [catalog](D:\Growth_up_youth\repo\skills\catalog) 下面的 YAML 配置。

如果你现在的目标是：

- 用你自己的本地 skills
- 加上 Claude 官方 skills
- 加上 GSD
- 再声明 Claude 官方 plugins

那你只需要看这份文档，不需要自己猜 YAML 格式。

## 1. 先理解目录

这个项目把外部配置分成两类：

```text
catalog/
  skills/
    *.yaml
  plugins/
    *.yaml
```

含义是：

- `catalog/skills/*.yaml`
  管理 skill 类来源
- `catalog/plugins/*.yaml`
  管理 plugin 类来源

你自己写的本地 skill 不在这里配，它们直接放在：

```text
skills/owned/<skill-id>/SKILL.md
```

## 2. 最核心的 YAML 结构

每个 YAML 文件的顶层都是：

```yaml
sources:
  - id: some-source
    type: github
```

也就是说，一个文件里可以放一个或多个 source。

每个 source 常见字段：

```yaml
sources:
  - id: some-source
    type: github
    enabled: true
    description: source description
    targets:
      include:
        - claude
    github:
      repo: owner/repo
      ref: main
      path: skills
    assets:
      - id: some-asset
        kind: skill
        path: some-asset/SKILL.md
```

字段解释：

- `id`
  这个 source 的唯一名字
- `type`
  目前常用两种：
  - `github`
  - `command`
- `enabled`
  `true` 表示启用，`false` 表示先保留配置但不执行
- `description`
  备注说明
- `targets.include`
  只给哪些 CLI 安装
- `github.repo`
  GitHub 仓库，格式 `owner/repo`
- `github.ref`
  分支、tag 或 commit，通常写 `main`
- `github.path`
  仓库里的子目录
- `assets`
  这个 source 里实际要拿哪些 asset
- `assets[].id`
  这个 asset 在你项目里的名字
- `assets[].kind`
  `skill` 或 `plugin`
- `assets[].path`
  这个 asset 在远程仓库里的实际路径

## 3. `github` source 和 `command` source 的区别

### `github`

意思是：
从某个 GitHub 仓库拉内容，然后把你指定的 asset 装进目标 CLI。

例子：

```yaml
sources:
  - id: claude-official
    type: github
    enabled: true
    github:
      repo: anthropics/skills
      ref: main
      path: skills
    assets:
      - id: docx
        kind: skill
        path: docx/SKILL.md
```

### `command`

意思是：
这个 source 不走“复制目录”安装，而是直接执行一个命令。

例子：

```yaml
sources:
  - id: gsd
    type: command
    enabled: true
    targets:
      include:
        - claude
    command:
      run: npx get-shit-done-cc@latest --global
    assets:
      - id: gsd
        kind: skill
```

这类 source 适合：

- 上游本身就有自己的安装命令
- 你不想自己复制它的 skill 目录
- 你只想让这个仓库统一调度它

## 4. 你当前仓库正在使用的配置

你现在的 `catalog` 已经换成真实可用配置，不是示例了。

### 4.1 Claude 官方 skills

文件：

- [catalog/skills/claude-official.yaml](D:\Growth_up_youth\repo\skills\catalog\skills\claude-official.yaml)

内容：

```yaml
sources:
  - id: claude-official
    type: github
    enabled: true
    description: Anthropic official skills from anthropics/skills
    github:
      repo: anthropics/skills
      ref: main
      path: skills
    assets:
      - id: docx
        kind: skill
        path: docx/SKILL.md
      - id: pdf
        kind: skill
        path: pdf/SKILL.md
      - id: pptx
        kind: skill
        path: pptx/SKILL.md
      - id: xlsx
        kind: skill
        path: xlsx/SKILL.md
      - id: frontend-design
        kind: skill
        path: frontend-design/SKILL.md
      - id: webapp-testing
        kind: skill
        path: webapp-testing/SKILL.md
      - id: mcp-builder
        kind: skill
        path: mcp-builder/SKILL.md
      - id: skill-creator
        kind: skill
        path: skill-creator/SKILL.md
```

它的意思是：

- 从 `anthropics/skills` 仓库读取
- 仓库里的根目录是 `skills/`
- 只取你列出来的这些 skills

如果你以后想再加一个官方 skill，只需要在 `assets:` 里继续追加：

```yaml
      - id: some-skill
        kind: skill
        path: some-skill/SKILL.md
```

### 4.2 GSD

文件：

- [catalog/skills/gsd.yaml](D:\Growth_up_youth\repo\skills\catalog\skills\gsd.yaml)

内容：

```yaml
sources:
  - id: gsd
    type: command
    enabled: true
    description: Install or update Get Shit Done for Claude Code
    targets:
      include:
        - claude
    command:
      run: npx get-shit-done-cc@latest --global
    assets:
      - id: gsd
        kind: skill
```

它的意思是：

- 这个 source 不走 GitHub 复制
- 直接执行 `npx get-shit-done-cc@latest --global`
- 目标只针对 `claude`

如果你以后想先停用 GSD，可以改成：

```yaml
enabled: false
```

### 4.3 Claude 官方 plugins

文件：

- [catalog/plugins/claude-official-plugins.yaml](D:\Growth_up_youth\repo\skills\catalog\plugins\claude-official-plugins.yaml)

内容：

```yaml
sources:
  - id: claude-official-plugins
    type: github
    enabled: true
    description: Anthropic official Claude plugins catalog
    targets:
      include:
        - claude
    github:
      repo: anthropics/claude-plugins-official
      ref: main
      path: external_plugins
    assets:
      - id: asana
        kind: plugin
        path: asana
      - id: context7
        kind: plugin
        path: context7
      - id: firebase
        kind: plugin
        path: firebase
      - id: github
        kind: plugin
        path: github
      - id: gitlab
        kind: plugin
        path: gitlab
      - id: greptile
        kind: plugin
        path: greptile
      - id: laravel-boost
        kind: plugin
        path: laravel-boost
      - id: linear
        kind: plugin
        path: linear
      - id: playwright
        kind: plugin
        path: playwright
      - id: serena
        kind: plugin
        path: serena
      - id: slack
        kind: plugin
        path: slack
      - id: stripe
        kind: plugin
        path: stripe
      - id: supabase
        kind: plugin
        path: supabase
```

它的意思是：

- 从 `anthropics/claude-plugins-official` 仓库读取
- 仓库里的插件目录是 `external_plugins/`
- 你现在已经把官方插件目录里的主要插件都声明进来了

注意：

- 这份配置现在是“声明 + 识别”
- 当前项目对 `claude` plugin 仍然是显式 `skip`
- 也就是会告诉你“我认得这些插件配置”，但不会替你自动完成 Claude 官方插件安装

这是当前项目的设计边界，不是 YAML 写错。

## 5. 你以后最常见的改法

### 5.1 我想减少 Claude 官方 skills，只保留几个

直接删掉不想要的 `assets` 条目即可。

例如你只保留：

```yaml
assets:
  - id: docx
    kind: skill
    path: docx/SKILL.md
  - id: pdf
    kind: skill
    path: pdf/SKILL.md
```

### 5.2 我想新增一个 GitHub skills 仓库

在 `catalog/skills/` 新建一个 YAML，例如：

```text
catalog/skills/my-extra-skills.yaml
```

写：

```yaml
sources:
  - id: my-extra-skills
    type: github
    enabled: true
    targets:
      include:
        - codex
        - claude
    github:
      repo: owner/repo
      ref: main
      path: skills
    assets:
      - id: review-helper
        kind: skill
        path: review-helper/SKILL.md
```

### 5.3 我想新增一个 command 安装器

在 `catalog/skills/` 新建：

```yaml
sources:
  - id: some-installer
    type: command
    enabled: true
    targets:
      include:
        - claude
    command:
      run: npx some-package@latest install
    assets:
      - id: some-installer
        kind: skill
```

### 5.4 我想只针对某个 CLI

这样写：

```yaml
targets:
  include:
    - claude
```

或者：

```yaml
targets:
  include:
    - codex
    - opencode
```

### 5.5 我想暂时禁用某个 source

最简单：

```yaml
enabled: false
```

## 6. 这套配置实际会发生什么

按你现在这套 catalog，运行 bootstrap 时：

### skills/owned

你自己写在 `skills/owned/*` 里的 skills 会直接参与安装。

### claude-official

会从 Anthropic 官方 skills 仓库取你列出来的 skill。

### gsd

会执行：

```bash
npx get-shit-done-cc@latest --global
```

### claude-official-plugins

会被识别为 plugin catalog。

但是当前结果是：

- 对 Claude：显式 skip
- 不会假装已经装好了

## 7. 你现在最应该怎么用

如果你想保持现在的默认配置，直接用：

```bash
npm run bootstrap
```

如果你只想先装 Claude 相关：

```bash
npm run bootstrap -- --target claude
```

安装后你可以用：

```bash
node dist/cli/index.js list
node dist/cli/index.js inspect --target claude
node dist/cli/index.js doctor
```

## 8. 一句话规则

你以后只要记住这几个点就够了：

- 你自己的 skill 放 `skills/owned/`
- GitHub skills 放 `catalog/skills/*.yaml`
- command 安装器也放 `catalog/skills/*.yaml`
- plugin 放 `catalog/plugins/*.yaml`
- 不想启用就改 `enabled: false`
- 改完后重新跑 `bootstrap`
