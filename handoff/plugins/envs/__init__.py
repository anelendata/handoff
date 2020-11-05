from typing import Dict

from handoff.config import get_state as _get_state
from handoff.core import admin

def get(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> None:
    """`handoff envs get -p <project_dir> -d key=<env_var_key>`
    Get the value of an evirohment varaible specified by <env_var_key>
    """
    state = _get_state()
    print(state[data["key"]])
