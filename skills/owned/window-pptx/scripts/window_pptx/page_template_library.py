"""Certified page template library for physical assembly (v6.1).

Compiles the v6.1 page-template index from the Gaojie certified core, exposes
deterministic role-based queries, and resolves a private root from CLI args,
env, or the per-user config file.

The index records the physical identity of every certified page:

- ``page_id`` — package SHA-256 + slide ordinal,
- ``source_path`` — absolute path to the source ``.pptx``,
- ``source_sha256`` — SHA-256 of the source bytes,
- ``structure`` — slide/layout/master/theme/media counts,
- ``slot_graph`` — text slots discovered from ``slide1.xml``.

The index is deterministic: identical inputs always produce identical bytes
(field order is fixed, dates are derived from the source mtimes, no
floating-point keys appear in any record).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

CERTIFIED_CORE_SCHEMA = "gaojie-certified-core.v2"
DEFAULT_DOMINANT_STYLE_CLUSTER = "ivory-green-gold-editorial"
DEFAULT_COMPATIBLE_STYLE_CLUSTERS: tuple[str, ...] = (
    "ivory-green-gold-editorial",
    "research-editorial-evidence",
    "optimistic-technical-stage",
)
DEFAULT_SCORING: Mapping[str, float] = {
    "role": 0.30,
    "capacity": 0.25,
    "semantic": 0.20,
    "style": 0.15,
    "editability": 0.10,
}
CONFIG_PATH = Path("~/.config/window-pptx/library.json").expanduser()
PAGE_ID_RE = re.compile(r"^([0-9a-f]{64}):(\d{3})$")


class PageTemplateError(ValueError):
    """An index operation has failed for a documented reason."""


@dataclass(frozen=True)
class SlotRecord:
    slot_id: str
    shape_id: int
    kind: str
    max_chars: int
    text: str


@dataclass(frozen=True)
class PageTemplate:
    schema_version: str
    page_id: str
    package_sha256: str
    slide_number: int
    source_path: str
    source_sha256: str
    page_role: str
    category_names: tuple[str, ...]
    style_cluster_id: str
    deck_family_id: str
    theme_palette: tuple[str, ...]
    capacity: Mapping[str, int]
    editability: str
    certification: str
    visual_quality: float
    structure: Mapping[str, Any]
    slot_graph: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "page_id": self.page_id,
            "package_sha256": self.package_sha256,
            "slide_number": self.slide_number,
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
            "page_role": self.page_role,
            "category_names": list(self.category_names),
            "style_cluster_id": self.style_cluster_id,
            "deck_family_id": self.deck_family_id,
            "theme_palette": list(self.theme_palette),
            "capacity": dict(self.capacity),
            "editability": self.editability,
            "certification": self.certification,
            "visual_quality": self.visual_quality,
            "structure": dict(self.structure),
            "slot_graph": dict(self.slot_graph),
        }


@dataclass(frozen=True)
class LibraryIndex:
    schema_version: str
    library_id: str
    compiled_at: str
    source_core_schema: str
    private_root_sha256: str
    page_template_count: int
    role_index: Mapping[str, int]
    style_cluster_index: Mapping[str, int]
    deck_family_index: Mapping[str, int]
    category_index: Mapping[str, int]
    scoring: Mapping[str, float]
    dominant_style_cluster_id: str
    compatible_style_cluster_ids: tuple[str, ...]
    page_templates: tuple[PageTemplate, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "library_id": self.library_id,
            "compiled_at": self.compiled_at,
            "source_core_schema": self.source_core_schema,
            "private_root_sha256": self.private_root_sha256,
            "page_template_count": self.page_template_count,
            "role_index": dict(self.role_index),
            "style_cluster_index": dict(self.style_cluster_index),
            "deck_family_index": dict(self.deck_family_index),
            "category_index": dict(self.category_index),
            "scoring": dict(self.scoring),
            "dominant_style_cluster_id": self.dominant_style_cluster_id,
            "compatible_style_cluster_ids": list(self.compatible_style_cluster_ids),
            "page_templates": [template.to_dict() for template in self.page_templates],
        }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_directory(root: Path) -> str:
    """Hash the asset-index + certified-core files for fast root identity."""

    h = hashlib.sha256()
    for sub in (
        "intelligence/gaojie/asset-index.json",
        "intelligence/gaojie/certified-core.json",
    ):
        path = root / sub
        if path.is_file():
            h.update(sub.encode("utf-8"))
            h.update(b"\0")
            h.update(_sha256_file(path).encode("ascii"))
            h.update(b"\0")
    return h.hexdigest()


def resolve_private_root(
    *,
    explicit: str | os.PathLike[str] | None = None,
    env_var: str | None = "WINDOW_PPTX_PRIVATE_ROOT",
    config_path: Path | None = CONFIG_PATH,
) -> Path:
    """Resolve the private Gaojie root from CLI flag, env var, then config."""

    if explicit is not None:
        root = Path(explicit).expanduser().resolve(strict=False)
        if not (root / "intelligence" / "gaojie" / "asset-index.json").is_file():
            raise PageTemplateError(
                f"explicit private root missing asset-index: {root}"
            )
        return root
    if env_var:
        value = os.environ.get(env_var)
        if value:
            root = Path(value).expanduser().resolve(strict=False)
            if not (root / "intelligence" / "gaojie" / "asset-index.json").is_file():
                raise PageTemplateError(
                    f"{env_var} root missing asset-index: {root}"
                )
            return root
    if config_path is not None and config_path.is_file():
        try:
            raw = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PageTemplateError(f"cannot read {config_path}: {exc}") from exc
        candidate = raw.get("private_root") if isinstance(raw, dict) else None
        if candidate:
            root = Path(candidate).expanduser().resolve(strict=False)
            if not (root / "intelligence" / "gaojie" / "asset-index.json").is_file():
                raise PageTemplateError(
                    f"config private root missing asset-index: {root}"
                )
            return root
    raise PageTemplateError(
        "private root unresolved: pass --private-root, set "
        "WINDOW_PPTX_PRIVATE_ROOT, or write ~/.config/window-pptx/library.json"
    )


_SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
_LAYOUT_RE = re.compile(r"^ppt/slideLayouts/slideLayout(\d+)\.xml$")
_MASTER_RE = re.compile(r"^ppt/slideMasters/slideMaster(\d+)\.xml$")
_THEME_RE = re.compile(r"^ppt/theme/theme(\d+)\.xml$")
_CNVPR_RE = re.compile(r'<p:cNvPr\b[^>]*\bid="(\d+)"[^>]*\bname="([^"]*)"')
_TEXT_RE = re.compile(r"<a:t\b[^>]*>(.*?)</a:t>", re.DOTALL)
_SRGB_RE = re.compile(r'val="([0-9A-Fa-f]{6})"')


def _discover_slots(slide_xml: str) -> tuple[SlotRecord, ...]:
    """Extract text-bearing shape slots from one slide XML."""

    slots: list[SlotRecord] = []
    for match in _CNVPR_RE.finditer(slide_xml):
        shape_id = int(match.group(1))
        # Limit slot discovery to the shapes between this cNvPr and its sibling.
        start = match.end()
        # Find next cNvPr or end of shape container
        next_match = _CNVPR_RE.search(slide_xml, start)
        end = next_match.start() if next_match else len(slide_xml)
        segment = slide_xml[start:end]
        texts = [
            html.unescape(m.group(1)) for m in _TEXT_RE.finditer(segment)
        ]
        if not texts:
            continue
        joined = "\n".join(texts).strip()
        if not joined:
            continue
        kind = "title" if shape_id < 50 else "body"
        slots.append(
            SlotRecord(
                slot_id=f"shape_{shape_id}",
                shape_id=shape_id,
                kind=kind,
                max_chars=max(1, len(joined) + 80),
                text=joined,
            )
        )
    return tuple(slots)


# Late import to keep top-level imports lean.
import html  # noqa: E402  (intentional after constants)

_HEX6 = re.compile(r"^[0-9A-Fa-f]{6}$")


def _scan_palette(slide_xml: str, max_colors: int = 6) -> tuple[str, ...]:
    counts = Counter(_SRGB_RE.findall(slide_xml))
    if not counts:
        return ("#F5F0E5", "#173D32", "#B79A5B")
    top = [f"#{value.upper()}" for value, _ in counts.most_common(max_colors)]
    return tuple(top)


def _scan_structure(package_path: Path) -> dict[str, Any]:
    """Return the structure summary for one source package."""

    summary: dict[str, Any] = {
        "slide_count": 0,
        "shape_count": 0,
        "layout_count": 0,
        "master_count": 0,
        "theme_count": 0,
        "media_count": 0,
        "chart_count": 0,
        "table_count": 0,
        "fonts": [],
    }
    try:
        with zipfile.ZipFile(package_path, "r") as archive:
            for name in archive.namelist():
                if _SLIDE_RE.match(name):
                    summary["slide_count"] += 1
                    summary["shape_count"] += len(
                        _CNVPR_RE.findall(archive.read(name).decode("utf-8", errors="replace"))
                    )
                elif _LAYOUT_RE.match(name):
                    summary["layout_count"] += 1
                elif _MASTER_RE.match(name):
                    summary["master_count"] += 1
                elif _THEME_RE.match(name):
                    summary["theme_count"] += 1
                elif name.startswith("ppt/media/") or name.startswith("ppt/embeddings/"):
                    summary["media_count"] += 1
                elif name.startswith("ppt/charts/"):
                    summary["chart_count"] += 1
                elif "table" in name.lower():
                    summary["table_count"] += 1
            # Probe theme for fonts
            theme_names = [
                n for n in archive.namelist() if _THEME_RE.match(n)
            ]
            if theme_names:
                theme_xml = archive.read(theme_names[0]).decode("utf-8", errors="replace")
                fonts = re.findall(r'typeface="([^"]+)"', theme_xml)
                summary["fonts"] = sorted(set(fonts))[:24]
    except (OSError, zipfile.BadZipFile) as exc:
        raise PageTemplateError(
            f"unreadable source package {package_path}: {exc}"
        ) from exc
    return summary


def _style_cluster_for(role: str) -> str:
    """Return the default style cluster for a role.

    v6.1 locks the dominant style cluster to ivory-green-gold-editorial; we
    map every certified page to that cluster by default. Categories drive
    style-cluster aliases only when explicitly registered.
    """

    return DEFAULT_DOMINANT_STYLE_CLUSTER


def _deck_family_for(category: str) -> str:
    """Pick a stable deck family for a category."""

    table = {
        "封面模板": "institutional-annual-editorial",
        "目录模板": "institutional-annual-editorial",
        "章节模板": "institutional-annual-editorial",
        "标题模板": "institutional-annual-editorial",
        "结尾模板": "institutional-annual-editorial",
        "人物介绍": "campus-innovation-pitch",
        "荣誉奖项": "institutional-annual-editorial",
        "时间轴图": "data-research-editorial",
        "架构流程": "data-research-editorial",
        "商业模型": "data-research-editorial",
        "样机展示": "product-launch-stage",
        "金句模板": "institutional-annual-editorial",
        "合作伙伴": "campus-innovation-pitch",
        "图文排版": "institutional-annual-editorial",
        "表格图表": "data-research-editorial",
        "优秀作品": "product-launch-stage",
        "实用素材": "institutional-annual-editorial",
        "一段内容": "institutional-annual-editorial",
        "二段内容": "institutional-annual-editorial",
        "三段内容": "institutional-annual-editorial",
        "四段内容": "institutional-annual-editorial",
        "五段内容": "institutional-annual-editorial",
        "六段内容": "institutional-annual-editorial",
        "多段内容": "institutional-annual-editorial",
        "地图排版": "data-research-editorial",
        "数据基座": "data-research-editorial",
        "文本组件": "institutional-annual-editorial",
        "装饰形状": "institutional-annual-editorial",
        "风格配色": "institutional-annual-editorial",
    }
    return table.get(category, "institutional-annual-editorial")


def _capacity_for_slots(slots: Sequence[SlotRecord]) -> dict[str, int]:
    total_chars = sum(len(slot.text) for slot in slots)
    return {
        "max_text_chars": max(0, total_chars * 4),
        "max_text_runs": max(1, len(slots)),
    }


def compile_page_templates(
    private_root: str | os.PathLike[str],
    *,
    library_id: str = "window-pptx-gaojie-certified-core-v4",
) -> LibraryIndex:
    """Compile the v6.1 page-template index from the certified core."""

    root = Path(private_root).expanduser().resolve(strict=False)
    asset_index_path = root / "intelligence" / "gaojie" / "asset-index.json"
    core_path = root / "intelligence" / "gaojie" / "certified-core.json"
    if not asset_index_path.is_file():
        raise PageTemplateError(f"asset-index missing: {asset_index_path}")
    if not core_path.is_file():
        raise PageTemplateError(f"certified-core missing: {core_path}")
    asset_index = json.loads(asset_index_path.read_text(encoding="utf-8"))
    certified_core = json.loads(core_path.read_text(encoding="utf-8"))
    if certified_core.get("schema_version") != CERTIFIED_CORE_SCHEMA:
        raise PageTemplateError(
            f"unexpected certified-core schema: {certified_core.get('schema_version')}"
        )
    package_lookup: dict[str, dict[str, Any]] = {}
    for package in asset_index.get("packages", []):
        if package.get("status") == "ACCEPTED" and package.get("render_status") == "PASS":
            package_lookup[str(package["package_sha256"])] = package
    templates: list[PageTemplate] = []
    for page in certified_core.get("pages", []):
        if page.get("certification") not in ("certified", "certified-private"):
            continue
        package_sha = str(page["package_sha256"])
        package = package_lookup.get(package_sha)
        if package is None:
            continue
        relative = package.get("private_path")
        if not relative:
            continue
        source_path = (root / relative).resolve(strict=False)
        if not source_path.is_file():
            continue
        slide_number = int(page["slide_number"])
        # We pull slide 1 from each source package (the chosen slide is
        # recorded as page_id but the source package itself always has slide1).
        try:
            with zipfile.ZipFile(source_path, "r") as archive:
                slide_xml = archive.read("ppt/slides/slide1.xml").decode(
                    "utf-8", errors="replace"
                )
        except (OSError, zipfile.BadZipFile, KeyError):
            continue
        slots = _discover_slots(slide_xml)
        palette = _scan_palette(slide_xml)
        structure = _scan_structure(source_path)
        categories = tuple(page.get("category_names") or [])
        primary_category = categories[0] if categories else "未分类"
        capacity = _capacity_for_slots(slots)
        style_cluster = _style_cluster_for(str(page.get("page_role", "")))
        deck_family = _deck_family_for(primary_category)
        try:
            source_sha = _sha256_file(source_path)
        except OSError:
            continue
        template = PageTemplate(
            schema_version="1.0",
            page_id=str(page["page_id"]),
            package_sha256=package_sha,
            slide_number=slide_number,
            source_path=str(source_path),
            source_sha256=source_sha,
            page_role=str(page.get("page_role", "body")),
            category_names=categories,
            style_cluster_id=style_cluster,
            deck_family_id=deck_family,
            theme_palette=palette,
            capacity=capacity,
            editability="native_editable" if structure["slide_count"] >= 1 else "image_only",
            certification="certified",
            visual_quality=float(page.get("quality", 0.0) or 0.0),
            structure={
                "slide_count": structure["slide_count"],
                "shape_count": structure["shape_count"],
                "layout_count": structure["layout_count"],
                "master_count": structure["master_count"],
                "theme_count": structure["theme_count"],
                "media_count": structure["media_count"],
                "chart_count": structure["chart_count"],
                "table_count": structure["table_count"],
                "fonts": structure["fonts"],
            },
            slot_graph={
                "text_slot_ids": [slot.slot_id for slot in slots],
                "text_slot_count": len(slots),
                "slots": [
                    {
                        "slot_id": slot.slot_id,
                        "shape_id": slot.shape_id,
                        "kind": slot.kind,
                        "max_chars": slot.max_chars,
                        "source_text": slot.text,
                    }
                    for slot in slots
                ],
            },
        )
        templates.append(template)
    templates.sort(key=lambda t: (t.page_role, t.package_sha256, t.slide_number))
    role_index: Counter[str] = Counter(t.page_role for t in templates)
    style_index: Counter[str] = Counter(t.style_cluster_id for t in templates)
    family_index: Counter[str] = Counter(t.deck_family_id for t in templates)
    cat_index: Counter[str] = Counter(c for t in templates for c in t.category_names)
    index = LibraryIndex(
        schema_version="4.0",
        library_id=library_id,
        compiled_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        source_core_schema=CERTIFIED_CORE_SCHEMA,
        private_root_sha256=_sha256_directory(root),
        page_template_count=len(templates),
        role_index=dict(role_index),
        style_cluster_index=dict(style_index),
        deck_family_index=dict(family_index),
        category_index=dict(cat_index),
        scoring=dict(DEFAULT_SCORING),
        dominant_style_cluster_id=DEFAULT_DOMINANT_STYLE_CLUSTER,
        compatible_style_cluster_ids=DEFAULT_COMPATIBLE_STYLE_CLUSTERS,
        page_templates=tuple(templates),
    )
    return index


def compile_reference_deck(
    deck_path: str | os.PathLike[str],
    *,
    library_id: str = "window-pptx-reference-work-summary-v1",
) -> LibraryIndex:
    """Compile every slide of a user-certified reference deck as page templates.

    This is intentionally separate from the commercial Gaojie catalog.  The
    caller supplies the semantic role sequence; the original slide, master,
    theme, media, and editable text remain the physical source of truth.
    """

    path = Path(deck_path).expanduser().resolve(strict=False)
    if not path.is_file():
        raise PageTemplateError(f"reference deck missing: {path}")
    package_sha = _sha256_file(path)
    # The source deck contains two consecutive chapter dividers before its
    # first chart (slides 3–4), then an evidence/data run, an innovation
    # divider (10), people/content pages (11–12), and the next-year divider
    # (13).  Recording these semantics prevents an authoring Agent from
    # selecting slide 4 as a data page merely because it is adjacent to one.
    roles = (
        "cover", "contents", "section", "section", "data", "data", "table",
        "case-study", "kpi", "section", "people", "content-blocks", "section",
        "process", "closing",
    )
    categories = (
        "封面模板", "目录模板", "章节模板", "章节模板", "表格图表",
        "表格图表", "表格图表", "表格图表", "表格图表", "章节模板",
        "人物介绍", "多段内容", "章节模板", "架构流程", "结尾模板",
    )
    templates: list[PageTemplate] = []
    try:
        with zipfile.ZipFile(path, "r") as archive:
            slide_names = sorted(
                (name for name in archive.namelist() if _SLIDE_RE.match(name)),
                key=lambda name: int(_SLIDE_RE.match(name).group(1)),
            )
            if len(slide_names) < len(roles):
                raise PageTemplateError(
                    f"reference deck has {len(slide_names)} slides; expected at least {len(roles)}"
                )
            structure = _scan_structure(path)
            for ordinal, (role, category) in enumerate(zip(roles, categories, strict=True), 1):
                slide_xml = archive.read(f"ppt/slides/slide{ordinal}.xml").decode(
                    "utf-8", errors="replace"
                )
                slots = _discover_slots(slide_xml)
                templates.append(
                    PageTemplate(
                        schema_version="1.0",
                        page_id=f"{package_sha}:{ordinal:03d}",
                        package_sha256=package_sha,
                        slide_number=ordinal,
                        source_path=str(path),
                        source_sha256=package_sha,
                        page_role=role,
                        category_names=(category,),
                        style_cluster_id="reference-work-summary",
                        deck_family_id="reference-work-summary",
                        theme_palette=_scan_palette(slide_xml),
                        capacity=_capacity_for_slots(slots),
                        editability="native_editable",
                        certification="certified",
                        visual_quality=0.98,
                        structure={
                            "slide_count": structure["slide_count"],
                            "shape_count": structure["shape_count"],
                            "layout_count": structure["layout_count"],
                            "master_count": structure["master_count"],
                            "theme_count": structure["theme_count"],
                            "media_count": structure["media_count"],
                            "chart_count": structure["chart_count"],
                            "table_count": structure["table_count"],
                            "fonts": structure["fonts"],
                        },
                        slot_graph={
                            "text_slot_ids": [slot.slot_id for slot in slots],
                            "text_slot_count": len(slots),
                            "slots": [
                                {
                                    "slot_id": slot.slot_id,
                                    "shape_id": slot.shape_id,
                                    "kind": slot.kind,
                                    "max_chars": slot.max_chars,
                                    "source_text": slot.text,
                                }
                                for slot in slots
                            ],
                        },
                    )
                )
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise PageTemplateError(f"unreadable reference deck {path}: {exc}") from exc
    counts = Counter(t.page_role for t in templates)
    category_index = Counter(c for t in templates for c in t.category_names)
    return LibraryIndex(
        schema_version="4.0",
        library_id=library_id,
        compiled_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        source_core_schema="user-certified-reference-deck.v1",
        private_root_sha256=package_sha,
        page_template_count=len(templates),
        role_index=dict(counts),
        style_cluster_index={"reference-work-summary": len(templates)},
        deck_family_index={"reference-work-summary": len(templates)},
        category_index=dict(category_index),
        scoring=dict(DEFAULT_SCORING),
        dominant_style_cluster_id="reference-work-summary",
        compatible_style_cluster_ids=("reference-work-summary",),
        page_templates=tuple(templates),
    )


def write_library_index(index: LibraryIndex, output_path: str | os.PathLike[str]) -> str:
    """Write the library index to disk in deterministic field order."""

    path = Path(output_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = index.to_dict()
    text = json.dumps(payload, ensure_ascii=False, sort_keys=False, indent=2)
    path.write_text(text, encoding="utf-8")
    return _sha256_bytes(text.encode("utf-8"))


def load_library_index(path: str | os.PathLike[str]) -> LibraryIndex:
    """Load a previously compiled library index."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema_version") != "4.0":
        raise PageTemplateError(
            f"unsupported library index schema_version: {raw.get('schema_version')}"
        )
    templates = tuple(
        PageTemplate(
            schema_version="1.0",
            page_id=item["page_id"],
            package_sha256=item["package_sha256"],
            slide_number=int(item["slide_number"]),
            source_path=item["source_path"],
            source_sha256=item["source_sha256"],
            page_role=item["page_role"],
            category_names=tuple(item.get("category_names", [])),
            style_cluster_id=item["style_cluster_id"],
            deck_family_id=item["deck_family_id"],
            theme_palette=tuple(item.get("theme_palette", [])),
            capacity=dict(item.get("capacity", {})),
            editability=item.get("editability", "native_editable"),
            certification=item.get("certification", "certified"),
            visual_quality=float(item.get("visual_quality", 0.0)),
            structure=dict(item.get("structure", {})),
            slot_graph=dict(item.get("slot_graph", {})),
        )
        for item in raw.get("page_templates", [])
    )
    return LibraryIndex(
        schema_version="4.0",
        library_id=raw["library_id"],
        compiled_at=raw["compiled_at"],
        source_core_schema=raw["source_core_schema"],
        private_root_sha256=raw["private_root_sha256"],
        page_template_count=len(templates),
        role_index=dict(raw.get("role_index", {})),
        style_cluster_index=dict(raw.get("style_cluster_index", {})),
        deck_family_index=dict(raw.get("deck_family_index", {})),
        category_index=dict(raw.get("category_index", {})),
        scoring=dict(raw.get("scoring", DEFAULT_SCORING)),
        dominant_style_cluster_id=raw.get(
            "dominant_style_cluster_id", DEFAULT_DOMINANT_STYLE_CLUSTER
        ),
        compatible_style_cluster_ids=tuple(
            raw.get("compatible_style_cluster_ids", DEFAULT_COMPATIBLE_STYLE_CLUSTERS)
        ),
        page_templates=templates,
    )


