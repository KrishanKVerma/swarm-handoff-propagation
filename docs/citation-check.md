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

## Not found — treat as cut unless a source is produced

| cite | what was searched | result |
|---|---|---|
| **Singh & Pawar 2026** | author names with agent-chain, error-propagation, handoff-verification, silent-failure and monitor terms, twice, extended search | **No such paper surfaced.** This is the entry Related Work calls "the closest study to ours", so the novelty claim rests on it. See below. |

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

## Papers that surfaced and are strikingly close to this study

Found while searching for Singh & Pawar. **None of these is cited yet**, and at
least one may be what that citation was reaching for — or may be a genuinely
closer study, which would change the novelty sentence.

- *Outcome Monitors: Recovery Affordances for Silent Tool Failures* — arXiv 2608.19303
- *CatchBench: When Can an Agent Failure Be Caught?* — arXiv 2608.22808
- *Silent Failures in Agent-Tool Interaction: An Audit of ToolUniverse* — arXiv 2609.26836
- *The Hallucination Snowball: Modeling Error Propagation as State Transitions in Multi-Agent LLM Pipelines* — arXiv 2608.14588
- *Preventing Error Propagation in Multi-Agent AI through Runtime Monitoring* — Shahnewaz Karim Sakib and Anindya Bijoy Das, arXiv 2606.29026

Each needs reading before it is cited or dismissed. Citing a title found in a
search result, without reading it, is the same error class as the withdrawn
figure.
