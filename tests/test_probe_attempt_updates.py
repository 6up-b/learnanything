from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.probes import enter_probe, record_probe_attempt
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def test_record_probe_attempt_increments_until_target(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    # No mastery row means no convergence; progress runs to the target of 3.
    record_probe_attempt(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    assert repository.probe_state("lo_svd_definition").probe_attempts_completed == 1
    assert repository.probe_state("lo_svd_definition").status == "in_progress"

    record_probe_attempt(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    record_probe_attempt(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    final = repository.probe_state("lo_svd_definition")
    assert final.probe_attempts_completed == 3
    assert final.status == "complete"
    assert final.completed_at is not None


def test_record_probe_attempt_completes_on_convergence(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    # Latent variance already below the convergence threshold (the mastery family
    # is pinned down). Convergence is read off the logit variance directly, not
    # the sigmoid-compressed display variance, so an uninformative P=1.0 must NOT
    # converge — see test_record_probe_attempt_does_not_converge_on_uninformative_prior.
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=0.05,
            evidence_count=4,
            last_evidence_at=NOW_ISO,
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    record_probe_attempt(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    state = repository.probe_state("lo_svd_definition")
    assert state.status == "complete"
    assert "mastery" in state.families_converged


def test_record_probe_attempt_does_not_converge_on_uninformative_prior(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    # P=1.0 is the initial, uninformative prior: display variance is ~0.0625
    # (below the 0.10 threshold) but the latent is wide open. The probe must keep
    # going to its attempt target rather than converging after one attempt.
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at=NOW_ISO,
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    record_probe_attempt(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    state = repository.probe_state("lo_svd_definition")
    assert state.status == "in_progress"
    assert state.families_converged == []


def test_record_probe_attempt_is_noop_when_not_probing(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    record_probe_attempt(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    assert repository.probe_state("lo_svd_definition") is None


def test_attempt_service_never_writes_legacy_probe_state(tmp_path):
    # Probe redesign Checkpoint 0: lo_probe_state is read-only legacy. The live
    # attempt pipeline routes through diagnostic episodes instead, and an
    # ordinary self-graded attempt can neither advance the frozen legacy phase
    # nor create a probe observation.
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    result = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="An answer."),
        SelfGradeInput(criterion_points={"correctness": 3}, confidence=4),
        clock=FrozenClock(NOW),
    )

    state = repository.probe_state("lo_svd_definition")
    assert state.probe_attempts_completed == 0
    assert state.status == "in_progress"  # untouched frozen legacy row
    assert repository.probe_observation_for_attempt(result.attempt_id) is None
