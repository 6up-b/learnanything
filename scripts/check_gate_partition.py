"""Check that the landing gate and the arc-close gate together run the whole suite, once each (refactor step A6).

The landing gate runs ``-m "not arc_close"`` and the arc-close gate ``-m arc_close``.
This collects the suite three ways (everything, each gate) and checks:

- the two gates are disjoint, and their union is every collected test;
- the arc-close gate isn't empty (a renamed marker would empty it silently);
- every ``arc_close`` test is also ``slow`` (``tests/conftest.py`` adds the mark),
  so ``-m "not slow"`` while iterating leaves the arc-close tests out too.

Collection only: nothing runs, so it takes about a minute. Run it under the memory
cap and the empty-home wrapper, from the repository root:

    uv run python scripts/check_gate_partition.py [--json out.json]

Exit 0 when every check holds; 1 with the offending node ids otherwise.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANES = {
    "all": [],
    "landing": ["-m", "not arc_close"],
    "arc_close": ["-m", "arc_close"],
    "arc_close_not_slow": ["-m", "arc_close and not slow"],
}


def collect(marker_args: list[str]) -> set[str]:
    """The node ids pytest collects from ``tests`` with these ``-m`` arguments."""

    cmd = [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q", "-p", "no:cacheprovider", *marker_args]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    # Exit 5 is "no tests collected", the expected answer for the arc_close-and-not-slow lane.
    if out.returncode not in (0, 5):
        raise SystemExit(f"collection failed ({out.returncode}): {' '.join(cmd)}\n{out.stdout[-2000:]}{out.stderr[-2000:]}")
    return {line.strip() for line in out.stdout.splitlines() if "::" in line and not line.startswith(" ")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--json", type=Path, help="write the counts and any offending node ids here")
    args = parser.parse_args(argv)
    found = {name: collect(marker_args) for name, marker_args in LANES.items()}
    every, landing, arc = found["all"], found["landing"], found["arc_close"]
    problems = {
        "in_both_gates": sorted(landing & arc),
        "in_neither_gate": sorted(every - (landing | arc)),
        "in_a_gate_but_not_collected": sorted((landing | arc) - every),
        "arc_close_not_slow": sorted(found["arc_close_not_slow"]),
    }
    if not arc:
        problems["arc_close_empty"] = ["no test carries the arc_close marker"]
    report = {"counts": {name: len(ids) for name, ids in found.items()},
              "problems": {key: value for key, value in problems.items() if value}}
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    counts = report["counts"]
    print(f"collected {counts['all']}: landing {counts['landing']} + arc_close {counts['arc_close']}")
    for key, ids in report["problems"].items():
        print(f"{key}: {len(ids)}", *ids[:20], sep="\n  ")
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
