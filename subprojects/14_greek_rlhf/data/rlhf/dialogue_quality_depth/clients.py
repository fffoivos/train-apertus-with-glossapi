"""Network clients behind small interfaces; tests use the fakes only."""
from __future__ import annotations

import json
import pathlib
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


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
    def complete(self, messages: list[dict[str, str]], *, model: str, temperature: float,
                 top_p: float, max_tokens: int, n: int) -> TargetResult: ...


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
            if exc.code in {400, 413} and any(word in detail.lower() for word in ("context", "length", "token")):
                raise ContextLimitError(detail) from exc
            raise
        except (TimeoutError, urllib.error.URLError) as exc:
            # Once urlopen is attempted, a timeout cannot prove non-observation.
            if isinstance(exc, TimeoutError) or "timed out" in str(exc).lower():
                raise AmbiguousTimeout(str(exc)) from exc
            raise

    def models(self) -> list[str]:
        data = self._request("/models")
        return [str(row["id"]) for row in data.get("data", [])]

    def complete(self, messages: list[dict[str, str]], *, model: str, temperature: float = .8,
                 top_p: float = .95, max_tokens: int = 1500, n: int = 1) -> TargetResult:
        if n != 1:
            raise ValueError("dialogue pilot sampling is frozen at n=1")
        started = time.monotonic()
        data = self._request("/chat/completions", {
            "model": model, "messages": messages, "n": 1, "temperature": temperature,
            "top_p": top_p, "max_tokens": max_tokens,
        })
        choices = data.get("choices", [])
        if len(choices) != 1:
            raise RuntimeError("target returned other than one completion")
        choice = choices[0]
        text = choice.get("message", {}).get("content")
        if not isinstance(text, str):
            raise RuntimeError("target completion text missing")
        usage = data.get("usage") or {}
        return TargetResult(text, str(choice.get("finish_reason") or "unknown"),
                            str(data.get("model") or model), usage, time.monotonic() - started)


class FakeTargetClient:
    def __init__(self, results: list[TargetResult | Exception], models: list[str] | None = None):
        self.results = list(results)
        self.model_ids = models or ["fake-model"]
        self.calls: list[dict[str, Any]] = []

    def models(self) -> list[str]:
        return list(self.model_ids)

    def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> TargetResult:
        self.calls.append({"messages": messages, **kwargs})
        if not self.results:
            raise RuntimeError("fake target exhausted")
        value = self.results.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


class SolClient(Protocol):
    def start(self) -> Any: ...
    def call(self, prompt: str, schema: dict[str, Any], *, model: str = "gpt-5.6-sol",
             effort: str = "high", timeout: int = 900) -> dict[str, Any]: ...
    def close(self) -> None: ...


class CodexSolClient:
    """Lazy wrapper so importing this package never spawns or imports Codex."""
    def __init__(self):
        self._server: Any = None

    def start(self) -> Any:
        if self._server is None:
            math_dir = pathlib.Path(__file__).resolve().parents[2] / "math"
            sys.path.insert(0, str(math_dir))
            from codex_server import CodexServer
            self._server = CodexServer()
        return self._server.start()

    def call(self, prompt: str, schema: dict[str, Any], *, model: str = "gpt-5.6-sol",
             effort: str = "high", timeout: int = 900) -> dict[str, Any]:
        if self._server is None:
            raise RuntimeError("Sol client not started")
        return self._server.call(prompt, schema, model=model, effort=effort, timeout=timeout)

    def close(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server = None


class FakeSolClient:
    def __init__(self, results: list[dict[str, Any] | Exception]):
        self.results = list(results)
        self.prompts: list[str] = []
        self.calls: list[dict[str, Any]] = []
        self.started = False

    def start(self) -> None:
        self.started = True

    def call(self, prompt: str, schema: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        self.prompts.append(prompt)
        self.calls.append({"prompt": prompt, "schema": schema, **kwargs})
        if not self.results:
            raise RuntimeError("fake Sol exhausted")
        value = self.results.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    def close(self) -> None:
        self.started = False

