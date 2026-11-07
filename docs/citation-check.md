# Citation verification

Apart states that made-up results or references can disqualify a project, and
this project has already withdrawn one fabricated figure. Every citation in
Related Work is checked here before it ships. **Anything not confirmed is cut,
not softened.**

Three questions per entry: does the work exist, are the authors right, and
does it say what our sentence claims it says. The third cannot be answered
without the sentence, so entries are marked accordingly.

Checked 2026-11-07.

## Confirmed — exists, authors correct

| cite | what it actually is | notes |
|---|---|---|
| **Kemeklis & Vemuri 2026** | *Omission Attacks: When Doing Nothing Is the Attack*, Jurgis Kemeklis and Nikhil Vemuri (Team MAIA). AI Control Hackathon 2026, Apart Research Sprint, 23 March 2026. **1st place, LinuxArena track.** | Real, placement real. **The figures matter:** 5 hand-crafted attack traces; the strongest attack scores at most 4.0/10 against an Opus 4.6 monitor, against a 92.3/100 mean detection score on commission attacks; postcondition monitoring catches 5 of 5. **The page reports no false-positive rate at all**, and a reviewer asks for one. Any sentence citing an FPR for this work is wrong. |
| **Najt et al. 2026** | *SLEIGHT-Bench: A Benchmark of Evasion Attacks Against Agent Monitors*, Elle Najt, Colin Toft, Tyler Tracy, Fabien Roger, Joe Benton. arXiv **2605.16626**. | 40 synthetic coding-agent transcripts, 11 blind-spot categories. An Opus 4.6 monitor with extended thinking at 1% FPR **never catches 20 of the 40** across 10 trials; overall catch rate **32%**. Targeted prompts help some categories, no single prompt covers all — directly relevant to our enumeration finding. |
| **Korbak et al. 2025** | *Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety*. arXiv **2507.11473**. | Exists, author-year correct. |
| **Turpin et al. 2023** | *Language Models Don't Always Say What They Think*. arXiv **2305.04388**. | Verified earlier in this project. |

## Singh & Pawar 2026 — confirmed, and it is the problem

**An earlier revision of this file recorded this citation as "not found". That
was wrong.** The paper surfaced in the first search under its title and the
author names were not connected to it. Soumyajit's citation is correct.

**Prabhjot Singh and Bhushan Pawar, *The Hallucination Snowball: Modeling
Error Propagation as State Transitions in Multi-Agent LLM Pipelines*, arXiv
2608.14588v1, submitted 22 June 2026.**

It is not merely the closest study. It is substantially the study we
registered:

| their design | ours |
|---|---|
| sequential **four-agent** pipeline (financial analysis, FinanceBench) | four-agent pipeline A→B→C→D |
| failures **injected** automatically | silent write failure injected |
| three verification conditions: **boundary gates at each stage**, **end-of-pipeline checking**, and **none** | `per_handoff`, `end_monitor` (and no third arm) |
| **survival** framing with per-boundary escape probabilities | survival curve, fraction uncaught after each step |
| **346 injected hallucinations** | 6 live runs, no endpoint computed |

Their results, which answer our registered primary question: 23.7% of 346
injected hallucinations survive undetected to the final output; detection falls
from 72.0% at stage 1 to 50.9% at stage 4 for gpt-4o; per-boundary escape
probabilities are 24.6%, 48.3% and 89.3%; **boundary gates cut survival from
58.4% to 16.2% against end-of-pipeline checking** (Cohen's h = −0.911,
p < 0.000001), while end-of-pipeline checking beats no verification by only
2.3 pp.

**What this means for the report, stated plainly.** The question we registered
— does a verifier at every handoff catch a propagating failure earlier than a
monitor at the end — **has been answered by prior work at n = 346 with
p < 10⁻⁶, and we did not run it.** The report cannot present that question as
open, and the novelty claim must be narrowed to what is actually ours:

