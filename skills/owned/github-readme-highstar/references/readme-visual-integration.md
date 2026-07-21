# README Visual Integration

## Shared Brief

Before producing media, establish one shared brief with:

- code-backed product name, version, category, audience, and positioning;
- shipped, experimental, planned, and obsolete boundaries;
- one hero claim and its product evidence;
- verified logo, wordmark, colors, UI, commands, screenshots, and links;
- required asset geometry, file budgets, source paths, output paths, and acceptance conditions.

The visual owner reads this brief and returns selected direction, editable source, final stills or video, and QA evidence. The README owner uses the same brief for copy and integration.

## Recommended Repository Media Set

| Artifact | Purpose | Default contract |
|---|---|---|
| README hero WebP | First product and audience signal | Wide static image, short embedded copy, relative path, meaningful alt text |
| Launcher ready-state image | Show current identity and environment | Real labels, version, prompt, status, and product chrome |
| Launcher action/result image | Show the product doing useful work | One real workflow with current command, progress, and result semantics |
| Product loop MP4 | Supplemental action-to-result proof | Silent short loop, deterministic source, poster fallback, linked from README |

Use captions to explain what each screen proves. Do not repeat the same screen with cosmetic differences.

## GitHub Integration

- Place a static image at the top; do not depend on video autoplay or unsupported HTML.
- Use relative repository paths so forks and branches render predictably.
- Keep three to five high-value badges below the hero unless the repository has a reason to differ.
- Put title, one-line positioning, quick-start links, and the first runnable path in one coherent scan sequence.
- Write alt text that names the product and visible proof, not “banner” or “screenshot.”
- Check image edges and contrast against GitHub light and dark themes.

Example supplemental motion link:

```md
[Watch the product loop](./docs/assets/product-loop.mp4)
```

## Acceptance

- Product identity is clear at thumbnail and README width.
- Every visible claim is backed by current code, docs, tests, or supplied evidence.
- No obsolete asset, version, brand name, command, status, or planned feature is presented as current.
- Static README communicates the complete first-screen story without motion.
- Links, anchors, image paths, alt text, and media paths resolve.
- Full-resolution and downscaled renders have no clipping, overlap, or unreadable text.
- Motion has deterministic source, a matching poster, valid dimensions/duration/codec, and nonblank inspected frames.
