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
import re
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
    """A call that could not be completed. Never carries the key.

    Carries the HTTP status and a short body excerpt when there was one: a 404
    for a retired model and a daily-quota 429 must not look alike in a trace.
    """

    def __init__(self, message: str, *, status: int | None = None,
                 body: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.body = (body or "")[:400]

    def as_trace(self) -> dict[str, Any]:
        return {"error": str(self), "http_status": self.status, "body_excerpt": self.body}


class RateLimited(ProviderError):
    """A rate limit with a short reset. The runner stops and checkpoints."""


class QuotaExhausted(RateLimited):
    """A cap that will not clear soon — a daily limit. Rerunning today is futile."""


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    model: str
    attempts: int
    elapsed_s: float
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None

    @property
    def truncated(self) -> bool:
        """Output cut off by the token cap.

        An instrument failure, not an agent returning unparseable output. §9's
        malformed-output exclusion is about the agent; this is about us.
        """
        return (self.finish_reason or "").lower() in {"length", "max_tokens"}

    @property
    def total_tokens(self) -> int:
        usage = self.usage or {}
        for key in ("total_tokens", "totalTokenCount"):
            value = usage.get(key)
            if isinstance(value, int):
                return value
        return 0


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
                "User-Agent": USER_AGENT,
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


GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_KEY_ENV = "GROQ_API_KEY"

USER_AGENT = "swarm-handoff-propagation/0.1 (research sprint; python-urllib)"
"""Sent on every request.

Without it urllib identifies itself as `Python-urllib/3.x`, which the
provider's edge blocks outright — HTTP 403, Cloudflare `error code: 1010`,
before the request ever reaches the API. It looks exactly like a bad key and
is not one. A plain descriptive agent string is enough; it names this client
truthfully and impersonates no one."""


@dataclass
class GroqProvider:
    """Groq, OpenAI-compatible chat completions.

    Free tier is capped on **tokens** before requests — 8k/min and 200k/day
    against 30/min and 1000/day at the time of writing — so the governor paces
    on both. Checker calls carry the step projection and are the expensive
    ones. `usage` comes back on every call and the runner totals it, so the
    smoke run measures the pilot's cost rather than estimating it.

    The model string is frozen in `metadata()` and written into every trace.
    """

    model: str = "openai/gpt-oss-120b"
    temperature: float = 0.0
    max_output_tokens: int = 4096
    requests_per_minute: int = 25          # under a 30 RPM tier
    tokens_per_minute: int = 7000          # under an 8k TPM tier
    max_attempts: int = 5
    base_backoff_s: float = 5.0
    timeout_s: float = 120.0
    long_reset_s: float = 900.0            # beyond this, treat 429 as a daily cap
    name: str = "groq"
    _recent: list[tuple[float, int]] = field(default_factory=list, init=False, repr=False)
    _last_call: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not os.getenv(GROQ_KEY_ENV):
            raise ProviderError(f"{GROQ_KEY_ENV} is not set; export it before running")

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "model": self.model,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "requests_per_minute": self.requests_per_minute,
            "tokens_per_minute": self.tokens_per_minute,
            "endpoint": GROQ_ENDPOINT,
        }

    # --- pacing -----------------------------------------------------------

    def _tokens_in_window(self, now: float) -> int:
        self._recent = [(at, n) for at, n in self._recent if now - at < 60.0]
        return sum(n for _, n in self._recent)

    def _pace(self, estimated_tokens: int) -> None:
        interval = 60.0 / max(self.requests_per_minute, 1)
        while True:
            now = time.monotonic()
            wait = interval - (now - self._last_call)
            used = self._tokens_in_window(now)
            if used + estimated_tokens > self.tokens_per_minute and self._recent:
                oldest = min(at for at, _ in self._recent)
                wait = max(wait, 60.0 - (now - oldest) + 0.5)
            if wait <= 0:
                return
            time.sleep(min(wait, 65.0))

    @staticmethod
    def _estimate(system: str, user: str, reserve: int) -> int:
        return (len(system) + len(user)) // 4 + reserve

    # --- the call ---------------------------------------------------------

    def generate(self, *, system: str, user: str) -> ProviderResponse:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        estimate = self._estimate(system, user, 512)
        started = time.monotonic()
        for attempt in range(1, self.max_attempts + 1):
            self._pace(estimate)
            self._last_call = time.monotonic()
            try:
                body = self._request(payload)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
                if exc.code == 429:
                    reset = _retry_after_seconds(exc.headers.get("Retry-After"), detail)
                    if reset is not None and reset > self.long_reset_s:
                        raise QuotaExhausted(
                            f"daily quota exhausted; resets in about {reset / 3600:.1f}h",
                            status=429, body=detail,
                        ) from None
                    if attempt == self.max_attempts:
                        raise RateLimited("rate limited; retries exhausted",
                                          status=429, body=detail) from None
                    time.sleep(min(reset or self._backoff(attempt), 120.0))
                    continue
                if exc.code not in RETRYABLE_STATUS or attempt == self.max_attempts:
                    raise ProviderError(f"provider returned HTTP {exc.code}",
                                        status=exc.code, body=detail) from None
                time.sleep(self._backoff(attempt))
                continue
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == self.max_attempts:
                    raise ProviderError(f"transport failure: {type(exc).__name__}") from None
                time.sleep(self._backoff(attempt))
                continue
            return self._parse(body, attempt, time.monotonic() - started)
        raise ProviderError("retries exhausted")

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            GROQ_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ[GROQ_KEY_ENV]}",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode("utf-8"))

    def _backoff(self, attempt: int) -> float:
        return min(self.base_backoff_s * (2 ** (attempt - 1)), 120.0) + random.uniform(0, 2)

    def _parse(self, body: dict[str, Any], attempts: int, elapsed: float) -> ProviderResponse:
        choices = body.get("choices") or []
        if not choices:
            raise ProviderError("no choice returned", body=json.dumps(body)[:400])
        choice = choices[0]
        usage = body.get("usage") or {}
        self._recent.append((time.monotonic(), int(usage.get("total_tokens", 0) or 0)))
        return ProviderResponse(
            text=(choice.get("message") or {}).get("content") or "",
            model=body.get("model", self.model),
            attempts=attempts,
            elapsed_s=elapsed,
            finish_reason=choice.get("finish_reason"),
            usage=usage,
        )


def _retry_after_seconds(header: str | None, body: str) -> float | None:
    """Seconds until the limit clears, from the header or the message text."""
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    match = re.search(r"(?:try again in|retry in)\s+([0-9.]+)\s*([smh])", body, re.I)
    if match:
        value, unit = float(match.group(1)), match.group(2).lower()
        return value * {"s": 1, "m": 60, "h": 3600}[unit]
    match = re.search(r'"retryDelay"\s*:\s*"?([0-9.]+)s', body)
    if match:
        return float(match.group(1))
    return None
