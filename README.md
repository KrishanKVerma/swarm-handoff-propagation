# Error propagation through agent handoffs

Agent A's unverified "done" becomes agent B's input, and B cannot
distinguish a completed task from a claimed one. We build a chain of
four agents, inject a silent failure at step one — the agent genuinely
fails, truthfully reports its own false belief, and hands on a wrong
state — and measure how far that false state travels before anything
catches it.

Design is crossed 2×2: injection (on / off) × verification scheme
(one monitor at the end of the chain / a verifier at every handoff).
The two clean cells give each scheme its own false-positive rate,
measured against the number of checks that scheme actually makes.

Framed as survival rather than a flat rate: of the runs with an
injected failure, what fraction is still uncaught after k handoffs.

**Verifiers flag only. They never stop the chain and never repair it.**
Flags do not change task execution. Refusals or execution failures can leave
later stages unexecuted; the trace retains all four step records.

Apart Research Swarm Alignment Hackathon, 6–8 November 2026.

## Team

| | |
|---|---|
| Krishan Kumar Verma | measurement, pre-registration, report |
| Ahmed Tariq | runner, trace format, reproducibility |
| Supriya Kamatagi | agents and A2A handoff, verifier hooks |
| Dora Zelenyanszki | propagation analysis (empirical) |
| Soumyajit Karmakar | related work, second coder |
| Nico Smith | analytical model — predicted survival curve |

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

The offline runner, fixture tests and replay tooling on this branch began on
**5 November 2026 (Europe/London), before the sprint**. They are declared
preexisting preparation. The v0.2 Amendment 7 changes were implemented on
**6 November after 13:30 Europe/London** and are recorded separately in new
fixture provenance. Synthetic fixture output is not study data. The
preregistration's earlier statement that all `src/` code would be written during
the sprint needs reconciliation with this dated declaration before submission.
The builders must preserve this provenance when integrating subsequent work.

## Layout

| path | what |
|---|---|
| `PREREGISTRATION.md` | question, hypotheses, design, endpoints, exclusions, resolution limit, what a null looks like, what this cannot establish |
| `trace_schema.md` | run, task-step, checker-opportunity and evaluation records |
| `src/swarm_handoff/` | offline runner, synthetic callbacks and fixture replay |
| `src/injection.py`, `src/oracle.py`, `src/checker_tools.py`, `src/scoring.py` | shared experiment helpers from main; live adapter reconciliation remains pending |
| `tests/` | data isolation, failure accounting and artifact validation |
| `scripts/offline_check.py` | one command to test, generate fixtures and replay their counts |
| `docs/offline-runner.md` | usage, provisional interface and remaining execution gates |
| `analysis/` | planned empirical analysis, not implemented by this offline package |

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
   propagation events. The offline exact-value matcher remains an explicit
   fixture policy pending agreement for live use. (§5)
3. **A run in which only the task caught the discrepancy counts as
   uncaught** for the primary endpoint, and stays in the denominator.
   The primary measures the verification scheme, not the chain. (§6)

## Status

The preregistration and its amendment history precede empirical collection.
The offline v0.2 implementation incorporates Amendment 7's strict C verdicts,
optional checker reads and flag isolation. It logs one checker opportunity per
scheduled boundary and distinct evaluations for repeats. Replay preserves the
original v0.1 examples. All generated data is synthetic and ineligible for study
endpoints; the CLI makes no provider calls and consumes no credits.

Exact matching, discrepancy adjudication, failure/continuation rules and the
live model, API access and pilot budget still need agreement. No live provider
adapter or empirical execution mode is included. Summaries provide fixture
counts and read diagnostics; the proposed read/report decomposition and
independence comparison remain analysis work, not measured results.

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
