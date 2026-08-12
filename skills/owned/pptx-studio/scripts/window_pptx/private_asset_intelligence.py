"""Quarantine, inspect, render, and deduplicate private Gaojie PPTX assets."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from .gaojie_diversity import (
    PreviewFingerprint,
    fingerprint_distance,
    fingerprint_preview,
    select_diverse,
)
from .layouts import SlideSize
from .libreoffice import LibreOfficeVerificationError, LibreOfficeVerifier
from .quarantine import inspect_package_bytes


_SLIDE_PATH = re.compile(r"ppt/slides/slide(\d+)\.xml", re.I)
_MAX_XML_BYTES = 16 * 1024 * 1024
_ROLE_BY_CATEGORY = {
    "封面模板": "cover",
    "目录模板": "contents",
    "章节模板": "section",
    "标题模板": "statement",
    "结尾模板": "closing",
    "人物介绍": "people",
    "荣誉奖项": "awards",
    "地图排版": "map",
    "时间轴图": "timeline",
    "架构流程": "process",
    "商业模型": "business-model",
    "样机展示": "mockup",
    "金句模板": "quote",
    "合作伙伴": "logo-wall",
    "图文排版": "image-text",
    "表格图表": "data",
    "发布会": "launch",
}


def _atomic_json(value: dict[str, Any], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".json", dir=target.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def _safe_xml(archive: zipfile.ZipFile, name: str) -> ElementTree.Element:
    info = archive.getinfo(name)
    if info.file_size > _MAX_XML_BYTES:
        raise ValueError("OOXML member exceeds inspection limit")
    payload = archive.read(info)
    upper = payload.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("OOXML member contains a DTD or entity")
    return ElementTree.fromstring(payload)


def _presentation_geometry(
    archive: zipfile.ZipFile,
) -> tuple[int, SlideSize]:
    root = _safe_xml(archive, "ppt/presentation.xml")
    slide_ids = [
        element
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] == "sldId"
    ]
    size = next(
        (
            element
            for element in root.iter()
            if element.tag.rsplit("}", 1)[-1] == "sldSz"
        ),
        None,
    )
    if size is None:
        raise ValueError("presentation slide size is missing")
    width = int(size.attrib["cx"]) / 914400
    height = int(size.attrib["cy"]) / 914400
    return len(slide_ids), SlideSize(width=width, height=height)


def _inspect_ooxml(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        slide_count, slide_size = _presentation_geometry(archive)
        slide_names = sorted(
            (name for name in names if _SLIDE_PATH.fullmatch(name)),
            key=lambda name: int(_SLIDE_PATH.fullmatch(name).group(1)),
        )
        if len(slide_names) != slide_count:
            raise ValueError("slide list and OOXML members disagree")
        shape_count = 0
        text_run_count = 0
        table_count = 0
        fonts: set[str] = set()
        for name in slide_names:
            root = _safe_xml(archive, name)
            for element in root.iter():
                local = element.tag.rsplit("}", 1)[-1]
                if local in {"sp", "pic", "graphicFrame", "cxnSp"}:
                    shape_count += 1
                if local == "t" and (element.text or "").strip():
                    text_run_count += 1
                if local == "tbl":
                    table_count += 1
                typeface = element.attrib.get("typeface")
                if typeface:
                    fonts.add(typeface)
        for name in names:
            if not (
                name.startswith("ppt/theme/")
                or name.startswith("ppt/slideMasters/")
                or name.startswith("ppt/slideLayouts/")
            ) or not name.endswith(".xml"):
                continue
            try:
                root = _safe_xml(archive, name)
            except (KeyError, ValueError, ElementTree.ParseError):
                continue
            for element in root.iter():
                typeface = element.attrib.get("typeface")
                if typeface:
                    fonts.add(typeface)
        metrics = {
            "slide_count": slide_count,
            "slide_width_in": round(slide_size.width, 6),
            "slide_height_in": round(slide_size.height, 6),
            "master_count": sum(
                name.startswith("ppt/slideMasters/slideMaster")
                and name.endswith(".xml")
                for name in names
            ),
            "layout_count": sum(
                name.startswith("ppt/slideLayouts/slideLayout")
                and name.endswith(".xml")
                for name in names
            ),
            "theme_count": sum(
                name.startswith("ppt/theme/theme") and name.endswith(".xml")
                for name in names
            ),
            "media_count": sum(name.startswith("ppt/media/") for name in names),
            "chart_count": sum(
                name.startswith("ppt/charts/chart") and name.endswith(".xml")
                for name in names
            ),
            "diagram_part_count": sum(
                name.startswith("ppt/diagrams/") for name in names
            ),
            "shape_count": shape_count,
            "text_run_count": text_run_count,
            "table_count": table_count,
            "fonts": sorted(fonts, key=str.casefold),
        }
        structural = {
            key: value
            for key, value in metrics.items()
            if key not in {"fonts"}
        }
        structural["font_count"] = len(fonts)
        metrics["structural_sha256"] = hashlib.sha256(
            json.dumps(
                structural,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        metrics["editable"] = bool(
            shape_count or text_run_count or metrics["chart_count"] or table_count
        )
        return metrics


def _category_role(
    category_keys: list[str],
    categories: dict[str, dict[str, Any]],
) -> tuple[str, list[str]]:
    names = sorted(
        {
            str(categories[key]["name"])
            for key in category_keys
            if key in categories
        }
    )
    roles = [_ROLE_BY_CATEGORY[name] for name in names if name in _ROLE_BY_CATEGORY]
    if roles:
        return roles[0], names
    for name in names:
        match = re.fullmatch(r"([一二三四五六])段内容", name)
        if match:
            return "content-blocks", names
    return "supporting-asset", names


def mine_gaojie_private_assets(
    private_root: Path | str,
    *,
    render: bool = False,
    maximum_items: int | None = None,
    render_workers: int = 4,
) -> dict[str, Any]:
    """Produce resumable private package and slide intelligence evidence."""

    root = Path(private_root).resolve()
    state_path = root / "state" / "gaojie-sync.json"
    try:
        sync_state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Gaojie sync state is missing or unreadable") from exc
    categories = sync_state.get("categories")
    artifacts = sync_state.get("artifacts")
    if not isinstance(categories, dict) or not isinstance(artifacts, list):
        raise ValueError("Gaojie sync state is incomplete")

    report_path = root / "intelligence" / "gaojie" / "asset-index.json"
    existing: dict[str, Any] = {}
    if report_path.is_file():
        try:
            existing_report = json.loads(report_path.read_text(encoding="utf-8"))
            existing = {
                item["package_sha256"]: item
                for item in existing_report.get("packages", [])
                if isinstance(item, dict) and isinstance(item.get("package_sha256"), str)
            }
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            existing = {}

    if not 1 <= render_workers <= 8:
        raise ValueError("render_workers must be between one and eight")
    packages: list[dict[str, Any]] = []
    for artifact in artifacts[:maximum_items]:
        relative = artifact.get("path")
        if not isinstance(relative, str):
            continue
        candidate = (root / relative).resolve()
        if root not in candidate.parents or not candidate.is_file():
            packages.append({
                "status": "REJECTED",
                "finding_codes": ["PACKAGE_MISSING"],
                "package_sha256": artifact.get("sha256"),
            })
            continue
        payload = candidate.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        cached = existing.get(digest)
        if cached is not None and (not render or cached.get("render_status") == "PASS"):
            packages.append(cached)
            continue
        quarantine = inspect_package_bytes(payload)
        role, category_names = _category_role(
            list(artifact.get("category_keys", [])),
            categories,
        )
        record: dict[str, Any] = {
            "package_sha256": digest,
            "bytes": len(payload),
            "private_path": candidate.relative_to(root).as_posix(),
            "category_names": category_names,
            "page_role": role,
            "quarantine": quarantine,
            "status": "QUARANTINED",
            "render_status": "NOT_RUN",
        }
        if quarantine["disposition"] != "ACCEPT":
            packages.append(record)
            _atomic_json(
                {
                    "schema_version": "gaojie-asset-intelligence.v1",
                    "packages": packages,
                },
                report_path,
            )
            continue
        try:
            structure = _inspect_ooxml(candidate)
        except (KeyError, OSError, ValueError, zipfile.BadZipFile, ElementTree.ParseError):
            record["status"] = "REJECTED"
            record["finding_codes"] = ["OOXML_INSPECTION_FAILED"]
            packages.append(record)
            _atomic_json(
                {
                    "schema_version": "gaojie-asset-intelligence.v1",
                    "packages": packages,
                },
                report_path,
            )
            continue
        record["structure"] = structure
        record["status"] = "ACCEPTED"
        packages.append(record)
        _atomic_json(
            {
                "schema_version": "gaojie-asset-intelligence.v1",
                "packages": packages,
            },
            report_path,
        )

    if render:
        render_indices = [
            index
            for index, package in enumerate(packages)
            if package.get("status") == "ACCEPTED"
            and package.get("render_status") != "PASS"
        ]

        def render_one(index: int) -> tuple[int, dict[str, Any]]:
            package = dict(packages[index])
            structure = package["structure"]
            candidate = root / package["private_path"]
            proof_root = (
                root
                / "evidence"
                / "gaojie"
                / "rendered"
                / package["package_sha256"][:20]
            )
            try:
                proof = LibreOfficeVerifier(dpi=96).verify(
                    candidate,
                    artifact_dir=proof_root,
                    expected_slide_count=structure["slide_count"],
                    slide_size=SlideSize(
                        width=structure["slide_width_in"],
                        height=structure["slide_height_in"],
                    ),
                )
            except LibreOfficeVerificationError:
                package["render_status"] = "FAIL"
                package["finding_codes"] = ["PORTABLE_RENDER_FAILED"]
                return index, package
            package["render_status"] = "PASS"
            package["rendered_pages"] = []
            for slide_number, png_path in enumerate(proof.png_paths, start=1):
                preview = fingerprint_preview(png_path.read_bytes())
                package["rendered_pages"].append({
                    "slide_number": slide_number,
                    "png_path": png_path.relative_to(root).as_posix(),
                    "visual_sha256": preview.sha256,
                    "dhash": preview.dhash,
                    "quality": preview.quality,
                    "width": preview.width,
                    "height": preview.height,
                })
            return index, package

        with ThreadPoolExecutor(
            max_workers=render_workers,
            thread_name_prefix="gaojie-render",
        ) as executor:
            for index, package in executor.map(render_one, render_indices):
                packages[index] = package
                _atomic_json(
                    {
                        "schema_version": "gaojie-asset-intelligence.v1",
                        "packages": packages,
                    },
                    report_path,
                )

    structural_clusters: dict[str, list[str]] = defaultdict(list)
    visual_clusters: dict[str, list[str]] = defaultdict(list)
    for package in packages:
        structure = package.get("structure")
        if isinstance(structure, dict):
            structural_clusters[str(structure["structural_sha256"])].append(
                package["package_sha256"]
            )
        for page in package.get("rendered_pages", []):
            visual_clusters[str(page["visual_sha256"])].append(
                f"{package['package_sha256']}:{page['slide_number']}"
            )
    report = {
        "schema_version": "gaojie-asset-intelligence.v1",
        "status": (
            "PASS"
            if packages
            and all(
                package.get("status") == "ACCEPTED"
                and (not render or package.get("render_status") == "PASS")
                for package in packages
            )
            else "PARTIAL"
        ),
        "render_requested": render,
        "package_count": len(packages),
        "accepted_count": sum(
            package.get("status") == "ACCEPTED" for package in packages
        ),
        "rendered_slide_count": sum(
            len(package.get("rendered_pages", [])) for package in packages
        ),
        "structural_clusters": {
            key: value
            for key, value in sorted(structural_clusters.items())
            if len(value) > 1
        },
        "visual_exact_clusters": {
            key: value
            for key, value in sorted(visual_clusters.items())
            if len(value) > 1
        },
        "packages": packages,
    }
    _atomic_json(report, report_path)
    return report


def _expanded_ordinals(value: dict[str, Any], *, page_count: int) -> list[int]:
    ordinals = value.get("ordinals", [])
    ranges = value.get("inclusive_ranges", [])
    if not isinstance(ordinals, list) or not isinstance(ranges, list):
        raise ValueError("visual disposition ordinals are malformed")
    expanded: list[int] = []
    for ordinal in ordinals:
        if type(ordinal) is not int:
            raise ValueError("visual disposition ordinal must be an integer")
        expanded.append(ordinal)
    for bounds in ranges:
        if (
            not isinstance(bounds, list)
            or len(bounds) != 2
            or any(type(item) is not int for item in bounds)
            or bounds[0] > bounds[1]
        ):
            raise ValueError("visual disposition range is malformed")
        expanded.extend(range(bounds[0], bounds[1] + 1))
    if any(ordinal < 1 or ordinal > page_count for ordinal in expanded):
        raise ValueError("visual disposition ordinal is out of range")
    return expanded


def apply_gaojie_visual_disposition(
    pages: list[dict[str, Any]],
    disposition_path: Path | str,
    *,
    source_core_schema: str,
) -> dict[str, Any]:
    """Bind a full-coverage independent visual disposition to ordered pages."""

    try:
        disposition = json.loads(
            Path(disposition_path).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("visual disposition is missing or unreadable") from exc
    if disposition.get("schema_version") != "gaojie-visual-disposition.v1":
        raise ValueError("visual disposition schema is unsupported")
    if disposition.get("source_core_schema") != source_core_schema:
        raise ValueError("visual disposition source schema does not match")
    if disposition.get("source_page_count") != len(pages):
        raise ValueError("visual disposition source page count does not match")
    page_ids = [str(page.get("page_id", "")) for page in pages]
    if any(not page_id for page_id in page_ids):
        raise ValueError("visual disposition source page ID is missing")
    order_digest = hashlib.sha256(
        ("\n".join(page_ids) + "\n").encode("utf-8")
    ).hexdigest()
    if disposition.get("source_order_sha256") != order_digest:
        raise ValueError("visual disposition source order does not match")

    records: dict[str, dict[str, Any]] = {}

    def bind(
        ordinals: list[int],
        *,
        decision: str,
        pool: str,
        reason_code: str | None = None,
        severity: str | None = None,
    ) -> None:
        for ordinal in ordinals:
            page_id = page_ids[ordinal - 1]
            if page_id in records:
                raise ValueError("visual disposition contains duplicate ordinals")
            record: dict[str, Any] = {
                "ordinal": ordinal,
                "decision": decision,
                "pool": pool,
            }
            if reason_code is not None:
                record["reason_code"] = reason_code
            if severity is not None:
                record["severity"] = severity
            records[page_id] = record

    keep = disposition.get("keep")
    reroute = disposition.get("reroute")
    deny = disposition.get("deny")
    if not isinstance(keep, dict) or not isinstance(reroute, dict) or not isinstance(deny, dict):
        raise ValueError("visual disposition decisions are incomplete")
    pool = keep.get("pool")
    if not isinstance(pool, str) or not pool:
        raise ValueError("visual disposition keep pool is missing")
    keep_ordinals = _expanded_ordinals(keep, page_count=len(pages))
    bind(keep_ordinals, decision="keep", pool=pool)
    reroute_count = 0
    for route, value in sorted(reroute.items()):
        if not isinstance(route, str) or not route or not isinstance(value, dict):
            raise ValueError("visual disposition reroute entry is malformed")
        ordinals = _expanded_ordinals(value, page_count=len(pages))
        reroute_count += len(ordinals)
        bind(ordinals, decision="reroute", pool=route)
    deny_count = 0
    for code, value in sorted(deny.items()):
        if not isinstance(code, str) or not code or not isinstance(value, dict):
            raise ValueError("visual disposition deny entry is malformed")
        severity = value.get("severity")
        if severity not in {"Blocker", "Important"}:
            raise ValueError("visual disposition deny severity is invalid")
        ordinals = _expanded_ordinals(value, page_count=len(pages))
        deny_count += len(ordinals)
        bind(
            ordinals,
            decision="deny",
            pool="excluded",
            reason_code=code,
            severity=severity,
        )
    if len(records) != len(pages):
        raise ValueError("visual disposition is not a complete page partition")
    return {
        "schema_version": disposition["schema_version"],
        "source_order_sha256": order_digest,
        "counts": {
            "keep": len(keep_ordinals),
            "reroute": reroute_count,
            "deny": deny_count,
        },
        "records": records,
    }


def deduplicate_routed_pages(
    pages: list[dict[str, Any]],
    *,
    private_root: Path | str,
    near_duplicate_distance: float = 0.03,
    same_package_near_duplicate_distance: float = 0.05,
) -> dict[str, Any]:
    """Deduplicate all routed pages, preferring complete layouts as canonical."""

    if not 0 <= near_duplicate_distance <= 1:
        raise ValueError("near_duplicate_distance must be between zero and one")
    if not near_duplicate_distance <= same_package_near_duplicate_distance <= 1:
        raise ValueError(
            "same-package duplicate distance must be at least the global distance"
        )
    root = Path(private_root).resolve()
    ranked = sorted(
        enumerate(pages),
        key=lambda item: (
            0 if item[1].get("pool") == "complete-layout" else 1,
            item[0],
        ),
    )
    canonical: list[dict[str, Any]] = []
    fingerprints: dict[str, PreviewFingerprint] = {}
    aliases: list[dict[str, str]] = []
    for _, page in ranked:
        relative = page.get("png_path")
        path = (root / relative).resolve() if isinstance(relative, str) else None
        if path is None or root not in path.parents or not path.is_file():
            raise ValueError("routed page render is missing or escapes private root")
        fingerprint = fingerprint_preview(path.read_bytes())
        match: tuple[dict[str, Any], str] | None = None
        for candidate in canonical:
            other = fingerprints[candidate["page_id"]]
            if fingerprint.sha256 == other.sha256:
                match = (candidate, "EXACT_VISUAL_DUPLICATE")
                break
            distance = fingerprint_distance(fingerprint, other)
            same_package = (
                page.get("package_sha256") is not None
                and page.get("package_sha256") == candidate.get("package_sha256")
            )
            if same_package and distance < same_package_near_duplicate_distance:
                match = (candidate, "SAME_PACKAGE_NEAR_DUPLICATE")
                break
            if distance < near_duplicate_distance:
                match = (candidate, "NEAR_VISUAL_DUPLICATE")
                break
        if match is not None:
            aliases.append({
                "alias_page_id": page["page_id"],
                "canonical_page_id": match[0]["page_id"],
                "reason": match[1],
            })
            continue
        enriched = dict(page)
        enriched["visual_fingerprint"] = fingerprint.to_dict()
        canonical.append(enriched)
        fingerprints[page["page_id"]] = fingerprint
    return {
        "canonical_pages": canonical,
        "aliases": aliases,
        "exact_duplicate_count": sum(
            alias["reason"] == "EXACT_VISUAL_DUPLICATE" for alias in aliases
        ),
        "near_duplicate_count": sum(
            alias["reason"] in {
                "NEAR_VISUAL_DUPLICATE",
                "SAME_PACKAGE_NEAR_DUPLICATE",
            }
            for alias in aliases
        ),
    }


def apply_gaojie_final_visual_overrides(
    pages: list[dict[str, Any]],
    override_path: Path | str,
) -> dict[str, Any]:
    """Apply sparse, digest-bound final visual-review decisions."""

    try:
        overrides = json.loads(Path(override_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("final visual override registry is unreadable") from exc
    if overrides.get("schema_version") != "gaojie-final-visual-overrides.v1":
        raise ValueError("final visual override schema is unsupported")
    if overrides.get("source_page_count") != len(pages):
        raise ValueError("final visual override source page count drifted")
    order_digest = hashlib.sha256(
        ("\n".join(str(page.get("page_id", "")) for page in pages) + "\n").encode()
    ).hexdigest()
    if overrides.get("source_order_sha256") != order_digest:
        raise ValueError("final visual override source order drifted")

    page_ids = [page.get("page_id") for page in pages]
    if any(not isinstance(page_id, str) or not page_id for page_id in page_ids):
        raise ValueError("final visual override source contains invalid page IDs")
    if len(set(page_ids)) != len(page_ids):
        raise ValueError("final visual override source contains duplicate page IDs")
    known_ids = set(page_ids)
    decisions: dict[str, dict[str, Any]] = {}

    deny = overrides.get("deny")
    if not isinstance(deny, list):
        raise ValueError("final visual override deny list is missing")
    for item in deny:
        if not isinstance(item, dict):
            raise ValueError("final visual deny entry is malformed")
        page_id = item.get("page_id")
        severity = item.get("severity")
        reason_code = item.get("reason_code")
        if (
            page_id not in known_ids
            or severity not in {"Blocker", "Important"}
            or not isinstance(reason_code, str)
            or not reason_code
        ):
            raise ValueError("final visual deny entry is invalid or unknown")
        if page_id in decisions:
            raise ValueError("final visual override page is assigned more than once")
        decisions[page_id] = {
            "decision": "deny",
            "pool": "excluded",
            "severity": severity,
            "reason_code": reason_code,
        }

    reference_only = overrides.get("reference_only")
    if not isinstance(reference_only, list):
        raise ValueError("final visual override reference-only list is missing")
    for group in reference_only:
        if not isinstance(group, dict):
            raise ValueError("final visual reference-only group is malformed")
        pool = group.get("pool")
        group_page_ids = group.get("page_ids")
        if (
            not isinstance(pool, str)
            or not pool.startswith("reference-only/")
            or not isinstance(group_page_ids, list)
        ):
            raise ValueError("final visual reference-only group is invalid")
        for page_id in group_page_ids:
            if page_id not in known_ids:
                raise ValueError("final visual reference-only page is unknown")
            if page_id in decisions:
                raise ValueError(
                    "final visual override page is assigned more than once"
                )
            decisions[page_id] = {
                "decision": "reference-only",
                "pool": pool,
                "auto_materialize": False,
                "direct_use": False,
                "requires_content_replacement": True,
            }

    kept_pages: list[dict[str, Any]] = []
    denied_pages: list[dict[str, Any]] = []
    reference_only_count = 0
    for page in pages:
        decision = decisions.get(page["page_id"])
        if decision is None:
            kept_pages.append(page)
            continue
        enriched = dict(page)
        enriched.update(decision)
        enriched["final_visual_override"] = decision["decision"]
        if decision["decision"] == "deny":
            denied_pages.append(enriched)
            continue
        reference_only_count += 1
        kept_pages.append(enriched)
    return {
        "schema_version": overrides["schema_version"],
        "source_order_sha256": order_digest,
        "source_page_count": len(pages),
        "decision_count": len(decisions),
        "deny_count": len(denied_pages),
        "reference_only_count": reference_only_count,
        "pages": kept_pages,
        "denied_pages": denied_pages,
    }


def collect_gaojie_quality_band_candidates(
    private_root: Path | str,
    *,
    minimum_quality: float = 0.65,
    maximum_quality: float = 0.75,
) -> dict[str, Any]:
    """Collect every rendered page in a half-open quality band for review."""

    if not 0 <= minimum_quality < maximum_quality <= 1:
        raise ValueError("quality band must satisfy 0 <= minimum < maximum <= 1")
    root = Path(private_root).resolve()
    index_path = root / "intelligence" / "gaojie" / "asset-index.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("rendered Gaojie asset index is unavailable") from exc
    pages: list[dict[str, Any]] = []
    for package in index.get("packages", []):
        if (
            package.get("status") != "ACCEPTED"
            or package.get("render_status") != "PASS"
        ):
            continue
        for page in package.get("rendered_pages", []):
            quality = float(page.get("quality", -1))
            if not minimum_quality <= quality < maximum_quality:
                continue
            pages.append({
                "page_id": (
                    f"{package['package_sha256']}:{int(page['slide_number']):03d}"
                ),
                "package_sha256": package["package_sha256"],
                "slide_number": int(page["slide_number"]),
                "png_path": page["png_path"],
                "page_role": package["page_role"],
                "category_names": package["category_names"],
                "visual_sha256": page["visual_sha256"],
                "quality": quality,
                "pool": "supplement-review",
            })
    pages.sort(
        key=lambda item: (
            item["page_role"],
            -item["quality"],
            item["package_sha256"],
            item["slide_number"],
        )
    )
    report = {
        "schema_version": "gaojie-supplement-candidates.v1",
        "status": "PASS" if pages else "PARTIAL",
        "minimum_quality_inclusive": minimum_quality,
        "maximum_quality_exclusive": maximum_quality,
        "candidate_page_count": len(pages),
        "pages": pages,
    }
    _atomic_json(
        report,
        root / "intelligence" / "gaojie" / "supplement-candidates.json",
    )
    return report


def certify_gaojie_core(
    private_root: Path | str,
    *,
    maximum_pages: int = 500,
    multi_page_limit: int = 155,
    minimum_render_quality: float = 0.75,
    disposition_path: Path | str | None = None,
    supplement_report_path: Path | str | None = None,
    supplement_disposition_path: Path | str | None = None,
    final_visual_overrides_path: Path | str | None = None,
    near_duplicate_distance: float = 0.03,
) -> dict[str, Any]:
    """Certify a bounded core from rendered accepted package pages."""

    if not 300 <= maximum_pages <= 500:
        raise ValueError("maximum_pages must be between 300 and 500")
    if multi_page_limit < 0:
        raise ValueError("multi_page_limit cannot be negative")
    if not 0 <= minimum_render_quality <= 1:
        raise ValueError("minimum_render_quality must be between zero and one")
    if not 0 <= near_duplicate_distance <= 1:
        raise ValueError("near_duplicate_distance must be between zero and one")
    if (
        supplement_report_path is not None
        or supplement_disposition_path is not None
        or final_visual_overrides_path is not None
    ) and disposition_path is None:
        raise ValueError(
            "supplement or final visual certification requires a primary disposition"
        )
    root = Path(private_root).resolve()
    index_path = root / "intelligence" / "gaojie" / "asset-index.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("rendered Gaojie asset index is unavailable") from exc

    singles: list[dict[str, Any]] = []
    multi_records: dict[str, dict[str, Any]] = {}
    multi_fingerprints: dict[str, PreviewFingerprint] = {}
    for package in index.get("packages", []):
        if (
            package.get("status") != "ACCEPTED"
            or package.get("render_status") != "PASS"
        ):
            continue
        pages = package.get("rendered_pages", [])
        for page in pages:
            if float(page["quality"]) < minimum_render_quality:
                continue
            record = {
                "page_id": (
                    f"{package['package_sha256']}:{int(page['slide_number']):03d}"
                ),
                "package_sha256": package["package_sha256"],
                "slide_number": int(page["slide_number"]),
                "png_path": page["png_path"],
                "page_role": package["page_role"],
                "category_names": package["category_names"],
                "visual_sha256": page["visual_sha256"],
                "quality": page["quality"],
            }
            if len(pages) == 1:
                singles.append(record)
                continue
            png_path = (root / page["png_path"]).resolve()
            if root not in png_path.parents or not png_path.is_file():
                continue
            multi_records[record["page_id"]] = record
            multi_fingerprints[record["page_id"]] = fingerprint_preview(
                png_path.read_bytes()
            )

    available_multi_slots = max(0, maximum_pages - len(singles))
    requested_multi = min(
        multi_page_limit,
        available_multi_slots,
        len(multi_fingerprints),
    )
    selected_multi_ids: list[str] = []
    diversity: dict[str, Any] = {}
    if requested_multi:
        diversity = select_diverse(
            multi_fingerprints,
            limit=requested_multi,
            near_duplicate_distance=0.03,
        )
        selected_multi_ids = list(diversity["selected_item_ids"])
    preliminary = sorted(
        singles + [multi_records[item_id] for item_id in selected_multi_ids],
        key=lambda item: (
            item["page_role"],
            item["package_sha256"],
            item["slide_number"],
        ),
    )
    disposition: dict[str, Any] | None = None
    denied_pages: list[dict[str, Any]] = []
    aliases: list[dict[str, str]] = []
    packages_by_sha = {
        str(package.get("package_sha256")): package
        for package in index.get("packages", [])
        if isinstance(package, dict)
    }

    def enrich_routed(
        source_pages: list[dict[str, Any]],
        source_disposition: dict[str, Any],
    ) -> list[dict[str, Any]]:
        routed_pages: list[dict[str, Any]] = []
        for page in source_pages:
            decision = source_disposition["records"][page["page_id"]]
            enriched = dict(page)
            enriched.update({
                "visual_disposition": decision["decision"],
                "pool": decision["pool"],
            })
            if decision["decision"] == "deny":
                enriched["reason_code"] = decision["reason_code"]
                enriched["severity"] = decision["severity"]
                denied_pages.append(enriched)
                continue
            package = packages_by_sha.get(page["package_sha256"], {})
            structure = package.get("structure", {})
            enriched.update({
                "certification": "certified-private",
                "rights": {
                    "scope": "private-user-authorized",
                    "redistribution": False,
                    "evidence": "authenticated-entitlement",
                },
                "provenance": {
                    "package_sha256": page["package_sha256"],
                    "slide_number": page["slide_number"],
                    "category_names": page["category_names"],
                },
                "structure_evidence": {
                    "structural_sha256": structure.get("structural_sha256"),
                    "editable": structure.get("editable"),
                    "slide_count": structure.get("slide_count"),
                    "master_count": structure.get("master_count"),
                    "layout_count": structure.get("layout_count"),
                },
                "render_evidence": {
                    "status": package.get("render_status"),
                    "quality": page["quality"],
                    "visual_sha256": page["visual_sha256"],
                },
            })
            routed_pages.append(enriched)
        return routed_pages

    supplement: dict[str, Any] | None = None
    supplement_disposition: dict[str, Any] | None = None
    final_visual_overrides: dict[str, Any] | None = None
    if disposition_path is not None:
        disposition = apply_gaojie_visual_disposition(
            preliminary,
            disposition_path,
            source_core_schema="gaojie-certified-core.v1",
        )
        routed = enrich_routed(preliminary, disposition)
        if (supplement_report_path is None) != (supplement_disposition_path is None):
            raise ValueError(
                "supplement report and disposition must be supplied together"
            )
        if supplement_report_path is not None:
            try:
                supplement = json.loads(
                    Path(supplement_report_path).read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(
                    "supplement candidate report is missing or unreadable"
                ) from exc
            if supplement.get("schema_version") != "gaojie-supplement-candidates.v1":
                raise ValueError("supplement candidate schema is unsupported")
            supplement_pages = supplement.get("pages")
            if not isinstance(supplement_pages, list):
                raise ValueError("supplement candidate pages are missing")
            supplement_disposition = apply_gaojie_visual_disposition(
                supplement_pages,
                supplement_disposition_path,
                source_core_schema="gaojie-supplement-candidates.v1",
            )
            routed.extend(
                enrich_routed(supplement_pages, supplement_disposition)
            )
        deduplicated = deduplicate_routed_pages(
            routed,
            private_root=root,
            near_duplicate_distance=near_duplicate_distance,
        )
        certified = deduplicated["canonical_pages"]
        aliases = deduplicated["aliases"]
        if final_visual_overrides_path is not None:
            final_visual_overrides = apply_gaojie_final_visual_overrides(
                certified,
                final_visual_overrides_path,
            )
            certified = final_visual_overrides["pages"]
            denied_pages.extend(final_visual_overrides["denied_pages"])
    else:
        certified = preliminary
        deduplicated = {
            "exact_duplicate_count": 0,
            "near_duplicate_count": 0,
        }
    layout_pages = [
        page for page in certified if page.get("pool") == "complete-layout"
    ]
    support_pages = [
        page for page in certified if page.get("pool") not in {None, "complete-layout"}
    ]
    if len(certified) > maximum_pages:
        raise ValueError("certified pages exceed maximum_pages after supplement")
    reviewed_candidate_count = len(preliminary) + (
        int(supplement.get("candidate_page_count", 0))
        if supplement is not None
        else 0
    )
    target_shortfall = max(0, 300 - len(certified))
    exhaustive_quality_floor = bool(
        final_visual_overrides is not None
        and supplement is not None
        and float(supplement.get("minimum_quality_inclusive", -1)) == 0.65
        and float(supplement.get("maximum_quality_exclusive", -1))
        == minimum_render_quality
    )
    status = (
        "PASS"
        if (
            300 <= len(certified) <= maximum_pages
            or (
                exhaustive_quality_floor
                and len(certified) <= maximum_pages
            )
        )
        else "PARTIAL"
    )
    report = {
        "schema_version": (
            "gaojie-certified-core.v2"
            if disposition_path is not None
            else "gaojie-certified-core.v1"
        ),
        "status": status,
        "source_package_count": index.get("package_count"),
        "accepted_package_count": index.get("accepted_count"),
        "rendered_slide_count": index.get("rendered_slide_count"),
        "single_page_core_count": len(singles),
        "multi_page_candidate_count": len(multi_records),
        "multi_page_selected_count": len(selected_multi_ids),
        "preliminary_page_count": len(preliminary),
        "supplement_page_count": (
            int(supplement.get("candidate_page_count", 0))
            if supplement is not None
            else 0
        ),
        "certified_page_count": len(certified),
        "reviewed_candidate_count": reviewed_candidate_count,
        "target_minimum_page_count": 300,
        "target_shortfall": target_shortfall,
        "exhaustive_quality_floor": exhaustive_quality_floor,
        "layout_page_count": len(layout_pages),
        "support_page_count": len(support_pages),
        "denied_page_count": len(denied_pages),
        "maximum_pages": maximum_pages,
        "minimum_render_quality": minimum_render_quality,
        "near_duplicate_distance": near_duplicate_distance,
        "multi_page_diversity": diversity,
        "visual_disposition": (
            {
                "schema_version": disposition["schema_version"],
                "source_order_sha256": disposition["source_order_sha256"],
                "counts": disposition["counts"],
            }
            if disposition is not None
            else None
        ),
        "supplement_visual_disposition": (
            {
                "schema_version": supplement_disposition["schema_version"],
                "source_order_sha256": supplement_disposition[
                    "source_order_sha256"
                ],
                "counts": supplement_disposition["counts"],
            }
            if supplement_disposition is not None
            else None
        ),
        "final_visual_overrides": (
            {
                "schema_version": final_visual_overrides["schema_version"],
                "source_order_sha256": final_visual_overrides[
                    "source_order_sha256"
                ],
                "source_page_count": final_visual_overrides["source_page_count"],
                "decision_count": final_visual_overrides["decision_count"],
                "deny_count": final_visual_overrides["deny_count"],
                "reference_only_count": final_visual_overrides[
                    "reference_only_count"
                ],
            }
            if final_visual_overrides is not None
            else None
        ),
        "cross_pool_deduplication": {
            "exact_duplicate_count": deduplicated["exact_duplicate_count"],
            "near_duplicate_count": deduplicated["near_duplicate_count"],
            "aliases": aliases,
        },
        "layout_pages": layout_pages,
        "support_pages": support_pages,
        "denied_pages": denied_pages,
        "pages": certified,
    }
    _atomic_json(
        report,
        root / "intelligence" / "gaojie" / "certified-core.json",
    )
    return report
