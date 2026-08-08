# Phase 37 Context

## Baseline

- Phase 36 closed at commit `61a6317` with workflow status `complete`.
- The repository contains 816 Window-PPTX tests after Phase 36, including
  registry, TemplatePack, OOXML, portable, and private-guard suites.
- `.private/` is ignored and the staged-index guard rejects private paths,
  credential-like content, private keys, and binaries without echoing values.
- Existing `registry.py` owns commercial narrative archetypes only.
- `legacy-templates.json` contains four `legacy_unverified` entries with
  `auto_recommend: false`.
- One authorized TemplatePack v1 exists and is loaded by a filesystem scan.

## Objective And Boundary

Phase 37 establishes a safe, resumable acquisition and Catalog v3 tracer. It
does not download a commercial library without a fresh private credential and
does not claim that any private template is licensed, certified, or available.

## Accepted Architecture

Use four additive boundaries:

1. acquisition policy and state;
2. passive package quarantine;
3. content-addressed catalog and dependency closure;
4. a dedicated JSON library-management CLI.

The generation CLI, archetype registry, legacy registry, and TemplatePack v1
remain compatibility surfaces. Catalog v3 becomes the future retrieval
surface, not a flag-day replacement.

## Implementation Decisions

- Use Draft 2020-12 JSON contracts with unknown-field rejection.
- Keep acquisition, quarantine, catalog, and CLI as separate owners.
- Use deterministic JSON storage behind module interfaces for the tracer.
- Require explicit apply for atomic writes below `.private/`.
- Make certified-only retrieval the default and preserve legacy quarantine.

## Existing Patterns To Preserve

- Existing strict dataclass/JSON loaders and structured `ValueError` failures.
- Existing schema validation, deterministic serialization, and SHA-256 use.
- Existing `tests/window_pptx/` import/bootstrap conventions.
- Existing TemplatePack v1, design registries, generation CLI, and private
  staged-index guard behavior.

## Security Invariants

- Credentials are read only from a caller-supplied file that resolves under
  `skills/owned/window-pptx/.private/`.
- Credential values never appear in arguments, returned objects, exceptions,
  logs, manifests, tests, or tracked evidence.
- Authorization is attached only to an allowlisted origin and stripped before
  following a cross-origin redirect.
- PPTX/POTX/PPTM/ZIP input is inspected without extracting or executing it.
- Traversal paths, macros, OLE, ActiveX, external relationships, encrypted or
  malformed archives, and expansion-limit violations are quarantined.
- Commands are dry-run by default. Explicit writes are atomic and remain
  below `.private/`.

## Compatibility

- Existing registry JSON is not rewritten.
- Existing TemplatePack v1 manifests remain loadable.
- Uncertified or legacy-unverified entries may be inventoried but never appear
  in automatic certified retrieval.
- Public seed metadata uses no commercial byte and exists only to make the
  contract reproducible in CI.

## Allowed Scope

- Phase 37 schemas, additive package modules, dedicated manager CLI, seed
  metadata, focused tests, Skill reference, and planning/evidence artifacts.
- Synthetic ZIP fixtures constructed in temporary test directories.

## Forbidden Scope

- Production credentials, private tree contents, commercial template bytes,
  site-specific bypasses, browser automation, redistribution, or active
  package execution.
- Changes to existing generation/renderer behavior, TemplatePack v1 schema,
  legacy registry content, COM, or canonical portable output.

## Integration And Compatibility

The manager CLI imports the new acquisition/quarantine/catalog modules
directly. Future Phase 38 retrieval consumes Catalog v3 through its public
query interface. Existing callers continue loading archetypes, design packs,
legacy registries, and TemplatePack v1 without migration.

## External Preconditions

Authenticated commercial sync remains `NEEDS_AUTH` until the user confirms
the earlier chat-only session was revoked and places a fresh short-lived
credential in the ignored private directory. Rights metadata remains a
separate per-item gate even after authentication succeeds.
