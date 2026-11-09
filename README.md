# What makes a boundary gate look?

### Prompt enumeration determines whether an LLM monitor inspects the artifact

Agent A's unverified "done" becomes agent B's input, and B cannot
distinguish a completed task from a claimed one. We build a chain of
four agents, inject a silent failure at step one — the agent genuinely
fails, truthfully reports its own false belief, and hands on a wrong
state — and measure how far that false state travels before anything
catches it.

Apart Research Swarm Alignment Hackathon, 6–8 November 2026

## Video

https://github.com/user-attachments/assets/2910b73f-5f23-4dae-88b3-ce55518ab2b8

Three minutes: the failure, the measurement, and what the head-to-head showed.

## What we found

Naming candidate failure modes in the checker's prompt moved detection of the
silent failure from **1 of 5 opportunities to 5 of 5** (two-sided Fisher exact
p = 0.0476, under a reading fixed before the run). The mechanism is reading
rather than reporting: checkers that were not pointed at the artifact mostly
never opened it, and returned an affirmative judgement that nothing was wrong.
**The constraint that made our detection metric machine-adjudicable was
eliciting the behaviour it measured.**

What that claim is not:

- It rests on **five opportunities an arm** across six live runs, one task
  family, one provider, one model. It is a claim about this instrument at this
  n, not a general law.
- The contrast is **narrower than enumeration against none**: the neutral arm
  removed the artifact spotlight and added three non-artifact options, so what
  it separates is pointing at the artifact from offering alternatives.
- Three of the six saved `live-0.2` traces record no `checker_prompt`
  identifier. The analysis assigns them to the enumerated arm by the live
  runner's own default (`src/live_runner.py:67`, read as that default at
  `analysis/recompute.py:46` and `:151`); the three neutral runs carry theirs
  explicitly. The enumerated side of the contrast is identified by what the
  writer defaulted to rather than by anything recorded in the trace.
  `REPORT.md` §3 states this.

The report is [`REPORT.md`](REPORT.md). Every number in it is reproduced from a
clean clone by:

```sh
python3 -m analysis.recompute runs/smoke
```

## What was registered, and what was run

The registered design is a crossed 2×2: injection (on / off) × verification
scheme (one monitor at the end of the chain / a verifier at every handoff).
**No cell of it was run to its registered n.** All six live runs are `inject`;
no clean cell was run, so neither scheme has a measured false-positive rate.
The resolved comparison is the prompt-salience head-to-head above, which the
registered design did not contain — it enters as amendment 14.

The original survival comparison is retained as design history. Amendment 16
withdraws it as an informative primary claim; see `PREREGISTRATION.md` and
`REPORT.md` for the current research framing and reported evidence.

**Verifiers flag only. They never stop the chain and never repair it.**
Flags do not change task execution. Refusals or execution failures can leave
later stages unexecuted; the trace retains all four step records.

## Team

**On this submission:**

| | |
|---|---|
| Krishan Kumar Verma | measurement design, pre-registration and amendments, injection, oracle, canary scorer, checker tools, agent and checker prompts, live runner, analysis, report |
| Soumyajit Karmakar | related work; LA-hub presentation |
| Ahmed Tariq | the trace format and the offline runner, begun 5 November and declared preexisting where applicable (see Prior work), and during the sprint the amendment 7 checker-access and flag-isolation implementation and the amendment 8 containment matcher, merged to `main` on 7 November |

Ahmed Tariq also raised the flag-only rule (amendment 3), the checker-evidence
question and flag isolation (amendment 7), and both p₁ definitions
(amendment 8).

## Other contributors

**The three below are not on this submission.** The credits record work
contributed before the project split, and the work is theirs whether or not
they are on the team.

- **Supriya Kamatagi** — the runner's propagation scoring enum,
  `PROPAGATED` / `NOT_PROPAGATED` / `MISSING_CANARY` / `INVALID_OUTPUT`
  (amendment 7).
- **Nico Smith** — the geometric framing and the independence question
  (`PREREGISTRATION.md` §7, amendment 7).
- **Dora Zelenyanszki** — the p₁ / p₂ decomposition: splitting per-opportunity
  detection into a read rate and reporting given a read
  (`PREREGISTRATION.md` §7).

Nobody has been removed as a repository collaborator.

## Two runners

There are two, and they are not duplicates. Ahmed Tariq's offline runner is
fixture-based and predates the sprint in part (see Prior work). The live runner
on `main` is sprint work: it makes real provider calls and emits `live-0.2`, a
distinct wire format from `offline-fixture-0.2`. The replay CLI accepts both
formats.

