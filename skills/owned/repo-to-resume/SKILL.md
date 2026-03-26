---
name: repo-to-resume
description: |
  侧重提取当前仓库的项目结构、技术栈和文档线索，生成符合同步 schema 的 `./statics/resume.json`。触发点是“自动收集项目经历”“生成项目级 resume JSON”“从 repo 抽取项目亮点”。个人信息不是重点，脚本可输出默认身份字段并让项目条目自洽。
compatibility:
  tools: [bash, python]
  requires: Git 仓库，最好包含 README/package.json/pyproject.toml 其一
---

# Repo to Resume

Purpose:
- Analyze the current repository and generate a resume payload matching your resume schema.
- Produce `./statics/resume.json`.
- Keep the output in a consistent structure so it can be pasted into resumes or downstream tools.

The skill focuses on inputs and project signals:

1. analyze repository layout, docs, and dependency manifests
2. extract project architecture cues from code, catalogs, and planning artifacts
3. infer stack and tooling from files/manifests
4. write `./statics/resume.json`

## Input

The helper script accepts project-first overrides and optional identity defaults.

Project-related flags:

- `--project-name`: 用于 `projects.name`，默认取 repo 名称
- `--summary`: 覆盖自动生成的项目概述
- `--links`: 补充链接（GitHub/LinkedIn 等），可重复
- `--no-projects`: 跳过生成 `projects` 数组，保留 schema 占位

Output control:

- `--output`: 输出路径，默认 `./statics/resume.json`
- `--source-root`: 项目目录，默认当前目录
- `--force`: 强制覆盖已有输出

## Invocation

Use it as a normal Codex task when user asks to generate resume JSON.

Example:

```bash
python /home/aimagician/.codex/skills/repo-to-resume/scripts/extract_resume_json.py \
  --project-name "aimagician-skills" \
  --summary "Multi-target skill bootstrap infrastructure with catalog-driven installs." \
  --links "https://github.com/TobeMagic/aimagician-skills" \
  --output ./statics/resume.json \
  --force
```

## Expected output fields

- schema keys: `name`, `title`, `contacts`, `summary`, `skills`, `experiences`, `projects`, `education`
- script fills schema placeholders even when personal info is missing so downstream resume tools can patch identity later; focus is on `projects` and `skills`.

## Script behavior

- `scripts/extract_resume_json.py`:
  - Reads project metadata from `README.md`, `package.json`, `pyproject.toml`, `go.mod`, `requirements.txt`
  - Detects common stack signals from file extensions and dependency manifests
  - Detects key architecture paths (`catalog`, `skills`, `.planning`, `src`, `app`, `scripts`, `skills/owned`)
  - Generates one `projects` item for the current codebase using extracted signals
  - Writes deterministic sorted JSON to `./statics/resume.json`
- If a field cannot be inferred, it still keeps schema keys with empty/empty-array values so output stays parseable.

## Output validation

- JSON should always be valid.
- Validate quickly with:

```bash
python -m json.tool ./statics/resume.json > /dev/null
```

If not parseable, rerun with `--source-root` 指向一个可读项目目录并检查权限。
