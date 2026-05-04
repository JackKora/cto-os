"""Tests for the grep MCP tool."""

import pytest

import server


def test_basic_match(data_root):
    (data_root / "notes.md").write_text("hello world\nfoo bar\nhello again\n")
    result = server.grep("hello", path=".")
    assert result["truncated"] is False
    texts = [m["text"] for m in result["matches"]]
    assert "hello world" in texts
    assert "hello again" in texts
    assert "foo bar" not in texts


def test_match_includes_file_and_line(data_root):
    (data_root / "sub").mkdir()
    (data_root / "sub" / "file.md").write_text("line1\ntarget line\nline3\n")
    result = server.grep("target", path=".")
    assert len(result["matches"]) == 1
    m = result["matches"][0]
    assert m["file"] == "sub/file.md"
    assert m["line"] == 2
    assert m["text"] == "target line"


def test_recursive_false_skips_subdirs(data_root):
    (data_root / "top.md").write_text("match here\n")
    (data_root / "sub").mkdir()
    (data_root / "sub" / "nested.md").write_text("match here\n")
    result = server.grep("match", path=".", recursive=False)
    files = {m["file"] for m in result["matches"]}
    assert "top.md" in files
    assert "sub/nested.md" not in files


def test_bad_regex_raises_invalid_pattern(data_root):
    with pytest.raises(server.InvalidPattern):
        server.grep("[invalid", path=".")


def test_binary_file_skipped_silently(data_root):
    (data_root / "text.md").write_text("match me\n")
    (data_root / "binary.bin").write_bytes(b"\x00\x01\x02match\xff\xfe")
    result = server.grep("match", path=".")
    files = {m["file"] for m in result["matches"]}
    assert "text.md" in files
    assert "binary.bin" not in files


def test_max_matches_cap_triggers_truncated(data_root):
    lines = "\n".join(f"match line {i}" for i in range(50))
    (data_root / "big.md").write_text(lines)
    result = server.grep("match", path=".", max_matches=10)
    assert result["truncated"] is True
    assert len(result["matches"]) == 10


def test_no_matches_returns_empty(data_root):
    (data_root / "file.md").write_text("nothing relevant\n")
    result = server.grep("xyzzy_not_present", path=".")
    assert result["matches"] == []
    assert result["truncated"] is False


def test_dotdot_path_rejected(data_root):
    with pytest.raises(server.InvalidPath):
        server.grep("x", path="../outside")


def test_missing_path_raises_path_not_found(data_root):
    with pytest.raises(server.PathNotFound):
        server.grep("x", path="nonexistent")


def test_file_path_raises_path_is_file(data_root):
    (data_root / "file.md").write_text("content\n")
    with pytest.raises(server.PathIsFile):
        server.grep("content", path="file.md")


def test_escaping_symlink_omitted(data_root, tmp_path):
    """A symlink inside DATA_ROOT pointing outside must not leak content via grep."""
    outside = tmp_path.parent / "outside.md"
    outside.write_text("secret password\n", encoding="utf-8")
    (data_root / "link.md").symlink_to(outside)
    (data_root / "regular.md").write_text("regular file with secret\n", encoding="utf-8")

    result = server.grep("secret", path=".")
    files = {m["file"] for m in result["matches"]}
    assert "regular.md" in files
    assert "link.md" not in files
