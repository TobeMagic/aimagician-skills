#!/usr/bin/env bash

set -euo pipefail

url="${1:-}"
output_dir="${2:-.}"
if [[ -z "$url" ]]; then
  printf 'Usage: download_subtitles.sh <video-url> [output-dir]\n' >&2
  exit 2
fi
if ! command -v yt-dlp >/dev/null 2>&1; then
  printf 'yt-dlp is required but was not found; install it explicitly outside this script.\n' >&2
  exit 2
fi

mkdir -p "$output_dir"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

attempt() {
  local mode="$1"
  local languages="$2"
  rm -f "$scratch"/*
  yt-dlp "$mode" --sub-langs "$languages" --sub-format "srt/vtt/best" --skip-download \
    -o "$scratch/%(title)s.%(ext)s" "$url" >/dev/null
  mapfile -d '' files < <(find "$scratch" -maxdepth 1 -type f \( -name '*.srt' -o -name '*.vtt' \) -print0)
  if (( ${#files[@]} == 0 )); then
    return 1
  fi
  for file in "${files[@]}"; do
    cp -n "$file" "$output_dir/"
    printf '%s\n' "$output_dir/$(basename "$file")"
  done
}

attempt --write-subs "zh-Hans,zh-Hant,zh,zh-CN,zh-TW" ||
attempt --write-subs "en,en-US,en-GB" ||
attempt --write-auto-subs "zh-Hans,zh,en" || {
  printf 'No usable subtitles were found.\n' >&2
  exit 1
}
