# Offline runner preparation

This implementation began on 5 November 2026 in Europe/London, before the
sprint. Declare it as preexisting preparation. No result from the synthetic
callbacks is a result of the study. The code uses Python's standard library
and makes no provider requests through the supplied CLI.

## Run and replay

From the repository root:

```sh
python3 scripts/offline_check.py
```

The command runs the tests and generates one synthetic chain for each of the
four conditions. It prints the output directory and recomputes fixture counts
from the saved records. Each invocation uses a new output directory. An explicit
path is also supported, and existing run directories are never overwritten:

```sh
python3 scripts/offline_check.py --output artifacts/offline-review-001
PYTHONPATH=src python3 -m swarm_handoff.cli summarize --input artifacts/offline-review-001
PYTHONPATH=src python3 -m swarm_handoff.cli audit --input artifacts/offline-review-001/fixture_inject_per_handoff
```

Use `--repeats 5` on the first command to exercise five evaluations of every
check input. This is an instrumentation test and does not generate the registered
pilot. The demonstration has four chains, not the pilot's twenty.

## What works

- A four-stage orchestration callback interface with separate run directories.
- A fetch/write tool for A, with identical reported success in clean and injected
  fixtures. The injected write leaves the file unchanged. B, C and D receive
  handoff content and cannot use the tool interface to reread the file.
- Boundary checks at 1, 2 and 3, or a monitor after stage 4. Flags never alter
  task-agent inputs or appear in later check inputs in this offline configuration.
- Detached, allowlisted checker transcripts. Runner metadata, the oracle and
  previous flags stay outside model-facing inputs.
- Raw response diagnostics, per-call elapsed time, status, attempts and all
  repeated decisions. Missing outputs remain missing after refusal or failure.
- A private file observation at each stage, plus SHA-256 manifests and replay
  validation. Unexpected programming errors remain visible and propagate after
  the runner persists the failure record.

This is interface isolation, not an OS sandbox for arbitrary Python callbacks.
Callbacks supplied to `run_offline` must be synthetic. Connect real agents only
through a separately agreed execution path with truthful provider receipts and
evidence status. The offline API must not label network-backed calls as fixtures.

## Saved records

Each run directory contains:

| File | Purpose |
| --- | --- |
| `trace.json` | Authoritative run metadata, four stage records, all checks and private oracle observations |
| `steps.jsonl` | Exact stage-record export, including `run_id` and `condition` |
| `checks.jsonl` | Exact repeated-check export, with inputs and their hashes |
| `artifact.json` | Actual file state, or an explicit missing-file manifest entry on an oracle failure |
| `manifest.json` | File hashes, missing-file inventory and implementation source hashes |

The manifest checks integrity relative to the saved manifest. It is not a signed
attestation. All fixture bundles carry `evidence_kind=synthetic_fixture`,
`study_eligible=false` and zero provider API calls. Token usage and costs remain
null. Elapsed time describes local callback execution.

`trace.json` is authoritative. Replay checks both JSONL exports against it and
rejects unsupported schema versions, changed files and incompatible visibility
records. Check records preserve every repeat. Per-step `verifier_verdict` and
`verifier_text` are convenience fields for repeat zero only. `verifier_status`
distinguishes an unscheduled check, a skipped check and a failed check.

## Provisional fixture contract

The explicit amended §3 handoff rule governs this runner: B transforms the
content in A's handoff and does not read the file. The earlier stage-table row
still says otherwise. Leave its logged correction and the preexisting-code
wording in the preregistration to the method owner; this branch does not rewrite
that amendment history.

The schema version is `offline-fixture-0.1`. This is not a frozen research trace
version or a complete A2A implementation. `trace_schema.md` describes the shared
intended fields; these additional status/receipt fields are proposals for review.

Synthetic callbacks use JSON objects for `asserted` and `inherited`. Their C
verdict is the fixture string `pass`. The optional `FixtureScoring` matcher tests
exact string values recursively, never dictionary keys or inherited fields.
It records C's canary and pass routes separately, with an OR for the fixture
propagation flag. Clean propagation is not applicable. If no fixture scoring
policy is supplied, propagation remains unresolved rather than choosing a rule.
Neither the C enum nor this matcher is a scientific default.

The private fixture oracle compares the file with the fetched record using
type-sensitive canonical JSON. This predicate needs review alongside the actual
task. The original fetched record reaches A normally; the runner's `held_record`
copy and oracle annotations never enter agent or checker inputs. The sole
authoritative reference-code metadata field is `held_record.reference_code`.

Task refusals and infrastructure failures have different statuses. A refusal is
not an infrastructure exclusion. The fixture stops invoking later tasks after a
refusal/error and records their stages as not executed. Remaining checks also
stay not executed. That continuation policy needs agreement before study use.
It does not change the rule that verifier flags cannot stop or repair a chain.

Malformed outputs, timeouts and missing oracle data retain distinct reasons.
Their fixture exclusion fields are diagnostic, not a frozen statistical policy.
No primary denominator, detection rate or confidence interval is computed here.
An emitted flag never automatically becomes a confirmed detection: adjudication
remains pending, and `confirmed_detections` is null.

The demo reuses its synthetic record across conditions solely to test visibility.
It does not choose a paired design for the study. Its deterministic reference
code is a fixture value, not the per-run random study canary.

## Before model execution

Agree the verifier's allowed evidence and adjudication rule, C verdict enum,
matching convention, flag visibility, refusal/continuation policy and A2A example
with the method and agent owners. Freeze model IDs, routes, prompts, settings,
timeouts and retries. Confirm credit activation, inference coverage and a spending
limit. Then implement truthful provider receipts and a separate empirical mode.

The empirical analysis belongs to Dora. This package currently recomputes fixture
counts only. It must not present those counts as study endpoints or infer that
flag-only data demonstrates mitigation success.
