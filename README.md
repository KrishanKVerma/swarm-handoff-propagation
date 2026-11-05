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
All four steps run in every run, whatever fires.

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
- `PREREGISTRATION.md` and `trace_schema.md` were written on
  5–6 November, before the sprint opened and before any code existed.
  They are design documents, not code.

The offline runner, fixture tests and replay tooling on this branch began on
**5 November 2026 (Europe/London), before the sprint**. They are declared
preexisting preparation. Synthetic fixture output is not study data. The
preregistration's earlier statement that all `src/` code would be written during
the sprint needs reconciliation with this dated declaration before submission.
The builders must preserve this provenance when integrating subsequent work.

## Layout

| path | what |
|---|---|
| `PREREGISTRATION.md` | question, hypotheses, design, endpoints, exclusions, resolution limit, what a null looks like, what this cannot establish |
| `trace_schema.md` | the per-step and per-run record format |
| `src/swarm_handoff/` | offline runner, synthetic callbacks and fixture replay |
| `tests/` | data isolation, failure accounting and artifact validation |
| `scripts/offline_check.py` | one command to test, generate fixtures and replay their counts |
| `docs/offline-runner.md` | usage, provisional interface and remaining execution gates |
| `analysis/` | planned empirical analysis, not implemented by this offline package |

## The three things that decide the build

1. **The handoff carries the record content; no agent re-reads the
   file after A writes it.** If B opens the file it finds it empty,
   reports so, and nothing propagates in either scheme. The file is
   ground truth precisely because the chain stops consulting it.
   (`PREREGISTRATION.md` §3)
2. **Propagation is a canary test, not a judgement.** `held_record` carries
   a 12-character random reference code in a field the pipeline carries
   and never transforms; propagation to step *k* is that code appearing
   in agent *k*'s `asserted` output fields. One string comparison — no
   inverse transform, no canonicalisation table, no scorer. (§5)
3. **A run in which only the task caught the discrepancy counts as
   uncaught** for the primary endpoint, and stays in the denominator.
   The primary measures the verification scheme, not the chain. (§6)

## Status

The preregistration and its amendment history precede empirical collection.
This branch aligns the trace schema with Amendment 4 and supplies an offline
implementation. Verifier evidence access, C verdict values, exact matching,
failure/continuation rules and the live provider configuration remain open.
No real agent, provider adapter or empirical execution mode is included.

Run the offline checks from the repository root with Python 3.11 or newer:

```sh
python3 scripts/offline_check.py
```

See [the runner notes](docs/offline-runner.md) for saved-data replay and the
distinction between fixture conventions and the study contract.
