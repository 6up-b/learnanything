"""Read the two Eedi releases the calibration harness uses (no network here).

* **Eedi 2024** ("Mining Misconceptions in Mathematics", Kaggle): 1,869
  four-option questions, each wrong option labelled with the misconception it
  diagnoses (or unlabelled). It has no student responses. This is the
  *question bank and hypothesis space* of the simulation.
* **Eedi NeurIPS 2020** (the Education Challenge public data): 15.9M answers
  (task 1/2) and 1.4M answers (task 3/4) to four-option diagnostic questions,
  with the chosen option, the correct option and the answer time. It has no
  misconception labels. This is what the *response model* is fitted to.

The two releases share Eedi's subject taxonomy (``SubjectId`` 33 is
"BIDMAS" in both), which is how a 2024 question inherits the response
parameters fitted on 2020 questions of the same level-3 subject.

The owner downloads both: 2024 needs a Kaggle login; 2020 is the challenge's
public archive. Neither is committed or redistributed (licences: Kaggle
competition rules; the NeurIPS 2020 challenge terms, arXiv:2007.12061). Only
aggregate fitted statistics leave this module.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

OPTIONS = ("A", "B", "C", "D")
#: 2020 answers are 1..4 for A..D.
_OPTION_INDEX = {"A": 1, "B": 2, "C": 3, "D": 4}

# Cache layout version: bump when the arrays saved beside the raw files change.
_CACHE_VERSION = 1


@dataclass(frozen=True)
class EediQuestion:
    """One 2024 question with its distractor labels."""

    question_id: str
    subject_id: int
    subject_name: str
    construct_id: int
    construct_name: str
    correct: str
    #: Option letter -> misconception id, for the labelled wrong options only.
    misconception_by_option: Mapping[str, str]

    @property
    def distractors(self) -> tuple[str, ...]:
        return tuple(option for option in OPTIONS if option != self.correct)

    def options_for(self, misconception_id: str) -> tuple[str, ...]:
        return tuple(
            option
            for option, label in sorted(self.misconception_by_option.items())
            if label == misconception_id
        )


@dataclass(frozen=True)
class EediBank:
    """The 2024 question bank: questions, misconception names, provenance."""

    questions: tuple[EediQuestion, ...]
    misconception_names: Mapping[str, str]
    manifest: Mapping[str, Any]
    source_hash: str

    def by_subject(self) -> dict[int, list[EediQuestion]]:
        grouped: dict[int, list[EediQuestion]] = {}
        for question in self.questions:
            grouped.setdefault(question.subject_id, []).append(question)
        return {subject: sorted(items, key=lambda q: q.question_id) for subject, items in grouped.items()}


def _read_manifest(directory: Path) -> dict[str, Any]:
    path = directory / "manifest.json"
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _file_hash(paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(str(path.stat().st_size).encode("utf-8"))
        with path.open("rb") as handle:
            digest.update(handle.read(1 << 20))  # first MiB: identity, not integrity
    return digest.hexdigest()[:16]


def _misconception_id(raw: Any) -> str | None:
    text = str(raw or "").strip()
    if not text or text.lower() == "nan":
        return None
    try:
        return str(int(float(text)))
    except ValueError:
        return text


def load_eedi_2024(directory: Path) -> EediBank:
    """Read ``train.csv`` and ``misconception_mapping.csv`` from ``directory``."""

    directory = Path(directory)
    mapping_path, train_path = directory / "misconception_mapping.csv", directory / "train.csv"
    for path in (mapping_path, train_path):
        if not path.is_file():
            raise ValueError(
                f"{path.name} is missing: download Eedi 'Mining Misconceptions in Mathematics' "
                f"(Kaggle, login required) into {directory}"
            )
    with mapping_path.open(encoding="utf-8", newline="") as handle:
        names = {
            str(row["MisconceptionId"]).strip(): str(row["MisconceptionName"]).strip()
            for row in csv.DictReader(handle)
            if str(row.get("MisconceptionId") or "").strip()
        }
    questions: list[EediQuestion] = []
    with train_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            correct = str(row.get("CorrectAnswer") or "").strip()
            if correct not in OPTIONS:
                continue
            labels: dict[str, str] = {}
            for option in OPTIONS:
                if option == correct:
                    continue
                misconception = _misconception_id(row.get(f"Misconception{option}Id"))
                if misconception is not None and misconception in names:
                    labels[option] = misconception
            questions.append(
                EediQuestion(
                    question_id=str(row.get("QuestionId") or "").strip(),
                    subject_id=int(float(row.get("SubjectId") or -1)),
                    subject_name=str(row.get("SubjectName") or "").strip(),
                    construct_id=int(float(row.get("ConstructId") or -1)),
                    construct_name=str(row.get("ConstructName") or "").strip(),
                    correct=correct,
                    misconception_by_option=labels,
                )
            )
    questions.sort(key=lambda q: (q.subject_id, q.question_id))
    return EediBank(
        questions=tuple(questions),
        misconception_names=names,
        manifest=_read_manifest(directory),
        source_hash=_file_hash([mapping_path, train_path]),
    )


# -- NeurIPS 2020 ----------------------------------------------------------------------------


@dataclass
class NeuripsResponses:
    """Answer arrays of one 2020 task, aligned by row (one row per answer)."""

    task: str
    question: np.ndarray  # int32
    user: np.ndarray  # int32
    answer_id: np.ndarray  # int64
    correct_option: np.ndarray  # int8, 1..4
    answer: np.ndarray  # int8, 1..4
    #: Question -> its deepest (level-3) subject, the unit the fit stratifies on.
    leaf_subject: dict[int, int]
    subject_names: dict[int, str]
    source_hash: str
    #: Minutes since the epoch per row, when the answer metadata was loaded.
    answered_minute: np.ndarray | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def rows(self) -> int:
        return int(self.question.shape[0])


def _subjects(directory: Path) -> tuple[dict[int, int], dict[int, str]]:
    levels: dict[int, int] = {}
    names: dict[int, str] = {}
    with (directory / "data" / "metadata" / "subject_metadata.csv").open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            subject = int(row["SubjectId"])
            levels[subject] = int(row["Level"])
            names[subject] = str(row["Name"]).strip()
    return levels, names


def _leaf_subjects(directory: Path, task: str, levels: Mapping[int, int]) -> dict[int, int]:
    leaf: dict[int, int] = {}
    path = directory / "data" / "metadata" / f"question_metadata_task_{task}.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            subjects = json.loads(row["SubjectId"])
            level3 = [int(value) for value in subjects if levels.get(int(value)) == 3]
            if level3:
                # A question tagged with two level-3 subjects is filed under the
                # last (deepest-listed) one; Eedi lists the path root -> leaf.
                leaf[int(row["QuestionId"])] = level3[-1]
    return leaf


def _parse_answers(path: Path) -> dict[str, np.ndarray]:
    questions: list[int] = []
    users: list[int] = []
    answer_ids: list[int] = []
    correct: list[int] = []
    answers: list[int] = []
    with path.open(encoding="utf-8") as handle:
        header = handle.readline().strip().split(",")
        index = {name: i for i, name in enumerate(header)}
        qi, ui, ai, ci, vi = (index[n] for n in ("QuestionId", "UserId", "AnswerId", "CorrectAnswer", "AnswerValue"))
        for line in handle:
            parts = line.rstrip("\n").split(",")
            questions.append(int(parts[qi]))
            users.append(int(parts[ui]))
            answer_ids.append(int(parts[ai]))
            correct.append(int(parts[ci]))
            answers.append(int(parts[vi]))
    return {
        "question": np.asarray(questions, dtype=np.int32),
        "user": np.asarray(users, dtype=np.int32),
        "answer_id": np.asarray(answer_ids, dtype=np.int64),
        "correct_option": np.asarray(correct, dtype=np.int8),
        "answer": np.asarray(answers, dtype=np.int8),
    }


def _parse_dates(path: Path, answer_ids: np.ndarray) -> np.ndarray:
    """Minutes since the epoch for each of ``answer_ids`` (-1 when unknown)."""

    ids: list[int] = []
    stamps: list[str] = []
    with path.open(encoding="utf-8") as handle:
        header = handle.readline().strip().split(",")
        index = {name: i for i, name in enumerate(header)}
        ai, di = index["AnswerId"], index["DateAnswered"]
        width = max(ai, di) + 1
        for line in handle:
            parts = line.split(",", width)
            stamp = parts[di][:16]
            if len(stamp) != 16:
                continue
            try:
                ids.append(int(float(parts[ai])))
            except ValueError:
                continue
            stamps.append(stamp)
    known_ids = np.asarray(ids, dtype=np.int64)
    known_minutes = np.asarray(stamps, dtype="U16").astype("datetime64[m]").astype(np.int64)
    order = np.argsort(known_ids, kind="stable")
    known_ids, known_minutes = known_ids[order], known_minutes[order]
    position = np.searchsorted(known_ids, answer_ids)
    position = np.clip(position, 0, max(known_ids.size - 1, 0))
    found = known_ids.size > 0
    out = np.full(answer_ids.shape[0], -1, dtype=np.int64)
    if found:
        hit = known_ids[position] == answer_ids
        out[hit] = known_minutes[position[hit]]
    return out


def load_neurips_2020(
    directory: Path,
    *,
    task: str = "1_2",
    cache_dir: Path | None = None,
    with_dates: bool = False,
) -> NeuripsResponses:
    """Load one 2020 task's answers (cached as ``.npz`` in ``cache_dir``)."""

    if task not in ("1_2", "3_4"):
        raise ValueError("task must be 1_2 or 3_4")
    directory = Path(directory)
    train = directory / "data" / "train_data" / f"train_task_{task}.csv"
    if not train.is_file():
        raise ValueError(
            f"{train} is missing: extract the Eedi NeurIPS 2020 public archive (data.zip) into {directory}"
        )
    levels, names = _subjects(directory)
    leaf = _leaf_subjects(directory, task, levels)
    source_hash = _file_hash([train])
    cache = None
    if cache_dir is not None:
        cache = Path(cache_dir) / f"neurips2020_task{task}_v{_CACHE_VERSION}_{source_hash}.npz"
    arrays: dict[str, np.ndarray]
    if cache is not None and cache.is_file():
        with np.load(cache) as loaded:
            arrays = {key: loaded[key] for key in loaded.files}
    else:
        arrays = _parse_answers(train)
        if cache is not None:
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, **arrays)
    responses = NeuripsResponses(
        task=task,
        question=arrays["question"],
        user=arrays["user"],
        answer_id=arrays["answer_id"],
        correct_option=arrays["correct_option"],
        answer=arrays["answer"],
        leaf_subject=leaf,
        subject_names=names,
        source_hash=source_hash,
    )
    if with_dates:
        if "answered_minute" in arrays:
            responses.answered_minute = arrays["answered_minute"]
        else:
            metadata = directory / "data" / "metadata" / f"answer_metadata_task_{task}.csv"
            if metadata.is_file():
                minutes = _parse_dates(metadata, responses.answer_id)
                responses.answered_minute = minutes
                if cache is not None:
                    np.savez(cache, **arrays, answered_minute=minutes)
            else:
                responses.notes.append(f"{metadata.name} missing: persistence not estimated")
    return responses


def option_index(option: str) -> int:
    return _OPTION_INDEX[option]
