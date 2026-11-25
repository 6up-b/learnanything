"""mvp-0.75 on top of mvp-0.74 (the selected view's forecast, prepared forecasts, exam finish's one attempt id, the
shadow report's forecast digests, the four-way script's arm (f) through production replay): what the integration
checks, and the router's miss-cause learning reading a lesson outcome in the fit's order end to end (L42-R19).
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.algorithm_versions import FORECAST_SCORING_ALGORITHM_VERSION, LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault, create_placement_vault, seed_due_item, set_algorithm_version


def _blocks(repository):
    with repository.connection() as connection:
        return {row[0]: json.loads(row[1]).get("mastery_application") for row in connection.execute(
            "SELECT attempt_id, payload_json FROM attempt_debug_payloads ORDER BY attempt_id")}


def _sources(repository):
    with repository.connection() as connection:
        return {row[0]: json.loads(row[1]).get("prediction_source") for row in connection.execute(
            "SELECT attempt_id, predicted_score_dist_json FROM attempt_surprise")}


def _graded_placement_vault(root, *, served: bool):
    from tests.difficulty_replay_helpers import _serve

    paths = create_placement_vault(root, version=LATEST_ALGORITHM_VERSION)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    item = vault.practice_items["pi_eig_mid"]
    ids = []
    for index in range(3):
        at = NOW + timedelta(days=index)
        presentation = None
        if served:
            from learnloop.db.stores.ad_serving import insert_selection

            from tests.difficulty_replay_helpers import _iso

            block = f"blk_h3_{index}"
            with repository.connection() as connection:
                insert_selection(connection, dict(
                    kind="serve", block_id=block, slot_position=1, decision_key=f"serve:{block}:1",
                    view=f"lo:{item.learning_object_id}", learning_object_id=item.learning_object_id,
                    chosen_item_id=item.id, mode="band", support=[], excluded=[], constants={}, versions={},
                    seed="seed", state_hash="state", algorithm_version=LATEST_ALGORITHM_VERSION, created_at=_iso(at)))
                connection.commit()
            presentation = _serve(vault, repository, item.id, index, at)
        ids.append(complete_self_graded_attempt(
            vault, repository, AttemptDraft(item.id, "answer", plan_presentation_id=presentation),
            SelfGradeInput({"correctness": 2 + index}, 4), clock=FrozenClock(at + timedelta(seconds=1))).attempt_id)
    return vault, repository, ids


def test_the_mastery_record_is_what_mastery_applied_whichever_forecast_scored_surprise(tmp_path):
    """(i): the same answers, one history scored against the selected view's serve receipts and one against the grade-time
    receipts (each forecast prepared before the grade's transaction). Mastery's record is the same in both, live and after two rebuilds."""

    served_vault, served, served_ids = _graded_placement_vault(tmp_path / "served", served=True)
    _plain_vault, plain, plain_ids = _graded_placement_vault(tmp_path / "plain", served=False)
    assert {_sources(served)[i] for i in served_ids} == {"serve_receipt"}
    assert {_sources(plain)[i] for i in plain_ids} == {"grade_receipt"}
    live = _blocks(served)
    assert [live[i] for i in served_ids] == [_blocks(plain)[i] for i in plain_ids]
    assert all(live[i]["applied"] for i in served_ids)
    for _ in range(2):
        rebuild_all_derived_state(served_vault, served)
        assert _blocks(served) == live


def _exam_vault(tmp_path):
    from learnloop.goals.exam_pool import reserve_exam_pool
    from learnloop.goals.exam_session import start_exam
    from learnloop.vault.writer import upsert_practice_item

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    for item_id, facet in (("pi_exam_a", "recall"), ("pi_exam_b", "apply")):
        upsert_practice_item(root, {
            "id": item_id, "learning_object_id": "lo_svd_definition", "subjects": None,
            "practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": [facet], "evidence_weights": {facet: 1.0}, "prompt": f"Prompt {item_id}.",
            "expected_answer": "Answer.", "difficulty": 0.5,
            "grading_rubric": {"max_points": 4, "criteria": [{"id": "correctness", "points": 4,
                                                              "description": "Correct."}], "fatal_errors": []},
            "created_at": NOW_ISO, "updated_at": NOW_ISO}, clock=FrozenClock(NOW))
    repository = seed_due_item(paths)
    vault = load_vault(root)
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))
    return vault, repository, start_exam(vault, repository, "goal_linear_algebra_ml", clock=FrozenClock(NOW))


def test_an_exam_finish_retried_under_its_one_attempt_id_observes_at_the_attempts_second(tmp_path, monkeypatch):
    """(ii): a finish whose link fails rolls back and retries under the same attempt id; the attempt is applied at the
    sitting's whole-second instant, so its record's instant is the stored one and a rebuild moves nothing."""

    from learnloop.goals.exam_session import finish_exam, record_exam_answer

    from tests.exam_session_helpers import _grade

    vault, repository, session = _exam_vault(tmp_path)
    sitting = session["session_id"]
    record_exam_answer(vault, repository, sitting, "pi_exam_a", answer_md="A", resolved_grade=_grade(4))
    link = repository.set_exam_answer_attempt_id

    def interrupted(session_id, item_id, attempt_id):
        raise RuntimeError("interrupted link")

    finishing = FrozenClock(NOW + timedelta(microseconds=900_000))
    monkeypatch.setattr(repository, "set_exam_answer_attempt_id", interrupted)
    with pytest.raises(RuntimeError, match="interrupted link"):
        finish_exam(vault, repository, sitting, clock=finishing)
    monkeypatch.setattr(repository, "set_exam_answer_attempt_id", link)
    report = finish_exam(vault, repository, sitting, clock=finishing)
    attempt_id = report["items"][0]["attempt_id"]
    created = repository.fetch_practice_attempt(attempt_id)["created_at"]
    assert _blocks(repository)[attempt_id]["observed_at"] == created == NOW_ISO
    # The fixture seeds mastery directly (no attempt), so a rebuild starts the LO from its cold seed: compare two
    # rebuilds, whose instants are the stored whole seconds.
    rebuild_all_derived_state(vault, repository)
    once = _blocks(repository)
    assert once[attempt_id]["observed_at"] == created
    rebuild_all_derived_state(vault, repository)
    assert _blocks(repository) == once


def test_the_four_way_arm_f_at_the_facts_tag_is_production(tmp_path):
    """(iii): at mvp-0.75 the label is off and surprise reads the receipts already, so arm (f), through production
    replay, is today's arm; the script runs on scratch copies and leaves the input as it was."""

    from datetime import UTC, datetime

    from tests.difficulty_replay_helpers import HISTORY, build_vault, file_digests, forbid_model_clients, load_script

    paths = build_vault(tmp_path / "vault", version=LATEST_ALGORITHM_VERSION)
    before = file_digests(paths.root)
    with pytest.MonkeyPatch.context() as monkeypatch:
        forbid_model_clients(monkeypatch)
        report = load_script("difficulty_four_way").run_four_way(paths.root, as_of=datetime(2027, 1, 15, tzinfo=UTC),
                                                                 top_k=(3, 10))
    assert report["arms"]["f_label_off_and_receipt"]["replayed_attempts"] == len(HISTORY)
    values = report["values"]
    assert values["f_label_off_and_receipt"]["mastery"] == values["a_today"]["mastery"]
    assert values["f_label_off_and_receipt"]["surprise"] == values["a_today"]["surprise"]
    assert report["input_databases_unchanged"] is True and file_digests(paths.root) == before


def test_the_shadow_reports_forecast_digests_hold_across_two_rebuilds_at_the_facts_tag(tmp_path):
    """(iv): a rebuild at mvp-0.75 rewrites each payload's mastery record but moves no surprise row, grade receipt or
    subject KL: the shadow report's forecast digests agree before and after, twice."""

    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    from tests.difficulty_replay_helpers import build_vault

    paths = build_vault(tmp_path / "vault", version=LATEST_ALGORITHM_VERSION)
    vault = load_vault(paths.root)
    first = shadow_rebuild(vault).as_dict()["forecast_digests"]
    second = shadow_rebuild(vault).as_dict()["forecast_digests"]
    assert first == second
    assert {key: first["before"][key] for key in ("surprise", "grade_receipts")} == {
        key: first["after"][key] for key in ("surprise", "grade_receipts")}


def _router_lesson_with_two_answers_in_one_second(tmp_path, version):
    """A lesson the router offered on a diagnosed miss, then two first answers on one new item in one second: B
    applied first (full credit), A second (none), their ids in the opposite order."""

    from tests.daily_plan_fakes import NOW as CLOCK_NOW
    from tests.daily_plan_fakes import iso

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, version)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    def at(days, minutes=0.0):
        return iso(CLOCK_NOW - timedelta(days=days) + timedelta(minutes=minutes))

    frozen = {"status": "diagnosed", "p_gap": 0.0, "p_slip": 1.0, "p_unknown": 0.0}
    detail = {"lesson_offer": {"learning_object_id": "lo_a", "miss_cause": frozen, "mass": {"mean": 0.5},
                               "card": {"candidates": [{"predicted_success": 0.4}]}}}
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO router_decisions (id, receipt_key, decision_kind, surface, mode, policy, algorithm_version, "
            "log_version, snapshot_hash, candidates_json, exclusions_json, candidate_count, chosen_ref, propensity, "
            "propensity_kind, detail_json, created_at) VALUES ('rd1', 'k', 'plan_block', 'desktop', 'live', 'p', ?, "
            "'v1', 'h', '[]', '[]', 0, 'lesson_offer:lo_a', 0.5, 'exact', ?, ?)", (version, json.dumps(detail), at(3)))
        connection.execute(
            "INSERT INTO lessons (id, driver, origin, origin_ref, entry, goal_text, learning_object_ids_json, "
            "doctrine_version, brief_version, algorithm_version, opened_at, closed_at, goal_json, close_reason) VALUES "
            "('les1', 'desktop', 'router', 'rd1', 'learning_object', 'g', '[\"lo_a\"]', 'd', 'b', ?, ?, ?, '{}', "
            "'learner_stop')", (version, at(3, 1), at(3, 20)))
        for sequence, (attempt_id, correctness) in enumerate((("att_B", 1.0), ("att_A", 0.0)), start=1):
            connection.execute(
                "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
                "correctness, primed, hints_used, created_at) VALUES (?, 'pi_new', 'lo_a', 'short_answer', "
                "'independent_attempt', ?, 0, 0, ?)", (attempt_id, correctness, at(2)))
            connection.execute("INSERT INTO attempt_application_order(sequence, attempt_id, basis, algorithm_version, "
                               "recorded_at) VALUES (?, ?, 'applied', ?, ?)", (sequence, attempt_id, version, at(2)))
        connection.commit()
    return vault, repository, iso(CLOCK_NOW)


@pytest.mark.parametrize(("version", "expected"), [
    (LATEST_ALGORITHM_VERSION, ("att_B", 1.0)),
    (FORECAST_SCORING_ALGORITHM_VERSION, ("att_A", 0.0)),  # below the tag: the legacy id order, as built
])
def test_the_routers_miss_cause_learning_reads_the_outcome_the_fit_reads(tmp_path, version, expected):
    """L42-R19, end to end: the router's miss-cause learning takes the first answer mastery applied,
    as the fit does, from the facts' tag."""

    from learnloop.router_objective import miss_cause as MC

    vault, repository, now = _router_lesson_with_two_answers_in_one_second(tmp_path, version)
    with repository.connection() as connection:
        (row,) = MC._offer_rows(connection, vault.config, now)
        slopes = MC.cause_slopes(connection, (0.2, 0.01), now, vault.config)
    assert (row["outcome_attempt_id"], row["y"]) == expected
    assert slopes["n"] == 1
    assert (slopes["slip"][0] > 0.0) is (expected[1] == 1.0)
