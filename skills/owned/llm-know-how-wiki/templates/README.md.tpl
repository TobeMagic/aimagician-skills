# LLM Know-how Wiki

This is a project-local compiled knowledge base.

## Core idea

- `raw/` stores append-only source evidence.
- `wiki/` stores curated, agent-maintained Markdown pages.
- `SCHEMA.md` defines how agents maintain the wiki.
- `wiki/index.md` is the navigation catalog.
- `wiki/log.md` is the append-only action history.

## Default workflow

1. Add source material under `raw/`.
2. Ask an agent to Ingest specific source paths.
3. The agent updates `wiki/`, `wiki/index.md`, and `wiki/log.md`.
4. Ask questions in Answer mode using the compiled wiki.
5. Run Lint periodically.

## Domain

{{DOMAIN}}

