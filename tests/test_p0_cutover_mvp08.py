"""P0.5 compatibility cutover (spec §7.2, §9.6 bullets 1-3).

upgrade_to_mvp08 in the shape of upgrade_to_mvp07: freeze the mvp-0.6/mvp-0.7
registry manifests, flip the default read path to the mvp-0.8 authority-propagation
projection, record a derived_state_rebuilds receipt, and never rewrite raw history.
"""

from __future__ import annotations

import json

from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.services import parameter_registry as pr
from learnloop.services.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.services.vault_upgrade import (
    COMPATIBILITY_DELTA_FILENAME,
    compatibility_projection_delta,
    upgrade_to_mvp08,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, set_algorithm_version

CLOCK = FrozenClock(NOW)
ITEM = "pi_svd_define_001"


def _mvp07_vault(tmp_path):
    """A fresh mvp-0.7 vault COPY (never a fixture in place) ready to cut over."""

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    return paths, vault, repo


def test_upgrade_to_mvp08_flips_and_records_receipt(tmp_path):
    paths, _vault, repo = _mvp07_vault(tmp_path)
    result = upgrade_to_mvp08(paths.root, clock=CLOCK)
    assert result.upgraded
    assert result.from_version == "mvp-0.7"
    assert result.to_version == "mvp-0.8"

    reloaded = load_vault(paths.root)
    assert reloaded.config.algorithms.algorithm_version == "mvp-0.8"

    latest = repo.latest_derived_state_rebuild()
    assert latest is not None
    assert latest["algorithm_version"] == "mvp-0.8"


def test_upgrade_freezes_legacy_manifests_immutably(tmp_path):
    paths, _vault, repo = _mvp07_vault(tmp_path)
    upgrade_to_mvp08(paths.root, clock=CLOCK)

    mvp06 = repo.parameter_registry_manifest("mvp-0.6")
    mvp07 = repo.parameter_registry_manifest("mvp-0.7")
    assert mvp06 is not None and len(mvp06["manifest_hash"]) == 32
    assert mvp07 is not None and len(mvp07["manifest_hash"]) == 32

    # F7: the manifest records the config version it was actually captured from
    # (both are frozen while the live config still names mvp-0.7), and flags that
    # per-version value divergence is not yet represented.
    for manifest in (mvp06, mvp07):
        entries = json.loads(manifest["entries_json"])
        assert entries["captured_from_config_version"] == "mvp-0.7"
        assert entries["per_version_divergence_represented"] is False
        assert entries["parameters"]  # the frozen decision-parameter value set

    # Re-freezing a version is a no-op (immutable per version).
    reloaded = load_vault(paths.root)
    reloaded.config.algorithms.algorithm_version = "mvp-0.7"
    assert (
        pr.freeze_manifest(reloaded, repo, algorithm_version="mvp-0.7", clock=CLOCK)
        is None
    )


def test_upgrade_refuses_from_non_mvp07(tmp_path):
    # A legacy mvp-0.6 vault cannot jump straight to mvp-0.8.
    paths = create_basic_vault(tmp_path / "vault")  # mvp-0.6
    result = upgrade_to_mvp08(paths.root, clock=CLOCK)
    assert not result.upgraded
    assert "only 'mvp-0.7'" in result.problems[0]


def test_upgrade_does_not_rewrite_raw_history(tmp_path):
    paths, vault, repo = _mvp07_vault(tmp_path)
    # Record a graded attempt under mvp-0.7 first.
    complete_self_graded_attempt(
        vault,
        repo,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="SVD factorizes a matrix as U Sigma V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=CLOCK,
    )
    with connect(repo.sqlite_path) as connection:
        before = connection.execute("SELECT id, rubric_score FROM practice_attempts ORDER BY id").fetchall()
        before = [(r["id"], r["rubric_score"]) for r in before]

    upgrade_to_mvp08(paths.root, clock=CLOCK)

    with connect(repo.sqlite_path) as connection:
        after = connection.execute("SELECT id, rubric_score FROM practice_attempts ORDER BY id").fetchall()
        after = [(r["id"], r["rubric_score"]) for r in after]
    assert after == before  # raw ledger untouched by the projection cutover


def _mvp06_derived_digest(repo: Repository) -> str:
    """Byte-string of the mvp-0.6 derived belief state (legacy per-LO mastery + the
    canonical facet ledgers, which are empty pre-KM2). Deterministic under FrozenClock."""

    with connect(repo.sqlite_path) as connection:
        mastery = connection.execute(
            "SELECT learning_object_id, logit_mean, logit_variance, evidence_count, "
            "last_evidence_at, algorithm_version FROM learning_object_mastery "
            "ORDER BY learning_object_id"
        ).fetchall()
        mastery_rows = [dict(r) for r in mastery]
    facet = [
        {
            "facet_id": c.facet_id,
            "capability": c.capability,
            "direct_positive_mass": c.direct_positive_mass,
            "direct_negative_mass": c.direct_negative_mass,
            "certification_credit": c.certification_credit,
        }
        for c in repo.facet_capability_evidence_all()
    ]
    return json.dumps({"mastery": mastery_rows, "facet_capability": facet}, sort_keys=True)


def test_mvp06_derived_output_is_byte_identical_across_p0_machinery(tmp_path):
    # §9.6 bullet 2 (F3): an mvp-0.6 vault's derived projection output is byte-identical
    # before and after all P0 machinery is present. P0 must not perturb frozen legacy
    # replay: the mvp-0.8 upgrade refuses mvp-0.6, and the registry projection/audit
    # touch only their own tables.
    paths = create_basic_vault(tmp_path / "vault")  # pins mvp-0.6
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    # Seed a graded attempt through the legacy mvp-0.6 path so there is derived
    # mastery to replay.
    complete_self_graded_attempt(
        vault,
        repo,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="SVD factorizes a matrix as U Sigma V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 3}, fatal_errors=[], confidence=4),
        clock=CLOCK,
    )
    before = _mvp06_derived_digest(repo)

    # (1) The P0.5 cutover refuses to touch an mvp-0.6 vault (no-op).
    result = upgrade_to_mvp08(paths.root, clock=CLOCK)
    assert not result.upgraded
    assert "only 'mvp-0.7'" in result.problems[0]
    # (2) The P0 registry projection + audit run against the same vault.
    pr.refresh(vault, repo, clock=CLOCK)
    assert pr.audit(vault, repo).clean
    # (3) Re-deriving legacy belief state reproduces it exactly (replay).
    sync_vault_state(vault, repo, clock=CLOCK)

    after = _mvp06_derived_digest(repo)
    assert after == before  # byte-identical mvp-0.6 replay under full P0 machinery
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.6"


def test_already_mvp08_is_a_noop(tmp_path):
    paths, _vault, _repo = _mvp07_vault(tmp_path)
    upgrade_to_mvp08(paths.root, clock=CLOCK)
    again = upgrade_to_mvp08(paths.root, clock=CLOCK)
    assert not again.upgraded
    assert "already mvp-0.8" in again.problems[0]


# ---------------------------------------------------------------------------
# §9.6 bullet 3: mvp-0.7 compatibility projection either matches or produces an
# explicit inspectable delta.
# ---------------------------------------------------------------------------


def test_cutover_delta_is_nonempty_and_inspectable_when_projections_differ(tmp_path):
    # F2: drive the REAL delta inside upgrade_to_mvp08 on a seeded vault where the
    # mvp-0.7 raw fraction differs from the mvp-0.8 calibrated fraction (a partial
    # self-grade). The delta must be non-empty, inspectable, and persisted.
    paths, vault, repo = _mvp07_vault(tmp_path)
    complete_self_graded_attempt(
        vault,
        repo,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="A partial explanation of SVD.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 2}, fatal_errors=[], confidence=3),
        clock=CLOCK,
    )
    result = upgrade_to_mvp08(paths.root, clock=CLOCK)
    assert result.upgraded
    delta = result.compatibility_delta
    assert delta is not None
    assert not delta.matches
    assert delta.changed_cells  # inspectable list of (cell, before, after)
    changed = delta.changed_cells[0]
    assert changed["before"] != changed["after"]

    # Persisted as a JSON artifact next to the sqlite (inspectable after the run).
    artifact = paths.sqlite_path.parent / COMPATIBILITY_DELTA_FILENAME
    assert artifact.exists()
    payload = json.loads(artifact.read_text())
    assert payload["from_version"] == "mvp-0.7"
    assert payload["to_version"] == "mvp-0.8"
    assert payload["matches"] is False
    assert payload["changed_cells"]


def test_cutover_delta_is_empty_when_projections_match(tmp_path):
    # F2: a vault with no graded attempts projects zero cells under both models, so
    # the reinterpretation delta is empty (matches) -- no spurious change reported.
    paths, _vault, _repo = _mvp07_vault(tmp_path)
    result = upgrade_to_mvp08(paths.root, clock=CLOCK)
    assert result.upgraded
    assert result.compatibility_delta is not None
    assert result.compatibility_delta.matches
    assert result.compatibility_delta.changed_cells == []


def test_compatibility_delta_matches_when_identical():
    cells = {("f1", "recall"): (1.0, 0.0, 1.0)}
    delta = compatibility_projection_delta(cells, dict(cells))
    assert delta.matches
    assert delta.changed_cells == []


def test_compatibility_delta_is_explicit_when_changed():
    before = {("f1", "recall"): (1.0, 0.0, 1.0)}
    after = {("f1", "recall"): (0.5, 0.5, 0.3)}
    delta = compatibility_projection_delta(before, after)
    assert not delta.matches
    assert len(delta.changed_cells) == 1
    assert delta.changed_cells[0]["before"] == (1.0, 0.0, 1.0)
    assert delta.changed_cells[0]["after"] == (0.5, 0.5, 0.3)
