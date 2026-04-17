#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests
from PIL import Image

BASE_URL = "https://api-inference.modelscope.cn/"
DEFAULT_MODEL = "Qwen/Qwen-Image-2512"
DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_POLL_INTERVAL_SECONDS = 5


class ModelScopeTaskTimeout(TimeoutError):
    def __init__(self, task_id: str, last_json: dict[str, Any]) -> None:
        self.task_id = task_id
        self.last_json = last_json
        message = (
            "Timed out waiting for ModelScope task to finish. "
            f"task_id={task_id} last_response={json.dumps(last_json, ensure_ascii=False)}"
        )
        super().__init__(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate images with ModelScope API-Inference."
    )
    parser.add_argument("--prompt", required=True, help="Main text prompt.")
    parser.add_argument(
        "--output",
        default="./result_image.jpg",
        help="Output image path. Default: ./result_image.jpg",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"ModelScope model id. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument("--negative-prompt", help="Optional negative prompt.")
    parser.add_argument("--width", type=int, help="Optional output width.")
    parser.add_argument("--height", type=int, help="Optional output height.")
    parser.add_argument(
        "--num-inference-steps",
        type=int,
        help="Optional num_inference_steps value.",
    )
    parser.add_argument("--seed", type=int, help="Optional deterministic seed.")
    parser.add_argument(
        "--loras",
        help=(
            "Optional LoRA config. Either a plain repo id string or a JSON object, "
            'for example \'{"owner/lora-a": 0.6, "owner/lora-b": 0.4}\'.'
        ),
    )
    parser.add_argument(
        "--extra-json",
        help="Optional JSON object merged into the request body last.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Polling timeout in seconds. Default: {DEFAULT_TIMEOUT_SECONDS}",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help=f"Polling interval in seconds. Default: {DEFAULT_POLL_INTERVAL_SECONDS}",
    )
    parser.add_argument(
        "--debug-json",
        help="Optional file path for saving raw request and task JSON.",
    )
    return parser.parse_args()


def get_api_key() -> str:
    api_key = os.getenv("MODELSCOPE_API_KEY", "").strip()
    if api_key:
        return api_key

    raise SystemExit(
        "MODELSCOPE_API_KEY is not set. Get a token from "
        "https://modelscope.cn/my/myaccesstoken and export it before running."
    )


def parse_loras(raw: str | None) -> str | dict[str, float] | None:
    if not raw:
        return None

    stripped = raw.strip()
    if stripped.startswith("{"):
        parsed = json.loads(stripped)
        if not isinstance(parsed, dict):
            raise SystemExit("--loras JSON must decode to an object.")
        return parsed
    return stripped


def parse_extra_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise SystemExit("--extra-json must decode to an object.")
    return parsed


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": args.model,
        "prompt": args.prompt,
    }

    optional_fields = {
        "negative_prompt": args.negative_prompt,
        "width": args.width,
        "height": args.height,
        "num_inference_steps": args.num_inference_steps,
        "seed": args.seed,
        "loras": parse_loras(args.loras),
    }

    for key, value in optional_fields.items():
        if value is not None:
            payload[key] = value

    payload.update(parse_extra_json(args.extra_json))
    return payload


def create_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def create_task(
    api_key: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    headers = create_headers(api_key)
    response = requests.post(
        f"{BASE_URL}v1/images/generations",
        headers={**headers, "X-ModelScope-Async-Mode": "true"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=60,
    )
    response.raise_for_status()
    return response.json(), headers


def poll_task(
    api_key: str,
    task_id: str,
    timeout_seconds: int,
    poll_interval_seconds: int,
) -> dict[str, Any]:
    headers = {
        **create_headers(api_key),
        "X-ModelScope-Task-Type": "image_generation",
    }
    deadline = time.time() + timeout_seconds
    last_json: dict[str, Any] = {}

    while time.time() < deadline:
        response = requests.get(
            f"{BASE_URL}v1/tasks/{task_id}",
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        last_json = response.json()
        status = last_json.get("task_status")

        if status == "SUCCEED":
            return last_json
        if status == "FAILED":
            raise RuntimeError(f"ModelScope image generation failed: {json.dumps(last_json, ensure_ascii=False)}")

        time.sleep(poll_interval_seconds)

    raise ModelScopeTaskTimeout(task_id=task_id, last_json=last_json)


def extract_image_url(create_json: dict[str, Any], task_json: dict[str, Any] | None) -> str:
    candidates: list[str] = []

    for source in [create_json, task_json or {}]:
        if not source:
            continue

        direct_output_images = source.get("output_images")
        if isinstance(direct_output_images, list):
            candidates.extend(str(item) for item in direct_output_images if item)

        outputs = source.get("outputs")
        if isinstance(outputs, dict):
            nested_output_images = outputs.get("output_images")
            if isinstance(nested_output_images, list):
                candidates.extend(str(item) for item in nested_output_images if item)

        images = source.get("images")
        if isinstance(images, list):
            for item in images:
                if isinstance(item, dict) and item.get("url"):
                    candidates.append(str(item["url"]))
                elif isinstance(item, str):
                    candidates.append(item)

    for candidate in candidates:
        if candidate.startswith("http://") or candidate.startswith("https://"):
            return candidate

    raise RuntimeError(
        "Could not find an image URL in the ModelScope responses. "
        f"create_json={json.dumps(create_json, ensure_ascii=False)} "
        f"task_json={json.dumps(task_json or {}, ensure_ascii=False)}"
    )


def save_image(image_url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(image_url, timeout=120)
    response.raise_for_status()
    output_path.write_bytes(response.content)

    try:
        with Image.open(output_path) as image:
            image.verify()
    except Exception as exc:  # pragma: no cover - defensive runtime validation
        raise RuntimeError(f"Downloaded file is not a valid image: {exc}") from exc


def maybe_write_debug_json(
    path: str | None,
    payload: dict[str, Any],
    create_json: dict[str, Any],
    task_json: dict[str, Any] | None,
) -> None:
    if not path:
        return

    debug_path = Path(path)
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_payload = {
        "payload": payload,
        "create_response": create_json,
        "task_response": task_json,
    }
    debug_path.write_text(
        json.dumps(debug_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    api_key = get_api_key()
    payload = build_payload(args)

    create_json, _headers = create_task(api_key, payload)
    task_id = str(create_json.get("task_id", "")).strip()
    request_id = str(create_json.get("request_id", "")).strip()

    if not task_id:
        maybe_write_debug_json(args.debug_json, payload, create_json, None)
        raise SystemExit(f"ModelScope did not return task_id: {json.dumps(create_json, ensure_ascii=False)}")

    task_json: dict[str, Any] | None = None
    try:
        task_json = poll_task(
            api_key=api_key,
            task_id=task_id,
            timeout_seconds=args.timeout,
            poll_interval_seconds=args.poll_interval,
        )
    except ModelScopeTaskTimeout as exc:
        task_json = exc.last_json
        maybe_write_debug_json(args.debug_json, payload, create_json, task_json)
        raise SystemExit(str(exc)) from exc
    finally:
        if task_json is not None:
            maybe_write_debug_json(args.debug_json, payload, create_json, task_json)

    image_url = extract_image_url(create_json, task_json)
    output_path = Path(args.output).expanduser().resolve()
    save_image(image_url, output_path)

    print(f"Saved image to: {output_path}")
    print(f"task_id={task_id}")
    if request_id:
        print(f"request_id={request_id}")
    print(f"image_url={image_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
