import os

import pytest

from handoff.core import admin
from handoff.services.container.docker import impl


IMAGE_FILE = os.path.join("images", "my-image", "0.1", "image.yml")
IMAGE_YML = """installs:
- venv: proc_01
  command: pip install foo
- venv: proc_02
  command: pip install bar
"""


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _make_project(root, installs):
    project_dir = os.path.join(root, "projects", "my_project")
    _write(os.path.join(project_dir, "project.yml"),
           "installs:\n" + installs)
    return project_dir


def _installed(monkeypatch, project_dir, workspace_dir):
    installed = list()
    monkeypatch.setattr(admin, "_make_python_venv", lambda venv: None)
    monkeypatch.setattr(admin, "_install",
                        lambda command, venv: installed.append((venv, command)))
    os.makedirs(workspace_dir, exist_ok=True)
    admin.workspace_install(project_dir, workspace_dir)
    return installed


def test_workspace_install_expands_file_in_place(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project_dir = _make_project(str(tmp_path), (
        "- command: echo before\n"
        f"- file: {IMAGE_FILE}\n"
        "- command: echo after\n"))
    _write(os.path.join(project_dir, IMAGE_FILE), IMAGE_YML)

    assert _installed(monkeypatch, project_dir, str(tmp_path / "ws")) == [
        (None, "echo before"),
        ("proc_01", "pip install foo"),
        ("proc_02", "pip install bar"),
        (None, "echo after"),
    ]


def test_workspace_install_with_relative_project_dir(tmp_path, monkeypatch):
    project_dir = _make_project(str(tmp_path), f"- file: {IMAGE_FILE}\n")
    _write(str(tmp_path / IMAGE_FILE), IMAGE_YML)
    monkeypatch.chdir(tmp_path)

    installed = _installed(monkeypatch, os.path.relpath(project_dir), "ws")

    assert ("proc_01", "pip install foo") in installed


def test_inline_installs_unchanged():
    installs = [{"venv": "tap", "command": "pip install foo"}]
    assert admin._expand_installs("unused", installs) == installs


def test_resolve_prefers_nearest_file(tmp_path):
    project_dir = _make_project(str(tmp_path), "")
    shared = str(tmp_path / IMAGE_FILE)
    _write(shared, IMAGE_YML)
    assert admin._resolve_install_file(project_dir, IMAGE_FILE) == shared

    local = os.path.join(project_dir, IMAGE_FILE)
    _write(local, IMAGE_YML)
    assert admin._resolve_install_file(project_dir, IMAGE_FILE) == local


@pytest.mark.parametrize("file_ref, error", [
    ("/etc/image.yml", "relative path"),
    ("../image.yml", "relative path"),
    ("images/../../image.yml", "relative path"),
    (".secrets/image.yml", "kept out of container bundles"),
    ("images/image.secret.yml", "kept out of container bundles"),
    ("images/missing.yml", "is not found"),
])
def test_resolve_rejects(tmp_path, file_ref, error):
    project_dir = _make_project(str(tmp_path), "")
    with pytest.raises(Exception, match=error):
        admin._resolve_install_file(project_dir, file_ref)


@pytest.mark.parametrize("content", [
    "",
    "- command: pip install foo\n",
    "installs: pip install foo\n",
    "installs:\n- venv: proc_01\n",
    "installs:\n- file: other.yml\n",
])
def test_invalid_install_file(tmp_path, content):
    project_dir = _make_project(str(tmp_path), "")
    _write(os.path.join(project_dir, IMAGE_FILE), content)
    with pytest.raises(Exception, match="image.yml"):
        admin._read_install_file(project_dir, IMAGE_FILE)


@pytest.mark.parametrize("install", [
    {"file": None},
    {"file": IMAGE_FILE, "venv": "proc_01"},
    {"file": IMAGE_FILE, "command": "pip install foo"},
])
def test_invalid_file_entry(tmp_path, install):
    project_dir = _make_project(str(tmp_path), "")
    _write(os.path.join(project_dir, IMAGE_FILE), IMAGE_YML)
    with pytest.raises(Exception, match="cannot have other keys"):
        admin._expand_installs(project_dir, [install])


def test_project_schema_accepts_file():
    admin._validate_project({"installs": [{"file": IMAGE_FILE}]})


def test_bundle_copies_file_from_above_project(tmp_path, monkeypatch):
    project_dir = _make_project(str(tmp_path), f"- file: {IMAGE_FILE}\n")
    _write(str(tmp_path / IMAGE_FILE), IMAGE_YML)
    build_dir = str(tmp_path / "build")
    os.mkdir(build_dir)

    impl.copy_files(project_dir, build_dir)

    bundled_project = os.path.join(build_dir, "project")
    with open(os.path.join(bundled_project, IMAGE_FILE)) as f:
        assert f.read() == IMAGE_YML
    # What the image's own `handoff workspace install` will run
    monkeypatch.chdir(build_dir)
    installed = _installed(monkeypatch, "project", "workspace")
    assert ("proc_02", "pip install bar") in installed


def test_bundle_keeps_file_inside_project(tmp_path):
    project_dir = _make_project(str(tmp_path), f"- file: {IMAGE_FILE}\n")
    _write(os.path.join(project_dir, IMAGE_FILE), IMAGE_YML)
    build_dir = str(tmp_path / "build")
    os.mkdir(build_dir)

    impl.copy_files(project_dir, build_dir)

    assert os.path.isfile(os.path.join(build_dir, "project", IMAGE_FILE))


def test_bundle_fails_on_missing_file(tmp_path):
    project_dir = _make_project(str(tmp_path), f"- file: {IMAGE_FILE}\n")
    build_dir = str(tmp_path / "build")
    os.mkdir(build_dir)

    with pytest.raises(Exception, match="is not found"):
        impl.copy_files(project_dir, build_dir)
