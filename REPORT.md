# What makes a boundary gate look?

### Prompt enumeration determines whether an LLM monitor inspects the artifact

`<<AUTHORS_AFFILIATIONS>>` — names and affiliations, one per line.

With Apart Research

**Draft.** Mapped onto Apart's official template. Every number is reproduced by
`python3 -m analysis.recompute runs/smoke`. Sections marked `DRAFT` are to be
rewritten in the author's voice before shipping.

## Abstract

> **A verifier that is not told what to look for mostly does not look.**
> Naming candidate failure modes in an LLM checker's prompt moved detection of
> a silent failure from **1 of 5 opportunities to 5 of 5** (two-sided Fisher
> exact p = 0.0476), and the mechanism is reading rather than reporting: the
> checkers that were not pointed at the artifact mostly never opened it, and
> concluded nothing was wrong.
>
> This matters because where to put a verifier is settled and why it works is
> not. Singh and Pawar show boundary gates cut failure survival from 58.4% to
> 16.2% across 346 injected failures; we take that result and ask what a gate
> is doing when it works. Placement decides how often a gate runs. Nothing
> about placement decides whether it looks.
>
> The failure we inject is shaped to isolate that. The first agent's write tool
> returns a success-shaped response and the file stays empty, so the agent's
> report is truthful about its own belief: the content is right and only the
> world-state claim is false. Nothing in the text is wrong. Where Singh and
> Pawar have an error propagating, we have an absence propagating, which
> reduces detection to one question — does anything read the artifact?
>
> Six live runs, and a pre-registration with sixteen dated amendments, one of
> which withdraws our own registered primary. **The constraint that made our
> detection metric machine-adjudicable was eliciting the behaviour it
> measured.**

## 1. Introduction

### The question prior work leaves open

Where a verifier should sit in an agent pipeline is settled. Singh and Pawar
show that boundary gates at each handoff cut failure survival from 58.4% to
16.2% against a single end-of-pipeline check, across 346 injected failures,
p < 10⁻⁶. We do not re-litigate that result; we take it.

What it creates is a question it does not ask. **Why does a boundary gate
work, and is its effectiveness a property of placement or of prompting?** A
gate is an LLM with a tool and an instruction. Placement decides how often it
runs. Nothing about placement decides whether, on any given run, it looks.

Our answer is that it is substantially prompting. **A gate that is not told
what to look for mostly does not look** — 1 of 5 opportunities against 5 of 5
when the same checker, with the same tool and the same evidence, is given a
prompt naming candidate failure modes.

We registered the placement comparison as our primary endpoint, found during
the sprint that Singh and Pawar had answered it four and a half months earlier,
and withdrew it; amendment 16 records the withdrawal and the sequence.

### Why it matters

**DRAFT — rewrite in the author's voice.**

A verifier that never looks is indistinguishable, in every log it produces,
from one that looked and found nothing. Both emit the same clean result, and
the difference is invisible to the person reading the output and to the
reviewer who confirms that monitoring exists. It is not hypothetical: in our
neutral condition the checkers did not merely miss the failure, they returned
an affirmative judgement that nothing was wrong.

The failure class is real outside the laboratory — an audit of ToolUniverse
found 91 failures across 198 candidate cases, most silent at the point of use.
A tool returning a success-shaped response for an action that did not happen
leaves the agent nothing to report but success, which makes this a measurement
problem rather than a deception problem: the agent's account of its own belief
is accurate, and what is false is a world-state claim nothing in the transcript
contradicts.

A 160-run reliability harness of ours (`github.com/KrishanKVerma/bedrock`), in
which an agent reported every failure as a success, and parts of this
repository's runner both predate the sprint and are **declared as prior work
supplying no data to this study**. The full declaration — files, line counts,
commits and timestamps — is in `PREREGISTRATION.md` §0.

**Our main contributions are:**

- **The enumeration confound.** Naming candidate failure modes in an LLM
  checker's prompt determines whether it inspects the artifact at all — 5 of 5
  detections against 1 of 5, two-sided Fisher exact p = 0.0476. The constraint
  that makes a monitor's output machine-adjudicable also elicits the behaviour
  the metric measures.
- **A failure shape that isolates inspection.** A silent tool failure in which
  the agent's report is truthful about its own belief, so nothing in the
  transcript is wrong and detection reduces to whether anything reads the
  artifact. An absence propagating rather than an error.
