import datetime

import pytest

from handoff.services import cloud
from handoff.services.cloud import aws


@pytest.fixture
def state(monkeypatch):
    st = {"AWS_ACCESS_KEY_ID": "old", "AWS_SECRET_ACCESS_KEY": "old", "AWS_SESSION_TOKEN": "old"}
    monkeypatch.setattr(aws, "get_state", lambda: st)
    monkeypatch.setattr(aws, "_ASSUMED_ROLE", {})
    monkeypatch.delenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI", raising=False)
    return st


def test_container_credentials_are_fetched_again(state, monkeypatch):
    monkeypatch.setenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI", "/v2/credentials/x")
    seen = []
    monkeypatch.setattr(aws.cred, "fetch_container_credentials",
                        lambda uri: seen.append(uri) or {"AccessKeyId": "new", "SecretAccessKey": "new",
                                                         "Token": "new", "Expiration": "2026-11-07T09:00:00Z"})
    msg = aws.refresh_credentials()
    assert seen == ["/v2/credentials/x"]
    assert state["AWS_ACCESS_KEY_ID"] == state["AWS_SECRET_ACCESS_KEY"] == state["AWS_SESSION_TOKEN"] == "new"
    assert "new" not in msg  # never logs the credentials


def _assumed(monkeypatch, expires_in):
    exp = datetime.datetime.now(datetime.timezone.utc) + expires_in
    monkeypatch.setattr(aws, "_ASSUMED_ROLE", {"role_arn": "arn:aws:iam::1:role/r", "external_id": "e",
                                               "source_cred_keys": {"aws_access_key_id": "src"}, "expiration": exp})
    calls = []
    monkeypatch.setattr(aws, "_assume_role", lambda arn, external_id=None, cred_keys=None: calls.append((arn, external_id, cred_keys)))
    return calls


def test_assumed_role_is_assumed_again_near_expiry(state, monkeypatch):
    calls = _assumed(monkeypatch, datetime.timedelta(minutes=5))
    aws.refresh_credentials()
    assert calls == [("arn:aws:iam::1:role/r", "e", {"aws_access_key_id": "src"})]


def test_assumed_role_still_valid_is_left_alone(state, monkeypatch):
    calls = _assumed(monkeypatch, datetime.timedelta(hours=1))
    assert "still valid" in aws.refresh_credentials()
    assert calls == []


def test_long_lived_credentials_need_nothing(state):
    assert "nothing to refresh" in aws.refresh_credentials()
    assert state["AWS_ACCESS_KEY_ID"] == "old"


def test_cloud_wrapper_logs_and_continues_on_failure(monkeypatch):
    class P:
        def refresh_credentials(self):
            raise RuntimeError("endpoint down")
    monkeypatch.setattr(cloud, "get_platform", lambda *a, **k: P())
    cloud.refresh_credentials()  # does not raise


def test_task_transfers_refresh_first(monkeypatch, tmp_path):
    from handoff.core import task as T
    order = []
    monkeypatch.setattr(cloud, "refresh_credentials", lambda: order.append("refresh"))

    class P:
        def upload_file(self, local, key):
            order.append("upload")
    monkeypatch.setattr(cloud, "get_platform", lambda *a, **k: P())
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out.txt").write_text("x")
    T._upload({"name": "t", "upload": [{"path": "out.txt", "to": "runs/out.txt"}]}, {})
    assert order == ["refresh", "upload"]
