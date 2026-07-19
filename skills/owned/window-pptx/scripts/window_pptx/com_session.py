"""PowerPoint COM session ownership and macro-security guards."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator
from typing import Any

from .errors import ComSessionError
from .models import PowerPointHandle


POWERPOINT_PROG_ID = "PowerPoint.Application"


def dispatch_powerpoint(attach_existing: bool, client: Any) -> PowerPointHandle:
    """Attach explicitly or create an isolated PowerPoint application."""

    if attach_existing:
        try:
            app = client.GetActiveObject(POWERPOINT_PROG_ID)
        except Exception as exc:
            raise ComSessionError(
                "Could not attach to an active PowerPoint application."
            ) from exc
        return PowerPointHandle(app, owned=False, dispatch_mode="get_active_object")

    try:
        app = client.DispatchEx(POWERPOINT_PROG_ID)
    except Exception:
        try:
            app = client.dynamic.Dispatch(POWERPOINT_PROG_ID)
        except Exception as fallback_error:
            raise ComSessionError(
                "Could not create or dispatch a PowerPoint application."
            ) from fallback_error
        return PowerPointHandle(
            app,
            owned=False,
            dispatch_mode="dynamic_dispatch_fallback",
        )

    return PowerPointHandle(app, owned=True, dispatch_mode="dispatch_ex")


@contextmanager
def macro_security(app: Any, force_disable: int = 3) -> Iterator[None]:
    """Disable macros temporarily and restore the exact prior setting."""

    try:
        previous = app.AutomationSecurity
    except Exception as exc:
        raise ComSessionError(
            "PowerPoint AutomationSecurity is unavailable."
        ) from exc

    try:
        app.AutomationSecurity = force_disable
    except Exception as exc:
        raise ComSessionError(
            "PowerPoint AutomationSecurity could not be disabled."
        ) from exc

    try:
        yield
    finally:
        try:
            app.AutomationSecurity = previous
        except Exception as exc:
            raise ComSessionError(
                "PowerPoint AutomationSecurity could not be restored."
            ) from exc
