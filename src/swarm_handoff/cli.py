"""Offline-only command line entry point."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .artifacts import audit_bundle, summarize
from .fixtures import demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic fixture validation; no live provider execution")
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("demo", help="generate four synthetic condition fixtures")
    make.add_argument("--output", type=Path,
                      default=Path("artifacts") / datetime.now(timezone.utc).strftime("offline-%Y%m%dT%H%M%S%fZ"))
    make.add_argument("--repeats", type=int, choices=range(1, 6), default=1)
    replay = commands.add_parser("summarize", help="verify hashes and recompute fixture counts")
    replay.add_argument("--input", required=True, type=Path)
    audit = commands.add_parser("audit", help="validate one saved fixture bundle")
    audit.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.command == "demo":
        demo(args.output, args.repeats)
        result = summarize(args.output)
        result["output"] = str(args.output.resolve())
        (args.output / "fixture-summary.json").write_text(json.dumps(result, indent=2) + "\n")
    elif args.command == "summarize":
        result = summarize(args.input)
    else:
        trace = audit_bundle(args.input)
        result = {"valid": True, "run_id": trace["run_id"], "evidence_kind": trace["evidence_kind"]}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
