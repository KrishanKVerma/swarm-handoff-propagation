"""§5's canary test: exact, scoped to k in {2,3,4}, NA on clean."""

from __future__ import annotations

import random

import pytest

from src.scoring import (
    ALPHABET,
    CODE_LENGTH,
    Propagation,
    SchemaAdapter,
    StepScore,
    generate_reference_code,
    is_valid_reference_code,
    propagated,
    score_step,
)

CODE = "K3M9QX7ZP2WD"


def _payload(asserted, inherited=None, verdict=None):
    asserted_block = dict(asserted)
    if verdict is not None:
        asserted_block["verdict"] = verdict
    return {"asserted": asserted_block, "inherited": inherited or {}}


# --- the code itself ------------------------------------------------------


def test_code_is_twelve_characters_from_the_alphabet():
    code = generate_reference_code()
    assert len(code) == CODE_LENGTH
    assert all(char in ALPHABET for char in code)


def test_alphabet_is_thirty_six_characters():
    assert len(set(ALPHABET)) == 36


def test_seeded_generation_is_reproducible():
    assert generate_reference_code(random.Random(7)) == generate_reference_code(
        random.Random(7)
    )


def test_distinct_codes_across_runs():
    codes = {generate_reference_code() for _ in range(200)}
    assert len(codes) == 200


def test_validity_check():
    assert is_valid_reference_code(CODE)
    assert not is_valid_reference_code(CODE.lower())
    assert not is_valid_reference_code(CODE[:-1])


# --- the comparison is exact ---------------------------------------------


def test_exact_match_in_a_nested_asserted_field():
    assert propagated(CODE, {"summary": {"ref": f"record {CODE} processed"}}) is True


def test_case_folding_is_not_applied():
    assert propagated(CODE, {"ref": CODE.lower()}) is False


def test_whitespace_inside_the_token_is_not_normalised():
    assert propagated(CODE, {"ref": "K3M9QX7Z P2WD"}) is False


def test_numbers_are_not_coerced_to_strings():
    assert propagated("123456789012", {"rows": 123456789012}) is False


def test_absent_code_is_false():
    assert propagated(CODE, {"summary": "nothing to report"}) is False


def test_empty_code_is_refused():
    with pytest.raises(ValueError):
        propagated("", {"ref": CODE})


# --- scope ----------------------------------------------------------------


def test_step_one_is_na_because_it_is_the_origin():
    score = score_step(
        step_index=1,
        agent_id="A",
        injected=True,
        output_payload=_payload({"ref": CODE}),
        reference_code=CODE,
    )
    assert score.score is Propagation.NA


def test_clean_cells_are_na_not_false():
    score = score_step(
        step_index=2,
        agent_id="B",
        injected=False,
        output_payload=_payload({"ref": CODE}),
        reference_code=CODE,
    )
    assert score.score is Propagation.NA
    assert score.score is not Propagation.NOT_PROPAGATED


def test_na_cannot_be_read_as_false():
    """The failure this guards: `if score:` treating NA as a negative."""
    with pytest.raises(TypeError):
        bool(Propagation.NA)


@pytest.mark.parametrize("step", [2, 3, 4])
def test_scored_steps(step):
    score = score_step(
        step_index=step,
        agent_id="B",
        injected=True,
        output_payload=_payload({"ref": CODE}),
        reference_code=CODE,
    )
    assert score.score is Propagation.PROPAGATED


# --- asserted vs inherited ------------------------------------------------


def test_code_only_in_inherited_is_not_propagation():
    """Carrying it through is not asserting it (§5)."""
    score = score_step(
        step_index=2,
        agent_id="B",
        injected=True,
        output_payload=_payload({"summary": "done"}, inherited={"ref": CODE}),
        reference_code=CODE,
    )
    assert score.score is Propagation.NOT_PROPAGATED


