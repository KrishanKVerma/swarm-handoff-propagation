"""Provider interface and the Google AI Studio (Gemini) adapter.

The model is one config line. `provider_metadata()` returns the exact frozen
settings, and the runner writes them into every trace bundle — §12 commits the
study to a single provider and the write-up has to name it, so the name cannot
live only in someone's shell history.

Free tier, so the adapter paces itself: a minimum interval between calls, and
backoff on 429 or 503 honouring `Retry-After` when the server sends one. The
runner checkpoints after every run, so a rate-limit stop costs one run rather
than the pilot.

The API key is read from the environment (`GEMINI_API_KEY`) and is never
written to a trace, a log line or an error message. Standard library only.
"""

from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
API_KEY_ENV = "GEMINI_API_KEY"
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class ProviderError(RuntimeError):
    """A call that could not be completed. Never carries the key."""


class RateLimited(ProviderError):
    """Retries exhausted against a rate limit. The runner stops and checkpoints."""


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    model: str
    attempts: int
    elapsed_s: float
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None


class Provider(Protocol):
    name: str
    model: str

    def generate(self, *, system: str, user: str) -> ProviderResponse: ...

    def metadata(self) -> dict[str, Any]: ...


@dataclass
class GeminiProvider:
    """Google AI Studio. Free tier, paced and retried."""

    model: str = "gemini-2.0-flash"
    temperature: float = 0.0
    max_output_tokens: int = 2048
    min_interval_s: float = 4.5          # ~13 requests/minute, under a 15 RPM tier
    max_attempts: int = 5
    base_backoff_s: float = 8.0
    timeout_s: float = 90.0
    name: str = "google_ai_studio"
    _last_call: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not os.getenv(API_KEY_ENV):
            raise ProviderError(
                f"{API_KEY_ENV} is not set; export it before running the pilot"
            )

    def metadata(self) -> dict[str, Any]:
        """Frozen settings for the trace bundle. No key, ever."""
        return {
            "provider": self.name,
            "model": self.model,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "min_interval_s": self.min_interval_s,
            "max_attempts": self.max_attempts,
            "endpoint": ENDPOINT.format(model=self.model),
        }

    def _pace(self) -> None:
        wait = self.min_interval_s - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            ENDPOINT.format(model=self.model),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": os.environ[API_KEY_ENV],
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode("utf-8"))

    def generate(self, *, system: str, user: str) -> ProviderResponse:
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens,
                "responseMimeType": "application/json",
            },
        }
        started = time.monotonic()
        last_error: str = "no attempt made"
        for attempt in range(1, self.max_attempts + 1):
            self._pace()
            self._last_call = time.monotonic()
            try:
                body = self._request(payload)
            except urllib.error.HTTPError as exc:
                last_error = f"HTTP {exc.code}"
                if exc.code not in RETRYABLE_STATUS or attempt == self.max_attempts:
                    if exc.code == 429:
                        raise RateLimited(
                            f"rate limited after {attempt} attempts"
                        ) from None
                    raise ProviderError(f"provider returned {exc.code}") from None
                time.sleep(self._backoff(attempt, exc.headers.get("Retry-After")))
                continue
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = type(exc).__name__
                if attempt == self.max_attempts:
                    raise ProviderError(f"transport failure: {last_error}") from None
                time.sleep(self._backoff(attempt, None))
                continue
            return self._parse(body, attempt, time.monotonic() - started)
        raise ProviderError(last_error)

    def _backoff(self, attempt: int, retry_after: str | None) -> float:
        if retry_after:
            try:
                return min(float(retry_after), 120.0)
            except ValueError:
                pass
        return min(self.base_backoff_s * (2 ** (attempt - 1)), 120.0) + random.uniform(0, 2)

    def _parse(self, body: dict[str, Any], attempts: int, elapsed: float) -> ProviderResponse:
        candidates = body.get("candidates") or []
        if not candidates:
            raise ProviderError(
                "no candidate returned: " + str(body.get("promptFeedback", "unknown"))
            )
        candidate = candidates[0]
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(part.get("text", "") for part in parts)
        return ProviderResponse(
            text=text,
            model=self.model,
            attempts=attempts,
            elapsed_s=elapsed,
            finish_reason=candidate.get("finishReason"),
            usage=body.get("usageMetadata"),
        )


@dataclass
class ScriptedProvider:
    """A provider for tests and dry runs. Returns queued texts in order."""

    replies: list[str]
    model: str = "scripted"
    name: str = "scripted"
    calls: list[dict[str, str]] = field(default_factory=list)

    def metadata(self) -> dict[str, Any]:
        return {"provider": self.name, "model": self.model, "scripted_replies": len(self.replies)}

    def generate(self, *, system: str, user: str) -> ProviderResponse:
        self.calls.append({"system": system, "user": user})
        if not self.replies:
            raise ProviderError("scripted provider exhausted")
        return ProviderResponse(
            text=self.replies.pop(0), model=self.model, attempts=1, elapsed_s=0.0
        )
