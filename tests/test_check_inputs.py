"""The committed check's two vault inputs (``daily_plan.check_inputs``): the availability predicate the lesson brief
already reads (shared, so ``delayed_check_words`` says the same words for the same inputs) and the dry minutes
estimate from the plan's own estimator. Fakes only; no model is called and nothing is written."""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from learnloop import delayed_checks as D
from learnloop import learner_protection as LP
from learnloop.ai import routing
from learnloop.daily_plan import check_inputs as CI
from learnloop.daily_plan import engine
from learnloop.daily_plan.estimates import DEFAULT_FEEDBACK_MINUTES, FALLBACK_PRIOR_MINUTES
from learnloop.db.repositories import Repository
from learnloop.teacher import te2 as T2
from learnloop.vault.loader import load_vault

from tests.teacher_fakes import build_teacher_vault

AS_OF = "2026-11-05T09:00:00Z"


def _attempt(repository, attempt_id: str, item: str, lo: str, at: str, latency: int = 120) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "latency_seconds, correctness, created_at) VALUES (?, ?, ?, 'short_answer', 'independent_attempt', ?, "
            "1.0, ?)", (attempt_id, item, lo, latency, at))
        connection.commit()


def _reveal(repository, item: str, lo: str) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, basis, "
            "created_at) VALUES (?, ?, ?, 'tutor_answer', 1.0, 'test', '2026-11-02T09:00:00Z')",
            (f"rv_{item}", item, lo))
        connection.commit()


