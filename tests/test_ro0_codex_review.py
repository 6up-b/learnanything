"""RO0's Codex review (docs/reviews/router-ro0-codex-review.md): each finding reproduced on the real paths, then fixed."""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import LESSON_SUGGESTIONS_ALGORITHM_VERSION
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.repositories import Repository
from learnloop.db.stores import router_objective as store
from learnloop.followup_run import router as followup_router
from learnloop.reader import reader_inquiry as RI
from learnloop.router_objective import decision_state as DS
from learnloop.router_objective import goal_lifecycle as GL
from learnloop.router_objective import trajectory as T
from learnloop.scheduling.fsrs import forgetting_curve
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import load_vault
from learnloop.daily_plan.router_chooser import INSERT_NOW
from tests.daily_plan_fakes import record_attempt, scheduled
from tests.helpers import NOW, append_config_toml, create_basic_vault, seed_due_item, set_algorithm_version
from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import fake_runtime
from tests.daily_plan_build_helpers import _wide_items
from tests.question_context_helpers import FakeTutorClient

SRC = Path(__file__).resolve().parents[1] / "src"
PLAN_OFF = "[plan]\nenabled = false\n"


def _state(repository, decision_id):
    with repository.connection() as connection:
        return store.decision_state(connection, decision_id)


# -- F1: refusing the disclosure state never takes the question with it ------------------------------


def test_f1_a_refused_disclosure_write_leaves_the_question_and_warns(tmp_path, caplog):
    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    with repository.connection() as connection:
        connection.execute("CREATE TRIGGER refuse_state BEFORE UPDATE OF reveal_state_json ON question_events "
                           "BEGIN SELECT RAISE(ABORT, 'refused'); END")
        connection.commit()
    result = ask_question(vault, repository, FakeTutorClient(), context="practice", question_md="Why?",
                          practice_item_id="pi_svd_define_001", session_id="s1", clock=FrozenClock(NOW))
    event = repository.question_event(result["event_id"])
    assert event["question_md"] == "Why?" and event["answer_md"], "the question and its answer stand"
    assert event["reveal_state_json"] is None
    assert "disclosure state" in caplog.text


def test_f1_the_refusal_is_the_receipts_alone_inside_a_callers_transaction(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    with repository.connection() as connection:
        connection.execute("CREATE TRIGGER refuse_state BEFORE UPDATE OF reveal_state_json ON question_events "
                           "BEGIN SELECT RAISE(ABORT, 'refused'); END")
        connection.commit()
    with repository.atomic():
        event_id = repository.insert_question_event({"context": "reader", "question_md": "Q", "reveal_state_json": "{}"})
    assert repository.question_event(event_id)["question_md"] == "Q"


# -- F2: a forced item keeps its belief and minutes ----------------------------------------------------


def test_f2_the_forced_shape_names_its_item():
    class Item:
        learning_object_id = "lo_item"

    class Vault:
        practice_items = {"a": Item()}

    assert DS.candidate_ids(Vault, [{"practice_item_id": "a", "origin": "requested", "est_minutes": 3.0}]) == (["a"], ["lo_item"])


def test_f2_a_forced_only_boundary_keeps_the_served_items_state_and_minutes(tmp_path):
    forced = "pi_spec_easy"
    env = mixture_env(tmp_path, fake_runtime(), items=lambda: [scheduled(forced, "lo_spectral"), *_wide_items()])
    env.repository.requested_practice_item_ids = lambda *, skip_commitment_ids=(): [forced]
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    advance(env, serve=True)
    with env.repository.connection() as connection:
        decision = connection.execute("SELECT id, candidates_json, detail_json FROM router_decisions "
                                      "WHERE decision_kind = 'plan_block' ORDER BY created_at, id").fetchone()
    detail = json.loads(decision["detail_json"])
    assert [row["practice_item_id"] for row in detail["forced"]] == [forced]
    named = {item for entry in json.loads(decision["candidates_json"]) for item in entry.get("item_ids") or ()}
    assert forced not in named, "the candidates do not name it: only the forced list does"
    state = _state(env.repository, decision["id"])["state"]
    assert state["items"][forced]["minutes_source"].startswith("estimator:") and state["items"][forced]["minutes"] > 0
    assert state["block_minutes"][forced] == detail["forced"][0]["est_minutes"], "what the block was charged"
    assert env.vault.practice_items[forced].learning_object_id in state["los"]


# -- F3: an offer's, a staged decision's and a suggestion's AD numbers are kept, not left to replay ----


def _assert_ad_kept(receipt, lo):
    state = receipt["state"]
    assert state["ad"]["status"] == "live", "the decision-time numbers, not a promise to replay them"
    assert receipt["ad_state_hash"] and state["ad"]["state_hash"] == receipt["ad_state_hash"]
    assert "ad" in state["los"][lo], f"{lo}: no AD numbers"


def _sidecar_call(ctx, name, params):
    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_f3_a_served_offer_keeps_its_candidates_ad_numbers(tmp_path):
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, LATEST_ALGORITHM_VERSION)
    append_config_toml(paths.root, PLAN_OFF)
    seed_due_item(paths)
    ctx = SidecarContext()
    ctx.load(paths.root, maintenance=False)
    ctx.grading_provider_override = "manual"
    session = _sidecar_call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    _sidecar_call(ctx, "get_today_queue", {"sessionId": session})
    _vault, repository = ctx.require_vault()
    with repository.connection() as connection:
        offer = connection.execute("SELECT id, propensity_kind, chosen_learning_object_id FROM router_decisions "
                                   "WHERE decision_kind = 'today_offer' ORDER BY created_at DESC, id DESC").fetchone()
    assert offer["propensity_kind"] != "not_served"
    receipt = _state(repository, offer["id"])
    _assert_ad_kept(receipt, offer["chosen_learning_object_id"])


