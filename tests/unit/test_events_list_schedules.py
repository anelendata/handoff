from handoff.services.cloud.aws import events


class FakeEventsClient:
    def __init__(self, rules):
        self._rules = rules
        self.list_targets_by_rule_calls = []

    def list_rules(self, **kwargs):
        return self._rules

    def list_targets_by_rule(self, **kwargs):
        self.list_targets_by_rule_calls.append(kwargs)
        return {"Targets": []}


def test_list_schedules_returns_empty_list_when_no_rules(monkeypatch):
    client = FakeEventsClient({"Rules": []})
    monkeypatch.setattr(events, "get_client", lambda cred_keys={}: client)

    result = events.list_schedules("task-stack")

    assert result == []
    assert client.list_targets_by_rule_calls == []


def test_list_schedules_returns_empty_list_when_rules_key_missing(monkeypatch):
    client = FakeEventsClient({})
    monkeypatch.setattr(events, "get_client", lambda cred_keys={}: client)

    result = events.list_schedules("task-stack")

    assert result == []
    assert client.list_targets_by_rule_calls == []


def test_list_schedules_returns_records_when_rules_present(monkeypatch):
    rules = {"Rules": [{"Name": "handoff-etl-task-stack-1"}]}
    client = FakeEventsClient(rules)
    monkeypatch.setattr(events, "get_client", lambda cred_keys={}: client)

    result = events.list_schedules("task-stack")

    assert len(result) == 1
    assert result[0]["rule"]["Name"] == "handoff-etl-task-stack-1"
    assert len(client.list_targets_by_rule_calls) == 1
