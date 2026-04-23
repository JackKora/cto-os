"""Tests for list_directory."""
import pytest

import server


def test_list_empty_dir(data_root):
    assert server.list_directory(".") == []


def test_list_files_and_dirs_sorted(data_root):
    (data_root / "b.md").write_text("yy", encoding="utf-8")
    (data_root / "a.md").write_text("x", encoding="utf-8")
    (data_root / "sub").mkdir()

    entries = server.list_directory(".")
    names = [e["name"] for e in entries]
    assert names == ["a.md", "b.md", "sub"]


def test_list_file_entries_include_size_and_mtime(data_root):
    (data_root / "a.md").write_text("hello", encoding="utf-8")
    [entry] = server.list_directory(".")

    assert entry["name"] == "a.md"
    assert entry["type"] == "file"
    assert entry["size"] == 5
    assert entry["mtime"].endswith("Z")
    # Basic shape check — full ISO-8601 UTC "YYYY-MM-DDTHH:MM:SSZ" is 20 chars
    assert len(entry["mtime"]) == 20


def test_list_dir_entries_have_no_size(data_root):
    (data_root / "sub").mkdir()
    [entry] = server.list_directory(".")
    assert entry["type"] == "directory"
    assert "size" not in entry
    assert "mtime" in entry


def test_list_recursive(data_root):
    (data_root / "a.md").write_text("x", encoding="utf-8")
    (data_root / "sub").mkdir()
    (data_root / "sub" / "b.md").write_text("y", encoding="utf-8")
    (data_root / "sub" / "nested").mkdir()
    (data_root / "sub" / "nested" / "c.md").write_text("z", encoding="utf-8")

    entries = server.list_directory(".", recursive=True)
    names = {e["name"] for e in entries}
    assert "a.md" in names
    assert "sub" in names
    assert "sub/b.md" in names
    assert "sub/nested" in names
    assert "sub/nested/c.md" in names


def test_list_missing(data_root):
    with pytest.raises(server.PathNotFound):
        server.list_directory("no/such/thing")


def test_list_on_file_errors(data_root):
    (data_root / "f.md").write_text("x", encoding="utf-8")
    with pytest.raises(server.PathIsFile):
        server.list_directory("f.md")


def test_list_omits_escaping_symlinks(data_root, tmp_path):
    outside = tmp_path.parent / "outside.md"
    outside.write_text("secret", encoding="utf-8")

    (data_root / "link.md").symlink_to(outside)
    (data_root / "regular.md").write_text("here", encoding="utf-8")

    names = {e["name"] for e in server.list_directory(".")}
    assert "regular.md" in names
    assert "link.md" not in names


def test_list_includes_dotfiles(data_root):
    (data_root / ".hidden").write_text("x", encoding="utf-8")
    (data_root / "visible.md").write_text("x", encoding="utf-8")

    names = {e["name"] for e in server.list_directory(".")}
    assert ".hidden" in names
    assert "visible.md" in names


def test_list_subdirectory_path(data_root):
    (data_root / "sub").mkdir()
    (data_root / "sub" / "file.md").write_text("x", encoding="utf-8")

    entries = server.list_directory("sub")
    assert [e["name"] for e in entries] == ["file.md"]
