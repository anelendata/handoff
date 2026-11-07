import os

import pytest

from handoff.core import admin


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _project(root, files_yaml, own_files=None):
    project_dir = os.path.join(root, "projects", "p")
    _write(os.path.join(project_dir, "project.yml"), "files:\n" + files_yaml)
    for rel, text in (own_files or {}).items():
        _write(os.path.join(project_dir, "files", rel), text)
    return project_dir


@pytest.fixture
def root(tmp_path):
    shared = tmp_path / "images" / "img" / "0.1" / "files"
    _write(str(shared / "scripts" / "run.py"), "print('{{ greeting }}')\n")
    _write(str(shared / "scripts" / "lib" / "util.py"), "X = 1\n")
    _write(str(shared / "query.sql"), "SELECT 1\n")
    return str(tmp_path)


def test_resolves_folders_and_files_from_parent_dirs(root):
    project_dir = _project(root, "- from: images/img/0.1/files/scripts\n"
                                 "- from: images/img/0.1/files/query.sql\n  to: sql/q.sql\n")
    got = admin._external_files(project_dir)
    assert [d for _, d in got] == ["scripts", os.path.join("sql", "q.sql")]
    assert got[0][0] == os.path.join(root, "images", "img", "0.1", "files", "scripts")


def test_files_get_local_renders_external_files(root, tmp_path, monkeypatch):
    project_dir = _project(root, "- from: images/img/0.1/files/scripts\n"
                                 "- from: images/img/0.1/files/query.sql\n  to: sql/q.sql\n",
                           own_files={"own.txt": "mine"})
    monkeypatch.setattr(admin, "get_state", lambda: {"greeting": "hi"})
    ws = str(tmp_path / "ws")
    os.makedirs(ws)
    admin.files_get_local(project_dir, ws)
    files = os.path.join(ws, "files")
    assert open(os.path.join(files, "own.txt")).read() == "mine"
    # Rendered like the project's own files (Jinja drops the trailing newline)
    assert open(os.path.join(files, "scripts", "run.py")).read() == "print('hi')"
    assert open(os.path.join(files, "scripts", "lib", "util.py")).read() == "X = 1"
    assert open(os.path.join(files, "sql", "q.sql")).read() == "SELECT 1"


def test_files_push_uploads_external_files_under_files(root, monkeypatch):
    project_dir = _project(root, "- from: images/img/0.1/files/scripts\n"
                                 "- from: images/img/0.1/files/query.sql\n", own_files={"own.txt": "x"})
    calls = []

    class P:
        def upload_dir(self, local, key):
            calls.append(("dir", os.path.relpath(local, root), key))

        def upload_file(self, local, key):
            calls.append(("file", os.path.relpath(local, root), key))

    monkeypatch.setattr(admin.cloud, "get_platform", lambda *a, **k: P())
    admin.files_push(project_dir, None)
    assert ("dir", os.path.join("images", "img", "0.1", "files", "scripts"), os.path.join("files", "scripts")) in calls
    assert ("file", os.path.join("images", "img", "0.1", "files", "query.sql"), os.path.join("files", "query.sql")) in calls


@pytest.mark.parametrize("entry,match", [
    ("- from: ../outside\n", "without '..'"),
    ("- from: /etc/hosts\n", "without '..'"),
    ("- from: images/img/0.1/files/missing\n", "not found"),
    ("- from: images/img/0.1/files/scripts\n  to: ../x\n", "without '..'"),
    ("- from: images/img/0.1/files/scripts\n  to: own.txt\n", "overwrite"),
    ("- from: images/img/0.1/files/scripts\n- from: images/img/0.1/files/query.sql\n  to: scripts/q.sql\n", "overlap"),
    ("- to: x\n", "needs from"),
    ("- from: images/img/0.1/files/scripts\n  junk: 1\n", "needs from"),
])
def test_unsafe_entries_are_refused(root, entry, match):
    project_dir = _project(root, entry, own_files={"own.txt": "x"})
    with pytest.raises(Exception, match=match):
        admin._external_files(project_dir)


def test_folder_with_a_secret_file_is_refused(root):
    _write(os.path.join(root, "images", "img", "0.1", "files", "scripts", "x.secret.json"), "{}")
    project_dir = _project(root, "- from: images/img/0.1/files/scripts\n")
    with pytest.raises(Exception, match="kept out of container bundles"):
        admin._external_files(project_dir)


def test_no_files_section_changes_nothing(tmp_path, monkeypatch):
    project_dir = str(tmp_path / "p")
    _write(os.path.join(project_dir, "project.yml"), "tasks: []\n")
    _write(os.path.join(project_dir, "files", "a.txt"), "a")
    monkeypatch.setattr(admin, "get_state", lambda: {})
    ws = str(tmp_path / "ws")
    os.makedirs(ws)
    admin.files_get_local(project_dir, ws)
    assert os.listdir(os.path.join(ws, "files")) == ["a.txt"]
