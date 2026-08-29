from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.substrate.canonical_projection import CANONICAL_PROJECTION_VERSION
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext

from tests.helpers import NOW, create_basic_vault, set_algorithm_version


def _projection_vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _rebuild_count(repository: Repository) -> int:
    with repository.connection() as connection:
        return int(
            connection.execute(
                "SELECT COUNT(*) FROM derived_state_rebuilds"
            ).fetchone()[0]
        )


def test_fresh_startup_stamps_a_silent_projection_baseline_once(tmp_path):
    paths, _vault, repository = _projection_vault(tmp_path)
    context = SidecarContext()

    context.load(paths.root, maintenance=False)

    marker = repository.latest_canonical_projection_rebuild()
    assert marker is not None
    assert marker["scope"] == "canonical_projection_startup"
    assert marker["canonical_projection_version"] == CANONICAL_PROJECTION_VERSION
    assert marker["replayed_attempts"] == 0
    assert repository.derived_state_rebuild_version_changes() == []

    context.reload(maintenance=False)
    assert _rebuild_count(repository) == 1


def test_projection_upgrade_stays_silent_while_vault_has_no_attempts(tmp_path):
    paths, _vault, repository = _projection_vault(tmp_path)
    repository.record_derived_state_rebuild(
        scope="canonical_projection_startup",
        learning_object_ids=[],
        algorithm_version="mvp-0.7",
        rebuilt_learning_objects=0,
        replayed_attempts=0,
        canonical_projection_version="canonical_projection_previous",
        clock=FrozenClock(NOW),
    )

    context = SidecarContext()
    context.load(paths.root, maintenance=False)

    marker = repository.latest_canonical_projection_rebuild()
    assert marker is not None
    assert marker["canonical_projection_version"] == CANONICAL_PROJECTION_VERSION
    assert _rebuild_count(repository) == 2
    assert repository.derived_state_rebuild_version_changes() == []


def test_startup_records_one_recalibration_for_an_unstamped_practised_vault(
    tmp_path,
):
    paths, vault, repository = _projection_vault(tmp_path)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="A = U Sigma V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(
            criterion_points={"correctness": 4},
            fatal_errors=[],
            confidence=4,
        ),
        clock=FrozenClock(NOW),
    )
    assert repository.latest_canonical_projection_rebuild() is None

    context = SidecarContext()
    context.load(paths.root, maintenance=False)

    marker = repository.latest_canonical_projection_rebuild()
    assert marker is not None
    assert marker["canonical_projection_version"] == CANONICAL_PROJECTION_VERSION
    assert marker["replayed_attempts"] == 1
    assert len(repository.derived_state_rebuild_version_changes()) == 1

    # A narrow marker that does not report projection semantics is not a
    # rollback, and neither it nor the following reload may mint a phantom
    # second recalibration.
    repository.record_derived_state_rebuild(
        scope="activity_card_state",
        learning_object_ids=[],
        algorithm_version="mvp-0.7",
        rebuilt_learning_objects=0,
        replayed_attempts=0,
    )
    context.reload(maintenance=False)
    assert _rebuild_count(repository) == 2
    assert len(repository.derived_state_rebuild_version_changes()) == 1
