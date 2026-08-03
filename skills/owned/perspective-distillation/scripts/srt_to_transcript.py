#!/usr/bin/env python3

import re
import sys
from pathlib import Path


def clean(content: str) -> str:
    content = re.sub(r"^WEBVTT.*?\n\n", "", content, flags=re.S)
    content = re.sub(r"^NOTE.*?(?:\n\n|\Z)", "", content, flags=re.S | re.M)
    lines = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or re.fullmatch(r"\d+", line):
            continue
        if re.search(r"-->", line):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\s+(?:align|position|line|size):.*$", "", line).strip()
        if line and (not lines or line != lines[-1]):
            lines.append(line)

    paragraphs = []
    buffer = []
    for line in lines:
        buffer.append(line)
        combined = " ".join(buffer)
        if len(combined) >= 200 or re.search(r"[.!?。！？]$", line):
            paragraphs.append(combined)
            buffer = []
    if buffer:
        paragraphs.append(" ".join(buffer))
    return "\n\n".join(paragraphs)


def main() -> None:
    if len(sys.argv) not in {2, 3}:
        print("Usage: srt_to_transcript.py <input.srt|input.vtt> [output.txt]", file=sys.stderr)
        raise SystemExit(2)
    source = Path(sys.argv[1])
    if not source.is_file():
        print(f"Subtitle file not found: {source}", file=sys.stderr)
        raise SystemExit(2)
    output = Path(sys.argv[2]) if len(sys.argv) == 3 else source.with_name(f"{source.stem}_transcript.txt")
    transcript = clean(source.read_text(encoding="utf-8-sig"))
    output.write_text(transcript, encoding="utf-8")
    print(f"{output}\tcharacters={len(transcript)}\tparagraphs={len(transcript.splitlines())}")


if __name__ == "__main__":
    main()
