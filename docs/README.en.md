# AImagician Skills (English Quick)

Chinese-first repo docs live in [../README.md](../README.md).

This repository is a personal skills distribution + bootstrap toolkit for multi-CLI AI environments. It installs skills to user-level directories for Codex / Claude / OpenCode / Gemini / Hermes / Cursor.

## Quick Start

```bash
npm install
npm run build
npm run bootstrap
```

Default bootstrap target set:

- `codex`
- `claude`
- `opencode`
- `gemini`
- `hermes`
- `cursor`

Published package flow:

```bash
npx aimagician-skills@latest bootstrap
```

## Core Commands

```bash
node dist/cli/index.js bootstrap --target claude
node dist/cli/index.js list
node dist/cli/index.js inspect --target codex
node dist/cli/index.js doctor
```

## Direct Image Workflows

### Text-to-image (ModelScope)

```bash
export MODELSCOPE_API_KEY="ms-your-token"
python skills/owned/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --model "Qwen/Qwen-Image-2512" \
  --prompt "A cinematic developer workspace, volumetric light, high detail" \
  --output ./result.jpg
```

### Image-to-image edit (ModelScope)

```bash
export MODELSCOPE_API_KEY="ms-your-token"
python skills/owned/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --model "Qwen/Qwen-Image-Edit-2511" \
  --prompt "Put a birthday hat on the dog while preserving composition" \
  --image-url "https://modelscope.oss-cn-beijing.aliyuncs.com/Dog.png" \
  --output ./dog-edit.jpg
```

## Docs

- YAML catalog config: [CATALOG-CONFIG.md](./CATALOG-CONFIG.md)
- GSD workflows: [GSD-WORKFLOW.md](./GSD-WORKFLOW.md)
- Advanced bilingual doc style guide: [DOC-STYLE.md](./DOC-STYLE.md)
