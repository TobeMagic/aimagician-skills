#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY="${1:-$ROOT/queries/query_registry.json}"
OUTPUT_ROOT="${2:-$ROOT}"

python "$ROOT/scripts/fetch_openalex.py" --registry "$REGISTRY" --output-root "$OUTPUT_ROOT"
python "$ROOT/scripts/fetch_arxiv.py" --registry "$REGISTRY" --output-root "$OUTPUT_ROOT"
python "$ROOT/scripts/fetch_crossref.py" --registry "$REGISTRY" --output-root "$OUTPUT_ROOT"
python "$ROOT/scripts/fetch_cvf_openaccess.py" --registry "$REGISTRY" --output-root "$OUTPUT_ROOT"
python "$ROOT/scripts/fetch_semantic_scholar.py" --registry "$REGISTRY" --output-root "$OUTPUT_ROOT"
python "$ROOT/scripts/build_literature_matrix.py" --registry "$REGISTRY" --output-root "$OUTPUT_ROOT"

echo "Deep research pipeline complete: registry=$REGISTRY output=$OUTPUT_ROOT"
