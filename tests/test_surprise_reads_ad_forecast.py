"""From the label's retirement (arm H, H3): mastery reads no difficulty label, and surprise is scored against adaptive
difficulty's forecast made before the answer (the serve-time receipt of its plan presentation, else the grade-time
receipt every grade now records, else mastery's own prediction), the row saying which. Replay reads receipts, so a
rebuild reproduces the live rows and writes no receipt; history graded before the tag falls back to mastery."""

from __future__ import annotations

import json
from contextlib import closing
from datetime import timedelta

import pytest

from learnloop.algorithm_versions import LABEL_RETIRED_ALGORITHM_VERSION, PROBE_ROUTER_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.scheduling.forecast_receipts import ITEM_UNASSISTED_SUCCESS_AT_GRADE
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.difficulty_replay_helpers import HISTORY, RETRY, UNBOUND, build_vault
from tests.helpers import NOW, set_algorithm_version


def _surprise(repository) -> dict[str, dict]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT attempt_id, predicted_score_dist_json, predictive_surprise, bayesian_surprise, surprise_direction,"
            " fsrs_interval_factor FROM attempt_surprise").fetchall()
    return {str(r[0]): {"dist": json.loads(r[1]), "predictive": r[2], "bayesian": r[3], "direction": r[4],
                        "factor": r[5]} for r in rows}


def _grade_receipts(repository) -> dict[str, dict]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT source_attempt_id, receipt_key, p, inputs_json FROM forecast_receipts WHERE kind = ?",
            (ITEM_UNASSISTED_SUCCESS_AT_GRADE,)).fetchall()
    return {str(r[0]): {"key": r[1], "p": r[2], "inputs": json.loads(r[3])} for r in rows}


def _attempt_ids(repository) -> list[str]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [str(r[0]) for r in connection.execute("SELECT id FROM practice_attempts ORDER BY created_at, id")]


@pytest.fixture(scope="module")
def served(tmp_path_factory):
    paths = build_vault(tmp_path_factory.mktemp("h3") / "vault", served=True, version=LABEL_RETIRED_ALGORITHM_VERSION)
    return paths, load_vault(paths.root), Repository(paths.sqlite_path)


def test_every_answer_records_a_grade_time_forecast_and_surprise_names_its_source(served):
    _paths, _vault, repository = served
    order = _attempt_ids(repository)
    receipts = _grade_receipts(repository)
    rows = _surprise(repository)
    # Every graded answer recorded AD's forecast, bound to it, with the events it read.
    assert set(receipts) == set(order)
    assert all(r["inputs"]["events_fingerprint"] for r in receipts.values())
    for index, attempt_id in enumerate(order):
        dist = rows[attempt_id]["dist"]
        bound = index not in UNBOUND and index != RETRY
        # A plan-bound answer reads its serve-time forecast; any other the grade-time one.
        assert dist["prediction_source"] == ("serve_receipt" if bound else "grade_receipt"), index
        if not bound:
            assert dist["p_ad"] == pytest.approx(receipts[attempt_id]["p"])
        # Mastery's own curve: no item term (a primed answer keeps the priming offset), whatever the label.
        primed = HISTORY[index][2]
        assert (dist["a"], dist["b"]) == (1.0, -2.0 if primed else 0.0)
        # Its prediction is mastery's, the scored one AD's; the interval factor never reads AD.
        assert dist["expected_correctness"] != pytest.approx(dist["p_scored"])
        assert rows[attempt_id]["factor"] == 1.0


def test_a_rebuild_reproduces_every_surprise_row_and_writes_no_receipt(served, tmp_path):
    from learnloop.db.copies import copy_tree_with_databases

    paths, _vault, _repository = served
    root = tmp_path / "copy"
    copy_tree_with_databases(paths.root, root)
    vault = load_vault(root)
    repository = Repository(vault.root / paths.sqlite_path.relative_to(paths.root))
    live, receipts = _surprise(repository), _grade_receipts(repository)
    for _ in range(2):
        rebuild_all_derived_state(vault, repository)
        assert _surprise(repository) == live
        assert _grade_receipts(repository) == receipts


def test_a_regrade_rereads_the_answers_first_forecast(served, tmp_path):
    from learnloop.db.copies import copy_tree_with_databases
    from tests.regrade_contract_replay_helpers import _regrade

    paths, _vault, _repository = served
    root = tmp_path / "regrade"
    copy_tree_with_databases(paths.root, root)
    vault = load_vault(root)
    repository = Repository(vault.root / paths.sqlite_path.relative_to(paths.root))
    attempt_id = _attempt_ids(repository)[UNBOUND[0]]
    before = _surprise(repository)[attempt_id]["dist"]
    receipts = _grade_receipts(repository)
    _regrade(vault, repository, attempt_id, {"correctness": 4.0}, when=NOW + timedelta(days=60))
    after = _surprise(repository)[attempt_id]["dist"]
    assert (after["prediction_source"], after["p_ad"], after["receipt_key"]) == (
        before["prediction_source"], before["p_ad"], before["receipt_key"])
    assert _grade_receipts(repository) == receipts


def test_history_before_the_tag_falls_back_to_mastery_marked(tmp_path):
    paths = build_vault(tmp_path / "old", served=True, version=PROBE_ROUTER_ALGORITHM_VERSION)
    repository = Repository(paths.sqlite_path)
    assert _grade_receipts(repository) == {}
    old = _surprise(repository)
    assert all("prediction_source" not in row["dist"] for row in old.values())
    set_algorithm_version(paths, LABEL_RETIRED_ALGORITHM_VERSION)
    rebuild_all_derived_state(load_vault(paths.root), repository)
    rows = _surprise(repository)
    order = _attempt_ids(repository)
    # The serve-time receipts recorded then are read; every other past answer falls back to mastery, marked. No AD
    # replay runs over history, and the rebuild records no receipt.
    for index, attempt_id in enumerate(order):
        bound = index not in UNBOUND and index != RETRY
        assert rows[attempt_id]["dist"]["prediction_source"] == ("serve_receipt" if bound else "mastery"), index
    assert _grade_receipts(repository) == {}


