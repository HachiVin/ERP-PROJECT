"""Test doubles for the OpenAI client, so no test ever touches the network."""

from __future__ import annotations

from types import SimpleNamespace

import openai

try:  # openai 3.x ships on "httpx2"; older releases use "httpx".
    import httpx2 as httpx
except ImportError:  # pragma: no cover - depends on the installed openai version
    import httpx

_URL = "https://openrouter.ai/api/v1/chat/completions"


def reply(text: str | None) -> SimpleNamespace:
    """A chat-completion response whose first choice contains ``text``."""
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def status_error(code: int, message: str = "ditolak") -> openai.APIStatusError:
    request = httpx.Request("POST", _URL)
    response = httpx.Response(code, request=request, json={"error": {"message": message}})
    return openai.APIStatusError(message, response=response, body=None)


def connection_error() -> openai.APIConnectionError:
    return openai.APIConnectionError(request=httpx.Request("POST", _URL))


def timeout_error() -> openai.APITimeoutError:
    return openai.APITimeoutError(request=httpx.Request("POST", _URL))


class FakeClient:
    """Mimics ``client.chat.completions.create``; records calls, returns or raises ``outcome``."""

    def __init__(self, outcome: object) -> None:
        self.calls: list[dict] = []
        self.outcome = outcome
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome
