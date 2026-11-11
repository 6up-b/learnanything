"""What other test files use from ``tests/test_evsi_multisim.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import csv

from tests.evsi_calibration_sim_helpers import SUBJECT, write_eedi_2024


def _write_long_bank(directory, questions: int):
    """The synthetic 2024 bank's label patterns repeated: one subject with
    ``questions`` questions (more than the old 25-check bound)."""

    write_eedi_2024(directory)
    labels = [
        ("A", {"B": 10, "C": 11}), ("B", {"A": 10, "D": 12}), ("C", {"A": 11, "B": 12}),
        ("D", {"A": 10}), ("A", {"C": 11, "D": 12}), ("B", {"C": 10}), ("C", {"D": 11}), ("D", {"B": 12}),
    ]
    with (directory / "train.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["QuestionId", "ConstructId", "ConstructName", "SubjectId", "SubjectName", "CorrectAnswer",
                         "QuestionText", "AnswerAText", "AnswerBText", "AnswerCText", "AnswerDText",
                         "MisconceptionAId", "MisconceptionBId", "MisconceptionCId", "MisconceptionDId"])
        for index in range(questions):
            correct, mis = labels[index % len(labels)]
            writer.writerow([index, 100 + index, "Order of operations", SUBJECT, "BIDMAS", correct, f"Q{index}",
                             "a", "b", "c", "d"] + [f"{float(mis[o]):.1f}" if o in mis else "" for o in "ABCD"])
    return directory
