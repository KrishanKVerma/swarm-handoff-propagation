"""Failure-receipt and replay regression checks for synthetic fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from swarm_handoff.artifacts import InvalidBundle, audit_bundle, summarize
from swarm_handoff.contracts import (AgentResponse, CheckResponse, Condition,
                                     RunConfig, canonical_bytes)
from swarm_handoff.fixtures import CarryAgent, unsupported_write_flag
from swarm_handoff.runner import observe_file, run_offline


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_fixture(self, **kwargs):
        record = kwargs.pop("record", {"reference_code": "AB12CD34EF56", "values": [2, 3, 5]})
        return run_offline(RunConfig("fixture", Condition.CLEAN_END), self.root, record,
                           kwargs.pop("agents", {a: CarryAgent() for a in "ABCD"}),
                           kwargs.pop("checker", unsupported_write_flag), **kwargs)

    def rewrite(self, trace):
        directory = self.root / "fixture"
        (directory / "trace.json").write_bytes(canonical_bytes(trace))
        for name, rows in (("steps.jsonl", trace["steps"]), ("checks.jsonl", trace["checks"])):
            (directory / name).write_bytes(b"".join(canonical_bytes(r) + b"\n" for r in rows))
        manifest = json.loads((directory / "manifest.json").read_text())
        for name in manifest["files"]:
            if (directory / name).exists():
                manifest["files"][name] = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        (directory / "manifest.json").write_bytes(canonical_bytes(manifest))

    def test_saved_data_replay_preserves_counts_without_generation(self):
        self.run_fixture()
        self.assertEqual(audit_bundle(self.root / "fixture")["run_status"], "completed")
        result = summarize(self.root)
        self.assertEqual(result["agent_invocations"], 4)
        self.assertEqual(result["check_invocations"], 1)
        self.assertEqual(result["provider_api_calls"], 0)
        self.assertFalse(result["study_results_generated"])
        self.assertIsNone(result["confirmed_detections"])

    def test_changed_artifact_fails_integrity_check(self):
        self.run_fixture()
        (self.root / "fixture/artifact.json").write_text('{}')
        with self.assertRaisesRegex(InvalidBundle, "hash mismatch"):
            audit_bundle(self.root / "fixture")

    def test_unknown_schema_is_rejected_even_when_file_hashes_are_updated(self):
        trace = self.run_fixture()
        trace["schema_version"] = "unrecognised"
        self.rewrite(trace)
        with self.assertRaisesRegex(InvalidBundle, "schema version"):
            audit_bundle(self.root / "fixture")

    def test_export_boolean_cannot_substitute_for_numeric_step_index(self):
        self.run_fixture()
        directory = self.root / "fixture"
        rows = [json.loads(line) for line in (directory / "steps.jsonl").read_text().splitlines()]
        rows[0]["step_index"] = True
        (directory / "steps.jsonl").write_bytes(b"".join(canonical_bytes(r) + b"\n" for r in rows))
        manifest = json.loads((directory / "manifest.json").read_text())
        manifest["files"]["steps.jsonl"] = hashlib.sha256((directory / "steps.jsonl").read_bytes()).hexdigest()
        (directory / "manifest.json").write_bytes(canonical_bytes(manifest))
        with self.assertRaisesRegex(InvalidBundle, "JSONL export differs"):
            audit_bundle(directory)

    def test_empirical_bundle_cannot_enter_fixture_replay(self):
        trace = self.run_fixture()
        trace["study_eligible"] = True
        self.rewrite(trace)
        with self.assertRaisesRegex(InvalidBundle, "fixture status"):
            audit_bundle(self.root / "fixture")

    def test_oracle_leak_is_rejected_after_resealing_hashes(self):
        trace = self.run_fixture()
        trace["checks"][0]["input"]["oracle_truth"] = True
        self.rewrite(trace)
        with self.assertRaisesRegex(InvalidBundle, "permitted transcript"):
            audit_bundle(self.root / "fixture")

    def test_missing_artifact_leaves_an_auditable_failed_bundle(self):
        original = observe_file
        def remove_then_read(path, record):
            path.unlink(missing_ok=True)
            return original(path, record)
        with patch("swarm_handoff.runner.observe_file", side_effect=remove_then_read):
            trace = self.run_fixture()
        self.assertEqual(trace["run_status"], "oracle_unavailable")
        self.assertTrue((self.root / "fixture/manifest.json").exists())
        manifest = json.loads((self.root / "fixture/manifest.json").read_text())
        self.assertIsNone(manifest["files"]["artifact.json"])
        self.assertEqual(manifest["missing_files"], ["artifact.json"])
        self.assertEqual(audit_bundle(self.root / "fixture")["run_status"], "oracle_unavailable")

    def test_malformed_agent_response_keeps_bounded_diagnostic_text(self):
        agents = {a: CarryAgent() for a in "ABCD"}
        agents["B"] = lambda *_: {"bad": "x" * 20000}
        trace = self.run_fixture(agents=agents)
        raw = trace["steps"][1]["raw_response"]
        self.assertEqual(trace["steps"][1]["status"], "malformed_output")
        self.assertTrue(raw["truncated"])
        self.assertEqual(len(raw["text"]), 8192)
        audit_bundle(self.root / "fixture")

    def test_malformed_check_response_keeps_raw_value(self):
        trace = self.run_fixture(checker=lambda _: {"flag": "not a bool"})
        check = trace["checks"][0]
        self.assertEqual(check["status"], "malformed_output")
        self.assertIn("not a bool", check["raw_response"]["text"])
        self.assertIsNone(check["flag"])
        audit_bundle(self.root / "fixture")

    def test_json_boolean_is_not_the_same_file_state_as_number_one(self):
        def wrong_type(request, tools):
            expected = tools.call("fetch_record")
            actual = dict(expected, values=[True])
            tools.call("write_record", {"record": actual})
            return AgentResponse({"asserted": {"record": expected}, "inherited": {}}, True, "fixture")
        agents = {a: CarryAgent() for a in "ABCD"}
        agents["A"] = wrong_type
        trace = self.run_fixture(agents=agents, record={"reference_code": "AB12CD34EF56", "values": [1]})
        self.assertTrue(all(s["oracle_truth"] is False for s in trace["steps"]))
        audit_bundle(self.root / "fixture")

    def test_unexpected_check_error_preserves_remaining_repeat_schedule(self):
        def broken(_):
            raise RuntimeError("fixture programming error")
        with self.assertRaises(RuntimeError):
            run_offline(RunConfig("fixture", Condition.INJECT_HANDOFF, 5), self.root,
                        {"reference_code": "AB12CD34EF56", "values": [2, 3, 5]},
                        {a: CarryAgent() for a in "ABCD"}, broken)
        trace = audit_bundle(self.root / "fixture")
        self.assertEqual(len(trace["checks"]), 15)
        self.assertEqual(trace["checks"][0]["status"], "runner_error")
        self.assertTrue(all(c["status"] == "not_executed" for c in trace["checks"][1:]))
        self.assertEqual(trace["check_invocations"], 1)


if __name__ == "__main__":
    unittest.main()
