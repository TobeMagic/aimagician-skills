from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "skills"
    / "owned"
    / "window-pptx"
    / "scripts"
    / "check_window_pptx_private_assets.py"
)
spec = importlib.util.spec_from_file_location("window_pptx_private_guard", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "guard@example.invalid")
    _git(root, "config", "user.name", "Window PPTX Guard")
    tracked = root / "README.md"
    tracked.write_text("safe\n", encoding="utf-8")
    _git(root, "add", "--", "README.md")
    _git(root, "commit", "-qm", "seed")
    return root


def test_private_and_cookie_paths_are_rejected() -> None:
    assert module.private_path_reason(
        Path("skills/owned/window-pptx/.private/secrets/gaojie.cookies")
    ) == "PRIVATE_PATH"
    assert module.private_path_reason(Path("secrets/session.txt")) == "SECRET_PATH"
    assert module.private_path_reason(Path("scripts/safe.py")) is None


def test_secret_payload_is_reported_without_exposing_the_value() -> None:
    secret = "sensitive-session-value-0123456789"
    findings = module.inspect_payload(
        Path("config.txt"),
        f'PHPSESSID="{secret}"'.encode(),
        is_new=True,
    )

    assert [finding.code for finding in findings] == ["SECRET_LITERAL"]
    serialized = json.dumps([finding.to_dict() for finding in findings])
    assert secret not in serialized


def test_new_binary_is_rejected_but_safe_source_is_allowed() -> None:
    binary = module.inspect_payload(
        Path("download/template.pptx"),
        b"PK\x03\x04\x00\x00",
        is_new=True,
    )
    source = module.inspect_payload(
        Path("scripts/safe.py"),
        b'print("safe")\n',
        is_new=True,
    )

    assert [finding.code for finding in binary] == ["UNAPPROVED_BINARY"]
    assert source == ()


def test_staged_guard_fails_closed_without_printing_cookie(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    fixture_value = "private-cookie-value-0123456789"
    private = (
        root
        / "skills"
        / "owned"
        / "window-pptx"
        / ".private"
        / "secrets"
        / "gaojie.cookies"
    )
    private.parent.mkdir(parents=True)
    private.write_text(f"PHPSESSID={fixture_value}\n", encoding="utf-8")
    _git(root, "add", "--", str(private.relative_to(root)))

    report = module.inspect_staged_repository(root)

    assert report.status == "FAIL"
    assert {finding.code for finding in report.findings} == {
        "PRIVATE_PATH",
        "SECRET_LITERAL",
    }
    serialized = json.dumps(report.to_dict())
    assert fixture_value not in serialized

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--staged",
            "--repo-root",
            str(root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["status"] == "FAIL"
    assert fixture_value not in completed.stdout
    assert fixture_value not in completed.stderr


def test_guard_error_output_does_not_echo_repository_details(
    tmp_path: Path,
) -> None:
    sensitive_fragment = "private-value-that-must-not-echo"
    missing = tmp_path / sensitive_fragment

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--staged",
            "--repo-root",
            str(missing),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    report = json.loads(completed.stdout)
    assert report["status"] == "ERROR"
    assert report["findings"][0]["detail"] == "staged-index inspection failed closed"
    assert sensitive_fragment not in completed.stdout
    assert sensitive_fragment not in completed.stderr


def test_staged_guard_passes_for_safe_text_change(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    source = root / "skills" / "owned" / "window-pptx" / "scripts" / "safe.py"
    source.parent.mkdir(parents=True)
    source.write_text('print("safe")\n', encoding="utf-8")
    _git(root, "add", "--", str(source.relative_to(root)))

    report = module.inspect_staged_repository(root)

    assert report.status == "PASS"
    assert report.findings == ()
