from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path
from typing import Callable

import pytest


SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "owned"
    / "window-pptx"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

from window_pptx.errors import OutputPolicyError, WindowPptxError  # noqa: E402
from window_pptx.models import OutputPolicy  # noqa: E402
from window_pptx.transaction import (  # noqa: E402
    PartialSaveError,
    SourceIntegrityError,
    TransactionError,
    candidate_path_for,
    save_candidate,
    sha256_file,
    validate_ooxml_package,
)


REQUIRED_PARTS = (
    "[Content_Types].xml",
    "_rels/.rels",
    "ppt/presentation.xml",
)


def write_ooxml(path: Path, *, omit: str | None = None) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as archive:
        for part in REQUIRED_PARTS:
            if part != omit:
                archive.writestr(part, b"<xml/>")


class RecordingPresentation:
    def __init__(
        self,
        events: list[str],
        *,
        save_error: Exception | None = None,
        pdf_bytes: bytes = b"%PDF-1.7\nbody",
    ) -> None:
        self.events = events
        self.save_error = save_error
        self.pdf_bytes = pdf_bytes
        self.save_copy_paths: list[Path] = []
        self.save_as_calls = 0

    def SaveCopyAs(self, value: str) -> None:
        self.events.append("save-copy")
        self.save_copy_paths.append(Path(value))
        if self.save_error is not None:
            raise self.save_error
        write_ooxml(Path(value))

    def SaveAs(self, _value: str) -> None:
        self.save_as_calls += 1
        raise AssertionError("SaveAs must never be used")

    def ExportAsFixedFormat(self, value: str, *_args: object) -> None:
        self.events.append("export-pdf")
        Path(value).write_bytes(self.pdf_bytes)


class ValidationPresentation:
    def __init__(
        self,
        events: list[str],
        *,
        close_error: Exception | None = None,
    ) -> None:
        self.events = events
        self.close_error = close_error

    def Close(self) -> None:
        self.events.append("close-validation")
        if self.close_error is not None:
            raise self.close_error


class RecordingPresentations:
    def __init__(self, app: "RecordingApp", events: list[str]) -> None:
        self.app = app
        self.events = events
        self.open_calls: list[tuple[object, ...]] = []

    def Open(self, *args: object) -> ValidationPresentation:
        self.events.append("reopen")
        self.open_calls.append(args)
        assert self.app.AutomationSecurity == 3
        return ValidationPresentation(self.events)


class RecordingApp:
    def __init__(self, events: list[str]) -> None:
        self.AutomationSecurity = 1
        self.Presentations = RecordingPresentations(self, events)


def recording_replace(events: list[str]) -> Callable[[str | Path, str | Path], None]:
    def replace(source: str | Path, target: str | Path) -> None:
        events.append(f"replace-{Path(target).suffix}")
        os.replace(source, target)

    return replace


@pytest.mark.parametrize("suffix", [".pptx", ".pptm"])
def test_candidate_path_is_ascii_safe_sibling_with_exact_suffix(
    tmp_path: Path,
    suffix: str,
) -> None:
    output = tmp_path / f"客户交付{suffix}"

    candidate = candidate_path_for(output, token="固定 token")

    assert candidate.parent == output.parent
    assert candidate.suffix == suffix
    assert candidate != output
    assert candidate.name.startswith(".")
    assert candidate.name.isascii()


@pytest.mark.parametrize("mode", ["dry_run", "no_output_deck"])
def test_no_write_modes_do_not_create_parent_or_call_save_copy(
    tmp_path: Path,
    mode: str,
) -> None:
    events: list[str] = []
    presentation = RecordingPresentation(events)
    output = tmp_path / "missing" / "final.pptx"
    policy = OutputPolicy(None, output, **{mode: True})

    result = save_candidate(presentation, RecordingApp(events), policy)

    assert result.promoted is False
    assert result.candidate_path is None
    assert not output.parent.exists()
    assert presentation.save_copy_paths == []


def test_invalid_policy_fails_before_directory_or_save_copy(tmp_path: Path) -> None:
    events: list[str] = []
    presentation = RecordingPresentation(events)
    output = tmp_path / "missing" / "final.pdf"

    with pytest.raises(OutputPolicyError, match="extension"):
        save_candidate(
            presentation,
            RecordingApp(events),
            OutputPolicy(None, output),
        )

    assert not output.parent.exists()
    assert presentation.save_copy_paths == []


