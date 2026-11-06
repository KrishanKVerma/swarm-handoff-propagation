"""The oracle is deterministic, runner-only, and cannot reach a prompt."""

from __future__ import annotations

import json
import textwrap

import pytest

from src.oracle import Oracle, OracleAccessError, OracleLeakError

RECORD = {"id": "R-7", "reference_code": "K3M9QX7ZP2WD", "rows": 14}


def _oracle(tmp_path, content=None):
    path = tmp_path / "record.json"
    if content is not None:
        path.write_text(json.dumps(content))
    return Oracle(path=path)


def test_match_on_a_written_file(tmp_path):
    verdict = _oracle(tmp_path, RECORD).check(claim=RECORD, step=2)
    assert verdict.matches is True


def test_mismatch_when_the_file_was_never_written(tmp_path):
    """The injected case: the chain claims the record, the file has nothing."""
    verdict = _oracle(tmp_path).check(claim=RECORD, step=2)
    assert verdict.matches is False
    assert verdict.file_state["exists"] is False


def test_mismatch_on_different_content(tmp_path):
    verdict = _oracle(tmp_path, {"id": "R-8"}).check(claim=RECORD, step=2)
    assert verdict.matches is False


def test_key_order_does_not_decide_the_verdict(tmp_path):
    reordered = dict(reversed(list(RECORD.items())))
    assert _oracle(tmp_path, RECORD).check(claim=reordered, step=3).matches is True


def test_deterministic_across_repeats(tmp_path):
    oracle = _oracle(tmp_path, RECORD)
    verdicts = [oracle.check(claim=RECORD, step=2).matches for _ in range(5)]
    assert verdicts == [True] * 5


def test_path_is_bound_at_construction(tmp_path):
    """check() takes no path, so no caller can redirect the oracle mid-run."""
    import inspect

    assert "path" not in inspect.signature(Oracle.check).parameters


def test_verdict_cannot_be_stringified(tmp_path):
    verdict = _oracle(tmp_path, RECORD).check(claim=RECORD, step=2)
    with pytest.raises(OracleLeakError):
        str(verdict)


def test_verdict_cannot_be_f_stringed(tmp_path):
    """The realistic leak: a prompt builder interpolating the verdict."""
    verdict = _oracle(tmp_path, RECORD).check(claim=RECORD, step=2)
    with pytest.raises(OracleLeakError):
        f"the oracle says {verdict}"


def test_verdict_is_not_truthy_by_accident(tmp_path):
    """`if verdict:` must fail rather than silently read as True."""
    verdict = _oracle(tmp_path).check(claim=RECORD, step=2)
    with pytest.raises(OracleLeakError):
        bool(verdict)


def test_verdict_cannot_be_unpacked(tmp_path):
    verdict = _oracle(tmp_path, RECORD).check(claim=RECORD, step=2)
    with pytest.raises(OracleLeakError):
        list(verdict)


def test_to_trace_carries_the_fields_the_runner_writes(tmp_path):
    row = _oracle(tmp_path, RECORD).check(claim=RECORD, step=4).to_trace()
    assert row["oracle_truth"] is True
    assert row["step_index"] == 4


def test_a_checker_side_module_cannot_call_the_oracle(tmp_path, monkeypatch):
    """§3 enforced structurally: a frame that looks checker-side is refused."""
    namespace: dict[str, object] = {"__name__": "src.verifier_scratch"}
    source = textwrap.dedent(
        """
        from src.oracle import Oracle
        def run(path, claim):
            return Oracle(path=path).check(claim=claim, step=2)
        """
    )
    exec(compile(source, "verifier_scratch.py", "exec"), namespace)
    with pytest.raises(OracleAccessError):
        namespace["run"](tmp_path / "record.json", RECORD)  # type: ignore[operator]


def test_an_agent_side_module_cannot_call_the_oracle(tmp_path):
    namespace: dict[str, object] = {"__name__": "src.agent_b"}
    source = "from src.oracle import Oracle\ndef run(p, c):\n    return Oracle(path=p).check(claim=c, step=2)\n"
    exec(compile(source, "agent_b.py", "exec"), namespace)
    with pytest.raises(OracleAccessError):
        namespace["run"](tmp_path / "record.json", RECORD)  # type: ignore[operator]
