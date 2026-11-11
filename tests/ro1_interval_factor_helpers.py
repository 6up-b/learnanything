"""What other test files use from ``tests/test_ro1_interval_factor.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_placement_vault


#: (item, points): a hard item answered right (positive surprise, factor > 1) and an easy one answered
#: badly (negative surprise, factor < 1), then the hard one again a few days later.
HISTORY = (("pi_eig_hard", 4, 0), ("pi_eig_easy", 1, 0), ("pi_eig_hard", 4, 3))


def _vault(tmp_path, version: str, toml: str | None = None):
    paths = create_placement_vault(tmp_path, version=version, placement_toml=toml)
    return paths, Repository(paths.sqlite_path)


def _play(paths, repository):
    """The history, returning per attempt (attempt id, item, observed_at, state, surprise row)."""

    out = []
    for index, (item_id, points, day) in enumerate(HISTORY):
        observed = NOW + timedelta(days=day, minutes=index)
        result = complete_self_graded_attempt(
            load_vault(paths.root),
            repository,
            AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer."),
            SelfGradeInput(criterion_points={"correctness": points}, confidence=4),
            clock=FrozenClock(observed),
        )
        state = repository.practice_item_state(item_id)
        out.append((result.attempt_id, item_id, observed, state, repository.latest_attempt_surprise(result.attempt_id)))
    return out


def _due(observed, days: float) -> str:
    return (observed + timedelta(days=days)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
