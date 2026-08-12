from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_window_pptx_v61_codex_acceptance as controller  # noqa: E402
import build_window_pptx_v61_runtime_identity as runtime_builder  # noqa: E402
from validate_window_pptx_v61_clean_pack import tree_fingerprint  # noqa: E402
from window_pptx.v61_runtime_identity import (  # noqa: E402
    RuntimeIdentityError,
    build_runtime_identity_payload,
    read_runtime_identity_manifest,
    verify_runtime_identity_payload,
    write_runtime_identity_manifest,
)


def _installed_fixture(tmp_path: Path) -> Path:
    installed = tmp_path / "codex-home" / "skills" / "window-pptx"
    entry = installed / "scripts" / "run_window_pptx_v61_codex_acceptance.py"
    entry.parent.mkdir(parents=True)
    entry.write_text("VALUE = 1\n", encoding="utf-8")
    (installed / "SKILL.md").write_text("# fixture\n", encoding="utf-8")
    return installed.resolve()


def _payload(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    installed = _installed_fixture(tmp_path)
    payload = build_runtime_identity_payload(
        installed_skill_root=installed,
        expected_installed_skill_sha256="a" * 64,
        controller_interpreter=Path(sys.executable).resolve(),
        codex_native_executable=Path(sys.executable).resolve(),
    )
    return installed, payload


def test_runtime_identity_schema_is_valid_and_payload_conforms(tmp_path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SKILL_ROOT / "schemas" / "codex-runtime-identity-manifest.v1.schema.json")
        .read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    _, payload = _payload(tmp_path)
    jsonschema.Draft202012Validator(schema).validate(payload)
    assert payload["launch_mode"] == "native-codex-direct"
    assert payload["codex"]["native_executable"]["binary_format"] in {
        "elf",
        "pe",
        "mach-o",
    }


def test_external_expected_sha_freezes_manifest_bytes(tmp_path: Path) -> None:
    _, payload = _payload(tmp_path)
    target = tmp_path / "external-runtime-identity.v1.json"
    record = write_runtime_identity_manifest(target, payload)
    manifest, raw, loaded = read_runtime_identity_manifest(target, record["sha256"])
    assert manifest == target.resolve()
    assert hashlib.sha256(raw).hexdigest() == record["sha256"]
    assert loaded == payload

    target.write_bytes(raw + b" ")
    with pytest.raises(RuntimeIdentityError, match="SHA256_MISMATCH"):
        read_runtime_identity_manifest(target, record["sha256"])


def test_component_bytes_are_rechecked_after_freeze(tmp_path: Path) -> None:
    installed, payload = _payload(tmp_path)
    entry = installed / "scripts" / "run_window_pptx_v61_codex_acceptance.py"
    verified = verify_runtime_identity_payload(
        payload,
        installed_skill_root=installed,
        expected_installed_skill_sha256="a" * 64,
        actual_controller_entry=entry,
        production=True,
    )
    assert verified["codex_native_executable"] == Path(sys.executable).resolve()

    entry.write_text("VALUE = 2\n", encoding="utf-8")
    with pytest.raises(RuntimeIdentityError, match="CONTROLLER_ENTRY_SHA256_MISMATCH"):
        verify_runtime_identity_payload(
            payload,
            installed_skill_root=installed,
            expected_installed_skill_sha256="a" * 64,
            actual_controller_entry=entry,
            production=True,
        )


def test_production_controller_origin_must_equal_installed_entry(tmp_path: Path) -> None:
    installed, payload = _payload(tmp_path)
    with pytest.raises(RuntimeIdentityError, match="CONTROLLER_NOT_RUNNING"):
        verify_runtime_identity_payload(
            payload,
            installed_skill_root=installed,
            expected_installed_skill_sha256="a" * 64,
            actual_controller_entry=Path(controller.__file__).resolve(),
            production=True,
        )
    with pytest.raises(
        controller.AcceptanceControllerError,
        match="CONTROLLER_NOT_RUNNING_FROM_INSTALLED_SKILL",
    ):
        controller._require_installed_controller_origin(installed, test_bypass=False)


def test_production_runtime_paths_cannot_be_path_lookups(tmp_path: Path) -> None:
    installed = _installed_fixture(tmp_path)
    with pytest.raises(RuntimeIdentityError, match="ABSOLUTE_PATH_REQUIRED"):
        build_runtime_identity_payload(
            installed_skill_root=installed,
            expected_installed_skill_sha256="a" * 64,
            controller_interpreter=Path(sys.executable).resolve(),
            codex_native_executable=Path("codex"),
        )


def test_cli_requires_external_runtime_manifest_and_exposes_no_test_bypass() -> None:
    parser = controller._parser()
    destinations = {action.dest for action in parser._actions}
    assert "runtime_identity_manifest" in destinations
    assert "expected_runtime_identity_manifest_sha256" in destinations
    assert "codex_bin" not in destinations
    assert "allow_test_codex" not in destinations
    required = {action.dest for action in parser._actions if action.required}
    assert {
        "runtime_identity_manifest",
        "expected_runtime_identity_manifest_sha256",
    }.issubset(required)


def test_programmatic_test_bypass_is_rejected_outside_pytest_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    with pytest.raises(
        controller.AcceptanceControllerError,
        match="TEST_CODEX_BYPASS_FORBIDDEN_OUTSIDE_PYTEST",
    ):
        controller.run_acceptance(
            project_root=tmp_path,
            installed_skill_root=tmp_path,
            private_root=tmp_path,
            harness_dir=tmp_path / "harness",
            allow_test_codex=True,
        )


def test_native_codex_requirement_rejects_script_in_production(tmp_path: Path) -> None:
    installed = _installed_fixture(tmp_path)
    script = tmp_path / "codex-script"
    script.write_text("#!/bin/sh\nprintf 'codex-cli fake\\n'\n", encoding="utf-8")
    script.chmod(0o755)
    with pytest.raises(RuntimeIdentityError, match="FORMAT_INVALID"):
        build_runtime_identity_payload(
            installed_skill_root=installed,
            expected_installed_skill_sha256="a" * 64,
            controller_interpreter=Path(sys.executable).resolve(),
            codex_native_executable=script.resolve(),
        )


def test_manifest_writer_refuses_overwrite(tmp_path: Path) -> None:
    _, payload = _payload(tmp_path)
    target = tmp_path / "runtime.json"
    write_runtime_identity_manifest(target, payload)
    with pytest.raises(RuntimeIdentityError, match="ALREADY_EXISTS"):
        write_runtime_identity_manifest(target, payload)


def test_builder_cli_emits_external_freeze_receipt(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    installed = _installed_fixture(tmp_path)
    installed_sha = tree_fingerprint(installed)["sha256"]
    output = (tmp_path / "external" / "runtime-identity.v1.json").resolve()
    code = runtime_builder.main(
        [
            "--installed-skill-root",
            str(installed),
            "--expected-installed-skill-sha256",
            str(installed_sha),
            "--codex-native-executable",
            str(Path(sys.executable).resolve()),
            "--output",
            str(output),
        ]
    )
    receipt = json.loads(capsys.readouterr().out)
    assert code == 0
    assert receipt["status"] == "FROZEN"
    assert receipt["runtime_identity_manifest"]["path"] == str(output)
    assert receipt["expected_runtime_identity_manifest_sha256"] == hashlib.sha256(
        output.read_bytes()
    ).hexdigest()
