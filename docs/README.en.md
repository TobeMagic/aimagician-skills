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

Equivalent explicit command:

```bash
node dist/cli/index.js bootstrap --targets codex,claude,opencode,gemini,hermes,cursor
```

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

## Included Owned Skills

Current owned skills include:

- `cloudflare-image-gen`
- `deep-research-system`
- `design-md-brand-router`
- `github-readme-highstar`
- `infinite-research-loop`
- `karpathy-coding-principles`
- `modelscope_imagegen`
- `modelscope_video_ops`
- `multilingual-diversity-loop`
- `parallel-worktree-pr-flow`
- `repo-to-resume`
- `window-pptx`

## Highlighted Workflows

- ModelScope text-to-image and image-to-image through `modelscope_imagegen`
- Cloudflare Workers AI image generation through `cloudflare-image-gen`
- Windows desktop PowerPoint COM/VBA automation through `window-pptx`
- High-star GitHub README authoring through `github-readme-highstar`
- GSD-compatible autonomous research loops through `infinite-research-loop`

## Docs

- YAML catalog config: [CATALOG-CONFIG.md](./CATALOG-CONFIG.md)
- GSD workflows: [GSD-WORKFLOW.md](./GSD-WORKFLOW.md)
- Advanced bilingual doc style guide: [DOC-STYLE.md](./DOC-STYLE.md)
