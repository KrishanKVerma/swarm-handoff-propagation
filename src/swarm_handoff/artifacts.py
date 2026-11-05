"""Validate saved fixture records and recompute fixture counts only."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .contracts import Condition, FixtureScoring, canonical_bytes, digest, propagation
from .runner import public_step


class InvalidBundle(ValueError):
    pass


def _require(ok: bool, text: str) -> None:
    if not ok:
        raise InvalidBundle(text)


def audit_bundle(run_dir: Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    _require(manifest.get("evidence_kind") == "synthetic_fixture" and manifest.get("study_eligible") is False,
             "only synthetic, non-study bundles are supported")
    _require(set(manifest.get("files", {})) == {"trace.json", "artifact.json", "steps.jsonl", "checks.jsonl"},
             "unexpected manifest paths")
    for name, expected in manifest["files"].items():
        if expected is None:
            _require(name == "artifact.json" and not (run_dir / name).exists(), "invalid missing-file entry")
            continue
        data = (run_dir / name).read_bytes()
        _require(hashlib.sha256(data).hexdigest() == expected, "file hash mismatch: " + name)
    trace = json.loads((run_dir / "trace.json").read_text())
    _require(trace.get("schema_version") == "offline-fixture-0.1", "unsupported schema version")
    _require(trace.get("evidence_kind") == "synthetic_fixture" and trace.get("study_eligible") is False,
             "fixture status missing from trace")
    _require(trace.get("provider_api_calls") == 0, "fixture reports provider calls")
    _require(manifest.get("missing_files") == [name for name, value in manifest["files"].items() if value is None],
             "missing-file inventory mismatch")
    if manifest["files"]["artifact.json"] is None:
        _require(trace["excluded"] is True and trace["exclusion_reason"] == "oracle_unavailable",
                 "missing artifact requires an oracle-unavailable failure record")
    condition = Condition(trace["condition"])
    _require(trace["injected"] is condition.injected, "condition/injection mismatch")
    _require(trace["run_id"] == run_dir.name, "run directory and identifier disagree")
    steps = trace["steps"]
    for name, expected_records in (("steps.jsonl", steps), ("checks.jsonl", trace["checks"])):
        records = [json.loads(line) for line in (run_dir / name).read_text().splitlines()]
        _require(canonical_bytes(records) == canonical_bytes(expected_records),
                 "JSONL export differs from authoritative trace: " + name)
    _require([s["step_index"] for s in steps] == [1, 2, 3, 4], "four ordered step records required")
    _require([s["agent_id"] for s in steps] == list("ABCD"), "stage identities mismatch")
    _require(trace["agent_invocations"] == sum(s["call_receipt"] is not None for s in steps),
             "agent invocation count mismatch")
    policy = FixtureScoring(**trace["scoring_policy"]) if trace["scoring_policy"] is not None else None
    for index, step in enumerate(steps):
        _require(step["run_id"] == trace["run_id"] and step["condition"] == trace["condition"],
                 "per-step run metadata mismatch")
        if index and step["status"] != "not_executed":
            _require(canonical_bytes(step["input_payload"]) == canonical_bytes(steps[index - 1]["output_payload"]),
                     "handoff differs from prior output")
        oracle = step.get("oracle_observation")
        if oracle is not None and "error" not in oracle:
            _require(step["oracle_truth"] is (canonical_bytes(oracle["actual_state"]) == canonical_bytes(trace["held_record"])),
                     "oracle flag disagrees with saved observation")
        _require(step["propagation"] == propagation(step, injected=condition.injected,
                   token=trace["held_record"]["reference_code"], policy=policy), "propagation replay mismatch")
    expected_boundaries = [1, 2, 3] if condition.scheme == "per_handoff" else [4]
    expected_pairs = [(b, r) for b in expected_boundaries for r in range(trace["verifier_repeats"])]
    _require([(c["boundary_step"], c["repeat_index"]) for c in trace["checks"]] == expected_pairs,
             "check schedule mismatch")
    for check in trace["checks"]:
        boundary = check["boundary_step"]
        expected_input = {"scheme": condition.scheme, "boundary_step": boundary,
                          "transcript": [public_step(s) for s in steps[:boundary]]}
        _require(canonical_bytes(check["input"]) == canonical_bytes(expected_input),
                 "checker input differs from permitted transcript")
        _require(check["input_sha256"] == digest(expected_input), "checker input hash mismatch")
        _require(check["detection"] is None, "fixture flag must not become adjudicated detection")
    _require(trace["check_invocations"] == sum(c["call_receipt"] is not None for c in trace["checks"]),
             "check invocation count mismatch")
    _require(trace["confirmed_detections"] is None, "fixtures cannot establish detections")
    return trace


def summarize(output_root: Path) -> dict[str, Any]:
    paths = sorted(p.parent for p in Path(output_root).glob("*/manifest.json"))
    _require(bool(paths), "no fixture bundles found")
    traces = [audit_bundle(p) for p in paths]
    return {"evidence_kind": "synthetic_fixture", "study_results_generated": False,
            "provider_api_calls": 0, "runs": len(traces),
            "run_status_counts": dict(Counter(t["run_status"] for t in traces)),
            "step_status_counts": dict(Counter(s["status"] for t in traces for s in t["steps"])),
            "check_status_counts": dict(Counter(c["status"] for t in traces for c in t["checks"])),
            "agent_invocations": sum(t["agent_invocations"] for t in traces),
            "check_invocations": sum(t["check_invocations"] for t in traces),
            "flags_emitted": sum(c["flag"] is True for t in traces for c in t["checks"]),
            "confirmed_detections": None,
            "per_run": [{"run_id": t["run_id"], "condition": t["condition"],
                         "status": t["run_status"], "study_eligible": False} for t in traces]}
