# Amendment 7 synthetic review examples

These examples validate the offline runner contract after the 13:30 GMT coding start on 6 November 2026. They do not contain model or study results.

The read and no-read demonstrations each complete four fixture chains, one per condition. Each demonstration contains eight checker opportunities and forty evaluations because each opportunity receives five repeat checks. The no-read callback emits a fixed flag without reading. The read callback reads the saved actual-artifact snapshot and compares it with A's claim in the visible transcript. Neither callback uses the private oracle.

`sample-opportunity.json` shows one opportunity with five evaluation IDs. `sample-check.json` shows repeat zero and its explicit read-tool receipt. The summary files retain zero provider calls and null confirmed detections. Do not interpret these deterministic fixture counts as read propensities, model accuracy or the registered pilot.

Recreate and replay the read example from the repository root:

```sh
.venv/bin/python scripts/offline_check.py --output artifacts/a7-review --checker-mode read --repeats 5
PYTHONPATH=src python3 -m swarm_handoff.cli summarize --input artifacts/a7-review
```

The original version 0.1 examples remain unchanged in `examples/offline/` and have their original replay rules. The current whole-string-value matching policy is explicit fixture behavior. The shared research matcher and discrepancy adjudication still need reconciliation before real collection.
