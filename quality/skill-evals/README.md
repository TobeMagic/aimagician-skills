# Skill Evaluation Assets

Behavioral scenarios, fixtures, and evaluation evidence live here so installable Skills remain focused on runtime capability.

- One directory per active or historically evaluated Skill ID.
- Runtime Skills under `skills/owned/<id>` must not depend on these files.
- Test and optimization tooling may load `quality/skill-evals/<id>/evals.json` from the source repository.
- Installed Codex and OpenCode Skill trees exclude this quality surface.
- Keep secrets, private user data, generated caches, and model credentials out of evaluation fixtures.

Use `skill-optimizer` for controlled baseline/treatment comparison. Moving an eval here does not make a treatment pass; behavior and acceptance still require independent evidence.
