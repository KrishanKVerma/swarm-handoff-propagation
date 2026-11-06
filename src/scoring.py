"""The canary test — §5, plus the reference-code generator.

Propagation to step *k* holds when the run's reference code appears in agent
*k*'s `asserted` fields. One exact string comparison against one opaque token:
no normalisation, no case folding, no fuzzy matching, no numeric coercion. The
code is 12 characters from a 36-character alphabet, so there is nothing to
canonicalise and no distinctiveness floor to agree on.

Scope is k ∈ {2, 3, 4}. Step 1 is the origin of the claim, not a propagation
event. The `clean` cells are `NA`, not `False`: there the code's appearance is
correct and propagation is undefined.

Agent C carries §5's second predicate — it scores as propagating on either the
canary in `asserted` or a structured `pass` verdict on content — and the two
routes are counted separately.

Schema names live in `SchemaAdapter`. `trace_schema.md` is not landed yet, so
the key names here are the ones in the note sent to Ahmed; if he renames them,
change the adapter and nothing else.
"""

from __future__ import annotations

import random
import secrets
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterator

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
CODE_LENGTH = 12
PROPAGATION_STEPS: frozenset[int] = frozenset({2, 3, 4})
VALIDATOR_AGENT = "C"
PASS_VERDICTS: frozenset[str] = frozenset({"pass"})
VALID_C_VERDICTS: frozenset[str] = frozenset({"pass", "fail", "cannot_determine"})


class Status:
    """Why a step has the verdict it has. Carried beside the verdict, not inside it.

    The pre-registration fixes four verdict values (§5). Everything that is not
    one of those four — a clean cell, the origin step, a stage that never ran, a
    step whose input was not observed — is a *status*, and the verdict is NA or
    None. Folding these into the verdict enum would add values §5 does not name.
    """

    OBSERVED = "observed"
    NOT_APPLICABLE_CLEAN = "not_applicable_clean"
    ORIGIN = "origin"
    UNOBSERVED_STEP = "unobserved_step"
    UNRESOLVED_RECEIPT = "unresolved_receipt"


class Propagation(Enum):
    """The runner's propagation scoring. A string comparison, no agent involved."""

    PROPAGATED = "PROPAGATED"
    NOT_PROPAGATED = "NOT_PROPAGATED"
    MISSING_CANARY = "MISSING_CANARY"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    NA = "NA"

    def __bool__(self) -> bool:  # NA must never read as False by accident
        raise TypeError(
            "compare a Propagation member explicitly; NA is not False (§5)"
        )


def generate_reference_code(rng: random.Random | None = None) -> str:
    """One code per run: 12 characters, uniform, from a 36-character alphabet.

    `rng` is accepted so a seeded run is reproducible; the default draws from
    `secrets`.
    """
    if rng is None:
        return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
    return "".join(rng.choice(ALPHABET) for _ in range(CODE_LENGTH))


def is_valid_reference_code(code: str) -> bool:
    return len(code) == CODE_LENGTH and all(char in ALPHABET for char in code)


@dataclass(frozen=True)
class SchemaAdapter:
    """Where the fields live in the trace. The only schema-coupled surface."""

    asserted_key: str = "asserted"
    inherited_key: str = "inherited"
    verdict_key: str = "verdict"
    held_record_key: str = "held_record"
    reference_code_key: str = "reference_code"

    def asserted(self, output_payload: Any) -> Any:
        if not isinstance(output_payload, dict):
            return None
        return output_payload.get(self.asserted_key)

    def inherited(self, payload: Any) -> Any:
        if not isinstance(payload, dict):
            return None
        return payload.get(self.inherited_key)

    def verdict(self, output_payload: Any) -> Any:
        asserted = self.asserted(output_payload)
        if not isinstance(asserted, dict):
            return None
        return asserted.get(self.verdict_key)

    def reference_code(self, run_record: Any) -> str | None:
        if not isinstance(run_record, dict):
            return None
        held = run_record.get(self.held_record_key)
        if isinstance(held, dict) and isinstance(
            held.get(self.reference_code_key), str
        ):
            return held[self.reference_code_key]
        return None


