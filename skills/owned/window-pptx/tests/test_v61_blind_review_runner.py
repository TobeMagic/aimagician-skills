"""Focused, network-free tests for the Phase 49 blind-review runner."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from PIL import Image


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import run_window_pptx_v61_blind_reviews as cli  # noqa: E402
from window_pptx.v61_blind_acceptance import (  # noqa: E402
    aggregate_v61_blind_acceptance,
    load_hashed_document,
)
from window_pptx.v61_blind_reviews import (  # noqa: E402
    REVIEWER_LENSES,
    REVIEW_DIMENSIONS,
    canonical_json_bytes,
    sha256_file,
)


SHA = "a" * 64


def _labels(ordinals: list[int]) -> list[dict[str, Any]]:
    return [
        {
            "kind": kind,
            "ordinal": ordinal,
            "label": f"{kind.upper()}  /  SLIDE {ordinal:02d}",
        }
        for ordinal in ordinals
        for kind in ("reference", "candidate")
    ]


def _deck(kind: str, name: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "file_name": name,
        "observed_sha256": SHA,
        "size_bytes": 10,
        "expected_sha256": SHA,
        "hash_match": True,
        "slide_count": 15,
    }


def _render(kind: str) -> dict[str, Any]:
    return {
        "pdf": {
            "path": f"renders/{kind}/deck.pdf",
            "sha256": SHA,
            "size_bytes": 10,
        },
        "page_count": 15,
        "pages": [
            {
                "ordinal": ordinal,
                "path": f"renders/{kind}/pages/slide-{ordinal:03d}.png",
                "sha256": SHA,
                "size_bytes": 10,
                "width_px": 100,
                "height_px": 60,
            }
            for ordinal in range(1, 16)
        ],
    }


def _packet(packet_root: Path) -> dict[str, Any]:
    pair_root = packet_root / "pairs"
    pair_root.mkdir(parents=True)
    pairs: list[dict[str, Any]] = []
    for pair_index in range(1, 9):
        start = (pair_index - 1) * 2 + 1
        ordinals = [start] if pair_index == 8 else [start, start + 1]
        suffix = (
            f"slide-{ordinals[0]:02d}"
            if len(ordinals) == 1
            else f"slides-{ordinals[0]:02d}-{ordinals[1]:02d}"
        )
        relative = f"pairs/pair-{pair_index:02d}-{suffix}.png"
        image_path = packet_root / relative
        color = (pair_index * 20, 40, 80)
        Image.new("RGB", (100, 60), color).save(image_path, format="PNG")
        pairs.append(
            {
                "pair_index": pair_index,
                "slide_ordinals": ordinals,
                "path": relative,
                "sha256": sha256_file(image_path),
                "size_bytes": image_path.stat().st_size,
                "width_px": 100,
                "height_px": 60,
                "labels": _labels(ordinals),
            }
        )
    ordinals = list(range(1, 16))
    packet: dict[str, Any] = {
        "schema_version": "1.0",
        "packet_kind": "phase49-reference-candidate-blind-review",
        "packet_id": "phase49-blind-0123456789abcdef",
        "status": "pass",
        "expected_slide_count": 15,
        "dpi": 144,
        "inputs": {
            "reference_pptx": _deck("reference-pptx", "reference.pptx"),
            "candidate_pptx": _deck("candidate-pptx", "candidate.pptx"),
            "physical_report": {
                "kind": "physical-assembly-report",
                "file_name": "physical-assembly-report.v1.json",
                "observed_sha256": SHA,
                "size_bytes": 10,
                "packet_path": "inputs/physical-assembly-report.v1.json",
            },
            "rule_qa_report": {
                "kind": "rule-qa-report",
                "file_name": "rule-qa.v1.json",
                "observed_sha256": SHA,
                "size_bytes": 10,
                "packet_path": "inputs/rule-qa.v1.json",
            },
        },
        "toolchain": {
            "libreoffice": {
                "executable": "libreoffice",
                "version": "test",
                "sha256": SHA,
                "size_bytes": 10,
            },
            "pdftoppm": {
                "executable": "pdftoppm",
                "version": "test",
                "sha256": SHA,
                "size_bytes": 10,
            },
            "pillow": {"version": "test"},
        },
        "renders": {
            "reference": _render("reference"),
            "candidate": _render("candidate"),
        },
        "pairs": pairs,
        "coverage": {
            "expected_slide_ordinals": ordinals,
            "reference_slide_ordinals": ordinals,
            "candidate_slide_ordinals": ordinals,
            "pair_slide_ordinals": ordinals,
            "missing_slide_ordinals": [],
            "duplicate_slide_ordinals": [],
            "status": "pass",
        },
    }
    packet["packet_sha256"] = hashlib.sha256(canonical_json_bytes(packet)).hexdigest()
    (packet_root / "packet.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return packet


def _executable(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def _fake_vision(path: Path) -> Path:
    return _executable(
        path,
        """#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
