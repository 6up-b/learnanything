"""Interaction signals as placement routes them (field §3.1, live with F2).

Help before starting, confusion questions (tutor or reader) and suspected
answer leaks on an LO mean it is taught first and never fast-tracked on early
answers. The derivation and the blocking rule are the field's own
(``field.signals``), shared with report 2, so live routing and the simulation
cannot drift apart. Signals never write evidence (G13): this module only reads.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from learnloop.field.signals import blocks_fast_track, load_interaction_signals
from learnloop.field.types import AttemptRow, ItemFeatures
from learnloop.placement.rules import AnswerFacts


def _attempt_rows(answers_by_lo: Mapping[str, Iterable[AnswerFacts]]) -> list[AttemptRow]:
    rows = []
    for answers in answers_by_lo.values():
        for answer in answers:
            outcome = 0.0 if answer.dont_know or answer.correctness is None else float(answer.correctness)
            rows.append(AttemptRow(
                attempt_id=answer.attempt_id,
                features=ItemFeatures(
                    item_id=answer.practice_item_id, lo_id=answer.learning_object_id,
                    observed_at=answer.created_at, primed=answer.primed,
                ),
                outcome=max(0.0, min(1.0, outcome)),
                effective_mass=1.0,
                hints_used=answer.hints_used,
            ))
    rows.sort(key=lambda row: (row.observed_at, row.attempt_id))
    return rows


def blocking_signals_by_lo(
    connection: Any,
    vault: Any,
    answers_by_lo: Mapping[str, Iterable[AnswerFacts]],
) -> dict[str, tuple[str, ...]]:
    """Signal ids, per LO, that keep it out of fast-track (sorted, stable)."""

    signals = load_interaction_signals(connection, vault, _attempt_rows(answers_by_lo))
    blocking: dict[str, set[str]] = defaultdict(set)
    for signal in signals:
        if blocks_fast_track(signal):
            blocking[signal.lo_id].add(signal.signal_id)
    return {lo: tuple(sorted(ids)) for lo, ids in blocking.items()}


def taught_first_learning_objects(vault: Any, repository: Any, learning_object_ids: Iterable[str]) -> set[str]:
    """Of these LOs, those with help or confusion signals: taught first."""

    from learnloop.placement.state import load_answers

    wanted = set(learning_object_ids)
    if not wanted:
        return set()
    with repository.connection() as connection:
        blocking = blocking_signals_by_lo(connection, vault, load_answers(connection))
    return {lo for lo in wanted if blocking.get(lo)}
