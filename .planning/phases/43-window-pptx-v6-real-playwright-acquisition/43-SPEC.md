# Phase 43 Specification — Real Playwright acquisition

## Production entrypoint

```bash
python skills/owned/window-pptx/scripts/manage_window_pptx_library.py sync \
  --private-root skills/owned/window-pptx/.private \
  --source-id gaojie-entitled \
  --source-adapter gaojie \
  --origin http://www.gaojiewenhua.cn \
  --allow-host www.gaojiewenhua.cn \
  --allow-insecure-http \
  --credential-file skills/owned/window-pptx/.private/auth/gaojie.cookie \
  --apply
```

The HTTP exception is explicit because the observed site does not serve
working HTTPS. Authentication remains same-origin and the adapter rejects
other schemes/hosts.

## Browser fixture

The repository test server models login redirect, cookie acceptance, category
navigation, pagination, detail pages, downloads, duplicate bytes, and expired
sessions. Real adapter work may not start from untested selectors alone.

## Runtime behavior

- Cookie text is read only from the validated private file and injected into a
  fresh ephemeral browser context.
- Successful authentication must reach products without login controls.
- At least 32 unique category IDs must be discovered or sync fails.
- Category and pagination URLs, product detail URLs, and downloads remain on
  the exact configured origin.
- Downloads are accepted only from successful non-HTML responses.
- Bytes are SHA-256 deduplicated and atomically promoted below
  `.private/sources/gaojie/`.
- Secret-free state below `.private/state/gaojie-sync.json` supports resume.
- Remaining disk below 40 GiB fails closed by default.
- Site drift, expired auth, incomplete taxonomy, missing download links, and
  HTTP errors produce explicit findings.

## Exit gate

Fixture tests, existing acquisition tests, secret guard, and independent
specification/quality review must pass. The external exercise remains
`NEEDS_AUTH` until `.private/auth/gaojie.cookie` exists. Phase 43 cannot claim
complete merely from fixture success.
