"""Router objective RO5 §9 item 6 (owner decision, Nov 4): a seeded share of misconception picks stays open.

A pick that would resolve its factor (a concrete candidate the trace does not contradict) is assigned an arm with
its report, in the report's transaction, from the factor's own seed, logged with its exact probability; an
existing assignment is reused (a retry). ``open``: the report is recorded, no provisional belief opens and the factor
stays open. ``resolve`` and below the tag: as before. Fakes only.
"""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import ROUTER_CALIBRATION_ALGORITHM_VERSION, ROUTER_OBJECTIVE_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_attribution import record_unresolved_cause_self_report
from learnloop.router_objective import assignments as A
from learnloop.router_objective import picks as PK
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, set_algorithm_version
from tests.km2_write_path_helpers import build_mvp07_vault

TAG = ROUTER_CALIBRATION_ALGORITHM_VERSION


def _pick(tmp_path, *, version: str, share: float | None = None, u: float | None = None, monkeypatch=None):
    paths = build_mvp07_vault(tmp_path / "vault")
    set_algorithm_version(paths, version)
    if share is not None:
        append_config_toml(paths.root, f"[router_objective]\npick_open_share = {share}\n")
    if u is not None:
        monkeypatch.setattr(PK.mx, "uniform", lambda _seed, _stage: u)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    result = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id="pi_svd_ambiguous_001", learner_answer_md="An answer."),
        SelfGradeInput(criterion_points={"whole_item": 0}, fatal_errors=[], confidence=4),
        clock=clock,
    )
    factor = repository.unresolved_cause_factors_for_attempt(result.attempt_id)[0]
    report = record_unresolved_cause_self_report(
        vault, repository, factor_id=factor["id"], response="believed_candidate", candidate_index=0, clock=clock)
    return vault, repository, factor["id"], report


def _assignments(repository):
    with repository.connection() as connection:
        return A.rows(connection, A.PICK)


def test_an_open_pick_is_recorded_as_opinion_opens_no_belief_and_leaves_the_factor_open(tmp_path, monkeypatch):
    _vault, repository, factor_id, report = _pick(tmp_path, version=TAG, share=0.3, u=0.0, monkeypatch=monkeypatch)
    assert report["resolved"] is False and report["provisional_belief_id"] is None
    assert report["open_pick"] == {"variant": PK.OPEN, "propensity": pytest.approx(0.3)}
    assert repository.unresolved_cause_factor(factor_id)["status"] == "open"
    rows = _assignments(repository)
    assert [(row["unit_id"], row["variant"], row["propensity"]) for row in rows] == [(factor_id, PK.OPEN, 0.3)]
    assert rows[0]["seed"] == PK.seed_for(factor_id) and rows[0]["detail"]["eligibility"]["concrete"] is True
    with repository.connection() as connection:
        reports = connection.execute("SELECT response FROM causal_attribution_reports WHERE factor_id = ?",
                                     (factor_id,)).fetchall()
        section = PK.section(connection)
    assert [row[0] for row in reports] == ["believed_candidate"]
    assert section["assignments"] == {PK.OPEN: 1} and section["eligibility"] == {"assigned": 1}
    assert "conditional on being probed" in section["pick_probe_agreement"]["label"]
    assert "self-selected" in section["delayed_performance"]["label"]


def test_a_resolving_pick_resolves_as_before_with_its_arm_logged(tmp_path, monkeypatch):
    _vault, repository, factor_id, report = _pick(tmp_path, version=TAG, share=0.3, u=0.99, monkeypatch=monkeypatch)
    assert report["resolved"] is True and report["provisional_belief_id"] is not None
    assert report["open_pick"]["variant"] == PK.RESOLVE
    assert [(row["variant"], row["propensity"]) for row in _assignments(repository)] == [(PK.RESOLVE, pytest.approx(0.7))]


def test_below_the_tag_and_at_zero_nothing_is_assigned_and_the_pick_resolves(tmp_path):
    _v, below_repo, _f, below = _pick(tmp_path / "below", version=ROUTER_OBJECTIVE_ALGORITHM_VERSION)
    assert below["resolved"] is True and "open_pick" not in below and _assignments(below_repo) == []
    _v, zero_repo, _f, zero = _pick(tmp_path / "zero", version=TAG, share=0.0)
    assert zero["resolved"] is True and "open_pick" not in zero and _assignments(zero_repo) == []


def test_a_retry_reuses_the_factors_assignment(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    with repository.atomic(), repository.connection() as connection:
        first = PK.assign(connection, factor_id="f1", share=0.5, report_id="r1", at="2026-11-05T10:00:00Z",
                          eligibility={})
    with repository.atomic(), repository.connection() as connection:
        again = PK.assign(connection, factor_id="f1", share=0.5, report_id="r2", at="2026-11-05T10:01:00Z",
                          eligibility={})
    assert again["reused"] is True and again["variant"] == first["variant"] and again["id"] == first["id"]
    assert len(_assignments(repository)) == 1
