"""Private, resumable Agnes-batch planning and strict report ingestion."""

from __future__ import annotations

import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Mapping, Sequence

from .observations import ObservationError, normalize_observation


class VisualBatchError(ValueError):
    """Raised when private evidence cannot be safely bound to a visual report."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _legacy_pngs(asset_index: Mapping[str, Any], private_root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for package in asset_index.get("packages", []):
        if not isinstance(package, Mapping) or package.get("status") != "ACCEPTED" or package.get("render_status") != "PASS":
            continue
        package_sha = package.get("package_sha256")
        if not isinstance(package_sha, str):
            continue
        for page in package.get("rendered_pages", []):
            if not isinstance(page, Mapping) or type(page.get("slide_number")) is not int:
                continue
            locator = page.get("png_path")
            if isinstance(locator, str) and locator and not Path(locator).is_absolute():
                result[f"{package_sha}:{page['slide_number']:03d}"] = private_root / locator
    return result


def _completed_pngs(render_index: Mapping[str, Any], evidence_root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for key, record in render_index.get("pages", {}).items():
        if not isinstance(key, str) or not isinstance(record, Mapping):
            continue
        locator = record.get("png_locator")
        if isinstance(locator, str) and locator and not Path(locator).is_absolute():
            result[key] = evidence_root / locator
    return result


def _existing_index(payload: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if payload is None:
        return {}
    entries = payload.get("observations")
    if not isinstance(entries, list):
        raise VisualBatchError("OBSERVATION_INDEX_INVALID")
    result: dict[str, Mapping[str, Any]] = {}
    for item in entries:
        if not isinstance(item, Mapping) or not isinstance(item.get("page_id"), str):
            raise VisualBatchError("OBSERVATION_INDEX_INVALID")
        result[item["page_id"]] = item
    return result


def plan_visual_batches(
    catalog: Mapping[str, Any],
    *,
    asset_index: Mapping[str, Any],
    completion_render_index: Mapping[str, Any],
    private_root: Path | str,
    completion_evidence_root: Path | str,
    existing_observations: Mapping[str, Any] | None = None,
    batch_size: int = 8,
) -> dict[str, Any]:
    """Resolve hash-bound local PNGs into private batches without source names."""

    if type(batch_size) is not int or not 1 <= batch_size <= 8:
        raise VisualBatchError("BATCH_SIZE_INVALID")
    root = Path(private_root).expanduser().resolve(strict=False)
    completed_root = Path(completion_evidence_root).expanduser().resolve(strict=False)
    if not root.is_dir() or root.is_symlink() or not completed_root.is_dir() or completed_root.is_symlink():
        raise VisualBatchError("PRIVATE_ROOT_INVALID")
    available = _legacy_pngs(asset_index, root)
    available.update(_completed_pngs(completion_render_index, completed_root))
    known = _existing_index(existing_observations)
    pending: list[dict[str, str]] = []
    for page in sorted(catalog.get("pages", []), key=lambda item: str(item.get("page_id"))):
        if not isinstance(page, Mapping):
            raise VisualBatchError("CATALOG_PAGE_INVALID")
        page_id, package_sha = page.get("page_id"), page.get("package_sha256")
        slide_number = page.get("slide_number")
        render = page.get("render")
        if not isinstance(page_id, str) or not isinstance(package_sha, str) or type(slide_number) is not int or not isinstance(render, Mapping):
            raise VisualBatchError("CATALOG_PAGE_INVALID")
        image_sha = render.get("image_sha256")
        if not isinstance(image_sha, str):
            raise VisualBatchError("CATALOG_RENDER_INVALID")
        already = known.get(page_id)
        if isinstance(already, Mapping) and already.get("image_sha256") == image_sha:
            continue
        png = available.get(f"{package_sha}:{slide_number:03d}")
        if png is None or not png.is_file() or png.is_symlink() or _sha256(png) != image_sha:
            raise VisualBatchError("PNG_EVIDENCE_MISSING")
        # This locator is private-only and never included in an Agnes prompt/report.
        pending.append({"page_id": page_id, "image_sha256": image_sha, "private_png_locator": png.relative_to(root).as_posix()})
    batches = [pending[index:index + batch_size] for index in range(0, len(pending), batch_size)]
    public_batches = [[{"page_id": item["page_id"], "image_sha256": item["image_sha256"]} for item in batch] for batch in batches]
    return {
        "schema_version": "1.0",
        "status": "PLANNED",
        "catalog_id": catalog.get("catalog_id"),
        "catalog_page_count": catalog.get("page_count"),
        "pending_page_count": len(pending),
        "batch_size": batch_size,
        "batches": batches,
        "public_batch_digest": hashlib.sha256(json.dumps(public_batches, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
    }


def prompt_for_batch(plan: Mapping[str, Any], *, batch_index: int) -> str:
    batches = plan.get("batches")
    if type(batch_index) is not int or not isinstance(batches, list) or not 0 <= batch_index < len(batches):
        raise VisualBatchError("BATCH_INDEX_INVALID")
    return (
        "You are cataloging presentation pages for deterministic retrieval. Return ONLY a JSON array, one object per supplied image in the same order, and no Markdown. Each object MUST be exactly "
        + '{"observation":{"visual_style":["..."],"composition":"...","hierarchy":"...","semantic_tags":["..."],"suggested_roles":["..."],"text_density":"...","uncertainty":"none|low|medium|high"}}. '
        + "Describe only visible visual and semantic qualities. Never mention or infer any filename, source, package, category, image bytes, credentials, paths, or external identity. "
        + "Use concise reusable tags. Suggested roles may be cover, contents, section, title, closing, one-item, two-item, three-item, four-item, five-item, six-item, multi-item, team, timeline, process, business-model, product, quote, partners, map, awards, case-study, table, chart, dashboard, comparison, roadmap."
    )


def ingest_batch_report(
    plan: Mapping[str, Any],
    *,
    batch_index: int,
    report: Mapping[str, Any],
    existing_observations: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize one sanitized Agnes report and merge it deterministically."""

    batches = plan.get("batches")
    if type(batch_index) is not int or not isinstance(batches, list) or not 0 <= batch_index < len(batches):
        raise VisualBatchError("BATCH_INDEX_INVALID")
    analysis = report.get("analysis")
    if not isinstance(analysis, str):
        raise VisualBatchError("AGNES_REPORT_INVALID")
    candidate = analysis.strip()
    # Some otherwise-conformant providers wrap the requested JSON in a fenced
    # block.  Accept only a single complete fence, then retain the same strict
    # identity/schema validation below; prose before/after remains rejected.
    if candidate.startswith("```") and candidate.endswith("```"):
        first_break = candidate.find("\n")
        if first_break <= 3:
            raise VisualBatchError("AGNES_REPORT_JSON_INVALID")
        candidate = candidate[first_break + 1:-3].strip()
    try:
        received = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise VisualBatchError("AGNES_REPORT_JSON_INVALID") from exc
    expected = batches[batch_index]
    if not isinstance(received, list) or len(received) != len(expected):
        raise VisualBatchError("AGNES_RESPONSE_CARDINALITY_INVALID")
    normalized: list[dict[str, Any]] = []
    for raw, identity in zip(received, expected, strict=True):
        if not isinstance(raw, Mapping) or not isinstance(identity, Mapping):
            raise VisualBatchError("AGNES_RESPONSE_INVALID")
        # The controller—not the vision model—attaches page and image identity.
        # This prevents a copied or mistyped 64-character model token from
        # weakening an otherwise direct one-image-to-one-observation binding.
        if set(raw) != {"observation"}:
            raise VisualBatchError("AGNES_RESPONSE_SCHEMA_INVALID")
        bound = {
            "schema_version": "1.0",
            "page_id": identity.get("page_id"),
            "image_sha256": identity.get("image_sha256"),
            "observation": raw.get("observation"),
        }
        try:
            normalized.append(normalize_observation(bound, page_id=str(identity.get("page_id")), image_sha256=str(identity.get("image_sha256"))))
        except ObservationError as exc:
            raise VisualBatchError(str(exc)) from exc
    merged = _existing_index(existing_observations)
    for item in normalized:
        merged[item["page_id"]] = item
    observations = [merged[key] for key in sorted(merged)]
    return {
        "schema_version": "1.0",
        "status": "PARTIAL" if len(observations) < int(plan.get("catalog_page_count", 0)) else "COMPLETE",
        "catalog_id": plan.get("catalog_id"),
        "observation_count": len(observations),
        "observations": observations,
    }


