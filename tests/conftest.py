"""Shared pytest fixtures for MCP server tests."""
from __future__ import annotations

import logging

import pytest

import server


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    """Point `server.DATA_ROOT` at a fresh tmp directory. Silences real logging."""
    # Attach a NullHandler so handlers don't spam test output or try to create logs/
    logging.getLogger().addHandler(logging.NullHandler())

    resolved = tmp_path.resolve()
    monkeypatch.setattr(server, "DATA_ROOT", resolved)
    return resolved


@pytest.fixture
def scripts_dir(tmp_path, monkeypatch):
    """Point `server.SCRIPT_DIR` at a fresh tmp scripts/ dir."""
    d = tmp_path / "scripts"
    d.mkdir(exist_ok=True)
    monkeypatch.setattr(server, "SCRIPT_DIR", d)
    return d
