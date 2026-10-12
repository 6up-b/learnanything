"""Report 3: first-review miss rate by source (field §7.3), read-only and aggregate-only."""

from __future__ import annotations

from contextlib import closing
import hashlib
import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.connection import connect
from learnloop.placement.decisions import reconcile_fast_track, record_self_report
from learnloop.placement.report import placement_report

from tests.test_assumed_known import LOW_Q, _answer, _at, _queue, _setup

CHECK = 14 * 24 * 60 + 5


def _scenario(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    # fast_track on lo_diag, later passed at its check.
    _answer(vault, repository, "pi_diag_hard", minutes=1)
    _answer(vault, repository, "pi_diag_mid", minutes=2)
    reconcile_fast_track(vault, repository, clock=_at(3))
    # self_report on lo_eigen_basics, failed at its check.
    record_self_report(vault, repository, learning_object_ids=["lo_eigen_basics"], report="know_this", clock=_at(4))
    # self_report on lo_spectral, then "I don't know this".
    record_self_report(vault, repository, learning_object_ids=["lo_spectral"], report="too_easy", clock=_at(5))
    record_self_report(vault, repository, learning_object_ids=["lo_spectral"], report="dont_know_this", clock=_at(6))
    _answer(vault, repository, "pi_diag_easy", minutes=CHECK)
    checks = {s.learning_object_id: s.practice_item_id for s in _queue(vault, repository, CHECK + 1, persist=False)
              if s.components.get("assumed_check")}
    _answer(vault, repository, checks["lo_eigen_basics"], 1.0, minutes=CHECK + 2)
    return paths, vault, repository


def _report(paths, vault):
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return placement_report(connection, vault)


def test_report3_scores_first_reviews_by_source(tmp_path):
    paths, vault, _repository = _scenario(tmp_path)
    report = _report(paths, vault)
    fast, self_report = report["sources"]["fast_track"], report["sources"]["self_report"]
    assert (fast["decisions"], fast["passed"], fast["failed"], fast["first_review_miss_rate"]) == (1, 1, 0, 0.0)
    assert (self_report["decisions"], self_report["failed"], self_report["returned_by_learner"]) == (2, 1, 1)
    assert self_report["first_review_miss_rate"] == 1.0
    assert self_report["first_review_miss_rate_wilson_ci95"][1] == 1.0
    assert fast["resolved_on_schedule"] == 1 and self_report["resolved_on_schedule"] == 1
    assert report["sources"]["predictor"]["decisions"] == 0
    assert report["sources"]["quick_check"]["decisions"] == 0
    assert report["returns_to_learning"] == {
        "failed_first_reviews": 1, "i_dont_know_this": 1, "i_dont_know_this_on_assumed": 1,
    }
    # lo_eigen_basics withheld its two other items until its check missed, and
    # lo_spectral was returned: deferred, then back to learning, not saved.
    assert self_report["items_deferred_then_returned"] == 4
    assert self_report["items_used_as_checks"] == 1 and fast["items_used_as_checks"] == 1
    assert self_report["items_avoided"] == fast["items_avoided"] == 0
    minutes = report["learning_minutes"]
    assert minutes["minutes_basis"] == "flat_3_minutes"
    assert minutes["saved_estimate"] == 0.0
    assert minutes["saved_estimate"] <= minutes["learning_every_new_lo_estimate"]
    assert report["confounds"] and report["manifest"]["placement_version"] is True


def test_report3_is_aggregate_only_and_read_only(tmp_path):
    paths, vault, _repository = _scenario(tmp_path)
    digest = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    output = tmp_path / "reports"
    result = CliRunner().invoke(
        app, ["eval", "placement", "--vault", str(paths.root), "--output-dir", str(output), "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    files = payload["reports"]
    text = open(files["json"], encoding="utf-8").read() + open(files["markdown"], encoding="utf-8").read()
    for identity in ("lo_diag", "lo_eigen_basics", "lo_spectral", "pi_diag", "An answer."):
        assert identity not in text
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == digest


def test_placement_status_lists_open_assumptions(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    result = CliRunner().invoke(app, ["placement", "status", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["active"] is True and list(payload["open"]) == ["lo_diag"]
    assert payload["open"]["lo_diag"]["first_review_due"] == "2026-06-02T12:01:00Z"


def test_report3_counts_each_learning_obligation_once(tmp_path):
    """F9: toggling "I know this" / "I don't know this" defers, it does not
    save; savings are unique untouched items on LOs still assumed or kept in
    maintenance, and practised items are never savings."""

    paths, vault, repository = _setup(tmp_path)
    for round_ in range(3):
        record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this",
                           clock=_at(1 + 2 * round_))
        record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="dont_know_this",
                           clock=_at(2 + 2 * round_))
    report = _report(paths, vault)
    minutes, self_report = report["learning_minutes"], report["sources"]["self_report"]
    assert self_report["decisions"] == 3 and self_report["returned_by_learner"] == 3
    assert minutes["saved_estimate"] == 0.0 and minutes["provisional_estimate"] == 0.0
    assert self_report["items_deferred_then_returned"] == 3
    assert minutes["saved_estimate"] <= minutes["learning_obligations_estimate"]

    # One more "I know this": three items deferred pending the check, once.
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(10))
    report = _report(paths, vault)
    assert report["sources"]["self_report"]["items_deferred_pending_check"] == 3
    assert report["learning_minutes"]["provisional_estimate"] == 9.0
    assert report["learning_minutes"]["saved_estimate"] == 0.0

    # The check passes: the two untouched items are avoided learning.
    _answer(vault, repository, "pi_diag_mid", minutes=CHECK + 10)
    report = _report(paths, vault)
    assert report["sources"]["self_report"]["items_avoided"] == 2
    assert report["learning_minutes"]["saved_estimate"] == 6.0
    # Practising one of them later means it was learned after all.
    _answer(vault, repository, "pi_diag_easy", minutes=CHECK + 40 * 24 * 60)
    report = _report(paths, vault)
    assert report["sources"]["self_report"]["items_avoided"] == 1
    assert report["sources"]["self_report"]["items_deferred_then_learned"] == 1
    total = report["learning_minutes"]
    assert total["saved_estimate"] + total["provisional_estimate"] <= total["learning_obligations_estimate"]


def test_report3_orders_same_second_practice_after_the_decision(tmp_path):
    """F11: report 3 reads the same durable (created_at, id) order as the
    placement state, so an item first practised in the same second as, but
    after, the LO's first decision is still a learning obligation."""

    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    _answer(vault, repository, "pi_diag_easy", 1.0, minutes=1)  # a miss right after "I know this"
    report = _report(paths, vault)
    self_report = report["sources"]["self_report"]
    assert self_report["failed"] == 1 and self_report["resolved_early"] == 1
    # The miss resolved the assumption, so its item is the one used as the check.
    assert self_report["items_used_as_checks"] == 1
    assert self_report["items_deferred_then_returned"] == 2