import re
import sys

args = sys.argv[1:]
images = [args[index + 1] for index, value in enumerate(args) if value == '--image']
prompt_path = Path(args[args.index('--prompt-file') + 1])
prompt = prompt_path.read_text(encoding='utf-8')
segment = re.search(r'segment_id must be "([A-Z0-9_]+)"', prompt).group(1)
slides = json.loads(re.search(r'inspected_slides must be exactly (\\[[0-9,]+\\])', prompt).group(1))
inputs = []
for image in images:
    payload = Path(image).read_bytes()
    inputs.append({
        'kind': 'local',
        'name': Path(image).name,
        'mime': 'image/png',
        'bytes': len(payload),
        'sha256': hashlib.sha256(payload).hexdigest(),
    })
analysis = {
    'segment_id': segment,
    'inspected_slides': slides,
    'observations': [
        {'slide': slide, 'evidence': f'Slide {slide:02d}: candidate and reference compared.'}
        for slide in slides
    ],
}
attempts = int(os.environ.get('FAKE_VISION_ATTEMPTS', '1'))
result = {
    'status': 'success',
    'provider': 'agnes',
    'model': 'agnes-2.0-flash',
    'endpoint': 'https://example.invalid',
    'inputs': inputs,
    'attempts': {
        'total': attempts,
        'rateLimitEvents': max(0, attempts - 1),
        'transientRetries': 0,
    },
    'analysis': json.dumps(analysis, ensure_ascii=False),
    'usage': {'fake': True},
}
log = os.environ.get('FAKE_VISION_LOG')
if log:
    with open(log, 'a', encoding='utf-8') as handle:
        handle.write(json.dumps({'pid': os.getpid(), 'argv': args}) + '\\n')
print(json.dumps(result, ensure_ascii=False))
""",
    )


def _fake_codex(path: Path) -> Path:
    return _executable(
        path,
        """#!/usr/bin/env python3
import json
import os
from pathlib import Path
import re
import sys

args = sys.argv[1:]
prompt = sys.stdin.read()
reviewer = re.search(r'Reviewer lens \\((ART|NARRATIVE|PRODUCTION)\\)', prompt).group(1)
score = float(os.environ.get('FAKE_CODEX_SCORE', '9'))
output = {
    'schema_version': '1.0',
    'reviewer_id': reviewer,
    'inspected_slides': list(range(1, 16)),
    'scores': {
        key: score
        for key in (
            'narrative_logic', 'visual_hierarchy', 'layout_craft',
            'typography_readability', 'data_visualization', 'visual_rhythm',
            'brand_coherence', 'art_direction', 'delivery_readiness'
        )
    },
    'reference_parity': score >= 8,
    'findings': [],
    'notes': 'Independent fake synthesis completed.',
}
output_path = Path(args[args.index('--output-last-message') + 1])
output_path.write_text(json.dumps(output, ensure_ascii=False) + '\\n', encoding='utf-8')
log = os.environ.get('FAKE_CODEX_LOG')
if log:
    with open(log, 'a', encoding='utf-8') as handle:
        handle.write(json.dumps({
            'pid': os.getpid(),
            'argv': args,
            'prompt_marks_evidence_untrusted': (
                'untrusted visual observations' in prompt
                and 'Do not invoke tools' in prompt
            ),
        }) + '\\n')
if os.environ.get('FAKE_CODEX_FAIL') == '1':
    raise SystemExit(17)
if os.environ.get('FAKE_CODEX_NO_CONTEXT') != '1':
    print(json.dumps({'type': 'thread.started', 'thread_id': f'ctx-{reviewer}-0001'}))