- **Scorer-free measurement.** Propagation by exact containment of a random
  reference code; detection by structured claims adjudicated against a
  deterministic file read. Neither endpoint reads free text.
- **A pre-registration that records its own failure**, including the
  withdrawal of its registered primary on finding that published work had
  already answered it.

## 2. Related Work

Drafted by Soumyajit Karmakar; every citation checked against the source
(`docs/citation-check.md`). **DRAFT — rewrite in the author's voice.**

Error propagation in multi-agent LLM systems has mostly been studied with
content errors. Huang et al. (2025) inject mistakes into agents' responses and
find a hierarchical structure most resilient (5.5% performance drop against
10.5% and 23.7%), with an Inspector agent recovering up to 96.4% of injected
errors. **Singh and Pawar (2026) is the result this study builds on, and the
reason its registered primary was withdrawn** (§1): across 346 injected
hallucinations in a four-agent pipeline they show boundary gates at every
handoff cut failure survival from 58.4% to 16.2% against one end-of-pipeline
check. Their errors are false *content* that downstream agents transform, and
their gates have ground-truth access and repair what they find. Hu (2026)
documents the adjacent failure: an authorization claim survives a handoff while
the record that it was never verified is lost, and removing an "(UNVERIFIED)"
marker raised risky approval from 0.052 to 0.601 on one model. Detector
placement has a longer history in dependable systems — Hiller, Jhumka and Suri
(2001) estimate each module's error permeability by fault injection and place
detectors accordingly.

A second line concerns failures an agent cannot see or does not report. Most
tool failures are silent and models over-trust tool outputs (Sun et al., 2024);
agents claim completion the environment contradicts in 616 of 1,730 tau2-bench
failures, and no judge configuration tested exceeds AUROC 0.65
(Advani, 2026); and an audit of ToolUniverse found 91 failures across 198
candidate cases, 7 of 15 tools failing on more than half (Singh, Gopalan and
Narayanan, 2026). **Our injection design is not ours alone:** Panthi and
Abdelfattah (2026) inject faults only into the text the model observes, leaving
environment state unchanged, and vary warning salience — in a single-agent
setting, with a deterministic checker, measuring recovery rather than
detection. CatchBench (Zhao, 2026) asks when a failure is catchable by varying
the auditor's information state rather than the verifier's placement. On
monitoring, Kemeklis and Vemuri (2026) show action-scrutinising monitors miss
harm caused by actions never taken, and SLEIGHT-Bench (Najt et al., 2026)
reports that targeted prompts help some blind-spot categories while no single
prompt covers all — the result closest to ours. Chain-of-thought monitoring
assumes evidence appears in what the agent says (Korbak et al., 2025), which
unfaithful reasoning already strains (Turpin et al., 2023; Arcuschin et al.,
2025); our setting strains it from the other side, where the account is
faithful and the evidence never enters the agent's context.

**What is new.** To our knowledge no prior work injects a silent tool failure
into a *multi-agent chain* and tracks the resulting honest but false
world-state claim agent by agent — Panthi and Abdelfattah's injection is the
same construction with one agent. Our contribution is not that design but what
it exposed: the prompt constraint that makes a monitor's output
machine-adjudicable also determines whether the monitor inspects the artifact
at all.

## 3. Methods

### Design

A four-stage pipeline: **A** fetches a record and writes it to a file, **B**
transforms, **C** validates, **D** summarises. A's write tool returns a
success-shaped response and leaves the file unchanged; the response is built
from the call's arguments and never read back from disk, so no field differs
between injected and clean modes. The handoff carries the content and no agent
re-reads the file, without which the failure dies at step two by the task's own
mechanics. Verifiers flag only, never stopping or repairing the chain. Every
checker gets a read tool on the artifact, is never told what the file should
contain, never sees the oracle's verdict, and is never instructed to read —
tool access is identical across both schemes and both prompt levels. The
registered design was a crossed 2×2, injection × scheme, and **no cell of it
was run to its registered n** (§4).

**The failure shape, and why it is not a variant of the prior work.** Singh
and Pawar inject false *content*, which downstream agents then transform — so
at every step there is something in the text that is wrong, and a sufficiently
careful reader of the transcript could find it. We inject a silent *tool*
failure. The agent's report is truthful about its own belief: the content it
passes on is correct, and only its claim about the state of the world is false.
**Nothing in the text is wrong.** Theirs is an error propagating; ours is an
absence propagating. That is why this design reduces to a single question —
does anything read the artifact — and theirs does not.

