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

**On this submission:**

| | |
|---|---|
| Krishan Kumar Verma | measurement design, pre-registration and amendments, injection, oracle, canary scorer, checker tools, agent and checker prompts, live runner, analysis, report |
| Soumyajit Karmakar | related work; LA-hub presentation |

## Contributions from outside the current team

The people below are **not on this submission**. The credits record work they
contributed before the project split, and the work is theirs whether or not
they are on the team.

- **Ahmed Tariq** — the trace format and the offline runner, including the
  Amendment 7 checker-access and flag-isolation implementation, on
  `feat/offline-runner-traces`, declared preexisting from 5 November where
  applicable (see Prior work). He also raised the flag-only rule
  (amendment 3), the checker-evidence question and flag isolation
  (amendment 7), and both p₁ definitions (amendment 8).
- **Supriya Kamatagi** — the runner's propagation scoring enum,
  `PROPAGATED` / `NOT_PROPAGATED` / `MISSING_CANARY` / `INVALID_OUTPUT`
  (amendment 7).
- **Nico Smith** — the geometric framing and the independence question in §7
  (amendment 7).
- **Dora Zelenyanszki** — the p₁ / p₂ decomposition: splitting per-opportunity
  detection into a read rate and reporting given a read (§7).

Nobody has been removed as a repository collaborator.

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

Everything in `src/` and `analysis/` is written during the sprint.

## Layout

| path | what |
|---|---|
| `PREREGISTRATION.md` | question, hypotheses, design, endpoints, exclusions, resolution limit, what a null looks like, what this cannot establish |
| `trace_schema.md` | the per-step and per-run record format |
| `src/` | chain, agents, verifiers, runner |
| `analysis/` | propagation, detection, survival curves |

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

Pre-registration and trace schema fixed before any run exists. All amendments are logged in §13 and dated before the sprint opened.
