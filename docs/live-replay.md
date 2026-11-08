# Replaying saved live runs

The replay CLI accepts the live runner's `live-0.2` output as well as the
`offline-fixture-0.1` and `offline-fixture-0.2` formats. It does not invoke a
provider, regenerate a trajectory, modify the saved files or rescore old
fixtures under a new rule.

## Commands

With Python 3.11 or newer, install the local package once:

```sh
.venv/bin/python -m pip install -e .
```

Then validate one saved run or summarize a folder of runs:

```sh
.venv/bin/swarm-handoff audit --input runs/smoke/ACTUAL_RUN_ID
.venv/bin/swarm-handoff summarize --input runs/smoke
```

Replace the example paths with the actual saved folders. A run folder must
contain its original `trace.json`, `steps.jsonl`, `checks.jsonl` and available
`artifact.json`. A missing artifact is accepted only when consistent with the
producer's recorded failure. Summarize also accepts one run folder. Mixed live
and fixture directories are rejected; summarize those evidence sets separately.
The installed executable works outside the repository working directory when
given absolute input paths.

For a repeatable compatibility check requiring no credentials:

```sh
.venv/bin/python scripts/check_live_replay.py --output artifacts/live-replay-compatibility
```

The output directory must be new. Omitting `--output` uses temporary files.
This calls the actual `run_live` writer with `ScriptedProvider`, then audits
all four clean/inject × end/per-handoff cells. The probe includes reads,
no-read repeats and a canary embedded in a summary sentence. It compares the
replayed analysis with `analysis.recompute.summarise` and checks that replay
leaves every saved byte unchanged. Its receipt explicitly records zero real
provider calls and zero empirical traces verified.

## Format and scoring

`live-0.2` is a distinct wire format. Its boundaries are strings (`1->2`, `2->3`,
`3->4`, `end`); checker inputs and raw responses are text, and read logs and
oracle observations have the live writer's native structure. It has no fixture
manifest or separate checker-opportunities export. The adapter reads these
records directly and checks exports, handoffs, public checker projections,
opportunity/repeat identities, read outcomes and propagation. A rate-limit
checkpoint can be a valid excluded partial run.

Replay targets the pilot script's default `SchemaAdapter` and finite JSON.
The live writer does not record custom adapter settings, so replay cannot infer
them. Nonstandard model output containing `NaN` or infinity is rejected, even
though Python's permissive JSON parser may have allowed the writer to save it.

Live propagation uses the shared scorer. New fixture policies also use
Amendment 8's case-sensitive token containment in recursive string values,
excluding keys and type coercion. Saved fixture policies record their own rule;
`exact_string_values` and omitted historical rule fields retain equality.
C's structured `pass` route remains independent of token carriage.

Live summaries preserve recorded eligibility, pilot flags and exclusions. They
accept early `live-0.2` traces without a `checker_prompt` identifier, following
the shared analysis's historical `enumerated` default. Explicit `neutral` values
remain separate; explicit null or non-string identifiers remain invalid. Replay
does not insert the inferred field into returned traces or saved files.
Summaries
separate recorded invocation/token counts from the replay's zero provider
calls, keep repeat-zero opportunities distinct from repeated evaluations, and
recompute checker adjudications using the shared analysis. `shared_analysis`
reproduces the upstream descriptive computation unchanged. Its cell metrics
include nonexcluded pilots and omit failed repeat-zero evaluations; its
repeat-zero detection numerator requires a successful read. These counts do
not establish a new study endpoint. Unsupported non-string claim/field values
are reported explicitly instead of inventing a scientific classification.

## Evidence limits

The compatibility probe establishes that current live-writer output can be
read, validated and replayed using scripted responses. The six saved Groq pilot
folders are now tracked in `runs/smoke`; the saved-pilot regression audits all
six, compares their replay summary with `analysis.recompute`, and checks every
input file's hash before and after. Neither operation makes provider calls.

Live files have no signed or hashed manifest, so the audit establishes internal
consistency, not authenticated provenance or proof that model calls occurred.
The live writer also uses its native `live_model_run` marker for scripted
providers; the probe's receipt and provider metadata identify its mocked source.
Full provider requests and checker token receipts are not saved. The adapter
does not invent them, and it preserves the producer's existing treatment of
an invalid C verdict rather than silently changing historical eligibility.
