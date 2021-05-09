import os, shutil
from typing import Dict
import pygit2
from github import Github

from handoff.config import get_state as _get_state
from handoff.config import GITHUB_ACCESS_TOKEN


GITHUB = None


def _get_github(access_token=None):
    state = _get_state()
    if not access_token:
        access_token = state.get(GITHUB_ACCESS_TOKEN)
    global GITHUB
    GITHUB = Github(access_token)
    return GITHUB


def clone(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff github clone -v organization=<github_org> repository=<github_repo> local_dir=<local_dir> force=False`
    Clone remote repository. If local_dir is omitted, ./<repository> is used.
    If force is set to True, an existing directory will be deleted before cloning.
    """
    state = _get_state()
    access_token = vars.get("access_token", state.get(GITHUB_ACCESS_TOKEN))
    github = _get_github(access_token)
    org_name = vars["organization"]
    repo_name = vars["repository"]
    local_dir = vars.get("local_dir", "./" + repo_name)
    if os.path.exists(local_dir):
        if not vars.get("force", False):
            raise Exception("The directory already exists.")
        shutil.rmtree(local_dir)
    git_url = "https://github.com/" + org_name + "/" + repo_name + ".git"
    callbacks = pygit2.RemoteCallbacks(pygit2.UserPass(access_token, "x-oauth-basic"))
    repo_clone = pygit2.clone_repository(
            git_url, local_dir, callbacks=callbacks)


def commit (
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff github commit -v local_dir=<local_dir> commit_msg=<msg> branch=<branch>`
    Commit all the outstanding changes to the remote branch. If the branch does not exist,
    it will be created.
    """
    access_token = vars.get("access_token")
    github = _get_github(access_token)
    commit_msg = vars["commit_msg"]
    local_dir = vars.get("local_dir")
    branch = vars.get("branch", "master")

    repo = pygit2.Repository(local_dir + "/.git")
    user = github.get_user()

    # repo.remotes.set_url("origin", repo.clone_url)
    index = repo.index
    index.add_all()
    index.write()
    author = pygit2.Signature(user.name, user.email)
    commiter = pygit2.Signature(user.name, user.email)
    tree = index.write_tree()
    oid = repo.create_commit(
            "refs/heads/" + branch,
            author,
            commiter,
            commit_msg,
            tree,
            [repo.head.target],
            # [repo.head.get_object().hex],
            )

    credentials = pygit2.UserPass(access_token, "x-oauth-basic")
    callbacks = pygit2.RemoteCallbacks(credentials=credentials)
    remote = repo.remotes["origin"]
    remote.credentials = credentials
    remote.push(["refs/heads/" + branch], callbacks=callbacks)
