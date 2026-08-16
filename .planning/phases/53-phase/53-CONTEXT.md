# Phase 53: Clean-Room Work-Report Acceptance and Release — Context

## Implementation Decisions

- Codex is the author and must use `gpt-5.6-terra` at medium reasoning.
- It may select narrative roles, catalog candidate IDs, selected IDs, fact IDs and
  asset IDs only. Native rendering, dimensions, formatting, OOXML and repair
  remain compiler authority.
- Output acceptance is bound to its own SHA-256 fingerprint, not merely to an
  author report or a named output path.

## Existing Patterns To Preserve

- Private library lookup is hash-bound under the ignored local root; a client
  folder is never searched for templates.
- `physical_adapter.py` uses the established recursive OPC importer and
  preserves native shapes for editability.
- `qa.py` permits only declared slot-local shrink-to-fit repair; all other
  defects require replan/reassembly.

## Allowed Scope

- Create client-local plans, reports and final delivery artifacts under the
  clean requirement directory.
- Resolve the existing private library at runtime via its configured external
  root, catalog and visual-observation index.
- Update Phase 53 evidence after observing real commands and artifacts.

## Forbidden Scope

- Copy private template packages, previews or the historical reference PPTX
  into the clean client directory.
- Generate any visual page with PptxGenJS/native freeform code, raw OOXML,
  HTML conversion or raster-only fallback.
- Alter private source decks, disclose private bytes or use self-scoring as a
  release override.

## Integration And Compatibility

- Delivery must open in LibreOffice and keep selected template elements native
  and editable; COM may certify but cannot be a dependency.
- The installed public Skill must retain source digest parity and must not copy
  the ignored `.private` directory.

- Clean client pack: `/tmp/pptx-studio-phase53-client.KV9xoK`.
- Private root: `skills/owned/pptx-studio/.private`, ignored and outside the
  client pack; catalog is `intelligence/pptx-studio/catalogs/gaojie-active.v2.json`.
- Reference deck remains external historical evidence only and is not copied to the
  client pack or shown to the author.
- Installed global Codex skill is verified by Skillbird doctor before the run.
- Original private location has been relocated into this new ignored root. This is a
  local asset ownership migration, not a Git change.