def test_the_label_does_not_move_mastery(tmp_path):
    """Two vaults that differ only in their items' labels hold the same mastery and the same surprise."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    states = []
    for name, difficulty in (("easy", 0.1), ("hard", 0.9)):
        paths = build_vault(tmp_path / name, version=LABEL_RETIRED_ALGORITHM_VERSION)
        for item_id in load_vault(paths.root).practice_items:
            path = paths.practice_item_path("linear-algebra", item_id)
            if path.exists():
                data = read_yaml(path)
                data["difficulty"] = difficulty
                write_yaml(path, data)
        vault = load_vault(paths.root)
        repository = Repository(paths.sqlite_path)
        rebuild_all_derived_state(vault, repository)
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            mastery = sorted(tuple(r) for r in connection.execute(
                "SELECT learning_object_id, logit_mean, logit_variance FROM learning_object_mastery"))
        states.append(mastery)
    assert states[0] == states[1]


def test_ads_trace_records_the_kl_of_its_posterior_from_the_tag_on(tmp_path):
    def kls(version):
        paths = build_vault(tmp_path / version, version=version)
        repository = Repository(paths.sqlite_path)
        rebuild_all_derived_state(load_vault(paths.root), repository)
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            return [json.loads(r[0]).get("kl_observation") for r in connection.execute(
                "SELECT detail_json FROM ad_attempt_trace WHERE view = 'subject' AND information IS NOT NULL")]

    after = kls(LABEL_RETIRED_ALGORITHM_VERSION)
    assert after and all(k is not None and k["total"] >= 0 and k["weights"] >= 0 and k["states"] >= 0 for k in after)
    assert all(k["total"] == pytest.approx(k["weights"] + k["states"]) for k in after)
    assert set(kls(PROBE_ROUTER_ALGORITHM_VERSION)) == {None}


def test_the_grade_does_not_wait_on_a_second_clock(served):
    """The forecast reads AD before the grade's write transaction; it is stamped at the grade's own instant."""

    paths, vault, repository = served
    draft = AttemptDraft(practice_item_id="pi_eig_mid", learner_answer_md="Again.", attempt_type="independent_attempt")
    when = NOW + timedelta(days=90)
    result = complete_self_graded_attempt(vault, repository, draft,
                                          SelfGradeInput(criterion_points={"correctness": 3}, confidence=3),
                                          clock=FrozenClock(when))
    receipt = _grade_receipts(repository)[result.attempt_id]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        as_of, created = connection.execute("SELECT inputs_as_of, created_at FROM forecast_receipts WHERE receipt_key = ?",
                                            (receipt["key"],)).fetchone()
    assert as_of == created == when.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_a_writer_committing_between_the_read_and_the_write_leaves_the_recorded_forecast_standing(
        served, tmp_path, monkeypatch):
    """The forecast is read before the grade's write transaction, so another writer (a background job, the phone) can
    commit in between. The receipt then records the events it read, which are not AD's events just before the write;
    the grade scores against the recorded forecast, and a rebuild reproduces it exactly, never recomputing it."""

    import learnloop.attempts.attempts as attempts_module
    from learnloop.adaptive_difficulty.grade_forecast import grade_receipt
    from learnloop.db.copies import copy_tree_with_databases

    paths, _vault, _repository = served
    root = tmp_path / "race"
    copy_tree_with_databases(paths.root, root)
    vault = load_vault(root)
    repository = Repository(vault.root / paths.sqlite_path.relative_to(paths.root))
    when = NOW + timedelta(days=90)
    real = attempts_module.with_grade_forecast
    seen: dict[str, str] = {}

    def racing(vault_, repository_, attempt, *, clock=None):
        attempt = real(vault_, repository_, attempt, clock=clock)
        if seen:
            return attempt
        seen["read"] = attempt.grade_forecast.inputs["events_fingerprint"]
        # Another answer commits after this grade's read and before its write.
        complete_self_graded_attempt(vault_, repository_, AttemptDraft(
            practice_item_id="pi_diag_mid", learner_answer_md="Meanwhile.", attempt_type="independent_attempt"),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=3), clock=FrozenClock(when))
        seen["before_write"] = grade_receipt(vault_, repository_, practice_item_id="pi_eig_mid",
                                             attempt_id="probe", at=attempt.grade_forecast.inputs_as_of
                                             ).inputs["events_fingerprint"]
        return attempt

    monkeypatch.setattr(attempts_module, "with_grade_forecast", racing)
    result = complete_self_graded_attempt(vault, repository, AttemptDraft(
        practice_item_id="pi_eig_mid", learner_answer_md="Again.", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 3}, confidence=3), clock=FrozenClock(when))
    monkeypatch.undo()
    receipt = _grade_receipts(repository)[result.attempt_id]
    assert receipt["inputs"]["events_fingerprint"] == seen["read"] != seen["before_write"]
    row = _surprise(repository)[result.attempt_id]
    assert (row["dist"]["prediction_source"], row["dist"]["p_ad"]) == ("grade_receipt", pytest.approx(receipt["p"]))
    live, receipts = _surprise(repository), _grade_receipts(repository)
    rebuild_all_derived_state(vault, repository)
    assert _surprise(repository) == live and _grade_receipts(repository) == receipts
