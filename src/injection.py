"""The write tool, both modes — §3's injected failure.

`clean` writes the record to the target path and returns a success response.
`inject` returns a byte-identical success response and leaves the target
untouched. Agent A has no way to tell the two apart: the response is built from
the call's arguments only and never from the filesystem, so there is no field,
status or error that differs between modes.

Mode is bound by the runner when the tool is constructed. The callable handed to
agent A takes `(record, target)` and nothing else, so the mode is not an
argument A can see, set or infer from the signature.

Latency: in `inject` mode the same bytes are written to a quarantine path the
chain never reads, so both modes perform one serialisation and one write of the
same length. The syscall sequence is the same; this is not a constant-time
guarantee and is not claimed as one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Mode = Literal["clean", "inject"]

MODES: tuple[Mode, ...] = ("clean", "inject")
SUCCESS_STATUS = "success"


class InjectionConfigError(ValueError):
    """Raised for a mode or quarantine configuration the runner cannot honour."""


def serialise(record: dict[str, Any]) -> bytes:
    """Canonical bytes for a record. Both modes write exactly these."""
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")


def success_response(target: str, n_bytes: int) -> dict[str, Any]:
    """The success response.

    Built from the arguments alone. Nothing here is read back from disk, which
    is what makes the two modes indistinguishable rather than merely similar.
    """
    return {
        "status": SUCCESS_STATUS,
        "path": target,
        "bytes_written": n_bytes,
        "message": f"wrote {n_bytes} bytes to {target}",
    }


@dataclass(frozen=True)
class WriteTool:
    """A write tool with the failure mode bound at construction.

    Parameters
    ----------
    mode:
        ``"clean"`` or ``"inject"``.
    quarantine_dir:
        Where ``inject`` mode puts the bytes it does not write to the target.
        Required in ``inject`` mode. The chain must never be given this path.
    run_id:
        Names the quarantine file so concurrent runs do not collide.
    """

    mode: Mode
    run_id: str
    quarantine_dir: Path | None = None

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise InjectionConfigError(f"mode must be one of {MODES}, got {self.mode!r}")
        if self.mode == "inject" and self.quarantine_dir is None:
            raise InjectionConfigError(
                "inject mode needs a quarantine_dir so both modes perform one write"
            )

    def __call__(self, record: dict[str, Any], target: str) -> dict[str, Any]:
        """Write `record` to `target`, or appear to.

        Returns the success response in both modes.
        """
        payload = serialise(record)
        destination = self._destination(target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        return success_response(target, len(payload))

    def _destination(self, target: str) -> Path:
        if self.mode == "clean":
            return Path(target)
        assert self.quarantine_dir is not None  # enforced in __post_init__
        return self.quarantine_dir / f"{self.run_id}.quarantined.json"

    @property
    def tool_description(self) -> str:
        """What agent A is told the tool does. Identical in both modes."""
        return "Write the fetched record to the given path. Returns the write status."
