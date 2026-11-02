"""Curriculum C2b: the learner's notes are the vault's own, searched by exact words or by meaning
(spec_deliverable_curriculum_v1 §10.1 as built).

* The corpus: Reader notes and highlights with the learner's words, and capture-inbox items; never a
  bare highlight, a deleted annotation, a dismissed capture, a model's annotation, or an annotation
  beside protected (exam) material.
* Exact words: always available, no model.
* By meaning: only while the vault's embeddings are on; the vault's own embedding route and model
  (a fake client here), notes embedded incrementally (only new or changed ones), the query embedded
  through the tutor's library-retrieval query path; with embeddings off the contract hides the
  toggle and a meaning search is refused.
* The note link judge's candidates come from the same search.

Every note is synthetic; every model and embedding client is a fake.
"""
from __future__ import annotations

import pytest

from learnloop.source_retrieval import note_links as NL
from learnloop.source_retrieval import vault_notes as VN
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake, build_deliverable_vault
from tests.notes_fixtures import (
    NoteEmbeddingFake,
    NoteLinkFake,
    add_annotation,
    add_capture,
    edit_annotation,
    eigen_notes,
    turn_on_embeddings,
)
from tests.reading_path_fixtures import call, context
from tests.section_coverage_fixtures import CoverageJudgeFake


def _vault(tmp_path, *, embeddings: bool = False):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    if embeddings:
        turn_on_embeddings(paths)
    return paths, repository


def _vectors(repository) -> list[tuple[str, str]]:
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT record_id, content_hash FROM embedding_vectors WHERE record_kind = ? ORDER BY rowid",
            (VN.RECORD_KIND,))]


def test_the_corpus_is_the_learners_own_words_never_protected_or_deleted(tmp_path):
    paths, repository = _vault(tmp_path)
    corpus = eigen_notes(repository)
    ai_note = add_annotation(repository, "Eigenvalues, an AI's note.")
    with repository.atomic():
        repository.connection().execute(
            "UPDATE source_annotation_versions SET authorship = 'ai' WHERE annotation_id = ?", (ai_note,))
    vault = load_vault(paths.root)
    keys = {note.note_key for note in VN.notes(vault, repository)}
    assert keys == {corpus["typed"], corpus["captured"], corpus["unrelated"]}
    typed = VN.read(vault, repository, corpus["typed"])
    assert typed is not None and typed.title == "Linear Algebra Notes" and typed.origin == "vault"
    assert typed.heading.startswith("Chapter 5 Eigenvalues") and typed.extraction_id == "ext_book"
    for gone in ("exam", "bare", "deleted"):
        assert VN.read(vault, repository, corpus[gone]) is None
    assert VN.beside_protected(vault, repository, corpus["exam"]) is True
    assert VN.beside_protected(vault, repository, corpus["typed"]) is False
    assert VN.beside_protected(vault, repository, corpus["captured"]) is False


def test_an_unreadable_protection_predicate_keeps_every_annotation_out(tmp_path, monkeypatch):
    from learnloop.source_retrieval import section_coverage as SC

    paths, repository = _vault(tmp_path)
    corpus = eigen_notes(repository)

    def broken(*_args, **_kwargs):
        raise SC.CoverageError("withheld", "unreadable")

    monkeypatch.setattr(SC, "read_protection", broken)
    vault = load_vault(paths.root)
    assert {note.note_key for note in VN.notes(vault, repository)} == {corpus["captured"], corpus["unrelated"]}
    assert VN.beside_protected(vault, repository, corpus["typed"]) is True


def test_exact_words_rank_by_distinct_terms_and_ignore_stopwords(tmp_path):
    paths, repository = _vault(tmp_path)
    corpus = eigen_notes(repository)
    vault = load_vault(paths.root)
    notes = VN.notes(vault, repository)
    assert [note.note_key for note in VN.words_search(notes, "the 2x2 example", limit=5)] == [corpus["captured"]]
    ranked = VN.words_search(notes, "eigenvalues by hand", limit=5)
    assert ranked[0].note_key == corpus["captured"]  # "eigenvalues" and "hand"
    assert {note.note_key for note in ranked} == {corpus["typed"], corpus["captured"], corpus["unrelated"]}
    assert VN.words_search(notes, "the and of", limit=5) == []  # only stopwords
    assert [n.note_key for n in VN.words_search(notes, "eigen", limit=5)] == [corpus["captured"]]  # whole words only
    assert len(VN.words_search(notes, "eigenvalues", limit=1)) == 1


