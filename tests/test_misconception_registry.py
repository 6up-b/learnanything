"""Phase 2 registry normalization, hypothesis rekeying, EIG, and resolution.

Covers spec_misconception_diagnostics.md §2.2 (normalization), §3 (hypothesis
set / discrimination-aware EIG), and §7 (posterior update & resolution rekeying).
"""

from __future__ import annotations

from tests.structured_ai import StructuredClientFake

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import ItemMisconceptionDiscrimination, Repository
from learnloop.ids import new_ulid
from learnloop.diagnosis.misconceptions import (
    misconception_posterior,
    normalize_attempt_misconceptions,
    update_misconception_posteriors_and_resolve,
)
from learnloop.diagnosis.probes import (
    Hypothesis,
    HypothesisSet,
    build_hypothesis_set,
    expected_information_gain,
    item_registry_discrimination,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, add_followup_item, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CONCEPT_ID = "singular_value_decomposition"


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault, repository


def _iso(minutes: int) -> str:
    return (NOW + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _insert_mc_event(
    repository: Repository,
    *,
    attempt_id: str,
    event_id: str,
    statement: str | None,
    severity: float = 0.7,
    facets: list[str] | None = None,
    consistent: str | None = None,
    minutes: int = 0,
) -> None:
    repository.insert_error_event(
        {
            "id": event_id,
            "attempt_id": attempt_id,
            "learning_object_id": LO_ID,
            "error_type": "conceptual_slip",
            "severity": severity,
            "is_misconception": True,
            "misconception_statement": statement,
            "misconception_consistent_answer": consistent,
            "repair_plan": {"target_evidence_families": facets} if facets else None,
            "status": "active",
            "created_at": _iso(minutes),
            "updated_at": _iso(minutes),
        }
    )


def _insert_attempt(
    repository: Repository,
    *,
    attempt_id: str,
    minutes: int,
    item_id: str = ITEM_ID,
    correctness: float = 1.0,
    fired_mc_id: str | None = None,
    primed: bool = False,
) -> None:
    repository.insert_practice_attempt(
        {
            "id": attempt_id,
            "practice_item_id": item_id,
            "learning_object_id": LO_ID,
            "practice_mode": "short_answer",
            "attempt_type": "independent_attempt",
            "rubric_score": 4 if correctness >= 1.0 else 1,
            "correctness": correctness,
            "error_type": "conceptual_slip" if fired_mc_id else None,
            "primed": primed,
            "created_at": _iso(minutes),
            "updated_at": _iso(minutes),
        }
    )
    if fired_mc_id is not None:
        repository.insert_error_event(
            {
                "id": f"err_{attempt_id}",
                "attempt_id": attempt_id,
                "learning_object_id": LO_ID,
                "error_type": "conceptual_slip",
                "severity": 0.7,
                "is_misconception": True,
                "misconception_id": fired_mc_id,
                "status": "active",
                "created_at": _iso(minutes),
                "updated_at": _iso(minutes),
            }
        )


def _discrimination(mc_id: str, *, item_id: str = ITEM_ID) -> ItemMisconceptionDiscrimination:
    # sens_mean = 9/10 = 0.9, spec_mean = 19/20 = 0.95.
    return ItemMisconceptionDiscrimination(
        practice_item_id=item_id,
        misconception_id=mc_id,
        sensitivity_alpha=9.0,
        sensitivity_beta=1.0,
        specificity_alpha=19.0,
        specificity_beta=1.0,
        n_planted_trials=10,
        n_clean_trials=20,
        source="sim",
        updated_at=NOW_ISO,
    )


# -- §2.2 normalization -----------------------------------------------------


def test_normalization_creates_row_with_provenance(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_mc_event(
        repository,
        attempt_id="att1",
        event_id="ev1",
        statement="believes Q maps standard vectors to eigenbasis coefficients",
        facets=["recall"],
        consistent="applies Q instead of Q^T",
    )

    touched = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, clock=FrozenClock(NOW)
    )

    assert len(touched) == 1
    record = repository.misconception(touched[0])
    assert record is not None
    assert record.statement == "believes Q maps standard vectors to eigenbasis coefficients"
    assert record.facet_ids == ["recall"]
    assert record.signature == "applies Q instead of Q^T"
    assert record.concept_id == CONCEPT_ID
    assert record.source_error_event_ids == ["ev1"]
    assert record.severity == pytest.approx(0.7)
    # error event links back to the registry row.
    linked = repository.error_events_for_attempt("att1")[0]
    assert linked["misconception_id"] == touched[0]


def test_normalization_dedupes_by_normalized_statement(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_mc_event(repository, attempt_id="att1", event_id="ev1", statement="Reverses Q and Q^T.", severity=0.6)
    first = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, clock=FrozenClock(NOW)
    )
    # A second attempt with the same belief (different punctuation/case) merges.
    _insert_mc_event(
        repository,
        attempt_id="att2",
        event_id="ev2",
        statement="reverses q and q t",
        severity=0.9,
        minutes=5,
    )
    second = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att2", learning_object_id=LO_ID, clock=FrozenClock(NOW + timedelta(minutes=5))
    )

    assert first == second  # same registry id
    record = repository.misconception(first[0])
    assert record.severity == pytest.approx(0.9)  # max over sources
    assert set(record.source_error_event_ids) == {"ev1", "ev2"}
    assert len(repository.misconceptions_for_learning_object(LO_ID)) == 1


def test_normalization_reactivates_resolved_row(tmp_path):
    vault, repository = _setup(tmp_path)
    mc_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="reverses q and q t",
        concept_id=CONCEPT_ID,
        severity=0.6,
        status="resolved",
        clock=FrozenClock(NOW),
    )
    _insert_mc_event(repository, attempt_id="att1", event_id="ev1", statement="Reverses Q and Q^T.", minutes=5)

    touched = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, clock=FrozenClock(NOW + timedelta(minutes=5))
    )

    assert touched == [mc_id]
    assert repository.misconception(mc_id).status == "active"


