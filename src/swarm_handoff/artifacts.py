"""Replay saved fixture and live records without calling model providers."""

from __future__ import annotations

import hashlib
import json
import math
import re
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


def _audit_v1(run_dir: Path) -> dict[str, Any]:
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
    policy = FixtureScoring.from_recorded(trace["scoring_policy"]) if trace["scoring_policy"] is not None else None
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


def _same(left: Any, right: Any) -> bool:
    """Compare JSON without treating True as interchangeable with 1."""
    return canonical_bytes(left) == canonical_bytes(right)


def _receipt(receipt: Any, *, executed: bool) -> None:
    if not executed:
        _require(receipt is None, "unexecuted callback has a receipt")
        return
    _require(isinstance(receipt, dict), "executed callback requires a receipt")
    _require(receipt.get("backend") == "offline_callback"
             and type(receipt.get("provider_api_calls")) is int
             and receipt["provider_api_calls"] == 0,
             "fixture callback receipt reports provider activity")
    _require(receipt.get("token_usage") is None and receipt.get("cost") is None,
             "fixture callback cannot report provider tokens or cost")
    elapsed = receipt.get("elapsed_seconds")
    _require(type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= 0,
             "invalid callback elapsed time")


def _response_replay(row: dict[str, Any], expected: dict[str, Any]) -> None:
    """Replay complete diagnostic responses; bounded truncated captures stay partial."""
    raw = row.get("raw_response")
    _require(isinstance(raw, dict) and isinstance(raw.get("text"), str)
             and type(raw.get("truncated")) is bool,
             "completed callback requires a raw response capture")
    if raw["truncated"]:
        return
    _require(raw.get("sha256") == hashlib.sha256(raw["text"].encode()).hexdigest(),
             "raw response hash mismatch")
    _require(_same(json.loads(raw["text"]), expected), "raw response replay mismatch")


def _snapshot(snapshot: Any) -> dict[str, Any]:
    _require(isinstance(snapshot, dict)
             and set(snapshot) == {"status", "content_utf8", "sha256", "error"},
             "invalid artifact snapshot fields")
    if snapshot["status"] == "available":
        _require(isinstance(snapshot["content_utf8"], str) and snapshot["error"] is None,
                 "available snapshot requires artifact text")
        _require(snapshot["sha256"] == hashlib.sha256(snapshot["content_utf8"].encode("utf-8")).hexdigest(),
                 "artifact snapshot hash mismatch")
        return {"ok": True, "content_utf8": snapshot["content_utf8"]}
    _require(snapshot["status"] == "unavailable" and snapshot["content_utf8"] is None
             and snapshot["sha256"] is None and isinstance(snapshot["error"], str)
             and bool(snapshot["error"]), "unavailable snapshot must preserve its error")
    return {"ok": False, "error": snapshot["error"]}


