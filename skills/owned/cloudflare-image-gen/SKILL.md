---
name: cloudflare-image-gen
description: |
  Generate images using Cloudflare Workers AI image models.

  Use when asked to generate, draw, create, render, or visualize any image.

  Required env vars: CF_ACCOUNT_ID, CF_API_TOKEN

  Notes:
  - Cloudflare Workers AI returns JSON, and the image bytes are usually in `.result.image` as Base64.
  - For exact Chinese text, logos, or watermarks, prefer post-processing; direct prompt text rendering is unreliable.
  - `flux-1-schnell` can accept `width` and `height`, and both should be divisible by 8.
---

## Requirements

- `CF_ACCOUNT_ID`
- `CF_API_TOKEN`
- `curl`
- `jq`
- `base64`

## Model

Default model:

- `@cf/black-forest-labs/flux-1-schnell`

Good defaults:

- `steps=4` to `8`
- English prompts usually work better than Chinese prompts
- For wide covers, use sizes like `1600x896`
- `width` and `height` should both be divisible by `8`

## Generate Image

```bash
PROMPT="futuristic tech article cover, glowing terminal UI, cinematic lighting"
OUTPUT_FILE="./output.jpg"
MODEL="@cf/black-forest-labs/flux-1-schnell"
STEPS=8
WIDTH=1600
HEIGHT=896
TMP_JSON="$(mktemp)"

REQUEST_JSON="$(
  jq -n \
    --arg prompt "$PROMPT" \
    --argjson steps "$STEPS" \
    --argjson width "$WIDTH" \
    --argjson height "$HEIGHT" \
    '{
      prompt: $prompt,
      steps: $steps,
      width: $width,
      height: $height
    }'
)"

curl -sS -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/ai/run/$MODEL" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_JSON" \
  > "$TMP_JSON"

jq -e '.success == true' "$TMP_JSON" >/dev/null
jq -r '.result.image' "$TMP_JSON" | base64 --decode > "$OUTPUT_FILE"

echo "Saved to: $OUTPUT_FILE"
```

## If jq Is Not Available

Use Python for JSON handling and Base64 decode:

```bash
PROMPT="futuristic tech article cover, glowing terminal UI, cinematic lighting"
OUTPUT_FILE="./output.jpg"
MODEL="@cf/black-forest-labs/flux-1-schnell"
STEPS=8
WIDTH=1600
HEIGHT=896
TMP_JSON="$(mktemp)"

python - <<'PY' > "$TMP_JSON.request"
import json

payload = {
    "prompt": "futuristic tech article cover, glowing terminal UI, cinematic lighting",
    "steps": 8,
    "width": 1600,
    "height": 896,
}

print(json.dumps(payload, ensure_ascii=False))
PY

curl -sS -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/ai/run/$MODEL" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @"$TMP_JSON.request" \
  > "$TMP_JSON"

export TMP_JSON OUTPUT_FILE

python - <<'PY'
import base64
import json
import os
from pathlib import Path

tmp_json = Path(os.environ["TMP_JSON"])
output_file = Path(os.environ["OUTPUT_FILE"])

data = json.loads(tmp_json.read_text(encoding="utf-8"))
if not data.get("success"):
    raise SystemExit(json.dumps(data, ensure_ascii=False, indent=2))

img_b64 = data["result"]["image"]
output_file.write_bytes(base64.b64decode(img_b64))
print(f"Saved to: {output_file}")
PY
```

## Handle API Errors

Print the full JSON if the request fails:

```bash
jq . "$TMP_JSON"
```

Common issues:

- missing `CF_ACCOUNT_ID` or `CF_API_TOKEN`
- `width` / `height` not divisible by `8`
- prompt contains exact text requirements that the model cannot render reliably
- output extension does not match the actual decoded image format

## Parameters

- `prompt`: Best written in English for more stable quality
- `steps`: Usually `4` to `8`
- `width`: Image width, divisible by `8`
- `height`: Image height, divisible by `8`
- `OUTPUT_FILE`: Output path such as `./output.jpg`

## Recommended Sizes

- Wide article cover: `1600x896`
- Square social image: `1024x1024`
- Portrait poster: `1024x1536`

## Available Models

| Model | Speed | Quality | Notes |
|---|---|---|---|
| `@cf/black-forest-labs/flux-1-schnell` | Fast | High | Best default choice |
| `@cf/stabilityai/stable-diffusion-xl-base-1.0` | Medium | Medium | Older, broad compatibility |
| `@cf/lykon/dreamshaper-8-lcm` | Fast | Medium | Stylized output |

## Example Prompts

- Realistic:
  `portrait of a woman, photorealistic, soft window light, 85mm lens`
- Illustration:
  `cute cat on the moon, storybook illustration, pastel palette`
- Product:
  `minimalist product photo, white background, soft shadows`
- Tech banner:
  `wide futuristic developer article cover, terminal interface, blue neon glow, cinematic perspective`

## Practical Guidance

- If the user needs exact Chinese title text, exact logo text, or a precise watermark location:
  - generate the background with the model
  - add the final text in post-processing
- If the user only needs concept art or a rough cover:
  - direct model output is enough
