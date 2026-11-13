"""K1-1: exam material is never read from source sets that did not load.

Rules 1 and 2 come only from ``vault.source_sets``. A file that fails
validation, is truncated or is empty loads as *no* source sets, which reads as
"no exam material". Every reader of the shared predicate refuses instead, and
the vault writer never exposes a truncated file."""

from __future__ import annotations

import pytest

from learnloop.content.sources import exam_material as EM
from learnloop.learner_protection import withheld_items
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set
from learnloop.vault.yaml_io import write_yaml_atomic
from tests.source_retrieval_fakes import build_retrieval_vault

SPAN = "s1"


def _truncated(valid: str) -> str:
    """The valid file cut inside a member's key: nonempty, and no longer a source-sets file."""

    cut = valid.index("default_role") + len("default_ro")
    return valid[:cut]


CORRUPTIONS = ("unparseable", "schema_invalid", "empty", "truncated")


@pytest.fixture
def vault_with_exam(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault", embeddings=False)
    return paths, repository


def _corrupt(paths, kind: str) -> None:
    path = paths.source_sets_path
    text = {
        "unparseable": "source_sets:\n  - id: sset_la\n    members: [{source_id: src_exam, default_role: exam\n",
        "schema_invalid": "source_sets:\n  - id: sset_la\n    subject_id: linear-algebra\n    members: not-a-list\n",
        "empty": "",
        "truncated": _truncated(path.read_text(encoding="utf-8")),
    }[kind]
    path.write_text(text, encoding="utf-8")


def _exam_span(repository) -> str:
    with repository.connection() as connection:
        row = connection.execute("SELECT span_id FROM source_document_blocks WHERE extraction_id = 'ext_exam' "
                                 "ORDER BY ordinal LIMIT 1").fetchone()
    return str(row[0])


def test_a_valid_file_still_reads_the_exam_member_as_exam_material(vault_with_exam):
    paths, repository = vault_with_exam
    vault = load_vault(paths.root)
    assert EM.protection_issues(vault) == []
    assert EM.exam_material(vault, repository).covers("ext_exam", _exam_span(repository))
    assert EM.spans_withheld(vault, repository, "ext_exam", [_exam_span(repository)])


@pytest.mark.parametrize("kind", CORRUPTIONS)
def test_the_premise_the_corrupt_file_is_unreadable(vault_with_exam, kind):
    paths, _repository = vault_with_exam
    _corrupt(paths, kind)
    vault = load_vault(paths.root)
    assert vault.source_sets == [] and EM.protection_issues(vault)


@pytest.mark.parametrize("kind", CORRUPTIONS)
def test_every_shared_reader_refuses_unloaded_source_sets(vault_with_exam, kind):
    paths, repository = vault_with_exam
    _corrupt(paths, kind)
    vault = load_vault(paths.root)
    span = _exam_span(repository)
    for read in (
        lambda: EM.exam_material(vault, repository),
        lambda: EM.held_out_partition(vault, repository),
        lambda: EM.held_out_material(vault, repository),
        lambda: EM.role_material(vault, repository, EM.is_exam_role),
        lambda: EM.exam_withheld(vault, repository, [("ext_exam", span)]),
        lambda: EM.spans_withheld(vault, repository, "ext_exam", [span]),
    ):
        with pytest.raises(EM.SourceSetsUnreadable):
            read()


@pytest.mark.parametrize("kind", CORRUPTIONS)
def test_the_tutor_figures_and_phone_withhold_when_source_sets_did_not_load(vault_with_exam, kind):
    from learnloop.figures.service import withheld_message
    from learnloop.reader.phone_media import phone_withheld
    from learnloop.source_retrieval.corpus import exam_exclusions, teaching_exclusions, teaching_scope

    paths, repository = vault_with_exam
    _corrupt(paths, kind)
    vault = load_vault(paths.root)
    span = _exam_span(repository)
    # Tutor, find_sources and compare read the teaching exclusions: they raise, never return "nothing excluded".
    for read in (lambda: teaching_exclusions(vault, repository), lambda: exam_exclusions(vault, repository),
                 lambda: teaching_scope(vault, repository, ["lo_eigen"]),
                 lambda: withheld_message(vault, repository, "ext_exam", [span])):
        with pytest.raises(EM.SourceSetsUnreadable):
            read()
    # The phone refuses the whole reading, with its message.
    refusal = phone_withheld(vault, repository, "ext_exam", [span])
    assert refusal.whole and refusal.message


@pytest.mark.parametrize("kind", CORRUPTIONS)
def test_the_exercise_import_and_the_facet_resolver_refuse(vault_with_exam, kind):
    from learnloop.content.authoring.source_exercise_import import import_source_exercise
    from learnloop.content.facet_identity.authority import CitationResolver

    paths, repository = vault_with_exam
    span = _exam_span(repository)
    _corrupt(paths, kind)
    outcome = import_source_exercise(paths.root, repository, extraction_id="ext_exam", span_ids=[span],
                                     caller="learner", clients={})
    assert outcome["status"] == "rejected" and "source sets could not be read" in outcome["reason"]
    assert outcome["practice_item_id"] is None
    resolver = CitationResolver.for_vault(repository, load_vault(paths.root))
    with pytest.raises(EM.SourceSetsUnreadable):
        resolver.is_exam("ext_exam", span)


@pytest.mark.parametrize("kind", CORRUPTIONS)
def test_the_readers_that_already_asked_still_refuse_and_ask_once(vault_with_exam, kind, monkeypatch):
    paths, repository = vault_with_exam
    _corrupt(paths, kind)
    vault = load_vault(paths.root)
    assert withheld_items(vault, repository).available is False
    # withheld_items stops at the metadata question: it never reaches the shared read to be refused by it again.
    calls = []
    real = EM.protection_issues
    import learnloop.learner_protection as LP

    monkeypatch.setattr(LP, "protection_issues", lambda vault: calls.append(1) or real(vault))
    monkeypatch.setattr(EM, "protection_issues", lambda vault: calls.append(2) or real(vault))
    withheld_items(vault, repository)
    assert calls == [1]


def test_a_vault_double_without_a_root_is_not_gated(vault_with_exam):
    paths, repository = vault_with_exam
    sets = load_vault(paths.root).source_sets
    assert EM.exam_material(sets, repository).covers("ext_exam", _exam_span(repository))


def test_the_source_sets_write_never_leaves_a_truncated_file(vault_with_exam, monkeypatch):
    paths, _repository = vault_with_exam
    before = paths.source_sets_path.read_bytes()
    seen: list[bytes] = []
    import learnloop.vault.yaml_io as YI

    def failing_replace(source, destination):
        seen.append(paths.source_sets_path.read_bytes())  # a reader here still sees the whole old file
        raise OSError("the rename failed")

    monkeypatch.setattr(YI.os, "replace", failing_replace)
    with pytest.raises(OSError):
        upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "Renamed",
                                       "members": []})
    assert seen == [before] and paths.source_sets_path.read_bytes() == before
    assert not [p for p in paths.source_sets_path.parent.iterdir() if p.name.endswith(".tmp")]


def test_write_yaml_atomic_round_trips(tmp_path):
    target = tmp_path / "nested" / "x.yaml"
    write_yaml_atomic(target, {"a": 1})
    assert target.read_text(encoding="utf-8").strip() == "a: 1"


def test_a_snapshot_loaded_from_an_empty_file_stays_unreadable_after_the_file_is_restored(vault_with_exam):
    """The gate judges the sets the reader will use: a snapshot with no source sets because the file was
    empty when it loaded must not pass once the file is back, the snapshot still has none."""

    paths, repository = vault_with_exam
    valid = paths.source_sets_path.read_text(encoding="utf-8")
    _corrupt(paths, "empty")
    vault = load_vault(paths.root)
    paths.source_sets_path.write_text(valid, encoding="utf-8")
    assert vault.source_sets == []
    with pytest.raises(EM.SourceSetsUnreadable):
        EM.exam_material(vault, repository)
    assert not EM.protection_issues(load_vault(paths.root))
