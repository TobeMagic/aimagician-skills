# Catalog YAML 配置说明

这份文档专门解释 [catalog](D:\Growth_up_youth\repo\skills\catalog) 下面的 YAML 怎么写，重点回答这几个问题：

- `github.path` 到底该写什么
- `assets` 是不是必须写
- Claude 官方 `skills` 仓库和 `plugins` 仓库应该怎么配
- 我只想“默认全量”时该怎么写
- 我只想拿一部分时该怎么写

## 1. 先记住最重要的规则

### 规则 1: `github.path` 指的是“仓库里的父目录”

它不是单个 skill，也不是单个 plugin。

比如：

- `anthropics/skills` 里，skills 放在 `skills/`
- `anthropics/claude-plugins-official` 里，对 Claude 官方目录插件，这个项目现在用的是 `external_plugins/`

所以你通常会这样写：

```yaml
github:
  repo: anthropics/skills
  ref: main
  path: skills
```

或者：

```yaml
github:
  repo: anthropics/claude-plugins-official
  ref: main
  path: external_plugins
```

### 规则 2: `assets` 对 `github` source 现在可以省略

如果你省略 `assets`，这个项目会自动“拿全部”。

自动展开规则是：

- `catalog/skills/*.yaml`
  扫描 `github.path` 下的一级子目录；只要该目录里有 `SKILL.md`，就算一个 skill
- `catalog/plugins/*.yaml`
  扫描 `github.path` 下的一级子目录，以及一级 `.js/.cjs/.mjs/.ts/.cts/.mts` 文件

### 规则 3: `command` source 仍然必须写 `assets`

因为命令型 source 没法从远程目录结构里自动推断要安装什么。

## 2. 目录分工

```text
skills/
  owned/
    <skill-id>/
      SKILL.md

catalog/
  skills/
    *.yaml
  plugins/
    *.yaml
```

含义：

- `skills/owned/`
  你自己仓库里直接维护的 skills
- `catalog/skills/*.yaml`
  外部 skill source，或者 command installer
- `catalog/plugins/*.yaml`
  外部 plugin source

## 3. 最小 YAML 结构

### 3.1 GitHub source

```yaml
sources:
  - id: some-source
    type: github
    enabled: true
    github:
      repo: owner/repo
      ref: main
      path: skills
```

这已经是有效配置了。

含义是：

- 从 `owner/repo` 拉取
- 以 `skills/` 作为父目录
- `assets` 没写，所以默认扫描并拿全量

### 3.2 Command source

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

这类 source 不是复制仓库目录，而是直接执行命令。

## 4. 字段到底什么意思

### 顶层字段

- `id`
  这个 source 在本项目里的名字
- `type`
  目前主要是 `github` 或 `command`
- `enabled`
  是否启用；`false` 时保留配置但不参与安装
- `description`
  说明文字
- `targets`
  这个 source 默认要给哪些 CLI 用

### `github` 字段

- `github.repo`
  GitHub 仓库，格式 `owner/repo`
- `github.ref`
  分支、tag 或 commit；一般写 `main`
- `github.path`
  仓库里用于扫描 assets 的父目录

### `assets` 字段

- `assets`
  这个 source 里要取哪些具体 asset
- `assets[].id`
  在本项目里的 asset id
- `assets[].kind`
  `skill` 或 `plugin`
- `assets[].path`
  该 asset 在 `github.path` 下面的相对路径

补一句最容易混淆的点：

- `assets` 永远是数组
- 单个 asset 也要写成 `assets:` 加一个 `-`
- 多个 assets 就是在 `assets:` 下面连续写多个 `-`

例如，单个 asset：

```yaml
assets:
  - id: docx
    kind: skill
    path: docx
```

多个 assets：

```yaml
assets:
  - id: docx
    kind: skill
    path: docx
  - id: pdf
    kind: skill
    path: pdf
  - id: xlsx
    kind: skill
    path: xlsx
```

## 5. “默认全部”到底怎么工作

### 5.1 Skills

如果你这样写：

```yaml
sources:
  - id: claude-official
    type: github
    github:
      repo: anthropics/skills
      ref: main
      path: skills
```

那么程序会去看：

```text
anthropics/skills
└─ skills/
   ├─ docx/
   │  └─ SKILL.md
   ├─ pdf/
   │  └─ SKILL.md
   └─ ...
```

然后自动把每个 `*/SKILL.md` 所在目录识别成一个 skill。

也就是说：

- `docx/` 会变成 asset `docx`
- `pdf/` 会变成 asset `pdf`
- `frontend-design/` 会变成 asset `frontend-design`

### 5.2 Plugins

如果你这样写：

```yaml
sources:
  - id: claude-official-plugins
    type: github
    targets:
      include:
        - claude
    github:
      repo: anthropics/claude-plugins-official
      ref: main
      path: external_plugins
```

那么程序会去看：

```text
anthropics/claude-plugins-official
└─ external_plugins/
   ├─ github/
   ├─ linear/
   ├─ playwright/
   └─ ...
```

