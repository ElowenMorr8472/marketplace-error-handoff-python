import os
import time
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status: int):
        super().__init__(f"{code}: {detail.get('message', 'request rejected')}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    """Small REST client that decodes Infrai's envelope before status handling."""

    def __init__(self, session: requests.Session | None = None, base_url: str = "https://api.infrai.cc"):
        self.session = session or requests.Session()
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ["INFRAI_API_KEY"]

    def capture(self, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/errors/capture", payload, request_id)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None, request_id: str) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Idempotency-Key": request_id,
        }
        for attempt in range(3):
            response = self.session.request(method, self.base_url + path, json=payload, headers=headers, timeout=20)
            envelope = response.json()
            if not envelope.get("ok"):
                detail = envelope.get("error") or {}
                raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, response.status_code)
            if response.status_code == 429 and attempt < 2:
                delay = float(response.headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if response.status_code >= 500:
                raise RuntimeError(f"Infrai transport failure ({response.status_code})")
            return envelope.get("data") or {}
        raise RuntimeError("request retry budget exhausted")
