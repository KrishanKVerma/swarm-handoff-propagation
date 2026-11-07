# What makes a boundary gate look?

### Prompt enumeration determines whether an LLM monitor inspects the artifact

Apart Research Swarm Alignment Hackathon · 6–8 November 2026

**Draft.** Every number is reproduced by
`python3 -m analysis.recompute runs/smoke`. Sections marked `DRAFT` are to be
rewritten in the author's voice before shipping.

---

## 0. Front matter

- **Title.** *What makes a boundary gate look? Prompt enumeration determines
  whether an LLM monitor inspects the artifact* — **DRAFT**, set as the header
  above so the document no longer opens on the withdrawn question.
  Alternatives: *A gate that isn't told what to look for doesn't look*;
  *Enumeration elicits inspection*.
- **Abstract, 150–250 words.** **DRAFT — rewrite in the author's voice.**

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
> The constraint that made our detection metric machine-adjudicable was
> eliciting the behaviour it measured. Six live runs, and a pre-registration
> with sixteen dated amendments, one of which withdraws our own registered
> primary.

- **Authors and affiliations.** `<<AUTHORS_AFFILIATIONS>>`
- **Contributions.** Krishan Kumar Verma: measurement design, pre-registration
  and amendments, injection, oracle, canary scorer, checker tools, prompts,
  live runner, analysis, report. Soumyajit Karmakar: related work; LA-hub
  presentation. From outside the current team, recording work done before the
  project split: Ahmed Tariq (trace format and offline runner, including the
  amendment 7 checker-access and flag-isolation implementation, declared
  preexisting from 5 November where applicable; raised the flag-only rule,
  the checker-evidence question and flag isolation, and both p₁ definitions),
  Supriya Kamatagi (the propagation scoring enum), Nico Smith (the geometric
  framing and the independence question), Dora Zelenyanszki (the p₁ / p₂
  decomposition).
- **Prior-work statement.** See §2 and `PREREGISTRATION.md` §0, which carries
  the file list, line counts and commit timestamps.

> **Tooling.** Implementation was AI-assisted. The research design, the
> pre-registration and the decisions recorded in its amendment log, the
> analysis and this write-up are the team's, and the team is responsible for
> everything in this report.

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

**We registered a different question and withdrew it.** The pre-registration's
primary endpoint was the placement comparison Singh and Pawar had already
answered four and a half months earlier; we found that during the sprint, not
before it, and amendment 16 records the withdrawal and the sequence. No
endpoint from the registered design was reached.

### Why it matters

**DRAFT — rewrite in the author's voice.**

A verifier that never looks is indistinguishable, in every log it produces,
from one that looked and found nothing. Both emit the same clean result. The
difference is invisible to the person reading the output and invisible to the
reviewer who confirms that monitoring exists, and it is not a hypothetical
distinction: in our neutral condition the checkers did not merely miss the
failure, they returned an affirmative judgement that nothing was wrong.

The failure class is real outside the laboratory. An audit of ToolUniverse
found 91 failures across 198 candidate cases, with 7 of 15 tools failing on
more than half of theirs, and most of them silent at the point of use. A tool
that returns a success-shaped response for an action that did not happen leaves
the agent nothing to report but success. That is why this is a measurement
problem rather than a deception problem: the agent's account of its own belief
is accurate, and what is false is a claim about the world that nothing in the
transcript contradicts.

We came to the question from the other side. A 160-run reliability harness
(`github.com/KrishanKVerma/bedrock`, 4 tasks, 2 models) produced an agent that
reported every failure as a success. **That corpus and that harness predate
this sprint, are declared as prior work, and supply no data to this study**;
they are the reason the question seemed worth asking and nothing more. The full
prior-work declaration — which files, how many lines, which commit, which
timestamp, including parts of this repository's runner that predate the sprint
by roughly fifteen hours — is in `PREREGISTRATION.md` §0.

## 2. Related Work

`<<RELATED_WORK>>` — Soumyajit Karmakar's section. Every citation is checked
against the source before it ships; the table is in `docs/citation-check.md`,
and anything unconfirmed is cut rather than softened.

Five placements this section must make, from that check:

