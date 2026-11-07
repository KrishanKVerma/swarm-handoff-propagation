"""Adjudication, intervals, and the rules that stop a number being wrong."""

from __future__ import annotations

import math

import pytest

from analysis.adjudicate import adjudicate_claim, adjudicate_evaluation
from analysis.stats import Rate, flip_rate, geometric_prediction, wilson

RECORD = {"record_id": "R-7", "reference_code": "K3M9QX7ZP2WD", "values": [1, 2]}
EMPTY = {"exists": True, "bytes": 2, "content": "{}", "parsed": {}}
MISSING = {"exists": False, "bytes": 0, "content": None, "parsed": None}
WRITTEN = {"exists": True, "bytes": 60, "content": "...", "parsed": RECORD}


def _check(**kwargs):
    row = {"evaluation_id": "e1", "status": "completed", "flag": True,
           "claim": None, "field": None}
    row.update(kwargs)
    return row


# --- claims against actual state -----------------------------------------


def test_empty_file_makes_two_claims_true():
    assert adjudicate_claim("artifact_empty", None, EMPTY, RECORD) is True
    assert adjudicate_claim("artifact_mismatch", None, EMPTY, RECORD) is True
    assert adjudicate_claim("artifact_missing", None, EMPTY, RECORD) is False


def test_missing_file():
    assert adjudicate_claim("artifact_missing", None, MISSING, RECORD) is True


def test_written_file_makes_them_all_false():
    for claim in ("artifact_missing", "artifact_empty", "artifact_mismatch"):
        assert adjudicate_claim(claim, None, WRITTEN, RECORD) is False


def test_field_mismatch_needs_a_real_field():
    assert adjudicate_claim("field_mismatch", "record_id", EMPTY, RECORD) is True
    assert adjudicate_claim("field_mismatch", "nonexistent", EMPTY, RECORD) is False


def test_unreadable_oracle_is_not_adjudicable():
    assert adjudicate_claim("artifact_empty", None, {"error": "OSError"}, RECORD) is None


# --- the three pins of amendment 10 --------------------------------------


def test_overlapping_true_claims_are_one_detection():
    """Both artifact_empty and artifact_mismatch are true; one detection each way."""
    for claim in ("artifact_empty", "artifact_mismatch"):
        result = adjudicate_evaluation(_check(claim=claim), EMPTY, RECORD)
        assert result.detection is True
    # Two evaluations each claiming one true thing are two rows, but a single
    # evaluation never contributes more than one detection.
    single = adjudicate_evaluation(_check(claim="artifact_empty"), EMPTY, RECORD)
    assert single.detection is True and single.false_positive is False


def test_no_discrepancy_with_a_flag_is_invalid_output():
    result = adjudicate_evaluation(_check(claim="no_discrepancy"), EMPTY, RECORD)
    assert result.status == "INVALID_OUTPUT"
    assert result.detection is None


def test_flag_with_no_claim_is_invalid_output():
    assert adjudicate_evaluation(_check(claim=None), EMPTY, RECORD).status == "INVALID_OUTPUT"


def test_false_positive_is_the_same_machinery():
    """Clean cell: flag true, every claim false."""
    result = adjudicate_evaluation(_check(claim="artifact_empty"), WRITTEN, RECORD)
    assert result.false_positive is True
    assert result.detection is False


def test_uncertain_is_flagged_but_not_detection():
    result = adjudicate_evaluation(_check(claim="uncertain"), EMPTY, RECORD)
    assert result.status == "adjudicated"
    assert result.detection is False


def test_other_is_not_adjudicated_and_counted_separately():
    result = adjudicate_evaluation(_check(claim="other", note="odd"), EMPTY, RECORD)
    assert result.status == "not_adjudicated"
    assert result.detection is None


def test_no_flag_is_not_a_detection_and_not_a_false_positive():
    result = adjudicate_evaluation(_check(flag=False, claim="no_discrepancy"), EMPTY, RECORD)
    assert (result.detection, result.false_positive) == (False, False)


def test_incomplete_evaluation_is_not_adjudicated():
    result = adjudicate_evaluation(_check(status="api_failure"), EMPTY, RECORD)
    assert result.status == "not_adjudicated"


# --- intervals and bounds -------------------------------------------------


def test_wilson_matches_known_values():
    low, high = wilson(2, 10)
    assert math.isclose(low, 0.05668, abs_tol=5e-4)
    assert math.isclose(high, 0.51014, abs_tol=5e-4)


def test_zero_snaps_to_zero_and_keeps_an_upper_bound():
    rate = Rate(0, 40)
    assert rate.interval[0] == 0.0
    assert math.isclose(rate.upper_bound_one_sided_95, 1 - 0.05 ** (1 / 40), rel_tol=1e-12)
    assert "upper bound" in rate.render()


def test_a_rate_with_no_denominator_is_refused():
    with pytest.raises(ValueError):
        wilson(0, 0)


def test_render_always_carries_the_denominator():
    assert "3 of 20" in Rate(3, 20).render()


def test_geometric_prediction():
    assert math.isclose(geometric_prediction(0.2), 1 - 0.8 ** 3)


# --- the instrument check -------------------------------------------------


def test_flip_rate_counts_opportunities_not_evaluations():
    groups = [[True, True, True], [True, False, True], [False, False, False]]
    flips = flip_rate(groups)
    assert (flips.flipped, flips.inputs) == (1, 3)


def test_single_repeat_groups_are_not_counted():
    assert flip_rate([[True], [False]]).inputs == 0


# --- a projection with nothing behind it refuses to answer ---------------


def test_projection_refuses_without_measurements():
    import sys
    sys.path.insert(0, "scripts")
    from run_pilot import _project

    out = _project({"end_monitor": [0, 0], "per_handoff": [0]}, 2)
    assert out["pilot_tokens_estimate"] is None
    assert out["fits_in_one_day"] is None
    assert "not an estimate of zero" in out["note"]


def test_projection_reports_what_it_measured():
    import sys
    sys.path.insert(0, "scripts")
    from run_pilot import _project

    out = _project({"end_monitor": [1000, 2000], "per_handoff": [4000]}, 2)
    assert out["end_monitor"]["runs_measured"] == 2
    assert out["pilot_tokens_estimate"] == 55000
    assert out["fits_in_one_day"] is True
