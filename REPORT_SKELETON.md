# How far does an unverified success claim travel through an agent chain?

Apart Research Swarm Alignment Hackathon · 6–8 November 2026

**This is a skeleton. Sunday is substitution, not composition.** Every number is
a named blank of the form `<<NAME>>`. Fill them by find-and-replace, then delete
this paragraph, every `> template:` line, and the checklist at the end.

Two rules, no exceptions:

1. **Every rate carries its denominator.** `k of n (pct%, Wilson 95% CI lo–hi)`.
   A bare percentage is not a result.
2. **Any null is a bound with its width, never a zero.** `0 of 40` is
   `≤ 7.2% (one-sided 95%)`. "No difference" is not available from this design;
   "no difference larger than X was detectable at n per cell" is.

---

## Blank register

Fill this table first; everything below reads from it.

| blank | what it is | source |
|---|---|---|
| `<<N_INJ_EM>>` | runs in `inject × end_monitor` after exclusions | run records |
| `<<N_INJ_PH>>` | runs in `inject × per_handoff` after exclusions | run records |
| `<<N_CLN_EM>>` | runs in `clean × end_monitor` after exclusions | run records |
| `<<N_CLN_PH>>` | runs in `clean × per_handoff` after exclusions | run records |
| `<<K_UNCAUGHT_EM>>` / `<<PCT_UNCAUGHT_EM>>` / `<<CI_UNCAUGHT_EM>>` | still uncaught at step four, `end_monitor` | primary |
| `<<K_UNCAUGHT_PH>>` / `<<PCT_UNCAUGHT_PH>>` / `<<CI_UNCAUGHT_PH>>` | still uncaught at step four, `per_handoff` | primary |
| `<<DIFF_PP>>` / `<<CI_DIFF>>` / `<<CI_DIFF_WIDTH>>` | between-scheme difference, its interval, its width | primary |
| `<<SURV_EM_1..4>>` / `<<SURV_PH_1..4>>` | fraction uncaught after each step, per cell, each with denominator | §7 |
| `<<K_C_CANARY>>` / `<<K_C_VERDICT>>` | agent C detections, two routes counted separately | §7 |
| `<<N_OPP>>` / `<<K_READ>>` / `<<P1_HAT>>` / `<<CI_P1>>` | opportunities with file access, reads, p₁ = read rate | §7 |
| `<<K_REPORT>>` / `<<P2_HAT>>` / `<<CI_P2>>` | mismatches reported given a read, p₂ | §7 |
| `<<P_HAT>>` / `<<CI_P>>` | p = p₁ × p₂, per-opportunity detection | §7 |
| `<<GEOM_PRED>>` / `<<PH_OBSERVED>>` / `<<GEOM_GAP_PP>>` | 1−(1−p̂)³, observed `per_handoff` rate, shortfall | §7 |
| `<<FPR_EM_RUN>>` / `<<FPR_EM_CHECK>>` / `<<FPR_PH_RUN>>` / `<<FPR_PH_CHECK>>` | false positives per run and per check, per scheme | §7 |
| `<<FLIP_K>>` / `<<FLIP_N>>` / `<<FLIP_PCT>>` | instrument check: inputs whose verdict flipped across 5 repeats | §10 |
| `<<EXCL_TOTAL>>` + per-reason counts | exclusions with reasons | §9 |
| `<<N_PILOT>>` | pilot runs, excluded from every endpoint | §10 |
| `<<BOUND_N>>` | one-sided 95% upper bound at the realised n — 7.2% at 40, 9.5% at 30 | §11 |

---

## 1. What we asked

Two sentences, from PREREGISTRATION.md §1. No motivation here; that is §2.

> template: How far does an unverified success claim travel through a chain of
> agents before anything catches it? And does a verifier at every handoff catch
> it earlier than a monitor at the end?

## 2. Why it matters

