import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("artifact", ["openapi.json", "api.ts"])
def test_contract_drift_fails_without_rewriting(artifact: str, tmp_path: Path) -> None:
    for name in ("openapi.json", "api.ts"):
        (tmp_path / name).write_bytes((ROOT / "frontend/src/generated" / name).read_bytes())
    target = tmp_path / artifact
    target.write_bytes(target.read_bytes() + b"\n")
    before = target.read_bytes()
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_contract.py"), "--output-dir", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert artifact in result.stderr
    assert target.read_bytes() == before


def test_matching_contract_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_contract.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("suite, count", [("offline", 2), ("unit", 1), ("integration", 1)])
def test_live_is_excluded_and_suites_select_real_tests(
    suite: str, count: int, tmp_path: Path
) -> None:
    source = tmp_path / "test_synthetic_suites.py"
    source.write_text(
        "import pytest\n"
        "def test_unit(): assert True\n"
        "@pytest.mark.integration\n"
        "def test_integration(): assert True\n"
        "@pytest.mark.live\n"
        "def test_live(): raise AssertionError('paid suite must not execute')\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "tests.conftest",
            str(source),
            "--suite",
            suite,
            "--basetemp",
            str(tmp_path / "missing-parent" / "child-temp"),
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"{count} passed" in result.stdout


def test_missing_generated_artifacts_fail(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_contract.py"), "--output-dir", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "openapi.json" in result.stderr and "api.ts" in result.stderr


def test_lint_failure_returns_nonzero(tmp_path: Path) -> None:
    source = tmp_path / "synthetic_bad.py"
    source.write_text("import unused_synthetic\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "F401" in result.stdout


def test_workflow_is_fail_closed_and_has_no_live_provider_job() -> None:
    # BaseLoader preserves GitHub's `on` key rather than treating it as YAML 1.1 true.
    workflow = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    assert workflow["permissions"] == {"contents": "read"}
    steps = workflow["jobs"]["quality"]["steps"]
    for step in steps:
        assert "continue-on-error" not in step
        if "uses" in step:
            assert len(step["uses"].split("@")[1]) == 40
    gates = next(
        step["run"]
        for step in steps
        if step.get("name") == "Run fail-fast gates without external networking"
    )
    assert "sudo --preserve-env=HOME unshare --net" in gates
    assert "--bounding-set=-all --no-new-privs" in gates
    assert "--suite unit" in gates and "--suite integration" in gates
    assert "scripts/check_contract.py" in gates
    assert 'BB_TEST_DB_URL="$6"' in gates
    assert '${BB_TEST_DB_URL:?PostgreSQL test DSN must be configured}' in gates
    assert "--suite live" not in json.dumps(workflow)
    assert "secrets." not in json.dumps(workflow)
    database = next(
        step["run"]
        for step in steps
        if step.get("name") == "Start isolated PostgreSQL 17 for integration gates"
    )
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
    assert compose["services"]["postgres"]["image"] in database
    assert "--network none" in database and "listen_addresses=" in database
    assert "--publish" not in database and "--network host" not in database
    assert "target=/var/run/postgresql" in database
    assert "BB_TEST_DB_URL=" in database and "?host=%s" in database
    cleanup = next(step for step in steps if step.get("name") == "Remove isolated PostgreSQL")
    assert cleanup["if"] == "always()"
    assert "docker rm --force --volumes bb-ci-postgres" in cleanup["run"]
