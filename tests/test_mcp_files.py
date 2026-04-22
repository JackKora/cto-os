"""Tests for read_file, write_file, append_to_file."""
import pytest

import server


# ---------- read_file ----------

def test_read_file_ok(data_root):
    (data_root / "hello.md").write_text("hello", encoding="utf-8")
    assert server.read_file("hello.md") == "hello"


def test_read_file_utf8_non_ascii(data_root):
    content = "café 🎉 — ünïcödé"
    (data_root / "u.md").write_text(content, encoding="utf-8")
    assert server.read_file("u.md") == content


def test_read_file_missing(data_root):
    with pytest.raises(server.PathNotFound):
        server.read_file("missing.md")


def test_read_file_is_directory(data_root):
    (data_root / "sub").mkdir()
    with pytest.raises(server.PathIsDirectory):
        server.read_file("sub")


def test_read_file_binary(data_root):
    (data_root / "b.bin").write_bytes(b"\xff\xfe\x00\x01")
    with pytest.raises(server.BinaryFileError):
        server.read_file("b.bin")


def test_read_file_empty(data_root):
    (data_root / "empty.md").write_text("", encoding="utf-8")
    assert server.read_file("empty.md") == ""


# ---------- write_file ----------

def test_write_file_creates(data_root):
    result = server.write_file("new.md", "hello")
    assert result == {"chars_written": 5, "created": True}
    assert (data_root / "new.md").read_text(encoding="utf-8") == "hello"


def test_write_file_overwrites(data_root):
    (data_root / "ex.md").write_text("old-content", encoding="utf-8")
    result = server.write_file("ex.md", "new")
    assert result == {"chars_written": 3, "created": False}
    assert (data_root / "ex.md").read_text(encoding="utf-8") == "new"


def test_write_file_counts_chars_not_bytes(data_root):
    # "🎉" is 1 Unicode code point but 4 bytes in UTF-8.
    result = server.write_file("e.md", "🎉")
    assert result["chars_written"] == 1
    assert (data_root / "e.md").read_bytes() == "🎉".encode("utf-8")


def test_write_file_auto_creates_parents(data_root):
    server.write_file("deep/nested/file.md", "x")
    assert (data_root / "deep" / "nested" / "file.md").read_text(encoding="utf-8") == "x"


def test_write_file_rejects_directory(data_root):
    (data_root / "d").mkdir()
    with pytest.raises(server.PathIsDirectory):
        server.write_file("d", "x")


def test_write_file_empty_content(data_root):
    result = server.write_file("empty.md", "")
    assert result == {"chars_written": 0, "created": True}
    assert (data_root / "empty.md").read_text(encoding="utf-8") == ""


# ---------- append_to_file ----------

def test_append_creates_missing(data_root):
    result = server.append_to_file("new.md", "one")
    assert result == {"chars_written": 3, "created": True}
    assert (data_root / "new.md").read_text(encoding="utf-8") == "one"


def test_append_to_existing(data_root):
    (data_root / "ex.md").write_text("one", encoding="utf-8")
    result = server.append_to_file("ex.md", "two")
    assert result == {"chars_written": 3, "created": False}
    assert (data_root / "ex.md").read_text(encoding="utf-8") == "onetwo"


def test_append_no_auto_newline(data_root):
    server.append_to_file("f.md", "a")
    server.append_to_file("f.md", "b")
    assert (data_root / "f.md").read_text(encoding="utf-8") == "ab"


def test_append_caller_controls_separator(data_root):
    server.append_to_file("f.md", "a\n")
    server.append_to_file("f.md", "b\n")
    assert (data_root / "f.md").read_text(encoding="utf-8") == "a\nb\n"


def test_append_auto_creates_parents(data_root):
    server.append_to_file("deep/nested.md", "x")
    assert (data_root / "deep" / "nested.md").read_text(encoding="utf-8") == "x"


def test_append_counts_chars_not_bytes(data_root):
    result = server.append_to_file("e.md", "café")
    # "café" is 4 code points, 5 bytes in UTF-8.
    assert result["chars_written"] == 4


# ---------- allow_create=False ----------

def test_append_allow_create_false_missing(data_root):
    with pytest.raises(server.PathNotFound):
        server.append_to_file("no-such-file.md", "x", allow_create=False)


def test_append_allow_create_false_existing(data_root):
    (data_root / "ex.md").write_text("one", encoding="utf-8")
    result = server.append_to_file("ex.md", "two", allow_create=False)
    assert result == {"chars_written": 3, "created": False}
    assert (data_root / "ex.md").read_text(encoding="utf-8") == "onetwo"


# ---------- Forbidden-prefix writes ----------

FORBIDDEN_WRITE_PATHS = [
    ".git/HEAD",
    ".git/config",
    "logs/mcp.log",
    "integrations-cache/slack/foo.md",
]


@pytest.mark.parametrize("bad_path", FORBIDDEN_WRITE_PATHS)
def test_write_file_rejects_forbidden_prefixes(data_root, bad_path):
    with pytest.raises(server.ForbiddenPath):
        server.write_file(bad_path, "x")


@pytest.mark.parametrize("bad_path", FORBIDDEN_WRITE_PATHS)
def test_append_file_rejects_forbidden_prefixes(data_root, bad_path):
    with pytest.raises(server.ForbiddenPath):
        server.append_to_file(bad_path, "x")


def test_write_file_rejects_root_itself(data_root):
    with pytest.raises(server.ForbiddenPath):
        # Resolves to DATA_ROOT itself — not a file.
        server.write_file(".", "x")


def test_read_file_allowed_on_forbidden_write_prefix(data_root):
    # Writes are forbidden, but reads are not.
    log_dir = data_root / "logs"
    log_dir.mkdir()
    (log_dir / "mcp.log").write_text("entry\n", encoding="utf-8")
    assert server.read_file("logs/mcp.log") == "entry\n"