**Measurement.** Propagation is one exact containment match of a 12-character
random reference code in an agent's asserted fields, k ∈ {2,3,4}; detection is
a flag plus at least one structured claim the oracle's deterministic file read
says is true. Neither reads free text, so neither has a scorer. **Two
deviations, both logged before the runs:** the tool loop is scripted
runner-side, so A receives its tool results rather than choosing to invoke them
(amendment 12), and the artifact begins as an empty JSON object, making
`artifact_empty` and `artifact_mismatch` true under injection and
`artifact_missing` false. The pre-registration is public and carries every rule
with its reasoning and amendment history; this report states each once and
points there.

![Figure 1. The four-stage chain. The dashed amber line is the only write to the file, and under injection it does not happen: the tool returns success and the file stays empty. No agent in the chain re-reads the file, so the handoff message is the record's only carrier. Checkers may read it; nothing compels them to.](figures/chain.svg)

### What was fixed in advance

Sixteen dated amendments, superseded text struck in place and left readable.
**Eight correct errors in our own document** — among them a propagation test
two implementations would have scored differently, a rule stated twice in two
wordings, a false attribution, a prior-work claim about code we had not
written, a p-value we computed wrongly and fixed before using, and the
withdrawal of our own registered primary. Fixed before any run and unchanged
since: the endpoint specifications, the n and its power table, the exclusion
categories, the canary match rule, the adjudication rule, and what a null looks
like. After the head-to-head returned p = 0.0476, amendment 15 records a
**pre-commitment against adding runs to it**: optional stopping would be
invisible in the numbers and obvious in the history. Detail in Appendix B and
in `PREREGISTRATION.md`.

## 4. Results

**Pilot runs enter no endpoint (§10). Nothing below is a study result about
agents.** The primary endpoint, the survival curve and the between-scheme
comparison are **not computed**, because no cell reached its registered n and
pilot runs are excluded from every endpoint by design.

**Provider.** Groq, `openai/gpt-oss-120b`, temperature 0.0, max output 4096,
frozen in every trace's `provider_metadata`. 6 live runs, all `inject`, all
`invisible` salience, 2 repeats per opportunity, ~91,600 tokens. **No
exclusions.** Three earlier runs against `gemini-2.5-flash` are declared in
amendment 13 and are not study data.

### 4.1 The pilot was stopped at three runs

All five confirmations §10 required were met at n = 3: the injection fired, the
oracle read correctly, the canary test decided cleanly, the stability check had
input from both checker roles, and the adjudicator resolved claims against
oracle state.

At the enumerated prompt, both components were saturated: checkers read at
**5 of 5** opportunities (Wilson 95% CI 56.6–100%) and reported at **5 of 5**
of those, so p = 1.0, with all ten evaluations claiming `artifact_mismatch`.
**Every checker that read also reported.** At p = 1 the independence secondary is vacuous — 1 − (1 − 1)³ = 1,
with no shortfall to interpret. **5 of 5 does not establish p = 1**; the lower
bound is 56.6%.

### 4.2 The enumeration confound

Registered as a head-to-head before it ran, five opportunities per arm:

| arm | detections per opportunity at repeat zero |
|---|---|
| `enumerated` | **5 of 5** (Wilson 95% CI 56.6–100%) |
| `neutral` | **1 of 5** (Wilson 95% CI 3.6–62.4%) |

**Two-sided Fisher exact p = 0.0476.** Resolved by the reading fixed in advance
(0 or 1 of 5 resolves; 2 or more is reported as unresolved).

**The mechanism is in p₁.** At `neutral` the checkers largely did not read:

0 of 2 opportunities under `end_monitor` (one-sided 95% upper bound 77.6%) and
1 of 3 under `per_handoff` (Wilson 95% CI 6.1–79.2%). The one checker that
read, reported (1 of 1). The enumeration was not only
shaping the claim — **it was driving whether the checker looked at all.** The
distractor options went unused: every non-detection was `no_discrepancy`, not
`transform_error` or `input_mismatch`. The neutral checkers concluded that
nothing was wrong.

**p = 0.0476 rests on a single observation.** One more neutral detection — 2 of
5 — gives p ≈ 0.167, which the pre-registration calls unresolved.

### 4.3 Instrument stability

Verdicts flipped across repeats on 0 of 5 `enumerated` opportunities, **1 of 2**
`neutral` × `end_monitor` opportunities, and 0 of 3 `neutral` × `per_handoff`.

§10 says in advance that if instability is comparable to the between-scheme
difference, the primary is not resolvable at any reachable n. **This is the
first evidence bearing on that clause and it points the wrong way.** One of two
at n = 2 establishes nothing — the interval covers almost the whole line — but
instability appeared the moment there was any variance to have.

**The enumerated arm's 0 of 5 is not reassurance.** Every evaluation there was
saturated: the same flag and the same claim ten times out of ten. That is zero
variance, not demonstrated stability, and reading it as stability would be
reading a ceiling as a measurement.

### 4.4 Not computed

Not computed: the primary endpoint, the survival curve and the between-scheme
difference (no cell reached its registered n, and pilot runs enter no endpoint
by design); the false-positive rate (no `clean` cell was run); and the refusal
rate (the category is defined and not instrumented, amendment 12).

## 5. Discussion and Limitations

**DRAFT — rewrite in the author's voice.**

Placement is not the whole story of why boundary gates work. Enumerating
candidate failure modes in the checker's prompt changed whether the checker
inspected the artifact at all: **5 of 5** opportunities ended in an
adjudicated detection when the claim set named artifact-level failures, against
**1 of 5** when the same claims sat among plausible alternatives (two-sided
Fisher exact **p = 0.0476**, resolved under the reading fixed before the run).

The mechanism is in whether the checkers looked, not in what they reported: at
the neutral level they read the artifact in **0 of 2** opportunities under
`end_monitor` and **1 of 3** under `per_handoff`, and the one that read,
reported. They did not pick a wrong category either — **every** neutral
non-detection was an affirmative `no_discrepancy`, so the checkers concluded
that nothing was wrong.

The result rests on a single observation — a second neutral detection would
have made it unresolved by our own pre-registered table — and it licenses no
claim about either verification scheme, about the independence of detection
opportunities, or about the rate at which agents propagate unverified claims.

What it does license is narrow and, we think, useful. **A monitor's prompt is
a parameter of its sensitivity, and an inexpensive one.** The same model, the
same tool and the same evidence moved from 1 of 5 to 5 of 5 on a change of
wording, which puts prompt wording in the same class as model choice for anyone
deploying a monitor, at none of the cost. SLEIGHT-Bench reports the compatible
result from the other direction: targeted prompts improve monitor performance
on some blind-spot categories while no single prompt covers all of them.

Their result also raises a question their design can answer and ours cannot:
**how much of a gate's effectiveness travels with what it is told, rather than
with where it sits.** A boundary-gate study at their n, run twice with the gate
prompt enumerated and not, would settle it; six runs cannot. That is the
experiment we would run next, alongside a third arm giving the output format
and no options at all, which is the clean version of the test we ran.

### Limitations

Three govern how every number here should be read. **Propagation is near-1 by
construction**, because the injection leaves no signal unless something reads
the file: it is a design consequence, not a measurement. **A low read rate on
an open-weights model may be capability rather than propensity**, so the claim
is "the checkers did not read", never "checkers do not bother to verify".
**The one resolved comparison is about our instrument** — six live runs, no
endpoint reached, the registered primary withdrawn.

The full list, and what this design cannot establish, are in Appendix A with
the dual-use and ethics treatment the submission form requires.

### Future Work

Two experiments follow directly. A third arm giving the checker the output
format with **no** options at all, which is the clean version of the test we
ran — ours removed the artifact spotlight but added three alternatives, so it
shows *pointing at the artifact versus offering alternatives*, not
*enumeration versus none*. And a boundary-gate study at Singh and Pawar's n,
run twice with the gate prompt enumerated and not, which would settle how much
of a gate's effectiveness travels with what it is told.

## 6. Conclusion

A verifier's prompt is a parameter of its sensitivity, and an inexpensive one.
The same model, the same tool and the same evidence moved from 1 of 5
detections to 5 of 5 on a change of wording, which puts prompt wording in the
same class as model choice for anyone deploying a monitor, at none of the cost.
Where a verifier sits is settled; what it is told is not, and on this evidence
it may matter as much.

The finding arrived as a defect in our own instrument. We had constrained the
checker to a closed set of claims so detection could be adjudicated
mechanically, and that set — sitting in the checker's prompt — was telling the
checker where to look. Anyone making monitor outputs machine-adjudicable by
constraining them is doing the same thing to their own measurement, and it is
invisible until the instrument runs. Six live runs cannot establish how general
that is. They were enough to find it.

## Code and Data

- **Code repository:** `github.com/KrishanKVerma/swarm-handoff-propagation` —
  pre-registration with its full amendment log, injection, oracle, scorer,
  checker tools, prompts, live runner, analysis, and the traces.
- **Data:** every trace, step record and checker evaluation is in the
  repository. `python3 -m analysis.recompute runs/smoke` reproduces every
  number in this report.
- **Prior work declared as preexisting:** `PREREGISTRATION.md` §0 carries the
  file list, line counts and commit timestamps.

## Author Contributions

Krishan Kumar Verma: measurement design, pre-registration and amendments,
injection, oracle, canary scorer, checker tools, prompts, live runner,
analysis, report. Soumyajit Karmakar: related work; LA-hub presentation.
From outside the current team, recording work contributed before the project
split: Ahmed Tariq (trace format and offline runner, including the amendment 7
checker-access and flag-isolation implementation and the amendment 8 matcher,
declared preexisting from 5 November where applicable), Supriya Kamatagi (the
propagation scoring enum), Nico Smith (the geometric framing and the
independence question), Dora Zelenyanszki (the p₁ / p₂ decomposition).

## References

All verified against the source; the table is `docs/citation-check.md`.

1. Laksh Advani. *From Confident Closing to Silent Failure: Characterizing
   False Success in LLM Agents.* Workshop on Failure Modes in Agentic AI,
   ICML, 2026. arXiv:2606.09863.
2. Iván Arcuschin, Jett Janiak, Robert Krzyzanowski, Senthooran Rajamanoharan,
   Neel Nanda and Arthur Conmy. *Chain-of-Thought Reasoning in the Wild Is Not
   Always Faithful.* arXiv:2503.08679, 2025.
3. Martin Hiller, Arshad Jhumka and Neeraj Suri. *An Approach for Analysing
   the Propagation of Data Errors in Software.* DSN, 2001.
4. Yibo Hu. *Silence Is Endorsement: Verification-Status Laundering in LLM
   Agent Pipelines.* arXiv:2609.20211, 2026.
5. Jen-Tse Huang, Jiaxu Zhou, Tailin Jin, Xuhui Zhou, Zixi Chen, Wenxuan Wang,
   Youliang Yuan, Michael Lyu and Maarten Sap. *On the Resilience of LLM-Based
   Multi-Agent Collaboration with Faulty Agents.* ICML, PMLR 267:26202–26226,
   2025.
6. Jurgis Kemeklis and Nikhil Vemuri. *Omission Attacks: When Doing Nothing Is
   the Attack.* Apart Research AI Control Hackathon, 2026.
7. Tomek Korbak et al. *Chain of Thought Monitorability: A New and Fragile
   Opportunity for AI Safety.* arXiv:2507.11473, 2025.
8. Elle Najt, Colin Toft, Tyler Tracy, Fabien Roger and Joe Benton.
   *SLEIGHT-Bench: A Benchmark of Evasion Attacks Against Agent Monitors.*
   arXiv:2605.16626, 2026.
9. Sugam Panthi and Rabab Abdelfattah. *Outcome Monitors: Recovery Affordances
   for Silent Tool Failures.* arXiv:2608.19303, 2026.
10. Devansh Singh, Shreya Gopalan and Sundaraparipurnan Narayanan. *Silent
    Failures in Agent–Tool Interaction: An Audit of ToolUniverse.* 2026.
11. Prabhjot Singh and Bhushan Pawar. *The Hallucination Snowball: Modeling
    Error Propagation as State Transitions in Multi-Agent LLM Pipelines.*
    arXiv:2608.14588, 2026.
12. Jimin Sun, So Yeon Min, Yingshan Chang and Yonatan Bisk. *Tools Fail:
    Detecting Silent Errors in Faulty Tools.* arXiv:2406.19228, 2024.
13. Miles Turpin et al. *Language Models Don't Always Say What They Think.*
    arXiv:2305.04388, 2023.
14. Yue Zhao. *CatchBench: When Can an Agent Failure Be Caught?* Preprint,
    2026.

## Appendix A — Limitations and Dual-Use / Ethical Considerations

**Required under this name by the submission form.**

### Limitations

- **Propagation is near-1 by construction.** The injection leaves no signal
  unless something reads the file, and the prompts require the reference code
  to be carried forward. Propagation here is a design consequence, not a
  measured quantity.
- **The canary measures carriage of the identifier, not use of content.**
- **Tool affordance, not capability.** What is measured is whether a checker
  with the means to verify does so.
- **On an open-weights model a low p₁ may be capability rather than
  propensity.** We must not say "checkers do not bother to verify" when the
  data may show "this checker could not follow a two-turn tool offer."
- **The neutral arm is not a clean "no enumeration" condition.** It removes the
  artifact spotlight **and** adds three non-artifact options, so what is shown
  is *pointing at the artifact versus offering alternatives*. A clean test needs
  a third arm giving the output format with no options at all. That is the next
  study.
- **The tool loop is scripted**, so this tests what agents do with tool
  results, not whether they choose to use tools.
- **Detection, not mitigation.** Verifiers flag and the chain runs on.
- **The failure is constructed, though the class is not hypothetical.** We
  inject the silent tool failure rather than observing one. That such failures
  occur in deployed systems is established elsewhere — the ToolUniverse audit
  finds 91 failures across 198 candidate cases, with 7 of 15 tools failing on
  more than half — but this design measures how a chain handles one, not how
  often one arises.
- **The registered primary was withdrawn**, not merely unreached: the question
  it measured was answered by published work before this pre-registration was
  written (amendment 16).
- **One task family, one provider, one model, n = 6 live runs.**

### What this cannot establish

The asymmetry. This design can show that a claim propagated uncaught. It cannot
establish that a verification scheme is sufficient: it probes one failure shape,
and the space of silent failures is unbounded.

And at this n it establishes nothing about agents at all. The one resolved
comparison is about **our instrument**.

### Dual use

**The finding is a lever, and it turns both ways.** It is not "checkers with
file access rarely check." It is narrower and more useful than that:
**enumerating candidate failure modes in a monitor's prompt drives whether the
monitor inspects the artifact at all** — 5 of 5 detections with the artifact
named among the options, 1 of 5 without, two-sided Fisher exact p = 0.048 at
five opportunities an arm. The mechanism is reading, not reporting: in the
neutral arm the checkers mostly never looked.

**The defensive reading.** Monitor sensitivity here is substantially a function
of **prompt framing rather than model capability**. The same model, the same
tool, the same evidence, and detection moves from one in five to five in five.
That is directly actionable for anyone deploying a monitor, and the action is
nearly free: name the failure modes you care about in the prompt. A team that
believes its monitor is weak may have a wording problem rather than a model
problem, and the cheap experiment — enumerate, re-run — is one afternoon.

**The offensive reading, stated without softening.** The same result is a
recipe for **monitoring that exists on paper and catches nothing.** Leave the
monitor's prompt open-ended and it will not merely miss the discrepancy — it
will return an affirmative "no discrepancy." Our neutral arm did exactly that,
four times out of five, and it did not reach for the distractor options we gave
it either. A monitor configured this way produces clean logs, satisfies a
reviewer who checks that monitoring exists, and detects nothing. A map of where
verification is thin is a map for evading it.

**What we think follows, and why — the asymmetry.** We judge the defensive use
to dominate, and the reason is specific rather than optimistic.

1. **The defensive action is cheap and currently not taken.** Enumeration costs
   nothing at inference time and is absent from the monitor prompts we have
   seen. The finding tells deployers to do something they are not doing.
2. **The offensive use requires control of the monitor's prompt**, and anyone
   who has that control already has easier and more reliable attacks available
   than degrading its wording — disabling the monitor, narrowing its inputs,
   not running it. Prompt vagueness is a worse tool than the tools such an
   attacker already holds.

**The objection to that argument, which we think is the real risk.** The
asymmetry assumes the same party controls the monitor and the system it
watches. Where those come apart it weakens. Two cases:

- **Negligence rather than attack.** A team told to "add a monitor" writes a
  vague prompt and gets a monitor that always says nothing is wrong. No
  adversary is required. This is the case our defensive recommendation
  addresses directly, and it is probably the common one.
- **Self-configured assurance.** Where a party writes the prompt of the monitor
  that audits that same party, vague wording is a deniable way to produce clean
  results. This is a governance problem about **who writes the monitor's
  prompt**, not a technical one, and we name it because our finding makes it
  concrete: the gap between a monitor that detects and one that does not can be
  a sentence of prompt text, invisible in any output the auditor sees.

**A second strand.** The study design is itself a description of how to move a
false claim through a chain uncaught: carry the claim in the handoff, never
re-read the artifact, keep the tool return success-shaped. We name it, but it
is **a description of how ordinary pipelines already fail** rather than a
technique anyone needs this paper to discover. The novelty here is the
measurement, not the failure.

**What we are releasing and why.** Pre-registration, code, prompts and traces,
in full. The defensive recommendation is unusable without the prompts that
produced the effect, and the result is not checkable without the traces. **We
do not argue that this work is harmless because it is small.** Six live runs do
not make a finding safe; they make it uncertain, which is a different thing and
is addressed in §7 and §8.

### Ethics

- **No human subjects.** No participants, no personal data, no user traffic.
- **Synthetic records only.** Every record was generated by the runner
  (`scripts/run_pilot.py`), with random identifiers and values.
- **No real system or third-party service was the target of the injected
  failure.** The silent write failure is injected into our own tool, writing to
  a file in our own run directory.
- **Model disclosure.** An open-weights model accessed through a hosted API:
  Groq, `openai/gpt-oss-120b`, temperature 0.0, max output 4096 tokens. The
  exact string is recorded in every trace's `provider_metadata`. Three earlier
  runs against `gemini-2.5-flash` are declared in amendment 13 and are not
  study data.
- **Tooling.** Implementation was AI-assisted; see the tooling note in §0.

## Appendix B — What was fixed in advance

Every amendment is timestamped, with superseded text struck in place and left
readable. **`PREREGISTRATION.md` §13 is authoritative for the count and the
dates**, and this appendix deliberately carries neither: a count maintained in
two documents goes stale, and in this one it has done so four times.

They fall in three phases. Most precede any study data. One follows the first
three live runs and precedes every run after them, recording a confound found
in our own instrument. One records the head-to-head result and closes that
comparison against further runs. **The last withdraws the registered primary
endpoint**, after we found that published work had answered it before this
pre-registration was written.

**Eight correct errors in our own document**, among them a propagation test
two implementations would have scored differently, a rule stated twice in two
wordings, a false attribution, a prior-work claim about code we had not
written, a p-value we had computed wrongly and corrected before it was used,
and the withdrawal above.

Fixed before any run and not changed afterwards: the n and its power table,
the exclusion categories, the scoring rule for task-level detections, the
canary match rule, the adjudication rule, and what a null looks like. **The
primary endpoint is not on that list** — it was specified before any run and
then withdrawn as uninformative, and the specification is left standing in the
pre-registration unaltered.

**One pre-commitment is load-bearing for §5.** After the head-to-head returned
p = 0.0476, amendment 15 records that **no further runs will be added to that
comparison**: extending n after seeing a p-value just under 0.05 is optional
stopping, and the refusal is in the log rather than only in our intentions.

## LLM Usage Statement

Implementation was AI-assisted. The research design, the pre-registration and
the decisions recorded in its amendment log, the analysis and this report are
the team's, and the team is responsible for everything in it. Every number was
recomputed from the traces by the command in Code and Data, and every citation
was checked against its source before use; the verification table is in
`docs/citation-check.md`. One figure quoted earlier in the project could not be
verified and was withdrawn rather than softened.

---

## Before submitting

- [ ] §2, §6, the abstract and the title **rewritten in the author's voice**;
      every `DRAFT — rewrite` line removed.
- [ ] No `<<` remains.
- [ ] Every rate carries its denominator; no zero without a bound.
- [ ] **Exactly two places state an amendment count** — the abstract and
      Methodology — and both match `PREREGISTRATION.md` §13, which is
      authoritative. Everywhere else points at §13 rather than repeating a
      number. Four stale counts have already been corrected in this project;
      if a third location acquires one, delete it rather than updating it.
- [ ] Every name in §9 did the thing written next to it.
- [ ] Apart's official template, ≤8 pages excluding references and appendices.
- [ ] Figure 1 present with its caption.
- [ ] No citation or figure taken from memory.
