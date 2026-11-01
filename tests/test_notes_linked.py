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


@pytest.mark.parametrize("mode", ["no_read", "serve_fail", "serve_garbage", "serve_slow"])
def test_f1_with_tends_read_down_no_file_is_read_and_linking_waits(tmp_path, monkeypatch, mode):
    """Codex review F1: tend's read op is the only privacy gate LearnLoop has (tend's
    ``private`` setting lives in tend's own config). With tend's read down (no read op,
    a crash, unreadable output, a stall) a note inside the allowlist that tend marks
    private is never read from its file: the read raises and the linking waits."""

    fake_tend = install_fake_tend(tmp_path / "tend", monkeypatch, mode=mode)
    corpus = eigen_corpus(fake_tend)
    settings = NT.TendSettings(**{**_settings(fake_tend).__dict__, "timeout": 1.0})
    hits = NT.search(settings, "Eigenvalues")  # tend's search still answers
    assert any(hit.heading == "Eigen private" for hit in hits)  # search does not filter private notes
    with pytest.raises(NT.TendUnavailable):
        NT.read_sections(settings, hits)
    assert NT.read_sections(settings, [hit for hit in hits if hit.path == corpus["outside"]["path"]]) == {}


def test_f1_the_background_linking_waits_for_tends_read_and_sends_nothing(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch, mode="serve_fail")
    out = call(ctx, "notes.path", {"goal_id": goal_id})
    assert out["linking"] == "waiting" and notes.calls == 0 and _lines(out) == []
    assert _count(repository, "learner_notes") == 0 and _count(repository, "learner_note_links") == 0


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


# -- Codex review (2026-11-01) -----------------------------------------------------------------------

def _target(paths, repository, goal_id):
    vault = load_vault(paths.root)
    return vault, NL.path_targets(vault, repository, goal_id)[0]


def _reconfigured(paths, change):
    """The vault as it loads after the learner changed learnloop.toml (``change``: text to
    append, or a function of the file's text)."""

    toml = paths.root / "learnloop.toml"
    original = toml.read_text(encoding="utf-8")
    toml.write_text(change(original) if callable(change) else original + change, encoding="utf-8")
    try:
        return load_vault(paths.root)
    finally:
        toml.write_text(original, encoding="utf-8")


@pytest.mark.parametrize("change", [
    "[notes]\nenabled = false\n",
    "lexical_only_flip",
    "allowlist_shrunk",
])
def test_f2_a_changed_notes_authorization_refuses_the_pending_request(tmp_path, monkeypatch, change):
    """Codex review F2: the run started authorized, then the learner switched the notes
    off, flipped words-only search or narrowed the allowlist before the request: the
    request is refused at its admission (nothing sent) and nothing is written."""

    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    vault, target = _target(paths, repository, goal_id)
    settings = NL.tend_settings(vault)
    if change == "lexical_only_flip":
        changed = _reconfigured(paths, lambda text: text.replace("lexical_only = false", "lexical_only = true"))
    elif change == "allowlist_shrunk":
        changed = _reconfigured(paths, lambda text: text.replace(f', "{fake_tend.quicknote}"', ""))
    else:
        changed = _reconfigured(paths, change)
    assert NL.tend_settings(changed) != settings
    before = table_counts(repository)
    result = NL.judge_target(vault, repository, target, settings=settings, client=notes, live_vault=lambda: changed)
    assert result.status == "switched_off" and notes.calls == 0
    assert table_counts(repository) == before


