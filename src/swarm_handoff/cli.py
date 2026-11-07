"""Generate synthetic fixtures or replay saved traces without provider calls."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .artifacts import InvalidBundle, audit_bundle, summarize
from .fixtures import demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate fixtures or replay saved fixture/live traces; no model calls")
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("demo", help="generate four synthetic condition fixtures")
    make.add_argument("--output", type=Path,
                      default=Path("artifacts") / datetime.now(timezone.utc).strftime("offline-%Y%m%dT%H%M%S%fZ"))
    make.add_argument("--repeats", type=int, choices=range(1, 6), default=1)
    make.add_argument("--checker-mode", choices=("no_read", "read"), default="no_read")
    replay = commands.add_parser("summarize", help="validate saved bundles and recompute descriptive counts")
    replay.add_argument("--input", required=True, type=Path)
    audit = commands.add_parser("audit", help="validate one saved fixture or live-0.2 bundle")
    audit.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            demo(args.output, args.repeats, args.checker_mode)
            result = summarize(args.output)
            result["output"] = str(args.output.resolve())
            (args.output / "fixture-summary.json").write_text(json.dumps(result, indent=2) + "\n")
        elif args.command == "summarize":
            result = summarize(args.input)
        else:
            trace = audit_bundle(args.input)
            result = {"valid": True, "run_id": trace["run_id"],
                      "schema_version": trace["schema_version"],
                      "evidence_kind": trace["evidence_kind"],
                      "replay_provider_api_calls": 0,
                      "verification_scope": ("saved record consistency; no signed or hashed live manifest"
                                             if trace["schema_version"] == "live-0.2" else
                                             "fixture manifest hashes and saved record consistency")}
    except InvalidBundle as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