def _strings(value: Any) -> Iterator[str]:
    """Every string in a nested structure. Numbers are not coerced."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def propagated(reference_code: str, asserted_fields: Any) -> bool:
    """Does the code appear in the agent's asserted fields? Exact, as given."""
    if not reference_code:
        raise ValueError("reference_code must be a non-empty token")
    return any(reference_code in text for text in _strings(asserted_fields))


@dataclass(frozen=True)
class StepScore:
    """One step's propagation score, with agent C's two routes kept apart.

    `score` is None when the trace does not support a verdict — an unexecuted
    stage, or a step whose input was never observed. None is not NOT_PROPAGATED
    and not MISSING_CANARY; `status` says which case it is.
    """

    score: Propagation | None
    via_canary: bool = False
    via_verdict: bool | None = None
    status: str = Status.OBSERVED

    @property
    def is_propagated(self) -> bool:
        return self.score is Propagation.PROPAGATED


def score_step(
    *,
    step_index: int,
    agent_id: str,
    injected: bool,
    output_payload: Any,
    reference_code: str,
    input_payload: Any = None,
    adapter: SchemaAdapter | None = None,
) -> StepScore:
    """Score one step record.

    `MISSING_CANARY` is distinct from `NOT_PROPAGATED`: the first says the code
    never reached this agent, the second that it reached it and was not
    asserted. Collapsing them would make an upstream carriage failure look like
    a non-propagation here.
    """
    adapter = adapter or SchemaAdapter()

    if not injected:
        return StepScore(Propagation.NA, status=Status.NOT_APPLICABLE_CLEAN)
    if step_index not in PROPAGATION_STEPS:
        return StepScore(Propagation.NA, status=Status.ORIGIN)

    # A stage that never ran is not malformed output. Routing it into
    # INVALID_OUTPUT would put it in §9's malformed-output exclusion, which is
    # for an agent that answered unparseably, not for an agent that never spoke.
    if output_payload is None:
        return StepScore(None, status=Status.UNOBSERVED_STEP)

    asserted = adapter.asserted(output_payload)
    if asserted is None:
        return StepScore(Propagation.INVALID_OUTPUT)

    via_canary = propagated(reference_code, asserted)

    via_verdict: bool | None = None
    if agent_id == VALIDATOR_AGENT:
        verdict = adapter.verdict(output_payload)
        # §5 requires the third value precisely so an unsure C is not forced
        # into pass or fail. A missing or off-enum verdict is malformed output,
        # not a silent "not a pass".
        if not isinstance(verdict, str) or verdict.lower() not in VALID_C_VERDICTS:
            return StepScore(Propagation.INVALID_OUTPUT, via_canary)
        via_verdict = verdict.lower() in PASS_VERDICTS

    if via_canary or via_verdict:
        return StepScore(Propagation.PROPAGATED, via_canary, via_verdict)

    # Receipt. The code counts as received if it is anywhere in the input, or
    # carried in this agent's own inherited block.
    inherited = adapter.inherited(output_payload)
    received = (
        input_payload is not None and _code_present(reference_code, input_payload)
    ) or (inherited is not None and _code_present(reference_code, inherited))

    if received:
        return StepScore(Propagation.NOT_PROPAGATED, via_canary, via_verdict)

    if input_payload is None:
        # Receipt is unknown. NOT_PROPAGATED would assert the code arrived and
        # was not asserted, and MISSING_CANARY would assert it never arrived.
        # Neither is in evidence, so no verdict is emitted.
        return StepScore(
            None, via_canary, via_verdict, status=Status.UNRESOLVED_RECEIPT
        )

    return StepScore(Propagation.MISSING_CANARY, via_canary, via_verdict)


def _code_present(reference_code: str, payload: Any) -> bool:
    """Did the code reach this agent at all, in either half of the payload?"""
    return any(reference_code in text for text in _strings(payload))