def _control_flow_v2(trace: dict[str, Any], condition: Condition) -> None:
    """Replay deterministic offline eligibility; checker flags never stop tasks."""
    blocked = unexpected = False
    run_status, excluded, exclusion_reason = "completed", False, None
    by_boundary = {o["boundary_step"]: [] for o in trace["checker_opportunities"]}
    for check in trace["checks"]:
        by_boundary[check["boundary_step"]].append(check)

    def check_group(boundary: int, available: bool) -> None:
        nonlocal blocked, unexpected, run_status, excluded, exclusion_reason
        pending_error = False
        for check in by_boundary[boundary]:
            eligible = available and not pending_error
            _require((check["status"] != "not_executed") is eligible,
                     "checker execution eligibility replay mismatch")
            if not eligible:
                expected_error = "previous_check_error" if pending_error else "incomplete_chain_fixture_policy"
                _require(check["error"] == expected_error, "skipped checker reason replay mismatch")
                _require(check["raw_response"] is None, "skipped checker cannot have a raw response")
            elif check["status"] == "runner_error":
                pending_error = True
        if pending_error:
            blocked = unexpected = excluded = True
            run_status = exclusion_reason = "runner_error"

    for index, step in enumerate(trace["steps"]):
        eligible = not blocked
        _require((step["status"] != "not_executed") is eligible,
                 "task execution eligibility replay mismatch")
        expected_input = ({"task": "fetch_and_write_record"} if index == 0 else
                          trace["steps"][index - 1]["output_payload"] if eligible else None)
        _require(_same(step["input_payload"], expected_input), "task input eligibility replay mismatch")
        if not eligible:
            _require(not step["action_log"] and step["raw_response"] is None,
                     "skipped task cannot have actions or a raw response")
        elif step["status"] == "completed":
            _require(step["halted_reason"] is None, "completed task cannot have a refusal reason")
        elif step["status"] == "task_refused":
            _require(isinstance(step["halted_reason"], str) and bool(step["halted_reason"].strip()),
                     "task refusal requires a reason")
            blocked, run_status = True, "task_refused"
        elif step["status"] in {"api_timeout", "malformed_output", "runner_error"}:
            blocked = excluded = True
            run_status = exclusion_reason = step["status"]
            if step["status"] == "runner_error":
                unexpected = True
        observation = step["oracle_observation"]
        _require(isinstance(observation, dict), "each step requires a private oracle observation")
        if "error" in observation:
            # The runner observes every saved step, including skipped ones. A
            # later failed observation therefore supersedes an earlier cause.
            blocked = excluded = True
            run_status = exclusion_reason = "oracle_unavailable"
        if condition.scheme == "per_handoff" and index < 3:
            check_group(index + 1, not blocked and step["status"] == "completed" and not unexpected)
    if condition.scheme == "end_monitor":
        check_group(4, not blocked and all(s["status"] == "completed" for s in trace["steps"])
                    and not unexpected)
    _require(trace["run_status"] == run_status and trace["excluded"] is excluded
             and trace["exclusion_reason"] == exclusion_reason, "run status replay mismatch")


