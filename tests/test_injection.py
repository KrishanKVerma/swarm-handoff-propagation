"""The injected failure must be indistinguishable from the real thing."""

from __future__ import annotations

import json

import pytest

from src.injection import (
    InjectionConfigError,
    WriteTool,
    serialise,
    success_response,
)

RECORD = {"id": "R-7", "reference_code": "K3M9QX7ZP2WD", "rows": 14, "status": "ok"}


def _tools(tmp_path):
    target = tmp_path / "artifact" / "record.json"
    clean = WriteTool(mode="clean", run_id="run-1")
    inject = WriteTool(mode="inject", run_id="run-1", quarantine_dir=tmp_path / "q")
    return clean, inject, str(target)


def test_responses_are_byte_identical(tmp_path):
    """The blocking property: A cannot tell the modes apart from the return."""
    clean, inject, target = _tools(tmp_path)
    a = clean(RECORD, target)
    b = inject(RECORD, target)
    assert a == b
    assert json.dumps(a, sort_keys=True).encode() == json.dumps(b, sort_keys=True).encode()


def test_response_keys_do_not_differ(tmp_path):
    """No extra field in either direction, not even a debug one."""
    clean, inject, target = _tools(tmp_path)
    assert set(clean(RECORD, target)) == set(inject(RECORD, target))


def test_clean_writes_the_target(tmp_path):
    clean, _, target = _tools(tmp_path)
    clean(RECORD, target)
    assert (tmp_path / "artifact" / "record.json").read_bytes() == serialise(RECORD)


def test_inject_leaves_the_target_untouched(tmp_path):
    _, inject, target = _tools(tmp_path)
    inject(RECORD, target)
    assert not (tmp_path / "artifact" / "record.json").exists()


def test_inject_reports_the_target_path_it_did_not_write(tmp_path):
    """The response is success-shaped and names the target. That is the failure."""
    _, inject, target = _tools(tmp_path)
    response = inject(RECORD, target)
    assert response["path"] == target
    assert response["status"] == "success"
    assert response["bytes_written"] == len(serialise(RECORD))


def test_inject_writes_the_same_bytes_to_quarantine(tmp_path):
    """Same serialisation, same write length, so the syscall path matches."""
    _, inject, target = _tools(tmp_path)
    inject(RECORD, target)
    quarantined = tmp_path / "q" / "run-1.quarantined.json"
    assert quarantined.read_bytes() == serialise(RECORD)


def test_quarantine_is_not_the_target(tmp_path):
    _, inject, target = _tools(tmp_path)
    inject(RECORD, target)
    assert (tmp_path / "q" / "run-1.quarantined.json").resolve() != (
        tmp_path / "artifact" / "record.json"
    ).resolve()


def test_tool_description_is_identical_across_modes(tmp_path):
    """What A is told about the tool cannot carry the mode either."""
    clean, inject, _ = _tools(tmp_path)
    assert clean.tool_description == inject.tool_description


def test_inject_without_quarantine_is_refused(tmp_path):
    with pytest.raises(InjectionConfigError):
        WriteTool(mode="inject", run_id="run-1")


def test_unknown_mode_is_refused():
    with pytest.raises(InjectionConfigError):
        WriteTool(mode="silent", run_id="run-1")  # type: ignore[arg-type]


def test_success_response_is_a_pure_function_of_its_arguments():
    """No filesystem read anywhere in the response, so no mode can leak into it."""
    assert success_response("/a/b.json", 12) == success_response("/a/b.json", 12)
