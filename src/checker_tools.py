"""The read tool every checker gets — amendment 7, §4.

Each checker, per-handoff verifier and end monitor alike, gets a read tool on
the artifact. It is not the oracle:

* it does no comparison;
* it holds no expectation of what the file should contain;
* it never sees the oracle's verdict.

The checker gets the bytes and decides for itself. Nothing compels it to call
the tool at all, which is the point — §7's secondary estimates **p**, the
probability that a checker which has file access reads it and reports the
mismatch, and `called_read` per checker opportunity is p's denominator.

Tool access is identical in both schemes. The only difference between
`end_monitor` and `per_handoff` is when and how often a checker runs.

This module must not import `src.oracle`, and a test asserts it does not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckerReadTool:
    """A raw read of the artifact, bound to one checker opportunity.

    Parameters
    ----------
    path:
        The artifact the chain was supposed to write.
    run_id, checker_id, opportunity:
        Identify the row this tool's use contributes to the verifier-flag log.
        `opportunity` is the boundary the checker ran at — ``"1->2"``,
        ``"2->3"``, ``"3->4"`` for a per-handoff verifier, ``"end"`` for the end
        monitor.
    """

    path: Path
    run_id: str
    checker_id: str
    opportunity: str
    _calls: int = field(default=0, init=False, repr=False)

    def __call__(self) -> dict[str, Any]:
        """Return the artifact's raw contents. No comparison, no expectation."""
        self._calls += 1
        if not self.path.exists():
            return {"path": str(self.path), "exists": False, "contents": None}
        return {
            "path": str(self.path),
            "exists": True,
            "contents": self.path.read_text(encoding="utf-8", errors="replace"),
        }

    @property
    def called_read(self) -> bool:
        """Whether this checker used its file access. §7's p is estimated from this."""
        return self._calls > 0

    @property
    def read_count(self) -> int:
        return self._calls

    def flag_log_row(
        self,
        *,
        verdict: str | None = None,
        verdict_text: str | None = None,
    ) -> dict[str, Any]:
        """One row of the verifier-flag log — separate from the step records.

        §4's flag-isolation rule: flags live in their own log and never enter a
        downstream agent's input. This row is written by the runner; the fields
        are the ones §7 needs per opportunity.
        """
        return {
            "run_id": self.run_id,
            "checker_id": self.checker_id,
            "opportunity": self.opportunity,
            "called_read": self.called_read,
            "read_count": self._calls,
            "verdict": verdict,
            "verdict_text": verdict_text,
        }

    @property
    def tool_description(self) -> str:
        """What the checker is told. Carries no expectation about the contents."""
        return (
            "Read the artifact at the given path and return its raw contents. "
            "Returns exists=false if there is no file."
        )
