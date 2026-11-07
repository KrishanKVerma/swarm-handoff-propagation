# Three-minute video — LA hub

Due 23:30 IST Sunday 8 November. ~450 words, lands around 2:55 at a normal
pace. Written to be said out loud; Soumyajit puts it in his own words.

**Slow down at the 2:10 beat.** It is the turn of the whole talk and it needs
room.

---

**[0:00] The hook**

A monitor that never looks is indistinguishable, in every log it produces, from
one that looked and found nothing. Both come back clean. We built a four-agent
pipeline to find out which one you actually have.

**[0:25] What's already settled**

Where to put a verifier is a solved question. Singh and Pawar ran 346 injected
failures through a four-agent chain and showed that checking at every handoff
cuts failure survival from 58 percent to 16, against checking once at the end.
We take that. We don't re-run it.

**[0:50] The question that leaves open**

A gate is a language model with a tool and an instruction. Placement decides
how often it runs. Nothing about placement decides whether, on any given run,
it actually looks.

So we built a failure that isolates exactly that. The first agent's write tool
returns success. The file stays empty. The agent's report is truthful — it
genuinely believes it wrote the file. Nothing in the transcript is wrong.
There's no error to find, only an absence. Which means detection reduces to one
question: does anything open the artifact?

**[1:25] The finding**

It does — but only when told to.

With the checker's prompt naming candidate failure modes, we got detection in
five opportunities out of five. With the same model, the same tool, the same
evidence, and those options sitting among plausible alternatives: one out of
five. Fisher exact, p equals 0.048.

And the mechanism isn't what they reported. It's whether they read at all. In
the neutral condition the checkers mostly never opened the file — and they
didn't pick a wrong answer either. They returned an affirmative "no
discrepancy." They concluded nothing was wrong.

**[2:10] The twist** — *slow down here*

Here's how we found it. We'd constrained the checker to a fixed set of claims
so that detection could be machine-adjudicated with no human scorer. That list
lives in the checker's prompt. The thing that made our metric rigorous was
eliciting the behaviour the metric measured.

Our own instrument was the confound, and we found it three runs in.

**[2:35] The honest frame**

Six live runs. No endpoint computed. And a pre-registration with sixteen dated
amendments — one of which withdraws our own registered primary, because we
discovered mid-sprint that published work had answered it before we wrote it
down.

What the result licenses is narrow: a monitor's prompt is a parameter of its
sensitivity, and a cheap one. Same model, same tool, one in five to five in
five, on wording.

Everything is public — pre-registration, code, prompts, traces.

---

## Delivery notes

- **Never say "100%".** Say "five of five". If pressed, the Wilson lower bound
  is 56.6%.
- **Never say "checkers don't bother to verify."** It may be that this model
  could not follow a two-turn tool offer. Say "they did not open the file" and
  leave the cause open.
- **On Singh and Pawar: we take their result, we do not dispute it.** If asked
  whether our finding undercuts them, the answer is no — it raises a question
  their design can answer and ours cannot, which is how the report puts it.
- **If asked for a headline result about agents: there isn't one.** Six live
  runs, no endpoint computed, nothing reached its registered n. The resolved
  finding is about the instrument.
- **If asked why the pilot stopped at three runs:** the free tier allows
  200,000 tokens a day and the measurement was already at ceiling — more runs
  would have tightened an interval around a number we had just learned not to
  trust.
- **If asked what's next:** a third arm giving the output format with no
  options at all, which is the clean version of this test; and a boundary-gate
  study at their n, run twice with the gate prompt enumerated and not.
