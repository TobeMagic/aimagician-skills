# Phase 42 Context — Reopen v6 and restore ground truth

## Why this phase exists

The user rejected the v6 visual result after the repository recorded a release
GO.  A fresh inspection established that the closure evidence overstated the
implemented product:

- the advertised 84 candidates are 15 physical pages, 60 code compositions,
  and nine aliases rather than 84 independently sourced templates;
- the three flagship generators start from a blank PptxGenJS presentation and
  do not materialize selected physical templates;
- the Phase 37 commercial-library sync is a contract tracer and returns
  `SITE_ADAPTER_NOT_CONFIGURED`; it does not browse or download the entitled
  catalog;
- the current flagship decks are orderly but visually generic and do not show
  the reference deck's art direction or the requested template-library reuse;
- acceptance allowed material single-reviewer visual findings to survive.

The latest user decision supersedes the earlier release claim. v6 is reopened
until the real acquisition-to-delivery chain passes.

## Accepted decisions

- Use Playwright to acquire the user's entitled Gaojie catalog through the
  normal authenticated UI.
- Keep credentials, originals, acquisition state, rendered mining artifacts,
  and commercial packages under ignored `.private/`.
- Never place cookie values in chat-derived commands, logs, manifests,
  screenshots, or Git. Runtime authentication is read only from
  `.private/auth/gaojie.cookie`.
- Download the complete entitled taxonomy, then certify a representative core
  of roughly 300–500 high-value pages before broadening.
- Local-machine quality is the immediate priority. Native editable PPTX remains
  canonical; COM is optional, HTML is proof-only.
- First prove three realistic anchor scenarios: annual work report, campus
  competition defense, and academic thesis defense. Then extend to all fifteen
  scenarios and ordinary-model mode.
- Visual acceptance uses fresh, isolated, image-capable AI contexts. Any
  independent `Blocker` or `Important` visual finding blocks promotion until it
  is fixed and re-reviewed.

## Security and authorization boundary

The user authorizes local use of assets available through their account. This
does not authorize bypassing access control, redistributing private originals,
committing them, or leaking credentials. The adapter must use normal product
navigation and same-origin downloads only.
