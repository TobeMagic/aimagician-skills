#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash bootstrap_research_dir.sh <target-root>" >&2
  exit 1
fi

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_ROOT="$1"

mkdir -p \
  "$TARGET_ROOT/assets" \
  "$TARGET_ROOT/profiles" \
  "$TARGET_ROOT/queries" \
  "$TARGET_ROOT/raw" \
  "$TARGET_ROOT/processed" \
  "$TARGET_ROOT/runs"

if [[ ! -f "$TARGET_ROOT/profiles/template_profile.json" ]]; then
  cp "$SKILL_ROOT/assets/template_profile.json" \
    "$TARGET_ROOT/profiles/template_profile.json"
fi

if [[ ! -f "$TARGET_ROOT/queries/query_registry.json" ]]; then
  cp "$SKILL_ROOT/assets/starter_query_registry.json" \
    "$TARGET_ROOT/queries/query_registry.json"
fi

if [[ ! -f "$TARGET_ROOT/paper_triage_template.csv" ]]; then
  cp "$SKILL_ROOT/assets/paper_triage_template_20260321.csv" \
    "$TARGET_ROOT/paper_triage_template.csv"
fi

if [[ ! -f "$TARGET_ROOT/README.md" ]]; then
  cp "$SKILL_ROOT/assets/research_readme_stub.md" \
    "$TARGET_ROOT/README.md"
fi

echo "Bootstrapped deep research directory at: $TARGET_ROOT"
