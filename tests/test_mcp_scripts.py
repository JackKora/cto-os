"""Tests for run_script and scan (which proxies to scripts/scan.py)."""
import json

import pytest

import server


def _write_script(scripts_dir, name: str, body: str) -> None:
    """Write a script file that's executable via `python script.py --args '<json>'`."""
    (scripts_dir / f"{name}.py").write_text(body, encoding="utf-8")


# ---------- run_script: whitelist enforcement ----------

def test_run_script_whitelisted_runs(data_root, scripts_dir):
    _write_script(
        scripts_dir,
        "roll_up",
        "import json, sys\n"
        "args = json.loads(sys.argv[2])\n"
        "print(json.dumps({'got': args}))\n",
    )
    result = server.run_script("roll_up", {"x": 1})
    assert result["exit_code"] == 0
    assert json.loads(result["stdout"]) == {"got": {"x": 1}}


def test_run_script_refuses_scan(data_root, scripts_dir):
    _write_script(scripts_dir, "scan", "print('should never run')")
    with pytest.raises(server.ScriptNotInWhitelist):
        server.run_script("scan", {})


def test_run_script_refuses_unknown(data_root, scripts_dir):
    _write_script(scripts_dir, "evil", "print('hi')")
    with pytest.raises(server.ScriptNotInWhitelist):
        server.run_script("evil", {})


def test_run_script_refuses_pull_slack(data_root, scripts_dir):
    # Side-effect scripts are deliberately off the Chat whitelist.
    _write_script(scripts_dir, "pull_slack", "print('hi')")
    with pytest.raises(server.ScriptNotInWhitelist):
        server.run_script("pull_slack", {})


# ---------- run_script: file-state errors ----------

def test_run_script_missing_file(data_root, scripts_dir):
    # roll_up is whitelisted but not on disk.
    with pytest.raises(server.ScriptNotFound):
        server.run_script("roll_up", {})


def test_run_script_empty_file(data_root, scripts_dir):
    _write_script(scripts_dir, "roll_up", "")
    with pytest.raises(server.ScriptNotImplemented):
        server.run_script("roll_up", {})


# ---------- run_script: return semantics ----------

def test_run_script_nonzero_exit_does_not_raise(data_root, scripts_dir):
    _write_script(scripts_dir, "roll_up", "import sys; sys.exit(7)")
    result = server.run_script("roll_up", {})
    assert result["exit_code"] == 7


def test_run_script_captures_stdout_and_stderr(data_root, scripts_dir):
    _write_script(
        scripts_dir,
        "roll_up",
        "import sys\n"
        "sys.stdout.write('out')\n"
        "sys.stderr.write('err')\n",
    )
    result = server.run_script("roll_up", {})
    assert result["stdout"] == "out"
    assert result["stderr"] == "err"


def test_run_script_timeout(data_root, scripts_dir, monkeypatch):
    _write_script(scripts_dir, "roll_up", "import time; time.sleep(5)")
    monkeypatch.setattr(server, "SCRIPT_TIMEOUT_SECONDS", 1)
    with pytest.raises(server.ScriptTimeout):
        server.run_script("roll_up", {})


# ---------- scan ----------

def test_scan_missing_script(data_root, scripts_dir):
    with pytest.raises(server.ScriptNotFound):
        server.scan({})


def test_scan_empty_file(data_root, scripts_dir):
    _write_script(scripts_dir, "scan", "")
    with pytest.raises(server.ScriptNotImplemented):
        server.scan({})


def test_scan_proxies_args_and_parses_json(data_root, scripts_dir):
    _write_script(
        scripts_dir,
        "scan",
        "import json, sys\n"
        "args = json.loads(sys.argv[2])\n"
        "print(json.dumps({'matches': [], 'query': args}))\n",
    )
    result = server.scan({"type": ["team"]})
    assert result == {"matches": [], "query": {"type": ["team"]}}


def test_scan_crash_raises_failed(data_root, scripts_dir):
    # Per docs/MCP_TOOLS.md: non-zero exit from scan.py is only expected on a crash
    # (uncaught exception, OS error). Query errors — bad spec, unknown field — must
    # surface via exit 0 with a structured error envelope in stdout.
    _write_script(
        scripts_dir,
        "scan",
        "import sys; sys.stderr.write('boom'); sys.exit(1)",
    )
    with pytest.raises(server.ScriptFailed):
        server.scan({})


def test_scan_bad_json_raises_failed(data_root, scripts_dir):
    _write_script(scripts_dir, "scan", "print('not valid json')")
    with pytest.raises(server.ScriptFailed):
        server.scan({})
