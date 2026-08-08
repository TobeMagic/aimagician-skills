#!/usr/bin/env python3
"""Run the fifteen locked briefs through an ordinary semantic-only model."""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from window_pptx.benchmark import run_opencode_response
from window_pptx.ordinary_model_suite import (
    build_ordinary_plan_prompt,
    evaluate_ordinary_plan,
)
from window_pptx.project_brief_corpus import load_project_brief_corpus


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--model", default="opencode/deepseek-v4-flash-free"
    )
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--scenario", action="append", default=[])
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    corpus = load_project_brief_corpus()
    selected = sorted(args.scenario or corpus)
    unknown = sorted(set(selected) - set(corpus))
    if unknown:
        raise SystemExit(f"unknown scenarios: {unknown}")

    def run_one(scenario: str) -> dict[str, object]:
        pack = corpus[scenario]
        prompt = build_ordinary_plan_prompt(pack)
        plan_path = args.output_dir / f"{scenario}.brief-plan.v1.json"
        if plan_path.is_file():
            existing = plan_path.read_text(encoding="utf-8")
            evaluation = evaluate_ordinary_plan(pack, existing)
            if evaluation.status == "PASS":
                return {
                    "scenario_id": scenario,
                    "model_id": args.model,
                    "provider_status": "resumed",
                    "provider_exit_code": 0,
                    "response_sha256": _sha256_text(existing),
                    "prompt_sha256": _sha256_text(prompt),
                    **evaluation.to_dict(),
                    "plan_file": plan_path.name,
                    "attempt_chain": [],
                }
        attempt_chain: list[dict[str, object]] = []
        active_prompt = prompt
        provider = None
        evaluation = None
        for attempt in range(1, max(1, args.attempts) + 1):
            provider = run_opencode_response(
                model_id=args.model,
                prompt=active_prompt,
                directory=Path.cwd(),
                timeout_seconds=args.timeout_seconds,
            )
            evaluation = evaluate_ordinary_plan(pack, provider.response)
            attempt_chain.append(
                {
                    "attempt": attempt,
                    "provider_status": provider.status,
                    "exit_code": provider.exit_code,
                    "response_sha256": provider.response_sha256,
                    "validation_status": evaluation.status,
                    "validation_error": evaluation.error,
                }
            )
            if evaluation.status == "PASS":
                break
            active_prompt = (
                prompt
                + "\n上一次输出被确定性校验器拒绝："
                + str(evaluation.error)
                + "。重新从零输出完整 JSON；逐个核对 fact id 恰好一次，"
                "beat_hint 必须来自允许列表，禁止解释。"
            )
        assert provider is not None and evaluation is not None
        if evaluation.status == "PASS" and evaluation.normalized is not None:
            plan_path.write_text(
                json.dumps(
                    evaluation.normalized, ensure_ascii=False, indent=2
                )
                + "\n",
                encoding="utf-8",
            )
        return {
            "scenario_id": scenario,
            "model_id": args.model,
            "provider_status": provider.status,
            "provider_exit_code": provider.exit_code,
            "response_sha256": provider.response_sha256,
            "prompt_sha256": _sha256_text(prompt),
            **evaluation.to_dict(),
            "plan_file": plan_path.name if plan_path.is_file() else None,
            "attempt_chain": attempt_chain,
        }

    records: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(run_one, scenario): scenario for scenario in selected}
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            print(
                json.dumps(
                    {
                        "scenario_id": record["scenario_id"],
                        "status": record["status"],
                        "provider_status": record["provider_status"],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
    records.sort(key=lambda item: str(item["scenario_id"]))

    passed = sum(item["status"] == "PASS" for item in records)
    report = {
        "schema_version": "ordinary-model-suite.v1",
        "model_id": args.model,
        "scenario_count": len(records),
        "passed": passed,
        "pass_rate": passed / len(records) if records else 0.0,
        "status": "PASS" if passed == len(records) else "FAIL",
        "records": records,
    }
    report_path = args.output_dir / "ordinary-model-suite-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
