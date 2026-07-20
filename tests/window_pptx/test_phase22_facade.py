from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "owned"
    / "window-pptx"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

import window_pptx_automation as automation  # noqa: E402
from window_pptx.cli import parse_args  # noqa: E402
from window_pptx.errors import OutputPolicyError  # noqa: E402
from window_pptx.models import PowerPointHandle  # noqa: E402


class RecordingPresentation:
    def __init__(self) -> None:
        self.close_calls = 0

    def Close(self) -> None:
        self.close_calls += 1


class RecordingPresentations:
    def __init__(
        self,
        app: "RecordingApplication",
        *,
        open_error: Exception | None = None,
    ) -> None:
        self.app = app
        self.open_error = open_error
        self.open_calls: list[tuple[object, ...]] = []
        self.add_calls: list[tuple[object, ...]] = []
        self.security_during_open: list[int] = []
        self.last_presentation: RecordingPresentation | None = None

    def Open(self, *args: object) -> RecordingPresentation:
        self.open_calls.append(args)
        self.security_during_open.append(self.app.AutomationSecurity)
        if self.open_error is not None:
            raise self.open_error
        self.last_presentation = RecordingPresentation()
        return self.last_presentation

    def Add(self, *args: object) -> RecordingPresentation:
        self.add_calls.append(args)
        self.security_during_open.append(self.app.AutomationSecurity)
        self.last_presentation = RecordingPresentation()
        return self.last_presentation


class RecordingApplication:
    def __init__(
        self,
        *,
        automation_security: int = 1,
        open_error: Exception | None = None,
    ) -> None:
        self.AutomationSecurity = automation_security
        self.Visible = 0
        self.quit_calls = 0
        self.Presentations = RecordingPresentations(self, open_error=open_error)

    def Quit(self) -> None:
        self.quit_calls += 1


class RecordingDynamicDispatch:
    def __init__(self, app: RecordingApplication) -> None:
        self.app = app
        self.calls: list[str] = []

    def Dispatch(self, prog_id: str) -> RecordingApplication:
        self.calls.append(prog_id)
        return self.app


class RecordingComClient:
    def __init__(
        self,
        app: RecordingApplication,
        *,
        dispatch_ex_error: Exception | None = None,
    ) -> None:
        self.app = app
        self.dispatch_ex_error = dispatch_ex_error
        self.active_calls: list[str] = []
        self.dispatch_ex_calls: list[str] = []
        self.dynamic = RecordingDynamicDispatch(app)

    def GetActiveObject(self, prog_id: str) -> RecordingApplication:
        self.active_calls.append(prog_id)
        return self.app

    def DispatchEx(self, prog_id: str) -> RecordingApplication:
        self.dispatch_ex_calls.append(prog_id)
        if self.dispatch_ex_error is not None:
            raise self.dispatch_ex_error
        return self.app