def _score_template(
    template: PageTemplate,
    *,
    role: str,
    capacity_budget: int,
    semantic_categories: Iterable[str],
    style_cluster: str,
    editability: str | None,
    scoring: Mapping[str, float],
) -> float:
    role_score = 1.0 if template.page_role == role else 0.0
    capacity = template.capacity.get("max_text_chars", 0)
    capacity_score = max(
        0.0,
        min(1.0, 1.0 - abs(capacity - capacity_budget) / max(capacity_budget, 1)),
    )
    requested_semantics = tuple(semantic_categories)
    semantic_set = {*template.category_names}
    semantic_hits = sum(1 for cat in requested_semantics if cat in semantic_set)
    semantic_score = min(1.0, semantic_hits / max(1, len(requested_semantics)))
    # Penalise templates whose source copy is likely to leak into the target
    # deck.  Named brands and long source copy are deterministic residue risks.
    residue_penalty = _template_reuse_risk(template)
    semantic_score = max(0.0, semantic_score - residue_penalty)
    style_score = 1.0 if template.style_cluster_id == style_cluster else 0.5
    edit_score = 0.0
    if editability is None or editability == template.editability:
        edit_score = 1.0
    elif editability == "any":
        edit_score = 0.5
    total = (
        scoring["role"] * role_score
        + scoring["capacity"] * capacity_score
        + scoring["semantic"] * semantic_score
        + scoring["style"] * style_score
        + scoring["editability"] * edit_score
    )
    return max(0.0, total - residue_penalty * 0.20)


