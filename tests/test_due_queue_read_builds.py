"""A read build of the due queue writes nothing, whoever calls it and whatever session it names.

A build that does not serve (a chart, the staged comparator's shadow, the simulator, the plan's prefetch on its
read-only attach) used to record the session's contrast-pair serving and end the session's committed probe
presentation: the first can stand for a serving the learner never got (serving rows are first-write-wins per item
and session), and the second fails a read-only attach, so the prefetch found nothing to start. Only the serving
build writes them.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

from learnloop.db.repositories import Repository
from learnloop.scheduling import staged_policy as sp
from learnloop.scheduling.controller_snapshot import Candidate
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue

from tests.due_queue_helpers import CLOCK, SESSION, build_rich_vault

ASSIGNED = "pi_svd_define_001"


def _withdraw_the_assigned_probe(repository):
    """Its item leaves the queue, so the session's committed presentation no longer has a place in it."""

    repository.upsert_practice_item_state(
        ASSIGNED, difficulty=5.0, stability=None, due_at=None, last_attempt_at=None, active=False, clock=CLOCK
    )


def test_a_read_build_with_a_session_records_no_contrast_pair_serving(tmp_path):
    vault, repository = build_rich_vault(tmp_path / "vault")

    queue = build_due_queue(vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION),
                            persist_explanations=False)

    assert {"pi_pair_first", "pi_pair_second"} <= {item.practice_item_id for item in queue}
    assert repository.contrast_pair_serving_rows() == []


def test_a_read_build_with_a_session_leaves_the_committed_presentation(tmp_path):
    vault, repository = build_rich_vault(tmp_path / "vault")
    _withdraw_the_assigned_probe(repository)
    committed = repository.active_probe_presentation_for_session(SESSION)

    queue = build_due_queue(vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION),
                            persist_explanations=False)

    assert ASSIGNED not in {item.practice_item_id for item in queue}
    assert repository.active_probe_presentation_for_session(SESSION) == committed


def test_the_serving_build_still_invalidates_a_presentation_with_no_place(tmp_path):
    vault, repository = build_rich_vault(tmp_path / "vault")
    _withdraw_the_assigned_probe(repository)

    build_due_queue(vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION))

    assert repository.active_probe_presentation_for_session(SESSION) is None
    assert len(repository.contrast_pair_serving_rows()) == 2


def test_the_plan_prefetch_builds_its_pool_on_the_read_only_attach(tmp_path, caplog):
    """The prefetch's own pool build (``plan_prefetch`` -> ``_env(prefetch=True)``), on its read-only attach."""

    from learnloop_sidecar.handlers.daily_plan import _env

    vault, repository = build_rich_vault(tmp_path / "vault")
    _withdraw_the_assigned_probe(repository)
    reader = Repository.attach(repository.sqlite_path, read_only=True)
    context = SimpleNamespace(request_origin=None, grading_provider_override=None)

    with caplog.at_level(logging.WARNING):
        pool = _env(context, vault, reader, SESSION, prefetch=True).eligible(30.0)

    assert {"pi_pair_first", "pi_pair_second"} <= {item.practice_item_id for item in pool}
    assert not [record for record in caplog.records if "contrast pair" in record.getMessage()]
    assert repository.active_probe_presentation_for_session(SESSION) is not None


def test_the_staged_comparator_records_no_serving(tmp_path):
    vault, repository = build_rich_vault(tmp_path / "vault")
    candidate = Candidate(candidate_ref="fits", active=True, purpose="practice", practice_mode="setup_only",
                          expected_minutes=3.0)

    result = sp.decide(vault, repository, SchedulerSession(session_id=SESSION), candidates=[candidate], clock=CLOCK)

    assert any(step["step"] == "comparator_logged" for step in result.trace["steps"])
    assert repository.contrast_pair_serving_rows() == []
