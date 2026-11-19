"""UX-2's macro table never carries text from material the learner may not see.

A source's macros are read from its whole stored original, so a definition in a protected part (a past
paper's solutions, a held-out unit, an exam unit) would reach a view of another part. While anything of the
source is exam material or held out, by the predicate the Reader and the phone withhold with
(``exam_material``), or that predicate cannot be read, no reply carries ``mathMacros``: the formulas show as
they did before the table existed.
"""

from __future__ import annotations

import json

import pytest

from learnloop.db.repositories import Repository
from tests.helpers import create_basic_vault
from tests.mobile_v4_reader_helpers import EXTRACTION, READER_APP, add_book, call, desktop, host

pytest.importorskip("starlette")
from starlette.testclient import TestClient

from tests.mobile_host_helpers import HOSTNAME, Phone, pair

#: An original whose hidden definitions include one that states an answer, as a solutions part might.
PAGE = (b"<!doctype html><html><body><div style='display:none'>\\(\\newcommand{\\vvec}{{\\mathbf v}}"
        b"\\newcommand{\\ans}{x = 3}\\)</div><p>A vector space.</p></body></html>")


def _book(tmp_path, *, held_out: bool):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    add_book(paths.root, repository, held_out=held_out, data=PAGE)
    return paths, repository


def _phone_view(tmp_path, paths, repository, params):
    with TestClient(host(paths.root, tmp_path / "pages"), base_url=f"https://{HOSTNAME}") as client:
        return Phone(client, pair(repository), capabilities=READER_APP).rpc("reader.render_view", params)


def test_ux2_a_source_with_a_held_out_part_sends_no_macros_with_any_view(tmp_path):
    paths, repository = _book(tmp_path, held_out=True)
    ctx = desktop(paths.root)
    # The whole reading, and a section of it that is not held out, on the desktop and on the phone.
    for params in ({"extractionId": EXTRACTION}, {"extractionId": EXTRACTION, "sectionId": "u1"}):
        view = call(ctx, "reader.render_view", params)
        assert "mathMacros" not in view, params
        assert "x = 3" not in json.dumps(view)
    phone = _phone_view(tmp_path, paths, repository, {"extractionId": EXTRACTION, "sectionId": "u1"})
    assert "mathMacros" not in phone
    assert "x = 3" not in json.dumps(phone)


def test_ux2_an_unreadable_protection_predicate_sends_no_macros(tmp_path, monkeypatch):
    paths, _repository = _book(tmp_path, held_out=False)
    from learnloop.reader import source_macros

    def unreadable(*_args, **_kwargs):
        raise RuntimeError("source sets unreadable")

    monkeypatch.setattr(source_macros, "exam_material", unreadable)
    view = call(desktop(paths.root), "reader.render_view", {"extractionId": EXTRACTION, "sectionId": "u1"})
    assert "mathMacros" not in view


def test_ux2_an_unprotected_source_sends_its_macros_on_the_desktop_and_the_phone(tmp_path):
    paths, repository = _book(tmp_path, held_out=False)
    expected = {"\\vvec": "{\\mathbf v}", "\\ans": "x = 3"}
    assert call(desktop(paths.root), "reader.render_view", {"extractionId": EXTRACTION})["mathMacros"] == expected
    phone = _phone_view(tmp_path, paths, repository, {"extractionId": EXTRACTION, "sectionId": "u1"})
    assert phone["mathMacros"] == expected


def test_ux2_the_second_pane_of_a_book_with_a_held_out_unit_gets_no_macros(tmp_path):
    from learnloop.ingest.originals import store_original_bytes
    from tests.reading_path_fixtures import call as rpc
    from tests.reading_path_fixtures import context
    from tests.section_coverage_fixtures import build_coverage_vault

    paths, repository = build_coverage_vault(tmp_path / "vault")  # ext_lay's lay_held unit is held out
    revision = repository.get_source_revision(repository.get_extraction_run("ext_lay")["revision_id"])
    store_original_bytes(paths.root, revision["asset_hash"], PAGE)
    section = rpc(context(paths.root, coverage_inline=True), "reader.side_by_side_section",
                  {"extraction_id": "ext_lay", "section_id": "lay_char"})["section"]
    assert section["blocks"]
    assert "mathMacros" not in section