1. the failure shape — a **silent tool failure in which the agent truthfully
   reports a false belief**, leaving no signal anywhere unless something reads
   the artifact, rather than an injected hallucination in content;
2. the **mechanical canary** propagation test and adjudicated detection, which
   remove the scorer from both endpoints;
3. **the enumeration confound** — that naming failure modes in a monitor's
   prompt determines whether it inspects at all. This is not in their paper and
   is the one finding we have;
4. the pre-registration and its amendment log as an object in itself.

Their paper strengthens (1) and (3) rather than weakening them: they show the
boundary-gate advantage is real and large, which makes the question of *what
makes a boundary gate actually look* more pointed, not less.

## Cannot be checked without the titles

An author-year alone is not searchable. These need the titles from Soumyajit's
text before they can be confirmed: **Huang et al. 2025**, **Hu 2026**,
**Sun et al. 2024**, **Advani 2026**, **Hiller / Jhumka / Suri 2001**,
**Arcuschin et al. 2025**.

Arcuschin et al. 2025 is probably *Chain-of-Thought Reasoning In The Wild Is
Not Always Faithful*, arXiv 2503.08679 — **recalled, not confirmed**, and it
is not citable on that basis.

Hiller / Jhumka / Suri 2001 is probably the DSN-era work on error propagation
in software — **recalled, not confirmed**.

## Verified by the author, recorded here

**FakeLab** (arXiv 2607.07368) and **SCHEME** (arXiv 2605.29178) — checked by
Krishan Kumar Verma on 2026-11-07, authors and claims as summarised. Not
re-checked here; recorded so the provenance of the check is on file.

## The other four surfaced papers — read, not skimmed

**Outcome Monitors: Recovery Affordances for Silent Tool Failures** — Sugam
Panthi and Rabab Abdelfattah, arXiv 2608.19303v1, 19 Aug 2026. **Pre-empts our
injection design.** Faults are injected *only into the text the model
observes*, with environment state unchanged so the evaluator scores the true
state — which is our injection, independently arrived at. They also vary
warning **salience** and placement (on-time against deferred, localized against
generic witness). **But:** a single acting agent per episode, no handoff chain;
the checker is deterministic and invariant-based rather than an LLM deciding
whether to look; and the outcome is task completion and recovery, not detection
propensity. Headline: ToolMaze completion 35/320 → 90/320, +17.2 pp
(95% CI 11.25–23.44). **We must stop implying the injection design is novel and
cite them for it.**

**CatchBench: When Can an Agent Failure Be Caught?** — Yue Zhao, University of
Southern California, preprint, work in progress. Varies the auditor's
**information state** (PRE / LIVE / POST), not monitor placement, and has no
multi-agent chain of its own. Mostly natural failures (126 Who&When, 376
SWE-Gym, 660 tau-bench) with an injected Gold split whose boards **failed their
own admissibility bar** and are reported as mechanism diagnostics only. Worth
citing for the framing and for its reporting discipline — 47 of 118 pre-declared
contrasts separate after correction and **the other 71 are reported as
unresolved rather than equal**, which is the rule we use. Does not pre-empt.

**Silent Failures in Agent–Tool Interaction: An Audit of ToolUniverse** —
Devansh Singh, Shreya Gopalan, Sundaraparipurnan Narayanan. **Naturally
occurring**, not injected: 91 failures observed across 198 candidate test cases
on 15 manually validated tools, 52 at the API layer and 25 at the wrapper
layer, 7 of 15 tools failing on more than half their cases. Single agent, no
chain, monitoring not varied. **This is the citation for "such failures
actually occur"**, which §7 currently concedes we cannot establish. Does not
pre-empt.

**Preventing Error Propagation in Multi-Agent AI through Runtime Monitoring** —
Shahnewaz Karim Sakib and Anindya Bijoy Das, arXiv 2606.29026. Two models
exchanging reasoning traces on multiple-choice questions with a third as judge;
cybersecurity accuracy 60.34% → 93.10%, networking mixed. Different object
entirely. Cite only if Related Work needs breadth.
