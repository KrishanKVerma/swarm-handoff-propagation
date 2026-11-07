# How far does an unverified success claim travel through an agent chain?

Apart Research Swarm Alignment Hackathon · 6–8 November 2026

**Draft. §2 and §6 are not written here — they are the author's prose and are
marked `<<AUTHOR>>`. Everything else is filled from the traces. Every number
below is reproduced by `python3 -m analysis.recompute runs/smoke`; none was
typed in by hand.**

---

## 0. Front matter

- **Title.** `<<TITLE>>`
- **Abstract, 150–250 words.** `<<ABSTRACT>>` — written last, after §6.
- **Authors and affiliations.** `<<AUTHORS_AFFILIATIONS>>`
- **Prior-work statement.** See §2 and `PREREGISTRATION.md` §0, which carries
  the file list, line counts and commit timestamps.

> **Tooling.** Implementation was AI-assisted. The research design, the
> pre-registration and the decisions recorded in its amendment log, the
> analysis and this write-up are the team's, and the team is responsible for
> everything in this report.

## 1. What we asked

How far does an unverified success claim travel through a chain of agents
before anything catches it, and does a verifier at every handoff catch it
earlier than a monitor at the end?

**What we are able to answer is narrower, and the distinction is the report.**
No endpoint was reached. What we have is an instrument, a pre-registration with
fifteen dated amendments, and one resolved finding — about the instrument
rather than about agents.

## 2. Why it matters

`<<AUTHOR>>`

*Must contain: handoffs carry claims, not verified state; the 160-run corpus
and the bedrock harness as motivation only, declared preexisting and supplying
no data; and the prior-work declaration in this report's own voice.*

## 3. Design

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

**The canary test.** The record carries a 12-character random reference code
the pipeline carries and never transforms. Propagation to step *k* is that code
appearing in agent *k*'s asserted fields: one exact containment match, no
scorer, scoped to k ∈ {2,3,4}.

**Adjudicated detection.** A checker that flags emits a structured claim from a
closed set; detection is a flag plus at least one claim the oracle's reading of
the file says is true. No text is parsed.

**Two deviations from the above, both logged before the runs.** The tool loop
is scripted runner-side — the runner calls A's tools and reports the results to
A, so A does not choose to invoke them (amendment 12). The artifact begins as an
empty JSON object, so `artifact_empty` and `artifact_mismatch` are both true
under injection and `artifact_missing` is false.

**Figure 1** — `figures/chain.svg`.

## 4. What was fixed in advance

Fifteen amendments, each timestamped, superseded text struck in place and left
readable. Entries 1–13 precede any study data. Entry 14 follows the first three
runs and precedes every run after them. Entry 15 records the head-to-head
result and closes the comparison.

**Eight of the fifteen correct errors in our own document**, including a
propagation test two implementations would have scored differently, a rule
stated twice in two wordings, a false attribution, a prior-work claim about
code we had not written, and — in entry 15 — a p-value we had computed wrongly
in entry 14, corrected before it was used.

Fixed before any run and not changed afterwards: the primary endpoint, the n
and its power table, the exclusion categories, the scoring rule for
task-level detections, the canary match rule, the adjudication rule, and what
a null looks like.

**One pre-commitment is load-bearing for §5.** After the head-to-head returned
p = 0.0476, amendment 15 records that **no further runs will be added to that
comparison**: extending n after seeing a p-value just under 0.05 is optional
stopping, and the refusal is in the log rather than only in our intentions.

## 5. Results

**Pilot runs enter no endpoint (§10). Nothing below is a study result about
agents.** The primary endpoint, the survival curve and the between-scheme
comparison are **not computed**, because no cell reached its registered n and
pilot runs are excluded from every endpoint by design.

**Provider.** Groq, `openai/gpt-oss-120b`, temperature 0.0, max output 4096,
frozen in every trace's `provider_metadata`. 6 live runs, all `inject`, all
`invisible` salience, 2 repeats per opportunity, ~91,600 tokens. **No
exclusions.** Three earlier runs against `gemini-2.5-flash` are declared in
amendment 13 and are not study data.

