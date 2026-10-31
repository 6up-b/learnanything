"""Reader CA5: also in your books (ux_reader_compare_ask_v1 §6.2, §6.3, §6.5, §13).

The Guide's one-line entry and its list read C0a/C0b's judged coverage
through ``reader.correspondents`` (no model call, no write). CA5 adds:

* a per-vault library cache, so crossing sections does not rebuild C0a's
  ``Library`` on the serial sidecar (CA5a open item 7), with protection read
  again on every read;
* *not about this* on a judged line as CA5a's one operation, naming the
  shared LOs the line is listed under;
* the line's hide preferences (*hide for this book* / *hide everywhere*) in
  the vault's ``[reader.correspondence]`` config, and Settings bringing it back;
* CA5a's deferred salience-only events.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

import pytest

from learnloop.config.schema import LearnLoopConfig
from learnloop.source_retrieval import section_coverage as SC
from learnloop_sidecar.errors import SidecarError
from tests.practice_index_fakes import _learning_object
from tests.reading_path_fixtures import call, context
from tests.section_coverage_fixtures import (
    BOOK_EIGEN,
    BOOK_EIGEN_SPAN,
    CoverageJudgeFake,
    build_coverage_vault,
    cite,
    hold_out,
    table_counts,
)

FIND = {"extraction_id": "ext_book", "section_id": BOOK_EIGEN}
QUIET = {**FIND, "search_fallback": False}


def _ctx(paths, **attrs):
    return context(paths.root, coverage_inline=True, **attrs)


def _second_lo(paths) -> None:
    """``lo_charpoly``, cited by the same section as ``lo_eigen`` (a section under two shared LOs)."""

    from learnloop.vault.yaml_io import write_yaml

    lo = _learning_object("lo_charpoly", "Eigenvalue polynomial")
    lo["summary"] = "The eigenvalues of A are the roots of det(A - tI), its characteristic polynomial."
    write_yaml(paths.learning_object_path("linear-algebra", "lo_charpoly"), lo)
    cite(paths, "lo_charpoly", "src_book", "ext_book", BOOK_EIGEN_SPAN)


def _judged(tmp_path, *, two=False, notation="uses row vectors", config=""):
    paths, repository = build_coverage_vault(tmp_path / "vault", config=config)
    if two:
        _second_lo(paths)
    judge = CoverageJudgeFake(treatments={"5.1 Eigenvectors and eigenvalues": "introduces",
                                          "5.2 The characteristic equation": "develops"}, notation=notation)
    ctx = _ctx(paths, coverage_judge_client=judge)
    call(ctx, "curriculum.cover", FIND)
    return paths, repository, ctx, judge


def _lines(view):
    return [(group["learningObjectId"], source["sourceId"], section["sectionId"])
            for group in view["learningObjects"] for source in group["sources"] for section in source["sections"]]


# -- the switch and the contract ---------------------------------------------------------------------


def test_the_hide_preferences_default_to_shown():
    config = LearnLoopConfig().reader.correspondence
    assert config.enabled is True and config.hide_everywhere is False and config.hidden_sources == []


def test_the_prompt_contract_names_the_line_and_its_preferences_only_while_on(tmp_path):
    paths, _repository = build_coverage_vault(tmp_path / "on")
    contract = call(_ctx(paths), "reader.prompt_contract", {})
    assert contract["correspondence"] == {"enabled": True, "findSection": True, "alsoInBooks": True,
                                          "hiddenEverywhere": False, "hiddenSources": []}
    for name, config in (("reader_off", "[reader.correspondence]\nenabled = false"),
                         ("curriculum_off", "[curriculum]\nenabled = false")):
        paths, _repository = build_coverage_vault(tmp_path / name, config=config)
        assert "correspondence" not in call(_ctx(paths), "reader.prompt_contract", {}), name


# -- the judged read the line and the list show ------------------------------------------------------


def test_the_judged_list_is_by_lo_with_treatments_notation_and_read_marks_and_no_model_call(tmp_path):
    paths, repository, ctx, judge = _judged(tmp_path)
    calls = judge.calls
    before = table_counts(repository)
    view = call(ctx, "reader.correspondents", QUIET)
    assert table_counts(repository) == before and judge.calls == calls
    assert view["status"] == "judged" and view["search"] is None
    groups = view["learningObjects"]
    assert [group["learningObjectId"] for group in groups] == ["lo_eigen"]
    assert groups[0]["title"] == "Eigenvalues"
    sections = [section for source in groups[0]["sources"] for section in source["sections"]]
    # introduces before develops (the API's order), each in the learner's words.
    assert [(section["title"], section["treatmentWords"]) for section in sections][:2] == [
        ("5.1 Eigenvectors and eigenvalues", "introduces it"), ("5.2 The characteristic equation", "develops it")]
    for section in sections:
        assert section["by"] == "judge" and section["sourceId"] != "src_book"
        assert section["notation"] == "uses row vectors" and section["notationLabel"] == SC.NOTATION_LABEL
        assert section["read"] is False and section["kept"] == [] and section["jump"]["spanId"]
        # No model-written pair relation on any line (the index has none).
        assert not {"relation", "pairRelation", "relations"} & set(section)
    # A read section carries the reading fact.
    lay = repository.reader_section_progress_for("ext_lay")
    assert lay == [] or all(not row.get("completed_at") for row in lay)
    with repository.atomic():
        repository.connection().execute(
            "INSERT INTO reader_section_progress (extraction_id, section_id, span_count, spans_seen, completed_at, "
            "updated_at) VALUES ('ext_lay', 'lay_eigen', 2, 2, '2026-10-31T00:00:00Z', '2026-10-31T00:00:00Z')")
    again = call(ctx, "reader.correspondents", QUIET)
    marks = {section["sectionId"]: section["read"] for group in again["learningObjects"]
             for source in group["sources"] for section in source["sections"]}
    assert marks["lay_eigen"] is True and marks["lay_char"] is False


def test_a_section_under_two_shared_los_names_the_other_for_also_on_focus(tmp_path):
    _paths, _repository, ctx, _judge = _judged(tmp_path, two=True)
    view = call(ctx, "reader.correspondents", QUIET)
    by_lo = {group["learningObjectId"]: group for group in view["learningObjects"]}
    assert set(by_lo) == {"lo_eigen", "lo_charpoly"}
    shared = set()
    for group in view["learningObjects"]:
        for source in group["sources"]:
            for section in source["sections"]:
                other = sorted({"lo_eigen", "lo_charpoly"} - {group["learningObjectId"]})
                assert section["alsoLearningObjectIds"] in (other, [])
                if section["alsoLearningObjectIds"]:
                    shared.add(section["sectionId"])
    # lay_char treats both: listed under each LO, each naming the other (the client shows it once).
    assert "lay_char" in shared


def test_exam_and_held_out_sections_are_never_listed_even_with_coverage_rows(tmp_path):
    """The presentation reads only through the protection C0a reads (G-C1)."""

    paths, repository, ctx, _judge = _judged(tmp_path)
    # A judge row naming a held-out section and one naming the exam's question, written straight in.
    view = call(ctx, "reader.correspondents", QUIET)
    template = next(section for group in view["learningObjects"] for source in group["sources"]
                    for section in source["sections"])
    with repository.connection() as connection:
        row = dict(connection.execute(
            "SELECT * FROM section_coverage WHERE extraction_id = 'ext_lay' AND section_id = ? AND origin != 'learner'",
            (template["sectionId"],)).fetchone())
    with repository.atomic():
        for extraction_id, section_id in (("ext_lay", "lay_held"), ("ext_exam", "exam_q")):
            forged = {**row, "id": f"scv_forged_{section_id}", "extraction_id": extraction_id, "section_id": section_id}
            columns = ", ".join(forged)
            repository.connection().execute(
                f"INSERT INTO section_coverage ({columns}) VALUES ({', '.join('?' for _ in forged)})",
                tuple(forged.values()))
    listed = {(source, section) for _lo, source, section in _lines(call(ctx, "reader.correspondents", QUIET))}
    assert ("src_lay", "lay_held") not in listed and all(source != "src_exam" for source, _s in listed)
    # A section held out after it was judged leaves the list on the next read.
    hold_out(repository, "lay_char")
    after = {section for _lo, _source, section in _lines(call(ctx, "reader.correspondents", QUIET))}
    assert "lay_char" not in after and "lay_eigen" in after


# -- the per-section cache ----------------------------------------------------------------------------


def test_crossing_sections_reuses_one_library_and_parses_each_reading_once(tmp_path, monkeypatch):
    paths, repository, ctx, _judge = _judged(tmp_path)
    loads: list[str] = []
    real = type(repository).load_document_ir

    def counted(self, extraction_id, *args, **kwargs):
        loads.append(extraction_id)
        return real(self, extraction_id, *args, **kwargs)

    monkeypatch.setattr(type(repository), "load_document_ir", counted)
    sections = list(SC.Library(ctx.vault, repository).reading("ext_book").sections)
    assert len(sections) >= 2
    loads.clear()
    first = call(ctx, "reader.correspondents", QUIET)
    cold = loads.count("ext_book")
    for section_id in sections:
        call(ctx, "reader.correspondents", {"extraction_id": "ext_book", "section_id": section_id,
                                            "search_fallback": False})
    call(ctx, "reader.correspondents", QUIET)
    assert loads.count("ext_book") == cold, "crossing sections parsed the open book again"
    caches = list(ctx.correspondent_libraries.values())
    assert len(caches) == 1 and caches[0].builds == 1
    # The answer read from the cache is the answer a fresh library gives.
    fresh = SC.correspondents(ctx.vault, repository, "ext_book", BOOK_EIGEN, search_fallback=False)
    assert _lines(call(ctx, "reader.correspondents", QUIET)) == _lines(SC_camel(fresh)) == _lines(first)


def SC_camel(view):
    from learnloop_sidecar.dto import versioned

    return versioned(view)


def test_the_cache_reads_protection_every_time_and_rebuilds_on_a_change(tmp_path):
    paths, repository, ctx, _judge = _judged(tmp_path)
    call(ctx, "reader.correspondents", QUIET)
    cache = next(iter(ctx.correspondent_libraries.values()))
    assert cache.builds == 1
    hold_out(repository, "lay_eigen")
    view = call(ctx, "reader.correspondents", QUIET)
    assert cache.builds == 2 and "lay_eigen" not in {section for *_x, section in _lines(view)}
    # The peek reads through the same cache: protection read now refuses.
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.correspondent_peek", {"extraction_id": "ext_lay", "section_id": "lay_eigen"})
    assert caught.value.code == "withheld"
    # A reload (a new vault object) rebuilds too.
    ctx.reload(maintenance=False)
    call(ctx, "reader.correspondents", QUIET)
    assert cache.builds == 3


def test_an_unreadable_protection_predicate_shows_nothing_through_the_cache(tmp_path, monkeypatch):
    paths, repository, ctx, _judge = _judged(tmp_path)
    call(ctx, "reader.correspondents", QUIET)

    def unreadable(*_args, **_kwargs):
        raise SC.CoverageError("withheld", "LearnLoop couldn't check this library's exam material.")

    monkeypatch.setattr(SC, "read_protection", unreadable)
    view = call(ctx, "reader.correspondents", QUIET)
    assert view["status"] == "withheld" and view["learningObjects"] == []


# -- not about this on a judged line -------------------------------------------------------------------


def _dismiss(ctx, line, operation_id, *, los=None, undo_of=None):
    params = {**FIND, "target_extraction_id": line[0], "target_section_id": line[1], "operation_id": operation_id}
    if los is not None:
        params["learning_object_ids"] = los
    if undo_of is not None:
        params["undo_of"] = undo_of
    return call(ctx, "reader.correspondent_dismiss", params)["operation"]


def test_not_about_this_on_a_judged_line_corrects_only_its_shared_los_with_undo(tmp_path):
    _paths, repository, ctx, judge = _judged(tmp_path, two=True)
    calls = judge.calls
    view = call(ctx, "reader.correspondents", QUIET)
    assert ("lo_eigen", "src_lay", "lay_char") in _lines(view)
    before = table_counts(repository)
    record = _dismiss(ctx, ("ext_lay", "lay_char"), "op_judged_001", los=["lo_eigen"])
    assert record["choice"] == "not_about" and record["learningObjectIds"] == ["lo_eigen"]
    after = table_counts(repository)
    changed = {name: after[name] - before[name] for name in after if after[name] != before.get(name)}
    # One learner row and verdict for the named LO, and the operation's pair verdict: nothing else.
    assert changed == {"section_coverage": 1, "judgment_ledger": 2}
    lines = _lines(call(ctx, "reader.correspondents", QUIET))
    assert ("lo_eigen", "src_lay", "lay_char") not in lines
    assert ("lo_charpoly", "src_lay", "lay_char") in lines, "an LO the line was not listed under is untouched"
    # The whole line (both shared LOs) in one operation, then undo brings it back.
    _dismiss(ctx, ("ext_lay", "lay_eigen"), "op_judged_002", los=["lo_eigen", "lo_charpoly"])
    assert not {line for line in _lines(call(ctx, "reader.correspondents", QUIET)) if line[2] == "lay_eigen"}
    undo = _dismiss(ctx, ("ext_lay", "lay_eigen"), "op_judged_003", undo_of="op_judged_002")
    assert undo["choice"] == "none" and sorted(undo["learningObjectIds"]) == ["lo_charpoly", "lo_eigen"]
    assert {line for line in _lines(call(ctx, "reader.correspondents", QUIET)) if line[2] == "lay_eigen"}
    assert judge.calls == calls


def test_not_about_this_names_only_los_of_the_open_section(tmp_path):
    _paths, repository, ctx, _judge = _judged(tmp_path)
    before = table_counts(repository)
    for los in (["lo_not_here"], []):
        with pytest.raises(SidecarError) as caught:
            _dismiss(ctx, ("ext_lay", "lay_char"), f"op_bad_{len(los)}_0001", los=los)
        assert caught.value.code == "validation_error"
    assert table_counts(repository) == before


# -- hide for this book / hide everywhere -----------------------------------------------------------


def _prefs(ctx, **params):
    out = dict(call(ctx, "reader.set_correspondence_preferences", params))
    out.pop("version", None)
    return out


def _shown(ctx):
    out = dict(call(ctx, "reader.correspondence_preferences", {}))
    out.pop("version", None)
    return out


def test_hiding_the_line_is_kept_in_the_vaults_config_and_settings_brings_it_back(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    ctx = _ctx(paths)
    before = table_counts(repository)
    shown = _shown(ctx)
    assert shown == {"enabled": True, "hideEverywhere": False, "hiddenSources": []}
    out = _prefs(ctx, source_id="src_book", hide_source=True)
    assert [entry["sourceId"] for entry in out["hiddenSources"]] == ["src_book"]
    # Settings names the book by its title, never by a count.
    assert out["hiddenSources"][0]["title"] and out["hiddenSources"][0]["title"] != "src_book"
    contract = call(ctx, "reader.prompt_contract", {})["correspondence"]
    assert contract["hiddenSources"] == ["src_book"] and contract["hiddenEverywhere"] is False
    out = _prefs(ctx, hide_everywhere=True)
    assert out["hideEverywhere"] is True
    toml = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    assert "hide_everywhere = true" in toml and "src_book" in toml
    # Hiding writes config only: no row anywhere, and the data is unchanged.
    assert table_counts(repository) == before
    assert call(ctx, "reader.correspondents", FIND)["status"] in ("unchecked", "none")
    # Settings brings both back.
    _prefs(ctx, hide_everywhere=False)
    out = _prefs(ctx, source_id="src_book", hide_source=False)
    assert out == {"enabled": True, "hideEverywhere": False, "hiddenSources": []}
    assert call(ctx, "reader.prompt_contract", {})["correspondence"]["hiddenSources"] == []


def test_no_change_writes_nothing_and_a_book_must_be_named(tmp_path):
    paths, _repository = build_coverage_vault(tmp_path / "vault")
    ctx = _ctx(paths)
    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    _prefs(ctx, hide_everywhere=False)
    _prefs(ctx, source_id="src_book", hide_source=False)
    assert config.read_text(encoding="utf-8") == text
    with pytest.raises(SidecarError) as caught:
        _prefs(ctx, hide_source=True)
    assert caught.value.code == "validation_error"


def test_switched_off_the_preferences_say_so_and_refuse_changes(tmp_path):
    paths, _repository = build_coverage_vault(tmp_path / "vault", config="[reader.correspondence]\nenabled = false")
    ctx = _ctx(paths)
    assert _shown(ctx) == {"enabled": False, "hideEverywhere": False, "hiddenSources": []}
    with pytest.raises(SidecarError) as caught:
        _prefs(ctx, hide_everywhere=True)
    assert caught.value.code == "correspondence_disabled"


def test_the_ca5_rpcs_are_registered_and_desktop_only():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.handlers.correspondents import ALSO_IN_BOOKS_RPCS
    from learnloop_sidecar.registry import METHOD_REGISTRY

    for method in ALSO_IN_BOOKS_RPCS:
        assert method in METHOD_REGISTRY and method not in ALLOWLIST


# -- CA5a's deferred events -----------------------------------------------------------------------


def test_peeked_and_opened_are_salience_only_client_events_with_ids_only(tmp_path):
    from learnloop.reader import reader_inquiry as RI

    assert {"corresponding_section_peeked", "corresponding_section_opened"} <= set(RI.CLIENT_ACTION_EVENTS)
    _paths, repository, _ctx_, _judge = _judged(tmp_path)
    payload = {"extraction_id": "ext_book", "section_id": BOOK_EIGEN, "target_source_id": "src_lay",
               "target_extraction_id": "ext_lay", "target_section_id": "lay_eigen", "target_span_id": "s1",
               "by": "judged", "via": "also_list", "title": "5.1 Eigenvectors and eigenvalues"}
    ids = RI.record_activity(repository, [
        {"kind": "reader_action_invoked", "event": "corresponding_section_peeked", "payload": payload},
        {"kind": "reader_action_invoked", "event": "corresponding_section_opened", "payload": payload},
    ])
    assert len(ids) == 2
    import json

    with repository.connection() as connection:
        rows = [json.loads(row[0]) for row in connection.execute(
            "SELECT payload_json FROM interaction_events WHERE kind = 'reader_action_invoked' "
            "ORDER BY rowid DESC LIMIT 2")]
    for row in rows:
        assert row["authority_class"] == "salience_only"
        assert row["target_section_id"] == "lay_eigen" and row["by"] == "judged" and row["via"] == "also_list"
        assert "title" not in row, "no title or learner text survives"


# -- Codex review (fix round) ------------------------------------------------------------------------


def test_an_operation_id_reused_for_another_lo_set_is_refused_and_writes_nothing(tmp_path):
    """Codex review F1: a retried id binds its whole payload, the LOs included."""

    _paths, repository, ctx, _judge = _judged(tmp_path, two=True)
    first = _dismiss(ctx, ("ext_lay", "lay_char"), "op_retry_0001", los=["lo_eigen"])
    before = table_counts(repository)
    # The same id, the same LOs (any order, repeated): the recorded operation, nothing written.
    again = _dismiss(ctx, ("ext_lay", "lay_char"), "op_retry_0001", los=["lo_eigen", "lo_eigen"])
    assert again["operationId"] == first["operationId"] and again["learningObjectIds"] == ["lo_eigen"]
    # The same id naming another LO set is another correction: refused, nothing written.
    for los in (["lo_charpoly"], ["lo_eigen", "lo_charpoly"]):
        with pytest.raises(SidecarError) as caught:
            _dismiss(ctx, ("ext_lay", "lay_char"), "op_retry_0001", los=los)
        assert caught.value.code == "validation_error", los
    assert table_counts(repository) == before
    assert ("lo_charpoly", "src_lay", "lay_char") in _lines(call(ctx, "reader.correspondents", QUIET))


def test_hide_preferences_from_a_stale_context_keep_another_writers_changes(tmp_path):
    """Codex review F2: each change applies to the config as it is on disk now."""

    paths, _repository = build_coverage_vault(tmp_path / "vault")
    first, second = _ctx(paths), _ctx(paths)
    assert _shown(first)["hiddenSources"] == [] and _shown(second)["hiddenSources"] == []
    _prefs(first, source_id="src_book", hide_source=True)
    # The second context still holds hidden_sources = [] in memory.
    out = _prefs(second, source_id="src_lay", hide_source=True)
    assert sorted(entry["sourceId"] for entry in out["hiddenSources"]) == ["src_book", "src_lay"]
    # Showing a book the stale context never saw hidden still shows it.
    out = _prefs(second, source_id="src_book", hide_source=False)
    assert [entry["sourceId"] for entry in out["hiddenSources"]] == ["src_lay"]
    # And the first context, stale in turn, keeps the second's change.
    _prefs(first, hide_everywhere=True)
    out = _prefs(first, source_id="src_exam", hide_source=True)
    assert sorted(entry["sourceId"] for entry in out["hiddenSources"]) == ["src_exam", "src_lay"]
    assert out["hideEverywhere"] is True
    assert _shown(second)["hideEverywhere"] is False  # not reloaded yet: in-memory only
    out = _prefs(second, hide_everywhere=False)
    assert out["hideEverywhere"] is False
    assert sorted(entry["sourceId"] for entry in out["hiddenSources"]) == ["src_exam", "src_lay"]