def _audit_v2(run_dir: Path) -> dict[str, Any]:
    # Imported only for v2: archived 0.1 bundles retain their original replay rules.
    from .contracts import CHECKER_READ_TOOL, propagation_v2

    manifest = json.loads((run_dir / "manifest.json").read_text())
    _require(manifest.get("evidence_kind") == "synthetic_fixture" and manifest.get("study_eligible") is False,
             "only synthetic, non-study bundles are supported")
    names = {"trace.json", "artifact.json", "steps.jsonl", "checks.jsonl", "checker_opportunities.jsonl"}
    _require(set(manifest.get("files", {})) == names, "unexpected manifest paths")
    for name, expected in manifest["files"].items():
        if expected is None:
            _require(name == "artifact.json" and not (run_dir / name).exists(), "invalid missing-file entry")
        else:
            _require(hashlib.sha256((run_dir / name).read_bytes()).hexdigest() == expected,
                     "file hash mismatch: " + name)
    _require(manifest.get("missing_files") == [name for name, value in manifest["files"].items() if value is None],
             "missing-file inventory mismatch")
    trace = json.loads((run_dir / "trace.json").read_text())
    _require(trace.get("schema_version") == "offline-fixture-0.2", "unsupported schema version")
    _require(trace.get("evidence_kind") == "synthetic_fixture" and trace.get("study_eligible") is False,
             "fixture status missing from trace")
    _require(type(trace.get("provider_api_calls")) is int and trace["provider_api_calls"] == 0,
             "fixture reports provider calls")
    _require(trace.get("confirmed_detections") is None, "fixtures cannot establish detections")
    _require(trace["run_id"] == run_dir.name and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", trace["run_id"]),
             "run directory and identifier disagree")
    _require(type(trace["verifier_repeats"]) is int and 1 <= trace["verifier_repeats"] <= 5,
             "invalid checker repeat count")
    condition = Condition(trace["condition"])
    _require(trace["injected"] is condition.injected, "condition/injection mismatch")
    token = trace["held_record"]["reference_code"]
    _require(isinstance(token, str) and re.fullmatch(r"[A-Z0-9]{12}", token), "invalid reference code")
    if manifest["files"]["artifact.json"] is None:
        _require(trace["excluded"] is True and trace["exclusion_reason"] == "oracle_unavailable",
                 "missing artifact requires an oracle-unavailable failure record")
    for field in ("flags_to_task_agents", "flags_to_later_checks", "oracle_to_models"):
        _require(trace["visibility_policy"].get(field) is False, "invalid visibility policy")

    steps, checks, opportunities = trace["steps"], trace["checks"], trace["checker_opportunities"]
    for name, rows in (("steps.jsonl", steps), ("checks.jsonl", checks),
                       ("checker_opportunities.jsonl", opportunities)):
        exported = [json.loads(line) for line in (run_dir / name).read_text().splitlines()]
        _require(_same(exported, rows), "JSONL export differs from authoritative trace: " + name)
    _require(_same([s["step_index"] for s in steps], [1, 2, 3, 4]), "four ordered step records required")
    _require([s["agent_id"] for s in steps] == list("ABCD"), "stage identities mismatch")
    policy = FixtureScoring.from_recorded(trace["scoring_policy"]) if trace["scoring_policy"] is not None else None
    for index, step in enumerate(steps):
        _require(not ({"verifier_verdict", "verifier_text", "verifier_status"} & set(step)),
                 "checker flags must be isolated from step records")
        _require(step["run_id"] == trace["run_id"] and step["condition"] == trace["condition"],
                 "per-step run metadata mismatch")
        _require(step["status"] in {"completed", "task_refused", "not_executed", "api_timeout",
                                    "malformed_output", "runner_error"}, "unknown step status")
        _receipt(step["call_receipt"], executed=step["status"] != "not_executed")
        if index and step["status"] != "not_executed":
            _require(_same(step["input_payload"], steps[index - 1]["output_payload"]),
                     "handoff differs from prior output")
        if step["status"] in {"completed", "task_refused"}:
            payload = step["output_payload"]
            _require(isinstance(payload, dict) and set(payload) == {"asserted", "inherited"}
                     and all(isinstance(payload[k], dict) for k in payload), "invalid agent output shape")
            if step["agent_id"] == "C":
                _require(payload["asserted"].get("verdict") in ("pass", "fail", "cannot_determine"),
                         "invalid C verdict enum")
            _require(type(step["self_report_claim"]) is bool and isinstance(step["self_report_text"], str),
                     "invalid agent self-report")
            _response_replay(step, {"output_payload": payload, "self_report_claim": step["self_report_claim"],
                                   "self_report_text": step["self_report_text"],
                                   "halted_reason": step["halted_reason"]})
        else:
            _require(step["output_payload"] is None, "unsuccessful step cannot have a validated output")
        oracle = step.get("oracle_observation")
        if oracle is not None and "error" not in oracle:
            truth = _same(oracle["actual_state"], trace["held_record"])
            _require(step["oracle_truth"] is truth and oracle["matches_expected"] is truth,
                     "oracle flag disagrees with saved observation")
        else:
            _require(step["oracle_truth"] is None, "unavailable oracle cannot have a truth value")
        _require(_same(step["propagation"], propagation_v2(step, injected=condition.injected,
                     token=token, policy=policy)), "propagation replay mismatch")
    _require(type(trace["agent_invocations"]) is int
             and trace["agent_invocations"] == sum(s["call_receipt"] is not None for s in steps),
             "agent invocation count mismatch")
    final_observation = steps[-1].get("oracle_observation")
    if manifest["files"]["artifact.json"] is not None and final_observation is not None and "error" not in final_observation:
        _require(manifest["files"]["artifact.json"] == final_observation["artifact_sha256"],
                 "final artifact differs from the final oracle observation")

    boundaries = [1, 2, 3] if condition.scheme == "per_handoff" else [4]
    expected_pairs = [[b, r] for b in boundaries for r in range(trace["verifier_repeats"])]
    _require(_same([[c["boundary_step"], c["repeat_index"]] for c in checks], expected_pairs),
             "check schedule mismatch")
    _require(_same([o["boundary_step"] for o in opportunities], boundaries), "checker opportunity schedule mismatch")
    for position, opportunity in enumerate(opportunities):
        boundary = boundaries[position]
        opp_id = f"{trace['run_id']}:boundary:{boundary}:{condition.scheme}"
        expected_input = {"scheme": condition.scheme, "boundary_step": boundary,
                          "transcript": [public_step(s) for s in steps[:boundary]],
                          "available_tools": [CHECKER_READ_TOOL]}
        common = {"opportunity_id": opp_id, "run_id": trace["run_id"], "boundary_step": boundary,
                  "scheme": condition.scheme, "checker_id": "external_checker"}
        for field, value in common.items():
            _require(_same(opportunity.get(field), value), "checker opportunity identity mismatch")
        _require(_same(opportunity["input"], expected_input), "checker input differs from permitted transcript and tools")
        _require(opportunity["input_sha256"] == digest(expected_input), "checker input hash mismatch")
        snapshot = opportunity["artifact_snapshot"]
        expected_result = _snapshot(snapshot)
        oracle = steps[boundary - 1].get("oracle_observation")
        if snapshot["status"] == "available" and oracle is not None and "error" not in oracle:
            _require(snapshot["sha256"] == oracle["artifact_sha256"]
                     and _same(json.loads(snapshot["content_utf8"]), oracle["actual_state"]),
                     "artifact snapshot differs from boundary observation")
        group = checks[position * trace["verifier_repeats"]:(position + 1) * trace["verifier_repeats"]]
        expected_ids = [f"{opp_id}:repeat:{repeat}" for repeat in range(trace["verifier_repeats"])]
        _require(opportunity["evaluation_ids"] == expected_ids, "opportunity evaluation inventory mismatch")
        for repeat, check in enumerate(group):
            for field, value in common.items():
                # Scheme is carried by the permitted input as well as the opportunity.
                if field != "scheme":
                    _require(_same(check.get(field), value), "checker evaluation identity mismatch")
            _require(check["evaluation_id"] == expected_ids[repeat], "checker evaluation identity mismatch")
            _require(_same(check["input"], expected_input), "checker input differs from permitted transcript and tools")
            _require(check["input_sha256"] == digest(expected_input), "checker input hash mismatch")
            _require(check["artifact_snapshot_sha256"] == snapshot["sha256"], "checker snapshot identity mismatch")
            _require(check["detection"] is None, "fixture flag must not become adjudicated detection")
            _require(check["status"] in {"completed", "not_executed", "timeout", "malformed_output", "runner_error"},
                     "unknown checker status")
            executed = check["status"] != "not_executed"
            _receipt(check["call_receipt"], executed=executed)
            calls = check["tool_calls"]
            _require(isinstance(calls, list), "checker tool log must be a list")
            for call in calls:
                _require(isinstance(call, dict) and set(call) == {"tool", "arguments", "result"}
                         and isinstance(call["tool"], str), "invalid checker tool log")
                if call["tool"] != "read_artifact":
                    permitted_result = {"ok": False, "error": "tool_not_available"}
                elif not _same(call["arguments"], {}):
                    permitted_result = {"ok": False, "error": "invalid_arguments"}
                else:
                    permitted_result = expected_result
                _require(_same(call["result"], permitted_result), "checker read differs from frozen artifact snapshot")
            called = any(c["tool"] == "read_artifact" for c in calls) if executed else None
            succeeded = any(c["tool"] == "read_artifact" and c["result"].get("ok") is True
                            for c in calls) if executed else None
            _require(check["read_tool_called"] is called and check["read_succeeded"] is succeeded,
                     "checker read diagnostics disagree with tool log")
            if not executed:
                _require(not calls, "unexecuted checker cannot have tool calls")
            if check["status"] == "completed":
                _require(type(check["flag"]) is bool and isinstance(check["text"], str),
                         "completed checker requires flag and text")
                _response_replay(check, {"flag": check["flag"], "text": check["text"]})
            else:
                _require(check["flag"] is None and check["text"] is None,
                         "unavailable checker cannot have a verdict")
        first = group[0]
        for field in ("status", "flag", "text", "read_tool_called", "read_succeeded"):
            _require(_same(opportunity.get(field), first[field]), "opportunity does not match repeat zero")
        verdict = (None if first["status"] == "not_executed" else
                   "flag" if first["flag"] is True else "clear" if first["flag"] is False else "unavailable")
        _require(opportunity["verdict"] == verdict, "opportunity verdict does not match repeat zero")
    _require(type(trace["check_invocations"]) is int
             and trace["check_invocations"] == sum(c["call_receipt"] is not None for c in checks),
             "check invocation count mismatch")
    _control_flow_v2(trace, condition)
    return trace