def test_f3_a_list_that_served_no_head_still_decides_nothing_and_reads_no_ad(tmp_path):
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, LATEST_ALGORITHM_VERSION)
    seed_due_item(paths)
    ctx = SidecarContext()
    ctx.load(paths.root, maintenance=False)
    ctx.grading_provider_override = "manual"
    session = _sidecar_call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    _sidecar_call(ctx, "get_today_queue", {"sessionId": session})
    _vault, repository = ctx.require_vault()
    with repository.connection() as connection:
        offer = connection.execute("SELECT id, propensity_kind FROM router_decisions WHERE decision_kind = 'today_offer' "
                                   "ORDER BY created_at DESC, id DESC").fetchone()
    assert offer["propensity_kind"] == "not_served"
    state = _state(repository, offer["id"])["state"]
    assert state["ad"]["status"] == DS.AD_NOT_READ and state["omitted"]["reason"] == "offer_not_served"


def test_f3_a_lesson_suggestion_keeps_its_ad_numbers_read_before_its_transaction(tmp_path, monkeypatch):
    from learnloop.router import lesson_suggestions as LS
    from tests.teacher_te1b_suggestions_helpers import _clock, _decisions, _suggestion, _vault

    monkeypatch.setattr(LS, "_uniforms", lambda seed: (0.5, 0.0, 0.0))
    paths, repository = _vault(tmp_path, version=LESSON_SUGGESTIONS_ALGORITHM_VERSION)
    assert _suggestion(paths, repository, _clock()) is not None
    decision = _decisions(repository)[0]
    receipt = _state(repository, decision["id"])
    assert receipt["state"]["ad"]["status"] == "live", "read outside the draw's transaction, so never refused"
    assert receipt["ad_state_hash"] and receipt["candidate_los"] >= 1


# -- F4: FG1's itemless decision follows its bindings ---------------------------------------------------


def _fg1(tmp_path):
    from tests.followup_router_helpers import _decide, _env, _workflow

    env, record = _env(tmp_path, fake_runtime())
    row = _workflow(env)
    decision = followup_router.record_decision(env.vault, env.repository, row, _decide(env, record, INSERT_NOW), clock=env.clock)
    return env, record, row, decision


def _link(env, decision_id):
    with env.repository.connection() as connection:
        return next(row for row in T.rows(connection) if row["decision_id"] == decision_id)


