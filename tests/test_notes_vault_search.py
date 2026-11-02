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


# -- Codex review (C2b) ---------------------------------------------------------------------------

def test_c2b_f1_a_note_under_a_protected_section_header_is_no_note(tmp_path):
    """Codex review C2b F1: the note's heading is its section header's text, so a header span
    that is protected makes the note one beside protected material (never searched or sent)."""

    from contextlib import closing
    from types import SimpleNamespace

    from learnloop.db.connection import connect

    paths, repository = _vault(tmp_path)
    stub = SimpleNamespace(reading_out=lambda _e: False, span_out=lambda _e, span: span == "s1",
                           excluded_spans=frozenset(), material=SimpleNamespace(spans=frozenset()))
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert VN._out(stub, "ext_book", [("s2", [])], connection) is True  # s1: ch_eigen's header
        assert VN._out(stub, "ext_book", [("s7", [])], connection) is False  # another chapter
        assert VN._out(stub, "ext_book", [("s2", [])]) is False  # (no connection: anchored spans only)


def test_c2b_f2_a_candidate_protected_before_the_request_refuses_it(tmp_path, monkeypatch):
    """Codex review C2b F2: the candidates were read, then a candidate Reader note's anchor
    became protected before the request: the request's admission reads the candidates'
    protection on the live snapshot and refuses; nothing is sent or written."""

    from tests.section_coverage_fixtures import table_counts
    from tests.test_notes_linked import _deliverable

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    vault = load_vault(paths.root)
    target = NL.path_targets(vault, repository, goal_id)[0]
    real = VN.snapshot_protected_keys
    monkeypatch.setattr(VN, "snapshot_protected_keys", lambda vault, repository, keys: (
        {key for key in keys if key == corpus["typed"]} | real(vault, repository, keys)))
    before = table_counts(repository)
    result = NL.judge_target(vault, repository, target, client=notes, live_vault=lambda: load_vault(paths.root))
    assert result.status == "switched_off" and notes.calls == 0
    assert table_counts(repository) == before


def test_c2b_f3_a_restored_text_keeps_its_vector(tmp_path):
    """Codex review C2b F3: a note edited and then restored to an earlier text is still covered
    by that text's stored vector (no row collapsing by note id)."""

    paths, repository = _vault(tmp_path, embeddings=True)
    annotation = add_annotation(repository, "Eigenvalues first version.")
    vault = load_vault(paths.root)
    embedder = NoteEmbeddingFake()
    VN.ensure_vectors(vault, VN.notes(vault, repository), client_factory=lambda: embedder)
    edit_annotation(repository, annotation, "Eigenvalues second version.")
    VN.ensure_vectors(vault, VN.notes(vault, repository), client_factory=lambda: embedder)
    edit_annotation(repository, annotation, "Eigenvalues first version.")
    notes = VN.notes(vault, repository)
    assert VN._covered(repository, vault.config.embedding.model, notes) == {
        f"annotation:{annotation}": notes[0].content_hash and VN.records(notes)[0].content_hash}
    embedded = len(embedder.inputs)
    found = VN.meaning_search(vault, repository, notes, ["eigenvalues"], limit=5, embedder=embedder)
    assert found.status == "ready" and [n.note_key for n in found.notes] == [f"annotation:{annotation}"]
    assert len(embedder.inputs) == embedded + 1  # only the query: the restored text was not paid again


def test_c2b_re_f2_embedding_batches_drop_notes_protected_meanwhile(tmp_path, monkeypatch):
    """Codex re-review C2b F2: notes are embedded in batches; before each later batch the vault
    is read again and a note now beside protected material is dropped (never embedded)."""

    from learnloop.source_retrieval.source_vectors import BATCH_SIZE

    paths, repository = _vault(tmp_path, embeddings=True)
    keys = [f"capture:{add_capture(repository, f'Eigen note number {index}.')}" for index in range(BATCH_SIZE)]
    late = f"annotation:{add_annotation(repository, 'Eigenvalues, a late Reader note.')}"
    vault = load_vault(paths.root)
    corpus = VN.notes(vault, repository)
    assert corpus[0].note_key == late  # annotations first: put it in the second batch
    corpus = corpus[1:] + corpus[:1]
    real = VN.snapshot_protected_keys
    calls: list[int] = []

    def protected_after_the_first_batch(vault, repository, wanted):
        calls.append(1)
        return {key for key in wanted if key == late} | real(vault, repository, wanted)

    monkeypatch.setattr(VN, "snapshot_protected_keys", protected_after_the_first_batch)
    embedder = NoteEmbeddingFake()
    report = VN.ensure_vectors(vault, corpus, client_factory=lambda: embedder, repository=repository)
    assert report["status"] == "complete" and report["dropped"] == 1 and calls
    assert len(embedder.inputs) == BATCH_SIZE and all("late Reader note" not in text for text in embedder.inputs)
    assert late not in {record for record, _hash in _vectors(repository)} and set(keys) <= {
        record for record, _hash in _vectors(repository)}


