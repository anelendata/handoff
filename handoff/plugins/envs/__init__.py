from handoff.config import get_state as _get_state
from handoff.core import admin

def get(project_dir, workspace_dir, data, **kwargs):
    """Get the value of an evirohment varaible
    Must have --data option:
    -d '{"key": <ENV_VAR_KEY>}'
    """
    state = _get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    print(state[data["key"]])
