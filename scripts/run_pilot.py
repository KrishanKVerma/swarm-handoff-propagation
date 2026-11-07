#!/usr/bin/env python3
"""Run the registered pilot: 20 runs, 10 per scheme, inject, invisible salience.

    export GEMINI_API_KEY=...
    python3 scripts/run_pilot.py runs/pilot --repeats 5

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
from src.provider import GeminiProvider, ProviderError, RateLimited  # noqa: E402
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
    parser.add_argument("--model", default="gemini-2.0-flash")
    parser.add_argument("--salience", default="invisible", choices=["invisible", "weak_cue"])
    parser.add_argument("--seed", type=int, default=20261107)
    args = parser.parse_args(argv)

    try:
        provider = GeminiProvider(model=args.model)
    except ProviderError as exc:
        print(f"cannot start: {exc}")
        return 2

    rng = random.Random(args.seed)
    done = completed_run_ids(args.output)
    planned = [
        RunConfig(run_id=f"pilot-{scheme}-{i:02d}", mode="inject", scheme=scheme,
                  salience=args.salience, verifier_repeats=args.repeats, pilot=True)
        for scheme in ("end_monitor", "per_handoff")
        for i in range(args.per_scheme)
    ]
    records = {config.run_id: make_record(rng, i) for i, config in enumerate(planned)}

    print(f"planned {len(planned)} runs, {len(done)} already on disk, model {args.model}")
    completed = failed = 0
    for config in planned:
        if config.run_id in done:
            continue
        try:
            bundle = run_live(config, args.output, records[config.run_id], provider)
        except RateLimited:
            print(f"rate limited at {config.run_id}; checkpointed, rerun to resume")
            return 3
        except ProviderError as exc:
            print(f"{config.run_id}: provider error {type(exc).__name__}")
            failed += 1
            continue
        completed += 1
        status = "excluded:" + str(bundle["exclusion_reason"]) if bundle["excluded"] else "ok"
        print(f"{config.run_id}: {status}  "
              f"agent_calls={bundle['agent_invocations']} "
              f"check_calls={bundle['check_invocations']}")

    print(json.dumps({"completed_now": completed, "provider_errors": failed,
                      "on_disk": len(completed_run_ids(args.output))}, indent=2))
    print("next: python3 -m analysis.recompute " + str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
