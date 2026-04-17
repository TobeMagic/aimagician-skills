# ModelScope Image API Notes

This file captures the official source-backed behavior used by `modelscope_imagegen`.

## Official Sources

- ModelScope API-Inference intro:
  `https://www.modelscope.cn/docs/model-service/API-Inference/intro`
- ModelScope model page for Qwen-Image-2512:
  `https://www.modelscope.cn/models/Qwen/Qwen-Image-2512`
- Qwen model page README as mirrored on ModelScope:
  `https://www.modelscope.cn/models/Qwen/Qwen-Image-2512`
- Qwen image blog:
  `https://qwen.ai/blog?id=qwen-image`
- Qwen-Image-2512 blog link exposed on the official ModelScope model page:
  `https://qwen.ai/blog?id=qwen-image-2512`

## Officially Confirmed API Basics

ModelScope API-Inference uses:

- base URL: `https://api-inference.modelscope.cn/v1/`
- bearer auth with a ModelScope token

The ModelScope docs intro page metadata states API-Inference is the standard service entry for hosted model calls.

Community and docs snippets on official ModelScope pages consistently show:

- image generation endpoint:
  `POST /v1/images/generations`
- auth header:
  `Authorization: Bearer <ModelScope Token>`
- content header:
  `Content-Type: application/json`

## Async Requirement

Live validation on 2026-04-17 against `Qwen/Qwen-Image-2512`:

- `POST /v1/images/generations` without `X-ModelScope-Async-Mode: true` returned HTTP 400
- returned message:
  `image-gen task currently does not support synchronous calls ... set header X-ModelScope-Async-Mode=true`

Treat async mode as mandatory for this model.

Required async header:

- `X-ModelScope-Async-Mode: true`

Polling header used in official and community examples:

- `X-ModelScope-Task-Type: image_generation`

Polling path:

- `GET /v1/tasks/{task_id}`

## Observed Create Response

Live validation returned:

- HTTP 200
- body shape:

```json
{
  "task_status": "SUCCEED",
  "task_id": "...",
  "request_id": "..."
}
```

This means the create endpoint can immediately acknowledge success while still requiring follow-up task inspection to obtain image URLs.

## Observed Task Query Quirk

Live validation on 2026-04-17 showed a current backend quirk:

- repeated `GET /v1/tasks/{task_id}` calls returned:

```json
{
  "request_id": "",
  "task_id": "",
  "task_status": "PROCESSING",
  "outputs": {}
}
```

even after the create response had already reported `task_status: SUCCEED`.

Implication:

- client code must have a timeout
- client code must dump raw JSON for debugging
- client code must surface `task_id` and `request_id`
- do not promise that polling always resolves cleanly

## Supported Payload Fields Used By This Skill

Based on official examples, official model card content, and live API acceptance:

- `model`
- `prompt`
- `negative_prompt`
- `width`
- `height`
- `num_inference_steps`
- `seed`
- `loras`

The exact full server-side schema is not published in a stable public OpenAPI page that was directly retrievable here, so keep unknown-field handling permissive and prefer server error messages for unsupported fields.

## Qwen-Image-2512 Official Model Defaults

The official ModelScope model README for `Qwen/Qwen-Image-2512` includes a local diffusers example with:

- `num_inference_steps=50`
- `true_cfg_scale=4.0`
- a negative prompt example
- official aspect ratio presets:
  - `1:1 -> 1328x1328`
  - `16:9 -> 1664x928`
  - `9:16 -> 928x1664`
  - `4:3 -> 1472x1104`
  - `3:4 -> 1104x1472`
  - `3:2 -> 1584x1056`
  - `2:3 -> 1056x1584`

These are local-model recommendations, not a guaranteed hosted API schema. For hosted API-Inference, `1024x1024` was also accepted in live validation.

## Model Positioning

The official Qwen material states Qwen-Image focuses on:

- stronger text rendering
- better Chinese and bilingual typography
- stronger general image quality

The `Qwen-Image-2512` model page on ModelScope highlights:

- enhanced human realism
- finer natural detail
- improved text rendering

That makes it a strong default for:

- posters
- slide covers
- Chinese text-heavy visuals
- marketing or editorial hero images

## Secret Handling

Never write the token into:

- `SKILL.md`
- committed example code
- screenshots
- shell history if avoidable

Prefer:

- `MODELSCOPE_API_KEY`

Token management page referenced by ModelScope ecosystem material:

- `https://modelscope.cn/my/myaccesstoken`
