#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

API_BASE = "https://www.modelscope.cn/api"
DEFAULT_TIMEOUT = 40


@dataclass
class ModelRecord:
    model_id: str
    stars: int
    downloads: int
    tasks: list[str]
    support_inference: str


def http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    response = requests.request(
        method=method,
        url=url,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json=payload,
        timeout=timeout,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.json()


def parse_model(item: dict[str, Any]) -> ModelRecord:
    path = str(item.get("Path") or "").strip()
    name = str(item.get("Name") or "").strip()
    model_id = f"{path}/{name}" if path and name else ""
    tasks = [
        str(task.get("Name") or "").strip()
        for task in (item.get("Tasks") or [])
        if isinstance(task, dict)
    ]
    tasks = [x for x in tasks if x]
    return ModelRecord(
        model_id=model_id,
        stars=int(item.get("Stars") or 0),
        downloads=int(item.get("Downloads") or 0),
        tasks=tasks,
        support_inference=str(item.get("SupportInference") or "").strip(),
    )


def query_models(keyword: str, page_size: int, timeout: int) -> list[ModelRecord]:
    payload = {"Path": "", "Name": keyword, "PageNumber": 1, "PageSize": page_size}
    data = http_json("PUT", f"{API_BASE}/v1/models/", payload=payload, timeout=timeout)
    models = ((data.get("Data") or {}).get("Models") or [])
    records: list[ModelRecord] = []
    for item in models:
        if not isinstance(item, dict):
            continue
        record = parse_model(item)
        if record.model_id:
            records.append(record)
    return records


def dedupe_models(models: list[ModelRecord]) -> list[ModelRecord]:
    merged: dict[str, ModelRecord] = {}
    for model in models:
        previous = merged.get(model.model_id)
        if previous is None or (model.stars, model.downloads) > (
            previous.stars,
            previous.downloads,
        ):
            merged[model.model_id] = model
    return list(merged.values())


def filter_by_task(
    models: list[ModelRecord], preferred_tasks: list[str] | None
) -> list[ModelRecord]:
    if not preferred_tasks:
        return models
    normalized = {x.strip().lower() for x in preferred_tasks if x.strip()}
    if not normalized:
        return models
    matched = []
    for model in models:
        task_set = {x.strip().lower() for x in model.tasks}
        if task_set.intersection(normalized):
            matched.append(model)
    return matched


def sort_models(models: list[ModelRecord]) -> list[ModelRecord]:
    return sorted(models, key=lambda m: (m.stars, m.downloads, m.model_id), reverse=True)


def command_recommend(args: argparse.Namespace) -> int:
    models: list[ModelRecord] = []
    for keyword in args.keyword:
        models.extend(
            query_models(keyword=keyword, page_size=args.page_size, timeout=args.timeout)
        )
    models = dedupe_models(models)
    models = filter_by_task(models, args.task)
    models = sort_models(models)[: args.top]

    if args.json:
        payload = [
            {
                "model_id": model.model_id,
                "stars": model.stars,
                "downloads": model.downloads,
                "tasks": model.tasks,
                "support_inference": model.support_inference,
            }
            for model in models
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for model in models:
            print(
                f"{model.stars:4d}  {model.model_id}  "
                f"tasks={model.tasks or ['']}"
            )
    return 0


DEFAULT_CAPABILITIES: dict[str, dict[str, Any]] = {
    "video_understanding": {
        "keywords": ["qwen2.5-omni", "video"],
        "tasks": ["any-to-any", "video-question-answering", "video-captioning"],
        "fallback_model": "Qwen/Qwen2.5-Omni-7B",
    },
    "video_caption": {
        "keywords": ["video-caption"],
        "tasks": ["video-captioning"],
        "fallback_model": "iic/multi-modal_hitea_video-captioning_base_en",
    },
    "subtitle_asr": {
        "keywords": ["paraformer", "asr"],
        "tasks": ["auto-speech-recognition"],
        "fallback_model": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    },
    "speech_language_id": {
        "keywords": ["lid", "speech-language-recognition", "language-id"],
        "tasks": ["speech-language-recognition"],
        "fallback_model": "iic/speech_whisper-large_lid_multilingual_pytorch",
    },
}


def query_model_detail(model_id: str, timeout: int) -> ModelRecord:
    data = http_json("GET", f"{API_BASE}/v1/models/{model_id}", timeout=timeout)
    item = data.get("Data") or {}
    return parse_model(item)


def pick_default_for_capability(
    capability: str,
    page_size: int,
    timeout: int,
) -> ModelRecord:
    rule = DEFAULT_CAPABILITIES[capability]
    candidates: list[ModelRecord] = []
    for keyword in rule["keywords"]:
        candidates.extend(query_models(keyword=keyword, page_size=page_size, timeout=timeout))
    candidates = dedupe_models(candidates)
    filtered = filter_by_task(candidates, rule["tasks"])
    ranked = sort_models(filtered if filtered else candidates)
    if ranked:
        return ranked[0]
    return query_model_detail(rule["fallback_model"], timeout=timeout)


def command_defaults(args: argparse.Namespace) -> int:
    output: dict[str, Any] = {}
    for capability in DEFAULT_CAPABILITIES:
        model = pick_default_for_capability(
            capability=capability,
            page_size=args.page_size,
            timeout=args.timeout,
        )
        output[capability] = {
            "model_id": model.model_id,
            "stars": model.stars,
            "downloads": model.downloads,
            "tasks": model.tasks,
            "support_inference": model.support_inference,
        }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def format_srt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    ms = int(round(seconds * 1000.0))
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1_000
    ms %= 1_000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_time_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.isdigit():
            return float(int(stripped))
        match = re.match(r"^(\\d+):(\\d+):(\\d+)(?:[\\.,](\\d+))?$", stripped)
        if match:
            hh = int(match.group(1))
            mm = int(match.group(2))
            ss = int(match.group(3))
            frac = match.group(4) or "0"
            frac_seconds = float(f"0.{frac}")
            return hh * 3600 + mm * 60 + ss + frac_seconds
    return None


def parse_segments(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if not isinstance(raw, dict):
        return []
    for key in ("segments", "sentences", "result", "outputs"):
        value = raw.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
        if isinstance(value, dict):
            nested = parse_segments(value)
            if nested:
                return nested
    return []


def command_build_srt(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    segments = parse_segments(payload)
    if not segments:
        raise SystemExit("No valid segments found in JSON.")

    lines: list[str] = []
    idx = 1
    for segment in segments:
        text = (
            segment.get("text")
            or segment.get("sentence")
            or segment.get("content")
            or ""
        )
        text = str(text).strip()
        if not text:
            continue

        start = parse_time_value(segment.get("start"))
        if start is None:
            start = parse_time_value(segment.get("start_time"))
        if start is None:
            start = parse_time_value(segment.get("begin_time"))

        end = parse_time_value(segment.get("end"))
        if end is None:
            end = parse_time_value(segment.get("end_time"))
        if end is None:
            end = parse_time_value(segment.get("stop"))

        if (start is None or end is None) and isinstance(
            segment.get("time_stamp"), (list, tuple)
        ):
            stamp = segment.get("time_stamp")
            if len(stamp) >= 2:
                start = parse_time_value(stamp[0]) if start is None else start
                end = parse_time_value(stamp[1]) if end is None else end

        if start is None or end is None:
            continue
        if end < start:
            end = start

        lines.append(str(idx))
        lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        lines.append(text)
        lines.append("")
        idx += 1

    if idx == 1:
        raise SystemExit("No subtitle entries could be generated from provided segments.")

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Saved subtitles to: {out_path}")
    return 0


def command_extract_audio(args: argparse.Namespace) -> int:
    video = Path(args.video).expanduser().resolve()
    audio = Path(args.output).expanduser().resolve()
    audio.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(args.sample_rate),
        "-ac",
        str(args.channels),
        str(audio),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        raise SystemExit(
            "ffmpeg failed.\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        )
    print(f"Extracted audio: {audio}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ModelScope video helper: model recommendation, audio extract, SRT conversion."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    recommend = subparsers.add_parser("recommend", help="Recommend models by keyword and star ranking.")
    recommend.add_argument("--keyword", action="append", required=True, help="Search keyword. Repeatable.")
    recommend.add_argument("--task", action="append", default=[], help="Preferred task filter. Repeatable.")
    recommend.add_argument("--page-size", type=int, default=80, help="Page size for each keyword query.")
    recommend.add_argument("--top", type=int, default=10, help="Top N models to output.")
    recommend.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout seconds.")
    recommend.add_argument("--json", action="store_true", help="Output JSON.")
    recommend.set_defaults(func=command_recommend)

    defaults = subparsers.add_parser("defaults", help="Resolve default models for core capabilities.")
    defaults.add_argument("--page-size", type=int, default=80, help="Page size for model search.")
    defaults.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout seconds.")
    defaults.set_defaults(func=command_defaults)

    srt = subparsers.add_parser("build-srt", help="Convert ASR segment JSON into .srt subtitles.")
    srt.add_argument("--segments", required=True, help="Input JSON path with segment timings.")
    srt.add_argument("--output", required=True, help="Output .srt path.")
    srt.set_defaults(func=command_build_srt)

    audio = subparsers.add_parser("extract-audio", help="Extract mono WAV from video with ffmpeg.")
    audio.add_argument("--video", required=True, help="Input video file path.")
    audio.add_argument("--output", required=True, help="Output WAV path.")
    audio.add_argument("--sample-rate", type=int, default=16000, help="Audio sample rate.")
    audio.add_argument("--channels", type=int, default=1, help="Number of channels.")
    audio.set_defaults(func=command_extract_audio)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        raise SystemExit(f"HTTP error: {status}") from exc
    except requests.RequestException as exc:
        raise SystemExit(f"Network error: {exc}") from exc


if __name__ == "__main__":
    sys.exit(main())
