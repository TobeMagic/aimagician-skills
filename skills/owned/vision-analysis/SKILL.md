---
name: vision-analysis
description: Use when an agent must understand pixels from screenshots, diagrams, charts, posters, UI captures, scanned image pages, or multiple reference images, especially when a CLI agent such as OpenCode cannot pass image attachments to its selected model. Routes authorized images through a direct multimodal API and returns sanitized textual evidence for later reasoning or review.
category: research
subcategory: visual-analysis
tags:
  - vision
  - image-understanding
  - multimodal
  - screenshot
  - visual-evidence
  - agnes
compatibility:
  tools: [bash, node]
  requires: Node.js 20+, AGNES_API_KEY, explicit authorization to upload every image to an external API
---

# Vision Analysis

Acquire trustworthy visual evidence without pretending a text-only CLI attachment path is multimodal. Agnes is the current backend; the skill contract is provider-neutral so another verified backend can replace or join it later.

## Trigger And Boundary

Use this skill for screenshot inspection, OCR-like reading, UI defects, chart or diagram interpretation, visual comparison, document pages already rendered to images, and any CLI-agent task that must understand pixels.

Do not use it for image generation, audio, native PDF parsing, video analysis, or a one-file textual lookup. A main Agent with a reliable native image tool may inspect locally, but CLI-agent visual work must acquire evidence here before text reasoning.

## Required Workflow

1. State what must be learned from the images and request a structured answer that distinguishes observation, inference, and uncertainty.
2. Confirm that external upload is authorized. Every invocation requires `--allow-external-upload`; the flag covers the entire invocation, including HTTPS URLs.
3. Run `scripts/analyze.mjs` with one or more `--image` values and a prompt or prompt file.
4. Treat the returned report as evidence, not final authority. Spot-check completion-critical claims with another reliable viewer or observable product check when available.
5. For broader reasoning, planning, or review, pass the sanitized textual report to `cli-agent-delegator`; OpenCode should not receive the original image attachment for Agnes.

## Command

```bash
node scripts/analyze.mjs \
  --image "./artifacts/screenshot.png" \
  --prompt-file "./visual-review-prompt.md" \
  --allow-external-upload \
  --json
```

Repeat `--image` to compare up to eight images. Supported local formats are PNG, JPEG, WebP, and GIF, with a 20 MiB default limit per image. HTTPS URLs must be public and must not contain embedded credentials.

Environment:

- `AGNES_API_KEY`: required and never printed or persisted;
- `AGNES_API_BASE_URL`: optional, defaults to `https://apihub.agnes-ai.com/v1`;
- `AGNES_VISION_MODEL`: optional, defaults to `agnes-2.0-flash`;
- `AGNES_REQUEST_TIMEOUT_MS`: optional per-request timeout, defaults to 120000.

Read [agnes-api.md](./references/agnes-api.md) for request, retry, output, and failure semantics.

## Safety Rules

- Never put a key in a command argument, source file, fixture, report, screenshot, or log.
- Never upload without the explicit flag, even when the image already has an HTTPS URL.
- Do not print base64 image data, absolute local paths, URL query strings, fragments, credentials, request headers, or raw error bodies.
- Refuse `file:`, `data:`, plain HTTP, localhost, and obvious private-network URLs.
- A 429 remains active work: wait and retry until success or cancellation. Do not silently switch to an unverified vision model.
- Authentication, invalid input, and other non-retriable 4xx responses stop immediately.

## Output Contract

JSON output includes status, provider, model, sanitized endpoint origin, input kind/name/MIME/size/hash, attempt counts, analysis text, and usage when returned. Progress events go to stderr. No image bytes or credentials are retained.

The caller must report:

- visual objective and images inspected;
- backend/model and retry history;
- observations, inferences, and uncertainty;
- controller spot-checks for critical claims;
- whether the report was passed into a later OpenCode reasoning or audit task.