def test_f4_a_generated_probes_attempt_is_uptake_counted_once_through_every_binding(tmp_path):
    env, record, row, decision = _fg1(tmp_path)
    assert _link(env, decision.decision_id)["attempts_on_presentations"] == 0
    item, lo = "pi_m2a", "lo_m2"
    followup_router.bind_item(env.repository, row, decision, SimpleNamespace(practice_item_id=item, presentation_id="pp_1"),
                              clock=env.clock)
    env.clock.advance(1)
    attempt = record_attempt(env.repository, item, lo, env.clock.now(), session_id=env.session_id)
    link = _link(env, decision.decision_id)
    assert link["bound_item_id"] == item and link["bound_probe_presentation_id"] == "pp_1"
    assert link["attempts_on_presentations"] == 1, "the item's binding"
    # The plan then serves it: a second, overlapping link to the same attempt.
    block = record.current_block()
    with env.repository.connection() as connection:
        connection.execute("INSERT INTO plan_presentations (id, block_id, practice_item_id, origin, session_id, served_at) "
                           "VALUES ('pres_fg1', ?, ?, 'followup', ?, ?)", (block.id, item, env.session_id, env.now_iso()))
        connection.execute("UPDATE practice_attempts SET plan_presentation_id = 'pres_fg1', probe_presentation_id = 'pp_1' "
                           "WHERE id = ?", (attempt,))
        connection.commit()
    followup_router.bind_plan_presentation(env.repository, row | {"decision_id": decision.decision_id},
                                           plan_presentation_id="pres_fg1", clock=env.clock)
    link = _link(env, decision.decision_id)
    assert link["attempts_on_presentations"] == 1, "one attempt, three links"
    assert link["presentations"] == 1 and link["first_served_at"] and link["bound_plan_presentation_id"] == "pres_fg1"


def test_f4_an_attempt_on_the_item_before_the_decision_is_not_its_uptake(tmp_path):
    env, _record, row, decision = _fg1(tmp_path)
    with env.repository.connection() as connection:
        decided_at = connection.execute("SELECT created_at FROM router_decisions WHERE id = ?", (decision.decision_id,)).fetchone()[0]
    earlier = datetime.fromisoformat(decided_at.replace("Z", "+00:00")) - timedelta(minutes=5)
    record_attempt(env.repository, "pi_m2a", "lo_m2", earlier, session_id=env.session_id)
    followup_router.bind_item(env.repository, row, decision, SimpleNamespace(practice_item_id="pi_m2a", presentation_id=None),
                              clock=env.clock)
    assert _link(env, decision.decision_id)["attempts_on_presentations"] == 0


@pytest.mark.parametrize(("outcome", "rejected"), [("skipped", 1), ("abandoned", 1), ("answered", 0), ("generation_failed", 0),
                                                   ("no_intervention", 0)])
def test_f4_a_binding_outcome_is_read_and_only_a_skip_or_abandonment_is_a_rejection(tmp_path, outcome, rejected):
    env, _record, row, decision = _fg1(tmp_path)
    followup_router.record_outcome(env.repository, row, decision, outcome=outcome, clock=env.clock)
    link = _link(env, decision.decision_id)
    assert link["binding_outcome"] == outcome and link["items_rejected"] == rejected


# -- F5: a return is after the session the action happened in ------------------------------------------


def _at(hours: float) -> FrozenClock:
    return FrozenClock(datetime(2026, 11, 4, 9, 59, tzinfo=UTC) + timedelta(hours=hours))


def test_f5_the_session_a_pre_session_decision_opened_is_not_its_return(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), session_id=None)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    with env.repository.connection() as connection:
        decision = connection.execute("SELECT id, session_id FROM router_decisions ORDER BY created_at, id").fetchone()
    assert decision["session_id"] is None, "Start builds before it opens a session"
    env.clock.advance(1)
    today = env.repository.create_session(clock=env.clock)
    env.session_id = today
    advance(env, serve=True)
    env.clock.advance(20)
    env.repository.end_session(today, clock=env.clock)
    link = _link(env, decision["id"])
    assert link["acting_session_id"] == today
    assert link["next_session_started_at"] is None and link["return_censored"] == "no_later_session"
    env.clock.advance(60 * 24)
    tomorrow = env.repository.create_session(clock=env.clock)
    link = _link(env, decision["id"])
    with env.repository.connection() as connection:
        started = connection.execute("SELECT started_at FROM sessions WHERE id = ?", (tomorrow,)).fetchone()[0]
    assert link["next_session_started_at"] == started and link["return_censored"] is None


