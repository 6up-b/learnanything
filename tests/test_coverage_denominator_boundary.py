"""Measurement §5.2 / A6: the coverage-denominator recalibration boundary.

A vault-content edit that removes contract cells shrinks the coverage denominator,
which drives the mastery variance floor — so displayed mastery moves with **no new
evidence**. A6's argument is that a silent change to a claim the learner has
already seen is the failure mode, so this must surface as exactly one honest
"estimates recomputed, your evidence unchanged" entry.

The version is content-addressed on the effective `(LO, facet, capability)`
frontier rather than on the authored YAML, which is what buys the two properties
tested here: a rerun or a later ordinary rebuild emits nothing, and a real cell
change emits exactly once.
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.learner.facet_diagnostics import (
    COVERAGE_DENOMINATOR_SEMANTICS,
    coverage_denominator_version,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, create_basic_vault, set_algorithm_version


def _declare_integration(paths, *, cells, integration=None) -> None:
    """Give the LO a recipe with `all_of` cells and an optional integration."""

    path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
    payload = read_yaml(path)
    recipe = {
        "id": "recipe_svd",
        "composition": "conjunctive",
        "all_of": [
            {"facet": facet, "capability": capability, "modality": "hard"}
            for facet, capability in cells
        ],
    }
    if integration is not None:
        recipe["integration"] = {
            "facet": integration[0],
            "capability": integration[1],
            "modality": "hard",
        }
    payload["blueprints"] = [{"id": "bp_svd", "weight": 1.0, "recipes": [recipe]}]
    write_yaml(path, payload)


def _canonical_vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    return paths


def test_version_is_semantics_plus_frontier_hash(tmp_path):
    paths = _canonical_vault(tmp_path)
    _declare_integration(paths, cells=[("recall", "retrieval")])
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    version = coverage_denominator_version(vault, repository)
    assert version.startswith(f"{COVERAGE_DENOMINATOR_SEMANTICS}:")
    # Stable across recomputation — it is a function of the frontier, not of the
    # clock, the row set, or file mtimes.
    assert version == coverage_denominator_version(vault, repository)


def test_removing_a_cell_changes_the_version(tmp_path):
    paths = _canonical_vault(tmp_path)
    _declare_integration(
        paths, cells=[("recall", "retrieval")], integration=("assembly", "coordination")
    )
    before = coverage_denominator_version(
        load_vault(paths.root), Repository(paths.sqlite_path)
    )

    # Drop the integration component: one fewer cell in the denominator.
    _declare_integration(paths, cells=[("recall", "retrieval")])
    after = coverage_denominator_version(
        load_vault(paths.root), Repository(paths.sqlite_path)
    )
    assert before != after


def test_a_comment_or_timestamp_touch_does_not_change_the_version(tmp_path):
    """Hashing the YAML would mint a phantom boundary here and narrate a
    recalibration that did not happen."""

    paths = _canonical_vault(tmp_path)
    _declare_integration(paths, cells=[("recall", "retrieval")])
    repository = Repository(paths.sqlite_path)
    before = coverage_denominator_version(load_vault(paths.root), repository)

    path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
    payload = read_yaml(path)
    payload["updated_at"] = "2030-01-01T00:00:00Z"
    write_yaml(path, payload)

    assert coverage_denominator_version(load_vault(paths.root), repository) == before


def test_legacy_vault_hashes_the_empty_frontier(tmp_path):
    """An LO with no authored blueprint components keeps the legacy denominator,
    so it must never contribute a boundary."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    empty = coverage_denominator_version(vault, repository)
    paths_two = create_basic_vault(tmp_path / "vault_two")
    assert (
        coverage_denominator_version(
            load_vault(paths_two.root), Repository(paths_two.sqlite_path)
        )
        == empty
    )


