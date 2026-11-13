"""What other test files use from ``tests/test_forecast_receipts.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, complete_attempt_with_ai_required
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.db.stores import forecast_receipts as receipt_store
from learnloop.evsi_calibration.forecast_report import resolved_receipts
from learnloop.scheduling import forecast_receipts as FR
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, at, drain_jobs, split_vault, submit


ITEM = "pi_svd_compute_001"
WRONG = "A = U Sigma V wrong"


def _present(repository: Repository, item: str, *, block: str, when) -> str:
    """One served plan item (router R2a's receipt), the presentation an answer binds to."""

    served = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
            "VALUES (?, 'practice', 10, 'hash', ?)",
            (block, served),
        )
        connection.execute(
            "INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
            "VALUES (?, ?, ?, 'chooser', ?)",
            (f"pp_{block}", block, item, served),
        )
        connection.commit()
    return f"pp_{block}"


def _answer(vault, repository, client, *, answer: str, when, presentation_id: str | None = None, **draft):
    """A graded attempt through the live door, bound to a plan presentation when given."""

    draft = AttemptDraft(
        practice_item_id=ITEM,
        learner_answer_md=answer,
        attempt_type="independent_attempt",
        plan_presentation_id=presentation_id,
        **draft,
    )
    clock = FrozenClock(when)
    result = complete_attempt_with_ai_required(
        vault, repository, draft, runtime=ReadyRuntime(), ai_client=client, clock=clock
    )
    run_post_attempt_pipeline(vault, repository, result=result, session_id=None, clock=clock)
    return result


def _receipts(repository: Repository, kind: str | None = None) -> list[dict]:
    with repository.connection() as connection:
        return receipt_store.list_receipts(connection, kind=kind)


def _diagnosed(tmp_path, *, version: str = LATEST_ALGORITHM_VERSION, config: str = "", method: bool = False):
    """A split vault with one wrong answer diagnosed (its forecast written).

    ``method``: the item is method-explicit (at the method-explicit
    successor), so a regrade reads and cites its assessment contract."""

    paths, vault, repository = split_vault(tmp_path, version=version, config=config)
    if method:
        from tests.required_method_grading_helpers import _require_method

        _require_method(paths)
        vault = load_vault(paths.root)
    client = ReviewFakeClient()
    diagnosed = submit(vault, repository, client, answer=WRONG, when=at(20))
    drain_jobs(vault, repository, client, clock=FrozenClock(at(20.5)))
    return paths, vault, repository, diagnosed


def _diagnosis_resolution(vault, attempt_id: str) -> dict:
    rows = [
        (receipt, resolution)
        for receipt, resolution in resolved_receipts(vault)
        if receipt["kind"] == FR.DIAGNOSIS_NEXT_OBSERVATION and receipt["source_attempt_id"] == attempt_id
    ]
    assert len(rows) == 1, rows
    return rows[0][1]
