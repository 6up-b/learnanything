"""What other test files use from ``tests/test_evsi_calibration_sim.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from learnloop.evsi_calibration.eedi import OPTIONS


SUBJECT = 33
#: Planted truth of the synthetic 2020 answers.
PLANTED_CONSISTENCY = 0.65


def write_eedi_2024(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "manifest.json").write_text(json.dumps({"sources": [
        {"name": "synthetic Eedi 2024", "version": "test", "licence": "test fixture"}]}))
    with (directory / "misconception_mapping.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["MisconceptionId", "MisconceptionName"])
        for mid, name in ((10, "adds before multiplying"), (11, "works left to right"), (12, "ignores brackets")):
            writer.writerow([mid, name])
    header = ["QuestionId", "ConstructId", "ConstructName", "SubjectId", "SubjectName", "CorrectAnswer",
              "QuestionText", "AnswerAText", "AnswerBText", "AnswerCText", "AnswerDText",
              "MisconceptionAId", "MisconceptionBId", "MisconceptionCId", "MisconceptionDId"]
    labels = [
        ("A", {"B": 10, "C": 11}), ("B", {"A": 10, "D": 12}), ("C", {"A": 11, "B": 12}),
        ("D", {"A": 10}), ("A", {"C": 11, "D": 12}), ("B", {"C": 10}), ("C", {"D": 11}), ("D", {"B": 12}),
    ]
    with (directory / "train.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for index, (correct, mis) in enumerate(labels):
            row = [index, 100 + index, "Order of operations", SUBJECT, "BIDMAS", correct, f"Q{index}",
                   "a", "b", "c", "d"]
            row += [f"{float(mis[o]):.1f}" if o in mis else "" for o in OPTIONS]
            writer.writerow(row)
    return directory


def write_eedi_2020(directory: Path, *, students: int = 6000, seed: int = 7) -> Path:
    """Six questions in one level-3 subject; two planted misconception triples."""

    meta = directory / "data" / "metadata"
    train = directory / "data" / "train_data"
    meta.mkdir(parents=True, exist_ok=True)
    train.mkdir(parents=True, exist_ok=True)
    with (meta / "subject_metadata.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["SubjectId", "Name", "ParentId", "Level"])
        writer.writerows([[3, "Maths", "NULL", 0], [32, "Number", 3, 1], [144, "Operations", 32, 2],
                          [SUBJECT, "BIDMAS", 144, 3]])
    correct = {q: 1 + (q % 4) for q in range(6)}
    designated = {q: 1 + ((q + 1) % 4) for q in range(6)}  # never the correct option
    with (meta / "question_metadata_task_3_4.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["QuestionId", "SubjectId"])
        for q in range(6):
            writer.writerow([q, f"[3, 32, 144, {SUBJECT}]"])
    rng = np.random.default_rng(seed)
    rows, dates = [], []
    answer_id = 0
    for user in range(students):
        cls = rng.choice(["knows", "mx", "my", "unsure"], p=[0.6, 0.15, 0.1, 0.15])
        for q in range(6):
            targeted = (cls == "mx" and q < 3) or (cls == "my" and q >= 3)
            if cls == "knows":
                probs = (0.9, 0.03, 0.07)
            elif targeted:
                probs = (0.2, PLANTED_CONSISTENCY, 0.15)
            else:
                probs = (0.35, 0.15, 0.5)
            category = rng.choice(3, p=probs)
            others = [o for o in range(1, 5) if o not in (correct[q], designated[q])]
            value = correct[q] if category == 0 else (designated[q] if category == 1 else int(rng.choice(others)))
            rows.append((q, user, answer_id, int(value == correct[q]), correct[q], value))
            dates.append((answer_id, f"2020-01-{1 + q:02d} 10:{user % 60:02d}:00.000"))
            answer_id += 1
    with (train / "train_task_3_4.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["QuestionId", "UserId", "AnswerId", "IsCorrect", "CorrectAnswer", "AnswerValue"])
        writer.writerows(rows)
    with (meta / "answer_metadata_task_3_4.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["AnswerId", "DateAnswered", "Confidence", "GroupId", "QuizId", "SchemeOfWorkId"])
        for aid, stamp in dates:
            writer.writerow([f"{aid}.0", stamp, "", 1, 1, ""])
    return directory