@pytest.fixture
def vault(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    return SimpleNamespace(paths=paths, repository=repository, vault=load_vault(paths.root))


def _predecessor_words(vault, repository, lo: str, *, withheld, attempted) -> str:
    """``delayed_check_words`` as it was written before the predicate was shared (its rule, inline)."""

    found = D.candidates(vault, repository, lo, exclude=(), withheld=withheld, attempted=attempted,
                         revealed=D.revealed_items(repository, ""))
    return T2.UNSEEN_EXISTS if found else T2.UNSEEN_NONE


def test_the_brief_says_the_same_words_and_the_offer_reads_the_same_rule(vault):
    """Every case the candidate rule distinguishes: a fresh topic, one whose questions were all attempted, one whose
    last question was revealed, protection unreadable, a topic the vault does not hold, and the reserved exam item
    (withheld) beside two fresh ones."""

    v, repository = vault.vault, vault.repository
    _attempt(repository, "a1", "pi_det_1", "lo_det", "2026-11-02T09:00:00Z")
    words = {}
    for label, withheld, attempted, lo in (
            ("fresh", LP.withheld_items(v, repository), set(), "lo_eigen"),
            ("all attempted", LP.withheld_items(v, repository), {"pi_det_1", "pi_det_2"}, "lo_det"),
            ("one attempted", LP.withheld_items(v, repository), D.attempted_items(repository), "lo_det"),
            ("unreadable protection", LP.Withheld(available=False), set(), "lo_eigen"),
            ("unknown topic", LP.withheld_items(v, repository), set(), "lo_nowhere")):
        said = T2.delayed_check_words(v, repository, lo, withheld=withheld, attempted=attempted)
        assert said == _predecessor_words(v, repository, lo, withheld=withheld, attempted=attempted), label
        assert D.check_available(v, repository, lo, withheld=withheld, attempted=attempted) is (
            said == T2.UNSEEN_EXISTS), label
        words[label] = said
    assert words == {"fresh": T2.UNSEEN_EXISTS, "all attempted": T2.UNSEEN_NONE, "one attempted": T2.UNSEEN_EXISTS,
                     "unreadable protection": T2.UNSEEN_NONE, "unknown topic": T2.UNSEEN_NONE}
    # The offer's adapter reads the vault's own protection and attempts, through the same rule.
    assert CI.eligible_now(v, repository, "lo_eigen") is True
    assert CI.eligible_now(v, repository, "lo_det") is True
    _reveal(repository, "pi_det_2", "lo_det")
    assert CI.eligible_now(v, repository, "lo_det") is False
    assert T2.delayed_check_words(v, repository, "lo_det", withheld=LP.withheld_items(v, repository),
                                  attempted=D.attempted_items(repository)) == T2.UNSEEN_NONE


def test_the_offer_adapter_fails_closed(vault, monkeypatch):
    v, repository = vault.vault, vault.repository
    monkeypatch.setattr(LP, "withheld_items", lambda *_args: LP.Withheld(available=False))
    assert CI.eligible_now(v, repository, "lo_eigen") is False

    def unreadable(*_args):
        raise RuntimeError("protection metadata not readable")

    monkeypatch.setattr(LP, "withheld_items", unreadable)
    assert CI.eligible_now(v, repository, "lo_eigen") is False


def test_the_adapters_write_nothing_and_call_no_model(vault, monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("a model or provider was asked")

    for name in ("provider_for_task", "provider_for_operation", "client_for_provider"):
        monkeypatch.setattr(routing, name, refuse)
    path = vault.paths.sqlite_path
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    reader = Repository.attach(path, read_only=True)
    assert CI.eligible_now(vault.vault, reader, "lo_eigen") is True
    assert CI.dry_check_minutes(vault.vault, reader, "lo_eigen", as_of=AS_OF).basis == CI.ITEM_ESTIMATE
    assert T2.delayed_check_words(vault.vault, reader, "lo_eigen", withheld=LP.withheld_items(vault.vault, reader),
                                  attempted=D.attempted_items(reader)) == T2.UNSEEN_EXISTS
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def _plan_estimator(vault):
    """The plan's own estimator, built as the engine builds it for a plan (``engine._estimator``)."""

    return engine._estimator(SimpleNamespace(plan_config=vault.vault.config.plan, repository=vault.repository))


def test_the_minutes_are_the_plans_estimate_of_the_item_the_picker_would_choose(vault):
    """Mode evidence from the other topic's attempts moves the estimate off its prior; the dry estimate is the plan's
    four-decimal planning estimate of the picker's item, feedback included."""

    repository = vault.repository
    _attempt(repository, "a1", "pi_det_1", "lo_det", "2026-11-02T09:00:00Z", latency=300)
    _attempt(repository, "a2", "pi_det_2", "lo_det", "2026-11-03T09:00:00Z", latency=420)
    dry = CI.dry_check_minutes(vault.vault, repository, "lo_eigen", as_of=AS_OF)
    assert dry.basis == CI.ITEM_ESTIMATE and dry.item_id in {"pi_eig_1", "pi_eig_2", "pi_eig_3"}
    plan = _plan_estimator(vault)
    assert dry.minutes == plan.item_minutes(vault.vault, dry.item_id)
    estimate = plan.estimate(dry.item_id, "short_answer", None)
    assert estimate.n_mode == 2 and estimate.feedback_minutes == DEFAULT_FEEDBACK_MINUTES
    assert dry.minutes == round(estimate.answer_minutes + estimate.feedback_minutes, 4) != (
        FALLBACK_PRIOR_MINUTES + DEFAULT_FEEDBACK_MINUTES)
    assert dry.estimator_version == plan.version and dry.as_of == AS_OF
    # The picker's own choice, with no receipt written and no reservation.
    found = D.candidates(vault.vault, repository, "lo_eigen", exclude=(), withheld=LP.withheld_items(
        vault.vault, repository), attempted=D.attempted_items(repository), revealed=D.revealed_items(repository, ""))
    assert dry.item_id == D.pick_with_receipt(vault.vault, repository, found, seed_key="dry:lo_eigen")[0].id


def test_evidence_recorded_after_the_decision_is_not_read(vault):
    repository = vault.repository
    _attempt(repository, "a1", "pi_det_1", "lo_det", "2026-11-02T09:00:00Z", latency=300)
    at_decision = CI.dry_check_minutes(vault.vault, repository, "lo_eigen", as_of=AS_OF)
    _attempt(repository, "a2", "pi_det_2", "lo_det", "2026-11-07T09:00:00Z", latency=900)
    assert CI.dry_check_minutes(vault.vault, repository, "lo_eigen", as_of=AS_OF).minutes == at_decision.minutes
    later = CI.dry_check_minutes(vault.vault, repository, "lo_eigen", as_of="2026-11-08T09:00:00Z")
    assert later.minutes == _plan_estimator(vault).item_minutes(vault.vault, later.item_id) != at_decision.minutes


def test_with_no_candidate_the_estimators_unknown_item_estimate(vault):
    """Every question on the topic attempted: no item to price, so the estimator's estimate for an item it knows
    nothing about; with no duration history that is its answer prior plus its feedback prior."""

    repository = vault.repository
    for index, item in enumerate(("pi_det_1", "pi_det_2"), start=1):
        _attempt(repository, f"a{index}", item, "lo_det", "2026-11-02T09:00:00Z", latency=0)
    dry = CI.dry_check_minutes(vault.vault, repository, "lo_det", as_of=AS_OF)
    assert (dry.basis, dry.item_id) == (CI.UNKNOWN_ITEM_ESTIMATE, None)
    assert dry.minutes == FALLBACK_PRIOR_MINUTES + DEFAULT_FEEDBACK_MINUTES == round(
        _plan_estimator(vault).estimate("", None, None).minutes, 4)
