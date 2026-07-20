#!/usr/bin/env python3
"""Real Windows PowerPoint acceptance for window-pptx Phase 22.

This script is intentionally self-contained and writes only beneath a UUID
directory in Windows TEMP.  Its only stdout output is one JSON document.
"""

from __future__ import annotations

import contextlib
import csv
import gc
import hashlib
import io
import json
import locale
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Callable

sys.dont_write_bytecode = True

import win32com.client  # type: ignore
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "skills" / "owned" / "window-pptx" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import window_pptx_automation as automation  # noqa: E402
from window_pptx.com_session import dispatch_powerpoint, macro_security  # noqa: E402
from window_pptx.errors import OutputPolicyError  # noqa: E402
from window_pptx.models import OutputPolicy  # noqa: E402
from window_pptx.transaction import (  # noqa: E402
    PartialSaveError,
    TransactionError,
    save_candidate,
    sha256_file,
    validate_ooxml_package,
)


MSO_FALSE = 0
MSO_TRUE = -1
MSO_TEXT_ORIENTATION_HORIZONTAL = 1
PP_LAYOUT_BLANK = 12
PP_SAVE_PPTX = 24
PP_SAVE_PPTM = 25


class BlockedCase(RuntimeError):
    """The host could not exercise a required acceptance condition."""


class RecordingClient:
    def __init__(self, active_app: Any | None = None) -> None:
        self.active_app = active_app
        self.created_app: Any | None = None
        self.dispatch_ex_calls = 0
        self.active_calls = 0
        self.dynamic = win32com.client.dynamic

    def DispatchEx(self, prog_id: str) -> Any:
        self.dispatch_ex_calls += 1
        self.created_app = win32com.client.DispatchEx(prog_id)
        return self.created_app

    def GetActiveObject(self, prog_id: str) -> Any:
        self.active_calls += 1
        if self.active_app is None:
            return win32com.client.GetActiveObject(prog_id)
        return self.active_app


def trace(message: str) -> None:
    print(f"window-pptx-uat: {message}", file=sys.stderr, flush=True)


def app_is_alive(app: Any) -> bool:
    try:
        str(app.Version)
    except Exception:
        return False
    return True


def digest(path: Path) -> str:
    return sha256_file(path)


def snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)).replace("\\", "/"): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def wait_app_closed(app: Any, seconds: float = 8.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not app_is_alive(app):
            return True
        time.sleep(0.1)
    return not app_is_alive(app)


def powerpoint_pids() -> set[int]:
    completed = subprocess.run(
        [
            "tasklist.exe",
            "/FI",
            "IMAGENAME eq POWERPNT.EXE",
            "/FO",
            "CSV",
            "/NH",
        ],
        capture_output=True,
        text=True,
        encoding=locale.getpreferredencoding(False),
        errors="replace",
        check=False,
    )
    pids: set[int] = set()
    for row in csv.reader(completed.stdout.splitlines()):
        if len(row) < 2 or row[0].upper() != "POWERPNT.EXE":
            continue
        try:
            pids.add(int(row[1]))
        except ValueError:
            continue
    return pids


def wait_new_powerpoint_processes_closed(
    baseline: set[int], seconds: float = 30.0
) -> set[int]:
    deadline = time.monotonic() + seconds
    residue = powerpoint_pids() - baseline
    while residue and time.monotonic() < deadline:
        time.sleep(0.25)
        residue = powerpoint_pids() - baseline
    return residue


def safe_close(presentation: Any | None) -> None:
    if presentation is None:
        return
    try:
        presentation.Saved = MSO_TRUE
    except Exception:
        pass
    try:
        presentation.Close()
    except Exception:
        pass


def safe_quit(app: Any | None) -> None:
    if app is None:
        return
    try:
        app.Quit()
    except Exception:
        pass
    closed = wait_app_closed(app, seconds=30.0)
    gc.collect()
    if not closed:
        raise RuntimeError("UAT-owned PowerPoint application did not exit within 30 seconds")


def new_app() -> Any:
    app = win32com.client.DispatchEx("PowerPoint.Application")
    try:
        app.Visible = MSO_FALSE
    except Exception:
        pass
    try:
        app.DisplayAlerts = 0
    except Exception:
        pass
    return app


def save_fixture(
    app: Any,
    path: Path,
    sentinel: str,
    *,
    width: float = 960.0,
    height: float = 540.0,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    presentation = None
    try:
        presentation = app.Presentations.Add(MSO_FALSE)
        presentation.PageSetup.SlideWidth = width
        presentation.PageSetup.SlideHeight = height
        slide = presentation.Slides.Add(1, PP_LAYOUT_BLANK)
        shape = slide.Shapes.AddTextbox(
            MSO_TEXT_ORIENTATION_HORIZONTAL,
            48,
            48,
            max(200.0, width - 96.0),
            80,
        )
        shape.TextFrame.TextRange.Text = sentinel
        shape.TextFrame.TextRange.Font.Size = 24
        file_format = PP_SAVE_PPTM if path.suffix.lower() == ".pptm" else PP_SAVE_PPTX
        presentation.SaveAs(str(path), file_format)
    finally:
        safe_close(presentation)


def open_presentation(app: Any, path: Path, read_only: bool = True) -> Any:
    with macro_security(app):
        return app.Presentations.Open(
            str(path),
            MSO_TRUE if read_only else MSO_FALSE,
            MSO_FALSE,
            MSO_FALSE,
        )


def text_shapes(presentation: Any) -> list[Any]:
    rows: list[Any] = []
    for slide_index in range(1, int(presentation.Slides.Count) + 1):
        slide = presentation.Slides(slide_index)
        for shape_index in range(1, int(slide.Shapes.Count) + 1):
            shape = slide.Shapes(shape_index)
            try:
                if bool(shape.HasTextFrame) and bool(shape.TextFrame.HasText):
                    rows.append(shape)
            except Exception:
                continue
    return rows


def presentation_text(presentation: Any) -> list[str]:
    return [str(shape.TextFrame.TextRange.Text) for shape in text_shapes(presentation)]


def capture_main(argv: list[str], *, client: Any | None = None) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = automation.main(argv, com_client=client)
    return code, stdout.getvalue(), stderr.getvalue()


def case_preflight(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    app = None
    try:
        app = new_app()
        environment.update(
            {
                "platform": platform.platform(),
                "python": sys.version.splitlines()[0],
                "python_executable": Path(sys.executable).name,
                "powerpoint_version": str(app.Version),
                "powerpoint_build": str(getattr(app, "Build", "unavailable")),
                "pillow": Image.__version__ if hasattr(Image, "__version__") else "available",
                "pywin32": "available",
            }
        )
        assert platform.system() == "Windows"
        assert app_is_alive(app)
        return {"powerpoint_registered": True, "automation_observed": True}
    finally:
        safe_quit(app)


def case_dry_run(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    project = root / "dry run 项目"
    project.mkdir(parents=True)
    marker = project / "marker.txt"
    marker.write_text("unchanged", encoding="utf-8")
    before = snapshot(project)
    calls: list[str] = []
    originals: dict[str, Any] = {}

    def forbidden(name: str) -> Callable[..., Any]:
        def fail(*_args: Any, **_kwargs: Any) -> Any:
            calls.append(name)
            raise AssertionError(f"dry-run reached {name}")

        return fail

    names = (
        "init_project_workspace",
        "pixabay_search",
        "download_image",
        "iconify_search",
        "download_icon",
        "require_windows",
        "dispatch_powerpoint",
        "import_win32com",
        "ensure_ascii_temp_copy",
        "save_outputs",
    )
    try:
        for name in names:
            if hasattr(automation, name):
                originals[name] = getattr(automation, name)
                setattr(automation, name, forbidden(name))
        code, stdout, stderr = capture_main(
            [
                "--project-dir",
                str(project),
                "--dry-run",
                "--json",
                "--init-project",
                "--search-images",
                "window",
                "--search-icons",
                "window",
                "--list-addins",
                "--probe-plugin-apis",
                "--make-ascii-temp-copy",
            ]
        )
    finally:
        for name, value in originals.items():
            setattr(automation, name, value)
    payload = json.loads(stdout)
    assert code == 0 and not calls and snapshot(project) == before
    assert set(payload) == {"schema_version", "mode", "would_run", "would_write", "warnings"}
    return {"zero_side_effects": True, "stderr_empty": stderr == ""}


def case_owned_cleanup(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    client = RecordingClient()
    handle = dispatch_powerpoint(False, client)
    assert handle.owned and client.dispatch_ex_calls == 1
    assert client.created_app is not None
    handle.quit()
    assert wait_app_closed(client.created_app)
    return {"dispatch_ex_calls": 1, "owned_application_closed": True}


def case_attached_preservation(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    project = root / "attached session"
    project.mkdir(parents=True)
    app = new_app()
    keeper = app.Presentations.Add(MSO_FALSE)
    unrelated = None
    try:
        unrelated = app.Presentations.Add(MSO_FALSE)
        before_count = int(app.Presentations.Count)
        client = RecordingClient(active_app=app)
        handle = dispatch_powerpoint(True, client)
        assert not handle.owned
        handle.quit()
        assert client.active_calls == 1 and client.dispatch_ex_calls == 0
        assert app_is_alive(app)
        assert int(app.Presentations.Count) == before_count
        return {"attached_window_preserved": True, "unrelated_presentations": before_count}
    finally:
        safe_close(unrelated)
        safe_close(keeper)
        safe_quit(app)


def case_macro_security(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    app = new_app()
    try:
        app.AutomationSecurity = 1
        with macro_security(app):
            assert int(app.AutomationSecurity) == 3
        assert int(app.AutomationSecurity) == 1
        try:
            with macro_security(app):
                assert int(app.AutomationSecurity) == 3
                raise RuntimeError("injected open failure")
        except RuntimeError as exc:
            assert "injected open failure" in str(exc)
            pass
        else:
            raise AssertionError("injected macro-security failure did not propagate")
        assert int(app.AutomationSecurity) == 1
        return {
            "forced_value": 3,
            "restored_value": 1,
            "failure_restored": True,
            "failure_mode": "injected inside real PowerPoint security context",
        }
    finally:
        safe_quit(app)


def case_terminal_addins(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    project = root / "terminal registry inspection"
    project.mkdir(parents=True)
    before_files = snapshot(root)
    code, stdout, _stderr = capture_main(
        [
            "--project-dir",
            str(project),
            "--list-addins",
            "--probe-plugin-apis",
            "--json",
        ]
    )
    payload = json.loads(stdout)
    assert code == 0 and snapshot(root) == before_files
    addins = payload["addins"]
    probe = payload["plugin_api_probe"]
    assert addins["mode"] == "registry_only"
    assert probe["mode"] == "registry_only"
    registered_addins = addins["com_addins"]
    addin_facts = {
        "com_addin_record_count": len(registered_addins),
        "unique_com_addin_progids": len(
            {str(row.get("prog_id", "")).lower() for row in registered_addins}
        ),
        "registry_views": sorted(
            {str(row.get("registry_view", "default")) for row in registered_addins}
        ),
        "powerpoint_addin_count": len(addins["powerpoint_addins"]),
        "requested_progids": probe.get("probed_progids", []),
        "office_addin_key_present": {
            progid: any(
                str(row.get("prog_id", "")).lower() == progid.lower()
                for row in registered_addins
            )
            for progid in probe.get("probed_progids", [])
        },
        "clsid_available": {
            key: bool(value.get("clsid"))
            for key, value in probe.get("registry", {}).items()
        },
    }
    environment["addin_facts"] = addin_facts
    return {"presentation_count_unchanged": True, "filesystem_unchanged": True}


def transaction_case(root: Path, suffix: str) -> dict[str, Any]:
    case_dir = root / f"transaction {suffix[1:]} 中文"
    case_dir.mkdir(parents=True)
    source = case_dir / f"源 文件{suffix}"
    output = case_dir / f"交付 文件{suffix}"
    edited = case_dir / f"可编辑 复验{suffix}"
    sentinel = f"EDITABLE-{suffix}-{uuid.uuid4().hex}"
    changed = sentinel + "-CHANGED"
    app = new_app()
    keeper = app.Presentations.Add(MSO_FALSE)
    presentation = None
    check = None
    editable = None
    recheck = None
    target = None
    stage = "create-source"
    try:
        save_fixture(app, source, sentinel)
        before_hash = digest(source)
        stage = "open-source"
        presentation = open_presentation(app, source, read_only=True)
        stage = "transactional-save"
        result = save_candidate(
            presentation,
            app,
            OutputPolicy(source, output),
        )
        safe_close(presentation)
        presentation = None
        assert result.promoted and result.source_hash_before == before_hash
        assert result.source_hash_after == before_hash and digest(source) == before_hash
        validate_ooxml_package(output)
        safe_close(keeper)
        keeper = None
        safe_quit(app)
        app = new_app()
        keeper = app.Presentations.Add(MSO_FALSE)
        stage = "open-output-editable"
        editable = open_presentation(app, output, read_only=False)
        texts = presentation_text(editable)
        assert sentinel in texts and text_shapes(editable)
        target = next(shape for shape in text_shapes(editable) if str(shape.TextFrame.TextRange.Text) == sentinel)
        target.TextFrame.TextRange.Text = changed
        stage = "save-edited-copy"
        editable.SaveCopyAs(str(edited))
        target = None
        gc.collect()
        safe_close(editable)
        editable = None
        stage = "reopen-edited-copy"
        recheck = open_presentation(app, edited, read_only=True)
        assert changed in presentation_text(recheck)
        assert digest(source) == before_hash
        return {
            "suffix": suffix,
            "source_sha256": before_hash,
            "source_unchanged": True,
            "editable_text_roundtrip": True,
            "validation_steps": list(result.validation_steps),
        }
    except Exception as exc:
        raise RuntimeError(f"{stage}: {type(exc).__name__}: {exc}") from exc
    finally:
        target = None
        gc.collect()
        safe_close(recheck)
        safe_close(editable)
        safe_close(check)
        safe_close(presentation)
        safe_close(keeper)
        safe_quit(app)


def case_pptx(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    return transaction_case(root, ".pptx")


def case_pptm(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    return transaction_case(root, ".pptm")


def case_ratio_exports(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    case_dir = root / "ratio exports"
    case_dir.mkdir(parents=True)
    ratios = {
        "16x9": (960.0, 540.0, (1600, 900)),
        "4x3": (720.0, 540.0, (1600, 1200)),
        "portrait": (540.0, 960.0, (900, 1600)),
    }
    app = new_app()
    keeper = app.Presentations.Add(MSO_FALSE)
    observed: dict[str, list[int]] = {}
    try:
        for name, (width, height, expected) in ratios.items():
            presentation = None
            try:
                presentation = app.Presentations.Add(MSO_FALSE)
                presentation.PageSetup.SlideWidth = width
                presentation.PageSetup.SlideHeight = height
                slide = presentation.Slides.Add(1, PP_LAYOUT_BLANK)
                shape = slide.Shapes.AddTextbox(
                    MSO_TEXT_ORIENTATION_HORIZONTAL, 20, 20, width - 40, 50
                )
                shape.TextFrame.TextRange.Text = name
                export_dir = case_dir / name
                result = automation.export_slides_to_png(presentation, [1], export_dir)
                image_path = Path(result["files"][0])
                with Image.open(image_path) as exported:
                    actual = exported.size
                assert abs(actual[0] - expected[0]) <= 1
                assert abs(actual[1] - expected[1]) <= 1
                observed[name] = [actual[0], actual[1]]
            finally:
                safe_close(presentation)
        return {"dimensions": observed}
    finally:
        safe_close(keeper)
        safe_quit(app)


def run_main_expect_error(argv: list[str], client: RecordingClient) -> Exception:
    try:
        capture_main(argv, client=client)
    except Exception as exc:
        return exc
    raise AssertionError("unsafe request unexpectedly succeeded")


def case_guard_failures(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    case_dir = root / "guard failures 中文"
    case_dir.mkdir(parents=True)
    creator = new_app()
    source = case_dir / "source.pptx"
    try:
        save_fixture(creator, source, "GUARD-SOURCE")
    finally:
        safe_quit(creator)
    source_hash = digest(source)
    project = case_dir / "project"
    project.mkdir()

    invalid_client = RecordingClient()
    invalid = case_dir / "bad.pdf"
    error = run_main_expect_error(
        [
            "--project-dir",
            str(project),
            "--template",
            str(source),
            "--output",
            str(invalid),
            "--make-ascii-temp-copy",
        ],
        invalid_client,
    )
    assert isinstance(error, OutputPolicyError)
    staging = project / ".window-pptx" / "temp" / "deck_temp_ascii.pptx"
    assert not staging.exists() and digest(source) == source_hash

    staging.parent.mkdir(parents=True)
    staging.write_bytes(b"STAGING-SENTINEL")
    staging_client = RecordingClient()
    error = run_main_expect_error(
        [
            "--project-dir",
            str(project),
            "--template",
            str(source),
            "--output",
            str(staging),
            "--make-ascii-temp-copy",
        ],
        staging_client,
    )
    assert isinstance(error, OutputPolicyError)
    assert staging.read_bytes() == b"STAGING-SENTINEL"

    same_client = RecordingClient()
    error = run_main_expect_error(
        [
            "--project-dir",
            str(project),
            "--template",
            str(source),
            "--output",
            str(source),
            "--make-ascii-temp-copy",
            "--allow-overwrite",
        ],
        same_client,
    )
    assert isinstance(error, OutputPolicyError)
    assert digest(source) == source_hash
    assert invalid_client.dispatch_ex_calls == 0
    assert staging_client.dispatch_ex_calls == 0
    assert same_client.dispatch_ex_calls == 0
    return {
        "invalid_extension_zero_write": True,
        "staging_sentinel_preserved": True,
        "same_path_rejected": True,
        "source_sha256": source_hash,
    }


def prepare_real_transaction(root: Path, name: str) -> tuple[Any, Any, Path, str]:
    case_dir = root / name
    case_dir.mkdir(parents=True)
    source = case_dir / "source.pptx"
    app = new_app()
    save_fixture(app, source, name)
    source_hash = digest(source)
    presentation = open_presentation(app, source, read_only=True)
    return app, presentation, source, source_hash


def case_promotion_failure(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    app, presentation, source, source_hash = prepare_real_transaction(root, "promotion failure")
    output = source.parent / "final.pptx"
    output.write_bytes(b"EXISTING-OUTPUT")
    existing = output.read_bytes()

    def fail_replace(_source: str | Path, _target: str | Path) -> None:
        raise PermissionError("injected promotion failure")

    try:
        try:
            save_candidate(
                presentation,
                app,
                OutputPolicy(source, output),
                replace=fail_replace,
            )
        except TransactionError as exc:
            assert "promotion failure" in str(exc)
        else:
            raise AssertionError("promotion failure unexpectedly succeeded")
        assert output.read_bytes() == existing and digest(source) == source_hash
        assert not list(output.parent.glob(".window-pptx-*.pptx"))
        return {"existing_output_unchanged": True, "candidate_cleanup": True}
    finally:
        safe_close(presentation)
        safe_quit(app)


def case_source_lock(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    app, presentation, source, source_hash = prepare_real_transaction(root, "source lock")
    output = source.parent / "locked-final.pptx"
    save_fixture(app, output, "LOCKED-OUTPUT")
    output_hash = digest(output)
    locked = None
    try:
        locked = open_presentation(app, output, read_only=False)
        try:
            save_candidate(presentation, app, OutputPolicy(source, output))
        except TransactionError:
            pass
        else:
            raise BlockedCase(
                "PowerPoint did not deny replacement of an open final output on this host"
            )
        assert digest(output) == output_hash and digest(source) == source_hash
        return {"locked_output_unchanged": True, "source_unchanged": True}
    finally:
        safe_close(locked)
        safe_close(presentation)
        safe_quit(app)


def case_pdf_partial(root: Path, environment: dict[str, Any]) -> dict[str, Any]:
    app, presentation, source, source_hash = prepare_real_transaction(root, "pdf partial")
    output = source.parent / "delivered.pptx"
    pdf_output = output.with_suffix(".pdf")
    pdf_output.write_bytes(b"%PDF-OLD-SENTINEL")
    old_pdf = pdf_output.read_bytes()

    def selective_replace(candidate: str | Path, target: str | Path) -> None:
        if Path(target).suffix.lower() == ".pdf":
            raise PermissionError("injected PDF promotion failure")
        os.replace(candidate, target)

    try:
        try:
            save_candidate(
                presentation,
                app,
                OutputPolicy(source, output),
                export_pdf=True,
                replace=selective_replace,
            )
        except PartialSaveError as exc:
            assert exc.pptx_result.promoted
        else:
            raise AssertionError("PDF partial failure unexpectedly succeeded")
        validate_ooxml_package(output)
        assert pdf_output.read_bytes() == old_pdf and digest(source) == source_hash
        assert not list(output.parent.glob(".window-pptx-*.pdf"))
        return {
            "pptx_promoted": True,
            "existing_pdf_unchanged": True,
            "source_unchanged": True,
        }
    finally:
        safe_close(presentation)
        safe_quit(app)


CASES: list[tuple[str, Callable[[Path, dict[str, Any]], dict[str, Any]]]] = [
    ("preflight", case_preflight),
    ("dry_run_zero_side_effects", case_dry_run),
    ("owned_isolated_cleanup", case_owned_cleanup),
    ("attached_preservation", case_attached_preservation),
    ("macro_security_success_failure", case_macro_security),
    ("terminal_addins_probe", case_terminal_addins),
    ("pptx_transaction", case_pptx),
    ("pptm_transaction", case_pptm),
    ("ratio_exports", case_ratio_exports),
    ("guard_failures", case_guard_failures),
    ("promotion_failure", case_promotion_failure),
    ("source_lock", case_source_lock),
    ("pdf_partial_failure", case_pdf_partial),
]


def scrub(value: Any, root: Path) -> Any:
    if isinstance(value, str):
        return value.replace(str(root), "%WINDOW_PPTX_UAT_TEMP%")
    if isinstance(value, dict):
        return {key: scrub(item, root) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub(item, root) for item in value]
    return value


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    selected_case_ids: set[str] | None = None
    if len(sys.argv) == 3 and sys.argv[1] == "--cases":
        selected_case_ids = {item.strip() for item in sys.argv[2].split(",") if item.strip()}

    baseline_powerpoint_pids = powerpoint_pids()
    run_id = uuid.uuid4().hex
    root = Path(tempfile.gettempdir()) / f"窗口 PPTX 验证 {run_id}"
    root.mkdir(parents=True, exist_ok=False)
    environment: dict[str, Any] = {}
    environment["preexisting_powerpoint_processes"] = len(
        baseline_powerpoint_pids
    )
    results: list[dict[str, Any]] = []
    started = time.time()
    selected_cases = [
        (case_id, function)
        for case_id, function in CASES
        if selected_case_ids is None or case_id in selected_case_ids
    ]
    for case_id, function in selected_cases:
        case_started = time.perf_counter()
        trace(f"start {case_id}")
        try:
            details = function(root, environment)
        except BlockedCase as exc:
            results.append(
                {
                    "id": case_id,
                    "status": "blocked",
                    "duration_ms": round((time.perf_counter() - case_started) * 1000),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        except Exception as exc:
            results.append(
                {
                    "id": case_id,
                    "status": "failed",
                    "duration_ms": round((time.perf_counter() - case_started) * 1000),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        else:
            results.append(
                {
                    "id": case_id,
                    "status": "passed",
                    "duration_ms": round((time.perf_counter() - case_started) * 1000),
                    "details": details,
                }
            )
        (root / "uat-progress.json").write_text(
            json.dumps(
                {"environment": environment, "cases": results},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        trace(f"finish {case_id}: {results[-1]['status']}")

    process_residue = wait_new_powerpoint_processes_closed(
        baseline_powerpoint_pids
    )
    cleanup_error: str | None = None
    try:
        shutil.rmtree(root)
    except Exception as exc:
        cleanup_error = f"{type(exc).__name__}: {exc}"

    counts = {
        status: sum(1 for result in results if result["status"] == status)
        for status in ("passed", "failed", "blocked")
    }
    payload = {
        "schema_version": "1.0",
        "run_id": run_id,
        "started_epoch": round(started),
        "duration_ms": round((time.time() - started) * 1000),
        "environment": environment,
        "cases": results,
        "summary": {
            **counts,
            "total": len(results),
            "cleanup": "passed" if cleanup_error is None else "failed",
            "cleanup_error": cleanup_error,
            "process_cleanup": "passed" if not process_residue else "failed",
            "new_powerpoint_process_residue": sorted(process_residue),
        },
    }
    print(json.dumps(scrub(payload, root), ensure_ascii=False, indent=2))
    return (
        0
        if counts["failed"] == 0
        and counts["blocked"] == 0
        and cleanup_error is None
        and not process_residue
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
