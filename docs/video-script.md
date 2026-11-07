# Three-minute video — script for Soumyajit

LA hub, due 23:30 IST Sunday 8 November. ~430 words, which runs about 3:00 at a
normal speaking pace. Timings are cumulative.

Two rules for delivery: every number keeps its denominator, and nothing is
claimed about agents that the data does not support. The finding is about our
instrument. That is not a hedge — it is the point.

---

**[0:00 – 0:25] The question**

When one agent hands work to another, what travels is a claim, not a verified
state. Agent A says "I wrote the file." Agent B has no way to tell a completed
task from a claimed one. So we asked: how far does an unverified success claim
travel through a chain of agents before anything catches it?

**[0:25 – 1:05] The design**

Four agents in a chain. The first one fetches a record and writes it to a file.
We inject a silent failure: the write tool returns a success response that is
byte-identical to the real one, and the file stays empty. The agent isn't
lying. It truthfully reports a false belief.

Nothing downstream re-reads the file, so the claim is the only carrier. We put
a twelve-character random code in the record, and propagation is just that code
appearing in an agent's own output. One string match, no human judgement.

Then we gave checkers a read tool on the file — and told them nothing about
what it should contain, and nothing that instructs them to use it. Whether a
checker with the means to verify actually does is the thing we measure.

**[1:05 – 1:35] It runs**

The pipeline executes end to end against a real model. Injection fires, the
oracle reads, the scorer decides, the adjudicator resolves.

And the first thing it found was a flaw in our own instrument.

**[1:35 – 2:25] The finding**

To make detection machine-scoreable instead of a judgement call, we required
checkers to pick from a fixed list of claims. That list names artifact-level
failures — so the thing that made detection objective was also telling the
checker where to look.

We tested it. With the list naming the artifact, checkers detected the failure
in five of five opportunities. With the artifact sitting among plausible
alternatives instead, one of five. Fisher exact, two-sided, p equals 0.048.

And the mechanism isn't what they claimed — it's whether they looked at all.
In the neutral condition they mostly didn't read the file. The one that read,
reported.

**[2:25 – 3:00] What it means, and what it doesn't**

That p-value rests on a single observation. One more detection and it's
unresolved, and we wrote that threshold down before we ran it. We also wrote
down that we would not add runs to improve it.

The general point survives the small numbers. If you constrain a monitor's
output to make it machine-adjudicable, you may be eliciting the very behaviour
you are trying to measure. Anyone evaluating monitors is doing this, and it is
invisible until the instrument runs.

Pre-registration, fifteen dated amendments, and all the code are public.

---

## Delivery notes

- **Do not say "100%".** Say "five of five". If asked, the lower bound is 56.6%.
- **Do not say "checkers don't bother to verify."** It may be that this model
  could not follow a two-turn tool offer. Say "they did not read the file" and
  leave the cause open.
- If asked for the headline result about agents: **there isn't one.** Six live
  runs, no endpoint computed, nothing reached its registered n. The resolved
  finding is about the instrument.
- If asked why the pilot stopped at three runs: the free tier allows 200,000
  tokens a day and the measurement was already at ceiling — more runs would
  have tightened an interval around a number the next slide shows we should
  not trust.
- If asked what's next: a third arm with the output format and no options at
  all, which is the clean version of this test.