def patch_deck_dependencies(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(automation, "require_windows", lambda: None)
    monkeypatch.setattr(
        automation,
        "import_win32com",
        lambda: (_ for _ in ()).throw(AssertionError("injected COM client ignored")),
    )
    monkeypatch.setattr(automation, "list_com_addins", lambda _app: [])
    monkeypatch.setattr(automation, "list_powerpoint_addins", lambda _app: [])
    monkeypatch.setattr(
        automation,
        "read_request",
        lambda *_args: (tmp_path / "REQUEST.md", "request"),
    )
    monkeypatch.setattr(automation, "add_request_summary_slide", lambda *_args: None)
    monkeypatch.setattr(
        automation,
        "save_outputs",
        lambda _presentation, output_path, _export_pdf: {"pptx": str(output_path)},
    )


def test_parse_args_accepts_explicit_argv_and_new_flags() -> None:
    args = parse_args(
        ["--project-dir", "project", "--dry-run", "--no-output-deck"]
    )

    assert args.project_dir == "project"
    assert args.request == "REQUEST.md"
    assert args.output == "output/final.pptx"
    assert args.dry_run is True
    assert args.no_output_deck is True


@pytest.mark.parametrize(
    "branch_args",
    [
        ["--init-project"],
        ["--search-images", "window"],
        ["--download-image", "https://example.test/window.png"],
        ["--search-icons", "window"],
        ["--download-icon", "bi:window"],
        ["--intake-template-library"],
        ["--extract-media", "--template", "deck.pptx"],
        ["--export-slides", "1"],
        ["--audit-deck"],
        ["--export-qa"],
        ["--list-addins"],
        ["--probe-plugin-apis"],
        [],
    ],
)
def test_dry_run_precedes_every_mutating_branch(
    branch_args: list[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    marker = project_dir / "marker.txt"
    marker.write_text("unchanged", encoding="utf-8")

    def snapshot() -> tuple[tuple[str, bytes], ...]:
        return tuple(
            (str(path.relative_to(tmp_path)), path.read_bytes())
            for path in sorted(tmp_path.rglob("*"))
            if path.is_file()
        )

    before = snapshot()

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("dry-run reached a mutating, network, or COM helper")

    for name in (
        "require_windows",
        "import_win32com",
        "dispatch_powerpoint",
        "open_or_create_presentation",
        "save_outputs",
        "export_slides_to_png",
        "export_all_slides_to_png",
        "init_project_workspace",
        "pixabay_search",
        "download_images",
        "iconify_search",
        "download_image",
        "download_icon",
        "intake_template_library",
        "extract_media_from_deck",
        "audit_presentation",
        "list_com_addins",
        "list_powerpoint_addins",
        "probe_plugin_apis",
    ):
        if hasattr(automation, name):
            monkeypatch.setattr(automation, name, forbidden)

    result = automation.main(
        ["--project-dir", str(project_dir), "--dry-run", "--json", *branch_args]
    )

    assert result == 0
    assert snapshot() == before
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {
        "schema_version",
        "mode",
        "would_run",
        "would_write",
        "warnings",
    }


def test_dry_run_stdout_is_exactly_one_json_document(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert automation.main(
        ["--project-dir", str(tmp_path), "--dry-run", "--json"]
    ) == 0

    stdout = capsys.readouterr().out
    payload = json.loads(stdout)
    assert set(payload) == {
        "schema_version",
        "mode",
        "would_run",
        "would_write",
        "warnings",
    }
    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "dry-run"


def test_no_save_is_normalized_with_one_deprecation_warning(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = parse_args(["--project-dir", "project", "--no-save"])

    assert args.no_output_deck is True
    assert args.dry_run is False
    stderr = capsys.readouterr().err
    assert stderr.lower().count("deprecated") == 1


def test_no_output_deck_is_normalized_without_warning(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = parse_args(["--project-dir", "project", "--no-output-deck"])

    assert args.no_output_deck is True
    assert args.dry_run is False
    assert capsys.readouterr().err == ""


def test_existing_non_com_json_branch_emits_one_document(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        automation, "pixabay_search", lambda *_args, **_kwargs: {"ok": True}
    )

    assert automation.main(
        [
            "--project-dir",
            str(tmp_path),
            "--search-images",
            "window",
            "--no-output-deck",
            "--json",
        ]
    ) == 0

    stdout = capsys.readouterr().out
    assert json.loads(stdout) == {
        "init_project": None,
        "pixabay_search": {"ok": True},
    }


@pytest.mark.parametrize(
    ("inspection_flag", "detail", "final_key"),
    [
        ("--list-addins", "LIST-ADDIN-DETAIL", "addins"),
        ("--probe-plugin-apis", "PROBE-API-DETAIL", "plugin_api_probe"),
    ],
)
def test_non_json_inspection_detail_is_not_repeated_in_final_result(
    inspection_flag: str,
    detail: str,
    final_key: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    app = SimpleNamespace(Quit=lambda: None)
    monkeypatch.setattr(automation, "require_windows", lambda: None)
    monkeypatch.setattr(automation, "import_win32com", lambda: object())
    monkeypatch.setattr(
        automation,
        "dispatch_powerpoint",
        lambda *_args: PowerPointHandle(app, owned=True, dispatch_mode="test"),
    )
    monkeypatch.setattr(
        automation,
        "list_com_addins",
        lambda _app: [{"description": detail, "prog_id": "test", "guid": "test", "connect": True}],
    )
    monkeypatch.setattr(automation, "list_powerpoint_addins", lambda _app: [])
    monkeypatch.setattr(
        automation,
        "probe_plugin_apis",
        lambda *_args: {"detail": detail},
    )
    assert automation.main(
        ["--project-dir", str(tmp_path), inspection_flag]
    ) == 0

    stdout = capsys.readouterr().out
    assert stdout.count(detail) == 1
    assert "window-pptx run complete" not in stdout
    assert final_key not in stdout.split(detail, 1)[1]


def test_owned_isolated_main_run_closes_deck_and_quits_app(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_deck_dependencies(monkeypatch, tmp_path)
    app = RecordingApplication(automation_security=8)
    client = RecordingComClient(app)

    assert automation.main(
        ["--project-dir", str(tmp_path), "--visible"],
        com_client=client,
    ) == 0

    assert client.dispatch_ex_calls == ["PowerPoint.Application"]
    assert client.active_calls == []
    assert client.dynamic.calls == []
    assert app.Visible == automation.MSO_TRUE
    assert app.Presentations.add_calls == [(automation.MSO_TRUE,)]
    assert app.Presentations.security_during_open == [3]
    assert app.AutomationSecurity == 8
    assert app.Presentations.last_presentation is not None
    assert app.Presentations.last_presentation.close_calls == 1
    assert app.quit_calls == 1


def test_attached_main_run_uses_active_object_closes_deck_but_never_quits_host(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_deck_dependencies(monkeypatch, tmp_path)
    template = tmp_path / "source.pptx"
    template.write_bytes(b"deck")
    app = RecordingApplication(automation_security=6)
    client = RecordingComClient(app)

    assert automation.main(
        [
            "--project-dir",
            str(tmp_path),
            "--template",
            str(template),
            "--attach-existing",
        ],
        com_client=client,
    ) == 0

    assert client.active_calls == ["PowerPoint.Application"]
    assert client.dispatch_ex_calls == []
    assert client.dynamic.calls == []
    assert len(app.Presentations.open_calls) == 1
    assert app.Presentations.security_during_open == [3]
    assert app.AutomationSecurity == 6
    assert app.Presentations.last_presentation is not None
    assert app.Presentations.last_presentation.close_calls == 1
    assert app.quit_calls == 0


def test_dynamic_dispatch_fallback_main_run_never_quits_fallback_app(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_deck_dependencies(monkeypatch, tmp_path)
    app = RecordingApplication()
    client = RecordingComClient(
        app,
        dispatch_ex_error=RuntimeError("DispatchEx failed"),
    )

    assert automation.main(["--project-dir", str(tmp_path)], com_client=client) == 0

    assert client.dispatch_ex_calls == ["PowerPoint.Application"]
    assert client.dynamic.calls == ["PowerPoint.Application"]
    assert app.Presentations.last_presentation is not None
    assert app.Presentations.last_presentation.close_calls == 1
    assert app.quit_calls == 0


def test_macro_security_is_restored_exactly_when_presentation_open_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_deck_dependencies(monkeypatch, tmp_path)
    template = tmp_path / "source.pptx"
    template.write_bytes(b"deck")
    app = RecordingApplication(
        automation_security=9,
        open_error=RuntimeError("open failed"),
    )
    client = RecordingComClient(app)

    with pytest.raises(RuntimeError, match="open failed"):
        automation.main(
            ["--project-dir", str(tmp_path), "--template", str(template)],
            com_client=client,
        )

    assert app.Presentations.security_during_open == [3]
    assert app.AutomationSecurity == 9
    assert app.quit_calls == 1


def test_template_intake_open_also_uses_macro_security(tmp_path: Path) -> None:
    template = tmp_path / "library.potm"
    app = RecordingApplication(automation_security=5)

    presentation = automation.open_template_presentation(app, template)

    assert presentation is app.Presentations.last_presentation
    assert app.Presentations.security_during_open == [3]
    assert app.AutomationSecurity == 5


def test_same_source_and_output_fails_before_presentation_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_deck_dependencies(monkeypatch, tmp_path)
    template = tmp_path / "source.pptx"
    template.write_bytes(b"deck")
    nested = tmp_path / "nested"
    nested.mkdir()
    output = nested / ".." / template.name
    app = RecordingApplication()
    client = RecordingComClient(app)

    with pytest.raises(OutputPolicyError, match="source"):
        automation.main(
            [
                "--project-dir",
                str(tmp_path),
                "--template",
                str(template),
                "--output",
                str(output),
            ],
            com_client=client,
        )

    assert app.Presentations.open_calls == []
    assert app.Presentations.add_calls == []


def test_allow_overwrite_permits_same_source_and_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_deck_dependencies(monkeypatch, tmp_path)
    template = tmp_path / "source.pptx"
    template.write_bytes(b"deck")
    app = RecordingApplication()
    client = RecordingComClient(app)

    assert automation.main(
        [
            "--project-dir",
            str(tmp_path),
            "--template",
            str(template),
            "--output",
            str(template),
            "--allow-overwrite",
        ],
        com_client=client,
    ) == 0

    assert len(app.Presentations.open_calls) == 1


def test_invalid_output_extension_fails_before_presentation_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_deck_dependencies(monkeypatch, tmp_path)
    app = RecordingApplication()
    client = RecordingComClient(app)

    with pytest.raises(OutputPolicyError, match="extension"):
        automation.main(
            ["--project-dir", str(tmp_path), "--output", "output/final.pdf"],
            com_client=client,
        )

    assert app.Presentations.open_calls == []
    assert app.Presentations.add_calls == []


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        (["--list-addins"], {"addins"}),
        (["--probe-plugin-apis"], {"plugin_api_probe"}),
        (
            ["--list-addins", "--probe-plugin-apis"],
            {"addins", "plugin_api_probe"},
        ),
    ],
)
def test_inspection_routes_are_terminal_and_emit_one_requested_json_object(
    flags: list[str],
    expected: set[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(automation, "require_windows", lambda: None)
    monkeypatch.setattr(
        automation,
        "import_win32com",
        lambda: (_ for _ in ()).throw(AssertionError("injected COM client ignored")),
    )
    monkeypatch.setattr(automation, "list_com_addins", lambda _app: [{"prog_id": "A"}])
    monkeypatch.setattr(automation, "list_powerpoint_addins", lambda _app: [{"name": "B"}])
    monkeypatch.setattr(
        automation,
        "probe_plugin_apis",
        lambda _app, progids: {"probed_progids": progids},
    )
    app = RecordingApplication()
    client = RecordingComClient(app)

    assert automation.main(
        ["--project-dir", str(tmp_path), "--json", *flags],
        com_client=client,
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == expected
    assert app.Presentations.open_calls == []
    assert app.Presentations.add_calls == []
    assert not (tmp_path / ".window-pptx").exists()
    assert app.quit_calls == 1


@pytest.mark.parametrize("suffix", [".pptm", ".potm"])
def test_ascii_temp_copy_preserves_macro_enabled_suffix(
    suffix: str,
    tmp_path: Path,
) -> None:
    source = tmp_path / f"source{suffix}"
    source.write_bytes(b"deck")

    copied = automation.ensure_ascii_temp_copy(tmp_path, source)

    assert copied.suffix == suffix
    assert copied.read_bytes() == b"deck"


class RecordingExportSlide:
    def __init__(self) -> None:
        self.exports: list[tuple[object, ...]] = []

    def Export(self, *args: object) -> None:
        self.exports.append(args)


class RecordingSlides:
    def __init__(self, slide: RecordingExportSlide) -> None:
        self.Count = 1
        self.slide = slide

    def __call__(self, index: int) -> RecordingExportSlide:
        assert index == 1
        return self.slide


@pytest.mark.parametrize(
    ("page_size", "export_all", "expected_size"),
    [
        ((10.0, 7.5), False, (1600, 1200)),
        ((7.5, 13.3333333333), True, (900, 1600)),
    ],
)
def test_png_export_uses_presentation_geometry(
    page_size: tuple[float, float],
    export_all: bool,
    expected_size: tuple[int, int],
    tmp_path: Path,
) -> None:
    slide = RecordingExportSlide()
    presentation = SimpleNamespace(
        PageSetup=SimpleNamespace(SlideWidth=page_size[0], SlideHeight=page_size[1]),
        Slides=RecordingSlides(slide),
    )

    if export_all:
        automation.export_all_slides_to_png(presentation, tmp_path / "exports")
    else:
        automation.export_slides_to_png(presentation, [1], tmp_path / "exports")

    assert slide.exports == [
        (
            str(tmp_path / "exports" / "slide-1.png"),
            "PNG",
            expected_size[0],
            expected_size[1],
        )
    ]