def audit_bundle(run_dir: Path) -> dict[str, Any]:
    """Dispatch by recorded version without upgrading or modifying saved data."""
    run_dir = Path(run_dir)
    try:
        version = json.loads((run_dir / "trace.json").read_text()).get("schema_version")
        if version == "offline-fixture-0.1":
            return _audit_v1(run_dir)
        if version == "offline-fixture-0.2":
            return _audit_v2(run_dir)
        if version == "live-0.2":
            from .live_artifacts import audit_live_bundle

            return audit_live_bundle(run_dir)
        raise InvalidBundle("unsupported schema version")
    except InvalidBundle:
        raise
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise InvalidBundle(f"invalid saved bundle: {type(exc).__name__}: {exc}") from exc


def summarize(output_root: Path) -> dict[str, Any]:
    output_root = Path(output_root)
    paths = ([output_root] if any((output_root / name).is_file()
                                 for name in ("trace.json", "manifest.json")) else
             sorted({p.parent for name in ("trace.json", "manifest.json")
                     for p in output_root.glob("*/" + name)}))
    _require(bool(paths), "no saved bundles found")
    traces = [audit_bundle(p) for p in paths]
    live = [t for t in traces if t["schema_version"] == "live-0.2"]
    if live:
        _require(len(live) == len(traces),
                 "mixed live and fixture bundles: summarize each evidence set separately")
        from .live_artifacts import summarize_live

        return summarize_live(paths)
    result = {"evidence_kind": "synthetic_fixture", "study_results_generated": False,
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
    v2 = [t for t in traces if t["schema_version"] == "offline-fixture-0.2"]
    if v2:
        opportunities = [o for t in v2 for o in t["checker_opportunities"]]
        evaluations = [c for t in v2 for c in t["checks"]]
        result.update(checker_opportunities=len(opportunities),
                      opportunity_status_counts=dict(Counter(o["status"] for o in opportunities)),
                      read_diagnostics={
                          "scope": "offline-fixture-0.2 only; descriptive fixture counts, not study estimates",
                          "legacy_runs_without_read_instrumentation": len(traces) - len(v2),
                          "opportunities_read_tool_called": sum(o["read_tool_called"] is True for o in opportunities),
                          "opportunities_read_succeeded": sum(o["read_succeeded"] is True for o in opportunities),
                          "evaluations": len(evaluations),
                          "evaluations_read_tool_called": sum(c["read_tool_called"] is True for c in evaluations),
                          "evaluations_read_succeeded": sum(c["read_succeeded"] is True for c in evaluations),
                          "evaluations_read_unavailable": sum(c["read_tool_called"] is True and c["read_succeeded"] is False
                                                              for c in evaluations),
                      })
    return result
