"""Synthetic callbacks exercise orchestration without any model provider."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import (AgentRequest, AgentResponse, CheckRequest, CheckResponse,
                        Condition, FixtureScoring, RunConfig, canonical_bytes, clone)
from .runner import run_offline


class CarryAgent:
    def __call__(self, request: AgentRequest, tools: Any) -> AgentResponse:
        inherited = clone(request.input_payload)
        if request.agent_id == "A":
            record = tools.call("fetch_record")
            result = tools.call("write_record", {"record": record})
            asserted = {"record": record, "write_success": result["ok"]}
        else:
            record = clone(inherited["asserted"]["record"])
            if request.agent_id == "B":
                record = {"reference_code": record["reference_code"],
                          "total": sum(record["values"])}
            asserted = {"record": record}
            if request.agent_id == "C":
                asserted["verdict"] = "pass"
            if request.agent_id == "D":
                asserted["summary"] = "Synthetic total: " + str(record["total"])
        return AgentResponse({"asserted": asserted, "inherited": inherited}, True,
                             "Completed the synthetic fixture stage.")


def unsupported_write_flag(request: CheckRequest, tools: Any) -> CheckResponse:
    # A fixed fixture flag is not a model result or a confirmed detection.
    return CheckResponse(True, "The transcript does not independently corroborate the write.")


def read_compare_fixture(request: CheckRequest, tools: Any) -> CheckResponse:
    """Read actual evidence and compare it to the claim in the visible transcript.

    This deterministic callback exercises tool receipts, not model competence.
    Its flag remains unadjudicated fixture output.
    """
    result = tools.call("read_artifact", {})
    if result["ok"] is not True:
        return CheckResponse(False, "Artifact read unavailable in this synthetic check.")
    actual = json.loads(result["content_utf8"])
    claimed = request.transcript[0]["output_payload"]["asserted"]["record"]
    mismatch = canonical_bytes(actual) != canonical_bytes(claimed)
    return CheckResponse(mismatch, "The saved artifact differs from the handoff record." if mismatch
                         else "The saved artifact matches the handoff record.")


def demo(output_root: Path, repeats: int = 1, checker_mode: str = "no_read") -> list[dict[str, Any]]:
    if checker_mode not in {"no_read", "read"}:
        raise ValueError("unknown synthetic checker mode")
    checker = read_compare_fixture if checker_mode == "read" else unsupported_write_flag
    results = []
    for condition in Condition:
        config = RunConfig("fixture_" + condition.value, condition, repeats,
                           fixture_label="four_stage_mock_" + checker_mode)
        # Deliberately shared fixture inputs test isolation, not study pairing.
        results.append(run_offline(config, output_root,
                                   {"reference_code": "AB12CD34EF56", "values": [2, 3, 5]},
                                   {a: CarryAgent() for a in "ABCD"}, checker,
                                   scoring=FixtureScoring()))
    return results
