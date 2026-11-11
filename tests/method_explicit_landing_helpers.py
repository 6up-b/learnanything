"""What other test files use from ``tests/test_method_explicit_landing.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.vault.models import RequiredMethod
from learnloop.vault.required_method import required_method_instruction


METHOD = "singular value decomposition"
SENTENCE = required_method_instruction(METHOD)
LONG = "Let A be the 2 by 2 matrix with rows (3, 0) and (4, 5). " * 12


def _graded_under_method(env, attempt_id: str, item_id: str, *, prompt: str, method: str | None) -> str:
    """Grade ``attempt_id`` under a pinned contract that showed ``prompt`` and froze ``method``."""

    from learnloop.learner.assessment_contracts import snapshot_for_presentation
    from tests.router_card_helpers import LAST
    from tests.daily_plan_fakes import iso

    update = {"prompt": prompt}
    if method is not None:
        update["required_method"] = RequiredMethod(name=method, criterion_ids=["correctness"])
    item = env.vault.practice_items[item_id].model_copy(update=update)
    version_id = snapshot_for_presentation(env.repository, env.vault, item)
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id, grading_revision) VALUES (?, ?, 'correctness', 4, 1, ?, ?, 0)",
            (f"ge_{attempt_id}", attempt_id, iso(LAST), version_id),
        )
        connection.commit()
    return version_id


def _graded_attempt_under(repository, vault, *, attempt_id: str, prompt: str, method: str | None) -> None:
    from learnloop.learner.assessment_contracts import snapshot_for_presentation
    from tests.helpers import NOW_ISO
    from tests.reader_cues_helpers import _attempt

    _attempt(repository, attempt_id=attempt_id, answer="SVD is the eigendecomposition.")
    update = {"prompt": prompt}
    if method is not None:
        update["required_method"] = RequiredMethod(name=method, criterion_ids=["correctness"])
    item = vault.practice_items["pi_svd_define_001"].model_copy(update=update)
    version_id = snapshot_for_presentation(repository, vault, item)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id, grading_revision) VALUES (?, ?, 'correctness', 1, 1, ?, ?, 0)",
            (f"ge_{attempt_id}", attempt_id, NOW_ISO, version_id),
        )
        connection.commit()
