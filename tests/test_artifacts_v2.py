"""Replay v0.2 checker evidence while preserving the committed v0.1 bundles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from swarm_handoff.artifacts import InvalidBundle, audit_bundle, summarize
from swarm_handoff.contracts import (AgentResponse, CheckResponse, Condition,
                                     FixtureScoring, RunConfig, canonical_bytes, clone, digest)
from swarm_handoff.runner import run_offline


REPO = Path(__file__).resolve().parents[1]
RECORD = {"reference_code": "AB12CD34EF56", "values": [2, 3, 5]}


def carry(request, tools):
    if request.agent_id == "A":
        record = tools.call("fetch_record")
        tools.call("write_record", {"record": record})
    else:
        record = clone(request.input_payload["asserted"]["record"])
    asserted = {"record": record}
    if request.agent_id == "C":
        asserted["verdict"] = "pass"
    return AgentResponse({"asserted": asserted, "inherited": clone(request.input_payload)},
                         True, "Synthetic callback only.")


def read_and_flag(request, tools):
    tools.call("read_artifact")
    return CheckResponse(True, "Synthetic flag; no adjudicated detection.")


def no_read(request, tools):
    return CheckResponse(True, "Synthetic flag without an artifact read.")


class ArtifactV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, *, condition=Condition.INJECT_HANDOFF, repeats=1,
                checker=read_and_flag, agents=None, run_id="fixture", scoring=FixtureScoring()):
        return run_offline(RunConfig(run_id, condition, repeats), self.root, RECORD,
                           agents or {a: carry for a in "ABCD"}, checker, scoring=scoring)

    def reseal(self, trace):
        directory = self.root / trace["run_id"]
        (directory / "trace.json").write_bytes(canonical_bytes(trace))
        for name, rows in (("steps.jsonl", trace["steps"]), ("checks.jsonl", trace["checks"]),
                           ("checker_opportunities.jsonl", trace["checker_opportunities"])):
            (directory / name).write_bytes(b"".join(canonical_bytes(row) + b"\n" for row in rows))
        manifest = json.loads((directory / "manifest.json").read_text())
        manifest["files"] = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                             if (directory / name).exists() else None for name in manifest["files"]}
        manifest["missing_files"] = [name for name, value in manifest["files"].items() if value is None]
        (directory / "manifest.json").write_bytes(canonical_bytes(manifest))

    def assert_rejected(self, trace, message):
        self.reseal(trace)
        with self.assertRaisesRegex(InvalidBundle, message):
            audit_bundle(self.root / trace["run_id"])

    def test_all_four_committed_legacy_examples_and_summary_are_unchanged(self):
        examples = REPO / "examples/offline"
        originals = {path: path.read_bytes() for path in examples.rglob("*") if path.is_file()}
        bundles = sorted(examples.glob("*/manifest.json"))
        self.assertEqual(len(bundles), 4)
        for manifest in bundles:
            trace = audit_bundle(manifest.parent)
            self.assertEqual(trace["schema_version"], "offline-fixture-0.1")
        self.assertEqual(summarize(examples), json.loads((examples / "fixture-summary.json").read_text()))
        self.assertTrue(all(path.read_bytes() == content for path, content in originals.items()))

    def test_opportunities_are_not_inflated_by_repeated_evaluations(self):
        self.fixture(repeats=5)
        trace = audit_bundle(self.root / "fixture")
        self.assertEqual(len(trace["checker_opportunities"]), 3)
        self.assertEqual(len(trace["checks"]), 15)
        result = summarize(self.root)
        self.assertEqual(result["checker_opportunities"], 3)
        self.assertEqual(result["check_invocations"], 15)
        self.assertEqual(result["read_diagnostics"]["opportunities_read_succeeded"], 3)
        self.assertEqual(result["read_diagnostics"]["evaluations_read_succeeded"], 15)
        self.assertEqual(result["provider_api_calls"], 0)
        self.assertFalse(result["study_results_generated"])
        self.assertIsNone(result["confirmed_detections"])

    def test_no_read_flag_remains_valid_without_becoming_confirmed_detection(self):
        self.fixture(checker=no_read)
        trace = audit_bundle(self.root / "fixture")
        for check in trace["checks"]:
            self.assertTrue(check["flag"])
            self.assertEqual(check["tool_calls"], [])
            self.assertFalse(check["read_tool_called"])
            self.assertFalse(check["read_succeeded"])
            self.assertIsNone(check["detection"])

    def test_read_returns_saved_actual_artifact_in_clean_and_injected_runs(self):
        for condition in (Condition.CLEAN_END, Condition.INJECT_END):
            with self.subTest(condition=condition):
                self.fixture(condition=condition, run_id=condition.value)
                trace = audit_bundle(self.root / condition.value)
                result = trace["checks"][0]["tool_calls"][0]["result"]
                self.assertEqual(set(result), {"ok", "content_utf8"})
                self.assertEqual(json.loads(result["content_utf8"]), {} if condition.injected else RECORD)

    def test_repeat_input_is_detached_and_auditable_after_callback_mutation(self):
        def mutating(request, tools):
            request.transcript.clear()
            request.available_tools.clear()
            result = tools.call("read_artifact")
            result["content_utf8"] = "invented by callback"
            return CheckResponse(False, "Synthetic clear.")
        self.fixture(checker=mutating, repeats=5)
        trace = audit_bundle(self.root / "fixture")
        self.assertTrue(all(check["input"]["transcript"] for check in trace["checks"]))
        self.assertTrue(all(check["tool_calls"][0]["result"]["content_utf8"] == "{}"
                            for check in trace["checks"]))

    def test_denied_tools_are_logged_without_becoming_successful_reads(self):
        def denied(request, tools):
            tools.call("write_record", {"record": {}})
            tools.call("read_artifact", {"path": "private-metadata.json"})
            return CheckResponse(False, "Denied tool requests.")
        self.fixture(checker=denied)
        trace = audit_bundle(self.root / "fixture")
        for check in trace["checks"]:
            self.assertTrue(check["read_tool_called"])
            self.assertFalse(check["read_succeeded"])
            self.assertEqual([call["result"]["error"] for call in check["tool_calls"]],
                             ["tool_not_available", "invalid_arguments"])

    def test_resealed_read_result_cannot_substitute_expected_record_for_actual_file(self):
        trace = self.fixture()
        trace["checks"][0]["tool_calls"][0]["result"]["content_utf8"] = json.dumps(RECORD)
        self.assert_rejected(trace, "frozen artifact snapshot")

    def test_resealed_final_file_still_has_to_match_its_recorded_observation(self):
        trace = self.fixture()
        (self.root / "fixture/artifact.json").write_bytes(canonical_bytes(RECORD))
        self.assert_rejected(trace, "final artifact differs")

    def test_unavailable_read_is_preserved_as_error_and_not_empty_content(self):
        unavailable = {"status": "unavailable", "content_utf8": None,
                       "sha256": None, "error": "PermissionError"}
        with patch("swarm_handoff.runner.capture_artifact_snapshot", return_value=unavailable):
            trace = self.fixture()
        audit_bundle(self.root / "fixture")
        for check in trace["checks"]:
            self.assertTrue(check["read_tool_called"])
            self.assertFalse(check["read_succeeded"])
            self.assertEqual(check["tool_calls"][0]["result"], {"ok": False, "error": "PermissionError"})
        trace["checks"][0]["tool_calls"][0]["result"] = {"ok": True, "content_utf8": "{}"}
        self.assert_rejected(trace, "frozen artifact snapshot")

    def test_resealed_snapshot_cannot_disagree_with_boundary_observation(self):
        trace = self.fixture()
        snapshot = trace["checker_opportunities"][0]["artifact_snapshot"]
        snapshot["content_utf8"] = json.dumps(RECORD)
        snapshot["sha256"] = hashlib.sha256(snapshot["content_utf8"].encode()).hexdigest()
        trace["checks"][0]["artifact_snapshot_sha256"] = snapshot["sha256"]
        trace["checks"][0]["tool_calls"][0]["result"]["content_utf8"] = snapshot["content_utf8"]
        self.assert_rejected(trace, "boundary observation")

    def test_resealed_snapshot_identity_cannot_change_between_repeats(self):
        trace = self.fixture(repeats=5)
        trace["checks"][1]["artifact_snapshot_sha256"] = "0" * 64
        self.assert_rejected(trace, "snapshot identity")

    def test_resealed_read_summary_must_replay_the_tool_log(self):
        trace = self.fixture()
        trace["checks"][0]["read_succeeded"] = False
        trace["checker_opportunities"][0]["read_succeeded"] = False
        self.assert_rejected(trace, "read diagnostics")

    def test_resealed_successful_write_tool_is_not_allowed_for_a_checker(self):
        trace = self.fixture()
        trace["checks"][0]["tool_calls"][0] = {
            "tool": "write_record", "arguments": {"record": {}}, "result": {"ok": True}}
        self.assert_rejected(trace, "frozen artifact snapshot")

    def test_resealed_expected_metadata_cannot_enter_a_checker_input(self):
        trace = self.fixture()
        for row in (trace["checks"][0], trace["checker_opportunities"][0]):
            row["input"]["held_record"] = clone(RECORD)
            row["input_sha256"] = digest(row["input"])
        self.assert_rejected(trace, "permitted transcript")

    def test_resealed_private_metadata_cannot_enter_tool_results(self):
        trace = self.fixture()
        trace["checks"][0]["tool_calls"][0]["result"]["oracle_truth"] = False
        self.assert_rejected(trace, "frozen artifact snapshot")

    def test_resealed_checker_flags_cannot_move_into_task_step_records(self):
        trace = self.fixture()
        trace["steps"][0]["verifier_verdict"] = "flag"
        self.assert_rejected(trace, "isolated from step records")

    def test_opportunity_summary_is_repeat_zero_and_not_any_repeat(self):
        counter = iter(range(15))
        def alternating(request, tools):
            return CheckResponse(next(counter) % 2 == 1, "Synthetic repeated verdict.")
        trace = self.fixture(checker=alternating, repeats=5)
        trace["checker_opportunities"][0]["flag"] = True
        trace["checker_opportunities"][0]["verdict"] = "flag"
        self.assert_rejected(trace, "repeat zero")

    def test_resealed_opportunity_and_evaluation_coverage_cannot_shrink(self):
        trace = self.fixture()
        trace["checker_opportunities"].pop()
        self.assert_rejected(trace, "opportunity schedule")

    def test_resealed_duplicate_evaluation_identity_is_rejected(self):
        trace = self.fixture(repeats=5)
        trace["checks"][1]["evaluation_id"] = trace["checks"][0]["evaluation_id"]
        self.assert_rejected(trace, "evaluation identity")

    def test_resealed_invalid_c_enum_is_rejected_before_scoring(self):
        trace = self.fixture()
        trace["steps"][2]["output_payload"]["asserted"]["verdict"] = "PROPAGATED"
        self.assert_rejected(trace, "C verdict enum")

    def test_resealed_propagation_score_must_be_recomputed(self):
        trace = self.fixture()
        trace["steps"][1]["propagation"]["propagated"] = False
        self.assert_rejected(trace, "propagation replay")

    def test_flags_do_not_turn_into_adjudicated_detections(self):
        trace = self.fixture()
        trace["checks"][0]["detection"] = True
        self.assert_rejected(trace, "adjudicated detection")

    def test_completed_flag_replays_the_recorded_callback_response(self):
        trace = self.fixture()
        trace["checks"][0]["flag"] = False
        trace["checker_opportunities"][0]["flag"] = False
        trace["checker_opportunities"][0]["verdict"] = "clear"
        self.assert_rejected(trace, "raw response replay")

    def test_resealed_completed_check_cannot_be_relabelled_as_skipped(self):
        trace = self.fixture()
        check, opportunity = trace["checks"][0], trace["checker_opportunities"][0]
        check.update(status="not_executed", flag=None, text=None, call_receipt=None,
                     raw_response=None, tool_calls=[], read_tool_called=None, read_succeeded=None,
                     error="incomplete_chain_fixture_policy")
        opportunity.update(status="not_executed", flag=None, text=None, verdict=None,
                           read_tool_called=None, read_succeeded=None)
        trace["check_invocations"] -= 1
        self.assert_rejected(trace, "checker execution eligibility replay")

    def test_resealed_failed_run_cannot_be_relabelled_as_completed(self):
        def timed_out(*args):
            raise TimeoutError("synthetic agent timeout")
        agents = {a: carry for a in "ABCD"}
        agents["B"] = timed_out
        trace = self.fixture(agents=agents)
        trace.update(run_status="completed", excluded=False, exclusion_reason=None)
        self.assert_rejected(trace, "run status replay")

    def test_timeout_after_read_keeps_read_evidence_and_no_verdict(self):
        def timed_out(request, tools):
            tools.call("read_artifact")
            raise TimeoutError("synthetic checker timeout")
        self.fixture(checker=timed_out)
        trace = audit_bundle(self.root / "fixture")
        for opportunity in trace["checker_opportunities"]:
            self.assertEqual(opportunity["status"], "timeout")
            self.assertTrue(opportunity["read_succeeded"])
            self.assertIsNone(opportunity["flag"])
            self.assertEqual(opportunity["verdict"], "unavailable")

    def test_skipped_opportunities_have_unknown_read_state(self):
        def timed_out(*args):
            raise TimeoutError("synthetic agent timeout")
        agents = {a: carry for a in "ABCD"}
        agents["A"] = timed_out
        self.fixture(agents=agents)
        trace = audit_bundle(self.root / "fixture")
        for opportunity in trace["checker_opportunities"]:
            self.assertEqual(opportunity["status"], "not_executed")
            self.assertIsNone(opportunity["read_tool_called"])
            self.assertIsNone(opportunity["read_succeeded"])
            self.assertIsNone(opportunity["verdict"])

    def test_mixed_summary_does_not_invent_read_observations_for_legacy_runs(self):
        source = REPO / "examples/offline/fixture_clean_end_monitor"
        shutil.copytree(source, self.root / source.name)
        self.fixture(condition=Condition.CLEAN_END)
        result = summarize(self.root)
        self.assertEqual(result["runs"], 2)
        self.assertEqual(result["checker_opportunities"], 1)
        self.assertEqual(result["read_diagnostics"]["legacy_runs_without_read_instrumentation"], 1)
        self.assertEqual(result["read_diagnostics"]["evaluations_read_succeeded"], 1)


if __name__ == "__main__":
    unittest.main()