def test_meaning_search_needs_the_vaults_embeddings(tmp_path):
    paths, repository = _vault(tmp_path)
    eigen_notes(repository)
    vault = load_vault(paths.root)
    assert not VN.meaning_available(vault)
    assert VN.meaning_unavailable(vault) == "embedding.enabled is false"
    with pytest.raises(VN.MeaningUnavailable):
        VN.meaning_search(vault, repository, VN.notes(vault, repository), ["eigen"], limit=5,
                          embedder=NoteEmbeddingFake())
    assert VN.ensure_vectors(vault, VN.notes(vault, repository))["status"] == "disabled"
    assert _vectors(repository) == []


def test_meaning_search_embeds_notes_incrementally_and_finds_what_words_miss(tmp_path):
    paths, repository = _vault(tmp_path, embeddings=True)
    corpus = eigen_notes(repository)
    vault = load_vault(paths.root)
    assert VN.meaning_available(vault)
    # "spectrum" means "eigenvalues" to this fake: a meaning the exact words miss.
    embedder = NoteEmbeddingFake(synonyms={"spectrum": "eigenvalues", "spectra": "eigenvalues"})
    notes = VN.notes(vault, repository)
    assert VN.words_search(notes, "spectrum", limit=5) == []
    found = VN.meaning_search(vault, repository, notes, ["spectrum"], limit=5, embedder=embedder)
    assert found.status == "ready" and found.covered == 3 == found.total
    assert {note.note_key for note in found.notes} == {corpus["typed"], corpus["captured"], corpus["unrelated"]}
    assert {record for record, _hash in _vectors(repository)} == {corpus["typed"], corpus["captured"],
                                                                 corpus["unrelated"]}
    embedded = len(embedder.inputs)
    # Searching again embeds no note again (content-addressed); the query is cached too.
    VN.meaning_search(vault, repository, VN.notes(vault, repository), ["spectrum"], limit=5, embedder=embedder)
    assert len(embedder.inputs) == embedded
    # A new note and an edited one are embedded, nothing else.
    added = add_capture(repository, "Spectra of symmetric matrices are real.")
    edit_annotation(repository, corpus["typed"].split(":", 1)[1], "Eigenvalues, edited: Av = lv.")
    VN.meaning_search(vault, repository, VN.notes(vault, repository), ["spectrum"], limit=5, embedder=embedder)
    new_inputs = embedder.inputs[embedded:]
    assert len(new_inputs) == 2 and any("Spectra of symmetric" in text for text in new_inputs)
    assert any("edited" in text for text in new_inputs)
    assert f"capture:{added}" in {record for record, _hash in _vectors(repository)}
    # The embedding receipts are the backfill's and the query's (the vault's embedding route).
    with repository.connection() as connection:
        owners = {row[0] for row in connection.execute("SELECT owner_kind FROM model_call_receipts")}
    assert {"embedding_backfill", "source_query_embedding"} <= owners


def test_the_reader_search_toggles_by_meaning_only_when_embeddings_are_on(tmp_path):
    paths, repository = _vault(tmp_path, embeddings=True)
    corpus = eigen_notes(repository)
    embedder = NoteEmbeddingFake(synonyms={"spectrum": "eigenvalues"})
    ctx = context(paths.root, note_embedding_client=embedder)
    assert call(ctx, "reader.prompt_contract", {})["notes"]["meaning"] is True
    words = call(ctx, "notes.search", {"query": "spectrum"})
    assert words["mode"] == "words" and words["hits"] == []
    meaning = call(ctx, "notes.search", {"query": "spectrum", "mode": "meaning"})
    assert meaning["mode"] == "meaning" and meaning["basis"] == "meaning:ready"
    assert {hit["noteKey"] for hit in meaning["hits"]} == {corpus["typed"], corpus["captured"], corpus["unrelated"]}
    assert all("copy this one" not in hit["snippet"] for hit in meaning["hits"])  # the exam's note: never