def test_missing_canary_is_distinct_from_not_propagated():
    """The code never reached this agent at all."""
    score = score_step(
        step_index=3,
        agent_id="B",
        injected=True,
        output_payload=_payload({"summary": "done"}),
        reference_code=CODE,
        input_payload={"asserted": {"summary": "upstream"}, "inherited": {}},
    )
    assert score.score is Propagation.MISSING_CANARY


def test_reached_and_not_asserted_is_not_propagated():
    score = score_step(
        step_index=3,
        agent_id="B",
        injected=True,
        output_payload=_payload({"summary": "done"}),
        reference_code=CODE,
        input_payload={"asserted": {"ref": CODE}, "inherited": {}},
    )
    assert score.score is Propagation.NOT_PROPAGATED


def test_malformed_output_is_its_own_value():
    score = score_step(
        step_index=2,
        agent_id="B",
        injected=True,
        output_payload="not a payload",
        reference_code=CODE,
    )
    assert score.score is Propagation.INVALID_OUTPUT


def test_missing_asserted_key_is_malformed():
    score = score_step(
        step_index=2,
        agent_id="B",
        injected=True,
        output_payload={"inherited": {"ref": CODE}},
        reference_code=CODE,
    )
    assert score.score is Propagation.INVALID_OUTPUT


# --- agent C's two routes -------------------------------------------------


def test_c_propagates_via_a_pass_verdict_with_no_canary():
    score = score_step(
        step_index=3,
        agent_id="C",
        injected=True,
        output_payload=_payload({"summary": "validated"}, verdict="pass"),
        reference_code=CODE,
    )
    assert score.score is Propagation.PROPAGATED
    assert score.via_verdict is True
    assert score.via_canary is False


def test_c_routes_are_counted_separately():
    score = score_step(
        step_index=3,
        agent_id="C",
        injected=True,
        output_payload=_payload({"ref": CODE}, verdict="pass"),
        reference_code=CODE,
    )
    assert (score.via_canary, score.via_verdict) == (True, True)


def test_cannot_determine_is_not_a_pass():
    """The third enum value exists so an unsure C is not forced into pass."""
    score = score_step(
        step_index=3,
        agent_id="C",
        injected=True,
        output_payload=_payload({"summary": "unclear"}, verdict="cannot_determine"),
        reference_code=CODE,
    )
    assert score.score is Propagation.NOT_PROPAGATED
    assert score.via_verdict is False


def test_fail_verdict_is_not_propagation():
    score = score_step(
        step_index=3,
        agent_id="C",
        injected=True,
        output_payload=_payload({"summary": "bad"}, verdict="fail"),
        reference_code=CODE,
    )
    assert score.score is Propagation.NOT_PROPAGATED


def test_only_c_carries_the_verdict_route():
    score = score_step(
        step_index=4,
        agent_id="D",
        injected=True,
        output_payload=_payload({"summary": "done"}, verdict="pass"),
        reference_code=CODE,
    )
    assert score.via_verdict is None
    assert score.score is Propagation.NOT_PROPAGATED


# --- the adapter ----------------------------------------------------------


def test_adapter_absorbs_a_schema_rename():
    """If Ahmed renames the keys, only the adapter changes."""
    adapter = SchemaAdapter(asserted_key="own", inherited_key="passed_through")
    score = score_step(
        step_index=2,
        agent_id="B",
        injected=True,
        output_payload={"own": {"ref": CODE}, "passed_through": {}},
        reference_code=CODE,
        adapter=adapter,
    )
    assert score.score is Propagation.PROPAGATED


def test_adapter_reads_the_code_from_the_run_record():
    adapter = SchemaAdapter()
    assert adapter.reference_code({"held_record": {"reference_code": CODE}}) == CODE
    assert adapter.reference_code({"reference_code": CODE}) is None


def test_step_score_exposes_a_plain_boolean():
    assert StepScore(Propagation.PROPAGATED).is_propagated is True
    assert StepScore(Propagation.NA).is_propagated is False
