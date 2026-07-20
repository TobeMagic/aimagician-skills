from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "owned"
    / "window-pptx"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

from window_pptx.com_session import dispatch_powerpoint, macro_security
from window_pptx.errors import ComSessionError, OutputPolicyError, WindowPptxError
from window_pptx.models import OutputPolicy, PowerPointHandle
from window_pptx.output_policy import calculate_export_size, validate_output_policy


class FakeApplication:
    def __init__(self, automation_security: int = 1) -> None:
        self.AutomationSecurity = automation_security
        self.quit_calls = 0

    def Quit(self) -> None:
        self.quit_calls += 1


class FakePresentation:
    def __init__(self, close_error: Exception | None = None) -> None:
        self.close_calls = 0
        self.close_error = close_error

    def Close(self) -> None:
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error


class FakeDynamicDispatch:
    def __init__(self, app: object, error: Exception | None = None) -> None:
        self.app = app
        self.error = error
        self.calls: list[str] = []

    def Dispatch(self, prog_id: str) -> object:
        self.calls.append(prog_id)
        if self.error is not None:
            raise self.error
        return self.app


class FakeClient:
    def __init__(
        self,
        *,
        active_app: object | None = None,
        isolated_app: object | None = None,
        fallback_app: object | None = None,
        active_error: Exception | None = None,
        isolated_error: Exception | None = None,
        fallback_error: Exception | None = None,
    ) -> None:
        self.active_app = active_app
        self.isolated_app = isolated_app
        self.active_error = active_error
        self.isolated_error = isolated_error
        self.active_calls: list[str] = []
        self.isolated_calls: list[str] = []
        self.dynamic = FakeDynamicDispatch(fallback_app, fallback_error)

    def GetActiveObject(self, prog_id: str) -> object:
        self.active_calls.append(prog_id)
        if self.active_error is not None:
            raise self.active_error
        return self.active_app

    def DispatchEx(self, prog_id: str) -> object:
        self.isolated_calls.append(prog_id)
        if self.isolated_error is not None:
            raise self.isolated_error
        return self.isolated_app


def test_public_errors_derive_from_runtime_error() -> None:
    assert issubclass(WindowPptxError, RuntimeError)
    assert issubclass(OutputPolicyError, RuntimeError)
    assert issubclass(ComSessionError, RuntimeError)


def test_output_policy_is_immutable() -> None:
    policy = OutputPolicy(None, Path("deck.pptx"))

    with pytest.raises(FrozenInstanceError):
        policy.output_path = Path("other.pptx")  # type: ignore[misc]


def test_source_overwrite_is_rejected_after_path_resolution(tmp_path: Path) -> None:
    source = tmp_path / "source.pptx"
    nested = tmp_path / "nested"
    nested.mkdir()
    unresolved_output = nested / ".." / source.name
    assert source != unresolved_output
    policy = OutputPolicy(source, unresolved_output)

    with pytest.raises(OutputPolicyError, match="source"):
        validate_output_policy(policy)


def test_explicit_source_overwrite_is_allowed_for_a_real_run(tmp_path: Path) -> None:
    source = tmp_path / "source.pptx"

    validate_output_policy(
        OutputPolicy(source, source, allow_overwrite=True)
    )


@pytest.mark.parametrize("suffix", [".pptx", ".pptm", ".potx", ".potm"])
def test_powerpoint_extensions_are_accepted_without_rewriting_suffix(
    tmp_path: Path,
    suffix: str,
) -> None:
    source = tmp_path / f"source{suffix}"
    output = tmp_path / f"output{suffix}"
    policy = OutputPolicy(source, output)

    validate_output_policy(policy)

    assert policy.source_path == source
    assert policy.output_path == output
    assert policy.source_path.suffix == suffix
    assert policy.output_path.suffix == suffix


@pytest.mark.parametrize(
    ("source_name", "output_name"),
    [
        ("source", "output.pptx"),
        ("source.pdf", "output.pptx"),
        ("source.pptx", "output"),
        ("source.pptx", "output.pdf"),
    ],
)
def test_missing_or_invalid_extensions_are_rejected(
    tmp_path: Path,
    source_name: str,
    output_name: str,
) -> None:
    with pytest.raises(OutputPolicyError, match="extension"):
        validate_output_policy(
            OutputPolicy(tmp_path / source_name, tmp_path / output_name)
        )


def test_output_path_is_required_for_a_normal_run() -> None:
    with pytest.raises(OutputPolicyError, match="output"):
        validate_output_policy(OutputPolicy(None, None))


@pytest.mark.parametrize(
    "policy",
    [
        OutputPolicy(None, None, dry_run=True),
        OutputPolicy(None, None, no_output_deck=True),
    ],
)
def test_dry_run_or_no_output_deck_permits_no_output_path(policy: OutputPolicy) -> None:
    validate_output_policy(policy)


def test_dry_run_rejects_allow_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source.pptx"

    with pytest.raises(OutputPolicyError, match="dry-run"):
        validate_output_policy(
            OutputPolicy(
                source,
                source,
                dry_run=True,
                allow_overwrite=True,
            )
        )


@pytest.mark.parametrize(
    ("width", "height", "expected"),
    [
        (16.0, 9.0, (1600, 900)),
        (4.0, 3.0, (1600, 1200)),
        (9.0, 16.0, (900, 1600)),
    ],
)
def test_export_size_preserves_aspect_ratio(
    width: float,
    height: float,
    expected: tuple[int, int],
) -> None:
    result = calculate_export_size(width, height)

    assert result == expected
    assert max(result) == 1600


