# Synthetic offline examples

These four fixture bundles were generated on 5 November 2026 during pre-sprint preparation. They contain no model responses or empirical study results. Every bundle is synthetic and ineligible for study endpoints. The fixed checker flags an uncorroborated write in every condition; those flags are not confirmed detections.

From the repository root, verify all bundle hashes and replay their fixture counts:

```sh
PYTHONPATH=src python3 -m swarm_handoff.cli summarize --input examples/offline
```

The expected fixture counts are in fixture-summary.json. Fresh generation is available through scripts/offline_check.py. See docs/offline-runner.md for the provisional contract and remaining live-execution gates.