def test_statementless_events_create_nothing(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_mc_event(repository, attempt_id="att1", event_id="ev1", statement=None)

    touched = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, clock=FrozenClock(NOW)
    )

    assert touched == []
    assert repository.misconceptions_for_learning_object(LO_ID) == []
    assert repository.error_events_for_attempt("att1")[0]["misconception_id"] is None


def test_normalization_is_idempotent(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_mc_event(repository, attempt_id="att1", event_id="ev1", statement="Reverses Q and Q^T.")
    normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, clock=FrozenClock(NOW)
    )
    second = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, clock=FrozenClock(NOW)
    )
    assert second == []
    assert len(repository.misconceptions_for_learning_object(LO_ID)) == 1


class _FakeMatch:
    def __init__(self, decision: str, misconception_id: str | None = None):
        self.decision = decision
        self.misconception_id = misconception_id


class _FakeClient(StructuredClientFake):
    def __init__(self, result: _FakeMatch):
        self._result = result
        self.calls = 0

    def run_misconception_match(self, context):
        self.calls += 1
        return self._result


def test_llm_match_same_merges(tmp_path):
    vault, repository = _setup(tmp_path)
    mc_id = repository.insert_misconception(
        learning_object_id=LO_ID, statement="an existing belief", concept_id=CONCEPT_ID, severity=0.5,
        clock=FrozenClock(NOW),
    )
    _insert_mc_event(
        repository, attempt_id="att1", event_id="ev1", statement="a totally different phrasing", severity=0.8
    )
    client = _FakeClient(_FakeMatch("same", mc_id))

    touched = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, ai_client=client, clock=FrozenClock(NOW)
    )

    assert client.calls == 1
    assert touched == [mc_id]
    assert len(repository.misconceptions_for_learning_object(LO_ID)) == 1
    assert repository.misconception(mc_id).severity == pytest.approx(0.8)


def test_llm_match_new_inserts_over_text_match(tmp_path):
    vault, repository = _setup(tmp_path)
    repository.insert_misconception(
        learning_object_id=LO_ID, statement="reverses q and q t", concept_id=CONCEPT_ID, severity=0.5,
        clock=FrozenClock(NOW),
    )
    # Text would match, but the LLM says these are distinct beliefs.
    _insert_mc_event(repository, attempt_id="att1", event_id="ev1", statement="Reverses Q and Q^T.")
    client = _FakeClient(_FakeMatch("new"))

    touched = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, ai_client=client, clock=FrozenClock(NOW)
    )

    assert client.calls == 1
    assert len(repository.misconceptions_for_learning_object(LO_ID)) == 2
    assert touched[0] not in {r.id for r in repository.misconceptions_for_learning_object(LO_ID) if r.severity == 0.5}


# -- §3 hypothesis set ------------------------------------------------------


