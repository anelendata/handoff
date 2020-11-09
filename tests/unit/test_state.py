from handoff.config import TASK, RESOURCE_GROUP, get_state, init_state


init_state(stage="prod")
state = get_state()


def test_set_not_allowed_env():
    try:
        state.set_env("foo", "bar")
    except Exception as e:
        print(e)
    else:
        assert False


def test_dict_set_get():
    if state.get("test_dict_set_get"):
        state.unset("test_dict_set_get")
    assert(state.get("test_dict_set_get") is None)
    state["test_dict_set_get"] = "test-resource"
    assert(state["test_dict_set_get"] == "test-resource")


def test_set_env_and_get():
    if state.get(TASK):
        state.unset(TASK)
    assert(state.get(TASK) is None)
    state.set_env(TASK, "test")
    assert(state[TASK] == "test")