def test_happy_path_validates_reopens_closes_and_promotes_in_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import window_pptx.transaction as transaction

    events: list[str] = []
    output = tmp_path / "final.pptx"
    presentation = RecordingPresentation(events)
    real_validate = validate_ooxml_package

    def record_validation(path: Path) -> None:
        events.append("validate-package")
        real_validate(path)

    monkeypatch.setattr(transaction, "validate_ooxml_package", record_validation)

    result = save_candidate(
        presentation,
        RecordingApp(events),
        OutputPolicy(None, output),
        replace=recording_replace(events),
    )

    assert events == [
        "save-copy",
        "validate-package",
        "reopen",
        "close-validation",
        "replace-.pptx",
    ]
    assert result.promoted is True
    assert result.candidate_path is None
    assert result.validation_steps == (
        "save-copy",
        "ooxml-package",
        "macro-disabled-reopen",
        "validation-copy-closed",
        "atomic-promote",
    )
    assert output.exists()
    assert presentation.save_as_calls == 0


def test_default_reopen_is_read_only_and_windowless_and_restores_security(
    tmp_path: Path,
) -> None:
    events: list[str] = []
    app = RecordingApp(events)

    save_candidate(
        RecordingPresentation(events),
        app,
        OutputPolicy(None, tmp_path / "final.pptx"),
    )

    assert app.Presentations.open_calls[0][1:] == (-1, 0, 0)
    assert app.AutomationSecurity == 1


def test_valid_minimal_ooxml_package_passes(tmp_path: Path) -> None:
    path = tmp_path / "valid.pptx"
    write_ooxml(path)

    validate_ooxml_package(path)


@pytest.mark.parametrize("kind", ["corrupt", "bad-member", "missing-part"])
def test_invalid_ooxml_package_is_rejected(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "invalid.pptx"
    if kind == "corrupt":
        path.write_bytes(b"not-a-zip")
    elif kind == "missing-part":
        write_ooxml(path, omit="ppt/presentation.xml")
    else:
        write_ooxml(path)
        data = bytearray(path.read_bytes())
        marker = data.find(b"<xml/>")
        assert marker >= 0
        data[marker] ^= 0xFF
        path.write_bytes(data)

    with pytest.raises(WindowPptxError, match="OOXML|ZIP|required|corrupt"):
        validate_ooxml_package(path)


@pytest.mark.parametrize(
    "failure",
    ["save-copy", "package", "reopen", "replace"],
)
def test_failures_leave_existing_output_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    import window_pptx.transaction as transaction

    events: list[str] = []
    output = tmp_path / "final.pptx"
    output.write_bytes(b"existing-final")
    presentation = RecordingPresentation(
        events,
        save_error=RuntimeError("save failed") if failure == "save-copy" else None,
    )

    if failure == "package":
        monkeypatch.setattr(
            transaction,
            "validate_ooxml_package",
            lambda _path: (_ for _ in ()).throw(RuntimeError("bad package")),
        )

    def reopen(_path: Path) -> ValidationPresentation:
        events.append("reopen")
        if failure == "reopen":
            raise RuntimeError("reopen failed")
        return ValidationPresentation(events)

    def replace(source: str | Path, target: str | Path) -> None:
        if failure == "replace":
            raise RuntimeError("replace failed")
        os.replace(source, target)

    with pytest.raises(TransactionError):
        save_candidate(
            presentation,
            RecordingApp(events),
            OutputPolicy(None, output),
            reopen=reopen,
            replace=replace,
        )

    assert output.read_bytes() == b"existing-final"
    assert not any(output.parent.glob(".window-pptx-*"))


def test_candidate_cleanup_failure_is_observable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import window_pptx.transaction as transaction

    events: list[str] = []
    output = tmp_path / "final.pptx"
    monkeypatch.setattr(
        transaction,
        "validate_ooxml_package",
        lambda _path: (_ for _ in ()).throw(RuntimeError("bad package")),
    )
    real_unlink = Path.unlink

    def fail_candidate_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path.name.startswith(".window-pptx-"):
            raise PermissionError("candidate locked")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_candidate_unlink)

    with pytest.raises(TransactionError) as caught:
        save_candidate(
            RecordingPresentation(events),
            RecordingApp(events),
            OutputPolicy(None, output),
        )

    assert caught.value.cleanup_errors
    assert "candidate locked" in str(caught.value)


