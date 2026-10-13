"""Eedi 2020 answers arranged for the simulator families (stage ``evsi-multisim``).

Every family in :mod:`.family_fit` is fitted to the *same* students on the
*same* misconception triples the single-family study found
(:mod:`.response_fit`): three questions whose designated distractors the same
students pick together far more than chance. Triples were selected on even
``UserId``s; the families are fitted and validated on odd ones only:

* **fit split**: odd ``UserId`` with ``UserId % 8 != 7`` (three quarters);
* **held-out split**: ``UserId % 8 == 7`` (one quarter), never seen by a fit.

Two shapes:

* :class:`TripleData`: per triple, the students who answered all three
  questions, their options (1..4) and answer minutes. The latent class, the
  nominal-response and the learning (latent transition) families fit here, and
  every family is scored on the held-out students of these triples.
* :class:`SubjectData`: per level-3 subject, the subject's triple questions as
  one item set (the triples are disjoint inside a subject), every fit-split
  student who answered at least two of them (missing answers allowed). The
  cognitive diagnosis family fits here, so one learner's skill is shared
  across the subject's misconceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from learnloop.evsi_calibration.eedi import NeuripsResponses
from learnloop.evsi_calibration.response_fit import CORRECT, DESIGNATED, OTHER, TripleFit

#: Consecutive encounters at most this many minutes apart are one session.
SESSION_GAP_MINUTES = 60
#: Gap types of the learning family's transitions.
GAP_SAME_SESSION, GAP_LATER = 0, 1
HELD_OUT_MODULUS, HELD_OUT_RESIDUE = 8, 7


def is_held_out(users: np.ndarray) -> np.ndarray:
    return (users % HELD_OUT_MODULUS) == HELD_OUT_RESIDUE


def is_fit(users: np.ndarray) -> np.ndarray:
    return ((users % 2) == 1) & ~is_held_out(users)


@dataclass(frozen=True)
class TripleData:
    """One misconception triple's answers (odd ``UserId``s only)."""

    index: int
    subject_id: int
    questions: tuple[int, int, int]
    correct: tuple[int, int, int]  # option 1..4 per item
    designated: tuple[int, int, int]  # option 1..4 per item
    users: np.ndarray  # (n,)
    options: np.ndarray  # (n, 3) int8, 1..4
    minutes: np.ndarray  # (n, 3) int64, -1 when unknown

    def split(self, held_out: bool) -> "TripleData":
        mask = is_held_out(self.users) if held_out else is_fit(self.users)
        return TripleData(self.index, self.subject_id, self.questions, self.correct, self.designated,
                          self.users[mask], self.options[mask], self.minutes[mask])

    @property
    def n(self) -> int:
        return int(self.users.shape[0])

    def categories(self) -> np.ndarray:
        """(n, 3) answer categories: CORRECT, DESIGNATED or OTHER."""

        correct = np.asarray(self.correct)[None, :]
        designated = np.asarray(self.designated)[None, :]
        out = np.full(self.options.shape, OTHER, dtype=np.int64)
        out[self.options == designated] = DESIGNATED
        out[self.options == correct] = CORRECT
        return out

    def role_options(self) -> np.ndarray:
        """(n, 3) answers in role space: 0 correct, 1 designated, 2/3 the other
        two distractors in option-letter order."""

        out = np.zeros(self.options.shape, dtype=np.int64)
        for item in range(3):
            roles = item_roles(self.correct[item], self.designated[item])
            lookup = np.zeros(5, dtype=np.int64)
            for option, role in roles.items():
                lookup[option] = role
            out[:, item] = lookup[self.options[:, item]]
        return out

    def time_order(self) -> tuple[np.ndarray, np.ndarray]:
        """Per student, the items in answer order and the two gap types.

        Ties (same minute, or unknown times) keep the item order. Returns
        ``order`` (n, 3) item indices and ``gaps`` (n, 2) of
        ``GAP_SAME_SESSION`` / ``GAP_LATER``.
        """

        minutes = np.where(self.minutes >= 0, self.minutes, 0)
        order = np.argsort(minutes, axis=1, kind="stable")
        ordered = np.take_along_axis(minutes, order, axis=1)
        gaps = np.where(np.diff(ordered, axis=1) <= SESSION_GAP_MINUTES, GAP_SAME_SESSION, GAP_LATER)
        unknown = (self.minutes < 0).any(axis=1)
        gaps[unknown] = GAP_SAME_SESSION
        return order, gaps.astype(np.int64)


def item_roles(correct: int, designated: int) -> dict[int, int]:
    """Option (1..4) -> role: 0 correct, 1 designated, 2/3 other in letter order."""

    roles = {correct: 0, designated: 1}
    others = [o for o in (1, 2, 3, 4) if o not in roles]
    for position, option in enumerate(others):
        roles[option] = 2 + position
    return roles


@dataclass(frozen=True)
class SubjectData:
    """A subject's triple items as one test (fit split, missing allowed)."""

    subject_id: int
    triple_indices: tuple[int, ...]
    #: Per item: the triple position inside the subject (its misconception attribute).
    attribute: np.ndarray  # (J,)
    correct: np.ndarray  # (J,)
    designated: np.ndarray  # (J,)
    questions: np.ndarray  # (J,)
    users: np.ndarray  # (n,)
    options: np.ndarray  # (n, J) int8, 0 = not answered

    @property
    def items(self) -> int:
        return int(self.questions.shape[0])

    @property
    def attributes(self) -> int:
        return len(self.triple_indices)


