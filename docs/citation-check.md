# Citation verification

Apart states that made-up results or references can disqualify a project, and
this project has already withdrawn one fabricated figure. Every citation in
Related Work is checked here before it ships. **Anything not confirmed is cut,
not softened.**

Three questions per entry: does the work exist, are the authors right, and
does it say what our sentence claims it says. The third cannot be answered
without the sentence, so entries are marked accordingly.

Checked 2026-11-07.

## Verified — exists, authors correct, claim matches the source

Fourteen references, all checked. Where a draft sentence overstated a source,
the correction is recorded here rather than quietly made.

| cite | what it is | claim check |
|---|---|---|
| **Advani 2026** | *From Confident Closing to Silent Failure: Characterizing False Success in LLM Agents*, Laksh Advani (Colorado). Workshop on Failure Modes in Agentic AI, ICML 2026. arXiv:2606.09863. | Confirmed. False success is 616 of 1,730 tau2-bench failures (35.6%). "No configuration across 5 judges, 5 prompt strategies, and full task specifications exceeds AUROC 0.65", on 295 trajectories. **Our sentence was corrected** from "LLM judges never exceed AUROC 0.65" — a universal claim — to "no judge configuration tested exceeds AUROC 0.65". |
| **Arcuschin et al. 2025** | *Chain-of-Thought Reasoning in the Wild Is Not Always Faithful*, Iván Arcuschin, Jett Janiak, Robert Krzyzanowski, Senthooran Rajamanoharan, Neel Nanda, Arthur Conmy. arXiv:2503.08679. | Confirmed. Across 4,834 question pairs the unfaithful-pair rate runs 0.04% (Claude 3.7 Sonnet, 1k thinking) to 13.49% (GPT-4o-mini). Cited only for the existence of unfaithful CoT, which it supports. |
| **Hiller, Jhumka & Suri 2001** | *An Approach for Analysing the Propagation of Data Errors in Software*, Martin Hiller, Arshad Jhumka, Neeraj Suri (Chalmers). DSN 2001. | Confirmed on all three parts of our sentence: §4.1 defines error permeability as the conditional probability of an output error given an input error; §6 estimates it per module by fault injection; §5 and observations OB4–OB6 use it to place detection mechanisms. |
| **Hu 2026** | *Silence Is Endorsement: Verification-Status Laundering in LLM Agent Pipelines*, Yibo Hu (Illinois Institute of Technology). arXiv:2609.20211v1. | Confirmed exactly. Removing an "(UNVERIFIED)" marker while keeping the authorization claim raised risky approval from 0.052 to 0.601 (Llama-3.1-8B) and 0.089 to 0.975 (Qwen2.5-14B). Summarizers drop the status on 0.10–0.13 of outputs. |
| **Huang et al. 2025** | *On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents*, Jen-Tse Huang, Jiaxu Zhou, Tailin Jin, Xuhui Zhou, Zixi Chen, Wenxuan Wang, Youliang Yuan, Michael Lyu, Maarten Sap. ICML 2025, PMLR 267:26202–26226. | Paper and authors confirmed. **Two of our claims were overstated and both were corrected.** (a) We wrote that it finds linear chains least resilient; the source reports the hierarchical structure most resilient at a 5.5% drop against 10.5% and 23.7%, without identifying which structure took the 23.7%. (b) We wrote that an Inspector agent "recovers most of the lost performance"; the source says it recovers "up to 96.4% errors made by faulty agents" — a best case on errors, not an average on performance. |
| **Kemeklis & Vemuri 2026** | *Omission Attacks: When Doing Nothing Is the Attack*, Jurgis Kemeklis and Nikhil Vemuri (Team MAIA). Apart Research AI Control Hackathon 2026, 23 March 2026. **1st place, LinuxArena track.** | Confirmed, placement included. 5 hand-crafted attack traces; the strongest scores at most 4.0/10 against an Opus 4.6 monitor, against 92.3/100 mean on commission attacks; postcondition monitoring catches 5 of 5. **The report contains no false-positive rate** — a reviewer asks for one — so no sentence of ours may cite an FPR to this work. |
| **Korbak et al. 2025** | *Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety*, Tomek Korbak et al. arXiv:2507.11473. | Confirmed. Cited for the premise that CoT monitoring assumes evidence appears in what the agent says. |
| **Najt et al. 2026** | *SLEIGHT-Bench: A Benchmark of Evasion Attacks Against Agent Monitors*, Elle Najt, Colin Toft, Tyler Tracy, Fabien Roger, Joe Benton. arXiv:2605.16626. | Confirmed. 40 synthetic transcripts, 11 blind-spot categories. An Opus 4.6 monitor with extended thinking at 1% FPR never catches 20 of the 40 across 10 trials; overall catch rate 32%. Targeted prompts help some categories while no single prompt covers all — the sentence we place beside our own finding. |
| **Panthi & Abdelfattah 2026** | *Outcome Monitors: Recovery Affordances for Silent Tool Failures*, Sugam Panthi and Rabab Abdelfattah (Southern Mississippi). arXiv:2608.19303v1, 19 Aug 2026. | Confirmed, and it is why we no longer claim the injection design as ours. Faults are injected only into the text the model observes, environment state unchanged so evaluators score the true state. Single acting agent per episode, deterministic invariant checker, recovery as the outcome. ToolMaze completion 35/320 to 90/320, +17.2 pp (95% CI 11.25–23.44). |
| **Singh & Pawar 2026** | *The Hallucination Snowball: Modeling Error Propagation as State Transitions in Multi-Agent LLM Pipelines*, Prabhjot Singh and Bhushan Pawar. arXiv:2608.14588v1, 22 June 2026. | Confirmed. Four-agent pipeline, injected hallucinations, boundary gates against end-of-pipeline checking against none. 23.7% of 346 survive to the final output; detection 72.0% to 50.9% stage 1 to 4; per-boundary escape 24.6%, 48.3%, 89.3%; boundary gates cut survival 58.4% to 16.2%, Cohen's h = −0.911, p < 0.000001. **See the section below: this is the work that superseded our registered primary.** |
| **Singh, Gopalan & Narayanan 2026** | *Silent Failures in Agent–Tool Interaction: An Audit of ToolUniverse*, Devansh Singh, Shreya Gopalan, Sundaraparipurnan Narayanan (AI Tech Ethics). | Confirmed. Failures are naturally occurring, not injected: 91 observed across 198 candidate test cases on 15 manually validated tools, 52 at the API layer and 25 at the wrapper layer, 7 of 15 tools failing on more than half. The authors call the results illustrative rather than representative, and our sentence does not generalise past that. |
| **Sun et al. 2024** | *Tools Fail: Detecting Silent Errors in Faulty Tools*, Jimin Sun (Cohere), So Yeon Min, Yingshan Chang, Yonatan Bisk (CMU). arXiv:2406.19228. | Confirmed in the paper's own words: "most tool failures are 'silent'" and "models tend to overtrust tools", with "smaller models… overtrust the tool and allow errors to pass". Note for honesty: the paper also finds models often *can* identify incorrect outputs (60–70 F1 with in-context interventions), so our sentence is scoped to over-trust rather than to incapacity. |
| **Turpin et al. 2023** | *Language Models Don't Always Say What They Think*, Miles Turpin et al. arXiv:2305.04388. | Confirmed. Cited alongside Arcuschin for unfaithful reasoning straining the CoT-monitoring premise. |
| **Zhao 2026** | *CatchBench: When Can an Agent Failure Be Caught?*, Yue Zhao (USC). Preprint, work in progress. | Confirmed. Varies the auditor's information state (PRE / LIVE / POST) rather than verifier placement; 126 Who&When, 376 SWE-Gym and 660 tau-bench runs, with an injected Gold split whose boards **failed the authors' own admissibility bar** and are reported as mechanism diagnostics only. Cited for framing and for the reporting discipline we follow: 47 of 118 pre-declared contrasts separate after correction and the other 71 are reported as unresolved, not equal. |

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