def test_distinct_source_hash_is_recorded_and_unchanged(tmp_path: Path) -> None:
    events: list[str] = []
    source = tmp_path / "source.pptx"
    source.write_bytes(b"source")

    result = save_candidate(
        RecordingPresentation(events),
        RecordingApp(events),
        OutputPolicy(source, tmp_path / "final.pptx"),
    )

    assert result.source_hash_before == sha256_file(source)
    assert result.source_hash_after == result.source_hash_before
    assert source.read_bytes() == b"source"


def test_source_mutation_aborts_before_promotion(tmp_path: Path) -> None:
    events: list[str] = []
    source = tmp_path / "source.pptx"
    source.write_bytes(b"source")
    output = tmp_path / "final.pptx"
    output.write_bytes(b"existing")

    def reopen(_candidate: Path) -> ValidationPresentation:
        events.append("reopen")
        source.write_bytes(b"mutated")
        return ValidationPresentation(events)

    with pytest.raises(TransactionError, match="source.*changed"):
        save_candidate(
            RecordingPresentation(events),
            RecordingApp(events),
            OutputPolicy(source, output),
            reopen=reopen,
            replace=recording_replace(events),
        )

    assert output.read_bytes() == b"existing"
    assert "replace-.pptx" not in events


def test_source_mutation_during_promotion_reports_partial_integrity_failure(
    tmp_path: Path,
) -> None:
    events: list[str] = []
    source = tmp_path / "source.pptx"
    source.write_bytes(b"source-before")
    output = tmp_path / "final.pptx"

    def mutating_replace(candidate: str | Path, final: str | Path) -> None:
        events.append("replace-.pptx")
        os.replace(candidate, final)
        source.write_bytes(b"source-after")

    with pytest.raises(SourceIntegrityError) as caught:
        save_candidate(
            RecordingPresentation(events),
            RecordingApp(events),
            OutputPolicy(source, output),
            replace=mutating_replace,
        )

    assert output.exists()
    assert caught.value.pptx_result.promoted is True
    assert caught.value.pptx_result.source_hash_before != sha256_file(source)
    assert caught.value.pptx_result.source_hash_after == sha256_file(source)
    assert "source integrity" in str(caught.value).lower()
    assert "pdf delivery failed" not in str(caught.value).lower()


def test_same_path_overwrite_is_explicitly_rejected_while_presentation_is_open(
    tmp_path: Path,
) -> None:
    events: list[str] = []
    source = tmp_path / "source.pptx"
    source.write_bytes(b"source")

    with pytest.raises(OutputPolicyError, match="same-path.*open"):
        save_candidate(
            RecordingPresentation(events),
            RecordingApp(events),
            OutputPolicy(source, source, allow_overwrite=True),
        )

    assert events == []
    assert source.read_bytes() == b"source"


def test_valid_pdf_candidate_promotes(tmp_path: Path) -> None:
    events: list[str] = []
    output = tmp_path / "final.pptx"

    result = save_candidate(
        RecordingPresentation(events),
        RecordingApp(events),
        OutputPolicy(None, output),
        export_pdf=True,
        replace=recording_replace(events),
    )

    assert result.promoted is True
    assert output.with_suffix(".pdf").read_bytes().startswith(b"%PDF-")
    assert events[-2:] == ["export-pdf", "replace-.pdf"]


@pytest.mark.parametrize("payload", [b"", b"not-pdf"])
def test_invalid_pdf_does_not_replace_existing_pdf_and_reports_partial_success(
    tmp_path: Path,
    payload: bytes,
) -> None:
    events: list[str] = []
    output = tmp_path / "final.pptx"
    pdf = output.with_suffix(".pdf")
    pdf.write_bytes(b"existing-pdf")

    with pytest.raises(PartialSaveError) as caught:
        save_candidate(
            RecordingPresentation(events, pdf_bytes=payload),
            RecordingApp(events),
            OutputPolicy(None, output),
            export_pdf=True,
            replace=recording_replace(events),
        )

    assert output.exists()
    assert pdf.read_bytes() == b"existing-pdf"
    assert caught.value.pptx_result.promoted is True
    assert str(output) in str(caught.value)
