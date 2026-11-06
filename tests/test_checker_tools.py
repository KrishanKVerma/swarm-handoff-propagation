"""The checker's read tool is not the oracle, and its use is recorded."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.checker_tools import CheckerReadTool

RECORD = {"id": "R-7", "reference_code": "K3M9QX7ZP2WD"}


def _tool(tmp_path, opportunity="1->2", content=None):
    path = tmp_path / "record.json"
    if content is not None:
        path.write_text(json.dumps(content))
    return CheckerReadTool(
        path=path, run_id="run-1", checker_id="verifier-1", opportunity=opportunity
    )


def test_returns_raw_contents(tmp_path):
    tool = _tool(tmp_path, content=RECORD)
    result = tool()
    assert result["exists"] is True
    assert json.loads(result["contents"]) == RECORD


def test_reports_a_missing_file_without_judging_it(tmp_path):
    """The injected case. The tool says what it saw and nothing more."""
    result = _tool(tmp_path)()
    assert result["exists"] is False
    assert result["contents"] is None
    assert set(result) == {"path", "exists", "contents"}


def test_no_verdict_no_expectation_in_the_return(tmp_path):
    """Nothing in the payload tells the checker what it should have found."""
    result = _tool(tmp_path, content=RECORD)()
    for leaked in ("expected", "oracle", "matches", "should", "verdict", "mismatch"):
        assert leaked not in result


def test_called_read_is_false_until_used(tmp_path):
    tool = _tool(tmp_path, content=RECORD)
    assert tool.called_read is False
    tool()
    assert tool.called_read is True


def test_read_count_tracks_repeats(tmp_path):
    tool = _tool(tmp_path, content=RECORD)
    tool()
    tool()
    assert tool.read_count == 2


def test_flag_log_row_has_the_fields_p_needs(tmp_path):
    """§7 estimates p per opportunity; the row is its denominator."""
    tool = _tool(tmp_path, opportunity="2->3", content=RECORD)
    row = tool.flag_log_row(verdict="no_mismatch", verdict_text="file matches claim")
    assert row["called_read"] is False
    assert row["opportunity"] == "2->3"
    assert row["run_id"] == "run-1"
    assert row["checker_id"] == "verifier-1"
    assert row["verdict"] == "no_mismatch"


def test_flag_log_row_records_a_checker_that_never_looked(tmp_path):
    """The case the secondary exists to measure."""
    row = _tool(tmp_path).flag_log_row(verdict="no_mismatch")
    assert row["called_read"] is False
    assert row["read_count"] == 0


def test_end_monitor_is_one_opportunity(tmp_path):
    row = _tool(tmp_path, opportunity="end", content=RECORD).flag_log_row()
    assert row["opportunity"] == "end"


def test_tool_description_carries_no_expectation(tmp_path):
    description = _tool(tmp_path).tool_description.lower()
    for leaked in ("expected", "should contain", "oracle", "mismatch", "verify that"):
        assert leaked not in description


def test_module_does_not_import_the_oracle():
    """Structural: the checker side cannot reach the oracle even by accident."""
    source = Path("src/checker_tools.py").read_text()
    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any("oracle" in name for name in imported)
