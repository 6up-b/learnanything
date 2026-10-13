"""EVSI calibration composed with router R1 (migrations 181 and 184 on main).

R1's ``router_decisions`` / ``router_outcomes`` exist on every migrated vault,
so the calibration report's router adapter reads the real tables, not a stand-in.
A probe forecast logged beside a Today offer joins the attempt R1 binds to that
offer. R1's other verdicts on that offer (``superseded`` by a queue refresh
that kept the presentation in front, ``open`` in a cache rebuilt before the
answer) describe the offer, not the presentation, so they never hide the
attempt the presentation's own binding names: the ledgers decide.

An explored probe (R1 at mvp-0.15 admits probe near-ties to the seeded
exploration) carries the R1 review F4 marker on its presentation; its forecast
records the same marker, so the receipt never presents a drawn check as the
EIG choice.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop import clock as clock_module
from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
from learnloop.db.stores import voi_forecasts as store
from learnloop.evsi_calibration import live_report as LR
from learnloop.ids import new_ulid
from learnloop.scheduling import scheduler as scheduler_module
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW
from tests.test_router_probe_ties import _probe_vault


@pytest.fixture
def ticking_clock(monkeypatch):
    """The system clock, one second further on each read (ordered ids and times)."""

    state = {"now": NOW + timedelta(hours=1)}

    def now(_self):
        state["now"] = state["now"] + timedelta(seconds=1)
        return state["now"]

    monkeypatch.setattr(clock_module.SystemClock, "now", now)
    return state


def _context(root):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    context = SidecarContext()
    context.load(root)
    context.grading_provider_override = "manual"
    return context


def _today(ctx, session_id: str) -> None:
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY["get_today_queue"]
    spec.handler(ctx, spec.params_model.model_validate({"sessionId": session_id}))


def _probe_forecasts(repository) -> list[dict]:
    with repository.connection() as connection:
        return [row for row in store.list_forecasts(connection) if row["site"] == "probe_selection"]


def _offers(repository) -> list[dict]:
    with repository.connection() as connection:
        return [
            dict(row)
            for row in connection.execute(
                "SELECT id, decision_kind, chosen_practice_item_id, chosen_scheduler_candidate_id "
                "FROM router_decisions WHERE decision_kind = 'today_offer' ORDER BY created_at, id"
            )
        ]


def _cached_status(repository, decision_id: str) -> str | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT action_status FROM router_outcomes WHERE decision_id = ?", (decision_id,)
        ).fetchone()
    return None if row is None else str(row["action_status"])


def _rebuild(paths, repository) -> None:
    """R1's outcome cache is DERIVED: its one replayer runs with every rebuild."""

    rebuild_all_derived_state(load_vault(paths.root), repository)


def _answer(vault, repository, presentation, *, session_id: str, candidate_id: str) -> str:
    """Answer the presentation through the offer ``candidate_id`` (as the desktop binds it)."""

    if presentation.served_at is None:
        repository.mark_probe_presentation_served(presentation.id)
    attempt_id = new_ulid()
    apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=presentation.practice_item_id,
                learner_answer_md="answer",
                attempt_type="diagnostic_probe",
                probe_presentation_id=presentation.id,
                session_id=session_id,
                scheduler_candidate_id=candidate_id,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=4,
                criterion_points={"correctness": 4.0},
                evidence_rows=[],
                error_attributions=[],
                grader_confidence=1.0,
                confidence=4,
                manual_review_reason=None,
            ),
            grading_source="ai",
        ),
    )
    return attempt_id


def _offered_probe(tmp_path):
    """A mvp-0.15 vault whose first Today offer commits a probe presentation."""

    paths, _vault, repository = _probe_vault(tmp_path, "mvp-0.15")
    ctx = _context(paths.root)
    session_id = repository.create_session(
        energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None
    )
    _today(ctx, session_id)
    presentation = repository.active_probe_presentation_for_session(session_id)
    assert presentation is not None and presentation.scheduler_candidate_id
    [forecast] = _probe_forecasts(repository)
    assert forecast["presentation_id"] == presentation.id
    assert forecast["scheduler_candidate_id"] == presentation.scheduler_candidate_id
    [offer] = _offers(repository)
    assert offer["chosen_scheduler_candidate_id"] == presentation.scheduler_candidate_id
    return paths, load_vault(paths.root), repository, ctx, session_id, presentation, offer