def _registry_row(repository, statement: str, *, severity: float = 0.7) -> str:
    return repository.insert_misconception(
        learning_object_id=LO_ID,
        statement=statement,
        concept_id=CONCEPT_ID,
        severity=severity,
        clock=FrozenClock(NOW),
    )


def test_build_hypothesis_set_registry_and_legacy_coexist(tmp_path):
    vault, repository = _setup(tmp_path)
    mc_a = _registry_row(repository, "belief A", severity=0.8)
    mc_b = _registry_row(repository, "belief B", severity=0.75)
    # Legacy misconception event with no registry link.
    repository.insert_error_event(
        {
            "id": "legacy1",
            "learning_object_id": LO_ID,
            "error_type": "conceptual_slip",
            "severity": 0.6,
            "is_misconception": True,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )

    hset = build_hypothesis_set(vault, repository, LO_ID, clock=FrozenClock(NOW))
    labels = {h.label for h in hset.hypotheses}

    assert f"misconception:{mc_a}" in labels
    assert f"misconception:{mc_b}" in labels
    assert "misconception:conceptual_slip" in labels
    registry = [h for h in hset.hypotheses if h.misconception_id is not None]
    assert {h.misconception_id for h in registry} == {mc_a, mc_b}
    assert sum(hset.prior.values()) == pytest.approx(1.0)


def test_build_hypothesis_set_skips_linked_legacy_event(tmp_path):
    vault, repository = _setup(tmp_path)
    mc_a = _registry_row(repository, "belief A")
    repository.insert_error_event(
        {
            "id": "linked1",
            "learning_object_id": LO_ID,
            "error_type": "conceptual_slip",
            "severity": 0.6,
            "is_misconception": True,
            "misconception_id": mc_a,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )
    hset = build_hypothesis_set(vault, repository, LO_ID, clock=FrozenClock(NOW))
    # Only the registry hypothesis, not a duplicate legacy error-type hypothesis.
    assert "misconception:conceptual_slip" not in {h.label for h in hset.hypotheses}
    assert f"misconception:{mc_a}" in {h.label for h in hset.hypotheses}


# -- §3 discrimination-aware EIG -------------------------------------------


def _registry_hypothesis_set(mc_id: str) -> HypothesisSet:
    hypotheses = [
        Hypothesis(label="mastered", severity_at_entry=0.5),
        Hypothesis(label="unfamiliar", severity_at_entry=0.5),
        Hypothesis(label=f"misconception:{mc_id}", misconception_id=mc_id, severity_at_entry=0.7),
    ]
    prior = {"mastered": 0.34, "unfamiliar": 0.33, f"misconception:{mc_id}": 0.33}
    return HypothesisSet(learning_object_id=LO_ID, hypotheses=hypotheses, prior=prior)


def test_discriminating_item_has_higher_eig(tmp_path):
    vault, repository = _setup(tmp_path)
    mc_id = new_ulid()
    hset = _registry_hypothesis_set(mc_id)
    item = vault.practice_items[ITEM_ID]
    disc = {mc_id: _discrimination(mc_id)}

    eig_discriminating = expected_information_gain(
        hset, item, discrimination=disc, discriminated_ids={mc_id}
    )
    eig_plain = expected_information_gain(hset, item)

    assert eig_discriminating > eig_plain
    assert eig_discriminating > 0.0


def test_item_registry_discrimination_reads_rows(tmp_path):
    vault, repository = _setup(tmp_path)
    mc_id = _registry_row(repository, "belief A")
    repository.upsert_item_misconception_discrimination(_discrimination(mc_id))
    hset = _registry_hypothesis_set(mc_id)
    item = vault.practice_items[ITEM_ID]

    rows, discriminated = item_registry_discrimination(
        repository, vault, item, vault.rubric_for_item(item), hset
    )
    assert discriminated == {mc_id}
    assert rows[mc_id].sensitivity_mean == pytest.approx(0.9)


# -- §7 posterior & resolution ---------------------------------------------


def test_clean_discriminating_attempts_resolve(tmp_path):
    vault, repository = _setup(tmp_path)
    mc_id = _registry_row(repository, "belief A", severity=0.7)
    repository.upsert_item_misconception_discrimination(_discrimination(mc_id))
    _insert_attempt(repository, attempt_id="clean1", minutes=1)
    _insert_attempt(repository, attempt_id="clean2", minutes=2)

    resolved = update_misconception_posteriors_and_resolve(
        vault, repository, learning_object_id=LO_ID, clock=FrozenClock(NOW + timedelta(minutes=3))
    )

    assert mc_id in resolved
    assert repository.misconception(mc_id).status == "resolved"


def test_clean_non_discriminating_attempts_do_not_resolve(tmp_path):
    vault, repository = _setup(tmp_path)
    add_followup_item(vault.root)  # pi_svd_define_002, no discrimination row
    vault = load_vault(vault.root)
    mc_id = _registry_row(repository, "belief A", severity=0.7)
    repository.upsert_item_misconception_discrimination(_discrimination(mc_id))
    _insert_attempt(repository, attempt_id="clean1", minutes=1, item_id="pi_svd_define_002")
    _insert_attempt(repository, attempt_id="clean2", minutes=2, item_id="pi_svd_define_002")

    resolved = update_misconception_posteriors_and_resolve(
        vault, repository, learning_object_id=LO_ID, clock=FrozenClock(NOW + timedelta(minutes=3))
    )

    assert resolved == []
    assert repository.misconception(mc_id).status == "active"


def test_primed_attempts_do_not_resolve_a_misconception(tmp_path):
    """mvp-0.9 admissibility. A primed non-firing attempt is not evidence.

    The learner was shown the repair and then retried. Not firing is what the
    priming was FOR; reading it as evidence the belief is gone lets a single
    primed redo close a durable misconception. Two of them used to be enough.
    """

    vault, repository = _setup(tmp_path)
    mc_id = _registry_row(repository, "belief A", severity=0.7)
    repository.upsert_item_misconception_discrimination(_discrimination(mc_id))
    _insert_attempt(repository, attempt_id="primed1", minutes=1, primed=True)
    _insert_attempt(repository, attempt_id="primed2", minutes=2, primed=True)

    before = misconception_posterior(vault, repository, repository.misconception(mc_id))
    assert before == pytest.approx(0.7)

    resolved = update_misconception_posteriors_and_resolve(
        vault,
        repository,
        learning_object_id=LO_ID,
        clock=FrozenClock(NOW + timedelta(minutes=3)),
    )
    assert resolved == []
    assert repository.misconception(mc_id).status == "active"


def test_a_primed_attempt_that_fires_anyway_still_counts_against_the_learner(
    tmp_path,
):
    """The exclusion is one-directional, and deliberately so.

    A belief that asserts itself DESPITE the correction is stronger evidence
    than an unprimed firing, not weaker — so the firing branch is untouched.
    """

    vault, repository = _setup(tmp_path)
    mc_id = _registry_row(repository, "belief A", severity=0.3)
    repository.upsert_item_misconception_discrimination(_discrimination(mc_id))
    _insert_attempt(
        repository,
        attempt_id="primed_fire",
        minutes=1,
        correctness=0.0,
        fired_mc_id=mc_id,
        primed=True,
    )

    posterior = misconception_posterior(
        vault, repository, repository.misconception(mc_id)
    )
    assert posterior > 0.3


def test_fired_keyed_fatal_raises_posterior(tmp_path):
    vault, repository = _setup(tmp_path)
    mc_id = _registry_row(repository, "belief A", severity=0.3)
    repository.upsert_item_misconception_discrimination(_discrimination(mc_id))
    # One clean attempt would push it down; a fired keyed fatal keeps it active.
    _insert_attempt(repository, attempt_id="clean1", minutes=1)
    _insert_attempt(repository, attempt_id="fired1", minutes=2, correctness=0.25, fired_mc_id=mc_id)

    resolved = update_misconception_posteriors_and_resolve(
        vault, repository, learning_object_id=LO_ID, clock=FrozenClock(NOW + timedelta(minutes=3))
    )

    assert resolved == []
    assert repository.misconception(mc_id).status == "active"


def test_resolution_reactivates_when_posterior_climbs(tmp_path):
    vault, repository = _setup(tmp_path)
    mc_id = _registry_row(repository, "belief A", severity=0.7)
    repository.update_misconception(mc_id, status="resolved", clock=FrozenClock(NOW))
    repository.upsert_item_misconception_discrimination(_discrimination(mc_id))
    _insert_attempt(repository, attempt_id="fired1", minutes=2, correctness=0.25, fired_mc_id=mc_id)

    update_misconception_posteriors_and_resolve(
        vault, repository, learning_object_id=LO_ID, clock=FrozenClock(NOW + timedelta(minutes=3))
    )

    assert repository.misconception(mc_id).status == "active"