def run_agnes_batch(
    plan: Mapping[str, Any],
    *,
    batch_index: int,
    private_root: Path | str,
    vision_script: Path | str,
    existing_observations: Mapping[str, Any] | None = None,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    """Send only approved local PNGs, then immediately normalize the report."""

    root = Path(private_root).expanduser().resolve(strict=False)
    script = Path(vision_script).expanduser().resolve(strict=False)
    batches = plan.get("batches")
    if not root.is_dir() or root.is_symlink() or not script.is_file() or type(batch_index) is not int or not isinstance(batches, list) or not 0 <= batch_index < len(batches):
        raise VisualBatchError("AGNES_RUNNER_INPUT_INVALID")
    images: list[Path] = []
    for item in batches[batch_index]:
        locator = item.get("private_png_locator") if isinstance(item, Mapping) else None
        if not isinstance(locator, str) or not locator:
            raise VisualBatchError("PNG_EVIDENCE_MISSING")
        image = (root / locator).resolve(strict=False)
        if not image.is_relative_to(root) or not image.is_file() or image.is_symlink():
            raise VisualBatchError("PNG_EVIDENCE_MISSING")
        images.append(image)
    command = ["node", str(script)]
    for image in images:
        command.extend(("--image", str(image)))
    command.extend(("--prompt", prompt_for_batch(plan, batch_index=batch_index), "--allow-external-upload", "--json"))
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout_seconds)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VisualBatchError("AGNES_PROCESS_UNAVAILABLE") from exc
    if result.returncode != 0:
        # Do not retain upstream raw errors; callers may safely retry the batch.
        raise VisualBatchError("AGNES_PROCESS_FAILED")
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise VisualBatchError("AGNES_REPORT_JSON_INVALID") from exc
    if not isinstance(report, Mapping) or report.get("status") != "success":
        raise VisualBatchError("AGNES_REPORT_INVALID")
    return ingest_batch_report(plan, batch_index=batch_index, report=report, existing_observations=existing_observations)


