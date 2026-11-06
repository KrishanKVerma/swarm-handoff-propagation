"""The oracle — a deterministic file read, runner-only. §3.

At each step it answers one question: does the file's actual content match what
the chain currently claims about it.

§3's hard constraint is that the oracle is never exposed to any agent or
verifier. That is enforced here rather than left as a convention, in two ways:

1. **Import guard.** Importing this module from a module whose name looks like
   an agent, checker, verifier, monitor or prompt raises `OracleAccessError` at
   import time. Calling into it from such a frame raises as well.
2. **No path into a prompt.** `check()` returns an `OracleVerdict` that refuses
   to render: `str()`, `repr()`, `format()`, f-strings, iteration and `bool()`
   all raise `OracleLeakError`. The verdict can only be consumed by reading
   `.matches` explicitly or by the runner calling `.to_trace()`. An accidental
   f-string in a prompt builder fails loudly instead of leaking the answer.

Residual, stated plainly: `check()` takes the chain's claim, which is
agent-derived by necessity — there is nothing to compare otherwise. The guard is
on the direction that matters, which is the verdict flowing back towards a
prompt.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FORBIDDEN_CALLER_MARKERS: tuple[str, ...] = (
    "agent",
    "checker",
    "verifier",
    "monitor",
    "prompt",
)


class OracleAccessError(ImportError):
    """Raised when an agent- or checker-side module reaches for the oracle."""


class OracleLeakError(RuntimeError):
    """Raised when a verdict is rendered somewhere it could enter a prompt."""


def _offending_caller() -> str | None:
    """The first calling module that looks agent- or checker-side."""
    for frame_info in inspect.stack()[1:]:
        module = frame_info.frame.f_globals.get("__name__", "")
        leaf = module.rsplit(".", 1)[-1].lower()
        if leaf.startswith("test_"):
            continue
        if any(marker in leaf for marker in FORBIDDEN_CALLER_MARKERS):
            return module
    return None


def _assert_runner_context(what: str) -> None:
    offender = _offending_caller()
    if offender is not None:
        raise OracleAccessError(
            f"{what} is runner-only (PREREGISTRATION.md §3); reached from {offender!r}"
        )


_assert_runner_context("src.oracle")


class OracleVerdict:
    """A verdict that cannot be rendered into text.

    Read `.matches` for the boolean. The runner writes it to the trace with
    `.to_trace()`. Everything else raises.
    """

    __slots__ = ("_matches", "_file_state", "_step", "_path")

    def __init__(self, *, matches: bool, file_state: Any, step: int, path: str) -> None:
        self._matches = matches
        self._file_state = file_state
        self._step = step
        self._path = path

    @property
    def matches(self) -> bool:
        return self._matches

    @property
    def file_state(self) -> Any:
        return self._file_state

    @property
    def step(self) -> int:
        return self._step

    def to_trace(self) -> dict[str, Any]:
        """Runner-only. The `oracle_truth` field and the state it saw."""
        _assert_runner_context("OracleVerdict.to_trace")
        return {
            "step_index": self._step,
            "oracle_truth": self._matches,
            "oracle_file_state": self._file_state,
            "oracle_path": self._path,
        }

    def _refuse(self, *_args: Any, **_kwargs: Any) -> Any:
        raise OracleLeakError(
            "an oracle verdict cannot be rendered as text (PREREGISTRATION.md §3); "
            "read .matches explicitly or call .to_trace() from the runner"
        )

    __str__ = _refuse
    __repr__ = _refuse
    __format__ = _refuse
    __iter__ = _refuse
    __bool__ = _refuse


@dataclass(frozen=True)
class Oracle:
    """A deterministic read of one artifact path.

    Fixed before the run: the path is bound at construction and `check()` takes
    no path argument, so no caller can redirect it at a later step.
    """

    path: Path

    def read_state(self) -> dict[str, Any]:
        """What is actually on disk. Deterministic; no parsing fallbacks."""
        if not self.path.exists():
            return {"exists": False, "bytes": 0, "content": None, "parsed": None}
        raw = self.path.read_bytes()
        try:
            parsed: Any = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = None
        return {
            "exists": True,
            "bytes": len(raw),
            "content": raw.decode("utf-8", errors="replace"),
            "parsed": parsed,
        }

    def check(self, *, claim: dict[str, Any], step: int) -> OracleVerdict:
        """Does the file match what the chain currently claims about it?

        `claim` is the record content the chain is asserting at this step. The
        comparison is on the parsed record, so key order and whitespace do not
        decide it; nothing else about the claim is interpreted.
        """
        _assert_runner_context("Oracle.check")
        state = self.read_state()
        matches = state["exists"] and state["parsed"] == claim
        return OracleVerdict(
            matches=matches, file_state=state, step=step, path=str(self.path)
        )
