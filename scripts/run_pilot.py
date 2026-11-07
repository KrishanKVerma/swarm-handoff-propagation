#!/usr/bin/env python3
"""Run the registered pilot: 20 runs, 10 per scheme, inject, invisible salience.

    export GROQ_API_KEY=...
    python3 scripts/run_pilot.py runs/smoke --smoke --repeats 2   # measure first
    python3 scripts/run_pilot.py runs/pilot --repeats 5           # then the pilot

Checkpointed: every completed run is on disk before the next starts, and a
second invocation skips run ids already there. A rate-limit stop costs one run.

The pilot is an instrument check, not a result (§10). It confirms that the
injection fires, the oracle reads, the canary test decides cleanly, the
stability check has input from both checker roles, and the adjudicator resolves
claims against oracle state. It enters no endpoint.
"""

from __future__ import annotations

import argparse
import json
import random
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.live_runner import RunConfig, completed_run_ids, run_live  # noqa: E402
from src.provider import (  # noqa: E402
    GeminiProvider, GroqProvider, ProviderError, QuotaExhausted, RateLimited,
)
from src.scoring import generate_reference_code  # noqa: E402

UNITS = ("kg", "ml", "units")


def make_record(rng: random.Random, index: int) -> dict[str, object]:
    return {
        "record_id": "R-" + "".join(rng.choice(string.digits) for _ in range(4)),
        "reference_code": generate_reference_code(rng),
        "unit": rng.choice(UNITS),
        "values": [rng.randint(1, 99) for _ in range(rng.randint(3, 6))],
        "source": f"batch-{index:02d}",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--per-scheme", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--provider", default="groq", choices=["groq", "gemini"])
    parser.add_argument("--model", default=None,
                        help="exact model string; frozen into every trace")
    parser.add_argument("--smoke", action="store_true",
                        help="3 runs across both schemes, then project the pilot's cost")
    parser.add_argument("--salience", default="invisible", choices=["invisible", "weak_cue"])
    parser.add_argument("--checker-prompt", default="enumerated",
                        choices=["enumerated", "neutral"],
                        help="amendment 14's prompt-salience level")
    parser.add_argument("--seed", type=int, default=20261107)
    args = parser.parse_args(argv)

    default_model = {"groq": "openai/gpt-oss-120b", "gemini": "gemini-2.5-flash"}
    model = args.model or default_model[args.provider]
    try:
        provider = (GroqProvider(model=model) if args.provider == "groq"
                    else GeminiProvider(model=model))
    except ProviderError as exc:
        print(f"cannot start: {exc}")
        return 2

    rng = random.Random(args.seed)
    done = completed_run_ids(args.output)
    if args.smoke:
        plan = [("end_monitor", 0), ("end_monitor", 1), ("per_handoff", 0)]
    else:
        plan = [(scheme, i) for scheme in ("end_monitor", "per_handoff")
                for i in range(args.per_scheme)]
    prefix = ("smoke" if args.smoke else "pilot") + "-" + args.checker_prompt
    planned = [
        RunConfig(run_id=f"{prefix}-{scheme}-{i:02d}", mode="inject", scheme=scheme,
                  salience=args.salience, verifier_repeats=args.repeats, pilot=True,
                  checker_prompt=args.checker_prompt)
        for scheme, i in plan
    ]
    records = {config.run_id: make_record(rng, i) for i, config in enumerate(planned)}

    print(f"planned {len(planned)} runs, {len(done)} already on disk, "
          f"provider {args.provider}, model {model}")
    completed = failed = 0
    tokens = calls = 0
    by_scheme: dict[str, list[int]] = {"end_monitor": [], "per_handoff": []}
    for config in planned:
        if config.run_id in done:
            continue
        try:
            bundle = run_live(config, args.output, records[config.run_id], provider)
        except QuotaExhausted as exc:
            print(f"daily quota exhausted at {config.run_id}: {exc}")
            print("checkpointed; rerunning today will not help")
            return 4
        except RateLimited:
            print(f"rate limited at {config.run_id}; checkpointed, rerun to resume")
            return 3
        except ProviderError as exc:
            print(f"{config.run_id}: provider error {type(exc).__name__}")
            failed += 1
            continue
        completed += 1
        run_calls = bundle["agent_invocations"] + bundle["check_invocations"]
        tokens += bundle["tokens_used"]
        calls += run_calls
        by_scheme[config.scheme].append(bundle["tokens_used"])
        status = "excluded:" + str(bundle["exclusion_reason"]) if bundle["excluded"] else "ok"
        print(f"{config.run_id}: {status}  calls={run_calls} "
              f"tokens={bundle['tokens_used']}")

    summary = {"completed_now": completed, "provider_errors": failed,
               "on_disk": len(completed_run_ids(args.output)),
               "calls": calls, "tokens": tokens}
    if args.smoke and completed:
        summary["projected_full_pilot"] = _project(by_scheme, args.repeats)
    print(json.dumps(summary, indent=2))
    print("next: python3 -m analysis.recompute " + str(args.output))
    return 0


def _project(by_scheme: dict[str, list[int]], repeats: int) -> dict[str, object]:
    """What ten runs per scheme would cost, from what the smoke runs actually used.

    A projection with no successful runs behind it refuses to answer. Reporting
    `fits_in_one_day: true` off zero tokens is the same error as a rate with no
    denominator, and it points the wrong way — it says go ahead.
    """
    out: dict[str, object] = {"repeats_sampled": repeats,
                              "free_tier_day_budget": 200_000}
    total = 0.0
    measured = 0
    for scheme, samples in by_scheme.items():
        usable = [n for n in samples if n > 0]
        if not usable:
            out[scheme] = "not measured — no run reported token usage"
            continue
        measured += len(usable)
        mean = sum(usable) / len(usable)
        out[scheme] = {"mean_tokens_per_run": round(mean),
                       "runs_measured": len(usable),
                       "ten_runs": round(mean * 10)}
        total += mean * 10
    if measured == 0:
        out["pilot_tokens_estimate"] = None
        out["fits_in_one_day"] = None
        out["note"] = ("no run reported token usage, so there is nothing to project. "
                       "This is not an estimate of zero.")
        return out
    if any(isinstance(out.get(s), str) for s in ("end_monitor", "per_handoff")):
        out["note"] = ("one scheme was not measured; the estimate covers only the "
                       "scheme that was")
    out["pilot_tokens_estimate"] = round(total)
    out["fits_in_one_day"] = total <= 200_000
    return out


if __name__ == "__main__":
    raise SystemExit(main())