def run_agnes_range(
    plan: Mapping[str, Any],
    *,
    batch_indices: Sequence[int],
    private_root: Path | str,
    vision_script: Path | str,
    existing_observations: Mapping[str, Any] | None = None,
    workers: int = 8,
) -> tuple[dict[str, Any], list[int]]:
    """Fetch independent one-page reports concurrently, then merge in order.

    No worker writes the observation index.  A response that fails validation
    leaves the caller's prior index untouched, so retries are deterministic.
    """

    if type(workers) is not int or not 1 <= workers <= 8 or not batch_indices or len(set(batch_indices)) != len(batch_indices):
        raise VisualBatchError("AGNES_RANGE_INVALID")
    ordered = sorted(batch_indices)
    if any(type(index) is not int for index in ordered):
        raise VisualBatchError("AGNES_RANGE_INVALID")

    def collect(index: int) -> Mapping[str, Any]:
        # Deliberately pass no existing index: this obtains a report only; the
        # deterministic merge below is the sole writer-equivalent operation.
        root = Path(private_root).expanduser().resolve(strict=False)
        script = Path(vision_script).expanduser().resolve(strict=False)
        batches = plan.get("batches")
        if not root.is_dir() or root.is_symlink() or not script.is_file() or not isinstance(batches, list) or not 0 <= index < len(batches):
            raise VisualBatchError("AGNES_RUNNER_INPUT_INVALID")
        images: list[Path] = []
        for item in batches[index]:
            locator = item.get("private_png_locator") if isinstance(item, Mapping) else None
            image = (root / locator).resolve(strict=False) if isinstance(locator, str) else None
            if image is None or not image.is_relative_to(root) or not image.is_file() or image.is_symlink():
                raise VisualBatchError("PNG_EVIDENCE_MISSING")
            images.append(image)
        command = ["node", str(script)]
        for image in images:
            command.extend(("--image", str(image)))
        command.extend(("--prompt", prompt_for_batch(plan, batch_index=index), "--allow-external-upload", "--json"))
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise VisualBatchError("AGNES_PROCESS_UNAVAILABLE") from exc
        if result.returncode != 0:
            raise VisualBatchError("AGNES_PROCESS_FAILED")
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise VisualBatchError("AGNES_REPORT_JSON_INVALID") from exc
        if not isinstance(report, Mapping) or report.get("status") != "success":
            raise VisualBatchError("AGNES_REPORT_INVALID")
        return report

    reports: dict[int, Mapping[str, Any]] = {}
    failures: list[int] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(collect, index): index for index in ordered}
        for future in as_completed(futures):
            index = futures[future]
            try:
                reports[index] = future.result()
            except VisualBatchError:
                failures.append(index)
    merged: Mapping[str, Any] | None = existing_observations
    for index in sorted(reports):
        try:
            merged = ingest_batch_report(plan, batch_index=index, report=reports[index], existing_observations=merged)
        except VisualBatchError:
            failures.append(index)
    assert isinstance(merged, dict)
    return merged, sorted(failures)