- **Singh & Pawar (arXiv 2608.14588)** — the result we build on, stated as
  settled, with its numbers: 346 injected failures, survival 58.4% → 16.2%
  under boundary gates, p < 10⁻⁶. Our contribution sits downstream of it.
- **Panthi & Abdelfattah, *Outcome Monitors* (arXiv 2608.19303)** — cited for
  the injection design, which is theirs as much as ours: faults injected only
  into the text the model observes, environment state unchanged. What differs
  here: a single acting agent rather than a chain, a deterministic
  invariant checker rather than an LLM deciding whether to look, and recovery
  rather than detection as the outcome.
- **Singh, Gopalan & Narayanan, ToolUniverse audit** — 91 failures across 198
  candidate cases, 7 of 15 tools failing on more than half. Evidence that
  silent tool failures occur naturally, which this study's injected design
  cannot establish.
- **Zhao, *CatchBench*** — for framing, and for reporting discipline: 47 of 118
  pre-declared contrasts separate, and the remaining 71 are reported as
  unresolved rather than equal.
- **Najt et al., *SLEIGHT-Bench* (arXiv 2605.16626)** — beside our enumeration
  finding. At 1% FPR an Opus 4.6 monitor never catches 20 of 40 attacks across
  10 trials, 32% overall, and targeted prompts help some blind-spot categories
  while no single prompt covers all.
- **Kemeklis & Vemuri, *Omission Attacks*** — real figures only, and **no
  false-positive rate**, since their report contains none.

## 3. Methodology

### Design

A four-stage pipeline. **A** fetches a record and writes it to a file, **B**
transforms, **C** validates, **D** summarises.

**The injected failure.** A's write tool returns a success-shaped response and
leaves the file unchanged. The response is built from the call's arguments and
never read back from disk, so no field, status or error differs between the
injected and clean modes. A truthfully reports a false belief.

**The handoff carries the content and no agent re-reads the file.** Without
this the failure dies at step two by the task's own mechanics.

**Crossed 2×2** as registered: injection × scheme (`end_monitor`,
`per_handoff`). **No cell of that design was run to its registered n** (§5).

**Verifiers flag only.** They never stop the chain and never repair it, so all
four steps run in every run.

**What the checkers can see.** Every checker gets a read tool on the artifact,
is never told what the file should contain, and never sees the oracle's
verdict. Tool access is identical in both schemes and at both prompt levels.
Nothing instructs a checker to read.

**The failure shape, and why it is not a variant of the prior work.** Singh
and Pawar inject false *content*, which downstream agents then transform — so
at every step there is something in the text that is wrong, and a sufficiently
careful reader of the transcript could find it. We inject a silent *tool*
failure. The agent's report is truthful about its own belief: the content it
passes on is correct, and only its claim about the state of the world is false.
**Nothing in the text is wrong.** Theirs is an error propagating; ours is an
absence propagating. That is why this design reduces to a single question —
does anything read the artifact — and theirs does not.

**Measurement.** Propagation is one exact containment match of the reference
code in an agent's asserted fields, scoped to k ∈ {2,3,4}. Detection is a flag
plus at least one structured claim that the oracle's reading of the file says
is true. Neither reads free text, so neither has a scorer.

**The pre-registration carries the design in full and is public**, with every
rule's reasoning and amendment history, so this report states each once and
points there rather than reproducing it.

**Two deviations from the above, both logged before the runs.** The tool loop
is scripted runner-side — the runner calls A's tools and reports the results to
A, so A does not choose to invoke them (amendment 12). The artifact begins as an
empty JSON object, so `artifact_empty` and `artifact_mismatch` are both true
under injection and `artifact_missing` is false.

**Figure 1** — `figures/chain.svg`.

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

| cell | read at repeat zero |
|---|---|
| `neutral` × `end_monitor` | **0 of 2** (one-sided 95% upper bound 77.6%) |
| `neutral` × `per_handoff` | **1 of 3** (Wilson 95% CI 6.1–79.2%) |