def _first_answers(responses: NeuripsResponses, questions: Sequence[int]) -> dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """question -> (users sorted, option, minute) over odd users, first answer each."""

    wanted = np.asarray(sorted(set(int(q) for q in questions)), dtype=np.int64)
    mask = np.isin(responses.question, wanted) & ((responses.user % 2) == 1)
    question = responses.question[mask].astype(np.int64)
    user = responses.user[mask].astype(np.int64)
    answer = responses.answer[mask].astype(np.int8)
    minute = (
        responses.answered_minute[mask].astype(np.int64)
        if responses.answered_minute is not None
        else np.full(question.shape[0], -1, dtype=np.int64)
    )
    order = np.lexsort((user, question))
    question, user, answer, minute = question[order], user[order], answer[order], minute[order]
    out: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    starts = np.flatnonzero(np.r_[True, question[1:] != question[:-1]])
    ends = np.r_[starts[1:], question.shape[0]]
    for start, end in zip(starts.tolist(), ends.tolist()):
        users = user[start:end]
        keep = np.r_[True, users[1:] != users[:-1]]
        out[int(question[start])] = (users[keep], answer[start:end][keep], minute[start:end][keep])
    return out


def build_triple_data(responses: NeuripsResponses, triples: Sequence[TripleFit]) -> list[TripleData]:
    """The answers of every triple's three questions, odd users only."""

    answers = _first_answers(responses, [q for t in triples for q in t.questions])
    correct_of = _correct_options(responses, [q for t in triples for q in t.questions])
    out: list[TripleData] = []
    for index, triple in enumerate(triples):
        parts = [answers.get(int(q)) for q in triple.questions]
        if any(p is None for p in parts):
            continue
        common = parts[0][0]
        for p in parts[1:]:
            common = np.intersect1d(common, p[0], assume_unique=True)
        options = np.zeros((common.shape[0], 3), dtype=np.int8)
        minutes = np.zeros((common.shape[0], 3), dtype=np.int64)
        for item, (users, option, minute) in enumerate(parts):
            position = np.searchsorted(users, common)
            options[:, item] = option[position]
            minutes[:, item] = minute[position]
        out.append(
            TripleData(
                index=index,
                subject_id=int(triple.subject_id),
                questions=tuple(int(q) for q in triple.questions),  # type: ignore[arg-type]
                correct=tuple(int(correct_of[int(q)]) for q in triple.questions),  # type: ignore[arg-type]
                designated=tuple(int(d) for d in triple.designated),  # type: ignore[arg-type]
                users=common,
                options=options,
                minutes=minutes,
            )
        )
    return out


def _correct_options(responses: NeuripsResponses, questions: Sequence[int]) -> dict[int, int]:
    wanted = np.asarray(sorted(set(int(q) for q in questions)), dtype=np.int64)
    mask = np.isin(responses.question, wanted)
    question = responses.question[mask]
    correct = responses.correct_option[mask]
    unique, first = np.unique(question, return_index=True)
    return {int(q): int(correct[i]) for q, i in zip(unique.tolist(), first.tolist())}


def build_subject_data(
    responses: NeuripsResponses,
    triples: Sequence[TripleData],
    *,
    min_answered: int = 2,
) -> list[SubjectData]:
    """Per subject, its triples' items as one test over the fit split."""

    grouped: dict[int, list[TripleData]] = {}
    for triple in triples:
        grouped.setdefault(triple.subject_id, []).append(triple)
    questions = [q for t in triples for q in t.questions]
    answers = _first_answers(responses, questions)
    out: list[SubjectData] = []
    for subject, members in sorted(grouped.items()):
        members = sorted(members, key=lambda t: t.index)
        item_questions, attribute, correct, designated = [], [], [], []
        for position, triple in enumerate(members):
            for item in range(3):
                item_questions.append(triple.questions[item])
                attribute.append(position)
                correct.append(triple.correct[item])
                designated.append(triple.designated[item])
        user_sets = [answers[q][0] for q in item_questions if q in answers]
        if not user_sets:
            continue
        users = np.unique(np.concatenate(user_sets))
        users = users[is_fit(users)]
        options = np.zeros((users.shape[0], len(item_questions)), dtype=np.int8)
        for j, question in enumerate(item_questions):
            if question not in answers:
                continue
            q_users, q_options, _ = answers[question]
            position = np.searchsorted(q_users, users)
            position = np.clip(position, 0, max(q_users.shape[0] - 1, 0))
            hit = q_users[position] == users
            options[hit, j] = q_options[position[hit]]
        answered = (options > 0).sum(axis=1)
        keep = answered >= min_answered
        out.append(
            SubjectData(
                subject_id=subject,
                triple_indices=tuple(t.index for t in members),
                attribute=np.asarray(attribute, dtype=np.int64),
                correct=np.asarray(correct, dtype=np.int64),
                designated=np.asarray(designated, dtype=np.int64),
                questions=np.asarray(item_questions, dtype=np.int64),
                users=users[keep],
                options=options[keep],
            )
        )
    return out


def category_counts(table: np.ndarray) -> Mapping[tuple[int, int, int], int]:
    """(n, 3) categories -> {(c1, c2, c3): count} for the latent class EM."""

    keys, counts = np.unique(table, axis=0, return_counts=True)
    return {(int(k[0]), int(k[1]), int(k[2])): int(c) for k, c in zip(keys, counts)}


__all__ = [
    "CORRECT",
    "DESIGNATED",
    "OTHER",
    "GAP_LATER",
    "GAP_SAME_SESSION",
    "SESSION_GAP_MINUTES",
    "SubjectData",
    "TripleData",
    "build_subject_data",
    "build_triple_data",
    "category_counts",
    "is_fit",
    "is_held_out",
    "item_roles",
]