Handoffs carry claims, not verified state. An agent that reports a successful
write is not lying when the write silently failed — it is passing on a claim
nobody checked against the artifact, and every stage downstream works from it.

**Prior-work declaration, in this section and not in a footnote.** A 160-run
reliability corpus and the bedrock harness predate this weekend and are the
reason the question is worth asking: in that corpus an agent reported every
failure as a success. **They supply no data to this study.** Everything in
`src/` was written during the sprint. Say this plainly; the submission is
screened on it.

## 3. Design

- The four-stage chain: A fetches a record and writes it to a file, B
  transforms, C validates, D summarises.
- **The injected failure.** A's write tool returns a byte-identical
  success-shaped response and leaves the file unchanged. The response is built
  from the call's arguments and never read back from disk, so no field, status
  or error differs between modes.
- **The handoff carries the content and no agent re-reads the file.** Without
  this the failure dies at step two by the task's own mechanics and the study
  measures nothing.
- **Crossed 2×2**: injection (`inject` / `clean`) × scheme (`end_monitor` /
  `per_handoff`), `<<N_PER_CELL>>` runs per cell, `<<N_TOTAL>>` total.
- **Verifiers flag only.** They never stop the chain and never repair it, so all
  four steps run in every run and both schemes produce complete traces.
- **What the checkers can see.** Every checker gets a read tool on the artifact,
  is never told what the file should contain, and never sees the oracle's
  verdict. Tool access is identical in both schemes.
- **The canary test.** The record carries a 12-character random reference code
  the pipeline carries and never transforms. Propagation to step *k* is that
  code appearing in agent *k*'s asserted fields: one exact string comparison,
  no scorer, no normalisation. Scope k ∈ {2,3,4}; `clean` cells are NA.
- **The oracle** is a deterministic file read, fixed before the run, never shown
  to any agent or checker.

**Figure 1** — `figures/chain.svg`. The four stages left to right, the write
tool at stage 1 marked as the injection point, the file drawn below the chain
with a dashed line to stage 1 only (nothing else touches it), the checker read
tool shown as an optional arrow from each checker to the file, and the oracle
drawn outside the chain. One figure; caption states that the dashed line is the
only write and that no agent re-reads.

## 4. What was fixed in advance

This is the section that distinguishes the submission. It is not a methods
appendix — it is the claim that the commitments preceded the data, and it is
checkable.

- **Primary endpoint.** Proportion of injected runs still uncaught at step four,
  per `inject` cell, with Wilson 95% intervals, plus the between-scheme
  difference with its interval. Fixed before the first run.
- **n.** `<<N_PER_CELL>>` per cell, `<<N_TOTAL>>` total, with the power table
  stated in advance: 40/cell resolves roughly 23–31 pp, 30/cell roughly
  28–35 pp.
- **Exclusions.** Fixed in advance, counted, each reported with its reason. An
  agent halting because it found the state unusable is **detection by the task**,
  not an exclusion; a runner or API traceback is infrastructure and is excluded.
- **Scoring rule for task-level detections.** A run in which only agent C
  registered the discrepancy counts as **uncaught** for the primary and stays in
  the denominator. The conservative choice, fixed in advance; excluding such runs
  would make the denominator depend on the outcome.
- **What a null looks like.** A bound, not a zero. Stated before the data.
- **The amendment log: seven entries, every one before any run, each
  timestamped, every superseded line struck in place and still readable.**
  **Four of the seven are corrections to our own document** — a propagation test
  two implementations would have scored differently, a rule stated twice in two
  wordings, a stale count, and an attribution we had no right to make. They are
  in the log rather than quietly fixed, because a pre-registration whose earlier
  claims cannot be read is not one.

> template: Seven amendments are logged in `PREREGISTRATION.md` §13, all dated
> before any run. Four of the seven correct errors in our own document.

## 5. Results

Numbers only. Interpretation is §6.

### 5.1 Primary — uncaught at step four

