#!/usr/bin/env python3
"""Exercise the live writer and saved-trace replay without making model calls.

    python scripts/check_live_replay.py
    python scripts/check_live_replay.py --output artifacts/live-replay-compatibility

The writer intentionally keeps its native live-0.2 metadata. This receipt, and
the scripted provider metadata in every trace, identify these as compatibility
fixtures. They are not empirical pilot runs or study results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from analysis.recompute import load_runs, summarise
from src.live_runner import RunConfig, run_live
from src.provider import ScriptedProvider
from swarm_handoff.live_artifacts import audit_live_bundle, summarize_live


CODE = "K3M9QX7ZP2WD"
RECORD = {"record_id": "REPLAY-PROBE", "reference_code": CODE,
          "unit": "kg", "values": [1, 2, 3]}


def _replies(mode: str, scheme: str) -> list[str]:
    """Both read/no-read repeats, both schedules, and an embedded canary."""
    outputs = [
        {"record": RECORD, "write_result": {"status": "success"}},
        {"transformed": {"reference": f"Record {CODE}", "total": 6}},
        {"verdict": "pass", "verdict_reason": f"Record {CODE} totals 6"},
        {"summary": f"Record {CODE} totals 6 kg."},
    ]
    checked = ({"flag": True, "claim": "artifact_mismatch",
                "note": "The returned artifact does not match the record."}
               if mode == "inject" else
               {"flag": False, "claim": "no_discrepancy",
                "note": "The returned artifact matches the record."})
    check_replies = [json.dumps({"tool": "read_artifact"}), json.dumps(checked),
                     json.dumps({"flag": False, "claim": "no_discrepancy",
                                 "note": "Scripted no-read repeat."})]
    replies: list[str] = []
    for index, output in enumerate(outputs, start=1):
        replies.append(json.dumps({"asserted": output, "inherited": {}}))
        if scheme == "per_handoff" and index < 4:
            replies.extend(check_replies)
    if scheme == "end_monitor":
        replies.extend(check_replies)
    return replies


def _hashes(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()}


def run_probe(output_root: Path) -> dict[str, Any]:
    """Create a fresh, isolated probe and verify nonmutating saved-data replay."""
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=False)
    written: list[dict[str, Any]] = []
    scripted_calls = 0
    for mode in ("clean", "inject"):
        for scheme in ("end_monitor", "per_handoff"):
            config = RunConfig(run_id=f"scripted_{mode}_{scheme}", mode=mode,
                               scheme=scheme, verifier_repeats=2, pilot=True)
            provider = ScriptedProvider(replies=_replies(mode, scheme))
            bundle = run_live(config, output_root, RECORD, provider)
            if bundle["excluded"] or provider.replies:
                raise AssertionError("Scripted writer did not complete the planned calls")
            scripted_calls += len(provider.calls)
            written.append(bundle)

    before = _hashes(output_root)
    for bundle in written:
        replayed = audit_live_bundle(output_root / bundle["run_id"])
        if replayed != bundle:
            raise AssertionError("Replay changed the saved writer trace")
    summary = summarize_live(output_root)
    expected = summarise(written)
    if summary["shared_analysis"] != expected or summarise(load_runs(output_root)) != expected:
        raise AssertionError("Saved-trace replay disagrees with the shared analysis")
    if _hashes(output_root) != before:
        raise AssertionError("Replay mutated a saved artifact")

    return {
        "valid": True,
        "evidence_kind": "scripted_live_writer_compatibility_probe",
        "empirical_traces_verified": 0,
        "study_results_generated": False,
        "provider_api_calls": 0,
        "scripted_provider_calls": scripted_calls,
        "writer_schema": "live-0.2",
        "bundles_written_and_replayed": len(written),
        "conditions": sorted(bundle["condition"] for bundle in written),
        "checks": sum(len(bundle["checks"]) for bundle in written),
        "checker_opportunities": sum(len(bundle["checker_opportunities"]) for bundle in written),
        "shared_analysis_equal": True,
        "saved_files_unchanged_by_replay": True,
        "bundle_sha256": before,
        "limitation": "Scripted provider only; no empirical pilot traces were verified.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        help="retain fixtures and receipt in a new directory")
    args = parser.parse_args(argv)
    try:
        if args.output is None:
            with TemporaryDirectory(prefix="swarm-live-replay-") as temporary:
                receipt = run_probe(Path(temporary) / "runs")
            receipt["bundles_retained"] = False
        else:
            receipt = run_probe(args.output)
            receipt["bundles_retained"] = True
            receipt["output_root"] = str(args.output.resolve())
            (args.output / "compatibility-receipt.json").write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    except FileExistsError:
        parser.error("--output must be a new directory; existing files were not replaced")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
