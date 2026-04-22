"""Path traversal defense — covers _resolve_path and its integration with file tools."""
import pytest

import server


# ---------- _resolve_path unit tests ----------

def test_resolves_simple_relative(data_root):
    assert server._resolve_path("foo.md") == data_root / "foo.md"


def test_resolves_nested_path(data_root):
    nested = "modules/personal-os/state/goals.md"
    assert server._resolve_path(nested) == data_root / nested


def test_rejects_absolute(data_root):
    with pytest.raises(server.InvalidPath):
        server._resolve_path("/etc/passwd")


def test_rejects_empty(data_root):
    with pytest.raises(server.InvalidPath):
        server._resolve_path("")


def test_rejects_leading_dotdot(data_root):
    with pytest.raises(server.InvalidPath):
        server._resolve_path("../evil")


def test_rejects_embedded_dotdot(data_root):
    with pytest.raises(server.InvalidPath):
        server._resolve_path("foo/../../etc")


def test_rejects_symlink_escaping_root(data_root, tmp_path):
    outside = tmp_path.parent / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    link = data_root / "link.md"
    link.symlink_to(outside)

    with pytest.raises(server.PathOutsideRoot):
        server._resolve_path("link.md")


# ---------- Integration: every path-taking tool enforces the defense ----------

ESCAPE_ATTEMPTS = [
    ("/etc/passwd", server.InvalidPath),
    ("", server.InvalidPath),
    ("../outside", server.InvalidPath),
    ("a/b/../../../etc", server.InvalidPath),
]


@pytest.mark.parametrize("bad_path,error", ESCAPE_ATTEMPTS)
def test_read_file_rejects_bad_paths(data_root, bad_path, error):
    with pytest.raises(error):
        server.read_file(bad_path)


@pytest.mark.parametrize("bad_path,error", ESCAPE_ATTEMPTS)
def test_write_file_rejects_bad_paths(data_root, bad_path, error):
    with pytest.raises(error):
        server.write_file(bad_path, "x")


@pytest.mark.parametrize("bad_path,error", ESCAPE_ATTEMPTS)
def test_append_rejects_bad_paths(data_root, bad_path, error):
    with pytest.raises(error):
        server.append_to_file(bad_path, "x")


@pytest.mark.parametrize("bad_path,error", ESCAPE_ATTEMPTS)
def test_list_directory_rejects_bad_paths(data_root, bad_path, error):
    with pytest.raises(error):
        server.list_directory(bad_path)
