"""The startup refresh skips the canonical fold when nothing it reads changed
(followups-nov1c B; fix 2 of the facet-table rewrite investigation in
``docs/reviews/followups-oct31.md``, queued by ruling R2 of the substrate facet
write-on-change landing).

``refresh_canonical_projection_on_startup`` runs on every ``SidecarContext.load``
and ``reload``. It folded the whole observation ledger each time, even when the
facet writers then wrote nothing. It now takes a fingerprint of every input the
fold reads (the database's commit version through a watcher connection, the
loaded vault's fields the fold reads, the code's versions) before reading any of
them, and skips the fold when a previous fold in this process that wrote nothing
was taken with the same fingerprint. These tests pin: a no-op reload skips the
fold; a change to each class of input forces it; the fold reads no vault field the
fingerprint leaves out; skipping never leaves the cache different from a fold.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import fields, replace
from datetime import timedelta

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.copies import backup_database
from learnloop.db.repositories import Repository
from learnloop.substrate import canonical_projection_rollout as R
from learnloop.substrate.canonical_projection import project_canonical_facet_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault

from tests.helpers import NOW, add_followup_item, create_placement_vault

FACET_TABLES = ("facet_recall_state", "facet_capability_evidence", "capability_residual_state",
                "unresolved_cause_factors")


def _forget() -> None:
    getattr(R, "forget_fold_memo", lambda: None)()  # (absent before the skip: the tests then fail on it)


@pytest.fixture(autouse=True)
def _fresh_memo():
    _forget()
    yield
    _forget()


class _Folds:
    """Counts the folds the startup refresh runs (the rollout's own reference)."""

    def __init__(self, monkeypatch):
        self.count = 0
        real = R.project_canonical_facet_state

        def counted(*args, **kwargs):
            self.count += 1
            return real(*args, **kwargs)

        monkeypatch.setattr(R, "project_canonical_facet_state", counted)


class _DataVersion:
    """``PRAGMA data_version`` from a connection of its own: it moves exactly when
    another connection commits a change to the database file."""

    def __init__(self, sqlite_path):
        self._connection = sqlite3.connect(sqlite_path)

    def __call__(self) -> int:
        return int(self._connection.execute("PRAGMA data_version").fetchone()[0])

    def close(self) -> None:
        self._connection.close()


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _history(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version=LATEST_ALGORITHM_VERSION)
    add_followup_item(paths.root)
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0))
    for minutes, (item_id, points) in enumerate(
            [("pi_svd_define_001", 4.0), ("pi_diag_easy", 1.0), ("pi_svd_define_002", 4.0), ("pi_eig_mid", 0.0)],
            start=1):
        _answer(vault, repository, item_id, minutes=minutes, points=points)
    return paths, vault, repository


def _answer(vault, repository, item_id, *, minutes, points=4.0):
    draft = AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.", attempt_type="independent_attempt")
    grade = SelfGradeInput(criterion_points={"correctness": points}, confidence=4)
    return complete_self_graded_attempt(vault, repository, draft, grade, clock=_at(minutes))


def _settle(vault, repository, folds):
    """The first refresh stamps the projection baseline (a commit: not remembered);
    the second folds and writes nothing (remembered); the third skips."""

    R.refresh_canonical_projection_on_startup(vault, repository)
    R.refresh_canonical_projection_on_startup(vault, repository)
    settled = folds.count
    assert R.refresh_canonical_projection_on_startup(vault, repository) is None
    assert folds.count == settled, "an unchanged third refresh must skip the fold"
    return settled


