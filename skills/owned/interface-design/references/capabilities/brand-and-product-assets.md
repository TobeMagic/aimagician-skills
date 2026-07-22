# Brand And Product Assets

Use this module for repository covers, banners, posters, social images, product showcases, campaign graphics, and other rendered stills whose quality depends on product understanding rather than decoration.

## Start From A Visual Contract

Record:

- distribution surface and final pixel geometry;
- product, offer, or event being represented;
- primary audience and the decision the asset should support;
- one dominant message and one concrete product proof;
- verified logo, wordmark, colors, screenshots, commands, data, and version;
- required text, forbidden claims, safe crop area, static fallback, and file-size budget;
- source artifact, final formats, and acceptance renders.

Use `assets/templates/repository-visual-brief.md` for repository work and `assets/templates/brand-spec.md` for reusable identity decisions.

## Acquire And Verify Core Assets

Use assets in this order:

1. project-local approved assets and design system;
2. official product or organization media and documentation;
3. public-domain or clearly licensed institutional sources;
4. reputable free-use photography when the license fits distribution;
5. generated media when it truthfully represents a subject and provenance is recorded;
6. a clearly labeled placeholder when no verified asset is available.

For each asset, record source URL or project path, retrieval date, owner, license or permission, original dimensions, crop, checksum when durable, and fallback. Verify content type, dimensions, transparency, focus, and whether the asset actually depicts the named product. Do not bulk-copy user directories or treat social avatars as authoritative product assets unless no better official source exists.

For public-domain or openly licensed discovery, `scripts/fetch-wikimedia-assets.mjs` provides a bounded on-demand route. Pass a descriptive `WIKIMEDIA_USER_AGENT`, query only what the brief needs, and review the generated source, author, license, dimensions, and SHA-256 manifest before using any result. The downloader is not a license decision and does not replace official product assets.

For an ambiguous image search, use the **5-10-2-8 evidence threshold**: inspect at least five credible channels or query angles, collect up to ten plausible candidates, retain the best two, and use an asset only when subject fit, technical quality, provenance, and license each support an overall score of at least 8/10. Scale the search down when an official project asset already satisfies the brief; the numbers are a quality threshold, not permission to scrape broadly.

## Build A Claim-To-Evidence Ledger

Every visible product claim must point to code, current documentation, a real screen, a supplied asset, or an explicitly labeled concept. Keep future plans, examples, and simulated states visibly distinct from shipped behavior. Never manufacture terminal output, metrics, customers, integrations, or version numbers for visual density.

## Explore Directions Before Production

For an open or high-impact brief, create exactly three real direction previews at target geometry. Each direction must differ in composition, typography, palette behavior, product-proof treatment, and motion potential, not only background color. Name:

1. the idea;
2. what is seen first;
3. why it fits the audience;
4. its main risk;
5. how it scales to the target surface.

Choose one direction against audience fit, product truth, legibility, distinctiveness, and implementation cost. Merge directions only when their systems are compatible.

## Compose The Asset

Use a three-level hierarchy:

1. **Identity:** product or offer is unmistakable at thumbnail scale.
2. **Value:** one short positioning statement or visual mechanism explains why it matters.
3. **Proof:** an actual screen, command, object, chart, workflow state, or result makes the claim credible.

Prefer a real product view over atmospheric imagery. Use a generated bitmap only when it represents a truthful subject that cannot be sourced or rendered more directly. Keep detailed copy outside the image when the distribution surface already provides text.

For a family of assets, lock shared tokens, crop behavior, logo clear space, type roles, proof treatment, and image policy before producing variants. Do not scale a desktop composition down blindly; redesign the hierarchy for each aspect ratio.

## Render And Verify

Keep the HTML/CSS/JS or other editable composition source beside generated output when the repository permits it. Render at the exact target geometry, then inspect:

- full resolution and a realistic thumbnail/downscaled view;
- text fit, safe areas, contrast, alignment, and subject visibility;
- factual labels, version, commands, and links against sources of truth;
- transparent and opaque backgrounds where required;
- image dimensions, format, compression, color profile, and file-size budget;
- fallback behavior when fonts or remote assets fail.

An asset is not accepted because it rendered. It is accepted when the product remains identifiable, the proof remains legible, and no visible claim outruns evidence.
