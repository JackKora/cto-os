"""Subprocess contract tests for the narrow read-only state validator."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate_state.py"


def _run(root: Path, args: dict | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), "--args", json.dumps(args or {})], capture_output=True, text=True, env={**os.environ, "CTO_OS_DATA": str(root)})


def _module(root: Path, *, extra: str = "", sensitivity: str = "") -> Path:
    state = root / "modules" / "test" / "state"
    state.mkdir(parents=True)
    (state.parent / "_module.md").write_text("---\ntype: _module\nslug: test\nmodule: test\nupdated: 2026-01-01\nschema_version: 1\nactive: true\nactivated_at: 2026-01-01\ndeactivated_at: null\n" + sensitivity + "---\n", encoding="utf-8")
    return state


def _record(state: Path, content: str) -> None:
    (state / "record.md").write_text(content, encoding="utf-8")


def _report(result: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(result.stdout)


def test_clean_state(tmp_path: Path) -> None:
    state = _module(tmp_path)
    _record(state, "---\ntype: team\nslug: platform\nupdated: 2026-01-01\n---\n")
    result = _run(tmp_path)
    assert result.returncode == 0
    assert _report(result)["summary"]["finding_count"] == 0


def test_frontmatter_and_baseline_findings(tmp_path: Path) -> None:
    state = _module(tmp_path)
    _record(state, "no frontmatter")
    result = _run(tmp_path)
    assert result.returncode == 1
    assert _report(result)["findings"][0]["code"] == "invalid_frontmatter"
    _record(state, "---\ntype: [bad\n---\n")
    assert _report(_run(tmp_path))["findings"][0]["code"] == "invalid_frontmatter"
    _record(state, "---\n- not-map\n---\n")
    assert _report(_run(tmp_path))["findings"][0]["code"] == "invalid_frontmatter"
    _record(state, "---\ntype: team\n---\n")
    report = _report(_run(tmp_path))
    assert {f["field"] for f in report["findings"] if f["code"] == "missing_field"} == {"slug", "updated"}


def test_dates_types_module_and_diagnosed_fields(tmp_path: Path) -> None:
    state = _module(tmp_path)
    (state.parent / "_module.md").write_text("---\ntype: wrong\nslug: other\nmodule: no\nupdated: no\nschema_version: nope\nactive: yes\nactivated_at: yesterday\ndeactivated_at: nope\n---\n", encoding="utf-8")
    _record(state, "---\ntype: requisition\nslug: req\nupdated: 2026-01-01\nopened: prose\n---\n")
    report = _report(_run(tmp_path, {"include_high_sensitivity": True}))
    assert any(f["field"] == "opened" for f in report["findings"])
    assert any(f["field"] == "schema_version" for f in report["findings"])
    _record(state, "---\ntype: stakeholder-profile\nslug: person\nupdated: 2026-01-01\ntenure_months: '12'\n---\n")
    report = _report(_run(tmp_path, {"include_high_sensitivity": True}))
    assert any(f["field"] == "tenure_months" for f in report["findings"])


def test_unknown_type_and_sensitive_hiding(tmp_path: Path) -> None:
    state = _module(tmp_path, sensitivity="sensitivity: high\n")
    _record(state, "---\ntype: imaginary\nslug: bad\nupdated: nope\n---\n")
    hidden = _report(_run(tmp_path))
    assert hidden["summary"]["skipped_high_sensitivity_count"] == 2
    strict = _report(_run(tmp_path, {"include_high_sensitivity": True}))
    assert any(f["code"] == "unknown_type" for f in strict["findings"])


def test_missing_module_metadata_fails_closed_for_sensitivity(tmp_path: Path) -> None:
    state = tmp_path / "modules" / "unclassified" / "state"
    state.mkdir(parents=True)
    _record(state, "---\ntype: team\nslug: hidden-team\nupdated: 2026-01-01\n---\n")

    hidden_result = _run(tmp_path)
    assert hidden_result.returncode == 1
    hidden = _report(hidden_result)
    assert hidden["findings"] == []
    assert hidden["summary"]["hidden_error_count"] == 1
    assert hidden["summary"]["skipped_high_sensitivity_count"] == 1
    assert "modules/unclassified" not in json.dumps(hidden)

    strict_result = _run(tmp_path, {"include_high_sensitivity": True})
    assert strict_result.returncode == 1
    strict = _report(strict_result)
    assert strict["findings"] == [{
        "path": "modules/unclassified/_module.md",
        "code": "missing_module_metadata",
        "message": "required module metadata is missing",
    }]


@pytest.mark.parametrize(
    "content",
    [
        "---\n  sensitivity :  high # private\n  type: [bad\n---\n",
        "---\nsensitivity: \"high\"\ntype: [bad\n---\n",
        "---\nsensitivity: 'high'\ntype: [bad\n---\n",
        "---\r\nsensitivity: high # private\r\ntype: [bad\r\n",
    ],
)
def test_malformed_high_sensitivity_hides_details(tmp_path: Path, content: str) -> None:
    state = _module(tmp_path)
    _record(state, content)

    hidden = _report(_run(tmp_path))
    assert hidden["findings"] == []
    assert hidden["summary"]["hidden_error_count"] == 1
    assert "modules/test/state/record.md" not in json.dumps(hidden)

    strict = _report(_run(tmp_path, {"include_high_sensitivity": True}))
    assert strict["findings"][0]["path"] == "modules/test/state/record.md"
    assert strict["findings"][0]["code"] == "invalid_frontmatter"


def test_sensitivity_line_in_body_does_not_hide_malformed_header(tmp_path: Path) -> None:
    state = _module(tmp_path)
    _record(state, "---\ntype: [bad\n---\nsensitivity: high\n")

    result = _report(_run(tmp_path))
    assert result["summary"]["hidden_error_count"] == 0
    assert result["findings"][0]["path"] == "modules/test/state/record.md"
    assert result["findings"][0]["code"] == "invalid_frontmatter"


def test_bad_args_and_missing_env(tmp_path: Path) -> None:
    bad = _run(tmp_path, {"include_high_sensitivity": "yes"})
    assert bad.returncode == 2
    env = {k: v for k, v in os.environ.items() if k != "CTO_OS_DATA"}
    missing = subprocess.run([sys.executable, str(SCRIPT), "--args", "{}"], capture_output=True, text=True, env=env)
    assert missing.returncode == 2