然后自动把每个一级目录识别成一个 plugin asset。

也就是说：

- `github/` 会变成 asset `github`
- `linear/` 会变成 asset `linear`
- `playwright/` 会变成 asset `playwright`

## 6. 你当前仓库里的真实配置

### 6.1 Claude 官方 skills

文件：

- [claude-official.yaml](D:\Growth_up_youth\repo\skills\catalog\skills\claude-official.yaml)

现在就是最简写法：

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
```

意思：

- 父目录是 `skills/`
- `assets` 没写
- 所以默认拿 `skills/` 下全部官方 skills

### 6.2 GSD

文件：

- [gsd.yaml](D:\Growth_up_youth\repo\skills\catalog\skills\gsd.yaml)

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

意思：

- 不走 GitHub 目录复制
- 直接执行 `npx get-shit-done-cc@latest --global`
- 这类 source 仍然要写 `assets`

### 6.3 Claude 官方 plugins

文件：

- [claude-official-plugins.yaml](D:\Growth_up_youth\repo\skills\catalog\plugins\claude-official-plugins.yaml)

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
```

意思：

- 父目录是 `external_plugins/`
- `assets` 没写
- 所以默认拿 `external_plugins/` 下全部官方目录插件

注意当前边界：

- 这些 plugin 现在能被识别、列出、纳入 plan
- 对 `claude` 目标仍然是显式 skip
- 也就是“知道它们存在”，但不会冒充已经自动安装进 Claude Code

## 7. 如果你只想拿一部分，不要默认全部

这时就把 `assets` 写出来。

### 7.1 单个官方 skill

```yaml
sources:
  - id: claude-official
    type: github
    targets:
      include:
        - claude
    github:
      repo: anthropics/skills
      ref: main
      path: skills
    assets:
      - id: docx
        kind: skill
        path: docx
```

### 7.2 多个官方 skills

```yaml
sources:
  - id: claude-official
    type: github
    targets:
      include:
        - claude
    github:
      repo: anthropics/skills
      ref: main
      path: skills
    assets:
      - id: docx
        kind: skill
        path: docx
      - id: pdf
        kind: skill
        path: pdf
      - id: xlsx
        kind: skill
        path: xlsx
```

这里的 `path` 对应的是 `skills/` 下面的目录名，不需要再写成 `docx/SKILL.md`。

### 7.3 单个官方 plugin

```yaml
sources:
  - id: claude-official-plugins
    type: github
    targets:
      include:
        - claude
    github:
      repo: anthropics/claude-plugins-official
      ref: main
      path: external_plugins
    assets:
      - id: github
        kind: plugin
        path: github
```

### 7.4 多个官方 plugins

```yaml
sources:
  - id: claude-official-plugins
    type: github
    targets:
      include:
        - claude
    github:
      repo: anthropics/claude-plugins-official
      ref: main
      path: external_plugins
    assets:
      - id: github
        kind: plugin
        path: github
      - id: linear
        kind: plugin
        path: linear
```

这里的 `path` 对应的是 `external_plugins/` 下面的目录名。

## 8. OpenCode plugin 的一个特殊点

对 OpenCode 自动安装 plugin 时，当前要求 asset 必须是明确的 JavaScript 或 TypeScript 文件。

也就是说，如果你要给 OpenCode 装 plugin，建议这样写：

```yaml
sources:
  - id: opencode-tools
    type: github
    targets:
      include:
        - opencode
    github:
      repo: owner/opencode-plugins
      ref: main
      path: plugins
    assets:
      - id: audit-helper
        kind: plugin
        path: audit-helper.ts
```

如果省略 `assets`，而扫描出来的是目录型 plugin，那么：

- 对 `claude`：会被识别，但显式 skip
- 对 `opencode`：会因为不是明确的 `.js/.ts` 文件而 skip

## 9. 以后你最常见的几种操作

### 9.1 增加一个你自己的 skill

直接放：

```text
skills/owned/my-skill/SKILL.md
```

### 9.2 增加一个新的 GitHub skills 仓库，并默认拿全量

```yaml
sources:
  - id: my-extra-skills
    type: github
    github:
      repo: owner/repo
      ref: main
      path: skills
```

### 9.3 增加一个新的 GitHub skills 仓库，但只拿一部分

```yaml
sources:
  - id: my-extra-skills
    type: github
    github:
      repo: owner/repo
      ref: main
      path: skills
    assets:
      - id: review-helper
        kind: skill
        path: review-helper
```

### 9.4 临时关闭一个 source

```yaml
enabled: false
```

### 9.5 重新执行安装

```bash
npm run bootstrap
```

或者只装 Claude：

```bash
npm run bootstrap -- --target claude
```

## 10. 官方仓库参考

官方仓库：

- Anthropic official skills: `https://github.com/anthropics/skills`
- Anthropic official Claude plugins: `https://github.com/anthropics/claude-plugins-official`

这两个仓库的目录约定，就是你这里 `github.path` 和默认全量扫描规则的来源。