def test_f5_a_decision_whose_session_is_unknown_is_censored_and_names_no_return(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), session_id=None)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    env.clock.advance(1)
    env.repository.create_session(clock=env.clock)
    with env.repository.connection() as connection:
        first = connection.execute("SELECT id FROM router_decisions ORDER BY created_at, id").fetchone()[0]
    link = _link(env, first)
    assert link["acting_session_id"] is None
    assert link["next_session_started_at"] is None and link["return_censored"] == "session_unresolved"


def test_f5_a_session_still_open_returns_in_the_next_one_it_was_replaced_by(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), session_id=None)
    env.session_id = env.repository.create_session(clock=env.clock)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    with env.repository.connection() as connection:
        first = connection.execute("SELECT id FROM router_decisions ORDER BY created_at, id").fetchone()[0]
    assert _link(env, first)["return_censored"] == "no_later_session"
    env.clock.advance(60)
    env.repository.create_session(clock=env.clock)
    assert _link(env, first)["return_censored"] is None


# -- F6: reading minutes belong to when they happened -------------------------------------------------


def _closed(repository, config, *, clock, closed_at, active, idle=0, visit="v1"):
    payload = {"visit_id": visit, "extraction_id": "e1", "active_seconds": active}
    if idle is not None:
        payload["idle_seconds"] = idle
    RI.record_activity(repository, [{"kind": "reader_view_closed", "occurred_at": closed_at, "payload": payload}],
                       clock=clock, config=config)


def _session(repository, started_at, ended_at=None):
    with repository.connection() as connection:
        connection.execute("INSERT INTO sessions (id, started_at, ended_at) VALUES ('s_read', ?, ?)", (started_at, ended_at))
        connection.commit()
    return "s_read"


def _reading(tmp_path, *, now, closes, session=None):
    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    clock = FrozenClock(now)
    session_id = _session(repository, *session) if session else None
    for close in closes:
        _closed(repository, vault.config, clock=clock, **close)
    material = DS.prepare(vault, repository, candidates=[], session_id=session_id, forgetting_curve=forgetting_curve, clock=clock)
    return material, json.loads(material.content)["active_minutes"]


def _utc(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_f6_a_visit_a_session_starts_during_gives_it_only_its_tail(tmp_path):
    local = datetime.now().astimezone().replace(hour=10, minute=0, second=0, microsecond=0)
    material, minutes = _reading(
        tmp_path, now=local + timedelta(minutes=30),
        session=(_utc(local + timedelta(minutes=20)),),
        closes=[{"closed_at": _utc(local + timedelta(minutes=25)), "active": 1500}])
    assert material.session_active_minutes == pytest.approx(5.0)
    assert material.day_active_minutes == pytest.approx(25.0)
    assert minutes["reader_split_visits"] == 1 and minutes["reader_unattributed"] == 0


def test_f6_a_visit_across_midnight_gives_the_day_only_what_came_after_it(tmp_path):
    midnight = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    material, minutes = _reading(
        tmp_path, now=midnight + timedelta(hours=1),
        closes=[{"closed_at": _utc(midnight + timedelta(minutes=15)), "active": 1500}])
    assert material.day_active_minutes == pytest.approx(15.0)
    assert minutes["reader_split_visits"] == 1


def test_f6_idle_time_spreads_a_visits_active_seconds_over_its_whole_stretch(tmp_path):
    local = datetime.now().astimezone().replace(hour=10, minute=0, second=0, microsecond=0)
    material, _minutes = _reading(
        tmp_path, now=local + timedelta(minutes=30),
        session=(_utc(local + timedelta(minutes=20)),),
        closes=[{"closed_at": _utc(local + timedelta(minutes=25)), "active": 600, "idle": 900}])
    assert material.session_active_minutes == pytest.approx(2.0), "10 of 25 minutes active, 5 of them in the session"


def test_f6_a_visit_from_before_the_session_is_not_its_because_its_receipt_came_late(tmp_path):
    local = datetime.now().astimezone().replace(hour=10, minute=0, second=0, microsecond=0)
    material, _minutes = _reading(
        tmp_path, now=local + timedelta(minutes=30),
        session=(_utc(local + timedelta(minutes=20)),),
        closes=[{"closed_at": _utc(local + timedelta(minutes=15)), "active": 300}])
    assert material.session_active_minutes == pytest.approx(0.0)
    assert material.day_active_minutes == pytest.approx(5.0)


def test_f6_a_visit_after_the_session_ended_is_not_its(tmp_path):
    local = datetime.now().astimezone().replace(hour=10, minute=0, second=0, microsecond=0)
    material, _minutes = _reading(
        tmp_path, now=local + timedelta(minutes=40),
        session=(_utc(local), _utc(local + timedelta(minutes=10))),
        closes=[{"closed_at": _utc(local + timedelta(minutes=30)), "active": 300}])
    assert material.session_active_minutes == pytest.approx(0.0)


def test_f6_a_visit_with_no_interval_is_said_and_never_summed(tmp_path):
    local = datetime.now().astimezone().replace(hour=10, minute=0, second=0, microsecond=0)
    material, minutes = _reading(
        tmp_path, now=local + timedelta(minutes=30),
        session=(_utc(local),),
        closes=[{"closed_at": _utc(local + timedelta(minutes=25)), "active": 600, "idle": None}])
    assert material.session_active_minutes == pytest.approx(0.0) and material.day_active_minutes == pytest.approx(0.0)
    assert minutes["reader_unattributed"] == pytest.approx(10.0), "incomplete, and it says so"


# -- F7: every writer names its initiator ---------------------------------------------------------------


def _exposures(repository, where=""):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(f"SELECT * FROM source_exposure_events {where}")]