The six saved Groq pilot folders are tracked in `runs/smoke`. The saved-pilot
regression audits all six, compares their replay summary with
`analysis.recompute`, and hashes every input file before and after; the
compatibility probe separately exercises the live writer with a scripted
provider. Neither makes provider calls. Live files carry no signed or hashed
manifest, so the audit establishes internal consistency, **not authenticated
provenance and not proof that model calls occurred**. See
[live replay](docs/live-replay.md) for commands and the full proof limits.

## Prior work

Per the sprint rules, only this weekend's work is submitted for
judging. The following existed before the sprint and is declared here
as preexisting:

- `github.com/KrishanKVerma/bedrock` — browser-agent harness with an
  independent end-state verifier. 160 instrumented runs, 4 tasks,
  2 models, zero honest failure reports.
- The 160-run corpus itself, used as background and motivation only.
  **No result in this submission is computed from it.**
- Initial versions of `PREREGISTRATION.md` and `trace_schema.md` were written on
  5–6 November, before the sprint opened.
  They are design documents, not code.

The offline runner, fixture tests and replay tooling began on
**5 November 2026 (Europe/London), before the sprint**. They are declared
preexisting preparation. The v0.2 Amendment 7 changes were implemented on
**6 November after 13:30 Europe/London** and are recorded separately in new
fixture provenance. Synthetic fixture output is not study data. Amendment 9
reconciles the preregistration with this dated declaration. The containment
matcher and live-format replay integration were added on **7 November**;
the original preparation retains its earlier provenance.
`PREREGISTRATION.md` §0 carries the file list, line counts and commit
timestamps.

## Layout

| path | what |
|---|---|
| `REPORT.md` | the submitted report: question, methods, results, limits, dual-use appendix |
| `PREREGISTRATION.md` | question, hypotheses, design, endpoints, exclusions, resolution limit, what a null looks like, what this cannot establish; §13 is the authoritative amendment log |
| `trace_schema.md` | run, task-step, checker-opportunity and evaluation records |
| `runs/smoke` | the six saved `live-0.2` pilot folders the report's numbers are computed from |
| `src/swarm_handoff/` | offline runner, synthetic callbacks and versioned fixture/live replay |
| `src/injection.py`, `src/oracle.py`, `src/checker_tools.py`, `src/scoring.py`, `src/prompts.py` | shared experiment helpers and the agent and checker prompts |
| `src/live_runner.py`, `src/provider.py`, `scripts/run_pilot.py` | live execution path maintained on main |
| `analysis/` | shared adjudication, descriptive summaries and statistics |
| `tests/` | data isolation, failure accounting and artifact validation |
| `figures/` | Figure 1, the four-stage chain |
| `scripts/offline_check.py` | one command to test, generate fixtures and replay their counts |
| `scripts/check_live_replay.py` | actual live writer and replay compatibility check using a scripted provider |
| `docs/offline-runner.md` | usage, provisional interface and remaining execution gates |
| `docs/live-replay.md` | saved live-run validation, commands and limitations |
| `docs/citation-check.md` | every citation in the report checked against its source |

## The three things that decide the build

1. **The handoff carries the record content; no agent re-reads the
   file after A writes it.** If B opens the file it finds it empty,
   reports so, and nothing propagates in either scheme. The file is
   ground truth precisely because the chain stops consulting it.
   External checkers have optional read-only access, identical under both
   schemes; that access never gives them the expected record or oracle.
   (`PREREGISTRATION.md` §§3–4)
2. **Propagation is a canary test, not a judgement.** `held_record` carries
   a 12-character random reference code in a field the pipeline carries
   and never transforms; propagation to step *k* is that code appearing
   in agent *k*'s `asserted` output fields. C also propagates if its structured
   verdict is `pass`, even without the code. Clean runs and A's origin are not
   propagation events. New fixtures follow Amendment 8: case-sensitive token
   containment in recursive string values, never object keys. Archived fixtures
   retain their recorded matching policy. (§5)
3. **A run in which only the task caught the discrepancy counts as
   uncaught** for the primary endpoint, and stays in the denominator.
   The primary measures the verification scheme, not the chain. (§6)

## Status

The offline v0.2 implementation includes Amendment 7's strict C verdicts,
optional checker reads and flag isolation, plus Amendment 8 containment.
Replay preserves original v0.1/v0.2 matching policies and saved bytes.
The `swarm-handoff` CLI generates only synthetic fixtures or reads saved data;
it makes no model calls. The separate live execution path is already present.

Saved `live-0.2` runs are validated against the producer's exports, handoffs,
propagation, optional reads and repeat-zero opportunity records. Summaries use
the shared analysis without pooling live and fixture evidence. The compatibility
probe generates mocked runs, not empirical results.

The runner runtime uses the standard library. Full repository checks also need
the pinned pytest development dependencies, including the shared helper tests.
From the repository root, with Python 3.11 or newer:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/offline_check.py
```

See [the runner notes](docs/offline-runner.md) for saved-data replay and the
distinction between fixture conventions and the study contract.
