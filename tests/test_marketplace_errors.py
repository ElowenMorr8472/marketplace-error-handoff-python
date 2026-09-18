import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from infrai_client import InfraiClient, InfraiError
from marketplace_errors import OrderHandoff, handoff


class FakeResponse:
    status_code = 200
    headers = {}

    def json(self):
        return {"ok": True, "data": {"event_id": "evt-1"}, "error": None, "metadata": {}}


class FakeSession:
    def __init__(self):
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return FakeResponse()


def test_handoff_captures_asset_group_and_rethrows(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    session = FakeSession()
    client = InfraiClient(session=session)
    order = OrderHandoff("ord-1", "asset-9", "update-2")

    def reject(_):
        raise ValueError("carrier rejected parcel")

    with pytest.raises(ValueError):
        handoff(order, reject, client)
    method, path, kwargs = session.calls[0]
    assert method == "POST"
    assert path.endswith("/v1/errors/capture")
    assert kwargs["json"]["fingerprint"] == ["order-handoff", "asset-9"]
    assert kwargs["headers"]["Idempotency-Key"] == "handoff:ord-1"