def test_f7_a_from_your_books_excerpt_names_its_initiator(tmp_path, monkeypatch):
    from tests.reader_tutor_fakes import LookupTutor, ask, reader_ctx
    from tests.reader_tutor_retrieval_helpers import _quote_of

    tutor = LookupTutor(excerpt=_quote_of(("ext_book", "s7")))
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    session = repository.create_session()
    ask(ctx)
    [row] = _exposures(repository, "WHERE entity_type = 'question_event'")
    assert (row["context"], row["initiator"], row["initiator_session_id"]) == ("tutor_citation", "tutor_citation", session)


def test_f7_the_book_beside_a_problem_names_its_initiator(tmp_path):
    from tests.reader_workbench_rw2a_helpers import _call, _context, _open, _vault

    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = repository.create_session()
    problem = _open(ctx, entry="check_me")
    assert _exposures(repository) == []
    _call(ctx, "workbench.set_book", {"sessionId": problem["sessionId"], "visible": True})
    rows = _exposures(repository)
    assert rows and {(row["context"], row["initiator"], row["initiator_session_id"]) for row in rows} == {("reader", "learner", session)}
    # Opening with the book in view, and resuming it, write through the same fields.
    other = tmp_path / "other"
    other.mkdir()
    paths, repository = _vault(other)
    ctx = _context(paths.root)
    session = repository.create_session()
    problem = _open(ctx)
    rows = _exposures(repository)
    assert rows and {(row["initiator"], row["initiator_session_id"]) for row in rows} == {("learner", session)}
    with repository.connection() as connection:
        connection.execute("DELETE FROM source_exposure_events")
        connection.commit()
    _call(ctx, "workbench.leave", {"sessionId": problem["sessionId"]})
    _open(ctx, sessionId=problem["sessionId"], entry="resume")
    rows = _exposures(repository)
    assert all(row["initiator"] == "learner" for row in rows)


def test_f7_the_exercise_list_names_its_initiator(tmp_path):
    from tests.library_ask_fixtures import build_library_vault, context, set_config
    from tests.library_exercises_helpers import QUERY, call

    paths, repository, _spans = build_library_vault(tmp_path)
    set_config(paths, "library_exercises", fallback_enabled=True)
    session = repository.create_session()
    found = call(context(paths.root), "reader.find_exercises", {"query": QUERY, "learningObjectIds": ["lo_matrices"]})
    assert found["candidates"]
    rows = _exposures(repository, "WHERE entity_type = 'library_exercises'")
    assert rows and {(row["context"], row["initiator"], row["initiator_session_id"]) for row in rows} == {("library", "learner", session)}


def test_f7_off_the_new_paths_write_none_of_it(tmp_path):
    from tests.reader_workbench_rw2a_helpers import _call, _context, _open, _vault

    paths, repository = _vault(tmp_path, config="[router_objective]\nreceipts = false\n")
    ctx = _context(paths.root)
    repository.create_session()
    problem = _open(ctx, entry="check_me")
    _call(ctx, "workbench.set_book", {"sessionId": problem["sessionId"], "visible": True})
    rows = _exposures(repository)
    assert rows and all(row["initiator"] is None and row["initiator_session_id"] is None for row in rows)


