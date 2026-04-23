# AImagician Skills

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Node](https://img.shields.io/badge/node-%3E%3D18-brightgreen)](https://nodejs.org/)

<p align="center">
  <img src="./docs/assets/readme-cover.webp" alt="AImagician Skills cover" width="100%" />
</p>

> Personal skills repository and one-command bootstrap toolkit for Codex / Claude / OpenCode / Gemini / Hermes / Cursor.
>
> 中文：面向多 AI CLI 的个人 skills 仓库与一键部署工具。

默认中文文档。  
English quick doc: [docs/README.en.md](./docs/README.en.md)

这是一个面向多 AI CLI 的个人 skills 仓库与一键部署工具，目标是把技能统一安装到用户级目录，让 Codex / Claude / OpenCode / Gemini / Hermes / Cursor 开箱可用。

快速入口：

- [封面生成脚本](#封面生成脚本)
- [快速开始](#快速开始)
- [常用命令](#常用命令)
- [文生图--图生图直接可用](#文生图--图生图直接可用)
- [当前支持矩阵](#当前支持矩阵)
- [用户级安装路径](#用户级安装路径)
- [验证与排障](#验证与排障)

## 封面生成脚本

当前 README 顶部封面由仓库内生图脚本生成，命令如下：

```bash
export MODELSCOPE_API_KEY="ms-your-token"
python skills/owned/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --model "Qwen/Qwen-Image-2512" \
  --prompt "Futuristic software engineering command center, multi-CLI agent orchestration dashboard, glowing terminal windows, elegant dark-neutral background with cyan and amber accents, premium open-source README hero banner style, no text, ultra clean composition" \
  --width 1600 \
  --height 896 \
  --num-inference-steps 8 \
  --output ./docs/assets/readme-cover.raw.png
```

将原图转成 README 头图（固定 16:9）：

```bash
python - <<'PY'
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
src = "docs/assets/readme-cover.raw.png"
out = "docs/assets/readme-cover.webp"
img = Image.open(src).convert("RGB")
canvas = (1600, 896)
bg = ImageOps.fit(img, canvas, method=Image.Resampling.LANCZOS)
bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(18))).enhance(0.58)
fg_h = int(canvas[1] * 0.9)
fg_w = int(img.width * (fg_h / img.height))
fg = img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)
shadow = Image.new("RGBA", (fg_w + 24, fg_h + 24), (0, 0, 0, 0))
shadow.paste(Image.new("RGBA", (fg_w, fg_h), (0, 0, 0, 150)), (12, 12))
shadow = shadow.filter(ImageFilter.GaussianBlur(10))
base = bg.convert("RGBA")
base.alpha_composite(shadow, ((canvas[0] - fg_w) // 2 - 12, (canvas[1] - fg_h) // 2 - 12))
base.alpha_composite(fg.convert("RGBA"), ((canvas[0] - fg_w) // 2, (canvas[1] - fg_h) // 2))
base.convert("RGB").save(out, format="WEBP", quality=86, method=6)
print("saved:", out)
PY
```

## 核心能力

- 管理自有技能：`skills/owned/*`
- 接入第三方技能源：`catalog/skills/*.yaml`
- 支持命令型安装源（如 GSD / UIPro）
- 按目标 CLI 安装到用户目录（默认全目标）
- 支持 Gemini 扩展生成、OpenCode 插件安装
- 支持安装结果检查：`list / inspect / doctor`

## 快速开始

```bash
npm install
npm run build
npm run bootstrap
```

如果不传 `--target` / `--targets`，默认安装到全部支持目标（包含 OpenCode 与 Hermes）：

- `codex`
- `claude`
- `opencode`
- `gemini`
- `hermes`
- `cursor`

发布后可直接：

```bash
npx aimagician-skills@latest bootstrap
```

默认 targets 等价于：

```bash
node dist/cli/index.js bootstrap --targets codex,claude,opencode,gemini,hermes,cursor
```

## 常用命令

```bash
# 默认全量安装
npm run bootstrap

# 仅安装到 Claude
node dist/cli/index.js bootstrap --target claude

# 指定多个目标
node dist/cli/index.js bootstrap --targets codex,claude,opencode,gemini,hermes,cursor

# 只看计划，不落盘
node dist/cli/index.js bootstrap --dry-run --json

# 检查已安装资产
node dist/cli/index.js list
node dist/cli/index.js inspect --target codex
node dist/cli/index.js doctor
```

## 文生图 / 图生图（直接可用）

仓库已包含图像能力 skill，可直接走脚本调用。

### ModelScope 文生图

```bash
export MODELSCOPE_API_KEY="ms-your-token"
python skills/owned/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --model "Qwen/Qwen-Image-2512" \
  --prompt "A cinematic developer workspace, volumetric light, high detail" \
  --output ./result.jpg
```

### ModelScope 图生图（编辑）

```bash
export MODELSCOPE_API_KEY="ms-your-token"
python skills/owned/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --model "Qwen/Qwen-Image-Edit-2511" \
  --prompt "给图中的狗戴上一个生日帽，写实风格，保持主体构图" \
  --image-url "https://modelscope.oss-cn-beijing.aliyuncs.com/Dog.png" \
  --output ./dog-edit.jpg
```

多图编辑可重复 `--image-url`：

```bash
python skills/owned/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --model "Qwen/Qwen-Image-Edit-2511" \
  --prompt "图一的狗去追图二的飞盘，写实风格" \
  --image-url "https://modelscope.oss-cn-beijing.aliyuncs.com/Dog.png" \
  --image-url "https://modelscope.oss-cn-beijing.aliyuncs.com/Frisbee.png" \
  --output ./dog-frisbee.jpg
```

Cloudflare 文生图请参考：

- [skills/owned/cloudflare-image-gen/SKILL.md](./skills/owned/cloudflare-image-gen/SKILL.md)

ModelScope 图像技能说明请参考：

- [skills/owned/modelscope_imagegen/SKILL.md](./skills/owned/modelscope_imagegen/SKILL.md)

## 当前支持矩阵

| 能力 | 状态 | 说明 |
|---|---|---|
| Owned skills | supported | 从 `skills/owned/*` 同步 |
| GitHub skill source | supported | 从仓库抓取后安装 |
| Command source | supported | 委托上游安装命令执行 |
| Codex skills | supported | `~/.codex/skills` |
| Claude Code skills | supported | `~/.claude/skills` |
| OpenCode skills | supported | `~/.config/opencode/skills` |
| Gemini extensions | supported | `~/.gemini/extensions` |
| Hermes skills | supported | `~/.hermes/skills` |
| Cursor skills | supported | `~/.cursor/skills` |
| OpenCode plugins | supported | `~/.config/opencode/plugins` |
| Claude plugins | explicit skip | 保持 marketplace/consent 流程 |
| Gemini plugin catalog | explicit skip | 当前仅支持 skill 扩展生成 |

Cursor 说明：

- Cursor 的 `rules` 和 `skills` 不是一回事。
- 本仓库安装的是 Cursor skills（`~/.cursor/skills`），不是 `.cursor/rules`。

## 目录结构

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
docs/
  CATALOG-CONFIG.md
  GSD-WORKFLOW.md
  DOC-STYLE.md
  README.en.md
```

## 配置说明入口

YAML 配置详解：

- [docs/CATALOG-CONFIG.md](./docs/CATALOG-CONFIG.md)

GSD 工作流说明：

- [docs/GSD-WORKFLOW.md](./docs/GSD-WORKFLOW.md)

中英文文档高级样式规范：

- [docs/DOC-STYLE.md](./docs/DOC-STYLE.md)

## 用户级安装路径

默认安装位置：

- Codex: `~/.codex/skills`
- Claude Code: `~/.claude/skills`
- OpenCode skills: `~/.config/opencode/skills`
- OpenCode plugins: `~/.config/opencode/plugins`
- Gemini extensions: `~/.gemini/extensions`
- Hermes: `~/.hermes/skills`
- Cursor: `~/.cursor/skills`

Bootstrap 状态目录：

- Linux: `${XDG_STATE_HOME:-~/.local/state}/aimagician-skills`
- Windows: `%LOCALAPPDATA%\\aimagician-skills`

## 隔离 HOME 测试

```bash
node dist/cli/index.js bootstrap --targets codex,claude --home /tmp/test-home
node dist/cli/index.js list --targets codex,claude --home /tmp/test-home
node dist/cli/index.js doctor --targets codex,claude --home /tmp/test-home
```

## 验证与排障

```bash
npm run build
npm test
node dist/cli/index.js doctor --json
```

如果命令源已执行但 `skills` 数量与预期不一致，先用 `inspect` 查看：

```bash
node dist/cli/index.js inspect --target claude
```

> 命令源（如 GSD）可能安装 commands/agents/hooks 等非纯 skills 资产，`list` 显示方式会与普通 skills 不同，属正常行为。

## Contributing

- 欢迎提交 issue 与 PR。
- 变更 README 时请同步检查：
  - [docs/README.en.md](./docs/README.en.md)
  - [docs/DOC-STYLE.md](./docs/DOC-STYLE.md)

## License

MIT，见 [LICENSE](./LICENSE)。
