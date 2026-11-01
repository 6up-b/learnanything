"""Curriculum C2: notes in the learner's voice, linked (spec_deliverable_curriculum_v1 §10, §12 C2, §12.3).

Every tend here is the FAKE executable (tests/notes_fixtures.py) over synthetic notes in
tmp; the owner's real tend and notes are never reached. Every model is a fake; background
work runs inline (``notes_inline``).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from learnloop.ai import plan_fallback
from learnloop.curriculum import notes_tend as NT
from learnloop.source_retrieval import note_links as NL
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.deliverable_fixtures import DeliverableFake, build_deliverable_vault
from tests.notes_fixtures import (SENTINEL, MeteredNoteLinkFake, NoteLinkFake, eigen_corpus, install_fake_tend)
from tests.reading_path_fixtures import call, context, normalized
from tests.section_coverage_fixtures import CoverageJudgeFake, table_counts

RPCS = ("notes.path", "notes.marks", "notes.passages", "notes.search", "notes.link", "notes.decide")


def _ctx(paths, **attrs):
    fake = attrs.pop("fake", None) or DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"})
    return context(paths.root, deliverable_inline=True, notes_inline=True, coverage_judge_client=CoverageJudgeFake(),
                   deliverable_scope_client=fake, deliverable_path_client=fake, **attrs)


def _deliverable(tmp_path: Path, monkeypatch, *, config: str = "", mode: str = "", lexical_only: bool = False,
                 notes: NoteLinkFake | None = None):
    """A deliverable vault with a judged path for lo_eigen (primary ch_eigen in ext_book),
    the fake tend over the eigen corpus, and the sidecar context."""

    fake_tend = install_fake_tend(tmp_path / "tend", monkeypatch, mode=mode)
    corpus = eigen_corpus(fake_tend)
    paths, repository = build_deliverable_vault(tmp_path / "vault",
                                                config=fake_tend.config(lexical_only=lexical_only) + config)
    notes = notes or NoteLinkFake()
    ctx = _ctx(paths, note_link_client=notes)
    created = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues for my midterm"})
    goal_id = created["goalId"]
    view = call(ctx, "curriculum.set_depth", {"goal_id": goal_id, "depth": "learn_to_use_it"})
    assert view["status"] == "ready"
    return paths, repository, ctx, goal_id, fake_tend, corpus, notes


def _lines(out, lo: str = "lo_eigen") -> list:
    return next((entry["notes"] for entry in out["lines"] if entry["learningObjectId"] == lo), [])


def _count(repository, table: str) -> int:
    with repository.connection() as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


# -- the adapter -------------------------------------------------------------------------------------

def _settings(fake_tend, *, lexical_only: bool = False) -> NT.TendSettings:
    roots = tuple(Path(p).resolve() for p in (fake_tend.notes, fake_tend.quicknote))
    return NT.TendSettings(binary=str(fake_tend.binary), roots=roots, pocket_roots=(fake_tend.pocket.resolve(),),
                           lexical_only=lexical_only, timeout=5.0, k=10)


def test_the_adapter_drops_every_hit_outside_the_allowlist_and_another_machines(tmp_path, monkeypatch):
    fake_tend = install_fake_tend(tmp_path / "tend", monkeypatch)
    corpus = eigen_corpus(fake_tend)
    hits = NT.search(_settings(fake_tend), "Eigenvalues")
    paths = {hit.path for hit in hits}
    assert str(Path(corpus["typed"]["path"]).resolve()) in paths and str(Path(corpus["pocket"]["path"]).resolve()) in paths
    assert corpus["outside"]["path"] not in paths  # a project repository: never returned
    assert all(hit.heading != "Eigen remote" for hit in hits)  # another machine's hit: never returned
    pocket = next(hit for hit in hits if hit.heading == "Eigen page")
    assert pocket.origin == "pocket_notes" and pocket.captured_on is not None
    # The command: tend's JSON search, this machine only, notes only, the query after "--".
    argv = fake_tend.calls()[-1]
    assert argv[:2] == ["search", "-k"] and {"--json", "--local", "--notes-only"} <= set(argv)
    assert "--words" not in argv and argv[-2:] == ["--", "Eigenvalues"]


def test_lexical_only_asks_tend_for_words_only(tmp_path, monkeypatch):
    fake_tend = install_fake_tend(tmp_path / "tend", monkeypatch)
    eigen_corpus(fake_tend)
    NT.search(_settings(fake_tend, lexical_only=True), "Eigenvalues")
    assert "--words" in fake_tend.calls()[-1]


def test_reads_go_through_tends_read_op_and_a_refused_note_is_dropped(tmp_path, monkeypatch):
    fake_tend = install_fake_tend(tmp_path / "tend", monkeypatch)
    eigen_corpus(fake_tend)
    settings = _settings(fake_tend)
    hits = NT.search(settings, "Eigenvalues")
    texts = NT.read_sections(settings, hits)
    typed = next(text for text in texts.values() if text.hit.heading == "Eigen stuff")
    assert typed.read_via == "tend" and SENTINEL in typed.text
    assert "Unrelated text" not in typed.text  # the heading section only: up to the next heading
    assert all(text.hit.heading != "Eigen private" for text in texts.values())  # tend refused it: dropped
    assert ["serve"] in fake_tend.calls()


def test_without_a_read_op_the_section_is_read_from_the_file_inside_the_allowlist(tmp_path, monkeypatch):
    fake_tend = install_fake_tend(tmp_path / "tend", monkeypatch, mode="no_read")
    corpus = eigen_corpus(fake_tend)
    settings = _settings(fake_tend)
    hits = NT.search(settings, "Eigenvalues")
    texts = NT.read_sections(settings, hits)
    assert {text.read_via for text in texts.values()} == {"file"}
    assert any(SENTINEL in text.text for text in texts.values())
    # A hit outside the allowlist is never read, even by the fallback.
    outside = NT.NoteHit(path=corpus["outside"]["path"], heading_path="Eigen solver", title="README", line=1,
                         snippet="", content_hash="", mtime=0.0, via="", origin="tend")
    assert NT.read_sections(settings, [outside]) == {}


def test_a_stalled_tend_times_out_and_an_absent_tend_hides_the_notes(tmp_path, monkeypatch):
    fake_tend = install_fake_tend(tmp_path / "tend", monkeypatch, mode="slow")
    settings = NT.TendSettings(**{**_settings(fake_tend).__dict__, "timeout": 1.0})
    with pytest.raises(NT.TendUnavailable) as caught:
        NT.search(settings, "Eigenvalues")
    assert caught.value.reason == "timeout"
    monkeypatch.setenv("LEARNLOOP_NOTES_TEND", "off")
    paths, _repository = build_deliverable_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    assert NT.executable(vault.config) is None and not NL.available(vault)
    assert "notes" not in call(context(paths.root), "reader.prompt_contract", {})
    with pytest.raises(SidecarError) as refused:
        call(context(paths.root), "notes.marks", {"extraction_id": "ext_book"})
    assert refused.value.code == "notes_unavailable"


def test_the_section_slice_follows_tends_heading_boundary():
    org = "#+title: t\n* A\nline a\n#+begin_src\n* not a heading\n#+end_src\nmore\n** B\nline b\n"
    assert NT.slice_section(org, 2, org=True) == "* A\nline a\n#+begin_src\n* not a heading\n#+end_src\nmore"
    md = "# A\ntext\n```\n# code\n```\n## B\nb\n"
    assert NT.slice_section(md, 1, org=False) == "# A\ntext\n```\n# code\n```"


# -- linking: candidates, the judgment, proposals --------------------------------------------------

def test_the_path_links_the_notes_that_discuss_it_and_stores_only_linked_notes(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    out = call(ctx, "notes.path", {"goal_id": goal_id})
    assert notes.calls == 1
    lines = _lines(out)
    by_heading = {line["note"]["heading"]: line for line in lines}
    assert set(by_heading) == {"Eigen stuff", "Eigen page"}  # the unrelated note is not linked
    assert by_heading["Eigen page"]["note"]["originLabel"] == NL.POCKET_NOTES_LABEL
    assert by_heading["Eigen stuff"]["note"]["originLabel"] is None
    assert all(line["byLabel"] == NL.BY_MODEL_LABEL and line["authorship"] == "ai" for line in lines)
    assert by_heading["Eigen stuff"]["line"].startswith("your note from ")
    # Only linked notes are stored; nothing of the unrelated, outside, remote or private notes.
    assert _count(repository, "learner_notes") == 2
    with repository.connection() as connection:
        stored = " ".join(str(row[0]) for row in connection.execute("SELECT text_md || path FROM learner_notes"))
        ledger = " ".join(str(row[0]) for row in connection.execute(
            "SELECT right_id || rationale FROM judgment_ledger WHERE task = 'note_link'"))
    assert "groceries" not in stored and "Eigen private" not in stored and "README" not in stored
    assert "groceries" not in ledger and str(fake_tend.notes) not in ledger  # the ledger names notes by digest
    # The judge read the LO, its passage's lead and the candidates; never an outside, remote or private note.
    prompt = notes.prompts[0]
    assert "Project docs about eigenvalues" not in prompt and "on the laptop" not in prompt
    assert "Eigenvalues, private" not in prompt
    context_ = notes.contexts[0]
    assert context_["topic"]["title"] == "Eigenvalues" and context_["passage"]["opening"]
    # The marks sit beside the primary passage's start span.
    marks = call(ctx, "notes.marks", {"extraction_id": "ext_book"})["marks"]
    assert len(marks) == 1 and {note["note"]["heading"] for note in marks[0]["notes"]} == {"Eigen stuff", "Eigen page"}


def test_the_same_state_is_never_judged_twice_and_a_new_content_hash_is(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    call(ctx, "notes.path", {"goal_id": goal_id})
    call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})
    assert notes.calls == 1  # same candidates, same hashes: answered from the ledger
    # The note changes: tend reports a new content hash; the snapshot is refreshed and re-judged.
    entry = next(e for e in fake_tend.entries if e["hit"]["heading"] == "Eigen stuff")
    Path(entry["hit"]["path"]).write_text("* Eigen stuff\nEigenvalues again: Av = lv, now with a picture.\n",
                                          encoding="utf-8")
    entry["hit"]["hash"] = "h-new"
    entry["hit"]["line"] = 1
    fake_tend.save()
    out = call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})
    assert notes.calls == 2
    texts = [line["note"]["text"] for line in _lines(out)]
    assert any("now with a picture" in text for text in texts) and not any(SENTINEL in text for text in texts)
    assert _count(repository, "learner_notes") == 3  # the old snapshot is kept (append-only)


def test_one_tap_hides_a_link_and_it_stays_hidden_across_rejudgments(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    lines = _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
    typed = next(line for line in lines if line["note"]["heading"] == "Eigen stuff")
    call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"})
    shown = _lines(call(ctx, "notes.path", {"goal_id": goal_id, "link": False}))
    assert [line["note"]["heading"] for line in shown] == ["Eigen page"]
    with repository.connection() as connection:
        verdicts = connection.execute("SELECT verdict FROM judgment_ledger WHERE task = 'note_link' "
                                      "AND judge = 'learner_card'").fetchall()
    assert [row[0] for row in verdicts] == ["rejected"]
    # A re-judgment (a new hash) proposes it again: it stays hidden.
    entry = next(e for e in fake_tend.entries if e["hit"]["heading"] == "Eigen stuff")
    entry["hit"]["hash"] = "h-again"
    fake_tend.save()
    note_file = Path(entry["hit"]["path"])
    note_file.write_text(note_file.read_text(encoding="utf-8").replace("* Other", "One more line.\n* Other"),
                         encoding="utf-8")
    again = _lines(call(ctx, "notes.path", {"goal_id": goal_id, "retry": True}))
    assert notes.calls == 2 and [line["note"]["heading"] for line in again] == ["Eigen page"]
    # keep (undo) shows it again, still labelled as the model's link.
    hidden_ids = [row[0] for row in repository.connection().execute(
        "SELECT id FROM learner_note_links WHERE authorship = 'learner' AND status = 'rejected'")]
    call(ctx, "notes.decide", {"link_id": hidden_ids[0], "choice": "keep"})
    kept = _lines(call(ctx, "notes.path", {"goal_id": goal_id, "link": False}))
    assert {line["note"]["heading"] for line in kept} == {"Eigen stuff", "Eigen page"}
    assert all(line["byLabel"] == NL.BY_MODEL_LABEL for line in kept)


def test_a_learner_links_a_note_by_hand_from_the_reader(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    # No words: tend's hits for the passage's section title.
    found = call(ctx, "notes.search", {"extraction_id": "ext_book", "span_id": "s2"})
    # The learner's own words: searched by words only (never leaves the machine).
    typed = call(ctx, "notes.search", {"query": "my eigenvalues page"})
    assert "--words" in fake_tend.calls()[-1]
    hit = next(h for h in typed["hits"] if h["heading"] == "Eigen page")
    assert all(h["path"] != corpus["outside"]["path"] for h in typed["hits"] + found["hits"])
    out = call(ctx, "notes.link", {"note": {"path": hit["path"], "line": hit["line"], "heading_path": hit["headingPath"],
                                            "title": hit["title"], "content_hash": hit["contentHash"],
                                            "mtime": hit["mtime"]},
                                   "extraction_id": "ext_book", "span_id": "s2"})
    assert notes.calls == 0  # a link by hand is the learner's: no model
    mark = next(mark for mark in out["marks"] if mark["spanId"] == "s2")
    assert [(n["note"]["heading"], n["byLabel"]) for n in mark["notes"]] == [("Eigen page", NL.BY_YOU_LABEL)]
    # Outside the allowlist: refused, nothing stored.
    before = _count(repository, "learner_notes")
    with pytest.raises(SidecarError) as refused:
        call(ctx, "notes.link", {"note": {"path": corpus["outside"]["path"], "line": 1},
                                 "extraction_id": "ext_book", "span_id": "s2"})
    assert refused.value.code == "not_allowed" and _count(repository, "learner_notes") == before
    # Compare's your-take band lists it with the take that quotes it.
    band = call(ctx, "notes.passages", {"passages": [{"extraction_id": "ext_book", "span_id": "s2"}]})
    assert band["notes"] and band["notes"][0]["takeText"].startswith(NL.TAKE_PREFIX + " “2026-10-03 › Eigen page”")
    assert "Worked the 2x2 eigen example" in band["notes"][0]["takeText"]


def test_a_metered_route_is_refused_and_plan_down_waits_quietly(tmp_path, monkeypatch):
    metered = MeteredNoteLinkFake()
    paths, repository, ctx, goal_id, fake_tend, corpus, _notes = _deliverable(tmp_path, monkeypatch, notes=metered)
    out = call(ctx, "notes.path", {"goal_id": goal_id})
    assert metered.calls == 0 and out["lines"] == [] and _count(repository, "learner_notes") == 0
    assert out["linking"] == "waiting"
    # No client and models off (the plan down, for the job): it waits; no OpenRouter offer is made.
    plain = context(paths.root, notes_inline=True)
    with plan_fallback.collecting() as offers:
        assert call(plain, "notes.path", {"goal_id": goal_id})["linking"] == "waiting"
    assert offers.hint() is None and _count(repository, "learner_note_links") == 0
    assert plan_fallback.offer_blocker(load_vault(paths.root).config, "note_link_judge") is not None


def test_switched_off_every_rpc_refuses_nothing_is_called_and_the_reader_is_todays(tmp_path, monkeypatch):
    fake_tend = install_fake_tend(tmp_path / "tend", monkeypatch)
    eigen_corpus(fake_tend)
    paths, repository = build_deliverable_vault(tmp_path / "vault",
                                                config=fake_tend.config() + "[notes]\nenabled = false\n")
    notes = NoteLinkFake()
    ctx = _ctx(paths, note_link_client=notes)
    before = table_counts(repository)
    params = {"notes.path": {"goal_id": "g"}, "notes.marks": {"extraction_id": "ext_book"},
              "notes.passages": {"passages": [{"extraction_id": "ext_book", "span_id": "s2"}]},
              "notes.search": {"query": "eigen"},
              "notes.link": {"note": {"path": str(fake_tend.notes / "linear.org"), "line": 2},
                             "extraction_id": "ext_book", "span_id": "s2"},
              "notes.decide": {"link_id": "nl_x", "choice": "hide"}}
    for name in RPCS:
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params[name])
        assert caught.value.code == "notes_disabled", name
    assert notes.calls == 0 and fake_tend.calls() == [] and table_counts(repository) == before
    contract = call(ctx, "reader.prompt_contract", {})
    assert "notes" not in contract
    monkeypatch.setenv("LEARNLOOP_NOTES_TEND", "off")
    assert normalized(call(context(paths.root), "reader.prompt_contract", {})) == normalized(contract)


def test_on_the_contract_only_when_on_and_tend_is_installed(tmp_path, monkeypatch):
    fake_tend = install_fake_tend(tmp_path / "tend", monkeypatch)
    paths, _repository = build_deliverable_vault(tmp_path / "vault", config=fake_tend.config(lexical_only=True))
    contract = call(context(paths.root), "reader.prompt_contract", {})
    assert contract["notes"] == {"enabled": True, "lexicalOnly": True, "pocketNotesLabel": NL.POCKET_NOTES_LABEL,
                                 "takePrefix": NL.TAKE_PREFIX}
    assert fake_tend.calls() == []  # the contract runs no tend


def test_the_rpcs_are_registered_and_desktop_only():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.handlers.notes import NOTES_RPCS
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert NOTES_RPCS == RPCS
    assert all(name in METHOD_REGISTRY and name not in ALLOWLIST for name in RPCS)


def test_the_report_counts_notes_without_their_text(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    lines = _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
    call(ctx, "notes.decide", {"link_id": lines[0]["linkId"], "choice": "hide"})
    row = NL.report_row(repository)
    assert row["proposals"] == 2 and row["hidden"] == 1 and row["hidden_share"] == 0.5 and row["takes"] == 0
    assert SENTINEL not in json.dumps(row)
