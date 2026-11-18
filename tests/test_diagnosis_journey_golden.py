"""Every persisted row of synthetic diagnosis journeys, including decision records."""
from __future__ import annotations

import os
import json
import fcntl
from pathlib import Path

import pytest

from tests.diagnosis_journey_helpers import CASES, recorded_twice
from tests.figure_build_golden_helpers import check_golden

GOLDEN = Path(__file__).parent / "fixtures" / "diagnosis_journey_golden.json"
WRITE = os.environ.get("DIAGNOSIS_JOURNEY_WRITE_GOLDEN") == "1"
pytestmark = pytest.mark.slow


@pytest.mark.parametrize("case", CASES)
def test_diagnosis_journey(case, tmp_path):
    recorded = recorded_twice(case, tmp_path)
    if WRITE:
        # Keep the lock on the rewritten file so parallel writers cannot lose
        # a case. Newlines without indentation keep this all-table golden small.
        with GOLDEN.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            handle.seek(0)
            text = handle.read()
            golden = json.loads(text) if text.strip() else {}
            golden[case] = recorded
            handle.seek(0)
            handle.truncate()
            handle.write(json.dumps(golden, indent=0, sort_keys=True, ensure_ascii=False) + "\n")
    check_golden(GOLDEN, case, recorded, write=False)
