"""What other test files use from ``tests/test_teacher_te1b_landing_r2.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.vault.loader import load_vault

from tests.teacher_te1b_suggestions_helpers import _clock


def _today(vault, repository, clock):
    return SG.today_suggestion(vault, repository, clock=clock)


def _start(paths, repository, response="accepted", **kwargs):
    card = _today(load_vault(paths.root), repository, _clock())
    started = SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response=response,
                         clock=_clock(hours=1), **kwargs)
    return card, started["lesson"]


def _without(paths, learning_object_ids):
    """The vault as loaded now, with the reserved LOs gone (edited out of the vault's content)."""

    vault = load_vault(paths.root)
    for lo in learning_object_ids:
        del vault.learning_objects[lo]
    return vault
