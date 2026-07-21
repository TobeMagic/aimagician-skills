# README Blueprint (Highstar Style)

## A. One-screen opener

- Title
- One-sentence positioning
- Hero cover image (recommended)
- 3-5 badges max
- First CTA: quick start link

Example:

```md
# Project Name

> One-line value proposition for the project.

[![CI](...)](...) [![License](...)](...) [![Version](...)](...)

Quick start: [Installation](#installation) · [Usage](#usage)
```

Cover embed example:

```md
<p align="center">
  <img src="./docs/assets/readme-cover.webp" alt="Project cover" width="100%" />
</p>
```

Cover design guidance:

- Route product understanding, visual direction, source composition, rendering, and visual QA to `interface-design`.
- Recommended wide geometry: `1600x900`, unless the repository defines another contract.
- Show current product proof and keep embedded copy readable after README downscaling.
- Preserve an editable visual source and use a static WebP/PNG as the default README surface.
- Link motion media as supplemental proof and provide a matching poster fallback.

## B. Table of contents (required for long docs)

```md
## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
```

## C. High-signal sections

- `Features`: short bullets, one benefit per bullet.
- `Installation`: minimum runnable commands only.
- `Usage`: 1-2 realistic examples with expected result.
- `Project Structure`: tree + short intent notes.
- `Contributing`: how to run tests/lint/commit.
- `License`: explicit license text and link.

## D. Visual consistency rules

- Keep heading levels consistent (`##` main blocks, `###` sub-blocks).
- Use one table style and one callout style throughout.
- Prefer short bullets over dense paragraphs.
- Place images near relevant text; avoid image walls.

## E. Quality checklist

- Reader can run the project in <= 5 minutes.
- All command blocks are copy-paste safe.
- All links/anchors resolve.
- README has explicit target audience and use case.
- README cover exists and is referenced by a relative path.
- README cover facts, version, commands, and visible UI match current source-of-truth evidence.
- Cover remains readable at realistic GitHub column width and against light/dark page backgrounds.
- Any linked video has a static poster and the README remains complete without playback.
- README ends with contribution + license + contact entry.
