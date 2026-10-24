import os
import tarfile

import pytest

from handoff.services.container import _tar_filter
from handoff.services.container.docker import impl


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _make_project(root):
    project_dir = os.path.join(root, "project")
    _write(os.path.join(project_dir, "project.yml"), "installs: []\n")
    _write(os.path.join(project_dir, "files", "tap_config.json"),
           '{"api_key": "{{ api_key }}"}')
    _write(os.path.join(project_dir, "scripts", "run.sh"), "echo run")
    # Same rule that drops .secrets/
    _write(os.path.join(project_dir, "files", "sa.secret.json"), "secret")
    _write(os.path.join(project_dir, ".env"), "API_KEY=value")
    _write(os.path.join(project_dir, ".git", "config"), "[remote]")
    _write(os.path.join(project_dir, ".venv", "bin", "python"))
    _write(os.path.join(project_dir, "files", ".aws", "credentials"), "key")
    # Exact-name patterns must not catch these
    _write(os.path.join(project_dir, ".gitignore"), "workspace\n")
    _write(os.path.join(project_dir, "files", ".keep"))
    return project_dir


def _make_workspace(workspace_dir):
    os.makedirs(os.path.join(workspace_dir, "artifacts"))
    _write(os.path.join(workspace_dir, "files", "tap_config.json"),
           '{"api_key": "rendered-value"}')
    _write(os.path.join(workspace_dir, "files", "google_client_secret.json"),
           "rendered-value")
    _write(os.path.join(workspace_dir, "tap", "bin", "python"))


def _copied(build_dir):
    copied = set()
    root = os.path.join(build_dir, "project")
    for dirpath, _, files in os.walk(root):
        for fn in files:
            copied.add(os.path.relpath(os.path.join(dirpath, fn), root))
    return copied


def test_bundle_excludes_workspace_in_project_dir(tmp_path):
    project_dir = _make_project(str(tmp_path))
    _make_workspace(os.path.join(project_dir, "workspace"))
    _make_workspace(os.path.join(project_dir, "nested", "old_ws"))
    build_dir = str(tmp_path / "build")
    os.mkdir(build_dir)

    impl.copy_files(project_dir, build_dir)

    assert _copied(build_dir) == {
        "project.yml",
        ".gitignore",
        os.path.join("files", "tap_config.json"),
        os.path.join("files", ".keep"),
        os.path.join("scripts", "run.sh"),
    }
    assert os.path.isfile(os.path.join(build_dir, impl.DOCKERFILE))


def test_bundle_excludes_given_workspace_dir(tmp_path):
    project_dir = _make_project(str(tmp_path))
    # Not recognizable as a workspace by its layout, but named with -w
    workspace_dir = os.path.join(project_dir, "ws")
    _write(os.path.join(workspace_dir, "files", "tap_config.json"),
           '{"api_key": "rendered-value"}')
    build_dir = str(tmp_path / "build")
    os.mkdir(build_dir)

    impl.copy_files(project_dir, build_dir, workspace_dir=workspace_dir)

    assert not any(p.startswith("ws") for p in _copied(build_dir))


def test_bundle_refuses_project_dir_used_as_workspace(tmp_path):
    project_dir = _make_project(str(tmp_path))
    os.mkdir(os.path.join(project_dir, "artifacts"))
    build_dir = str(tmp_path / "build")
    os.mkdir(build_dir)

    with pytest.raises(Exception, match="also a handoff workspace"):
        impl.copy_files(project_dir, build_dir)


def test_tar_filter_uses_bundle_ignore_patterns(tmp_path):
    files_dir = str(tmp_path / "extra")
    _write(os.path.join(files_dir, "keep.txt"), "ok")
    _write(os.path.join(files_dir, ".gitignore"))
    _write(os.path.join(files_dir, ".env.prod"), "API_KEY=value")
    _write(os.path.join(files_dir, ".ssh", "id_rsa"), "key")
    _write(os.path.join(files_dir, ".secrets", "secrets.yml"), "- key: k")
    tar_path = str(tmp_path / "bundle.tar.gz")

    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(files_dir, arcname=".", recursive=True, filter=_tar_filter)
    with tarfile.open(tar_path) as tar:
        names = set(tar.getnames())

    assert names == {".", "./keep.txt", "./.gitignore"}
