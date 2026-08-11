# State Storage

Store orchestration state with the project, not inside application runtime code.

- Planning-managed repository: `.planning/workstreams/registry.json`
- Repository without planning: `.agent/workstreams/registry.json`

Use repository policy if it defines another location. Local-private planning may keep the same logical path in a Git-common-dir-backed store shared by worktrees.

## Required Registry Fields

Each workstream records:

- `id`, `objective`, `status`, and `mode`;
- `provider`, `model`, `session_id`, and `last_activity_at`;
- `source_context`, `required_skills`, and `dependencies`;
- `read_scope`, `write_scope`, and `forbidden_scope`;
- optional `branch`, `worktree`, and `base_commit`;
- `expected_output`, `validation`, `evidence`, and `handoff`;
- `blockers` and unresolved findings.

Keep secrets, raw credentials, and full transcripts out of the registry. Store only durable decisions and evidence locators. One integration owner writes shared state when several sessions are active.
