"""B7 coverage rollup (spec §4.11): buckets are mutually exclusive, sum to the
facet universe, and pooled demonstration outranks the no-supply debt bucket."""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.services.coverage_rollup import coverage_rollup
from learnloop.vault.loader import load_vault
from learnloop.vault.models import SourceSet

from tests.helpers import NOW_ISO, create_basic_vault
from tests.test_goal_decay_projection import _add_application_item


def _source_set() -> SourceSet:
    return SourceSet(id="set_svd", subject_id="linear-algebra", title="SVD sources")


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_application_item(vault_root)  # second facet: application
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault, repository


def _bank_credit(repository, facet_id, credit=0.5):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO facet_capability_evidence(
              facet_id, capability, certification_credit,
              independent_surface_groups_json, algorithm_version,
              created_at, updated_at
            ) VALUES (?, 'retrieval', ?, '["g1"]', 'mvp-0.7', ?, ?)
            """,
            (facet_id, credit, NOW_ISO, NOW_ISO),
        )
        connection.commit()


def _deactivate(repository, item_id):
    repository.upsert_practice_item_state(item_id, active=False)


def test_buckets_are_mutually_exclusive_and_sum_to_facet_count(tmp_path):
    vault, repository = _setup(tmp_path)
    _bank_credit(repository, "recall")

    rollup = coverage_rollup(vault, repository, _source_set())
    buckets = rollup["buckets"]
    assert rollup["total"] == 2
    assert sum(bucket["count"] for bucket in buckets.values()) == rollup["total"]
    all_ids = [
        facet_id for bucket in buckets.values() for facet_id in bucket["facet_ids"]
    ]
    assert len(all_ids) == len(set(all_ids)), "a facet may appear in exactly one bucket"
    assert buckets["demonstrated"]["facet_ids"] == ["recall"]
    assert buckets["assessed"]["facet_ids"] == ["application"]
    assert buckets["no_practice_supply"]["count"] == 0


def test_facet_without_active_supply_is_the_system_debt_bucket(tmp_path):
    vault, repository = _setup(tmp_path)
    _deactivate(repository, "pi_svd_apply_001")

    rollup = coverage_rollup(vault, repository, _source_set())
    buckets = rollup["buckets"]
    # attempts_to_certify is None for 'application' (no active supporting
    # items): with no evidence either, it is the system's debt, not the
    # learner's gap.
    assert buckets["no_practice_supply"]["facet_ids"] == ["application"]
    assert buckets["assessed"]["facet_ids"] == ["recall"]
    assert sum(bucket["count"] for bucket in buckets.values()) == rollup["total"] == 2


def test_pooled_demonstration_outranks_no_supply(tmp_path):
    """The overlap case: demonstrated via pooled/embedded evidence while the
    facet has no local practice supply (attempts_to_certify = None). Explicit
    precedence must land it in 'demonstrated', never double-count it as debt."""

    vault, repository = _setup(tmp_path)
    _deactivate(repository, "pi_svd_apply_001")
    _bank_credit(repository, "application")

    rollup = coverage_rollup(vault, repository, _source_set())
    buckets = rollup["buckets"]
    assert buckets["demonstrated"]["facet_ids"] == ["application"]
    assert buckets["no_practice_supply"]["count"] == 0
    assert buckets["assessed"]["facet_ids"] == ["recall"]
    assert sum(bucket["count"] for bucket in buckets.values()) == rollup["total"] == 2
