"""Synthetic callbacks exercise orchestration without any model provider."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import (AgentRequest, AgentResponse, CheckRequest, CheckResponse,
                        Condition, FixtureScoring, RunConfig, clone)
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


def unsupported_write_flag(request: CheckRequest) -> CheckResponse:
    # A fixed fixture flag is not a model result or a confirmed detection.
    return CheckResponse(True, "The transcript does not independently corroborate the write.")


def demo(output_root: Path, repeats: int = 1) -> list[dict[str, Any]]:
    results = []
    for condition in Condition:
        config = RunConfig("fixture_" + condition.value, condition, repeats)
        # Deliberately shared fixture inputs test isolation, not study pairing.
        results.append(run_offline(config, output_root,
                                   {"reference_code": "AB12CD34EF56", "values": [2, 3, 5]},
                                   {a: CarryAgent() for a in "ABCD"}, unsupported_write_flag,
                                   scoring=FixtureScoring()))
    return results
