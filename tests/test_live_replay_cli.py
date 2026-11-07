"""Writer-to-replay integration, with scripted responses and no model API."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts.check_live_replay import run_probe


@pytest.fixture
def probe(tmp_path, monkeypatch):
    # The compatibility check must remain safe with real credentials present.
    def no_network(*args, **kwargs):
        raise AssertionError("Compatibility replay must not use the network")

    monkeypatch.setattr("urllib.request.urlopen", no_network)
    directory = tmp_path / "probe"
    return directory, run_probe(directory)


def _cli(tmp_path, *args):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT)))
    result = subprocess.run([sys.executable, "-m", "swarm_handoff.cli", *args],
                            cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_probe_preserves_writer_and_evidence_boundaries(probe):
    directory, receipt = probe
    assert receipt["bundles_written_and_replayed"] == 4
    assert receipt["checker_opportunities"] == 8
    assert receipt["checks"] == 16
    assert receipt["scripted_provider_calls"] == 40
    assert receipt["provider_api_calls"] == 0
    assert receipt["empirical_traces_verified"] == 0
    assert receipt["study_results_generated"] is False
    assert receipt["shared_analysis_equal"] is True
    for relative, digest in receipt["bundle_sha256"].items():
        assert hashlib.sha256((directory / relative).read_bytes()).hexdigest() == digest
    for trace in directory.glob("*/trace.json"):
        bundle = json.loads(trace.read_text())
        assert bundle["schema_version"] == "live-0.2"
        assert bundle["evidence_kind"] == "live_model_run"
        assert bundle["provider_metadata"]["provider"] == "scripted"


def test_cli_discovers_live_writer_traces_without_manifests(probe, tmp_path):
    directory, _ = probe
    assert not list(directory.glob("*/manifest.json"))
    before = {path: path.read_bytes() for path in directory.rglob("*") if path.is_file()}
    summary = _cli(tmp_path, "summarize", "--input", str(directory))
    assert summary["shared_analysis"]["runs_total"] == 4
    assert len(summary["shared_analysis"]["cells"]) == 4
    for cell_name, cell in summary["shared_analysis"]["cells"].items():
        opportunities = 3 if "per_handoff" in cell_name else 1
        detections = opportunities if cell_name.startswith("inject_") else 0
        assert cell["p1_read_rate_repeat_zero"]["n"] == opportunities
        assert cell["p1_read_rate_repeat_zero"]["k"] == opportunities
        assert cell["detections_per_opportunity_repeat_zero"]["n"] == opportunities
        assert cell["detections_per_opportunity_repeat_zero"]["k"] == detections
    for run_dir in sorted(directory.iterdir()):
        audited = _cli(tmp_path, "audit", "--input", str(run_dir))
        assert audited["valid"] is True
        assert audited["run_id"] == run_dir.name
    assert {path: path.read_bytes() for path in before} == before


def test_probe_cli_runs_from_outside_checkout_and_refuses_overwrite(tmp_path):
    output = tmp_path / "retained"
    command = [sys.executable, str(ROOT / "scripts" / "check_live_replay.py"),
               "--output", str(output)]
    first = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    receipt = json.loads(first.stdout)
    assert receipt["bundles_retained"] is True
    assert json.loads((output / "compatibility-receipt.json").read_text()) == receipt
    before = {path: path.read_bytes() for path in output.rglob("*") if path.is_file()}
    second = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert second.returncode != 0
    assert "must be a new directory" in second.stderr
    assert {path: path.read_bytes() for path in before} == before