#: The calls that write an exposure, and the keyword that carries row 4's fields.
_EXPOSURE_WRITERS = frozenset({"record_shown_spans", "record_shown_passages", "record_span_exposures", "_record_book_exposure"})


def _keyword_names(call: ast.Call) -> set[str | None]:
    return {keyword.arg for keyword in call.keywords}


def test_f7_every_writer_of_the_table_passes_the_initiators_fields():
    """A new surface can't write an exposure with null metadata by forgetting the keyword."""

    missing: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            if name in _EXPOSURE_WRITERS:
                if "exposure_fields" not in _keyword_names(node):
                    missing.append(f"{path.relative_to(SRC)}:{node.lineno} {name}")
            elif name == "build_span_view":
                # ``record=False`` writes nothing (the remediation delivery then writes its own row).
                record = next((keyword.value for keyword in node.keywords if keyword.arg == "record"), None)
                silent = isinstance(record, ast.Constant) and record.value is False
                if not silent and "exposure_fields" not in _keyword_names(node):
                    missing.append(f"{path.relative_to(SRC)}:{node.lineno} {name}")
    # The table's own writer: only ever from a function that takes row 4's fields.
    for path in sorted(SRC.rglob("*.py")):
        for function in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(function, ast.FunctionDef):
                continue
            takes = {arg.arg for arg in (*function.args.args, *function.args.kwonlyargs)}
            writes = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                         and node.func.attr == "insert_source_exposure_event" for node in ast.walk(function))
            if writes and "exposure_fields" not in takes:
                missing.append(f"{path.relative_to(SRC)}:{function.lineno} {function.name}")
    assert missing == []


# -- F8: two loaders append one transition -----------------------------------------------------------


GOAL = {"id": "g1", "title": "A goal", "status": "active", "priority": 0.5, "due_at": "2026-12-01T00:00:00Z",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-11-01T00:00:00Z",
        "facet_scope": {"concepts": ["singular_value_decomposition"]}, "target_recall": 0.8}


def _goal_rows(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM goal_lifecycle_events ORDER BY created_at, id")]


def _write_goals(paths, *goals):
    from learnloop.vault.yaml_io import write_yaml

    write_yaml(paths.goals_path, {"schema_version": 2, "goals": list(goals)})


def _interleaved(monkeypatch, paths):
    """Loader A reads the old state; loader B then sweeps start to finish on its own connection; A goes on."""

    vault = load_vault(paths.root)
    a, b = Repository(paths.sqlite_path), Repository(paths.sqlite_path)
    real = GL.changes
    calls = {"n": 0}

    def changes(*args, **kwargs):
        found = real(*args, **kwargs)
        calls["n"] += 1
        if calls["n"] == 1:
            monkeypatch.setattr(GL, "changes", real)
            GL.sweep(vault, b)
            monkeypatch.setattr(GL, "changes", changes)
        return found

    monkeypatch.setattr(GL, "changes", changes)
    wrote = GL.sweep(vault, a)
    monkeypatch.setattr(GL, "changes", real)
    return a, wrote


def test_f8_two_loaders_sweeping_a_new_goal_write_it_once(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    _write_goals(paths, GOAL)
    repository, wrote = _interleaved(monkeypatch, paths)
    assert wrote == 0, "the other loader wrote it"
    assert [row["event"] for row in _goal_rows(repository)] == [GL.CREATED]


def test_f8_two_loaders_sweeping_a_pause_write_it_once(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    _write_goals(paths, GOAL)
    GL.sweep(load_vault(paths.root), Repository(paths.sqlite_path))
    _write_goals(paths, {**GOAL, "status": "paused"})
    repository, wrote = _interleaved(monkeypatch, paths)
    assert wrote == 0
    assert [row["event"] for row in _goal_rows(repository)] == [GL.CREATED, "paused"]


def test_f8_an_unchanged_load_takes_no_write_lock(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    _write_goals(paths, GOAL)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    assert GL.sweep(vault, repository) == 1
    opened = []
    real = repository.atomic
    monkeypatch.setattr(repository, "atomic", lambda: opened.append(1) or real())
    assert GL.sweep(vault, repository) == 0
    assert opened == [], "a load that changes nothing writes nothing"
