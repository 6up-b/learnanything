"""Curriculum C2: notes in the learner's voice, linked (spec_deliverable_curriculum_v1 §10, §12 C2,
§12.3), with C2b's vault-native notes: the learner's Reader notes (annotations with their words) and
capture-inbox items in the vault, searched by exact words or (embeddings on) by meaning.

Every note is synthetic vault data (tests/notes_fixtures.py); every model and embedding client is a
fake; background work runs inline (``notes_inline``).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from learnloop.ai import plan_fallback
from learnloop.source_retrieval import note_links as NL
from learnloop.source_retrieval import vault_notes as VN
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.deliverable_fixtures import DeliverableFake, build_deliverable_vault
from tests.notes_fixtures import (
    SENTINEL,
    MeteredNoteLinkFake,
    NoteLinkFake,
    add_capture,
    delete_annotation,
    dismiss_capture,
    edit_annotation,
    eigen_notes,
)
from tests.reading_path_fixtures import call, context, normalized
from tests.section_coverage_fixtures import CoverageJudgeFake, table_counts

RPCS = ("notes.path", "notes.marks", "notes.passages", "notes.search", "notes.link", "notes.decide",
        "notes.hidden", "notes.set_gaps")  # followups-nov1c C; curriculum C5's opt-in


def _ctx(paths, **attrs):
    fake = attrs.pop("fake", None) or DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"})
    return context(paths.root, deliverable_inline=True, notes_inline=True, coverage_judge_client=CoverageJudgeFake(),
                   deliverable_scope_client=fake, deliverable_path_client=fake, **attrs)


def _deliverable(tmp_path: Path, *, config: str = "", notes: NoteLinkFake | None = None):
    """A deliverable vault with a judged path for lo_eigen (primary ch_eigen in ext_book),
    the synthetic vault notes, and the sidecar context."""

    paths, repository = build_deliverable_vault(tmp_path / "vault", config=config)
    corpus = eigen_notes(repository)
    notes = notes or NoteLinkFake()
    ctx = _ctx(paths, note_link_client=notes)
    created = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues for my midterm"})
    goal_id = created["goalId"]
    view = call(ctx, "curriculum.set_depth", {"goal_id": goal_id, "depth": "learn_to_use_it"})
    assert view["status"] == "ready"
    return paths, repository, ctx, goal_id, corpus, notes


def _lines(out, lo: str = "lo_eigen") -> list:
    return next((entry["notes"] for entry in out["lines"] if entry["learningObjectId"] == lo), [])


def _keys(lines) -> set[str]:
    return {line["noteKey"] for line in lines}


def _count(repository, table: str) -> int:
    with repository.connection() as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _ref(key: str) -> str:
    return key.split(":", 1)[1]


# -- linking: candidates, the judgment, proposals --------------------------------------------------

def test_the_path_links_the_vault_notes_that_discuss_it_and_stores_only_linked_notes(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    out = call(ctx, "notes.path", {"goal_id": goal_id})
    assert notes.calls == 1
    lines = _lines(out)
    assert _keys(lines) == {corpus["typed"], corpus["captured"]}  # the unrelated capture is not linked
    by_key = {line["noteKey"]: line for line in lines}
    assert all(line["note"]["origin"] == "vault" and line["note"]["originLabel"] is None for line in lines)
    assert all(line["byLabel"] == NL.BY_MODEL_LABEL and line["authorship"] == "ai" for line in lines)
    assert by_key[corpus["captured"]]["line"] == "your note from 3 Oct"
    assert "Chapter 5 Eigenvalues" in by_key[corpus["typed"]]["note"]["heading"]
    # Only linked notes are stored, with origin vault and their vault reference.
    with repository.connection() as connection:
        stored = [dict(zip(("key", "origin", "kind", "ref", "path", "text"), row)) for row in connection.execute(
            "SELECT note_key, origin, vault_ref_kind, vault_ref_id, path, text_md FROM learner_notes")]
        ledger = " ".join(str(row[0]) for row in connection.execute(
            "SELECT right_id || rationale FROM judgment_ledger WHERE task = 'note_link'"))
    assert {row["key"] for row in stored} == {corpus["typed"], corpus["captured"]}
    assert all(row["origin"] == "vault" and row["path"] is None for row in stored)
    assert {(row["kind"], row["ref"]) for row in stored} == {("annotation", _ref(corpus["typed"])),
                                                              ("capture", _ref(corpus["captured"]))}
    assert "Shopping list" not in " ".join(row["text"] for row in stored)
    assert _ref(corpus["unrelated"]) not in ledger  # the ledger names notes by digest
    # The judge read the LO, its passage's lead and the candidates; never the exam's annotation,
    # a deleted note or a bare highlight.
    prompt = notes.prompts[0]
    assert "copy this one" not in prompt and "deleted thought" not in prompt
    context_ = notes.contexts[0]
    assert context_["topic"]["title"] == "Eigenvalues" and context_["passage"]["opening"]
    assert len(context_["notes"]) == 3 and any(SENTINEL in note["text"] for note in context_["notes"])
    # The marks sit beside the primary passage's start span.
    marks = call(ctx, "notes.marks", {"extraction_id": "ext_book"})["marks"]
    assert len(marks) == 1 and {n["noteKey"] for n in marks[0]["notes"]} == {corpus["typed"], corpus["captured"]}


def test_the_same_state_is_never_judged_twice_and_an_edited_note_is(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    call(ctx, "notes.path", {"goal_id": goal_id})
    call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})
    assert notes.calls == 1  # same candidates, same texts: answered from the ledger
    # The learner edits the note in the Reader: a new text, a new snapshot, judged again.
    edit_annotation(repository, _ref(corpus["typed"]), "Eigenvalues again: Av = lv, now with a picture.")
    out = call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})
    assert notes.calls == 2
    texts = [line["note"]["text"] for line in _lines(out)]
    assert any("now with a picture" in text for text in texts) and not any(SENTINEL in text for text in texts)
    assert _count(repository, "learner_notes") == 3  # the old snapshot is kept (append-only)


def test_one_tap_hides_a_link_and_it_stays_hidden_across_rejudgments(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    lines = _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
    typed = next(line for line in lines if line["noteKey"] == corpus["typed"])
    call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"})
    shown = _lines(call(ctx, "notes.path", {"goal_id": goal_id, "link": False}))
    assert _keys(shown) == {corpus["captured"]}
    with repository.connection() as connection:
        verdicts = connection.execute("SELECT verdict FROM judgment_ledger WHERE task = 'note_link' "
                                      "AND judge = 'learner_card'").fetchall()
    assert [row[0] for row in verdicts] == ["rejected"]
    # A re-judgment (an edited note) proposes it again: it stays hidden.
    edit_annotation(repository, _ref(corpus["typed"]), f"Eigenvalues: Av = lv. One more line. {SENTINEL}")
    again = _lines(call(ctx, "notes.path", {"goal_id": goal_id, "retry": True}))
    assert notes.calls == 2 and _keys(again) == {corpus["captured"]}
    # keep (undo) shows it again, still labelled as the model's link.
    hidden_ids = [row[0] for row in repository.connection().execute(
        "SELECT id FROM learner_note_links WHERE authorship = 'learner' AND status = 'rejected'")]
    call(ctx, "notes.decide", {"link_id": hidden_ids[0], "choice": "keep"})
    kept = _lines(call(ctx, "notes.path", {"goal_id": goal_id, "link": False}))
    assert _keys(kept) == {corpus["typed"], corpus["captured"]}
    assert all(line["byLabel"] == NL.BY_MODEL_LABEL for line in kept)


def test_a_learner_links_a_note_by_hand_from_the_reader(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    # No words: the notes for the passage's section title (exact words: embeddings are off).
    found = call(ctx, "notes.search", {"extraction_id": "ext_book", "span_id": "s2"})
    assert found["query"] == "Chapter 5 Eigenvalues" and found["mode"] == "words"
    assert {hit["noteKey"] for hit in found["hits"]} == {corpus["typed"], corpus["captured"], corpus["unrelated"]}
    # The learner's own words: exact words.
    typed = call(ctx, "notes.search", {"query": "2x2 example"})
    assert [hit["noteKey"] for hit in typed["hits"]] == [corpus["captured"]]
    hit = typed["hits"][0]
    assert hit["origin"] == "vault" and hit["refKind"] == "capture" and "2x2" in hit["snippet"]
    out = call(ctx, "notes.link", {"note": {"note_key": hit["noteKey"]}, "extraction_id": "ext_book", "span_id": "s2"})
    assert notes.calls == 0  # a link by hand is the learner's: no model
    mark = next(mark for mark in out["marks"] if mark["spanId"] == "s2")
    assert [(n["noteKey"], n["byLabel"]) for n in mark["notes"]] == [(corpus["captured"], NL.BY_YOU_LABEL)]
    # A note that is not one (beside the exam, deleted, or unknown): refused, nothing stored.
    before = _count(repository, "learner_notes")
    for key in (corpus["exam"], corpus["deleted"], "capture:nope"):
        with pytest.raises(SidecarError) as refused:
            call(ctx, "notes.link", {"note": {"note_key": key}, "extraction_id": "ext_book", "span_id": "s2"})
        assert refused.value.code == "unreadable"
    with pytest.raises(SidecarError) as malformed:
        call(ctx, "notes.link", {"note": {"note_key": "/home/x/notes.org#Eigen"}, "extraction_id": "ext_book",
                                 "span_id": "s2"})
    assert malformed.value.code == "validation_error" and _count(repository, "learner_notes") == before
    # Compare's your-take band lists it with the take that quotes it.
    band = call(ctx, "notes.passages", {"passages": [{"extraction_id": "ext_book", "span_id": "s2"}]})
    assert band["notes"] and band["notes"][0]["takeText"].startswith(NL.TAKE_PREFIX + " “captured note”, 3 Oct")
    assert "Worked the 2x2 eigen example" in band["notes"][0]["takeText"]


def test_meaning_search_is_refused_while_embeddings_are_off(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    with pytest.raises(SidecarError) as refused:
        call(ctx, "notes.search", {"query": "eigen", "mode": "meaning"})
    assert refused.value.code == "meaning_unavailable"
    with pytest.raises(SidecarError) as unknown:
        call(ctx, "notes.search", {"query": "eigen", "mode": "vibes"})
    assert unknown.value.code == "validation_error"


def test_a_metered_route_needs_its_price_and_a_route_down_waits_quietly(tmp_path):
    """C2b: note_link_judge takes ordinary quiet-route rules (no longer the plan only): a
    metered route without ``source_retrieval.llm_price_per_million`` sends nothing and waits;
    priced, it is asked inside the curriculum's daily cap; no client (models off) waits
    and no OpenRouter offer is made."""

    metered = MeteredNoteLinkFake()
    paths, repository, ctx, goal_id, corpus, _notes = _deliverable(tmp_path, notes=metered)
    out = call(ctx, "notes.path", {"goal_id": goal_id})
    assert metered.calls == 0 and out["lines"] == [] and _count(repository, "learner_notes") == 0
    assert out["linking"] == "waiting"
    plain = context(paths.root, notes_inline=True)
    with plan_fallback.collecting() as offers:
        assert call(plain, "notes.path", {"goal_id": goal_id})["linking"] == "waiting"
    assert offers.hint() is None and _count(repository, "learner_note_links") == 0
    assert "note_link_judge" not in plan_fallback.PLAN_ONLY_TASKS
    assert plan_fallback.offer_blocker(load_vault(paths.root).config, "note_link_judge") is None
    priced = tmp_path / "priced"
    paths2, repository2, ctx2, goal2, _corpus2, metered2 = _deliverable(
        priced, config="[source_retrieval]\nllm_price_per_million = 1.0\n", notes=MeteredNoteLinkFake())
    linked = call(ctx2, "notes.path", {"goal_id": goal2})
    assert metered2.calls == 1 and linked["linking"] == "done" and len(_lines(linked)) == 2


def test_switched_off_every_rpc_refuses_nothing_is_read_and_the_reader_is_todays(tmp_path, monkeypatch):
    paths, repository = build_deliverable_vault(tmp_path / "vault", config="[notes]\nenabled = false\n")
    corpus = eigen_notes(repository)
    notes = NoteLinkFake()
    ctx = _ctx(paths, note_link_client=notes)
    reads: list[str] = []
    real = VN.notes
    monkeypatch.setattr(VN, "notes", lambda *a, **k: reads.append("notes") or real(*a, **k))
    before = table_counts(repository)
    params = {"notes.path": {"goal_id": "g"}, "notes.marks": {"extraction_id": "ext_book"},
              "notes.passages": {"passages": [{"extraction_id": "ext_book", "span_id": "s2"}]},
              "notes.search": {"query": "eigen"},
              "notes.link": {"note": {"note_key": corpus["typed"]}, "extraction_id": "ext_book", "span_id": "s2"},
              "notes.decide": {"link_id": "nl_x", "choice": "hide"}, "notes.hidden": {},
              "notes.set_gaps": {"enabled": True}}
    for name in RPCS:
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params[name])
        assert caught.value.code == "notes_disabled", name
    assert notes.calls == 0 and reads == [] and table_counts(repository) == before
    contract = call(ctx, "reader.prompt_contract", {})
    assert "notes" not in contract
    assert normalized(call(context(paths.root), "reader.prompt_contract", {})) == normalized(contract)


def test_on_the_contract_in_every_vault_with_the_meaning_flag(tmp_path):
    from tests.notes_fixtures import turn_on_embeddings

    paths, _repository = build_deliverable_vault(tmp_path / "vault")
    contract = call(context(paths.root), "reader.prompt_contract", {})
    assert contract["notes"] == {"enabled": True, "meaning": False, "pocketNotesLabel": NL.POCKET_NOTES_LABEL,
                                 "takePrefix": NL.TAKE_PREFIX}
    on, _repository = build_deliverable_vault(tmp_path / "on")
    turn_on_embeddings(on)
    assert call(context(on.root), "reader.prompt_contract", {})["notes"]["meaning"] is True
    half, _repository = build_deliverable_vault(tmp_path / "half")
    turn_on_embeddings(half, backfill=False)
    assert call(context(half.root), "reader.prompt_contract", {})["notes"]["meaning"] is False


def test_the_rpcs_are_registered_and_desktop_only():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.handlers.notes import NOTES_RPCS
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert NOTES_RPCS == RPCS
    assert all(name in METHOD_REGISTRY and name not in ALLOWLIST for name in RPCS)


def test_the_report_counts_notes_without_their_text(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    lines = _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
    call(ctx, "notes.decide", {"link_id": lines[0]["linkId"], "choice": "hide"})
    row = NL.report_row(repository)
    assert row["proposals"] == 2 and row["hidden"] == 1 and row["hidden_share"] == 0.5 and row["takes"] == 0
    assert SENTINEL not in json.dumps(row)


# -- C2b: note text is learner text --------------------------------------------------------------

def test_the_judges_receipts_keep_the_prompt_like_any_learner_text(tmp_path):
    """C2b (owner, 2026-11-01): Codex review F3's withheld receipt input is dropped for notes:
    the judge's receipt keeps its prompt (the notes' text included) and its verdicts."""

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    call(ctx, "notes.path", {"goal_id": goal_id})
    assert notes.calls == 1
    with repository.connection() as connection:
        connection.row_factory = None
        receipts = connection.execute(
            "SELECT * FROM model_call_receipts WHERE purpose LIKE 'note_link_judge%'").fetchall()
        names = [column[0] for column in connection.execute(
            "SELECT * FROM model_call_receipts LIMIT 0").description]
    rows = [dict(zip(names, row)) for row in receipts]
    assert rows and any(row["input_text"] and SENTINEL in row["input_text"] for row in rows)
    assert any(row["output_text"] and "discusses" in row["output_text"] for row in rows)


def test_legacy_tend_snapshots_stay_readable(tmp_path):
    """C2's tend-era rows (origin tend / pocket_notes, a path and line) are history: they
    still render (a Pocket Notes page keeps its label) after migration 233."""

    from learnloop.db.stores import learner_notes as store

    paths, repository = build_deliverable_vault(tmp_path / "vault")
    with repository.atomic():
        connection = repository.connection()
        note_id = store.insert_note(connection, {
            "id": "ln_old", "note_key": "/n/2026-10-03.md#Eigen page", "path": "/n/2026-10-03.md",
            "heading_path": "Eigen page", "line": 1, "content_hash": "h-old", "title": "2026-10-03",
            "heading": "Eigen page", "captured_on": "2026-10-03", "origin": "pocket_notes",
            "text_md": "Worked it by hand.", "truncated": 0, "created_at": "2026-10-03T09:00:00Z"})
        store.insert_link(connection, {
            "id": "nl_old", "note_id": note_id, "note_key": "/n/2026-10-03.md#Eigen page", "target_kind": "passage",
            "target_key": "passage:ext_book/ch_eigen/s2", "learning_object_id": None, "extraction_id": "ext_book",
            "section_id": "ch_eigen", "span_id": "s2", "goal_id": None, "authorship": "learner",
            "status": "accepted", "how": None, "how_line": None, "state_key": None, "ledger_id": None,
            "model": None, "prompt_version": None, "created_at": "2026-10-03T09:00:00Z"})
    with repository.connection() as connection:
        rows = store.links(connection, extraction_id="ext_book")
    views = [NL.link_view(row, store.notes_by_id(repository.connection(), [row["note_id"]])[row["note_id"]])
             for row in rows]
    assert views[0]["note"]["origin"] == "pocket_notes" and views[0]["note"]["origin_label"] == NL.POCKET_NOTES_LABEL
    # The refresh never reads a tend-era note (there is no tend): it keeps its snapshot.
    assert NL.refresh_learner_links(load_vault(paths.root), repository) == 0


# -- Codex review (2026-11-01, C2), adapted to the vault's notes --------------------------------------

def _target(paths, repository, goal_id):
    vault = load_vault(paths.root)
    return vault, NL.path_targets(vault, repository, goal_id)[0]


def _reconfigured(paths, change):
    """The vault as it loads after the learner changed learnloop.toml (``change``: text to append)."""

    toml = paths.root / "learnloop.toml"
    original = toml.read_text(encoding="utf-8")
    toml.write_text(original + change, encoding="utf-8")
    try:
        return load_vault(paths.root)
    finally:
        toml.write_text(original, encoding="utf-8")


def test_f2_notes_switched_off_refuses_the_pending_request(tmp_path):
    """Codex review F2: the run started authorized, then the learner switched the notes off
    before the request: the request is refused at its admission (nothing sent) and nothing
    is written."""

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    vault, target = _target(paths, repository, goal_id)
    changed = _reconfigured(paths, "[notes]\nenabled = false\n")
    before = table_counts(repository)
    result = NL.judge_target(vault, repository, target, client=notes, live_vault=lambda: changed)
    assert result.status == "switched_off" and notes.calls == 0
    assert table_counts(repository) == before


def test_f2_switching_notes_off_during_the_request_records_nothing(tmp_path):
    paths, repository, ctx, goal_id, corpus, _notes = _deliverable(tmp_path)
    vault, target = _target(paths, repository, goal_id)
    live = {"vault": vault}
    off = _reconfigured(paths, "[notes]\nenabled = false\n")
    notes = NoteLinkFake(on_call=lambda: live.update(vault=off))  # the learner switches off meanwhile
    with repository.connection() as connection:
        ledger_before = connection.execute("SELECT COUNT(*) FROM judgment_ledger").fetchone()[0]
    result = NL.judge_target(vault, repository, target, client=notes, live_vault=lambda: live["vault"])
    assert result.status == "switched_off" and notes.calls == 1
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger").fetchone()[0] == ledger_before
    assert _count(repository, "learner_notes") == 0 and _count(repository, "learner_note_links") == 0
    run = NL.link_goal(vault, repository, goal_id, client=notes, live_vault=lambda: live["vault"])
    assert run.status == "switched_off" and notes.calls == 1


def test_f4_background_linking_completes_and_the_next_read_shows_it(tmp_path):
    from learnloop_sidecar.background_jobs import background_jobs

    paths, repository, _ctx_inline, goal_id, corpus, notes = _deliverable(tmp_path)
    ctx = _ctx(paths, note_link_client=notes)
    ctx.notes_inline = False
    first = call(ctx, "notes.path", {"goal_id": goal_id})
    assert first["linking"] in ("running", "done")
    for thread in background_jobs(ctx).running:
        thread.join(timeout=60)
    after = call(ctx, "notes.path", {"goal_id": goal_id})
    assert after["linking"] == "done" and _keys(_lines(after)) == {corpus["typed"], corpus["captured"]}
    assert notes.calls == 1


def test_f6_undo_shows_the_current_proposal_not_the_one_hidden(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    typed = next(line for line in _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
                 if line["noteKey"] == corpus["typed"])
    hidden = call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"})
    edit_annotation(repository, _ref(corpus["typed"]), "Eigenvalues: Av = lv. Edited after the hide.")
    call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})
    assert notes.calls == 2
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    kept = {line["noteKey"]: line for line in _lines(call(ctx, "notes.path", {"goal_id": goal_id, "link": False}))}
    assert "Edited after the hide." in kept[corpus["typed"]]["note"]["text"]
    assert kept[corpus["typed"]]["authorship"] == "ai" and kept[corpus["typed"]]["linkId"] != typed["linkId"]


def test_f7_returning_to_a_judged_state_shows_that_states_links_without_a_call(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    keys = lambda out: _keys(_lines(out))  # noqa: E731
    both = {corpus["typed"], corpus["captured"]}
    assert keys(call(ctx, "notes.path", {"goal_id": goal_id})) == both
    original = f"Eigenvalues: Av = lv, so det(A - lI) = 0. {SENTINEL}"
    edit_annotation(repository, _ref(corpus["typed"]), "Eigenvalues: something else.")
    assert keys(call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})) == {corpus["captured"]}  # state B
    edit_annotation(repository, _ref(corpus["typed"]), original)
    assert keys(call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})) == both
    assert notes.calls == 2  # A again was not paid again
    # No candidates at all: nothing shows.
    delete_annotation(repository, _ref(corpus["typed"]))
    dismiss_capture(repository, _ref(corpus["captured"]))
    dismiss_capture(repository, _ref(corpus["unrelated"]))
    assert keys(call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})) == set()
    assert call(ctx, "notes.marks", {"extraction_id": "ext_book"})["marks"] == []


def _link_typed_by_hand(ctx, corpus):
    return call(ctx, "notes.link", {"note": {"note_key": corpus["typed"]}, "extraction_id": "ext_book",
                                    "span_id": "s2"})


def _hand_texts(ctx):
    marks = call(ctx, "notes.marks", {"extraction_id": "ext_book"})["marks"]
    return [n["note"]["text"] for m in marks for n in m["notes"] if n["byLabel"] == NL.BY_YOU_LABEL]


def test_refresh_reads_a_hand_linked_note_again_from_the_vault(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    _link_typed_by_hand(ctx, corpus)
    vault = load_vault(paths.root)
    assert NL.refresh_learner_links(vault, repository) == 0  # unchanged
    edit_annotation(repository, _ref(corpus["typed"]), "Rewritten: Av = lv, redone.")
    assert NL.refresh_learner_links(vault, repository) == 1
    assert all("redone" in text for text in _hand_texts(ctx))
    assert _count(repository, "learner_note_links") == 1  # refreshing writes no link row
    # Deleted from the Reader: the last snapshot stays.
    delete_annotation(repository, _ref(corpus["typed"]))
    assert NL.refresh_learner_links(vault, repository) == 0
    assert all("redone" in text for text in _hand_texts(ctx))


def test_f9_a_link_hidden_during_the_refresh_stays_hidden(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    out = _link_typed_by_hand(ctx, corpus)
    edit_annotation(repository, _ref(corpus["typed"]), "Changed: Av = lv.")
    real_read = VN.read_many

    def read_while_hiding(*args, **kwargs):
        call(ctx, "notes.decide", {"link_id": out["linkId"], "choice": "hide"})
        return real_read(*args, **kwargs)

    monkeypatch.setattr(VN, "read_many", read_while_hiding)
    vault = load_vault(paths.root)
    links_before = _count(repository, "learner_note_links")
    assert NL.refresh_learner_links(vault, repository) == 0
    with repository.connection() as connection:
        rows = connection.execute("SELECT authorship, status FROM learner_note_links ORDER BY created_at, rowid").fetchall()
    assert len(rows) == links_before + 1 and tuple(rows[-1]) == ("learner", "rejected")
    assert _count(repository, "learner_notes") == 1  # nothing snapshotted for a hidden link
    monkeypatch.setattr(VN, "read_many", real_read)
    assert _hand_texts(ctx) == []


def _drop_first(verdicts):
    return verdicts[1:]


def _twice(verdicts):
    return verdicts + verdicts[:1]


def _unknown(verdicts):
    return verdicts + [{"note": "n99", "verdict": "unrelated"}]


def _discusses_without_how(verdicts):
    return [{**v, "how": None} if v["verdict"] == "discusses" else v for v in verdicts]


@pytest.mark.parametrize("shape", [lambda verdicts: [], _drop_first, _twice, _unknown, _discusses_without_how],
                         ids=["empty", "omitted", "duplicate", "unknown", "discusses_without_how"])
def test_f12_an_incomplete_answer_is_never_recorded_or_cached(tmp_path, shape):
    notes = NoteLinkFake(shape=shape)
    paths, repository, ctx, goal_id, corpus, _notes = _deliverable(tmp_path, notes=notes)
    out = call(ctx, "notes.path", {"goal_id": goal_id})
    assert out["linking"] == "waiting" and _lines(out) == [] and notes.calls >= 1
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task LIKE 'note_link%'").fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM model_work_checkpoints WHERE purpose LIKE 'note_link_judge%'").fetchone()[0] == 0
    assert _count(repository, "learner_note_links") == 0 and _count(repository, "learner_notes") == 0
    calls = notes.calls
    notes.shape = None
    again = call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})
    assert notes.calls == calls + 1 and _keys(_lines(again)) == {corpus["typed"], corpus["captured"]}


def test_f12_verdict_problem_names_each_defect():
    output = NL.NoteLinkOutputV1.model_validate({"notes": [
        {"note": "n1", "verdict": "discusses", "about": "passage", "how": "restates"},
        {"note": "n1", "verdict": "unrelated"}, {"note": "n9", "verdict": "unrelated"},
        {"note": "n3", "verdict": "discusses", "about": None, "how": "applies"}]})
    problem = NL.verdict_problem(output, ["n1", "n2", "n3"])
    assert "unknown notes: n9" in problem and "without a verdict: n2" in problem
    assert "judged twice: n1" in problem and "discusses without about and how: n3" in problem
    good = NL.NoteLinkOutputV1.model_validate({"notes": [{"note": "n1", "verdict": "unrelated"}]})
    assert NL.verdict_problem(good, ["n1"]) is None


class _Published:
    """A loaded-vault provider shaped as the sidecar's (``snapshot()`` and a
    generation-bound ``admit``): ``publish`` is a settings reload."""

    def __init__(self, vault):
        self.vault, self.generation = vault, 1

    def publish(self, vault):
        self.vault, self.generation = vault, self.generation + 1

    def __call__(self):
        return self.vault

    def snapshot(self):
        return self.vault, self.generation

    def admit(self, generation):
        return generation == self.generation


def _reload_during_notes_reading(monkeypatch, provider, to):
    """Publish ``to`` right after the guard reads the notes switch for the ``at``-th time."""

    real = NL.enabled
    plan = {"at": None, "readings": 0}

    def reading(vault):
        out = real(vault)
        plan["readings"] += 1
        if plan["at"] == plan["readings"]:
            provider.publish(to)
        return out

    monkeypatch.setattr(NL, "enabled", reading)
    return plan


def test_re_f2_the_composed_gate_admits_on_one_snapshot(tmp_path, monkeypatch):
    from learnloop.source_retrieval import section_coverage as SC

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    vault, target = _target(paths, repository, goal_id)
    provider = _Published(vault)
    plan = _reload_during_notes_reading(monkeypatch, provider, _reconfigured(paths, "[notes]\nenabled = false\n"))
    guard = NL.NotesGuard(vault, live_vault=provider).with_coverage(
        SC.Library(vault, repository), [(target.extraction_id, target.section_id)])
    plan["at"] = plan["readings"] + 1  # the admission's notes reading
    with pytest.raises(NL.NotesSwitchedOff):
        guard.admit(notes, purpose="note_link_judge", prompt="p", budget=None)
    provider.publish(vault)  # switched on again: the judgment still refuses
    with pytest.raises(NL.NotesSwitchedOff):
        guard.check("recording note links")
    with pytest.raises(NL.NotesSwitchedOff):
        guard.check_notes("recording which notes show")


def test_re_f2_an_unchanged_reload_still_links(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    vault, target = _target(paths, repository, goal_id)
    provider = _Published(vault)
    plan = _reload_during_notes_reading(monkeypatch, provider, load_vault(paths.root))
    plan["at"] = 2
    result = NL.judge_target(vault, repository, target, client=notes, live_vault=provider)
    assert result.status == "linked" and notes.calls == 1


def test_re_f13_a_note_linked_by_hand_changed_and_changed_back_shows_its_text_now(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    _link_typed_by_hand(ctx, corpus)
    original = f"Eigenvalues: Av = lv, so det(A - lI) = 0. {SENTINEL}"
    vault = load_vault(paths.root)
    refresh = lambda: NL.refresh_learner_links(vault, repository)  # noqa: E731
    edit_annotation(repository, _ref(corpus["typed"]), "Version B of the note.")
    assert refresh() == 1 and all("Version B" in text for text in _hand_texts(ctx))
    edit_annotation(repository, _ref(corpus["typed"]), original)
    assert refresh() == 1
    texts = _hand_texts(ctx)
    assert texts and all(SENTINEL in text and "Version B" not in text for text in texts)
    assert _count(repository, "learner_notes") == 2 and _count(repository, "learner_note_links") == 1
    assert refresh() == 0


def test_re_f14_a_waiting_run_is_not_restarted_by_every_read(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import notes as NH

    metered = MeteredNoteLinkFake()  # unpriced: the run waits
    paths, repository, ctx, goal_id, corpus, _notes = _deliverable(tmp_path, notes=metered)
    searches = {"n": 0}
    real = VN.notes

    def counted(*args, **kwargs):
        searches["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(VN, "notes", counted)
    clock = {"now": 1000.0}
    monkeypatch.setattr(NH, "_monotonic", lambda: clock["now"])
    assert call(ctx, "notes.path", {"goal_id": goal_id})["linking"] == "waiting"
    seen = searches["n"]
    assert seen > 0
    for _poll in range(3):
        assert call(ctx, "notes.path", {"goal_id": goal_id})["linking"] == "waiting"
    assert searches["n"] == seen
    clock["now"] += NL.WAITING_RETRY_SECONDS
    assert call(ctx, "notes.path", {"goal_id": goal_id})["linking"] == "waiting"
    assert searches["n"] > seen
    seen = searches["n"]
    assert call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})["linking"] == "waiting"
    assert searches["n"] > seen and metered.calls == 0


def test_re3_f13_a_delayed_judgment_never_makes_its_snapshot_current_again(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    _link_typed_by_hand(ctx, corpus)
    vault, target = _target(paths, repository, goal_id)
    refreshed: list[int] = []

    def meanwhile():  # the judgment of A is held here, at the model
        edit_annotation(repository, _ref(corpus["typed"]), "Version B: Av = lv.")
        refreshed.append(NL.refresh_learner_links(vault, repository))

    notes.on_call = meanwhile
    result = NL.judge_target(vault, repository, target, client=notes)
    assert result.status == "linked" and notes.calls == 1 and refreshed == [1]
    texts = _hand_texts(ctx)
    assert texts and all("Version B" in text for text in texts)
    proposed = [line for line in _lines(call(ctx, "notes.path", {"goal_id": goal_id, "link": False}))
                if line["authorship"] == "ai" and line["noteKey"] == corpus["typed"]]
    assert proposed and SENTINEL in proposed[0]["note"]["text"]
    with repository.connection() as connection:
        markers = connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task = ?",
                                     (NL.CURRENT_TASK,)).fetchone()[0]
    assert markers == 2


# -- C2 ruling R6 (followups-nov1c A): monotonic read tokens, published by token order ------------
# Ported at C2b's landing from main's tend-era tests: the note is read again from the vault
# (VN.read_many), not from tend.

def test_r6_two_concurrent_refreshes_resolve_to_the_newest_read(tmp_path, monkeypatch):
    """C2 ruling R6, the round-3 verify's first ordering: two refreshes of the same hand-linked
    note run concurrently; the older one (started first, it reads B) writes first and the
    newer one (started after the note changed to C, it reads C) writes second. Each read takes
    a monotonic token when it starts and publishes by token order, so C (the newest read)
    shows, whichever writes first."""

    import threading

    from learnloop.db.repositories import Repository

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    _link_typed_by_hand(ctx, corpus)
    edit_annotation(repository, _ref(corpus["typed"]), "Version B of the note.")
    vault = load_vault(paths.root)
    real_read = VN.read_many
    older_read, newer_read, older_done = threading.Event(), threading.Event(), threading.Event()

    def read(*args, **kwargs):
        result = real_read(*args, **kwargs)
        if threading.current_thread().name == "r6-older":
            older_read.set()
            assert newer_read.wait(20)  # the newer refresh started (and read) before this one writes
        elif threading.current_thread().name == "r6-newer":
            newer_read.set()
            assert older_done.wait(20)  # ... and writes only after this one wrote
        return result

    monkeypatch.setattr(VN, "read_many", read)
    results: dict[str, int] = {}

    def run(name: str) -> None:
        try:
            results[name] = NL.refresh_learner_links(vault, Repository.attach(repository.sqlite_path))
        finally:
            if name == "r6-older":
                older_done.set()

    older = threading.Thread(target=run, args=("r6-older",), name="r6-older")
    older.start()
    assert older_read.wait(20)
    edit_annotation(repository, _ref(corpus["typed"]), "Version C of the note.")
    newer = threading.Thread(target=run, args=("r6-newer",), name="r6-newer")
    newer.start()
    older.join(30)
    newer.join(30)
    assert not older.is_alive() and not newer.is_alive()
    monkeypatch.setattr(VN, "read_many", real_read)
    assert results == {"r6-older": 1, "r6-newer": 1}  # both published, in token order
    texts = _hand_texts(ctx)
    assert texts and all("Version C" in text for text in texts)  # the newest read shows


def test_r6_an_unchanged_read_fences_off_an_older_refresh_in_flight(tmp_path, monkeypatch):
    """C2 ruling R6, the round-3 verify's second ordering: the note shows A; a refresh reads B
    slowly; meanwhile the note changes back to A and a newer refresh reads A, unchanged. The
    unchanged read advances the fence (a marker naming the snapshot already shown), so the
    older refresh writes nothing and A (the newest read) stays shown."""

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    _link_typed_by_hand(ctx, corpus)
    original = f"Eigenvalues: Av = lv, so det(A - lI) = 0. {SENTINEL}"
    edit_annotation(repository, _ref(corpus["typed"]), "Version B of the note.")
    vault = load_vault(paths.root)
    refresh = lambda: NL.refresh_learner_links(vault, repository)  # noqa: E731
    real_read = VN.read_many
    inner: list[int] = []

    def slow_read(*args, **kwargs):
        result = real_read(*args, **kwargs)  # B, read before the note changed back
        monkeypatch.setattr(VN, "read_many", real_read)
        edit_annotation(repository, _ref(corpus["typed"]), original)
        inner.append(refresh())  # reads A: unchanged, nothing to refresh, but it fences
        return result

    monkeypatch.setattr(VN, "read_many", slow_read)
    assert refresh() == 0 and inner == [0]
    texts = _hand_texts(ctx)
    assert texts and all(SENTINEL in text and "Version B" not in text for text in texts)
    with repository.connection() as connection:
        stored = [row[0] for row in connection.execute("SELECT text_md FROM learner_notes")]
    assert not any("Version B" in text for text in stored)  # the older read stored nothing
    assert _count(repository, "learner_note_links") == 1  # and no link row: refreshing is never an acceptance


# -- C2 ruling R5 (followups-nov1c C): Settings' hidden notes, with show again ------------------

def test_r5_settings_lists_the_hidden_notes_and_show_again_unhides_through_decide(tmp_path, monkeypatch):
    """C2 ruling R5 / open question 4: ``notes.hidden`` lists the learner's standing hides,
    newest first, naming each note (title, heading, date; never its text or where it lives),
    where it was linked and who linked it; *show again* is the existing ``notes.decide keep``
    (a ``learner_card`` verdict reversing the hide). No vault-notes read and no model call."""

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    model_link = next(line for line in _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
                      if line["authorship"] == "ai" and line["noteKey"] == corpus["captured"])
    hand = _link_typed_by_hand(ctx, corpus)
    assert call(ctx, "notes.hidden", {})["hidden"] == []
    call(ctx, "notes.decide", {"link_id": model_link["linkId"], "choice": "hide"})
    call(ctx, "notes.decide", {"link_id": hand["linkId"], "choice": "hide"})
    reads: list[str] = []
    real_notes, real_read = VN.notes, VN.read_many
    monkeypatch.setattr(VN, "notes", lambda *a, **k: reads.append("notes") or real_notes(*a, **k))
    monkeypatch.setattr(VN, "read_many", lambda *a, **k: reads.append("read") or real_read(*a, **k))
    model_calls = notes.calls
    listed = call(ctx, "notes.hidden", {})["hidden"]
    assert reads == [] and notes.calls == model_calls  # no vault-notes read, no model
    by_hand, by_model = listed  # newest first
    assert by_hand["byLabel"] == NL.BY_YOU_LABEL and by_hand["targetKind"] == "passage"
    assert by_hand["note"]["dateLabel"] and by_hand["note"]["originLabel"] is None
    assert by_model["byLabel"] == NL.BY_MODEL_LABEL and by_model["where"] == "the topic “Eigenvalues”"
    assert by_model["learningObjectId"] == "lo_eigen"
    text = json.dumps(listed)
    assert SENTINEL not in text and "eigen example" not in text and "text" not in by_hand["note"]  # no text
    monkeypatch.setattr(VN, "notes", real_notes)
    monkeypatch.setattr(VN, "read_many", real_read)
    # Show again: the existing decide path (keep), a learner_card verdict reversing the hide.
    call(ctx, "notes.decide", {"link_id": by_hand["linkId"], "choice": "keep"})
    assert [entry["linkId"] for entry in call(ctx, "notes.hidden", {})["hidden"]] == [by_model["linkId"]]
    assert _hand_texts(ctx)  # the hand link shows again beside its passage
    call(ctx, "notes.decide", {"link_id": by_model["linkId"], "choice": "keep"})
    assert call(ctx, "notes.hidden", {})["hidden"] == []
    shown = _keys(_lines(call(ctx, "notes.path", {"goal_id": goal_id, "link": False})))
    assert corpus["captured"] in shown  # the model's link shows again: still the topic's current proposal
    with repository.connection() as connection:
        verdicts = [row[0] for row in connection.execute(
            "SELECT verdict FROM judgment_ledger WHERE task = 'note_link' AND judge = 'learner_card' "
            "ORDER BY rowid")]
    assert verdicts[-4:] == ["rejected", "rejected", "accepted", "accepted"]


def test_landing_c2b_a_hidden_note_beside_material_protected_since_is_not_listed(tmp_path):
    """C2b's landing (main's R5 list is a new delivery boundary): a Reader note hidden while
    its section was readable, then its section held out, is not listed (its title and its
    source-derived heading are never delivered again); the hide row stays."""

    from tests.notes_fixtures import add_annotation
    from tests.section_coverage_fixtures import hold_out

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    lay = "annotation:" + add_annotation(repository, "My own words on Lay's section.", extraction_id="ext_lay",
                                         span_id="s2", source_id="src_lay", revision_id="rev_lay")
    out = call(ctx, "notes.link", {"note": {"note_key": lay}, "extraction_id": "ext_book", "span_id": "s2"})
    call(ctx, "notes.decide", {"link_id": out["linkId"], "choice": "hide"})
    assert [entry["linkId"] for entry in call(ctx, "notes.hidden", {})["hidden"]] == [out["linkId"]]
    links = _count(repository, "learner_note_links")
    hold_out(repository, "lay_eigen")
    assert call(ctx, "notes.hidden", {})["hidden"] == []
    assert _count(repository, "learner_note_links") == links


def test_r6_review_f2_a_clock_correction_and_restart_never_blocks_later_refreshes(tmp_path, monkeypatch):
    """Codex review F2: a note published a token while the machine clock ran an hour ahead;
    the clock is then corrected and LearnLoop restarts (a fresh process: its ULID state
    starts over), so the wall clock now mints ULIDs that sort below the persisted fence. A
    read's token sorts after the newest token already published (read from the database when
    the read starts), so each refresh after the restart publishes its changed text."""

    from learnloop import ids

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    now_ms = ids._wall_clock_ms()
    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)
    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: now_ms + 3_600_000)  # an hour ahead
    _link_typed_by_hand(ctx, corpus)  # publishes the first snapshot with a future token
    vault = load_vault(paths.root)
    # The clock is corrected and LearnLoop restarts: the generator's in-process floor is gone.
    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)
    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: now_ms)
    for version in ("B", "C", "D"):
        edit_annotation(repository, _ref(corpus["typed"]), f"Version {version} of the note.")
        assert NL.refresh_learner_links(vault, repository) == 1
        texts = _hand_texts(ctx)
        assert texts and all(f"Version {version}" in text for text in texts)


# -- Landing: CoverageGuard's two hooks (C1's gate, C2's also) on one guard -----------------------

def test_landing_the_coverage_guard_composes_c1s_gate_and_c2s_also(tmp_path):
    from learnloop.source_retrieval import section_coverage as SC

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    vault, target = _target(paths, repository, goal_id)
    library = SC.Library(vault, repository)
    keys = [(target.extraction_id, target.section_id)]
    provider = _Published(vault)

    def guard(gate, also):
        return SC.CoverageGuard(library, keys, live_vault=provider, gate=lambda _vault: gate,
                                also=lambda _vault: also, also_refusal=NL.NotesSwitchedOff)

    guard(True, None).check("request")
    with pytest.raises(SC.GateClosed):
        guard(False, None).check("request")
    with pytest.raises(NL.NotesSwitchedOff):
        guard(True, "notes switched off").check("request")
    closed = guard(False, None)
    with pytest.raises(SC.GateClosed):
        closed.admit(notes, purpose="request", prompt="p", budget=None)
    with pytest.raises(SC.GateClosed):
        closed.check("record")


def test_a_capture_is_a_note_and_a_dismissed_one_is_not(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    kept = add_capture(repository, "Spectral theorem: symmetric means orthogonal eigenvectors.")
    gone = add_capture(repository, "Spectral idea I dismissed.")
    dismiss_capture(repository, gone)
    vault = load_vault(paths.root)
    keys = {note.note_key for note in VN.notes(vault, repository)}
    assert f"capture:{kept}" in keys and f"capture:{gone}" not in keys