def test_f2_switching_notes_off_during_the_request_records_nothing(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, corpus, _notes = _deliverable(tmp_path, monkeypatch)
    vault, target = _target(paths, repository, goal_id)
    live = {"vault": vault}
    off = _reconfigured(paths, "[notes]\nenabled = false\n")
    notes = NoteLinkFake(on_call=lambda: live.update(vault=off))  # the learner switches off meanwhile
    with repository.connection() as connection:
        ledger_before = connection.execute("SELECT COUNT(*) FROM judgment_ledger").fetchone()[0]
    result = NL.judge_target(vault, repository, target, settings=NL.tend_settings(vault), client=notes,
                             live_vault=lambda: live["vault"])
    assert result.status == "switched_off" and notes.calls == 1
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger").fetchone()[0] == ledger_before
    assert _count(repository, "learner_notes") == 0 and _count(repository, "learner_note_links") == 0
    run = NL.link_goal(vault, repository, goal_id, client=notes, live_vault=lambda: live["vault"])
    assert run.status == "switched_off" and notes.calls == 1


def test_f3_the_judges_receipts_keep_no_note_text(tmp_path, monkeypatch):
    """Codex review F3: an unlinked candidate's text is never kept, receipts included;
    the receipt keeps the prompt hash, usage and the verdicts."""

    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    call(ctx, "notes.path", {"goal_id": goal_id})
    assert notes.calls == 1
    with repository.connection() as connection:
        connection.row_factory = None
        receipts = connection.execute(
            "SELECT * FROM model_call_receipts WHERE purpose LIKE 'note_link_judge%'").fetchall()
        names = [column[0] for column in connection.execute(
            "SELECT * FROM model_call_receipts LIMIT 0").description]
    assert receipts, "the judge's call has receipts"
    rows = [dict(zip(names, row)) for row in receipts]
    assert all(row["input_text"] is None and row["prompt_hash"] for row in rows)
    dumped = json.dumps(rows, default=str)
    assert "eigen-free bread" not in dumped and SENTINEL not in dumped  # neither the unlinked nor a linked note
    assert any(row["output_text"] and "discusses" in row["output_text"] for row in rows)  # the verdicts stay


def test_f4_background_linking_completes_and_the_next_read_shows_it(tmp_path, monkeypatch):
    """Codex review F4 (server half): with the linking really in the background, the read
    that starts it says ``running`` and the read after it finishes shows the notes."""

    from learnloop_sidecar.background_jobs import background_jobs

    paths, repository, _ctx_inline, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    ctx = _ctx(paths, note_link_client=notes)
    ctx.notes_inline = False
    first = call(ctx, "notes.path", {"goal_id": goal_id})
    assert first["linking"] in ("running", "done")
    for thread in background_jobs(ctx).running:
        thread.join(timeout=60)
    after = call(ctx, "notes.path", {"goal_id": goal_id})
    assert after["linking"] == "done" and {line["note"]["heading"] for line in _lines(after)} == {"Eigen stuff", "Eigen page"}
    assert notes.calls == 1


def test_f6_undo_shows_the_current_proposal_not_the_one_hidden(tmp_path, monkeypatch):
    """Codex review F6: hide, the note changes and is judged again, then undo: the topic
    shows the current proposal (its new text), still the model's link."""

    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    typed = next(line for line in _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
                 if line["note"]["heading"] == "Eigen stuff")
    hidden = call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"})
    entry = next(e for e in fake_tend.entries if e["hit"]["heading"] == "Eigen stuff")
    entry["hit"]["hash"] = "h-edited"
    fake_tend.save()
    note_file = Path(entry["hit"]["path"])
    note_file.write_text(note_file.read_text(encoding="utf-8").replace("* Other", "Edited after the hide.\n* Other"),
                         encoding="utf-8")
    call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})
    assert notes.calls == 2
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    kept = {line["note"]["heading"]: line for line in _lines(call(ctx, "notes.path", {"goal_id": goal_id, "link": False}))}
    assert "Edited after the hide." in kept["Eigen stuff"]["note"]["text"]
    assert kept["Eigen stuff"]["authorship"] == "ai" and kept["Eigen stuff"]["linkId"] != typed["linkId"]
    marks = call(ctx, "notes.marks", {"extraction_id": "ext_book"})["marks"]
    assert all(note["extractionId"] == "ext_book" for mark in marks for note in mark["notes"])


def test_f6_a_kept_proposal_follows_the_topic_to_its_new_passage(tmp_path, monkeypatch):
    """Codex review F6: the learner's keep on a proposal anchored in one reading never shows
    in another reading's marks with its old anchor; the topic's current proposal does."""

    from learnloop.db.stores import learner_notes as store
    from learnloop.db.stores.judgments import append_judgment

    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    typed = next(line for line in _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
                 if line["note"]["heading"] == "Eigen stuff")
    hidden = call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"})
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    # The topic is judged again at another reading (its primary passage moved): state S2.
    with repository.atomic():
        connection = repository.connection()
        old = next(row for row in store.links(connection) if row["id"] == typed["linkId"])
        ledger = append_judgment(connection, task=NL.LEDGER_TASK, left_kind="learning_object", left_id="lo_eigen",
                                 right_kind="learner_note", right_id=NL.opaque(old["note_key"]), judge="llm",
                                 judge_model="m", prompt_version=NL.PROMPT_VERSION, input_hash="S2",
                                 verdict="discusses", rationale="{}", created_at="2099-01-01T00:00:00+00:00")
        store.insert_link(connection, {**old, "id": "nl_s2", "extraction_id": "ext_other", "section_id": "sec_o",
                                       "span_id": "o1", "target_key": "passage:ext_other/sec_o/o1", "state_key": "S2",
                                       "ledger_id": ledger, "created_at": "2099-01-01T00:00:00+00:00"})
        append_judgment(connection, task=NL.SHOWN_TASK, left_kind=NL.SHOWN_LEFT,
                        left_id=store.topic_key(goal_id, "lo_eigen"), right_kind="learning_object", right_id="lo_eigen",
                        judge="exact_key", prompt_version=NL.SHOWN_VERSION, input_hash="S2", verdict="shown",
                        rationale=json.dumps({"goal_id": goal_id, "learning_object_id": "lo_eigen"}),
                        created_at="2099-01-01T00:00:00+00:00")
    vault = load_vault(paths.root)
    other = NL.effective(repository, store.links(repository.connection(), extraction_id="ext_other"))
    assert [(view["link_id"], view["extraction_id"]) for view in other] == [("nl_s2", "ext_other")]
    assert NL.marks(vault, repository, "ext_book") == []  # the old anchor shows nothing now


