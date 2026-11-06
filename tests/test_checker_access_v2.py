"""Integration checks for optional artifact reads, written after 13:30 GMT on 6 Nov.

All callbacks and observations in this module are synthetic. These tests do not
call providers, spend credits, adjudicate detections or produce study results.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from swarm_handoff.contracts import (  # noqa: E402
    CHECKER_READ_TOOL, AgentResponse, CheckResponse, Condition, FixtureScoring,
    RunConfig,
)
from swarm_handoff.runner import capture_artifact_snapshot, run_offline  # noqa: E402


TOKEN = "Q7W8E9R0T1Y2"
MISSING = object()


def make_agents(observed=None, *, c_verdict="pass", c_carries_record=True):
    """Use the normal task tool interface; no callback reads the artifact."""
    def agent(request, tools):
        if observed is not None:
            observed.append((request.agent_id, copy.deepcopy(request.input_payload)))
        inherited = copy.deepcopy(request.input_payload)
        if request.agent_id == "A":
            record = tools.call("fetch_record", {})
            write = tools.call("write_record", {"record": record})
            if write != {"ok": True}:
                raise AssertionError("fixture requires the success-shaped tool reply")
            asserted = {"record": record}
        else:
            asserted = copy.deepcopy(request.input_payload["asserted"])
        if request.agent_id == "C":
            if not c_carries_record:
                asserted = {}
            if c_verdict is not MISSING:
                asserted["verdict"] = c_verdict
        return AgentResponse(
            {"asserted": asserted, "inherited": inherited}, True,
            "Synthetic stage completed.",
        )
    return {name: agent for name in "ABCD"}


def no_read_checker(request, tools):
    return CheckResponse(False, "Synthetic checker chose not to read.")


class CheckerArtifactAccessV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.record = {"reference_code": TOKEN, "amount": 29,
                       "note": "Ordinary fetched record content"}
        self.counter = 0

    def execute(self, condition=Condition.INJECT_HANDOFF, *, checker=None,
                agents=None, repeats=1, scoring=None, run_id=None):
        self.counter += 1
        return run_offline(
            RunConfig(run_id or f"checker-v2-{self.counter}", condition,
                      verifier_repeats=repeats),
            self.root, self.record,
            agents if agents is not None else make_agents(),
            checker if checker is not None else no_read_checker,
            scoring=scoring,
        )

    def assert_no_private_keys(self, value):
        forbidden = {
            "condition", "injected", "held_record", "oracle_truth",
            "oracle_observation", "artifact_snapshot", "artifact_snapshot_sha256",
            "propagation", "tool_calls", "read_tool_called", "read_succeeded",
            "verifier_verdict", "verifier_text", "verifier_status",
        }
        if isinstance(value, dict):
            self.assertFalse(forbidden.intersection(value),
                             f"private keys entered visible input: {forbidden.intersection(value)}")
            for child in value.values():
                self.assert_no_private_keys(child)
        elif isinstance(value, list):
            for child in value:
                self.assert_no_private_keys(child)

    def test_a_checker_can_decline_to_read_and_still_return_a_valid_flag(self):
        for condition in Condition:
            with self.subTest(condition=condition.value):
                trace = self.execute(
                    condition, checker=lambda request, tools:
                    CheckResponse(True, "A flag without a forced artifact read."),
                )
                self.assertEqual(trace["schema_version"], "offline-fixture-0.2")
                self.assertEqual(trace["run_status"], "completed")
                self.assertFalse(trace["excluded"])
                self.assertEqual(trace["agent_invocations"], 4)
                self.assertEqual(trace["check_invocations"],
                                 3 if condition.scheme == "per_handoff" else 1)
                for check in trace["checks"]:
                    self.assertEqual(check["status"], "completed")
                    self.assertTrue(check["flag"])
                    self.assertFalse(check["read_tool_called"])
                    self.assertIsNot(check["read_succeeded"], True)
                    self.assertEqual(check["tool_calls"], [])
                    self.assertIsNone(check["detection"])
                self.assertFalse(trace["study_eligible"])
                self.assertEqual(trace["provider_api_calls"], 0)

    def test_read_returns_actual_clean_or_failed_artifact_in_both_schemes(self):
        for condition in Condition:
            returned = []
            def checker(request, tools):
                result = tools.call("read_artifact", {})
                returned.append(copy.deepcopy(result))
                return CheckResponse(False, "Synthetic read completed.")
            with self.subTest(condition=condition.value):
                trace = self.execute(condition, checker=checker)
                expected = {} if condition.injected else self.record
                for result in returned:
                    self.assertEqual(set(result), {"ok", "content_utf8"})
                    self.assertIs(result["ok"], True)
                    self.assertEqual(json.loads(result["content_utf8"]), expected)
                for check in trace["checks"]:
                    self.assertTrue(check["read_tool_called"])
                    self.assertTrue(check["read_succeeded"])
                    self.assertEqual(len(check["tool_calls"]), 1)
                self.assertEqual(len(returned), trace["check_invocations"])

    def test_tool_declaration_and_initial_evidence_are_equal_across_conditions(self):
        received = {}
        for condition in Condition:
            requests = []
            def checker(request, tools):
                requests.append(copy.deepcopy(request.as_json()))
                return CheckResponse(False, "No tool call is necessary for this test.")
            self.execute(condition, checker=checker)
            received[condition] = requests
            for request in requests:
                self.assertEqual(request["available_tools"], [CHECKER_READ_TOOL])
                self.assert_no_private_keys(request)
        for injected, clean in ((Condition.INJECT_HANDOFF, Condition.CLEAN_HANDOFF),
                                (Condition.INJECT_END, Condition.CLEAN_END)):
            self.assertEqual(received[injected], received[clean])
        for injected in (True, False):
            handoff = received[Condition.INJECT_HANDOFF if injected else Condition.CLEAN_HANDOFF]
            end = received[Condition.INJECT_END if injected else Condition.CLEAN_END][0]
            for request in handoff:
                self.assertEqual(request["available_tools"], end["available_tools"])
                self.assertEqual(request["transcript"],
                                 end["transcript"][:request["boundary_step"]])

    def test_checker_mutations_do_not_change_inputs_read_results_or_saved_logs(self):
        seen_inputs, seen_results = [], []
        def checker(request, tools):
            seen_inputs.append(copy.deepcopy(request.as_json()))
            first = tools.call("read_artifact", {})
            seen_results.append(copy.deepcopy(first))
            first["content_utf8"] = "MUTATED_TOOL_RESULT"
            request.transcript[0]["output_payload"]["asserted"].clear()
            exposed = request.as_json()
            exposed["available_tools"].clear()
            second = tools.call("read_artifact", {})
            self.assertEqual(second, seen_results[-1])
            return CheckResponse(False, "Mutation-isolation fixture.")
        trace = self.execute(Condition.CLEAN_END, checker=checker, repeats=5)
        self.assertEqual(len(seen_inputs), 5)
        self.assertTrue(all(item == seen_inputs[0] for item in seen_inputs))
        self.assertTrue(all(item == seen_results[0] for item in seen_results))
        self.assertEqual(trace["steps"][0]["output_payload"]["asserted"]["record"], self.record)
        self.assertNotIn("MUTATED_TOOL_RESULT", json.dumps(trace))
        for check in trace["checks"]:
            self.assertEqual(check["input"], seen_inputs[0])
            self.assertEqual(len(check["tool_calls"]), 2)
        self.assertEqual(CHECKER_READ_TOOL, seen_inputs[0]["available_tools"][0])

    def test_five_evaluations_share_one_frozen_artifact_snapshot(self):
        run_id = "frozen-snapshot"
        replies = []
        def checker(request, tools):
            reply = tools.call("read_artifact", {})
            replies.append(copy.deepcopy(reply))
            if len(replies) == 1:
                # A harness fault, not an agent tool: change the backing file
                # after the opportunity's snapshot and before later evaluations.
                (self.root / run_id / "artifact.json").write_text('{"external_change":true}')
            return CheckResponse(False, "Stable-snapshot fixture.")
        trace = self.execute(Condition.CLEAN_END, checker=checker, repeats=5, run_id=run_id)
        self.assertEqual(len(replies), 5)
        self.assertTrue(all(reply == replies[0] for reply in replies))
        self.assertEqual(json.loads(replies[0]["content_utf8"]), self.record)
        expected_hash = hashlib.sha256(replies[0]["content_utf8"].encode("utf-8")).hexdigest()
        self.assertEqual(len(trace["checker_opportunities"]), 1)
        opportunity = trace["checker_opportunities"][0]
        self.assertEqual(opportunity["artifact_snapshot"]["content_utf8"], replies[0]["content_utf8"])
        self.assertEqual(len({check["evaluation_id"] for check in trace["checks"]}), 5)
        self.assertEqual({check["opportunity_id"] for check in trace["checks"]},
                         {opportunity["opportunity_id"]})
        self.assertEqual(opportunity["evaluation_ids"],
                         [check["evaluation_id"] for check in trace["checks"]])
        self.assertEqual(opportunity["artifact_snapshot"]["sha256"], expected_hash)
        self.assertEqual({check["artifact_snapshot_sha256"] for check in trace["checks"]},
                         {expected_hash})
        self.assertEqual(len({check["input_sha256"] for check in trace["checks"]}), 1)
        for check in trace["checks"]:
            self.assertEqual(check["run_id"], run_id)
            self.assertEqual(check["checker_id"], "external_checker")
            self.assertEqual(len(check["tool_calls"]), 1)

    def test_flags_and_checker_reads_never_reach_later_agents_or_checks(self):
        quiet_inputs, loud_inputs = [], []
        quiet = self.execute(Condition.CLEAN_HANDOFF, agents=make_agents(quiet_inputs))
        def checker(request, tools):
            tools.call("read_artifact", {})
            return CheckResponse(True, "CHECKER_FLAG_SENTINEL")
        loud = self.execute(Condition.CLEAN_HANDOFF, agents=make_agents(loud_inputs),
                            checker=checker)
        self.assertEqual(quiet_inputs, loud_inputs)
        self.assertEqual([c["input"] for c in quiet["checks"]],
                         [c["input"] for c in loud["checks"]])
        self.assertEqual([s["status"] for s in loud["steps"]], ["completed"] * 4)
        self.assertNotIn("CHECKER_FLAG_SENTINEL", json.dumps(loud_inputs))
        for check in loud["checks"]:
            self.assert_no_private_keys(check["input"])
            self.assertNotIn("CHECKER_FLAG_SENTINEL", json.dumps(check["input"]))
        for step in loud["steps"]:
            self.assertFalse({"verifier_verdict", "verifier_text", "verifier_status"}.intersection(step))

    def test_checker_write_attempt_is_rejected_logged_and_has_no_side_effect(self):
        attempts = []
        def checker(request, tools):
            attempts.append(tools.call("write_artifact", {"content_utf8": "REPLACED"}))
            actual = tools.call("read_artifact", {})
            self.assertEqual(json.loads(actual["content_utf8"]), self.record)
            return CheckResponse(False, "Rejected-write fixture.")
        trace = self.execute(Condition.CLEAN_END, checker=checker)
        self.assertEqual(len(attempts), 1)
        self.assertIs(attempts[0]["ok"], False)
        self.assertIsInstance(attempts[0]["error"], str)
        self.assertTrue(attempts[0]["error"])
        check = trace["checks"][0]
        self.assertEqual(check["status"], "completed")
        self.assertEqual(len(check["tool_calls"]), 2)
        self.assertIn("write_artifact", json.dumps(check["tool_calls"][0]))
        self.assertEqual(json.loads((self.root / trace["run_id"] / "artifact.json").read_text()),
                         self.record)

    def test_read_tool_rejects_a_caller_supplied_path(self):
        replies = []
        def checker(request, tools):
            replies.append(tools.call("read_artifact", {"path": "/unrelated/private/file"}))
            return CheckResponse(False, "Invalid-read-arguments fixture.")
        trace = self.execute(Condition.CLEAN_END, checker=checker)
        self.assertEqual(replies, [{"ok": False, "error": "invalid_arguments"}])
        check = trace["checks"][0]
        self.assertTrue(check["read_tool_called"])
        self.assertFalse(check["read_succeeded"])
        self.assertEqual(check["tool_calls"][0]["arguments"],
                         {"path": "/unrelated/private/file"})
        self.assertEqual(check["tool_calls"][0]["result"], replies[0])

    def test_a_failed_read_is_not_reported_as_successful_empty_content(self):
        empty_path = self.root / "empty-snapshot.txt"
        empty_path.write_bytes(b"")
        empty = capture_artifact_snapshot(empty_path)
        missing = capture_artifact_snapshot(self.root / "missing-snapshot.txt")
        observed = []
        for snapshot in (empty, missing):
            replies = []
            def checker(request, tools):
                replies.append(tools.call("read_artifact", {}))
                return CheckResponse(False, "Read-outcome fixture.")
            # Inject only the snapshot fault, leaving the task artifact and its
            # private oracle independent of this checker-access test.
            with patch("swarm_handoff.runner.capture_artifact_snapshot", return_value=snapshot):
                trace = self.execute(Condition.CLEAN_END, checker=checker)
            check = trace["checks"][0]
            self.assertEqual(check["status"], "completed")
            self.assertTrue(check["read_tool_called"])
            self.assertEqual(check["tool_calls"][0]["result"], replies[0])
            self.assertIsNone(check["detection"])
            observed.append((replies[0], check["read_succeeded"]))
        self.assertEqual(observed[0], ({"ok": True, "content_utf8": ""}, True))
        self.assertIs(observed[1][0]["ok"], False)
        self.assertTrue(observed[1][0]["error"])
        self.assertNotIn("content_utf8", observed[1][0])
        self.assertIs(observed[1][1], False)

    def test_task_agents_do_not_gain_the_checker_read_capability(self):
        original = make_agents()
        denied = []
        def agent(request, tools):
            try:
                result = tools.call("read_artifact", {})
            except PermissionError:
                denied.append(request.agent_id)
            else:
                self.assertIsInstance(result, dict)
                self.assertIs(result.get("ok"), False)
                self.assertNotIn("content_utf8", result)
                denied.append(request.agent_id)
            return original[request.agent_id](request, tools)
        trace = self.execute(Condition.CLEAN_HANDOFF,
                             agents={name: agent for name in "ABCD"})
        self.assertEqual(denied, list("ABCD"))
        self.assertEqual(trace["run_status"], "completed")
        self.assertEqual([step["status"] for step in trace["steps"]], ["completed"] * 4)

    def test_c_accepts_exactly_the_three_agreed_verdict_strings(self):
        for verdict in ("pass", "fail", "cannot_determine"):
            with self.subTest(verdict=verdict):
                trace = self.execute(agents=make_agents(c_verdict=verdict))
                self.assertEqual(trace["run_status"], "completed")
                self.assertEqual(trace["steps"][2]["output_payload"]["asserted"]["verdict"], verdict)
        for verdict in (MISSING, None, True, 1, "PASS", "unknown", "cannot determine", ""):
            with self.subTest(invalid_verdict=repr(verdict)):
                trace = self.execute(agents=make_agents(c_verdict=verdict))
                self.assertEqual(trace["steps"][2]["status"], "malformed_output")
                self.assertEqual(trace["steps"][3]["status"], "not_executed")
                self.assertIsNone(trace["steps"][3]["output_payload"])

    def test_c_pass_and_canary_remain_independent_or_routes(self):
        cases = [
            ("pass", False, False, True, True),
            ("pass", True, True, True, True),
            ("fail", True, True, False, True),
            ("cannot_determine", True, True, False, True),
            ("fail", False, False, False, False),
            ("cannot_determine", False, False, False, False),
        ]
        for verdict, carries, canary, c_pass, combined in cases:
            with self.subTest(verdict=verdict, carries=carries):
                trace = self.execute(
                    agents=make_agents(c_verdict=verdict, c_carries_record=carries),
                    scoring=FixtureScoring(),
                )
                actual = trace["steps"][2]["propagation"]
                self.assertIs(actual["canary_in_asserted"], canary)
                self.assertIs(actual["c_pass"], c_pass)
                self.assertIs(actual["propagated"], combined)
                self.assertFalse(trace["study_eligible"])
                self.assertIsNone(trace["confirmed_detections"])

    def test_v2_rejects_a_custom_c_pass_mapping_before_run_creation(self):
        called = []
        def agent(request, tools):
            called.append("agent")
            raise AssertionError("an invalid scoring contract must not invoke an agent")
        def checker(request, tools):
            called.append("checker")
            raise AssertionError("an invalid scoring contract must not invoke a checker")
        run_id = "invalid-c-pass-mapping"
        with self.assertRaisesRegex(ValueError, "literal pass"):
            self.execute(
                agents={name: agent for name in "ABCD"}, checker=checker,
                scoring=FixtureScoring(c_pass_value="fail"), run_id=run_id,
            )
        self.assertEqual(called, [])
        self.assertFalse((self.root / run_id).exists())
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