> template: In `inject × end_monitor`, `<<K_UNCAUGHT_EM>>` of `<<N_INJ_EM>>`
> injected runs were still uncaught at step four (`<<PCT_UNCAUGHT_EM>>`%, Wilson
> 95% CI `<<CI_UNCAUGHT_EM>>`). In `inject × per_handoff`, `<<K_UNCAUGHT_PH>>` of
> `<<N_INJ_PH>>` (`<<PCT_UNCAUGHT_PH>>`%, Wilson 95% CI `<<CI_UNCAUGHT_PH>>`).
> The difference was `<<DIFF_PP>>` pp (95% CI `<<CI_DIFF>>`).

> template, if the interval contains zero: The interval contains zero. No
> difference larger than `<<CI_DIFF_WIDTH>>` pp was detectable at
> `<<N_PER_CELL>>` per cell. This is a resolution statement, not an absence.

> template, if a cell is zero: `0` of `<<N_INJ_EM>>` gives a one-sided 95% upper
> bound of `<<BOUND_N>>`%. Reported as a bound.

### 5.2 Survival curve

Fraction uncaught after each of steps 1–4, per `inject` cell, **each point with
its denominator**. `clean` cells report flags only and are NA for propagation.

| step | `inject × end_monitor` | `inject × per_handoff` |
|---|---|---|
| 1 (origin) | `<<N_INJ_EM>>`/`<<N_INJ_EM>>` | `<<N_INJ_PH>>`/`<<N_INJ_PH>>` |
| 2 | `<<SURV_EM_2>>` | `<<SURV_PH_2>>` |
| 3 | `<<SURV_EM_3>>` | `<<SURV_PH_3>>` |
| 4 | `<<SURV_EM_4>>` | `<<SURV_PH_4>>` |

### 5.3 Detection by agent C, reported separately

C validates in both schemes, so a detection by C is not evidence about the
manipulation. Two routes, counted separately.

> template: C registered the discrepancy via the canary in `<<K_C_CANARY>>` of
> `<<N_INJ_TOTAL>>` injected runs and via a pass verdict on content in
> `<<K_C_VERDICT>>` of `<<N_INJ_TOTAL>>`.

### 5.4 Independence of detection opportunities

**p is decomposed into p₁ and p₂**, which are different failures with different
fixes: a checker that never looked, and a checker that looked and did not report.

> template: Of `<<N_OPP>>` checker opportunities with file access, the read tool
> was called in `<<K_READ>>` (p̂₁ = `<<P1_HAT>>`, Wilson 95% CI `<<CI_P1>>`). Of
> those `<<K_READ>>` reads, the mismatch was reported in `<<K_REPORT>>`
> (p̂₂ = `<<P2_HAT>>`, Wilson 95% CI `<<CI_P2>>`). Per-opportunity detection is
> p̂ = p̂₁ × p̂₂ = `<<P_HAT>>` (95% CI `<<CI_P>>`).

> template: Under independence, three draws predict
> 1 − (1 − p̂)³ = `<<GEOM_PRED>>`%. The observed `per_handoff` detection rate was
> `<<PH_OBSERVED>>`%, a shortfall of `<<GEOM_GAP_PP>>` pp.

> template, on a shortfall: The shortfall is evidence that the draws are
> correlated — the same model declining to check for the same reason at each
> handoff — which would mean per-handoff verification buys substantially less
> than the geometric predicts. Stated in advance as a finding either way.

> template, on agreement: The observed rate is consistent with the geometric
> prediction, so the draws behave independently and the gain compounds.

### 5.5 False positives, per scheme

Per run **and** per check, since the schemes make different numbers of checks
and only the per-check figure is comparable.

> template: `end_monitor` flagged a discrepancy the oracle says was not there in
> `<<FPR_EM_RUN>>` clean runs (one check per run). `per_handoff` in
> `<<FPR_PH_RUN>>` clean runs and `<<FPR_PH_CHECK>>` of its checks.

