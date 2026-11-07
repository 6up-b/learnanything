"""Router speed stage 2, item 1: AD's section → LO map held across calls (``adaptive_difficulty.reading_cache``).

No successor: every value is the landing code's. The landing's ``VaultReadingMap.los_for_section`` and
``los_for_span`` (main ``e9ceaf8d44``) are copied here verbatim and run beside the held map, inside a real AD
operation in the guard's deny mode, on a textbook and a re-read of it, through every change the held map must see:

* protection: a held-out span (the reading withheld), a withheld re-read, an exam reservation, each released again;
* the source: an edited block (the IR rewritten in place), a new reading of the book, a manual alias onto it;
* the vault: an LO's references edited and reloaded, and the same edit made in place on the loaded vault.

Each state is compared twice (the second time from what was held), and the held path is shown to compute nothing.
The guard denies nothing and every IR load is inside ``MaterialView.document_ir``; RO2's opportunity resolve over the
same vault gives the landing code's rows. Fakes only; no model call.
"""

from __future__ import annotations

from contextlib import closing
import json
import sqlite3
from typing import Any

import pytest

from learnloop.adaptive_difficulty import operation as O
from learnloop.adaptive_difficulty import reading as ADR
from learnloop.adaptive_difficulty import reading_cache
from learnloop.adaptive_difficulty.material_view import MaterialView
from learnloop.algorithm_versions import LESSON_OFFERS_ALGORITHM_VERSION
from learnloop.content.sources import exam_material
from learnloop.db.repositories import Repository


# -- the landing code (main e9ceaf8d44), verbatim ---------------------------------------------------------------


class _LandingMap(ADR.VaultReadingMap):
    def los_for_section(self, extraction_id: str, section_id: str) -> list[str]:
        from learnloop.section_map import learning_objects_for_section_in_ir

        key = (extraction_id, section_id)
        if key not in self._sections:
            # The sweep's withheld rule first (a reading the withheld material touches maps to nothing).
            ir = None if self.withheld(extraction_id, None) else self._document_ir(extraction_id)
            try:
                self._sections[key] = [] if ir is None else list(learning_objects_for_section_in_ir(
                    self.vault, self._projected, ir, extraction_id=extraction_id, section_id=section_id))
            except Exception:  # noqa: BLE001 - an unreadable extraction maps to nothing
                self._sections[key] = []
        return self._sections[key]

    def los_for_span(self, extraction_id: str, span_id: str) -> list[str]:
        from learnloop.section_map import learning_objects_for_span_in_ir

        key = (extraction_id, span_id)
        if key not in self._spans:
            ir = None if self.withheld(extraction_id, span_id) else self._document_ir(extraction_id)
            try:
                self._spans[key] = [] if ir is None else list(learning_objects_for_span_in_ir(
                    self.vault, self._projected, ir, extraction_id=extraction_id, span_id=span_id))
            except Exception:  # noqa: BLE001
                self._spans[key] = []
        return self._spans[key]


# -- the vault: a textbook, a re-read of it, LOs citing both by locator and quote ---------------------------------

UNITS = 6
BLOCKS = 5
LOS = [f"lo_m{i}" for i in range(6)]


def _units(variant: str = "") -> dict[str, tuple[str, list[tuple[str, int]]]]:
    return {f"u{u}": (f"Chapter {u}", [(f"Chapter {u} paragraph {b}: statement {u * 31 + b} about matrices{variant}.",
                                        1 + u) for b in range(BLOCKS)]) for u in range(UNITS)}


