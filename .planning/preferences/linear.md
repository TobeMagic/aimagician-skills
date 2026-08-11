# Linear Project Preference

Linear is auxiliary project tracking, not a prerequisite for implementation.

- Use Linear only when ticket context is required, the user asks for an update, or post-delivery closure is useful.
- Route discovery and actions through Composio CLI via `composio-tool-router`; do not use Linear MCP.
- Prefer core delivery first: understand, implement, run risk-appropriate verification, and deliver according to repository branch policy.
- Delegate bounded status lookup, result notes, PR/commit links, acceptance summaries, and closure to OpenCode when that saves controller context.
- Do not assume a reviewer bot, base branch, workflow state, team ID, issue ID, or merge policy. Discover only the field needed for the current action.
- Preview writes and confirm the exact action. A Linear outage or missing connection must not block code delivery unless Linear contains indispensable requirement context.

Never put this project preference into a general-purpose installed Skill.