def test_c2b_re_f3_exact_words_search_the_whole_note(tmp_path):
    """Codex re-review C2b F3: a long note is bounded when stored and sent, but searched (and
    hashed for change detection) whole."""

    paths, repository = _vault(tmp_path)
    long_text = ("filler " * (VN.NOTE_CHARS // 7 + 50)) + "eigendecomposition at the very end."
    annotation = add_annotation(repository, long_text)
    vault = load_vault(paths.root)
    (note,) = [n for n in VN.notes(vault, repository) if n.note_key == f"annotation:{annotation}"]
    assert note.truncated and "eigendecomposition" not in note.text
    assert [n.note_key for n in VN.words_search([note], "eigendecomposition", limit=5)] == [note.note_key]
    before = note.content_hash
    edit_annotation(repository, annotation, long_text.replace("very end", "very, very end"))
    (edited,) = [n for n in VN.notes(load_vault(paths.root), repository) if n.note_key == note.note_key]
    assert edited.text == note.text and edited.content_hash != before


def _many_captures(repository, count):
    return [f"capture:{add_capture(repository, f'Eigen note number {index}.')}" for index in range(count)]


def test_c2b_r3_f2_a_switch_turned_off_between_batches_stops_the_embedding(tmp_path, monkeypatch):
    from learnloop.source_retrieval.source_vectors import BATCH_SIZE

    paths, repository = _vault(tmp_path, embeddings=True)
    _many_captures(repository, BATCH_SIZE + 3)
    vault = load_vault(paths.root)
    real = VN._authorized_now
    seen: list[int] = []

    def off_after_the_first(vault):
        seen.append(1)
        return real(vault) if len(seen) == 1 else (None, "embedding.enabled is false")

    monkeypatch.setattr(VN, "_authorized_now", off_after_the_first)
    embedder = NoteEmbeddingFake()
    report = VN.ensure_vectors(vault, VN.notes(vault, repository), client_factory=lambda: embedder,
                               repository=repository)
    assert report["status"] == "disabled" and report["embedded"] == BATCH_SIZE
    assert len(embedder.inputs) == BATCH_SIZE  # the second batch was never sent


def test_c2b_r3_f3_one_money_cap_for_the_whole_run(tmp_path, monkeypatch):
    from learnloop.ops import embedding_backfill as EB
    from learnloop.source_retrieval.source_vectors import BATCH_SIZE

    paths, repository = _vault(tmp_path, embeddings=True)
    _many_captures(repository, BATCH_SIZE * 2)
    vault = load_vault(paths.root)
    cap = float(vault.config.embedding.source_backfill_max_cost_usd)
    asked: list[float] = []

    def fake_backfill(loaded, *, caps, records, **_kwargs):
        asked.append(caps.max_estimated_usd)
        return {"status": "complete", "records": len(records), "embedded": len(records),
                "charged": {"estimated_usd": cap * 0.6}}

    monkeypatch.setattr(EB, "backfill_embeddings", fake_backfill)
    VN.ensure_vectors(vault, VN.notes(vault, repository), repository=repository)
    assert asked[0] == cap and abs(asked[1] - cap * 0.4) < 1e-9


def test_c2b_r3_f4_several_named_subjects_send_the_grouped_form_for_those(tmp_path, monkeypatch):
    from learnloop.source_retrieval import deliverables as DL
    from tests.test_curriculum_c2b_past_papers import _two_subject_vault

    paths, repository = _two_subject_vault(tmp_path)
    vault = load_vault(paths.root)
    goal_id = DL.create_deliverable(vault, repository, "my midterm")["goal_id"]
    monkeypatch.setattr(DL, "deliverable_subjects", lambda *_a, **_k: frozenset({"linear-algebra", "probability"}))
    with repository.connection() as connection:
        from learnloop.db.stores import deliverables as store

        rows = store.inputs(connection, goal_id)
    prompt = DL.build_scope_prompt(load_vault(paths.root), repository, DL.goal_of(load_vault(paths.root), goal_id), rows)
    assert prompt.version == DL.SCOPE_PAST_PAPERS_GROUPED_PROMPT_VERSION
    assert [subject for subject, _ids in prompt.past_paper_groups] == ["linear-algebra", "probability"]
