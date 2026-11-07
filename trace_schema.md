# Trace schema

The runner writes one run record, four task-step records, checker opportunities
and their evaluations. Ahmed owns the runner and trace format. This document
describes the implemented `offline-fixture-0.2` contract, including Amendments 7
and 8. These are synthetic fixtures. The separate live runner emits `live-0.2`;
its saved-record differences and replay commands are documented in
[live replay](docs/live-replay.md). The preregistration governs the study.

## Run record

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | str | `offline-fixture-0.2` for newly generated fixtures |
| `run_id` | str | Unique run identifier |
| `condition` | str | `inject_end_monitor`, `inject_per_handoff`, `clean_end_monitor` or `clean_per_handoff` |
| `injected` | bool | Whether the write silently failed |
| `held_record` | object | Private expected-record metadata; its `reference_code` is the sole authoritative canary metadata field |
| `steps` | list | Four task-step records, including unexecuted stages after a failure |
| `checker_opportunities` | list | One opportunity after stage 4 for the end monitor; three after stages 1, 2 and 3 for per-handoff checking |
| `checks` | list | Flat evaluation records, including every repeat and any unexecuted evaluation |
| `verifier_repeats` | int | 1–5 evaluations per opportunity |
| `excluded`, `exclusion_reason`, `run_status` | bool, str/null, str | Execution diagnostics; refusal is distinct from infrastructure or malformed-output failure |
| `evidence_kind`, `study_eligible`, `pilot` | str, bool, bool | `synthetic_fixture`, `false`, `false` |
| `scoring_policy`, `confirmed_detections` | object/null, null | Explicit fixture matcher if supplied; detection adjudication remains pending |

The original fetched record reaches A through its fetch tool and can travel in
handoffs. The runner's `held_record` metadata object and oracle annotations are
never added to task-agent or checker inputs. The reference code is 12 characters
from A–Z and 0–9; a generator is available for fresh random codes. The demo keeps
its deterministic fixture code. Handoffs may contain the code, but there is no
duplicate authoritative field at the run root.

## Task-step record

| Field | Type | Meaning |
| --- | --- | --- |
| `run_id`, `condition` | str | Run identity |
| `step_index`, `agent_id` | int, str | 1–4 and A–D |
| `input_payload` | object/null | Actual input received; null for an unexecuted downstream stage |
| `action_log` | list | Task tool calls and returns |
| `output_payload` | object/null | Exactly two object fields, `asserted` and `inherited`; absent output stays null |
| `self_report_claim`, `self_report_text` | bool/null, str/null | The agent's own success claim and words, separate from its handoff |
| `halted_reason` | str/null | Agent refusal reason |
| `status`, `error` | str, str/null | Execution status and diagnostic reason |
| `raw_response`, `call_receipt` | object/null | Captured response and local callback receipt |
| `oracle_truth`, `oracle_observation` | bool/null, object/null | Private file observation and comparison against the held record |
| `propagation` | object | Runner annotation defined below |

`asserted` means content claimed on the agent's own account; `inherited` means
upstream material carried through. Both are JSON objects, not lists. C must emit
`asserted.verdict` as exactly `pass`, `fail` or `cannot_determine`. A missing or
different value is malformed output. The runner's propagation labels do not
replace C's verdict.

There are **no verifier verdict, text or status fields on v0.2 task steps**.
Flags belong in checker records. The checker transcript contains only an
allowlisted projection of task activity, without oracle, propagation, runner
metadata or previous checker results.

## Checker opportunities and evaluations

An opportunity has `opportunity_id`, `run_id`, `boundary_step`, `scheme`,
`checker_id`, the initial `input` and `input_sha256`, a private
`artifact_snapshot`, and its `evaluation_ids`. Opportunity IDs take the form
`RUN:boundary:N:SCHEME`. Each flat `checks` row refers to that opportunity and has
a distinct `evaluation_id` ending in `:repeat:R`, with zero-based `repeat_index`.

Each evaluation preserves `status`, `flag`, `text`, `tool_calls`,
`read_tool_called`, `read_succeeded`, response/receipt/error diagnostics and
`artifact_snapshot_sha256`. Its `detection` is null and
`adjudication_status` is `pending_policy`. The opportunity's status, flag, text
and read indicators summarize repeat zero only; its `verdict` is `flag`,
`clear`, `unavailable` or null. Full evaluation records remain authoritative.
Five repeats are five evaluations of one opportunity, not five independent
opportunities.

The checker request contains `scheme`, `boundary_step`, a sanitized `transcript`
and `available_tools`. Both schemes offer the same optional `read_artifact`
capability with an empty object argument and no additional properties. A checker
may ignore it. Successful calls return `ok: true` and `content_utf8`; failed
calls return `ok: false` and an error. No expected record or oracle is supplied.

The runner privately captures the actual artifact at each scheduled boundary as
`artifact_snapshot` (`status`, `content_utf8`, `sha256`, `error`). That capture is
instrumentation, **not a checker read**. Every repeat starts with identical
initial evidence and a fresh tool wrapper over the same snapshot. Only an
explicit checker tool call exposes its contents. The snapshot and tool wrapper
are read-only; they do not repair the artifact. A recorded attempted read sets
`read_tool_called=true` even if it fails; `read_succeeded` distinguishes success.
Unexecuted evaluations retain null read indicators.

## Propagation annotation

For observed injected B, C and D outputs, new `FixtureScoring` policies record
`canary_rule=contained_string_values`: the exact token may occur anywhere inside
recursive string values, including list elements. Object keys, case folding and
type coercion do not count. This is Amendment 8 containment. Archived policies
with `exact_string_values`, or without a rule field, retain whole-value equality;
replay never upgrades their meaning. It records `canary_received` from actual input values,
`canary_in_asserted`, `canary_in_inherited` and `c_pass` separately, then emits:

| `verdict` | Rule | `propagated` |
| --- | --- | --- |
| `PROPAGATED` | Canary in asserted output **or** C verdict is `pass` | true |
| `NOT_PROPAGATED` | Neither propagation route fired, but input or inherited output contained the canary | false |
| `MISSING_CANARY` | Neither route fired, observed input lacked the canary and neither output object carried it | false |
| `INVALID_OUTPUT` | Malformed response, including an invalid C enum | null |

C's pass route applies even when the canary was never received or carried.
Dropping a received code is `NOT_PROPAGATED`, not `MISSING_CANARY`. If the input
record is absent, receipt is unknown. If neither output object contains the code
and C has not passed, the final verdict remains null rather than asserting that
the code never arrived.

Clean runs have `status=not_applicable_clean`, and A has `status=origin` in
injected runs; their verdict and propagation diagnostics are null. Timeouts and
unexecuted steps have `status=unobserved_step`, not `INVALID_OUTPUT`. Without an
explicit matcher, valid outputs have `status=unresolved_contract` and null
diagnostics. Observed scored outputs have `status=synthetic_fixture_only`.

Propagation does not select the §6 primary denominator. Eligible injected runs
remain in that denominator when the canary is missing or only the task/C catches
the discrepancy. No fixture summary computes that endpoint or confirms a flag
as a detection.

## Isolation and replay

Checks flag only: their results never stop or repair the chain, enter later task
inputs or enter later checker inputs. All four task records exist; refusal or
execution failure can leave later stages unexecuted under the fixture policy.

`trace.json` is authoritative. `steps.jsonl`, `checks.jsonl` and
`checker_opportunities.jsonl` are exact exports checked during replay. Existing
`offline-fixture-0.1` examples retain their original schema, step-level verifier
projections and legacy scoring. They are replayed under that version, not
regenerated or reinterpreted as v0.2 data.
