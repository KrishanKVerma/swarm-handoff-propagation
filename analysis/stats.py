"""The numbers. Every rate carries its denominator; no zero without a bound.

p1 is the read rate per checker **opportunity**, computed on **repeat zero
only** — five repeats are five evaluations of one opportunity, and pooling them
would inflate the denominator fivefold on evidence that is not independent
(§7, amendment 8). p1 counts a **successful** read, not an attempted one.

p2 is a mismatch reported given a successful read. p = p1 x p2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Z95 = 1.959963984540054


@dataclass(frozen=True)
class Rate:
    k: int
    n: int

    @property
    def point(self) -> float | None:
        return None if self.n == 0 else self.k / self.n

    @property
    def interval(self) -> tuple[float, float] | None:
        return None if self.n == 0 else wilson(self.k, self.n)

    @property
    def upper_bound_one_sided_95(self) -> float | None:
        """For a zero numerator: the exact bound, never 'zero'."""
        if self.n == 0 or self.k != 0:
            return None
        return 1 - 0.05 ** (1 / self.n)

    def render(self) -> str:
        if self.n == 0:
            return "0 of 0 — no denominator"
        text = f"{self.k} of {self.n} ({100 * self.point:.1f}%"
        low, high = self.interval  # type: ignore[misc]
        text += f", Wilson 95% CI {100 * low:.1f}–{100 * high:.1f}%)"
        if self.k == 0:
            text += f"; one-sided 95% upper bound {100 * self.upper_bound_one_sided_95:.1f}%"
        return text


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    if n == 0:
        raise ValueError("a rate with no denominator is not a rate")
    if k == 0:
        return (0.0, _wilson_raw(k, n, z)[1])
    if k == n:
        return (_wilson_raw(k, n, z)[0], 1.0)
    return _wilson_raw(k, n, z)


def _wilson_raw(k: int, n: int, z: float) -> tuple[float, float]:
    phat = k / n
    denominator = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denominator
    spread = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denominator
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def geometric_prediction(p: float, draws: int = 3) -> float:
    """1 - (1 - p)^draws. What independence predicts for per_handoff."""
    return 1 - (1 - p) ** draws


@dataclass(frozen=True)
class FlipRate:
    """The instrument check (§10): inputs whose verdict changed across repeats."""

    flipped: int
    inputs: int

    def as_rate(self) -> Rate:
        return Rate(self.flipped, self.inputs)


def flip_rate(groups: list[list[bool | None]]) -> FlipRate:
    """One group per opportunity, one entry per repeat's flag."""
    usable = [g for g in groups if len([v for v in g if v is not None]) > 1]
    flipped = sum(1 for g in usable if len({v for v in g if v is not None}) > 1)
    return FlipRate(flipped, len(usable))


def fisher_exact_2x2(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for [[a, b], [c, d]].

    Sums the probability of every table with the same margins whose
    probability is no greater than the observed one. Exact, so it is usable at
    the n this study actually has.
    """
    from math import comb

    row1, row2 = a + b, c + d
    col1 = a + c
    total = row1 + row2
    if total == 0 or row1 == 0 or row2 == 0 or col1 == 0 or col1 == total:
        return 1.0

    def probability(x: int) -> float:
        return comb(row1, x) * comb(row2, col1 - x) / comb(total, col1)

    observed = probability(a)
    low = max(0, col1 - row2)
    high = min(row1, col1)
    tolerance = observed * (1 + 1e-9)
    return min(1.0, sum(probability(x) for x in range(low, high + 1)
                        if probability(x) <= tolerance))
