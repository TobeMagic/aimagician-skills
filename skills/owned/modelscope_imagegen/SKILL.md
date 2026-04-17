---
name: modelscope_imagegen
description: |
  Generate images through ModelScope API-Inference, especially for Qwen/Qwen-Image-2512 and other ModelScope-hosted text-to-image or LoRA image models.

  Use this skill whenever the user asks to generate images with ModelScope, Qwen-Image, Qwen-Image-2512, ModelScope API-Inference, or wants a hosted image generation flow that uses a ModelScope token instead of local diffusion weights. Also use it when the user mentions async image generation with task polling, ModelScope LoRA image models, or wants Python or curl examples for ModelScope image APIs.

  Prefer environment variable MODELSCOPE_API_KEY. Do not hardcode tokens into source files, commits, logs, or screenshots.
compatibility:
  tools: [bash, python]
  requires: Python 3, requests, Pillow
---

# ModelScope Image Generation

This skill is for hosted image generation through ModelScope API-Inference.

Default target:

- `Qwen/Qwen-Image-2512`

Also works for:

- other API-Inference text-to-image model IDs on ModelScope
- LoRA model IDs hosted on ModelScope

Read [modelscope-api.md](./references/modelscope-api.md) when you need the source-backed details behind endpoints, headers, model defaults, or current quirks.

Use [modelscope_imagegen.py](./scripts/modelscope_imagegen.py) instead of retyping request logic by hand unless the user explicitly wants a one-off snippet.

## Before You Run

1. Prefer `MODELSCOPE_API_KEY` from the environment.
2. If the user pasted a token in chat, do not write it into repo files.
3. Confirm the target model ID if the user names a specific ModelScope model. Otherwise default to `Qwen/Qwen-Image-2512`.
4. Decide whether you need:
   - single image generation
   - multiple LoRAs
   - explicit width and height
   - deterministic output via `seed`

## Default Workflow

1. Build a JSON body for `POST https://api-inference.modelscope.cn/v1/images/generations`.
2. Send header `X-ModelScope-Async-Mode: true`.
3. Capture `task_id` and `request_id`.
4. Poll `GET https://api-inference.modelscope.cn/v1/tasks/{task_id}` with header `X-ModelScope-Task-Type: image_generation`.
5. Save the first returned image URL to disk.
6. If polling does not converge, save raw JSON and surface the `task_id` and `request_id` for debugging.

## Use the Bundled Script

Basic example:

```bash
export MODELSCOPE_API_KEY="ms-your-token"
python ~/.codex/skills/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --prompt "A golden cat" \
  --output ./result_image.jpg
```

Qwen-Image-2512 with explicit size, steps, and seed:

```bash
python ~/.codex/skills/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --model "Qwen/Qwen-Image-2512" \
  --prompt "A cinematic poster of a golden cat astronaut, detailed fur, crisp typography area" \
  --negative-prompt "low quality, blurry text, distorted anatomy" \
  --width 1024 \
  --height 1024 \
  --num-inference-steps 50 \
  --seed 42 \
  --output ./poster.jpg
```

Single LoRA:

```bash
python ~/.codex/skills/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --prompt "A fashion editorial portrait" \
  --loras "owner/lora-repo-id" \
  --output ./fashion.jpg
```

Multiple LoRAs:

```bash
python ~/.codex/skills/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --prompt "A stylized sci-fi portrait" \
  --loras '{"owner/lora-a": 0.6, "owner/lora-b": 0.4}' \
  --output ./portrait.jpg
```

Pass additional future-compatible JSON fields without editing the script:

```bash
python ~/.codex/skills/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --prompt "A product hero image" \
  --extra-json '{"num_images": 1}' \
  --output ./hero.jpg
```

## Parameters

Required:

- `model`: ModelScope model ID. Default `Qwen/Qwen-Image-2512`.
- `prompt`: Main generation prompt.

Common optional fields:

- `negative_prompt`: Use when you need to suppress blur, bad anatomy, oversaturation, or low-detail output.
- `width`
- `height`
- `num_inference_steps`
- `seed`
- `loras`

Operational controls:

- `poll_interval`
- `timeout`
- `output`
- `debug_json`

## Recommended Defaults

For `Qwen/Qwen-Image-2512`, prefer:

- `num_inference_steps=50`
- `seed` only when reproducibility matters
- aspect-ratio presets from the official model card:
  - `1328x1328`
  - `1664x928`
  - `928x1664`
  - `1472x1104`
  - `1104x1472`
  - `1584x1056`
  - `1056x1584`

If you are using hosted API-Inference rather than local diffusers, `1024x1024` is also a pragmatic default and was accepted in live API validation.

## Failure Handling

If the API returns HTTP 400 without async mode:

- add `X-ModelScope-Async-Mode: true`

If polling keeps returning `PROCESSING` with empty payload:

- do not silently loop forever
- stop at timeout
- print the last raw task JSON
- write `--debug-json` so the final task payload is preserved even on timeout
- include `task_id` and `request_id`
- keep the payload and headers minimal when retrying

If image download fails:

- dump the raw JSON first
- verify whether the result uses `output_images`, `outputs.output_images`, or another URL container

## Practical Guidance

- Keep prompts explicit about composition, style, camera, lighting, text, and layout.
- Use English prompts for broad visual control unless Chinese text rendering is itself the goal.
- If the user needs Chinese or bilingual poster text, Qwen-Image family is a strong default.
- Never commit `MODELSCOPE_API_KEY`.
- When generating assets for the current repo, save outputs outside the skill directory unless the user explicitly wants examples committed.
