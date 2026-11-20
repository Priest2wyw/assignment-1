"""Run explicitly with pytest; leaves assignment tests untouched."""
import json

import pytest

from artifact_viewer import list_files, read_artifact


def test_lists_nested_json_only(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested/run.json").write_text('{"compactions": []}')
    (tmp_path / "secret.env").write_text("private")
    assert [item["name"] for item in list_files(tmp_path)] == ["nested/run.json"]


def test_reads_arbitrary_json(tmp_path):
    (tmp_path / "run.json").write_text('{"other": [1, "中文"]}')
    assert read_artifact(tmp_path, "run.json") == {"other": [1, "中文"]}


@pytest.mark.parametrize("name", ["../outside.json", "/etc/passwd", "secret.env"])
def test_rejects_paths_outside_json_scope(tmp_path, name):
    with pytest.raises(ValueError):
        read_artifact(tmp_path, name)


def test_rejects_external_symlink(tmp_path):
    root = tmp_path / "artifacts"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    (root / "link.json").symlink_to(outside)
    assert list_files(root) == []
    with pytest.raises(ValueError):
        read_artifact(root, "link.json")


def test_reports_invalid_json(tmp_path):
    (tmp_path / "run.json").write_text('{"incomplete":')
    with pytest.raises(json.JSONDecodeError):
        read_artifact(tmp_path, "run.json")
