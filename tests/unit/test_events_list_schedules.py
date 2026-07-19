import pytest

from handoff.services.cloud.aws import events


class FakeEventsClient:
    """Simulates the subset of boto3's EventBridge client used by
    list_schedules: NamePrefix filtering (with pagination) and
    per-rule target lookups.
    """

    def __init__(self, rule_names, page_size=None):
        self._rules = [{"Name": n, "ScheduleExpression": "cron(0 0 * * ? *)"}
                       for n in rule_names]
        self._page_size = page_size
        self.list_rules_calls = []
        self.list_targets_by_rule_calls = []

    def list_rules(self, **kwargs):
        self.list_rules_calls.append(kwargs)
        prefix = kwargs.get("NamePrefix", "")
        matches = [r for r in self._rules if r["Name"].startswith(prefix)]

        if not self._page_size:
            return {"Rules": matches}

        token = kwargs.get("NextToken")
        start = int(token) if token else 0
        end = start + self._page_size
        page = {"Rules": matches[start:end]}
        if end < len(matches):
            page["NextToken"] = str(end)
        return page

    def list_targets_by_rule(self, **kwargs):
        self.list_targets_by_rule_calls.append(kwargs)
        return {"Targets": []}


def test_declared_scope_filters_out_sibling_task_rule(monkeypatch):
    # "handoff-etl-widgets" and "handoff-etl-widgets-legacy" are sibling
    # tasks whose stack names share a prefix, so a NamePrefix match on the
    # shorter one also matches rules belonging to the longer one.
    client = FakeEventsClient([
        "handoff-etl-widgets-daily-1",
        "handoff-etl-widgets-legacy-nightly-1",
    ])
    monkeypatch.setattr(events, "get_client", lambda cred_keys={}: client)

    result = events.list_schedules(
        "handoff-etl-widgets",
        scope="declared",
        target_ids=["daily-1"],
    )

    assert [r["rule"]["Name"] for r in result] == [
        "handoff-etl-widgets-daily-1"
    ]


def test_declared_scope_returns_empty_when_no_target_ids(monkeypatch):
    client = FakeEventsClient(["handoff-etl-widgets-daily-1"])
    monkeypatch.setattr(events, "get_client", lambda cred_keys={}: client)

    result = events.list_schedules("handoff-etl-widgets", scope="declared")

    assert result == []
    assert client.list_targets_by_rule_calls == []


def test_prefix_scope_still_over_matches_sibling_task(monkeypatch):
    # Documents the known limitation of the legacy "prefix" scope: it is
    # kept only for backward compatibility and explicitly does not fix
    # the #134 over-match.
    client = FakeEventsClient([
        "handoff-etl-widgets-daily-1",
        "handoff-etl-widgets-legacy-nightly-1",
    ])
    monkeypatch.setattr(events, "get_client", lambda cred_keys={}: client)

    result = events.list_schedules("handoff-etl-widgets", scope="prefix")

    names = {r["rule"]["Name"] for r in result}
    assert names == {
        "handoff-etl-widgets-daily-1",
        "handoff-etl-widgets-legacy-nightly-1",
    }


def test_all_scope_ignores_task_stack_and_returns_every_handoff_rule(monkeypatch):
    client = FakeEventsClient([
        "handoff-etl-widgets-daily-1",
        "handoff-etl-widgets-legacy-nightly-1",
        "handoff-role-other-thing",
    ])
    monkeypatch.setattr(events, "get_client", lambda cred_keys={}: client)

    result = events.list_schedules("handoff-etl-widgets", scope="all")

    names = {r["rule"]["Name"] for r in result}
    assert names == {
        "handoff-etl-widgets-daily-1",
        "handoff-etl-widgets-legacy-nightly-1",
        "handoff-role-other-thing",
    }
    assert client.list_rules_calls[0]["NamePrefix"] == "handoff-"


def test_list_rules_by_prefix_paginates(monkeypatch):
    client = FakeEventsClient(
        ["handoff-etl-widgets-1", "handoff-etl-widgets-2",
         "handoff-etl-widgets-3"],
        page_size=1,
    )
    monkeypatch.setattr(events, "get_client", lambda cred_keys={}: client)

    result = events.list_schedules(
        "handoff-etl-widgets",
        scope="declared",
        target_ids=["1", "2", "3"],
    )

    assert len(client.list_rules_calls) == 3
    assert {r["rule"]["Name"] for r in result} == {
        "handoff-etl-widgets-1",
        "handoff-etl-widgets-2",
        "handoff-etl-widgets-3",
    }


def test_list_schedules_returns_empty_list_when_no_rules(monkeypatch):
    client = FakeEventsClient([])
    monkeypatch.setattr(events, "get_client", lambda cred_keys={}: client)

    result = events.list_schedules("handoff-etl-widgets", scope="prefix")

    assert result == []
    assert client.list_targets_by_rule_calls == []


def test_invalid_scope_raises_instead_of_falling_back_to_prefix(monkeypatch):
    client = FakeEventsClient(["handoff-etl-widgets-daily-1"])
    monkeypatch.setattr(events, "get_client", lambda cred_keys={}: client)

    with pytest.raises(ValueError):
        events.list_schedules("handoff-etl-widgets", scope="declare")

    assert client.list_rules_calls == []
