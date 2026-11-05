#!/usr/bin/env python3
"""Run meaningful fixture tests, generate examples, and replay their counts."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

if __name__ == "__main__":
    tests = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    if tests.countTestCases() == 0:
        raise SystemExit("No tests discovered")
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if not result.wasSuccessful():
        raise SystemExit(1)
    from swarm_handoff.cli import main
    raise SystemExit(main(["demo", *sys.argv[1:]]))