def _ir(units: dict[str, Any]):
    from tests.source_service_fakes import _Block, _Health, _IR, _Unit

    blocks, document_units, ordinal = [], [], 1
    for unit_ordinal, (unit_id, (header, rows)) in enumerate(units.items()):
        spans = [f"t{ordinal}"]
        blocks.append(_Block.build(span_id=f"t{ordinal}", block_type="SectionHeader", text=header, ordinal=ordinal,
                                   page=rows[0][1], section_path=[header]))
        ordinal += 1
        for text, page in rows:
            blocks.append(_Block.build(span_id=f"t{ordinal}", block_type="Text", text=text, ordinal=ordinal, page=page,
                                       section_path=[header]))
            spans.append(f"t{ordinal}")
            ordinal += 1
        document_units.append(_Unit(unit_id=unit_id, label=header, ordinal=unit_ordinal, semantic_hash=f"h{unit_id}",
                                    page_start=rows[0][1], page_end=rows[-1][1], span_ids=spans))
    return _IR(extractor="marker", extractor_version="1", units=document_units, blocks=blocks, assets=[],
               health=_Health())


def _refs(lo_index: int) -> list[dict[str, Any]]:
    """Locators on the first reading (re-read safety: they resolve onto the second through its aliases), one on the
    second reading, and a quote."""

    u = lo_index % UNITS
    first = 2 + u * (BLOCKS + 1)
    return [
        {"ref_type": "canonical_source", "ref_id": "src_m", "source_id": "src_m", "extraction_id": "ext_m1",
         "locator": f"span:ext_m1/t{first}", "span_ids": [f"t{first}"]},
        {"ref_type": "canonical_source", "ref_id": "src_m", "source_id": "src_m", "extraction_id": "ext_m2",
         "locator": f"span:ext_m2/t{first + 1 + (lo_index % 2)}"},
        {"ref_type": "canonical_source", "ref_id": "src_m", "source_id": "src_m",
         "quote": f"Chapter {(u + 1) % UNITS} paragraph 3: statement {((u + 1) % UNITS) * 31 + 3} about matrices"},
    ]


def _vault(tmp_path):
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    from tests.helpers import create_daily_plan_vault
    from tests.source_service_fakes import seed_textbook
    from tests.test_source_inventory import _persist

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={lo: [(f"pi_{lo}", 2.0)] for lo in LOS},
                                    version=LESSON_OFFERS_ALGORITHM_VERSION)
    repository = Repository(paths.sqlite_path)
    seed_textbook(repository, source_id="src_m", revision_id="rev_m", extraction_id="ext_m1", title="Matrices",
                  units=_units())
    _persist(repository, _ir(_units()), revision_id="rev_m", extraction_id="ext_m2", config={"engine": "reread"})  # a re-read
    for index, lo in enumerate(LOS):
        path = paths.learning_object_path("linear-algebra", lo)
        body = read_yaml(path)
        body["provenance"] = {"origin": "human", "source_refs": _refs(index)}
        write_yaml(path, body)
    return paths, repository


def _sections(repository) -> list[tuple[str, str, list[str]]]:
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        return [(row[0], row[1], json.loads(row[2] or "[]")) for row in connection.execute(
            "SELECT extraction_id, unit_id, span_ids_json FROM source_document_units ORDER BY extraction_id, ordinal")]


class _Protected:
    """The held-out predicate's inputs, set by the test (the real predicate, view, epoch and withheld rule run)."""

    def __init__(self) -> None:
        self.extractions: set[str] = set()
        self.spans: set[tuple[str, str]] = set()
        self.reserved: list[str] = []


@pytest.fixture
def protected(monkeypatch):
    state = _Protected()
    monkeypatch.setattr(exam_material, "held_out_material", lambda _vault, _repository: exam_material.Material(
        frozenset(state.extractions), frozenset(state.spans)))
    monkeypatch.setattr(Repository, "reserved_exam_pool_item_ids", lambda _self: list(state.reserved))
    return state


@pytest.fixture
def observed(monkeypatch):
    seen: list[O.Operation] = []
    monkeypatch.setattr(O, "OBSERVERS", [seen.append])
    monkeypatch.setitem(O._MODE, "mode", "deny")
    reading_cache.clear()
    yield seen
    reading_cache.clear()


def _maps(vault, repository, sections, cls) -> dict[str, Any]:
    """Every section's and span's LOs through one map of ``cls`` inside a read-only AD operation."""

    from learnloop.adaptive_difficulty.operation import ad_operation

    with ad_operation(vault, repository, read_only=True) as op:
        mapping = cls(op.vault, repository, op.view)
        out: dict[str, Any] = {}
        for extraction, section, spans in sections:
            out[f"{extraction}/{section}"] = mapping.los_for_section(extraction, section)
            for span in [*spans, "t999"]:
                out[f"{extraction}#{span}"] = mapping.los_for_span(extraction, span)
        out["epoch"] = op.view.epoch
    return out


