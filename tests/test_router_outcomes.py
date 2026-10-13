"""Router R1: ``router_outcomes`` (DERIVED) joins R_next and R_cold per decision.

S = 0.75 R_cold + 0.25 R_next (the Pipeline plan's outcome). R_next is the
first fresh, unassisted, independent attempt on the decision's learning object
after the action; R_cold the next attempt at least a day after the last
exposure to that learning object (an attempt, or a reveal on it). Pending
outcomes are right-censored at the newest attempt, never failures. One
replayer rebuilds the table deterministically, with no model call.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import sqlite3

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.db.stores.router import ROUTER_LOG_VERSION, insert_router_decision
from learnloop.router.outcomes import S_ALPHA, derive_router_outcomes
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, add_followup_item, create_basic_vault, seed_due_item

T0 = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
LO = "lo_svd_definition"
A, B = "pi_svd_define_001", "pi_svd_define_002"


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _at(**delta) -> str:
    return _iso(T0 + timedelta(**delta))


@pytest.fixture
def repo(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return Repository(paths.sqlite_path)


def _decision(repo, decision_id: str, *, created_at: str, kind: str = "today_offer", session: str = "s1",
              item: str | None = A, candidate: str | None = "c1", parent: str | None = None) -> None:
    pick = kind == "learner_pick"
    row = {
        "id": decision_id, "receipt_key": f"{kind}:{decision_id}", "decision_kind": kind,
        "surface": "desktop_queue", "mode": "legacy_queue", "policy": "learner" if pick else "composed_offer_v2",
        "algorithm_version": "mvp-0.11", "log_version": ROUTER_LOG_VERSION, "session_id": session,
        "parent_decision_id": parent, "snapshot_hash": "h", "candidates_json": "[]", "exclusions_json": "{}",
        "candidate_count": 0, "chosen_ref": item or "stop_for_today", "chosen_practice_item_id": item,
        "chosen_learning_object_id": LO if item else None, "chosen_scheduler_candidate_id": candidate,
        "propensity": None if pick else 1.0, "propensity_kind": "none" if pick else "deterministic",
        "learner_pick": 1 if pick else 0, "detail_json": "{}", "created_at": created_at,
    }
    with repo.atomic(), repo.connection() as connection:
        insert_router_decision(connection, row)


def _attempt(repo, attempt_id: str, *, item: str, created_at: str, correctness: float, session: str = "s1",
             candidate: str | None = None, hints: int = 0, primed: int = 0,
             attempt_type: str = "independent_attempt", origin: str = "human") -> None:
    with repo.connection() as connection:
        connection.execute(
            """INSERT INTO practice_attempts(
                 id, practice_item_id, learning_object_id, practice_mode, attempt_type, hints_used,
                 correctness, manual_review, created_at, session_id, scheduler_candidate_id, primed,
                 evidence_origin)
               VALUES (?,?,?,?,?,?,?,0,?,?,?,?,?)""",
            (attempt_id, item, LO, "short_answer", attempt_type, hints, correctness, created_at, session,
             candidate, primed, origin),
        )
        connection.commit()


def _reveal(repo, reveal_id: str, *, item: str, created_at: str) -> None:
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, created_at)"
            " VALUES (?,?,?,?,?,?)",
            (reveal_id, item, LO, "tutor_answer", 1.0, created_at),
        )
        connection.commit()


def _outcomes(repo, pfc=None) -> dict[str, dict]:
    with repo.connection() as connection:
        return {row["decision_id"]: row for row in derive_router_outcomes(connection, pfc_states=pfc)}


def test_r_next_is_the_first_fresh_unassisted_attempt_after_the_action(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=0.5, candidate="c1")
    _attempt(repo, "a1", item=A, created_at=_at(minutes=2), correctness=1.0)            # same item: not fresh
    _attempt(repo, "a2", item=B, created_at=_at(minutes=3), correctness=1.0, hints=1)   # assisted
    _attempt(repo, "a3", item=B, created_at=_at(minutes=4), correctness=0.75)

    outcome = _outcomes(repo)["d1"]

    assert (outcome["action_status"], outcome["action_attempt_id"]) == ("taken", "a0")
    assert (outcome["r_next_status"], outcome["r_next_value"], outcome["r_next_attempt_id"]) == ("observed", 0.75, "a3")
    assert outcome["r_next_skipped"] == 2 and outcome["r_next_elapsed_seconds"] == 180
    # Everything happened within minutes: no cold retrieval yet.
    assert outcome["r_cold_status"] == "pending" and outcome["r_cold_value"] is None
    assert (outcome["s_status"], outcome["s_value"]) == ("provisional", 0.75)
    detail = json.loads(outcome["detail_json"])
    assert detail["r_next_skip_reasons"] == {"hinted": 1, "not_fresh_same_item": 1}
    assert detail["s_provisional_from"] == "r_next"


def test_r_cold_needs_a_day_since_the_last_exposure_including_reveals(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=0.5, candidate="c1")
    _attempt(repo, "a1", item=B, created_at=_at(minutes=5), correctness=1.0)                     # R_next
    _reveal(repo, "r1", item=A, created_at=_at(hours=36))
    _attempt(repo, "a2", item=A, created_at=_at(hours=48), correctness=1.0, session="s2")        # 12 h after a reveal
    _attempt(repo, "a3", item=A, created_at=_at(hours=96), correctness=0.0, session="s3")        # cold

    outcome = _outcomes(repo)["d1"]

    assert (outcome["r_next_value"], outcome["r_next_attempt_id"]) == (1.0, "a1")
    assert (outcome["r_cold_status"], outcome["r_cold_value"], outcome["r_cold_attempt_id"]) == ("observed", 0.0, "a3")
    assert outcome["r_cold_gap_seconds"] == 48 * 3600
    assert json.loads(outcome["detail_json"])["r_cold_skip_reasons"]["insufficient_delay"] == 2
    assert outcome["s_status"] == "final"
    assert outcome["s_value"] == pytest.approx(S_ALPHA * 0.0 + (1 - S_ALPHA) * 1.0)


def test_cold_needs_an_unassisted_independent_answer_in_another_session(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=0.5, candidate="c1")
    _attempt(repo, "a1", item=B, created_at=_at(days=2), correctness=1.0, session="s1")          # same session
    _attempt(repo, "a2", item=B, created_at=_at(days=4), correctness=1.0, session="s2", primed=1)
    _attempt(repo, "a3", item=B, created_at=_at(days=6), correctness=1.0, session="s3",
             attempt_type="self_report")
    _attempt(repo, "a4", item=B, created_at=_at(days=8), correctness=1.0, session="s4", origin="simulator")
    _attempt(repo, "a5", item=B, created_at=_at(days=10), correctness=0.5, session="s5")

    outcome = _outcomes(repo)["d1"]

    assert (outcome["r_cold_value"], outcome["r_cold_attempt_id"]) == (0.5, "a5")
    reasons = json.loads(outcome["detail_json"])["r_cold_skip_reasons"]
    assert {"same_session", "primed", "not_independent_type", "non_human_outcome"} <= set(reasons)


def test_a_nothing_assessed_answer_is_never_an_outcome(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=0.5, candidate="c1")
    _attempt(repo, "a1", item=B, created_at=_at(minutes=2), correctness=1.0)
    outcome = _outcomes(repo, pfc={"a1": "nothing_assessed"})["d1"]
    assert outcome["r_next_status"] == "pending"


def test_pending_outcomes_are_right_censored_never_failures(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=0.0, candidate="c1")
    outcome = _outcomes(repo)["d1"]
    assert outcome["action_status"] == "taken"
    assert (outcome["r_next_status"], outcome["r_cold_status"], outcome["s_status"]) == ("pending",) * 3
    assert outcome["r_next_value"] is None and outcome["s_value"] is None
    assert outcome["observed_through"] == _at(minutes=1)


def test_an_untaken_offer_is_open_superseded_or_overridden(repo):
    _decision(repo, "d1", created_at=_at(minutes=0), candidate="c1")
    _decision(repo, "d2", created_at=_at(minutes=1), candidate="c2")                   # supersedes d1
    _decision(repo, "pick", created_at=_at(minutes=2), kind="learner_pick", item=B, candidate="c3", parent="d2")
    _decision(repo, "d3", created_at=_at(minutes=3), candidate="c4", session="s9")     # latest of its session
    _decision(repo, "stop", created_at=_at(minutes=4), item=None, candidate=None, session="s8")
    _attempt(repo, "a0", item=B, created_at=_at(minutes=5), correctness=1.0, candidate="c3")

    outcomes = _outcomes(repo)

    assert outcomes["d1"]["action_status"] == "superseded"
    assert outcomes["d2"]["action_status"] == "overridden"
    assert outcomes["d3"]["action_status"] == "open" and outcomes["d3"]["s_status"] == "pending"
    assert outcomes["stop"]["action_status"] == "not_applicable"
    assert outcomes["d1"]["s_status"] == outcomes["d2"]["s_status"] == "not_applicable"
    # The learner pick's own outcome follows the candidate the learner took.
    assert (outcomes["pick"]["action_status"], outcomes["pick"]["action_attempt_id"]) == ("taken", "a0")


def test_a_staged_decision_is_taken_by_the_first_attempt_on_its_item_in_session(repo):
    _decision(repo, "d1", created_at=_at(minutes=10), kind="staged_p2", candidate=None)
    _attempt(repo, "early", item=A, created_at=_at(minutes=5), correctness=1.0)
    _attempt(repo, "other", item=A, created_at=_at(minutes=11), correctness=1.0, session="elsewhere")
    _attempt(repo, "a0", item=A, created_at=_at(minutes=12), correctness=1.0)
    assert _outcomes(repo)["d1"]["action_attempt_id"] == "a0"


# ── the replayer ─────────────────────────────────────────────────────────────


def test_the_replayer_rebuilds_router_outcomes_deterministically_with_no_model_call(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop.ai import client
    from learnloop.ai.providers import decider
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    def forbidden(*_args, **_kwargs):
        raise AssertionError("router outcomes replay must not construct a model client")

    monkeypatch.setattr(client, "make_ai_provider_client", forbidden)
    monkeypatch.setattr(client, "make_ai_provider_client_from_profile", forbidden)
    monkeypatch.setattr(decider.DeciderProviderClient, "__init__", forbidden)

    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    add_followup_item(paths.root, B)
    repository.upsert_practice_item_state(
        B, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=True,
    )
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=20, notes_md_path=None)
    spec = METHOD_REGISTRY["get_today_queue"]
    queue = spec.handler(ctx, spec.params_model.model_validate({"sessionId": session_id}))
    head = queue["sections"][0]["items"][0]
    vault = load_vault(paths.root)
    complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=head["practiceItemId"], learner_answer_md="An answer.", session_id=session_id,
                     scheduler_candidate_id=head["schedulerCandidateId"], evidence_origin="human"),
        SelfGradeInput(criterion_points={"correctness": 4.0}, confidence=4),
    )

    def table():
        with sqlite3.connect(paths.sqlite_path) as connection:
            return sorted(tuple(row) for row in connection.execute("SELECT * FROM router_outcomes"))

    rebuild_all_derived_state(vault, repository)
    first = table()
    rebuild_all_derived_state(vault, repository)
    assert table() == first and len(first) == 1
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM router_outcomes").fetchone()
    assert row["action_status"] == "taken" and row["outcome_version"] == "router_outcomes_v1"
    # The decision ledger is never touched by replay.
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM router_decisions").fetchone()[0] == 1


@pytest.mark.durability
def test_router_tables_survive_rebuild_under_production_pragmas(tmp_path):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = Repository(paths.sqlite_path)
    _decision(repository, "d1", created_at=_at(minutes=0))
    _attempt(repository, "a0", item=A, created_at=_at(minutes=1), correctness=0.5, candidate="c1")
    vault = load_vault(paths.root)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW), require_complete_attempt_coverage=False)
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM router_decisions").fetchone()[0] == 1
        assert connection.execute("SELECT action_status FROM router_outcomes").fetchone()[0] == "taken"
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


# ── Codex review F8: applicability, finalization, ended sessions ────────────


def test_r_next_is_not_applicable_on_a_single_item_learning_object_and_r_cold_finalizes_s(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=0.5, candidate="c1")
    _attempt(repo, "a1", item=A, created_at=_at(days=2), correctness=1.0, session="s2")       # cold

    with repo.connection() as connection:
        outcome = {
            row["decision_id"]: row
            for row in derive_router_outcomes(connection, servable_items_by_lo={LO: {A}})
        }["d1"]

    assert outcome["r_next_status"] == "not_applicable"
    assert json.loads(outcome["detail_json"])["r_next_not_applicable"] == "no_other_servable_item"
    assert (outcome["r_cold_status"], outcome["r_cold_value"]) == ("observed", 1.0)
    assert (outcome["s_status"], outcome["s_value"]) == ("final", 1.0)


def test_an_observed_cold_retrieval_finalizes_s_and_closes_r_next(repo):
    _decision(repo, "d1", created_at=_at(minutes=0))
    _attempt(repo, "a0", item=A, created_at=_at(minutes=1), correctness=0.5, candidate="c1")
    _attempt(repo, "a1", item=A, created_at=_at(days=2), correctness=0.0, session="s2")       # cold, same item
    _attempt(repo, "a2", item=B, created_at=_at(days=3), correctness=1.0, session="s3")       # after the cold one

    with repo.connection() as connection:
        outcome = {
            row["decision_id"]: row
            for row in derive_router_outcomes(connection, servable_items_by_lo={LO: {A, B}})
        }["d1"]

    # Only R_cold finalizes S; a "next" attempt after the cold retrieval is not
    # immediate uptake, so S is final at the cold attempt and never moves.
    assert (outcome["r_cold_status"], outcome["r_cold_attempt_id"]) == ("observed", "a1")
    assert outcome["r_next_status"] == "not_applicable" and outcome["r_next_value"] is None
    assert json.loads(outcome["detail_json"])["r_next_not_applicable"] == "closed_by_r_cold"
    assert (outcome["s_status"], outcome["s_value"]) == ("final", 0.0)


def test_an_untaken_offer_of_an_ended_session_is_not_taken(repo):
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO sessions(id, started_at, ended_at) VALUES ('s9', ?, ?)", (_at(minutes=-5), _at(minutes=30))
        )
        connection.execute("INSERT INTO sessions(id, started_at) VALUES ('s8', ?)", (_at(minutes=-5),))
        connection.commit()
    _decision(repo, "ended", created_at=_at(minutes=3), candidate="c4", session="s9")
    _decision(repo, "running", created_at=_at(minutes=3), candidate="c5", session="s8")

    outcomes = _outcomes(repo)

    assert outcomes["ended"]["action_status"] == "not_taken"
    assert (outcomes["ended"]["r_next_status"], outcomes["ended"]["s_status"]) == ("not_applicable", "not_applicable")
    assert outcomes["running"]["action_status"] == "open" and outcomes["running"]["s_status"] == "pending"


def test_the_replayer_applies_the_vaults_servable_items(tmp_path):
    from learnloop.router.outcomes import servable_items_by_learning_object

    paths = create_basic_vault(tmp_path / "vault")
    add_followup_item(paths.root, B)
    vault = load_vault(paths.root)
    assert servable_items_by_learning_object(vault)[LO] == {A, B}