def _tables(sqlite_path):
    out = {}
    with sqlite3.connect(sqlite_path) as connection:
        for table in FACET_TABLES:
            out[table] = [tuple(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")]
    return out


def _forces_a_fold(vault, repository, folds) -> bool:
    before = folds.count
    R.refresh_canonical_projection_on_startup(vault, repository)
    return folds.count == before + 1


# -- a no-op reload skips the fold ---------------------------------------------------------------


def test_a_noop_refresh_skips_the_fold_and_commits_nothing(tmp_path, monkeypatch):
    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    data_version = _DataVersion(paths.sqlite_path)
    try:
        version, tables = data_version(), _tables(paths.sqlite_path)
        for _ in range(3):
            assert R.refresh_canonical_projection_on_startup(load_vault(paths.root), repository) is None
        assert data_version() == version
    finally:
        data_version.close()
    assert folds.count == 2  # the stamp and the remembered fold only
    assert _tables(paths.sqlite_path) == tables
    # A skipped fold left the cache exactly as a fold computes it: folding now writes nothing.
    data_version = _DataVersion(paths.sqlite_path)
    try:
        version = data_version()
        project_canonical_facet_state(vault, repository)
        assert data_version() == version
    finally:
        data_version.close()


@pytest.mark.durability
def test_a_noop_refresh_skips_the_fold_with_production_durability_and_wal(tmp_path, monkeypatch):
    paths, vault, repository = _history(tmp_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower() == "wal"
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    # A commit by another connection is seen through the WAL by the watcher.
    _answer(vault, repository, "pi_eig_easy", minutes=10)
    assert _forces_a_fold(vault, repository, folds)


def test_a_sidecar_reload_after_nothing_happened_skips_the_fold(tmp_path, monkeypatch):
    from learnloop_sidecar.context import SidecarContext

    paths, _vault, _repository = _history(tmp_path)
    monkeypatch.setattr(SidecarContext, "prepare_new_revisions", lambda self, previous: None)
    folds = _Folds(monkeypatch)
    ctx = SidecarContext()
    try:
        ctx.load(paths.root, maintenance=False)
        ctx.reload(maintenance=False)
        settled = folds.count
        ctx.reload(maintenance=False)
        ctx.reload(maintenance=False)
        assert folds.count == settled  # nothing changed: the reloads skipped the fold
        _answer(ctx.vault, ctx.repository, "pi_eig_easy", minutes=10)
        ctx.reload(maintenance=False)
        assert folds.count == settled + 1  # a new attempt: the next reload folds
    finally:
        ctx.close()
    assert R._MEMO.watcher is None and R._MEMO.folded is None  # closing the context forgets the memo


def test_the_first_refresh_of_a_process_always_folds(tmp_path, monkeypatch):
    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    _forget()  # a new process: nothing remembered
    assert _forces_a_fold(vault, repository, folds)


# -- any change to each input class forces the fold ---------------------------------------------


def test_a_new_attempt_forces_the_fold(tmp_path, monkeypatch):
    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    _answer(vault, repository, "pi_eig_easy", minutes=10)
    assert _forces_a_fold(vault, repository, folds)


def test_any_committed_write_anywhere_forces_the_fold(tmp_path, monkeypatch):
    """No list of the tables the fold reads: a commit to any table forces it."""

    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute("CREATE TABLE unrelated_scratch (x INTEGER)")
    assert _forces_a_fold(vault, repository, folds)


def test_a_tampered_cache_forces_the_fold_which_restores_it_and_is_not_remembered(tmp_path, monkeypatch):
    """The outputs are covered too: a commit that changed the cache (a replay that
    stopped half way, a hand edit) forces the fold; that fold writes the rows back,
    so it is not remembered and the next refresh folds again (writing nothing,
    remembered), and only then is the fold skipped."""

    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    tables = _tables(paths.sqlite_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute("DELETE FROM facet_recall_state")
    assert _forces_a_fold(vault, repository, folds)
    assert len(_tables(paths.sqlite_path)["facet_recall_state"]) == len(tables["facet_recall_state"]) > 0
    assert _forces_a_fold(vault, repository, folds)  # the restoring fold wrote: not remembered
    assert not _forces_a_fold(vault, repository, folds)  # the next one wrote nothing: remembered


def test_a_database_restored_at_the_same_path_forces_the_fold(tmp_path, monkeypatch):
    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    copy = tmp_path / "restored.sqlite"
    backup_database(paths.sqlite_path, copy)
    os.replace(copy, paths.sqlite_path)  # same bytes, another file (a restore)
    assert _forces_a_fold(vault, repository, folds)


def test_a_config_change_forces_the_fold(tmp_path, monkeypatch):
    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    certification = vault.config.evidence.certification
    changed = vault.config.model_copy(update={"evidence": vault.config.evidence.model_copy(update={
        "certification": certification.model_copy(update={
            "max_groups_per_attempt": certification.max_groups_per_attempt + 1})})})
    assert _forces_a_fold(replace(vault, config=changed), repository, folds)


def test_a_practice_item_change_forces_the_fold(tmp_path, monkeypatch):
    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    item = vault.practice_items["pi_svd_define_001"]
    rubric = item.grading_rubric
    criterion = rubric.criteria[0].model_copy(update={"points": rubric.criteria[0].points + 1})
    changed = item.model_copy(update={"grading_rubric": rubric.model_copy(update={"criteria": [criterion]})})
    assert _forces_a_fold(replace(vault, practice_items={**vault.practice_items, item.id: changed}),
                          repository, folds)


def test_a_default_rubric_change_forces_the_fold(tmp_path, monkeypatch):
    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    rubric = vault.practice_items["pi_svd_define_001"].grading_rubric
    assert _forces_a_fold(replace(vault, default_rubrics={**vault.default_rubrics, "short_answer": rubric}),
                          repository, folds)


def test_a_facet_alias_change_forces_the_fold(tmp_path, monkeypatch):
    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    assert _forces_a_fold(replace(vault, facet_aliases={**vault.facet_aliases, "recall_old": "recall"}),
                          repository, folds)


def test_a_projection_version_change_forces_the_fold(tmp_path, monkeypatch):
    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    monkeypatch.setattr(R, "CANONICAL_PROJECTION_VERSION", R.CANONICAL_PROJECTION_VERSION + "+probe")
    assert _forces_a_fold(vault, repository, folds)
    assert repository.latest_canonical_projection_rebuild()["canonical_projection_version"].endswith("+probe")


def test_a_fold_racing_a_commit_is_not_remembered(tmp_path, monkeypatch):
    """A write that lands while the fold runs changes the fingerprint taken after
    it: the fold is not remembered, and the next refresh folds."""

    paths, vault, repository = _history(tmp_path)
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    _forget()
    real = R.project_canonical_facet_state

    def fold_then_commit(*args, **kwargs):
        real(*args, **kwargs)
        with sqlite3.connect(paths.sqlite_path) as connection:
            connection.execute("CREATE TABLE written_during_the_fold (x INTEGER)")

    monkeypatch.setattr(R, "project_canonical_facet_state", fold_then_commit)
    R.refresh_canonical_projection_on_startup(vault, repository)
    monkeypatch.setattr(R, "project_canonical_facet_state", real)
    assert _forces_a_fold(vault, repository, folds)


# -- the fingerprint covers every vault field the fold reads ------------------------------------


class _Unread:
    """A vault field the fold must not read: any access raises."""

    def __init__(self, name: str) -> None:
        object.__setattr__(self, "_name", name)

    def _refuse(self, *_args, **_kwargs):
        raise AssertionError(f"the canonical fold read LoadedVault.{object.__getattribute__(self, '_name')}, "
                             "which its fingerprint does not cover (FOLD_VAULT_FIELDS)")

    __getattr__ = __iter__ = __len__ = __getitem__ = __contains__ = __bool__ = _refuse
    __eq__ = __hash__ = __call__ = _refuse


@pytest.mark.parametrize("residuals", [False, True])
def test_the_fold_reads_no_vault_field_its_fingerprint_leaves_out(tmp_path, monkeypatch, residuals):
    paths, vault, repository = _history(tmp_path)
    if residuals:  # the residual activation's body runs too
        vault = replace(vault, config=vault.config.model_copy(update={
            "capabilities": vault.config.capabilities.model_copy(update={"residual_activation_enabled": True})}))
    folds = _Folds(monkeypatch)
    _settle(vault, repository, folds)
    _forget()
    unread = {field.name: _Unread(field.name) for field in fields(LoadedVault)
              if field.name not in R.FOLD_VAULT_FIELDS}
    assert unread, "LoadedVault has fields the fold does not read"
    poisoned = replace(vault, **unread)
    assert _forces_a_fold(poisoned, repository, folds)  # the skip-eligible path, folding
    project_canonical_facet_state(poisoned, repository)  # and the fold itself
    assert R.fold_inputs_fingerprint(poisoned, repository) is not None