@pytest.mark.parametrize(
    ("width", "height", "long_edge"),
    [
        (0.0, 9.0, 1600),
        (-1.0, 9.0, 1600),
        (16.0, 0.0, 1600),
        (16.0, -1.0, 1600),
        (16.0, 9.0, 0),
        (16.0, 9.0, -1),
    ],
)
def test_export_size_rejects_non_positive_values(
    width: float,
    height: float,
    long_edge: int,
) -> None:
    with pytest.raises(ValueError):
        calculate_export_size(width, height, long_edge)


def test_isolated_dispatch_records_true_ownership() -> None:
    app = FakeApplication()
    client = FakeClient(isolated_app=app)

    handle = dispatch_powerpoint(attach_existing=False, client=client)

    assert handle.app is app
    assert handle.owned is True
    assert client.isolated_calls == ["PowerPoint.Application"]
    assert client.dynamic.calls == []


def test_dynamic_dispatch_fallback_is_never_assumed_owned() -> None:
    app = FakeApplication()
    client = FakeClient(
        isolated_error=RuntimeError("DispatchEx unavailable"),
        fallback_app=app,
    )

    handle = dispatch_powerpoint(attach_existing=False, client=client)

    assert handle.app is app
    assert handle.owned is False
    assert client.isolated_calls == ["PowerPoint.Application"]
    assert client.dynamic.calls == ["PowerPoint.Application"]


def test_explicit_attach_uses_active_object_and_never_quits_it() -> None:
    app = FakeApplication()
    client = FakeClient(active_app=app)

    handle = dispatch_powerpoint(attach_existing=True, client=client)
    handle.quit()

    assert handle.app is app
    assert handle.owned is False
    assert client.active_calls == ["PowerPoint.Application"]
    assert client.isolated_calls == []
    assert client.dynamic.calls == []
    assert app.quit_calls == 0


def test_owned_session_quits_unless_keep_open() -> None:
    app = FakeApplication()
    handle = PowerPointHandle(app, owned=True, dispatch_mode="dispatch_ex")

    handle.quit(keep_open=True)
    handle.quit()

    assert app.quit_calls == 1


def test_macro_security_restores_exact_value_after_success() -> None:
    app = FakeApplication(automation_security=7)

    with macro_security(app):
        assert app.AutomationSecurity == 3

    assert app.AutomationSecurity == 7


def test_macro_security_restores_exact_value_after_body_exception() -> None:
    app = FakeApplication(automation_security=2)

    with pytest.raises(ValueError, match="body failed"):
        with macro_security(app, force_disable=3):
            assert app.AutomationSecurity == 3
            raise ValueError("body failed")

    assert app.AutomationSecurity == 2


def test_macro_security_supports_late_bound_callable_property_getter() -> None:
    class LateBoundApplication:
        def __init__(self) -> None:
            object.__setattr__(self, "security_value", 1)

        def __getattr__(self, name: str) -> object:
            if name == "AutomationSecurity":
                return lambda: self.security_value
            raise AttributeError(name)

        def __setattr__(self, name: str, value: object) -> None:
            if name == "AutomationSecurity":
                object.__setattr__(self, "security_value", value)
                return
            object.__setattr__(self, name, value)

    app = LateBoundApplication()

    with macro_security(app):
        assert app.security_value == 3

    assert app.security_value == 1


def test_macro_security_unavailable_raises_before_entering_body() -> None:
    class ApplicationWithoutMacroSecurity:
        @property
        def AutomationSecurity(self) -> int:
            raise AttributeError("unavailable")

    body_entered = False

    with pytest.raises(ComSessionError, match="AutomationSecurity"):
        with macro_security(ApplicationWithoutMacroSecurity()):
            body_entered = True

    assert body_entered is False


def test_close_failure_is_recorded_without_escaping() -> None:
    presentation = FakePresentation(RuntimeError("close failed"))
    handle = PowerPointHandle(FakeApplication(), owned=False, dispatch_mode="attached")

    handle.close_presentation(presentation)

    assert presentation.close_calls == 1
    assert len(handle.cleanup_errors) == 1
    assert "close" in handle.cleanup_errors[0].lower()
    assert "close failed" in handle.cleanup_errors[0]


def test_quit_failure_is_recorded_without_hiding_original_error() -> None:
    class ApplicationWithBrokenQuit:
        def Quit(self) -> None:
            raise RuntimeError("quit failed")

    handle = PowerPointHandle(
        ApplicationWithBrokenQuit(),
        owned=True,
        dispatch_mode="dispatch_ex",
    )
    original = ValueError("original failure")

    with pytest.raises(ValueError) as raised:
        try:
            raise original
        finally:
            handle.quit()

    assert raised.value is original
    assert len(handle.cleanup_errors) == 1
    assert "quit" in handle.cleanup_errors[0].lower()
    assert "quit failed" in handle.cleanup_errors[0]


def test_cleanup_error_lists_are_not_shared_between_handles() -> None:
    first = PowerPointHandle(FakeApplication(), owned=False, dispatch_mode="attached")
    second = PowerPointHandle(FakeApplication(), owned=False, dispatch_mode="attached")

    first.cleanup_errors.append("first only")

    assert second.cleanup_errors == []
