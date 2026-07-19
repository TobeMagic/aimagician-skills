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
    presentation = SimpleNamespace(Close=lambda: None)
    monkeypatch.setattr(automation, "require_windows", lambda: None)
    monkeypatch.setattr(automation, "import_win32com", lambda: object())
    monkeypatch.setattr(automation, "dispatch_powerpoint", lambda *_args: app)
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
    monkeypatch.setattr(automation, "choose_template", lambda *_args: None)
    monkeypatch.setattr(
        automation,
        "open_or_create_presentation",
        lambda *_args: presentation,
    )
    monkeypatch.setattr(
        automation,
        "read_request",
        lambda *_args: (tmp_path / "REQUEST.md", "request"),
    )
    monkeypatch.setattr(automation, "add_request_summary_slide", lambda *_args: None)
    monkeypatch.setattr(
        automation,
        "save_outputs",
        lambda *_args: {"pptx": str(tmp_path / "output" / "final.pptx")},
    )

    assert automation.main(
        ["--project-dir", str(tmp_path), inspection_flag]
    ) == 0

    stdout = capsys.readouterr().out
    assert stdout.count(detail) == 1
    final_stdout = stdout.split("window-pptx run complete\n", 1)[1]
    final_result = json.loads(final_stdout)
    assert final_key not in final_result