def _corpus_entry(fake_tend, heading):
    return next(e for e in fake_tend.entries if e["hit"]["heading"] == heading)


def test_f7_returning_to_a_judged_state_shows_that_states_links_without_a_call(tmp_path, monkeypatch):
    """Codex review F7: state A links two notes, state B one; back to A, A's links show
    again (no new call); with no candidates at all, nothing shows."""

    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    heads = lambda out: sorted(line["note"]["heading"] for line in _lines(out))  # noqa: E731
    assert heads(call(ctx, "notes.path", {"goal_id": goal_id})) == ["Eigen page", "Eigen stuff"]
    entry = _corpus_entry(fake_tend, "Eigen stuff")
    note_file = Path(entry["hit"]["path"])
    text_a, hash_a = note_file.read_text(encoding="utf-8"), entry["hit"]["hash"]
    note_file.write_text(text_a.replace("Av = lv", "something else"), encoding="utf-8")
    entry["hit"]["hash"] = "h-b"
    fake_tend.save()
    assert heads(call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})) == ["Eigen page"]  # state B
    note_file.write_text(text_a, encoding="utf-8")
    entry["hit"]["hash"] = hash_a
    fake_tend.save()
    assert heads(call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})) == ["Eigen page", "Eigen stuff"]
    assert notes.calls == 2  # A again was not paid again
    marks = call(ctx, "notes.marks", {"extraction_id": "ext_book"})["marks"]
    assert sorted(n["note"]["heading"] for m in marks for n in m["notes"]) == ["Eigen page", "Eigen stuff"]
    for item in fake_tend.entries:
        item["words"] = ["nothing-matches-this"]
    fake_tend.save()
    assert heads(call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})) == []
    assert call(ctx, "notes.marks", {"extraction_id": "ext_book"})["marks"] == []


def _link_pocket_by_hand(ctx, fake_tend):
    hit = next(h for h in call(ctx, "notes.search", {"query": "my eigenvalues page"})["hits"]
               if h["heading"] == "Eigen page")
    return call(ctx, "notes.link", {"note": {"path": hit["path"], "line": hit["line"], "heading_path": hit["headingPath"],
                                             "title": hit["title"], "content_hash": hit["contentHash"],
                                             "mtime": hit["mtime"]}, "extraction_id": "ext_book", "span_id": "s2"})


def _hand_texts(ctx):
    marks = call(ctx, "notes.marks", {"extraction_id": "ext_book"})["marks"]
    return [n["note"]["text"] for m in marks for n in m["notes"] if n["byLabel"] == NL.BY_YOU_LABEL]


