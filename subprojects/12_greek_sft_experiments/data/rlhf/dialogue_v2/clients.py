"""Target (vLLM) and Sol clients behind small interfaces; tests use the fakes.
Copied from dialogue_quality_depth/clients.py; the sampling config is passed explicitly (dv2-sampling-v1)."""
from __future__ import annotations

import json
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from common import RLHF


@dataclass(frozen=True)
class TargetResult:
    text: str
    finish_reason: str
    model: str
    usage: dict[str, int]
    wall_seconds: float


class AmbiguousTimeout(TimeoutError):
    """The request may have reached the server and produced an unseen response."""


class ContextLimitError(RuntimeError):
    pass


class TargetClient(Protocol):
    def models(self) -> list[str]: ...
    def complete(self, messages: list[dict[str, str]], *, model: str, temperature: float, top_p: float,
                 max_tokens: int, n: int) -> TargetResult: ...


def result_to_dict(result: TargetResult) -> dict[str, Any]:
    return asdict(result)


def result_from_dict(data: dict[str, Any]) -> TargetResult:
    return TargetResult(**data)


class HTTPApertusClient:
    def __init__(self, base_url: str, timeout: int = 600):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(self.base_url + path, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:1000]
            if exc.code in {400, 413} and any(w in detail.lower() for w in ("context", "maximum", "token")):
                raise ContextLimitError(detail) from exc
            raise
        except (TimeoutError, urllib.error.URLError) as exc:
            if isinstance(exc, TimeoutError) or "timed out" in str(exc).lower():
                raise AmbiguousTimeout(str(exc)) from exc
            raise

    def models(self) -> list[str]:
        return [str(row["id"]) for row in self._request("/models").get("data", [])]

    def complete(self, messages: list[dict[str, str]], *, model: str, temperature: float, top_p: float,
                 max_tokens: int, n: int = 1) -> TargetResult:
        if n != 1:
            raise ValueError("dialogue v2 sampling is n=1 per call")
        started = time.monotonic()
        data = self._request("/chat/completions", {"model": model, "messages": messages, "n": 1,
                                                   "temperature": temperature, "top_p": top_p,
                                                   "max_tokens": max_tokens})
        choices = data.get("choices", [])
        if len(choices) != 1:
            raise RuntimeError("target returned other than one completion")
        text = choices[0].get("message", {}).get("content")
        if not isinstance(text, str):
            raise RuntimeError("target completion text missing")
        return TargetResult(text, str(choices[0].get("finish_reason") or "unknown"), str(data.get("model") or model),
                            data.get("usage") or {}, time.monotonic() - started)


class FakeTargetClient:
    def __init__(self, responder, models: list[str] | None = None):
        """responder(messages) -> TargetResult | Exception"""
        self.responder = responder
        self.model_ids = models or ["fake-model"]
        self.calls: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def models(self) -> list[str]:
        return list(self.model_ids)

    def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> TargetResult:
        with self._lock:
            self.calls.append({"messages": [dict(m) for m in messages], **kwargs})
        value = self.responder(messages)
        if isinstance(value, Exception):
            raise value
        return value


class SolClient(Protocol):
    def start(self) -> Any: ...
    def call(self, prompt: str, schema: dict[str, Any], *, model: str = "gpt-5.6-sol", effort: str = "medium",
             timeout: int = 900) -> dict[str, Any]: ...
    def close(self) -> None: ...


class CodexSolClient:
    """Sol via data/math/codex_server.py (one app-server, concurrent threads). Never astra."""

    def __init__(self):
        self._server: Any = None

    def start(self) -> Any:
        if self._server is None:
            sys.path.insert(0, str(RLHF.parent / "math"))
            from codex_server import CodexServer
            self._server = CodexServer()
            return self._server.start()
        return None

    def call(self, prompt: str, schema: dict[str, Any], *, model: str = "gpt-5.6-sol", effort: str = "medium",
             timeout: int = 900) -> dict[str, Any]:
        if model != "gpt-5.6-sol":
            raise ValueError("dialogue v2 uses gpt-5.6-sol only")
        if self._server is None:
            raise RuntimeError("Sol client not started")
        return self._server.call(prompt, schema, model=model, effort=effort, timeout=timeout)

    def close(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server = None


class FakeSolClient:
    def __init__(self, responder):
        """responder(prompt, schema) -> dict | Exception"""
        self.responder = responder
        self.calls: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def start(self) -> None:
        return None

    def call(self, prompt: str, schema: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        with self._lock:
            self.calls.append({"prompt": prompt, "schema": schema, **kwargs})
        value = self.responder(prompt, schema)
        if isinstance(value, Exception):
            raise value
        return value

    def close(self) -> None:
        return None