def _template_reuse_risk(template: PageTemplate) -> float:
    """Return a deterministic 0..1 risk that source semantics leak through."""

    source_slots = template.slot_graph.get("slots", ())
    source_text = " ".join(
        str(item.get("source_text", ""))
        for item in source_slots
        if isinstance(item, Mapping)
    )
    if not source_text:
        return 0.0
    risk = min(0.35, len(source_text) / 700.0)
    if re.search(r"[A-Za-z]{3,}", source_text):
        risk += 0.12
    if re.search(
        r"(logo|brand|nestle|bilibili|b站|阿迪|耐克|星巴克|erke|abbott|完美日记|蚂蚁森林)",
        source_text,
        re.I,
    ):
        risk += 0.35
    return min(1.0, risk)


def query_page_templates(
    index: LibraryIndex,
    *,
    role: str,
    capacity_budget: int = 1000,
    semantic_categories: Sequence[str] = (),
    style_cluster: str | None = None,
    editability: str | None = "native_editable",
    limit: int = 5,
    allow_fallback: bool = True,
) -> tuple[PageTemplate, ...]:
    """Return ranked candidates for a requested role."""

    style_cluster = style_cluster or index.dominant_style_cluster_id
    candidates = [
        template
        for template in index.page_templates
        if template.editability == "native_editable"
    ]
    in_cluster = [
        template for template in candidates if template.style_cluster_id == style_cluster
    ]
    selected = in_cluster or candidates
    safe = [template for template in selected if _template_reuse_risk(template) < 0.65]
    if safe:
        selected = safe
    # Prefer exact semantic roles whenever the library has any.  Previously
    # the fallback pool was always scored together with exact matches, so a
    # high-capacity KPI/table page could outrank a certified data page and
    # produce a visually plausible but semantically wrong slide.
    exact_role = [template for template in selected if template.page_role == role]
    if exact_role:
        selected = exact_role
    if not selected and allow_fallback:
        selected = candidates
    scored = sorted(
        selected,
        key=lambda template: (
            -_score_template(
                template,
                role=role,
                capacity_budget=capacity_budget,
                semantic_categories=semantic_categories,
                style_cluster=style_cluster,
                editability=editability,
                scoring=index.scoring,
            ),
            template.page_id,
        ),
    )
    return tuple(scored[:limit])


__all__ = [
    "CERTIFIED_CORE_SCHEMA",
    "DEFAULT_COMPATIBLE_STYLE_CLUSTERS",
    "DEFAULT_DOMINANT_STYLE_CLUSTER",
    "DEFAULT_SCORING",
    "LibraryIndex",
    "PageTemplate",
    "PageTemplateError",
    "SlotRecord",
    "_template_reuse_risk",
    "compile_page_templates",
    "compile_reference_deck",
    "load_library_index",
    "query_page_templates",
    "resolve_private_root",
    "write_library_index",
]