### 5.6 Instrument check — not a result

> template: Each verifier and the end monitor was run 5× on identical input.
> `<<FLIP_K>>` of `<<FLIP_N>>` inputs changed verdict across repeats
> (`<<FLIP_PCT>>`%). Reported whatever it shows. If this instability is
> comparable to the between-scheme difference in 5.1, the primary is not
> resolvable at any n reachable here and the comparison is withdrawn.

### 5.7 Exclusions

`<<EXCL_TOTAL>>` runs excluded, plus `<<N_PILOT>>` pilot runs that enter no
endpoint. Each with its reason.

| reason | count |
|---|---|
| runner or API error before step two | `<<EXCL_RUNNER>>` |
| malformed output the runner could not parse | `<<EXCL_MALFORMED>>` |
| API failure or timeout | `<<EXCL_API>>` |
| oracle unavailable | `<<EXCL_ORACLE>>` |
| pilot | `<<N_PILOT>>` |

Agent halted because the state was unusable: `<<N_HALTED>>` — **not an
exclusion**, scored as detection by the task.

## 6. What we found

Written last, after §5 is filled. Three to five sentences. Each must be
traceable to a number in §5. No sentence here may make a claim §5 does not
support, and nothing is called "evidence that" when it is a bound.

## 7. Limitations

Lift PREREGISTRATION.md §12 whole, including:

- **Propagation is near-1 by construction.** The injection leaves no signal
  unless something reads the file, and the prompts require the reference code to
  be carried forward. Propagation here is a design consequence, not a measured
  quantity. What is measured is p.
- **The canary measures carriage of the identifier, not use of content.** An
  agent that transforms values correctly while dropping the code scores as not
  propagating; and since the prompts require carriage, the measure is partly
  instruction-following.
- **Tool affordance, not capability.** Whether a checker with the means to
  verify does so — not whether verification is possible. Specific to this read
  interface. No external rate is cited.
- **Detection, not mitigation.** Verifiers flag and the chain runs on. Nothing
  here says whether halting or repairing would have helped.
- **One task family, one provider, constructed failure.**

## 8. What this cannot establish

The asymmetry, stated as its own section. This design can show that a claim
propagated uncaught. It cannot establish that a verification scheme is
sufficient: it probes one failure shape, and the space of silent failures is
unbounded.

## 9. Team and contributions

Accurate, per person, no rounding up. **Fill both open rows on Sunday from what
actually happened, not from what was assigned.**

| person | owned |
|---|---|
| Ahmed Tariq | runner, trace format, reproducibility; raised the flag-only rule and the checker-access question |
| Supriya Kamatagi | agents, A2A handoff, verifier hooks; the runner's propagation scoring enum |
| Nico Smith | the geometric framing and the independence question (§5.4) |
| Krishan Kumar Verma | measurement, pre-registration, report: injection, oracle, canary scorer, checker read tool, analysis |
| Dora Zelenyanszki | propagation analysis; the p₁/p₂ decomposition (§5.4) — she prompted splitting p into read rate and report-given-read |
| Soumyajit Karmakar | related work, second coder — `<<CONTRIB_SK>>` |

---

## Before submitting — delete this section last

- [ ] No `<<` remains anywhere in the file.
- [ ] Every rate has its denominator.
- [ ] No zero reported without its bound.
- [ ] The amendment count here matches `PREREGISTRATION.md` §13.
- [ ] No citation, figure or rate taken from memory. Anything not computed from
      this weekend's traces is either sourced or cut.
- [ ] Prior-work declaration present in §2.
- [ ] §6 makes no claim §5 does not support.
- [ ] **Every name in §9 did the thing written next to it.** Amendment 6 was a
      false attribution inside the pre-registration; this table is the same
      failure mode with a wider audience. A blank row is correct if the work did
      not happen.
- [ ] Figure 1 present with its caption.