### 5.1 The pilot was stopped at three runs

All five confirmations §10 required were met at n = 3: the injection fired, the
oracle read correctly, the canary test decided cleanly, the stability check had
input from both checker roles, and the adjudicator resolved claims against
oracle state.

| quantity (enumerated prompt) | value |
|---|---|
| p₁, read rate at repeat zero | **5 of 5** (Wilson 95% CI 56.6–100%) |
| p₂, reported given a read | **5 of 5** |
| p = p₁ × p₂ | 1.0 |
| claims emitted | `artifact_mismatch`, 10 of 10 evaluations |

**Both components are saturated, not only p₁: every checker that read also
reported.** At p = 1 the independence secondary is vacuous — 1 − (1 − 1)³ = 1,
with no shortfall to interpret. **5 of 5 does not establish p = 1**; the lower
bound is 56.6%.

### 5.2 The enumeration confound

The claim set that amendment 10 introduced to make detection machine-decidable
lives in the checker's prompt and names artifact-level failures. The instrument
that made detection adjudicable **also told the checker where to look.**

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

### 5.3 Instrument stability

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

### 5.4 Not computed

| quantity | why |
|---|---|
| primary endpoint, uncaught at step four | no cell reached its registered n; pilot runs enter no endpoint |
| survival curve | same |
| between-scheme difference | smallest cell is 1 run against the 30 per cell §8 requires |
| false-positive rate per scheme | no `clean` cell was run |
| refusal rate | the category is defined and **not instrumented** (amendment 12) |

## 6. What we found

`<<AUTHOR>>`

*Three to five sentences. Each must be traceable to a number in §5. The
candidates: the instrument reached ceiling end to end; the thing that made
detection machine-decidable was also eliciting it; the mechanism is reading,
not reporting; and whether this design can resolve anything is open.*

## 7. Limitations

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
- **One task family, one provider, one model, constructed failure, n = 6 live
  runs.**

## 8. What this cannot establish

The asymmetry. This design can show that a claim propagated uncaught. It cannot
establish that a verification scheme is sufficient: it probes one failure shape,
and the space of silent failures is unbounded.

And at this n it establishes nothing about agents at all. The one resolved
comparison is about **our instrument**.

## 9. Team and contributions

**On this submission:**

| | |
|---|---|
| Krishan Kumar Verma | measurement design, pre-registration and amendments, injection, oracle, canary scorer, checker tools, prompts, live runner, analysis, report |
| Soumyajit Karmakar | related work; LA-hub presentation |

**Contributions from outside the current team.** Not on this submission; the
credits record work contributed before the project split.

- **Ahmed Tariq** — trace format and offline runner, including the amendment 7
  checker-access and flag-isolation implementation, declared preexisting from
  5 November where applicable; raised the flag-only rule (amendment 3), the
  checker-evidence question and flag isolation (amendment 7), and both p₁
  definitions (amendment 8).
- **Supriya Kamatagi** — the runner's propagation scoring enum (amendment 7).
- **Nico Smith** — the geometric framing and the independence question
  (amendment 7).
- **Dora Zelenyanszki** — the p₁ / p₂ decomposition.

## 10. Appendix — Limitations and Dual-Use / Ethical Considerations

**Required under this name by the submission form.**

### Limitations

§7 and §8, in full.

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

---

## Before submitting

- [ ] `<<AUTHOR>>` sections written: §2, §6, abstract.
- [ ] No `<<` remains.
- [ ] Every rate carries its denominator; no zero without a bound.
- [ ] Amendment count here matches `PREREGISTRATION.md` §13 (fifteen).
- [ ] Every name in §9 did the thing written next to it.
- [ ] Apart's official template, ≤8 pages excluding references and appendices.
- [ ] Figure 1 present with its caption.
- [ ] No citation or figure taken from memory.
