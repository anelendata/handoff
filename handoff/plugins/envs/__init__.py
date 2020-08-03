from handoff.config import get_state
from handoff.core import admin

def get(project_dir, workspace_dir, data, **kwargs):
    state = get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    print(state[data["key"]])
