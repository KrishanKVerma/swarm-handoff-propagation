"""One command that recomputes every number from the traces.

    python -m analysis.recompute runs/ --json out/numbers.json

Nothing here is typed into the report by hand. If a number is in the report it
came out of this, and re-running it on the same traces reproduces it.

The pilot is an instrument check, not a result (§10). Below 30 runs per cell
§8 permits per-cell rates with Wilson intervals and **no between-scheme
comparison**, so this refuses to compute one and says why.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analysis.adjudicate import adjudicate_bundle, state_for_boundary
from analysis.stats import Rate, flip_rate, geometric_prediction

MIN_N_FOR_COMPARISON = 30


def load_runs(root: Path) -> list[dict[str, Any]]:
    traces = []
    for path in sorted(Path(root).glob("*/trace.json")):
        traces.append(json.loads(path.read_text()))
    return traces


def _repeat_zero(bundle: dict[str, Any], opportunity_id: str) -> dict[str, Any] | None:
    for row in bundle["checks"]:
        if row["opportunity_id"] == opportunity_id and row["repeat_index"] == 0:
            return row
    return None


def summarise(bundles: list[dict[str, Any]]) -> dict[str, Any]:
    cells: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for bundle in bundles:
        cells[(bundle["condition"], bundle.get("salience", "invisible"))].append(bundle)

    out: dict[str, Any] = {
        "runs_total": len(bundles),
        "pilot_runs": sum(1 for b in bundles if b.get("pilot")),
        "study_eligible": sum(1 for b in bundles if b.get("study_eligible")),
        "providers": sorted({json.dumps(b.get("provider_metadata", {}), sort_keys=True)
                             for b in bundles}),
        "exclusions": dict(Counter(
            b["exclusion_reason"] for b in bundles if b.get("excluded")
        )),
        "cells": {},
        "between_scheme_comparison": None,
        "notes": [],
    }

    for (condition, salience), group in sorted(cells.items()):
        eligible = [b for b in group if not b.get("excluded")]
        read_k = read_n = 0
        report_k = report_n = 0
        flip_groups: list[list[bool | None]] = []
        claim_counts: Counter[str] = Counter()
        adjudication_status: Counter[str] = Counter()
        detections = 0
        false_positives = 0
        adjudicated_n = 0

        for bundle in eligible:
            verdicts = {a.evaluation_id: a for a in adjudicate_bundle(bundle)}
            for opportunity in bundle["checker_opportunities"]:
                row = _repeat_zero(bundle, opportunity["opportunity_id"])
                if row is None or row["status"] != "completed":
                    continue
                read_n += 1
                if row.get("read_succeeded"):
                    read_k += 1
                    report_n += 1
                    verdict = verdicts.get(row["evaluation_id"])
                    if verdict is not None and verdict.detection:
                        report_k += 1
                flip_groups.append([
                    r["flag"] for r in bundle["checks"]
                    if r["opportunity_id"] == opportunity["opportunity_id"]
                ])
            for row in bundle["checks"]:
                if row.get("claim"):
                    claim_counts[row["claim"]] += 1
                verdict = verdicts.get(row.get("evaluation_id", ""))
                if verdict is None:
                    continue
                adjudication_status[verdict.status] += 1
                if verdict.status == "adjudicated":
                    adjudicated_n += 1
                    detections += bool(verdict.detection)
                    false_positives += bool(verdict.false_positive)

        p1 = Rate(read_k, read_n)
        p2 = Rate(report_k, report_n)
        p = None if p1.point is None or p2.point is None else p1.point * p2.point
        flips = flip_rate(flip_groups)

        out["cells"][f"{condition}|{salience}"] = {
            "runs": len(group),
            "runs_after_exclusions": len(eligible),
            "p1_read_rate_repeat_zero": {"k": p1.k, "n": p1.n, "render": p1.render()},
            "p2_report_given_read": {"k": p2.k, "n": p2.n, "render": p2.render()},
            "p_per_opportunity": p,
            "geometric_prediction_three_draws": None if p is None else geometric_prediction(p),
            "instrument_flip_rate": {
                "k": flips.flipped, "n": flips.inputs, "render": flips.as_rate().render()
            },
            "claims": dict(claim_counts),
            "adjudication_status": dict(adjudication_status),
            "detections_adjudicated_true": detections,
            "false_positives": false_positives,
            "adjudicated_evaluations": adjudicated_n,
        }

    smallest = min((c["runs_after_exclusions"] for c in out["cells"].values()), default=0)
    if smallest < MIN_N_FOR_COMPARISON:
        out["notes"].append(
            f"No between-scheme comparison computed: smallest cell is {smallest} runs, "
            f"below the {MIN_N_FOR_COMPARISON} per cell §8 requires. Per-cell rates with "
            "Wilson intervals only."
        )
    out["notes"].append(
        "The pilot is an instrument check, not a result (§10). Pilot runs enter no endpoint."
    )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recompute every report number from traces.")
    parser.add_argument("root", type=Path, help="directory holding one subdirectory per run")
    parser.add_argument("--json", type=Path, default=None, help="write the numbers here")
    args = parser.parse_args(argv)

    bundles = load_runs(args.root)
    if not bundles:
        print(f"no traces under {args.root}")
        return 1
    numbers = summarise(bundles)
    text = json.dumps(numbers, indent=2, sort_keys=True)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
