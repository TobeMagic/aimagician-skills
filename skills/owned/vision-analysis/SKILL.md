---
name: vision-analysis
description: Use when the current model or worker cannot see images, or when the user asks for an authorized Agnes evidence package from screenshots, diagrams, charts, posters, UI captures, scanned pages, or multiple reference images. Do not use when this session already has a reliable native image tool. Routes authorized images through a direct multimodal API and returns sanitized textual evidence for later reasoning or review.
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

Use this skill when the current model or worker cannot inspect pixels, or when the user asks for an Agnes evidence package with sanitized provenance.

Do not use it for image generation, audio, native PDF parsing, video analysis, a one-file textual lookup, or a session that already has a reliable native image tool. Inspect locally first in that case.

## Required Workflow

1. State what must be learned from the images and request a structured answer that distinguishes observation, inference, and uncertainty.
2. Confirm that external upload is authorized. Every invocation requires `--allow-external-upload`; the flag covers the entire invocation, including HTTPS URLs.
3. Run `scripts/analyze.mjs` with one or more `--image` values and a prompt or prompt file.
4. Treat the returned report as evidence, not final authority. Spot-check completion-critical claims with another reliable viewer or observable product check when available.
5. For broader reasoning, planning, or review, pass the sanitized textual report to the current host's subagent. Do not attach the original image to a text-only worker.

### 1. Bind Inputs And Question

Name each image, permitted upload scope, inspection question, and expected downstream decision.

### 2. Acquire Sanitized Evidence

Validate inputs, invoke the approved backend, and retain provenance without image bytes, keys, or sensitive URL data.

### 3. Separate Observation From Inference

Return visual observations, inferences, uncertainty, and any need for an independent product check.

### 4. Route The Evidence

Pass only the sanitized report to downstream reasoning, planning, or audit work.

**CHECKPOINT:** Do not upload or interpret pixels until every input path/URL, the inspection question, external-upload authorization, and expected evidence consumer are explicit.

**CHECKPOINT:** Confirm returned provenance, retry classification, and report uncertainty before using visual evidence for a completion or safety decision.

**CHECKPOINT:** If the image, authorization, provider result, or independent spot-check is missing, stop downstream interpretation at the verified boundary.

## Failure Handling

| Trigger | First response | Fallback |
|---|---|---|
| Upload authorization, image path, MIME, or size is invalid | Stop before API use and report the safe validation failure | Request an authorized supported image or downscaled derivative; never infer pixels from a filename |
| Provider returns a transient failure or rate limit | Follow the bounded retry/rate-limit policy in `references/agnes-api.md` and retain sanitized attempt evidence | Return `NOT_RUN` only after the defined terminal failure; do not silently switch to text-only guessing |
| Observation is ambiguous or completion-critical | Separate observation, inference, and uncertainty in the report | Require an independent viewer or product check before an irreversible decision |

When visual evidence conflicts with code, runtime, or a second viewer, stop the dependent decision and preserve both evidence sources for reconciliation.

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
