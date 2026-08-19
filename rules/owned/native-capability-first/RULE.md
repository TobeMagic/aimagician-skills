---
name: native-capability-first
description: Use the current model and host tools before substitute skills
alwaysApply: true
---

# Native Capability First

Prefer tools already in this session.

- Images: if this model can read pixels (for example Cursor Read on png/jpg/webp), inspect locally. Load vision-analysis only when the current model or worker cannot see images, or the user asks for the Agnes evidence package.
- Delegation: use this host's subagent. Do not start OpenCode, Codex, or Cursor as a foreign CLI unless the user names that runtime.
- Documents and browsers: load pdf/docx/xlsx/webapp-testing only when those files or a real browser check are the work.