print(json.dumps({'type': 'turn.completed'}))
""",
    )


def _fake_tools(tmp_path: Path) -> tuple[Path, Path, Path]:
    analyzer = tmp_path / "analyze.mjs"
    analyzer.write_text("// fake analyzer marker\n", encoding="utf-8")
    return _fake_vision(tmp_path / "fake-node"), analyzer, _fake_codex(tmp_path / "fake-codex")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _argv(
    packet_root: Path,
    output_root: Path,
    node: Path,
    analyzer: Path,
    codex: Path,
) -> list[str]:
    return [
        "--packet-root",
        str(packet_root),
        "--output-dir",
        str(output_root),
        "--allow-external-upload",
        "--node-bin",
        str(node),
        "--analyzer",
        str(analyzer),
        "--codex-bin",
        str(codex),
    ]


def test_runner_uses_six_fresh_vision_processes_and_three_fresh_codex_contexts(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    packet_root = tmp_path / "packet"
    packet_root.mkdir()
    packet = _packet(packet_root)
    node, analyzer, codex = _fake_tools(tmp_path)
    vision_log = tmp_path / "vision.jsonl"
    codex_log = tmp_path / "codex.jsonl"
    monkeypatch.setenv("FAKE_VISION_LOG", str(vision_log))
    monkeypatch.setenv("FAKE_CODEX_LOG", str(codex_log))
    output_root = tmp_path / "reviews"

    assert cli.main(_argv(packet_root, output_root, node, analyzer, codex)) == 0

    vision_calls = _read_jsonl(vision_log)
    codex_calls = _read_jsonl(codex_log)
    assert len(vision_calls) == 6
    assert len({item["pid"] for item in vision_calls}) == 6
    assert len(codex_calls) == 3
    assert len({item["pid"] for item in codex_calls}) == 3
    for call in vision_calls:
        assert call["argv"].count("--image") == 4
        assert call["argv"][call["argv"].index("--model") + 1] == "agnes-2.0-flash"
        assert "--allow-external-upload" in call["argv"]
    for call in codex_calls:
        assert "--ephemeral" in call["argv"]
        assert "--ignore-rules" in call["argv"]
        assert "resume" not in call["argv"]
        assert call["prompt_marks_evidence_untrusted"] is True
        assert call["argv"][call["argv"].index("-m") + 1] == "gpt-5.6-terra"

    segments = []
    reviews = []
    context_ids = set()
    invocation_ids = set()
    for reviewer_id in REVIEWER_LENSES:
        reviewer_root = output_root / "reviewers" / reviewer_id
        for segment_id in ("SLIDES_01_08", "SLIDES_09_15"):
            segment = reviewer_root / "segments" / f"{segment_id}.json"
            segments.append(load_hashed_document(segment))
            value = json.loads(segment.read_text(encoding="utf-8"))
            invocation_ids.add(value["invocation_id"])
            assert value["model_id"] == "agnes-2.0-flash"
            assert value["context_mode"] == "fresh-isolated"
            start = 0 if segment_id == "SLIDES_01_08" else 4
            stop = 4 if segment_id == "SLIDES_01_08" else 8
            assert value["image_sha256s"] == [
                item["sha256"]
                for item in packet["pairs"][start:stop]
            ]
        review_path = reviewer_root / "review.json"
        reviews.append(load_hashed_document(review_path))
        review = json.loads(review_path.read_text(encoding="utf-8"))
        context_ids.add(review["synthesis_context_id"])
        assert review["status"] == "PASS"
        assert review["median_score"] == 9.0
        assert set(review["scores"]) == set(REVIEW_DIMENSIONS)
    assert len(invocation_ids) == 6
    assert len(context_ids) == 3

    rubric_hash = hashlib.sha256(cli.DEFAULT_RUBRIC.read_bytes()).hexdigest()
    aggregate = aggregate_v61_blind_acceptance(
        segments,
        reviews,
        expected_packet_sha256=packet["packet_sha256"],
        expected_rubric_sha256=rubric_hash,
    )
    assert aggregate["status"] == "PASS"
    report = json.loads((output_root / "run-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["segment_invocation_count"] == 6
    assert report["unique_synthesis_context_count"] == 3


def test_runner_rejects_missing_slide_before_external_calls(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    packet_root = tmp_path / "packet"
    packet_root.mkdir()
    packet = _packet(packet_root)
    packet["pairs"][-1]["slide_ordinals"] = [14]
    packet["pairs"][-1]["labels"] = _labels([14])
    hash_basis = {
        key: value for key, value in packet.items() if key != "packet_sha256"
    }
    packet["packet_sha256"] = hashlib.sha256(
        canonical_json_bytes(hash_basis)
    ).hexdigest()
    (packet_root / "packet.json").write_text(json.dumps(packet), encoding="utf-8")
    node, analyzer, codex = _fake_tools(tmp_path)
    vision_log = tmp_path / "vision.jsonl"
    codex_log = tmp_path / "codex.jsonl"
    monkeypatch.setenv("FAKE_VISION_LOG", str(vision_log))
    monkeypatch.setenv("FAKE_CODEX_LOG", str(codex_log))
    output_root = tmp_path / "reviews"

    assert cli.main(_argv(packet_root, output_root, node, analyzer, codex)) == 2
    report = json.loads((output_root / "run-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "NOT_RUN"
    assert report["failure_reason"].startswith("PAIR_COVERAGE_INVALID:")
    assert not vision_log.exists()
    assert not codex_log.exists()


def test_runner_rejects_any_agnes_retry_and_does_not_synthesize(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    packet_root = tmp_path / "packet"
    packet_root.mkdir()
    _packet(packet_root)
    node, analyzer, codex = _fake_tools(tmp_path)
    vision_log = tmp_path / "vision.jsonl"
    codex_log = tmp_path / "codex.jsonl"
    monkeypatch.setenv("FAKE_VISION_LOG", str(vision_log))
    monkeypatch.setenv("FAKE_CODEX_LOG", str(codex_log))
    monkeypatch.setenv("FAKE_VISION_ATTEMPTS", "2")
    output_root = tmp_path / "reviews"

    assert cli.main(_argv(packet_root, output_root, node, analyzer, codex)) == 2
    report = json.loads((output_root / "run-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "NOT_RUN"
    assert report["failure_reason"].startswith("VISION_ATTEMPTS_INVALID:")
    assert len(_read_jsonl(vision_log)) == 1
    assert not codex_log.exists()


def test_runner_treats_codex_command_failure_as_not_run(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    packet_root = tmp_path / "packet"
    packet_root.mkdir()
    _packet(packet_root)
    node, analyzer, codex = _fake_tools(tmp_path)
    vision_log = tmp_path / "vision.jsonl"
    codex_log = tmp_path / "codex.jsonl"
    monkeypatch.setenv("FAKE_VISION_LOG", str(vision_log))
    monkeypatch.setenv("FAKE_CODEX_LOG", str(codex_log))
    monkeypatch.setenv("FAKE_CODEX_FAIL", "1")
    output_root = tmp_path / "reviews"

    assert cli.main(_argv(packet_root, output_root, node, analyzer, codex)) == 2
    report = json.loads((output_root / "run-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "NOT_RUN"
    assert report["failure_reason"].startswith("SYNTHESIS_COMMAND_FAILED:")
    assert len(_read_jsonl(vision_log)) == 2
    assert len(_read_jsonl(codex_log)) == 1


def test_runner_requires_an_actual_codex_context_id(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    packet_root = tmp_path / "packet"
    packet_root.mkdir()
    _packet(packet_root)
    node, analyzer, codex = _fake_tools(tmp_path)
    monkeypatch.setenv("FAKE_CODEX_NO_CONTEXT", "1")
    output_root = tmp_path / "reviews"

    assert cli.main(_argv(packet_root, output_root, node, analyzer, codex)) == 2
    report = json.loads((output_root / "run-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "NOT_RUN"
    assert report["failure_reason"].startswith("SYNTHESIS_CONTEXT_MISSING:")
    assert not (output_root / "reviewers" / "ART" / "review.json").exists()


def test_dry_run_validates_packet_without_resolving_or_running_models(
    tmp_path: Path,
) -> None:
    packet_root = tmp_path / "packet"
    packet_root.mkdir()
    _packet(packet_root)
    output_root = tmp_path / "reviews"

    assert cli.main(
        [
            "--packet-root",
            str(packet_root),
            "--output-dir",
            str(output_root),
            "--node-bin",
            "definitely-missing-node",
            "--codex-bin",
            "definitely-missing-codex",
            "--dry-run",
        ]
    ) == 0
    plan = json.loads((output_root / "dry-run-plan.json").read_text(encoding="utf-8"))
    assert plan["status"] == "DRY_RUN"
    assert len(plan["reviewers"]) == 3
    assert all(len(item["vision_processes"]) == 2 for item in plan["reviewers"])
    assert not (output_root / "reviewers").exists()


def test_completed_low_score_round_is_fail_not_not_run(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    packet_root = tmp_path / "packet"
    packet_root.mkdir()
    _packet(packet_root)
    node, analyzer, codex = _fake_tools(tmp_path)
    monkeypatch.setenv("FAKE_CODEX_SCORE", "7")
    output_root = tmp_path / "reviews"

    assert cli.main(_argv(packet_root, output_root, node, analyzer, codex)) == 1
    report = json.loads((output_root / "run-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "FAIL"
    assert [item["status"] for item in report["reviews"]] == ["FAIL", "FAIL", "FAIL"]