The one checker that read, reported (1 of 1). The enumeration was not only
shaping the claim — **it was driving whether the checker looked at all.** The
distractor options went unused: every non-detection was `no_discrepancy`, not
`transform_error` or `input_mismatch`. The neutral checkers concluded that
nothing was wrong.

**p = 0.0476 rests on a single observation.** One more neutral detection — 2 of
5 — gives p ≈ 0.167, which the pre-registration calls unresolved.

### 4.3 Instrument stability

| arm | verdict flips across repeats |
|---|---|
| `enumerated` | 0 of 5 opportunities |
| `neutral` × `end_monitor` | **1 of 2 opportunities** |
| `neutral` × `per_handoff` | 0 of 3 opportunities |

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

The primary endpoint, the survival curve and the between-scheme difference are
not computed: no cell reached its registered n, pilot runs enter no endpoint by
design, and the smallest cell is 1 run against the 30 per cell the
pre-registration requires. The false-positive rate is not computed because no
`clean` cell was run, and the refusal rate is not computed because the category
is defined and not instrumented (amendment 12).

## 5. Discussion

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

Verdict instability appeared as soon as there was any variance to have: **1 of
2** neutral `end_monitor` opportunities flipped across repeats, while the
enumerated arm's 0 of 5 is zero variance rather than demonstrated stability.

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

It also raises a question for the result we built on. If a gate's effectiveness
depends this much on what it is told, part of Singh and Pawar's boundary-gate
advantage may be a property of what their gates were told rather than of where
they sat. **We cannot test that** — we did not run their comparison, and ours
had no variance left to compare. It is a hypothesis their design could settle
and ours cannot, and it is the thing we would run next, together with a third
arm giving the output format and no options at all, which is the clean version
of the test we ran.

## 6. Limitations and Dual-Use / Ethical Considerations

Three govern how every number here should be read. **Propagation is near-1 by
construction**, because the injection leaves no signal unless something reads
the file: it is a design consequence, not a measurement. **A low read rate on
an open-weights model may be capability rather than propensity**, so the claim
is "the checkers did not read", never "checkers do not bother to verify".
**The one resolved comparison is about our instrument** — six live runs, no
endpoint reached, the registered primary withdrawn.

The full list, what this design cannot establish, and the dual-use and ethics
treatment are in Appendix A, as the submission form requires.

## 7. References

From §2. **Only entries verified against the source appear here**; the
verification table is `docs/citation-check.md`.

1. Prabhjot Singh and Bhushan Pawar. *The Hallucination Snowball: Modeling
   Error Propagation as State Transitions in Multi-Agent LLM Pipelines.*
   arXiv:2608.14588v1, 2026.
2. Sugam Panthi and Rabab Abdelfattah. *Outcome Monitors: Recovery Affordances
   for Silent Tool Failures.* arXiv:2608.19303v1, 2026.
3. Elle Najt, Colin Toft, Tyler Tracy, Fabien Roger and Joe Benton.
   *SLEIGHT-Bench: A Benchmark of Evasion Attacks Against Agent Monitors.*
   arXiv:2605.16626, 2026.
4. Devansh Singh, Shreya Gopalan and Sundaraparipurnan Narayanan. *Silent
   Failures in Agent–Tool Interaction: An Audit of ToolUniverse.* 2026.
5. Yue Zhao. *CatchBench: When Can an Agent Failure Be Caught?* Preprint, 2026.
6. Jurgis Kemeklis and Nikhil Vemuri. *Omission Attacks: When Doing Nothing Is
   the Attack.* Apart Research AI Control Hackathon, 2026.
7. Tomek Korbak et al. *Chain of Thought Monitorability: A New and Fragile
   Opportunity for AI Safety.* arXiv:2507.11473, 2025.
8. Miles Turpin et al. *Language Models Don't Always Say What They Think.*
   arXiv:2305.04388, 2023.

`<<REMAINING_REFERENCES>>` — the entries from Soumyajit's text still awaiting
titles before they can be verified: Huang et al. 2025, Hu 2026, Sun et al.
2024, Advani 2026, Hiller/Jhumka/Suri 2001, Arcuschin et al. 2025, plus FakeLab
(arXiv 2607.07368) and SCHEME (arXiv 2605.29178), verified by the author.

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