def test_a_null_version_is_not_reported_not_a_rollback(tmp_path):
    """A writer that does not stamp the column must not create phantom
    boundaries. Comparing NULL as a real value would emit one entry when the
    stamped rebuild lands and another on the next unstamped one."""

    paths = _canonical_vault(tmp_path)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    version = f"{COVERAGE_DENOMINATOR_SEMANTICS}:deadbeefdeadbeef"
    common = {
        "scope": "all",
        "learning_object_ids": ["lo_svd_definition"],
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "rebuilt_learning_objects": 1,
        "replayed_attempts": 3,
        "canonical_projection_version": "canonical_projection_v4_item_declared_capability",
        "clock": FrozenClock(NOW),
    }
    # stamped -> unstamped -> unstamped: exactly one boundary, at the first row.
    repository.record_derived_state_rebuild(
        **common, coverage_denominator_version=version
    )
    repository.record_derived_state_rebuild(**common)
    repository.record_derived_state_rebuild(**common)

    boundaries = [
        change
        for change in repository.derived_state_rebuild_version_changes()
        if change.get("coverage_denominator_version") == version
    ]
    assert len(boundaries) == 1


def test_dry_run_writes_no_boundary(tmp_path):
    from learnloop.curriculum.integration_backfill import (
        COORDINATION,
        apply_integration_backfill_and_recalibrate,
        plan_integration_backfill,
    )

    paths = _canonical_vault(tmp_path)
    _declare_integration(
        paths,
        cells=[("recall", "retrieval"), ("apply_it", "procedure_execution")],
        integration=("recall", "coordination"),
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    report = plan_integration_backfill(vault, capabilities=[COORDINATION])
    assert report.verdicts, "fixture must produce at least one verdict to judge"

    result = apply_integration_backfill_and_recalibrate(
        vault, repository, report.verdicts, dry_run=True, clock=FrozenClock(NOW)
    )
    assert result.rebuild_marker_id is None
    assert result.coverage_denominator_version is None
    assert repository.derived_state_rebuild_version_changes() == []


def test_apply_writes_one_boundary_and_a_rerun_writes_none(tmp_path):
    from learnloop.curriculum.integration_backfill import (
        COORDINATION,
        apply_integration_backfill_and_recalibrate,
        plan_integration_backfill,
    )
    from learnloop.attempts.attempts import (
        AttemptDraft,
        SelfGradeInput,
        complete_self_graded_attempt,
    )
    from learnloop.learner.learner_review_feed import build_learner_review_feed
    from learnloop.substrate.replay import rebuild_derived_state

    paths = _canonical_vault(tmp_path)
    _declare_integration(
        paths,
        cells=[("recall", "retrieval"), ("apply_it", "procedure_execution")],
        integration=("recall", "coordination"),
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    # The learner must have history: a rebuild that recomputes nothing the learner
    # ever saw is housekeeping, and the reader correctly stays silent for it. The
    # case A6 cares about is exactly this one — an estimate they have already been
    # shown moving without new evidence.
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_001", "U Sigma V^T"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )
    report = plan_integration_backfill(vault, capabilities=[COORDINATION])

    applied = apply_integration_backfill_and_recalibrate(
        vault, repository, report.verdicts, dry_run=False, clock=FrozenClock(NOW)
    )
    assert applied.edits
    assert applied.rebuild_marker_id is not None
    first_version = applied.coverage_denominator_version
    assert first_version is not None

    recalibrations = [
        entry
        for entry in build_learner_review_feed(load_vault(paths.root), repository)[
            "changelog"
        ]
        if entry["kind"] == "recalibration"
    ]
    assert len(recalibrations) == 1
    assert recalibrations[0]["coverage_denominator_version"] == first_version

    # A rerun of the backfill: the verdicts are already applied, so nothing
    # changes content and no second boundary is written.
    reloaded = load_vault(paths.root)
    rerun = apply_integration_backfill_and_recalibrate(
        reloaded,
        repository,
        plan_integration_backfill(reloaded, capabilities=[COORDINATION]).verdicts,
        dry_run=False,
        clock=FrozenClock(NOW),
    )
    assert rerun.edits == ()

    # And an ordinary rebuild afterwards re-stamps the SAME content-addressed
    # version, so it is not a boundary either.
    rebuild_derived_state(reloaded, repository, clock=FrozenClock(NOW))
    still_one = [
        entry
        for entry in build_learner_review_feed(reloaded, repository)["changelog"]
        if entry["kind"] == "recalibration"
    ]
    assert len(still_one) == 1
