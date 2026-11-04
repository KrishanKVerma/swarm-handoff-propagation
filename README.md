# Error propagation through agent handoffs

Agent A's unverified "done" becomes agent B's input, and B cannot
distinguish a completed task from a claimed one. We build a chain of
four agents, inject a silent failure at step one, and measure how far
that false state travels before anything catches it.

Two conditions on the same runs: one monitor at the end of the chain
versus a verifier at every handoff. Plus runs with no injection, to
report each condition's false-positive rate rather than only its
catch rate.

Apart Research Swarm Alignment Hackathon, 6-8 November 2026.

## Team
- Krishan Kumar Verma — measurement, pre-registration, report
- Ahmed Tariq — runner, trace format, reproducibility
- Supriya — agents and A2A handoff, verifier hooks
- Dora Zelenyanszki — propagation analysis
- (tbc) — related work, second coder

## Prior work

Per the sprint rules, only this weekend's work is submitted for
judging. The following existed before the sprint and is declared here
as preexisting:

- `github.com/KrishanKVerma/bedrock` — browser-agent harness with an
  independent end-state verifier. 160 instrumented runs, 4 tasks,
  2 models, zero honest failure reports.
- The 160-run corpus itself, used as background and motivation only.
  No result in this submission is computed from it.

Everything in `src/` and `analysis/` is written during the sprint.

## Layout
- `PREREGISTRATION.md` — hypothesis, endpoints, exclusions, resolution limit
- `trace_schema.md` — the per-step record format
- `src/` — chain, agents, verifiers, runner
- `analysis/` — propagation and detection analysis
