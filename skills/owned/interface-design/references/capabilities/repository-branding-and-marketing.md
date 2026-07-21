# Repository Branding And Marketing

Use this module for GitHub README covers, repository banners, launch visuals, product-demo links, launcher screenshots, and visual systems for developer tools.

## Ownership Contract

`interface-design` owns product interpretation, art direction, source composition, still or motion rendering, and visual QA. The README skill owns document structure, copy hierarchy, links, anchors, accessibility text, and final Markdown integration. Work sequentially from one shared product brief rather than letting each skill invent a separate story.

## Repository Evidence Pass

Read the repository in this order:

1. code-backed product name, version, entry point, and current launcher or first-run behavior;
2. repository guidance and source-of-truth documents;
3. README positioning, install path, examples, links, and current media;
4. tests or runtime evidence for claims shown in the visual;
5. existing logo, wordmark, icon, palette, typography, screenshots, and stale assets.

Separate shipped, experimental, planned, and obsolete material. Record contradictions before design. A polished reproduction of stale UI is still incorrect.

## Repository Visual Brief

Define:

- primary user and the repository decision: understand, trust, try, star, install, or contribute;
- literal product category and one-line positioning;
- one hero proof and up to five supporting capabilities;
- brand signal, product UI signal, developer-tool signal, and trust signal;
- static hero geometry, launcher-screen geometry, motion duration, and media budgets;
- desktop, mobile, light/dark GitHub, and downscaled reading conditions.

For developer tools, favor real terminal, editor, diff, build, test, trace, or architecture evidence. Generic neon terminal chrome without actual product behavior is not proof.

## Recommended Asset Set

### README Hero

- Product name or literal offer is the first signal.
- Show one actual workflow or product state, not a feature collage.
- Keep embedded text short enough to survive GitHub downscaling.
- Provide meaningful alt text and a relative repository path.

### Launcher Or Product Screens

- Use current UI structure, prompts, labels, status fields, and version.
- Show distinct moments: ready state and active/result state, not two cosmetic variants.
- Explain each image with one factual caption in the README.

### Motion Demo

- Tell one complete story: context, action, progress, result.
- Use a static poster as the README default and link to the MP4 or hosted demo.
- Keep the first frame useful, the loop silent, and the ending stable long enough to inspect.
- Do not rely on embedded autoplay support in a repository README.

## Integration Checks

- Hero, title, tagline, badges, and quick-start links form one scan path.
- Three to five badges are enough unless the project has a documented exception.
- Media uses relative paths and does not depend on expiring URLs.
- Poster and linked motion have the same claims, visual system, and current version.
- README light and dark themes preserve image edges and text contrast.
- The static README remains complete when motion cannot play.

Use `assets/templates/repository-visual-brief.md` and coordinate final Markdown integration with the README owner.
