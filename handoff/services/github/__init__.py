import logging, os, shutil
from typing import Dict
import pygit2
from github import Github

from handoff.config import get_state as _get_state
from handoff.config import GITHUB_ACCESS_TOKEN

LOGGER = logging.getLogger(__name__)
GITHUB = None


def _get_github(access_token=None):
    state = _get_state()
    if not access_token:
        access_token = state.get(GITHUB_ACCESS_TOKEN)
    global GITHUB
    GITHUB = Github(access_token)
    return GITHUB


def _get_callbacks(access_token):
    return  pygit2.RemoteCallbacks(pygit2.UserPass(access_token, "x-oauth-basic"))


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

    repo_name = vars["repository"]
    org_name = vars.get("organization")
    local_dir = vars.get("local_dir", "./" + repo_name)
    if os.path.exists(local_dir):
        if not vars.get("force", False):
            raise Exception("The directory already exists.")
        shutil.rmtree(local_dir)
    git_url = vars.get("url", "https://github.com/" + str(org_name) + "/" + repo_name + ".git")

    if vars.get("use_cli", False):
        LOGGER.debug("Running git CLI")
        git_url = git_url.replace("https://", f"https://{access_token}:x-oauth-basic@")
        git_path = os.environ.get("GIT_PATH", "git")
        os.system(f"{git_path} clone {git_url}")
    else:
        repo_clone = pygit2.clone_repository(
                git_url, local_dir, callbacks=_get_callbacks(access_token))

    return {"status": "success", "repository": repo_name}


def pull(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff github commit -v local_dir=<local_dir> commit_msg=<msg> branch=<branch>`
    Commit all the outstanding changes to the remote branch. If the branch does not exist,
    it will be created.
    """
    state = _get_state()
    access_token = vars.get("access_token", state.get(GITHUB_ACCESS_TOKEN))
    github = _get_github(access_token)

    local_dir = vars["local_dir"]  # typically the "./{repository_name}"
    repo = pygit2.Repository(local_dir + "/.git")
    remote_name = "origin"

    # Adopted from https://github.com/MichaelBoselowitz/pygit2-examples/blob/68e889e50a592d30ab4105a2e7b9f28fac7324c8/examples.py#L48
    for remote in repo.remotes:
        if remote.name == remote_name:
            remote.fetch()
            remote_master_id = repo.lookup_reference('refs/remotes/origin/master').target
            merge_result, _ = repo.merge_analysis(remote_master_id)
            # Up to date, do nothing
            if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                return {
                    "status": "success",
                    "message": "Repository is up-to-date",
                }

            # We can just fastforward
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                repo.checkout_tree(repo.get(remote_master_id))
                master_ref = repo.lookup_reference('refs/heads/master')
                master_ref.set_target(remote_master_id)
                repo.head.set_target(remote_master_id)
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                repo.merge(remote_master_id)

                if repo.index_conflicts:
                    return {
                        "status": "error",
                        "mesage": repo.index.conflicts,
                    }

                user = repo.default_signature
                tree = repo.index.write_tree()
                commit = repo.create_commit('HEAD',
                                            user,
                                            user,
                                            'Merge!',
                                            tree,
                                            [repo.head.target, remote_master_id])
                repo.state_cleanup()
                return {
                    "status": "success",
                    "message": "successfully fast forwarded the repository",
                }
            else:
                return {
                    "status": "error",
                    "mesage": "Unknown merge analysis result"
                }


def commit (
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff github commit -v local_dir=<local_dir> commit_msg=<msg> branch=<branch>`
    Commit all the outstanding changes to the remote branch. If the branch does not exist,
    it will be created.
    """
    state = _get_state()
    access_token = vars.get("access_token", state.get(GITHUB_ACCESS_TOKEN))
    github = _get_github(access_token)

    local_dir = vars["local_dir"]  # typically the "./{repository_name}"
    repo = pygit2.Repository(local_dir + "/.git")

    user = github.get_user()

    branch = vars.get("branch", "master")
    commit_msg = vars["commit_msg"]

    # repo.remotes.set_url("origin", repo.clone_url)
    index = repo.index
    index.add_all()
    index.remove_all("*.secrets*")
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
    # callbacks = pygit2.RemoteCallbacks(credentials=credentials)
    remote = repo.remotes["origin"]
    remote.credentials = credentials
    remote.push(["refs/heads/" + branch], callbacks=_get_callbacks(access_token))