def _compare(vault, repository, sections, monkeypatch, observed) -> tuple[dict[str, Any], int]:
    """The landing map's values, the held map's (twice), and how many mappings the second held pass computed."""

    import learnloop.section_map as SM

    old = _maps(vault, repository, sections, _LandingMap)
    new = _maps(vault, repository, sections, ADR.VaultReadingMap)
    computed = []
    real = SM.learning_objects_for_section_in_ir

    def counted(*args, **kwargs):
        computed.append(kwargs.get("section_id"))
        return real(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(SM, "learning_objects_for_section_in_ir", counted)
        again = _maps(vault, repository, sections, ADR.VaultReadingMap)
    assert new == old, {key: (new[key], old[key]) for key in old if new.get(key) != old[key]}
    assert again == old
    assert [denial for op in observed for denial in op.guard.denials] == []
    return old, len(computed)


def _load(paths):
    from learnloop.vault.loader import load_vault

    return load_vault(paths.root)


def test_the_held_map_is_the_landing_codes_through_protection_source_and_vault_changes(
        tmp_path, monkeypatch, protected, observed):
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    from tests.test_source_inventory import _persist

    paths, repository = _vault(tmp_path)
    vault = _load(paths)
    sections = _sections(repository)
    states: dict[str, dict[str, Any]] = {}

    def state(name: str, current_vault=None) -> int:
        values, computed = _compare(current_vault or vault, repository, sections, monkeypatch, observed)
        states[name] = values
        return computed

    # Nothing withheld: the second held pass computes nothing.
    assert state("open") == 0
    mapped = {key: value for key, value in states["open"].items() if key != "epoch" and value}
    assert len(mapped) >= 12, mapped  # locators, the re-read's aliases and the quote all map
    assert any(value and key.startswith("ext_m2") for key, value in mapped.items())
    # A held-out span: its reading is withheld (maps to nothing), the re-read keeps what it maps itself.
    protected.spans = {("ext_m1", "t3")}
    state("held_out_span")
    assert states["held_out_span"]["epoch"] != states["open"]["epoch"]
    assert all(not value for key, value in states["held_out_span"].items() if key.startswith("ext_m1"))
    assert states["held_out_span"] != states["open"]
    # Released: the earlier values again, from what was held.
    protected.spans = set()
    assert state("released") == 0
    assert states["released"] == states["open"]
    # A withheld re-read (the whole reading), then an exam reservation.
    protected.extractions = {"ext_m2"}
    state("withheld_reading")
    assert all(not value for key, value in states["withheld_reading"].items() if key.startswith("ext_m2"))
    protected.extractions = set()
    protected.reserved = ["pi_lo_m0"]
    state("reserved")
    assert states["reserved"]["epoch"] != states["open"]["epoch"]
    protected.reserved = []
    # The source: a block's text edited in place (the IR rewritten: the quote no longer matches).
    units = _units()
    header, rows = units["u2"]
    units["u2"] = (header, [(text.replace("about matrices", "about vectors"), page) for text, page in rows])
    repository.persist_document_ir("ext_m1", _ir(units))
    state("edited_source")
    assert states["edited_source"] != states["open"]
    # A new reading of the book, then a manual alias onto it.
    _persist(repository, _ir(_units(" again")), revision_id="rev_m", extraction_id="ext_m3",
             config={"engine": "third"})
    sections = _sections(repository)
    state("new_reading")
    repository.insert_span_reanchor(from_extraction_id="ext_m1", from_span_id="t2", to_extraction_id="ext_m3",
                                    to_span_id="t9", match_kind="manual", confidence=1.0)
    state("manual_alias")
    assert states["manual_alias"] != states["new_reading"]
    # The vault: an LO's references edited and reloaded (another vault object) ...
    path = paths.learning_object_path("linear-algebra", "lo_m3")
    body = read_yaml(path)
    body["provenance"]["source_refs"] = [_refs(5)[0]]
    write_yaml(path, body)
    reloaded = _load(paths)
    state("vault_edit", reloaded)
    assert states["vault_edit"] != states["manual_alias"]
    # ... and the same kind of edit made in place on the loaded vault object (no reload).
    from learnloop.vault.models import SourceRef

    lo = reloaded.learning_objects["lo_m1"]
    lo.provenance.source_refs.append(SourceRef.model_validate(_refs(4)[0]))
    state("in_place", reloaded)
    assert states["in_place"] != states["vault_edit"]


def test_every_ir_load_of_the_held_map_is_inside_the_chokepoint(tmp_path, monkeypatch, protected, observed):
    paths, repository = _vault(tmp_path)
    inside = {"depth": 0}
    loads: list[bool] = []
    raw_load = Repository.load_document_ir
    chokepoint = MaterialView.document_ir

    def counted_load(self, extraction_id):
        loads.append(inside["depth"] > 0)
        return raw_load(self, extraction_id)

    def counted_chokepoint(self, repository, extraction_id):
        inside["depth"] += 1
        try:
            return chokepoint(self, repository, extraction_id)
        finally:
            inside["depth"] -= 1

    monkeypatch.setattr(Repository, "load_document_ir", counted_load)
    monkeypatch.setattr(MaterialView, "document_ir", counted_chokepoint)
    vault = _load(paths)
    sections = _sections(repository)
    first = _maps(vault, repository, sections, ADR.VaultReadingMap)
    assert loads and all(loads), loads
    loads.clear()
    assert _maps(vault, repository, sections, ADR.VaultReadingMap) == first
    assert loads == []  # held: no IR is loaded at all
    assert [denial for op in observed for denial in op.guard.denials] == []


def test_a_failed_mapping_is_not_held(tmp_path, monkeypatch, protected, observed):
    import learnloop.section_map as SM

    paths, repository = _vault(tmp_path)
    vault = _load(paths)
    sections = _sections(repository)
    good = _maps(vault, repository, sections, ADR.VaultReadingMap)
    reading_cache.clear()

    def broken(*_args, **_kwargs):
        raise RuntimeError("unreadable")

    with monkeypatch.context() as patch:
        patch.setattr(SM, "learning_objects_for_section_in_ir", broken)
        failed = _maps(vault, repository, sections, ADR.VaultReadingMap)
    assert all(not value for key, value in failed.items() if key != "epoch")
    assert _maps(vault, repository, sections, ADR.VaultReadingMap) == good


@pytest.mark.parametrize("change", ["structure", "metadata"])
def test_a_mapping_computed_across_a_source_write_is_not_held(tmp_path, monkeypatch, protected, observed, change):
    """A source write committed while a map computes, after it read its key: what the map computed from the new
    rows is not held under the earlier key. The write is then undone, so the earlier key is current again: a value
    wrongly held under it would be read now, and every value is still the landing code's. ``structure``: the IR
    rewritten before the map loads it; ``metadata``: a manual alias onto the reading recorded during its third
    mapping (after the map verified the IR)."""

    import learnloop.section_map as SM

    paths, repository = _vault(tmp_path)
    vault = _load(paths)
    sections = _sections(repository)
    original = _maps(vault, repository, sections, _LandingMap)
    before = repository.load_document_ir("ext_m1")
    u1 = set(next(unit.span_ids for unit in before.units if unit.unit_id == "u1"))
    edited = before.model_copy(update={"blocks": [
        block.model_copy(update={"text": block.text.replace("about matrices", "about kernels")})
        if block.span_id in u1 else block for block in before.blocks]})
    calls = {"n": 0}
    real_ir = ADR.VaultReadingMap._document_ir
    real_map = SM.learning_objects_for_section_in_ir

    def elsewhere(write) -> None:
        """A write by another connection outside the operation (a writer elsewhere: a plain thread has no context)."""

        import threading

        thread = threading.Thread(target=write)
        thread.start()
        thread.join()

    def ir_after_a_write(self, extraction_id):
        if change == "structure" and extraction_id == "ext_m1" and extraction_id not in self._irs:
            elsewhere(lambda: Repository(repository.sqlite_path).persist_document_ir("ext_m1", edited))
        return real_ir(self, extraction_id)

    def mapping_after_a_write(*args, **kwargs):
        calls["n"] += 1
        if change == "metadata" and calls["n"] == 3:
            elsewhere(lambda: Repository(repository.sqlite_path).insert_span_reanchor(
                from_extraction_id="ext_m2", from_span_id="t3", to_extraction_id="ext_m1", to_span_id="t20",
                match_kind="manual", confidence=1.0))
        return real_map(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(ADR.VaultReadingMap, "_document_ir", ir_after_a_write)
        patch.setattr(SM, "learning_objects_for_section_in_ir", mapping_after_a_write)
        during = _maps(vault, repository, sections, ADR.VaultReadingMap)
    changed = _maps(vault, repository, sections, _LandingMap)
    assert changed != original  # the write changed what the landing code maps
    assert during != original
    # Undone: the earlier rows (and so the earlier key) again.
    if change == "structure":
        repository.persist_document_ir("ext_m1", before)
    else:
        with closing(sqlite3.connect(repository.sqlite_path)) as connection:
            connection.execute("DELETE FROM source_span_reanchors WHERE match_kind = 'manual'")
            connection.commit()
    assert _maps(vault, repository, sections, _LandingMap) == original
    assert _maps(vault, repository, sections, ADR.VaultReadingMap) == original
    assert [denial for op in observed for denial in op.guard.denials] == []


def test_the_opportunity_resolve_is_the_landing_codes_with_the_held_map(tmp_path, monkeypatch, protected, observed):
    """RO2's opportunity resolve (every reading event and its LOs) over completed sections, span views and an
    anchored question: the landing map's rows, then the held map's twice."""

    from learnloop.adaptive_difficulty import history_resolve as HR
    from learnloop.adaptive_difficulty.operation import ad_operation

    paths, repository = _vault(tmp_path)
    sections = _sections(repository)
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        for index, (extraction, section, spans) in enumerate(sections):
            at = f"2026-10-0{1 + index % 9}T09:{index:02d}:00Z"
            if index % 2 == 0:
                connection.execute(
                    "INSERT INTO reader_section_progress(extraction_id, section_id, spans_seen, span_count, revealed_at, "
                    "completed_at, updated_at) VALUES (?, ?, 1, 1, ?, ?, ?)", (extraction, section, at, at, at))
            connection.execute("INSERT INTO source_exposure_events(id, context, extraction_id, span_id, "
                               "section_path_json, created_at) VALUES (?, 'reader', ?, ?, '[]', ?)",
                               (f"sx_{index}", extraction, spans[-1], at))
        connection.execute(
            "INSERT INTO question_events(id, context, note_id, question_md, answer_status, answered_at, resolution, "
            "created_at) VALUES ('qe_span', 'reader', 'span:ext_m1/t3', 'Why?', 'answered', ?, 'open', ?)",
            ("2026-10-05T09:05:00Z", "2026-10-05T09:00:00Z"))
        connection.commit()
    vault = _load(paths)

    def rows(cls) -> list[dict[str, Any]]:
        from learnloop.db.connection import connect

        with monkeypatch.context() as patch:
            patch.setattr(ADR, "VaultReadingMap", cls)
            with ad_operation(vault, repository, read_only=True) as op:
                with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                    return HR._opportunities(connection, op.vault, op.repository, op.view, now="2026-11-01T00:00:00Z")

    old = rows(_LandingMap)
    assert len(old) >= 10, old
    assert rows(ADR.VaultReadingMap) == old
    assert rows(ADR.VaultReadingMap) == old
    protected.spans = {("ext_m2", "t2")}
    assert rows(ADR.VaultReadingMap) == rows(_LandingMap) != old
    assert [denial for op in observed for denial in op.guard.denials] == []
