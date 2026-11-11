"""What other test files use from ``tests/test_ux_phase4_feedback.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock

from tests.helpers import create_basic_vault, seed_due_item


ITEM = "pi_svd_define_001"


@pytest.fixture()
def ctx(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    context = SidecarContext()
    context.load(paths.root)
    # Never a real grading provider: "manual" is a never-ready runtime.
    context.grading_provider_override = "manual"
    context.paths = paths
    return context


def _later(**delta) -> FrozenClock:
    """A clock ``delta`` after now (the ledger rows here are stamped now)."""

    from datetime import UTC, datetime

    return FrozenClock(datetime.now(UTC) + timedelta(**delta))


def _iso(clock: FrozenClock) -> str:
    from learnloop.clock import utc_now_iso

    return utc_now_iso(clock)


def _feedback_answer(ctx, *, then: FrozenClock) -> str:
    vault, repository = ctx.require_vault()
    return complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=ITEM, learner_answer_md="my answer", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
        clock=then,
    ).attempt_id


def _exposure(ctx, attempt_id: str, display_id: str, *, clock: FrozenClock) -> None:
    from learnloop.attempts.reveal_ledger import record_feedback_answer_display_reveal

    vault, repository = ctx.require_vault()
    record_feedback_answer_display_reveal(
        repository, attempt_id=attempt_id, practice_item_id=ITEM,
        learning_object_id=vault.practice_items[ITEM].learning_object_id,
        display_id=display_id, clock=clock,
    )


def _served_items(env) -> list[str]:
    import json

    with env.repository.connection() as connection:
        rows = connection.execute(
            "SELECT detail_json FROM attention_block_events WHERE kind = 'item_served' ORDER BY created_at, event_ordinal"
        ).fetchall()
    return [json.loads(row[0])["practice_item_id"] for row in rows]


def _administration_receipts(repository) -> int:
    with repository.connection() as connection:
        return int(connection.execute(
            "SELECT COUNT(*) FROM coldness_receipts WHERE stage = 'administration'"
        ).fetchone()[0])


def _due_cold_task(ctx, *, case_ref: str = "ep_detail") -> dict:
    _vault, repository = ctx.require_vault()
    return repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref=case_ref,
        not_before=_iso(_later(hours=-1)), expires_at=_iso(_later(days=30)), selected_item_id=ITEM,
        clock=_later(days=-1),
    )


def _one_item_plan(tmp_path, display_age: timedelta):
    from datetime import UTC, datetime

    from tests.daily_plan_fakes import MovableClock, make_env, scheduled, seed_due
    from tests.helpers import create_daily_plan_vault

    start = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_c": [("pi_cold", 1.0)]})
    clock = MovableClock(start)
    env = make_env(paths.root, [scheduled("pi_cold", "lo_c", priority=0.9, followup_kind="cold_retry")],
                   clock=clock, session_id="s_wait")
    seed_due(env.repository, "pi_cold", due=start - timedelta(days=2), last=start - timedelta(days=9))
    env.repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_wait",
        not_before=_iso(FrozenClock(start - timedelta(hours=1))), expires_at=_iso(FrozenClock(start + timedelta(days=30))),
        selected_item_id="pi_cold", clock=FrozenClock(start - timedelta(days=1)),
    )
    env.repository.insert_reveal_event(
        {"practice_item_id": "pi_cold", "learning_object_id": "lo_c", "source_kind": "answer_display",
         "amount": 1.0, "basis": "feedback_full_answer:desktop:display_wait"},
        clock=FrozenClock(start - display_age),
    )
    return env, clock