def test_f8_refresh_finds_the_heading_again_before_reading_it(tmp_path, monkeypatch):
    """Codex review F8: a heading inserted above the linked one moves it; the refresh finds
    it again through tend (words only) and never snapshots the new heading's text; when
    tend no longer finds it, the link keeps its last snapshot."""

    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    _link_pocket_by_hand(ctx, fake_tend)
    entry = _corpus_entry(fake_tend, "Eigen page")
    Path(entry["hit"]["path"]).write_text("# New top\nUnrelated top text here.\n# Eigen page\nWorked it again, redone.\n",
                                          encoding="utf-8")
    # tend has not re-indexed yet: the stored line (1) now opens "New top". Nothing is refreshed.
    vault = load_vault(paths.root)
    assert NL.refresh_learner_links(vault, repository, settings=NL.tend_settings(vault)) == 0
    assert all("Unrelated top text" not in text for text in _hand_texts(ctx))
    # tend re-indexed: the heading is at line 3 and found again by a words-only search.
    entry["hit"].update(line=3, hash="h-moved")
    entry["words"] = ["eigenvalues", "eigen page"]
    fake_tend.save()
    assert NL.refresh_learner_links(vault, repository, settings=NL.tend_settings(vault)) == 1
    assert "--words" in fake_tend.calls()[-2]  # the resolving search never leaves the machine
    texts = _hand_texts(ctx)
    assert texts and all("redone" in text and "Unrelated top text" not in text for text in texts)
    assert _count(repository, "learner_note_links") == 1  # refreshing writes no link row
    # Not found any more: the last snapshot stays.
    entry["words"] = ["nothing-matches-this"]
    fake_tend.save()
    Path(entry["hit"]["path"]).write_text("# Eigen page\nChanged once more.\n", encoding="utf-8")
    assert NL.refresh_learner_links(vault, repository, settings=NL.tend_settings(vault)) == 0
    assert all("redone" in text for text in _hand_texts(ctx))


def test_f8_a_stale_line_that_opens_another_heading_is_never_read_as_the_note(tmp_path, monkeypatch):
    fake_tend = install_fake_tend(tmp_path / "tend", monkeypatch)
    corpus = eigen_corpus(fake_tend)
    path = Path(corpus["pocket"]["path"])
    path.write_text("# New top\nUnrelated top text here.\n# Eigen page\nWorked it.\n", encoding="utf-8")
    stale = NT.NoteHit(path=str(path.resolve()), heading_path="Eigen page", title="2026-10-03", line=1, snippet="",
                       content_hash="", mtime=0.0, via="", origin="pocket_notes")
    assert NT.read_sections(_settings(fake_tend), [stale]) == {}
    moved = NT.read_sections(_settings(fake_tend), [NT.NoteHit(**{**stale.__dict__, "line": 3})])
    assert [text.text for text in moved.values()] == ["# Eigen page\nWorked it."]
    assert NT.heading_text("** TODO Eigen stuff   :math:", org=True) == "Eigen stuff"
    assert NT.heading_text("## Eigen page ##", org=False) == "Eigen page"
    assert NT.heading_text("plain text", org=False) is None


def test_f9_a_link_hidden_during_the_refresh_stays_hidden(tmp_path, monkeypatch):
    """Codex review F9: the refresh read the learner's link, then (during its slow tend
    read) the learner hid it: the refresh writes nothing and the link stays hidden."""

    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    out = _link_pocket_by_hand(ctx, fake_tend)
    entry = _corpus_entry(fake_tend, "Eigen page")
    entry["words"] = ["eigenvalues", "eigen page"]
    entry["hit"]["hash"] = "h-changed"
    fake_tend.save()
    Path(entry["hit"]["path"]).write_text("# Eigen page\nWorked the 2x2 eigen example by hand, changed.\n",
                                          encoding="utf-8")
    real_read = NT.read_sections

    def read_while_hiding(settings, hits):
        call(ctx, "notes.decide", {"link_id": out["linkId"], "choice": "hide"})
        return real_read(settings, hits)

    monkeypatch.setattr(NL.NT, "read_sections", read_while_hiding)
    vault = load_vault(paths.root)
    links_before = _count(repository, "learner_note_links")
    assert NL.refresh_learner_links(vault, repository, settings=NL.tend_settings(vault)) == 0
    with repository.connection() as connection:
        rows = connection.execute("SELECT authorship, status FROM learner_note_links ORDER BY created_at, rowid").fetchall()
    assert len(rows) == links_before + 1 and tuple(rows[-1]) == ("learner", "rejected")  # the hide only: no new acceptance
    assert _count(repository, "learner_notes") == 1  # nothing snapshotted for a hidden link
    monkeypatch.setattr(NL.NT, "read_sections", real_read)
    assert _hand_texts(ctx) == []  # hidden, and it stays hidden


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
def test_f12_an_incomplete_answer_is_never_recorded_or_cached(tmp_path, monkeypatch, shape):
    """Codex review F12: an answer without exactly one verdict per candidate (or a
    ``discusses`` without how) is not read as ``unrelated``: nothing is recorded, nothing
    checkpointed, and the next run asks again."""

    notes = NoteLinkFake(shape=shape)
    paths, repository, ctx, goal_id, fake_tend, corpus, _notes = _deliverable(tmp_path, monkeypatch, notes=notes)
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
    assert notes.calls == calls + 1 and {line["note"]["heading"] for line in _lines(again)} == {"Eigen stuff", "Eigen page"}


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
