#!/usr/bin/env python3
"""Regenerate every generated reference note: the module, desktop and db generators, in turn.

Each generator records its own commit in Reference/_generated.md (generated_provenance.py),
so running one alone is fine too; this is the one command for "regenerate the references".
Stops at the first generator that fails.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from generated_provenance import GENERATORS  # noqa: E402


def main() -> int:
    for script, _notes in GENERATORS:
        print(f"== {script}", flush=True)
        result = subprocess.run([sys.executable, str(SCRIPTS / script)], check=False)
        if result.returncode:
            print(f"{script} failed ({result.returncode}); the generators after it did not run", file=sys.stderr)
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
