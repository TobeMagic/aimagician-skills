# Source Notes

Primary source:

- `https://github.com/VoltAgent/awesome-design-md`

Observation used in this skill:

- The repository organizes brand folders under `design-md/<brand>/`.
- Many folders currently point to hosted `getdesign.md` pages from their `README.md`.
- Therefore this skill fetches DESIGN.md content through:
  - `https://getdesign.md/design-md/{brand}/DESIGN.md`

This keeps the flow stable when the upstream repository stores pointers instead of local DESIGN.md files.
