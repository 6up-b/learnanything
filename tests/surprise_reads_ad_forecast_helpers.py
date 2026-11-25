"""What other test files use from ``tests/test_surprise_reads_ad_forecast.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``)."""

from __future__ import annotations

import json
from contextlib import closing

from learnloop.db.connection import connect


def _surprise(repository) -> dict[str, dict]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT attempt_id, predicted_score_dist_json, predictive_surprise, bayesian_surprise, surprise_direction,"
            " fsrs_interval_factor FROM attempt_surprise").fetchall()
    return {str(r[0]): {"dist": json.loads(r[1]), "predictive": r[2], "bayesian": r[3], "direction": r[4],
                        "factor": r[5]} for r in rows}