def test_the_link_judges_candidates_come_from_the_same_vault_search(tmp_path):
    """With embeddings on, the topic's candidates are found by meaning first (a note that
    shares no word with the topic or its sections), then by exact words; the judge reads
    exactly those notes."""

    paths, repository = _vault(tmp_path, embeddings=True)
    corpus = eigen_notes(repository)
    spectral = add_capture(repository, "Spectrum of a 2x2: worked by hand, Av = lv.")
    embedder = NoteEmbeddingFake(synonyms={"spectrum": "eigenvalues"})
    notes = NoteLinkFake(discusses=("Av = lv",))
    fake = DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"})
    ctx = context(paths.root, deliverable_inline=True, notes_inline=True, coverage_judge_client=CoverageJudgeFake(),
                  deliverable_scope_client=fake, deliverable_path_client=fake, note_link_client=notes,
                  note_embedding_client=embedder)
    goal_id = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues for my midterm"})["goalId"]
    call(ctx, "curriculum.set_depth", {"goal_id": goal_id, "depth": "learn_to_use_it"})
    vault = load_vault(paths.root)
    assert VN.words_search(VN.notes(vault, repository), "Eigenvalues", limit=10) and all(
        note.note_key != f"capture:{spectral}"
        for note in VN.words_search(VN.notes(vault, repository), "Chapter 5 Eigenvalues", limit=10))
    out = call(ctx, "notes.path", {"goal_id": goal_id})
    sent = {note["text"] for note in notes.contexts[0]["notes"]}
    assert any("Spectrum of a 2x2" in text for text in sent)  # found by meaning only
    assert all("copy this one" not in text for text in sent)
    linked = {line["noteKey"] for entry in out["lines"] for line in entry["notes"]}
    assert {corpus["typed"], f"capture:{spectral}"} <= linked
    # Words-only (embeddings off) the same judge never sees the meaning-only note.
    target = NL.path_targets(vault, repository, goal_id)[0]
    off = NL.candidates(vault, repository, target, limit=8, settings=NL.NotesSettings(meaning=False))
    assert f"capture:{spectral}" not in {note.note_key for note in off}


def test_captures_with_only_media_or_a_link_and_no_words_are_not_notes(tmp_path):
    paths, repository = _vault(tmp_path)
    link_only = add_capture(repository, "", kind="url", url="https://example.org/eigen")
    link_note = add_capture(repository, "", kind="url", url="https://example.org/eigen2", note="Eigen intuition.")
    vault = load_vault(paths.root)
    found = {note.note_key: note for note in VN.notes(vault, repository)}
    assert f"capture:{link_only}" not in found
    assert found[f"capture:{link_note}"].text == "Eigen intuition."
    assert found[f"capture:{link_note}"].heading == "https://example.org/eigen2"


def test_a_legacy_tend_table_in_an_existing_config_is_ignored(tmp_path):
    """C2b removed ``[notes.tend]``: a vault config written at C2 still loads (no crash), the
    table is ignored, the notes work from the vault, and the effective config has no tend."""

    from learnloop.config.loader import load_config

    paths, repository = _vault(tmp_path)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8") + (
        '\n[notes]\nenabled = true\nmax_candidates = 6\n\n[notes.tend]\nbinary = "tend"\n'
        'paths = ["~/Documents/thinking/notes", "~/org"]\npocket_notes_paths = ["~/org/pocket-inbox.org"]\n'
        'lexical_only = true\ntimeout_seconds = 10.0\nk = 5\n'), encoding="utf-8")
    vault = load_vault(paths.root)
    assert vault.config.notes.enabled is True and vault.config.notes.max_candidates == 6
    assert "tend" not in vault.config.notes.model_dump()
    assert "tend" not in load_config(toml, load_environment=False).model_dump()["notes"]
    corpus = eigen_notes(repository)
    assert corpus["typed"] in {note.note_key for note in VN.notes(vault, repository)}
    assert call(context(paths.root), "reader.prompt_contract", {})["notes"]["enabled"] is True
