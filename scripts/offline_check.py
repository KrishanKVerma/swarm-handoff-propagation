#!/usr/bin/env python3
"""Run meaningful fixture tests, generate examples, and replay their counts."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    try:
        import pytest
    except ImportError:
        raise SystemExit("Full repository checks require pytest. Install requirements-dev.txt in a local virtual environment.")
    result = pytest.main(["-q", str(ROOT / "tests")])
    if result != 0:
        raise SystemExit(result)
    from swarm_handoff.cli import main
    raise SystemExit(main(["demo", *sys.argv[1:]]))