def _probe_site(vault) -> dict:
    report = LR.calibration_report(vault)
    assert report["outcome_adapter"] == "router_outcomes then ledgers"
    return report["sites"]["probe_selection"]


def test_a_probe_forecast_joins_the_attempt_r1_binds_to_its_offer(tmp_path, ticking_clock):
    paths, vault, repository, _ctx, session_id, presentation, offer = _offered_probe(tmp_path)
    _answer(vault, repository, presentation, session_id=session_id,
            candidate_id=presentation.scheduler_candidate_id)
    _rebuild(paths, repository)
    assert _cached_status(repository, offer["id"]) == "taken"

    site = _probe_site(vault)
    assert site["forecasts"] == 1
    assert site["adapters"] == {"router_outcomes": 1}
    assert site["join_status"] == {"realized": 1}


def test_an_offer_superseded_by_a_refresh_never_hides_the_presentations_answer(tmp_path, ticking_clock):
    paths, vault, repository, ctx, session_id, presentation, first = _offered_probe(tmp_path)
    # The queue refreshes: a new offer keeps the committed presentation in
    # front under a new scheduler candidate, and the learner answers that one.
    _today(ctx, session_id)
    second = _offers(repository)[-1]
    assert second["id"] != first["id"]
    assert second["chosen_practice_item_id"] == presentation.practice_item_id
    assert second["chosen_scheduler_candidate_id"] != presentation.scheduler_candidate_id
    _answer(vault, repository, presentation, session_id=session_id,
            candidate_id=second["chosen_scheduler_candidate_id"])
    _rebuild(paths, repository)
    # R1 is right about the offer the forecast names: it was superseded.
    assert _cached_status(repository, first["id"]) == "superseded"
    assert _cached_status(repository, second["id"]) == "taken"

    # The presentation was answered all the same: its forecast is realized.
    site = _probe_site(vault)
    assert site["adapters"] == {"ledgers": 1}
    assert site["join_status"] == {"realized": 1}


def test_a_stale_router_cache_never_hides_the_presentations_answer(tmp_path, ticking_clock):
    paths, vault, repository, _ctx, session_id, presentation, offer = _offered_probe(tmp_path)
    # The cache is rebuilt while the offer is open, then the learner answers;
    # router_outcomes is rebuilt only by `learnloop rebuild`, so it lags.
    _rebuild(paths, repository)
    assert _cached_status(repository, offer["id"]) == "open"
    _answer(vault, repository, presentation, session_id=session_id,
            candidate_id=presentation.scheduler_candidate_id)
    assert _cached_status(repository, offer["id"]) == "open"

    site = _probe_site(vault)
    assert site["adapters"] == {"ledgers": 1}
    assert site["join_status"] == {"realized": 1}


def test_an_explored_probes_forecast_says_the_scheduler_drew_it(tmp_path, ticking_clock, monkeypatch):
    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.15")
    session_id = repository.create_session(
        energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None
    )
    # The draw lands on the runner-up probe (R1's own F4 test setup).
    monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, **_k: (0.0, 0.0))
    queue = build_due_queue(vault, repository, session=SchedulerSession(session_id=session_id))
    assert queue[0].components.get("exploration_selected") == 1.0
    presentation = repository.active_probe_presentation_for_session(session_id)
    marker = presentation.selection_components["scheduler_exploration"]
    assert marker["mechanism"] == "scheduler_seeded_exploration"

    [forecast] = _probe_forecasts(repository)
    assert forecast["presentation_id"] == presentation.id
    assert forecast["forecast"]["selection"]["scheduler_exploration"] == marker


def test_a_probe_the_eig_chose_records_no_draw(tmp_path, ticking_clock, monkeypatch):
    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.15")
    session_id = repository.create_session(
        energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None
    )
    monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, **_k: (1.0, 0.0))
    build_due_queue(vault, repository, session=SchedulerSession(session_id=session_id))
    presentation = repository.active_probe_presentation_for_session(session_id)
    assert "scheduler_exploration" not in presentation.selection_components

    [forecast] = _probe_forecasts(repository)
    assert "scheduler_exploration" not in forecast["forecast"]["selection"]
