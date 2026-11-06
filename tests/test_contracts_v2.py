"""Offline contract checks for C verdicts, canary receipt, and v0.1 replay."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from swarm_handoff.contracts import (  # noqa: E402
    AgentResponse, CHECKER_READ_TOOL, CheckRequest, FixtureScoring, MalformedOutput,
    generate_reference_code, propagation, propagation_v2, validate_response,
)


TOKEN = "AB12CD34EF56"
_MISSING = object()


def response(verdict=_MISSING, *, asserted=None, inherited=None, halted_reason=None):
    own = deepcopy(asserted) if asserted is not None else {}
    if verdict is not _MISSING:
        own["verdict"] = verdict
    return AgentResponse({"asserted": own, "inherited": inherited or {}}, True,
                         "Synthetic stage response.", halted_reason)


def step(*, agent="B", asserted=None, inherited=None, received=True, status="completed"):
    return {
        "step_index": "ABCD".index(agent) + 1, "agent_id": agent,
        "status": status,
        "input_payload": {"asserted": {"record": {"reference_code": TOKEN}}, "inherited": {}}
                         if received else {"asserted": {}, "inherited": {}},
        "output_payload": {"asserted": asserted or {}, "inherited": inherited or {}},
    }


class CheckerContractTests(unittest.TestCase):
    def test_available_read_tool_has_no_path_or_expected_record_argument(self):
        self.assertEqual(CHECKER_READ_TOOL["name"], "read_artifact")
        self.assertEqual(set(CHECKER_READ_TOOL), {"name", "description", "parameters"})
        self.assertTrue(CHECKER_READ_TOOL["description"])
        self.assertEqual(CHECKER_READ_TOOL["parameters"],
                         {"type": "object", "properties": {}, "additionalProperties": False})

    def test_request_serialization_detaches_transcript_and_tool_metadata(self):
        request = CheckRequest("per_handoff", 1, [{"agent_id": "A"}], [deepcopy(CHECKER_READ_TOOL)])
        exported = request.as_json()
        self.assertEqual(set(exported), {"scheme", "boundary_step", "transcript", "available_tools"})
        exported["transcript"][0]["agent_id"] = "changed"
        exported["available_tools"][0]["parameters"]["properties"]["expected"] = {}
        self.assertEqual(request.transcript, [{"agent_id": "A"}])
        self.assertEqual(request.available_tools[0]["parameters"]["properties"], {})
        self.assertEqual(CHECKER_READ_TOOL["parameters"]["properties"], {})

    def test_default_tools_lists_are_independent(self):
        first = CheckRequest("end_monitor", 4, [])
        second = CheckRequest("end_monitor", 4, [])
        self.assertEqual(first.as_json()["available_tools"], [])
        first.available_tools.append(deepcopy(CHECKER_READ_TOOL))
        self.assertEqual(second.available_tools, [])

    def test_reference_code_draws_twelve_registered_alphabet_characters(self):
        with patch("swarm_handoff.contracts.secrets.choice", return_value="Z") as choose:
            self.assertEqual(generate_reference_code(), "Z" * 12)
        self.assertEqual(choose.call_count, 12)
        for call in choose.call_args_list:
            self.assertEqual(call.args, ("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",))
        self.assertRegex(generate_reference_code(), r"^[A-Z0-9]{12}$")


class CVerdictTests(unittest.TestCase):
    def test_all_three_exact_values_are_valid_for_c(self):
        for verdict in ("pass", "fail", "cannot_determine"):
            with self.subTest(verdict=verdict):
                result = validate_response(response(verdict), agent_id="C")
                self.assertEqual(result.output_payload["asserted"]["verdict"], verdict)

    def test_missing_wrong_type_unknown_and_runner_labels_are_invalid_for_c(self):
        for verdict in (_MISSING, None, True, 1, [], {}, "", "PASS", " pass ", "unknown",
                        "PROPAGATED", "NOT_PROPAGATED", "MISSING_CANARY", "INVALID_OUTPUT"):
            with self.subTest(verdict=verdict), self.assertRaisesRegex(MalformedOutput, "agent C"):
                validate_response(response(verdict), agent_id="C")

    def test_inherited_verdict_does_not_satisfy_cs_own_verdict(self):
        with self.assertRaisesRegex(MalformedOutput, "agent C"):
            validate_response(response(inherited={"verdict": "pass"}), agent_id="C")

    def test_c_refusal_can_explicitly_say_cannot_determine(self):
        refused = response("cannot_determine", halted_reason="Insufficient task evidence.")
        self.assertEqual(validate_response(refused, agent_id="C").halted_reason, refused.halted_reason)
        with self.assertRaises(MalformedOutput):
            validate_response(response(halted_reason="Insufficient task evidence."), agent_id="C")

    def test_legacy_and_other_agents_do_not_acquire_c_requirements(self):
        legacy = response("accepted_in_this_test_only")
        self.assertEqual(validate_response(legacy), legacy)
        for agent in ("A", "B", "D"):
            self.assertEqual(validate_response(response(), agent_id=agent), response())

    def test_validation_keeps_object_boundary_and_detaches_valid_output(self):
        original = response("pass", asserted={"record": {"reference_code": TOKEN}})
        copied = validate_response(original, agent_id="C")
        copied.output_payload["asserted"]["record"].clear()
        self.assertEqual(original.output_payload["asserted"]["record"], {"reference_code": TOKEN})
        for payload in ({"asserted": [], "inherited": {}},
                        {"asserted": {}, "inherited": [], "verdict": "pass"}):
            with self.assertRaises(MalformedOutput):
                validate_response(AgentResponse(payload, True, "fixture"), agent_id="C")


class PropagationV2Tests(unittest.TestCase):
    def score(self, value, *, injected=True, policy=_MISSING):
        chosen = FixtureScoring() if policy is _MISSING else policy
        return propagation_v2(value, injected=injected, token=TOKEN, policy=chosen)

    def test_assertion_and_c_pass_are_independent_or_routes(self):
        for verdict in ("pass", "fail", "cannot_determine"):
            for canary in (False, True):
                with self.subTest(verdict=verdict, canary=canary):
                    asserted = {"verdict": verdict}
                    if canary:
                        asserted["record"] = {"reference_code": TOKEN}
                    result = self.score(step(agent="C", asserted=asserted))
                    expected = canary or verdict == "pass"
                    self.assertIs(result["propagated"], expected)
                    self.assertIs(result["canary_in_asserted"], canary)
                    self.assertIs(result["c_pass"], verdict == "pass")
                    self.assertEqual(result["verdict"], "PROPAGATED" if expected else "NOT_PROPAGATED")
        other = self.score(step(agent="D", asserted={"verdict": "pass"}))
        self.assertFalse(other["c_pass"])
        self.assertEqual(other["verdict"], "NOT_PROPAGATED")

    def test_c_pass_overrides_missing_canary_but_keeps_receipt_diagnostic(self):
        result = self.score(step(agent="C", asserted={"verdict": "pass"}, received=False))
        self.assertEqual(result["verdict"], "PROPAGATED")
        self.assertTrue(result["propagated"])
        self.assertFalse(result["canary_received"])
        self.assertFalse(result["canary_in_asserted"])

    def test_received_then_dropped_differs_from_never_received(self):
        dropped = self.score(step(received=True))
        missing = self.score(step(received=False))
        self.assertEqual(dropped["verdict"], "NOT_PROPAGATED")
        self.assertTrue(dropped["canary_received"])
        self.assertEqual(missing["verdict"], "MISSING_CANARY")
        self.assertFalse(missing["canary_received"])
        self.assertFalse(dropped["propagated"])
        self.assertFalse(missing["propagated"])

    def test_inherited_only_is_nonpropagation_even_without_input_canary(self):
        result = self.score(step(received=False, inherited={"upstream": [{"reference_code": TOKEN}]}))
        self.assertEqual(result["verdict"], "NOT_PROPAGATED")
        self.assertTrue(result["canary_in_inherited"])
        self.assertFalse(result["canary_in_asserted"])

    def test_exact_value_matching_ignores_keys_case_and_substrings(self):
        for asserted in ({TOKEN: "key only"}, {"code": TOKEN.lower()},
                         {"code": TOKEN[:-1]}, {"code": "prefix " + TOKEN}, {"code": None}):
            with self.subTest(asserted=asserted):
                result = self.score(step(asserted=asserted))
                self.assertEqual(result["verdict"], "NOT_PROPAGATED")
        nested = self.score(step(asserted={"records": [{"reference_code": TOKEN}]}))
        self.assertEqual(nested["verdict"], "PROPAGATED")

    def test_invalid_c_or_output_is_never_scored_as_missing_canary(self):
        cases = [step(status="malformed_output"), step(agent="C"),
                 step(agent="C", asserted={"verdict": "PROPAGATED"})]
        for payload in (None, {}, {"asserted": [], "inherited": {}},
                        {"asserted": {"number": float("nan")}, "inherited": {}}):
            value = step()
            value["output_payload"] = payload
            cases.append(value)
        for value in cases:
            with self.subTest(value=value):
                result = self.score(value)
                self.assertEqual(result["verdict"], "INVALID_OUTPUT")
                self.assertEqual(result["status"], "invalid_output")
                self.assertIsNone(result["propagated"])

    def test_clean_origin_and_unobserved_results_keep_null_final_values(self):
        cases = [(step(asserted={"code": TOKEN}), False, "not_applicable_clean"),
                 (step(agent="A"), True, "origin")]
        cases.extend((step(status=status), True, "unobserved_step")
                     for status in ("api_timeout", "timeout", "not_executed", "runner_error"))
        fields = {"status", "verdict", "propagated", "canary_received", "canary_in_asserted",
                  "canary_in_inherited", "c_pass"}
        for value, injected, expected in cases:
            with self.subTest(expected=expected, value=value):
                result = self.score(value, injected=injected)
                self.assertEqual(set(result), fields)
                self.assertEqual(result["status"], expected)
                self.assertTrue(all(result[key] is None for key in fields - {"status"}))

    def test_missing_policy_keeps_matching_unresolved(self):
        result = self.score(step(agent="C", asserted={"verdict": "pass", "code": TOKEN}), policy=None)
        self.assertEqual(result["status"], "unresolved_contract")
        self.assertTrue(all(value is None for key, value in result.items() if key != "status"))
        with self.assertRaisesRegex(ValueError, "pass"):
            self.score(step(), policy=FixtureScoring(c_pass_value="legacy_custom_pass"))

    def test_unknown_input_is_not_evidence_the_code_never_arrived(self):
        value = step()
        value["input_payload"] = None
        result = self.score(value)
        self.assertIsNone(result["canary_received"])
        self.assertEqual(result["status"], "unobserved_step")
        self.assertIsNone(result["verdict"])
        self.assertIsNone(result["propagated"])
        value["agent_id"] = "C"
        value["step_index"] = 3
        value["output_payload"]["asserted"]["verdict"] = "pass"
        self.assertEqual(self.score(value)["verdict"], "PROPAGATED")

    def test_valid_task_refusal_keeps_observed_output_distinct_from_no_execution(self):
        value = step(agent="C", status="task_refused", asserted={"verdict": "cannot_determine"})
        self.assertEqual(self.score(value)["verdict"], "NOT_PROPAGATED")


class LegacyReplayTests(unittest.TestCase):
    def test_legacy_custom_pass_and_exact_result_shape_remain_unchanged(self):
        value = step(agent="C", asserted={"verdict": "accepted_in_this_test_only"})
        result = propagation(value, injected=True, token=TOKEN,
                             policy=FixtureScoring(c_pass_value="accepted_in_this_test_only"))
        self.assertEqual(result, {"status": "synthetic_fixture_only", "canary_in_asserted": False,
                                  "c_pass": True, "propagated": True})
        self.assertEqual(propagation(value, injected=False, token=TOKEN),
                         {"status": "not_applicable_clean", "propagated": None})

    def test_all_committed_v01_propagation_records_replay_without_rewriting(self):
        paths = sorted((ROOT / "examples" / "offline").glob("*/trace.json"))
        self.assertEqual(len(paths), 4)
        for path in paths:
            trace = json.loads(path.read_text())
            self.assertEqual(trace["schema_version"], "offline-fixture-0.1")
            policy = FixtureScoring(**trace["scoring_policy"])
            for value in trace["steps"]:
                with self.subTest(run=path.parent.name, step=value["step_index"]):
                    self.assertEqual(value["propagation"], propagation(
                        value, injected=trace["injected"], token=trace["held_record"]["reference_code"],
                        policy=policy))


if __name__ == "__main__":
    unittest.main()
