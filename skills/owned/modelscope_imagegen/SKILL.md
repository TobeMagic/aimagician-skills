---
name: modelscope_imagegen
description: |
  Generate and edit images through ModelScope API-Inference, especially for Qwen/Qwen-Image-2512 (text-to-image) and Qwen/Qwen-Image-Edit-2511 (image-to-image edit).

  Use this skill whenever the user asks to generate images with ModelScope, edit an existing image with ModelScope, use Qwen-Image/Qwen-Image-Edit, call ModelScope API-Inference, or wants a hosted image workflow with token auth instead of local diffusion weights. Also use it when the user mentions async task polling, LoRA image models, single-image or multi-image edit, or wants Python/curl examples for ModelScope image APIs.

  Prefer environment variable MODELSCOPE_API_KEY. Do not hardcode tokens into source files, commits, logs, or screenshots.
compatibility:
  tools: [bash, python]
  requires: Python 3, requests, Pillow
---

# ModelScope Image Generation and Editing

This skill is for hosted image generation and image editing through ModelScope API-Inference.

Default target:

- `Qwen/Qwen-Image-2512`

Default image-edit target:

- `Qwen/Qwen-Image-Edit-2511`

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
   - image editing from one or more input images
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

Image edit (图生图): single input image URL:

```bash
python ~/.codex/skills/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --model "Qwen/Qwen-Image-Edit-2511" \
  --prompt "给图中的狗戴上一个生日帽，写实风格，保留原图构图" \
  --image-url "https://modelscope.oss-cn-beijing.aliyuncs.com/Dog.png" \
  --output ./dog-birthday.jpg
```

Image edit (multi-image composition):

```bash
python ~/.codex/skills/modelscope_imagegen/scripts/modelscope_imagegen.py \
  --model "Qwen/Qwen-Image-Edit-2511" \
  --prompt "写实风格，生成图一中的狗去追图二中的飞盘" \
  --image-url "https://modelscope.oss-cn-beijing.aliyuncs.com/Dog.png" \
  --image-url "https://modelscope.oss-cn-beijing.aliyuncs.com/Frisbee.png" \
  --output ./dog-frisbee.jpg
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
- `image_url`: one or more input image URLs for image-to-image editing (`--image-url` can be repeated)

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

For `Qwen/Qwen-Image-Edit-2511`, prefer:

- explicitly provide one or more `image_url` inputs
- keep prompt instruction specific about what to preserve and what to modify
- for multi-image editing, list image URLs in semantic order used by the prompt

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
- For image editing, ask the user to specify "what to keep unchanged" to avoid over-editing.
- Never commit `MODELSCOPE_API_KEY`.
- When generating assets for the current repo, save outputs outside the skill directory unless the user explicitly wants examples committed.
