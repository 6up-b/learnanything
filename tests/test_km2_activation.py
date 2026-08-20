"""KM2 item 9 — atomic mvp-0.7 activation and mixed-version guards."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.ops.vault_upgrade import (
    KM_ALGORITHM_VERSION,
    upgrade_to_mvp07,
    validate_mvp07_readiness,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml
from learnloop_sidecar.context import SidecarContext

from tests.helpers import NOW, create_basic_vault, set_algorithm_version, write_facets


def test_upgrade_refuses_when_facets_unregistered(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    # pi_svd_define_001 declares facet 'recall' but the registry is empty.
    result = upgrade_to_mvp07(paths.root)
    assert result.upgraded is False
    assert any("recall" in p for p in result.problems)
    # The version field was NOT flipped.
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.6"


def test_upgrade_succeeds_when_registry_complete(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD recall definition."}],
    )
    result = upgrade_to_mvp07(paths.root)
    assert result.upgraded is True
    assert result.to_version == KM_ALGORITHM_VERSION
    assert load_vault(paths.root).config.algorithms.algorithm_version == KM_ALGORITHM_VERSION


def test_upgrade_projects_existing_attempts_into_canonical_facet_state(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD factors a matrix into U, Sigma, and V transpose.",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=clock,
    )
    assert repository.canonical_facet_recall_states() == []

    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD recall definition."}],
    )
    result = upgrade_to_mvp07(paths.root, clock=clock)

    assert result.upgraded is True
    rows = repository.canonical_facet_recall_states()
    assert any(row.facet_id == "recall" and row.practice_item_id is None for row in rows)
    assert sum(row.independent_evidence_mass for row in rows) > 0
    assert any(cell.facet_id == "recall" for cell in repository.facet_capability_evidence_all())


def test_app_load_repairs_vault_activated_by_old_upgrade(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="U Sigma V transpose."),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=clock,
    )
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD recall definition."}],
    )
    # This is the state left by the old upgrader: new version on disk, raw
    # attempts intact, but no canonical projection for the knowledge field.
    set_algorithm_version(paths, KM_ALGORITHM_VERSION)
    assert repository.canonical_facet_recall_states() == []

    context = SidecarContext()
    context.load(paths.root, maintenance=False)

    assert any(row.facet_id == "recall" for row in repository.canonical_facet_recall_states())


def test_upgrade_is_idempotent(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD recall definition."}],
    )
    upgrade_to_mvp07(paths.root)
    second = upgrade_to_mvp07(paths.root)
    assert second.upgraded is False
    assert "already mvp-0.7" in " ".join(second.problems)


def test_upgrade_refuses_from_unknown_version(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_facets(
        paths,
        [{"id": "recall", "kind": "definition", "claim": "SVD recall definition."}],
    )
    set_algorithm_version(paths, "mvp-0.5")
    result = upgrade_to_mvp07(paths.root)
    assert result.upgraded is False
    assert any("mvp-0.5" in p for p in result.problems)


def test_validate_readiness_flags_incomplete_contract(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    # Registered id but no claim/kind -> incomplete semantic contract.
    write_yaml(paths.facets_path, {"schema_version": 2, "facets": [{"id": "recall"}]})
    problems = validate_mvp07_readiness(load_vault(paths.root))
    assert any("incomplete semantic contract" in p for p in problems)
