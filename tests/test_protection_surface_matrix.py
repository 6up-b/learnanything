"""What every protection surface answers today, for every protected fixture: one matrix.

LearnLoop asks several protection questions (is a span exam material or held out; may it ground a model; may it
become practice; may an item be served, measured or shown to a model; what may leave the desktop), and each
surface reads one set to answer it. Several differences between surfaces are deliberate, so the matrix pins each
surface's answer per fixture: a later change to any surface's set shows up as a changed cell, and a deliberate
difference stays a pinned cell rather than an unexplained disagreement.

``EXPECTED`` is written out by hand. It is never computed by calling a predicate under test: that would pin the
implementation against itself. Each adapter calls the production function and reduces its answer to

* ``S``: the target is admitted or shown;
* ``W``: the target is left out, masked, or classed as withheld;
* ``R``: the operation refuses or raises before admitting it;
* ``-``: the question does not apply to the row (no cell is asked).

A defect the matrix shows keeps its current answer pinned here; its desired answer is a separate strict xfail
naming its ledger row (``docs/reviews/refactor-bug-ledger.md``), so a fix flips exactly one test.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import replace
from typing import Any

import pytest

from learnloop.content.sources import exam_material as EM
from tests.protection_matrix_helpers import (
    CLOCK,
    LO,
    NOW,
    Target,
    World,
    build_world,
    sentence,
    store_png,
    world_in_state,
)

# The world holds every fixture and the matrix asks about 1,500 cells through the production functions (the
# library's searches and the pinned tutor alone take about 20 s): over the fast lane's 15 s, so not in it.
pytestmark = pytest.mark.slow

S, W, R, NA = "S", "W", "R", "-"

# The rows are the fixtures (``tests/protection_matrix_helpers.py``); the columns are the surfaces, by the codes of
# the record (docs/reviews/refactor-g6.1.md), grouped as there: model, authoring and retrieval spans | practice |
# serving, measurement and devices | a model's view of an item | the phone | library, replays, local reading and
# payloads | raw reading and authoring neighbours.
EXPECTED_TABLE = """
fixture           | TE MR RA PS CK GU FI IP SC SQ MC | CI BS RI LF RF | RT OT PK SS DV PF EX EH CO SE | LP AP AD LC | PW PG PI RV GP PA PH AS DO | ML LA OR LJ PT TJ TB LS DH FB FD KY BG CM | RD RN CN
0.control         | S  S  S  S  S  S  S  -  S  S  S | S  S  S  S  S | -  -  -  -  -  -  -  -  -  - | -  -  -  - | S  S  S  S  S  S  S  -  S | S  S  S  S  S  S  S  S  S  -  -  -  S  S | S  -  -
1.paper           | W  W  S  S  S  S  W  -  W  W  W | R  W  S  S  W | -  -  -  -  -  -  -  -  -  - | -  -  -  - | W  R  R  R  R  R  W  -  S | S  W  R  R  W  S  R  S  S  -  -  -  R  W | S  -  -
2.exam            | W  W  S  S  S  S  W  -  W  W  W | R  W  S  S  S | -  -  -  -  -  -  -  -  -  - | -  -  -  - | W  R  R  W  W  R  W  -  S | S  W  R  R  W  S  R  S  S  -  -  -  W  W | S  S  S
2.neighbor        | S  S  S  S  S  S  S  -  S  S  S | S  S  S  S  S | -  -  -  -  -  -  -  -  -  - | -  -  -  - | S  S  R  S  S  S  S  -  S | S  S  S  S  S  S  S  S  S  -  -  -  S  S | S  -  -
2.split-exam      | W  W  S  S  S  S  W  -  W  W  W | R  W  S  S  S | -  -  -  -  -  -  -  -  -  - | -  -  -  - | W  R  R  W  W  R  W  -  S | S  W  R  R  W  S  R  S  S  -  -  -  W  W | S  S  S
2.split-theory    | S  S  S  S  S  S  S  -  S  S  S | S  S  S  S  S | -  -  -  -  -  -  -  -  -  - | -  -  -  - | S  S  R  S  W  S  S  -  S | S  S  S  S  S  S  R  S  S  -  -  -  W  S | S  -  -
3.held            | W  W  R  R  R  W  W  -  W  W  W | R  W  R  W  W | -  -  -  -  -  -  -  -  -  - | -  -  -  - | W  R  R  W  W  R  W  -  W | S  W  R  R  R  S  R  S  S  -  -  -  W  W | S  S  S
3.unresolved      | W  W  R  R  R  W  W  -  W  W  W | R  W  R  W  W | -  -  -  -  -  -  -  -  -  - | -  -  -  - | W  R  R  R  R  R  W  -  W | S  W  R  R  R  S  R  S  S  -  -  -  R  W | S  -  -
3.neighbor        | S  S  S  S  S  S  S  -  S  S  S | S  S  S  S  S | -  -  -  -  -  -  -  -  -  - | -  -  -  - | S  S  R  S  S  S  S  -  W | S  S  S  S  S  S  S  S  S  -  -  -  S  S | S  -  -
3.camel           | W  W  R  R  R  W  W  -  W  W  W | R  W  S  W  W | -  -  -  -  -  -  -  -  -  - | -  -  -  - | W  R  R  W  W  R  W  -  W | S  W  R  R  R  S  R  S  S  -  -  -  W  W | S  S  S
4.unmarked        | W  W  R  R  R  W  W  -  W  W  W | R  W  R  S  S | -  -  -  -  -  -  -  -  -  - | -  -  -  - | W  R  R  R  R  R  W  -  W | S  W  R  R  R  S  R  W  S  -  -  -  R  W | S  -  -
4.legacy          | W  W  R  R  R  W  W  -  W  W  W | R  W  R  W  W | -  -  -  -  -  -  -  -  -  - | -  -  -  - | W  R  R  R  R  R  W  -  W | S  W  R  R  R  S  R  S  S  -  -  -  R  W | S  -  -
5.signal          | W  W  R  R  R  W  W  -  W  W  W | R  W  R  W  W | -  -  -  -  -  -  -  -  -  - | -  -  -  - | W  R  R  W  W  R  W  -  W | S  W  R  R  R  S  R  S  S  -  -  -  W  W | S  S  S
5.unknown         | W  W  R  R  R  W  W  -  W  W  W | R  W  R  W  W | -  -  -  -  -  -  -  -  -  - | -  -  -  - | W  R  R  R  R  R  W  -  W | S  W  R  R  R  S  R  S  S  -  -  -  R  W | S  -  -
6.1canonical      | W  W  S  S  S  S  W  S  W  W  W | R  W  S  S  W | S  S  S  S  S  S  S  S  S  S | W  W  S  W | W  R  R  R  R  R  W  W  - | S  W  R  R  W  S  R  S  S  -  S  S  R  W | S  -  -
6.1block          | W  W  S  S  S  S  W  S  W  W  W | R  W  S  S  W | S  S  S  S  S  S  S  S  S  S | W  W  S  W | W  R  R  R  R  R  W  -  - | S  W  R  R  W  S  R  S  S  -  S  S  R  W | S  -  -
6.2canonical      | W  W  S  S  S  S  W  S  W  W  W | R  W  S  S  W | S  S  S  S  S  S  S  S  S  S | W  W  S  W | W  R  R  W  W  R  W  W  - | S  W  R  R  W  S  R  S  S  -  S  S  W  W | S  S  S
6.2block          | W  W  S  S  S  S  W  S  W  W  W | R  W  S  S  W | S  S  S  S  S  S  S  S  S  S | W  W  S  W | W  R  R  W  W  R  W  -  - | S  W  R  R  W  S  R  S  S  -  S  S  W  W | S  S  S
6.3canonical      | W  W  R  R  R  W  W  S  W  W  W | R  W  R  W  W | W  W  R  R  S  S  S  W  S  S | W  W  W  W | W  R  R  W  W  R  W  W  - | S  W  R  R  R  S  R  S  S  -  S  S  W  W | S  S  S
6.3block          | W  W  R  R  R  W  W  S  W  W  W | R  W  R  W  W | W  W  R  R  S  S  S  W  S  S | W  W  W  W | W  R  R  W  W  R  W  -  - | S  W  R  R  R  S  R  S  S  -  S  S  W  W | S  S  S
6.4canonical      | W  W  R  R  R  W  W  S  W  W  W | R  W  R  S  W | W  W  R  R  S  S  S  W  S  S | W  W  W  W | W  R  R  R  R  R  W  W  - | S  W  R  R  R  S  R  W  S  -  S  S  R  W | S  -  -
6.4block          | W  W  R  R  R  W  W  S  W  W  W | R  W  R  S  W | W  W  R  R  S  S  S  W  S  S | W  W  W  W | W  R  R  R  R  R  W  -  - | S  W  R  R  R  S  R  W  S  -  S  S  R  W | S  -  -
6.5canonical      | W  W  R  R  R  W  W  S  W  W  W | R  W  R  W  W | W  W  R  R  S  S  S  W  S  S | W  W  W  W | W  R  R  W  W  R  W  W  - | S  W  R  R  R  S  R  S  S  -  S  S  W  W | S  S  S
6.5block          | W  W  R  R  R  W  W  S  W  W  W | R  W  R  W  W | W  W  R  R  S  S  S  W  S  S | W  W  W  W | W  R  R  W  W  R  W  -  - | S  W  R  R  R  S  R  S  S  -  S  S  W  W | S  S  S
6.whole-ref       | -  -  -  -  -  -  -  S  -  W  - | -  -  -  -  S | S  S  S  S  S  S  S  S  S  S | S  S  S  S | -  -  -  -  -  -  -  -  - | -  -  -  -  -  -  -  -  -  -  S  S  -  - | -  -  -
6.exam-reserved   | S  S  S  S  S  S  S  S  S  S  W | S  S  S  S  W | W  W  R  R  S  S  S  S  W  S | W  W  W  W | S  S  S  S  S  S  S  S  - | S  S  S  S  S  S  S  S  S  -  S  S  S  S | S  -  -
6.cold-task       | S  S  S  S  S  S  S  W  S  S  W | S  S  S  S  S | S  W  S  S  S  S  S  S  W  S | W  W  S  W | S  S  S  S  S  S  S  S  - | S  S  S  S  S  S  S  S  S  -  S  S  S  S | S  -  -
6.remediation     | S  S  S  S  S  S  S  W  S  S  W | S  S  S  S  S | S  W  S  S  S  S  S  S  W  S | W  W  S  W | S  S  S  S  S  S  S  S  - | S  S  S  S  S  S  S  S  S  -  S  S  S  S | S  -  -
6.assess-reserved | S  S  S  S  S  S  S  W  S  S  W | S  S  S  S  W | S  S  S  S  S  S  S  S  S  S | W  W  S  W | S  S  S  S  S  S  S  S  - | S  S  S  S  S  S  S  S  S  -  S  S  S  S | S  -  -
6.probe           | S  S  S  S  S  S  S  W  S  S  W | S  S  S  S  S | S  S  S  S  S  S  S  S  S  S | W  W  S  W | S  S  S  S  S  S  S  S  - | S  S  S  S  S  S  S  S  S  -  S  S  S  S | S  -  -
6.held-grade      | S  S  S  S  S  S  S  S  S  S  S | S  S  S  S  S | S  S  S  S  S  S  S  S  S  S | S  S  S  S | S  S  S  S  S  S  S  S  - | S  S  S  S  S  S  S  S  S  -  S  S  S  S | S  -  -
7.reader-import   | W  W  S  S  S  S  W  S  W  W  W | R  W  S  S  W | S  S  S  S  S  S  S  S  S  S | W  W  S  W | W  R  R  R  R  R  W  W  - | S  W  R  R  W  S  R  S  S  -  S  S  R  W | S  -  -
8.invalid         | R  R  R  R  R  R  R  W  R  R  R | R  R  R  R  R | R  R  R  R  S  S  S  R  S  S | W  W  W  W | W  R  R  R  R  R  W  W  W | S  R  R  R  R  S  R  S  S  -  S  R  R  R | R  -  -
8.empty           | R  R  R  R  R  R  R  W  R  R  R | R  R  R  R  R | R  R  R  R  S  S  S  R  S  S | W  W  W  W | W  R  R  R  R  R  W  W  W | S  R  R  R  R  S  R  S  S  -  S  R  R  R | R  -  -
9.switch-off      | W  W  R  R  R  W  W  S  W  W  W | R  W  R  W  W | S  S  S  S  S  S  S  S  S  S | W  W  W  W | W  R  R  W  W  R  W  W  - | S  W  R  R  R  S  R  S  S  -  S  S  W  W | S  S  S
+.shown           | S  S  S  S  S  S  S  S  S  S  S | S  S  S  S  S | S  W  S  S  S  S  W  W  S  R | S  S  S  S | S  S  S  S  S  S  S  S  - | S  S  S  S  S  S  S  S  S  -  S  S  S  S | S  -  -
+.held-feedback   | -  -  -  -  -  -  -  -  -  -  - | -  -  -  -  - | -  -  -  -  -  -  -  -  -  - | -  -  -  - | -  -  -  -  -  -  -  -  - | -  -  -  -  -  -  -  -  -  W  -  S  -  - | -  -  -
"""


def _parse(table: str) -> tuple[list[str], dict[tuple[str, str], str]]:
    lines = [line for line in table.strip().splitlines() if line.strip()]
    columns = [cell for cell in lines[0].split("|", 1)[1].split() if cell != "|"]
    cells: dict[tuple[str, str], str] = {}
    for line in lines[1:]:
        row, rest = line.split("|", 1)
        values = [cell for cell in rest.split() if cell != "|"]
        assert len(values) == len(columns), row
        for column, value in zip(columns, values, strict=True):
            cells[(row.strip(), column)] = value
    return columns, cells


COLUMNS, EXPECTED = _parse(EXPECTED_TABLE)


# --- the world, read once per module ---------------------------------------------------------------------------


class Probe:
    """The module's world and its other states, each built once, and what a surface read of one state."""

    def __init__(self, world: World, factory: Any) -> None:
        self.base = world
        self._factory = factory
        self._states: dict[str, World] = {"base": world}
        self._memo: dict[tuple[str, str], Any] = {}
        self.contexts: dict[str, Any] = {}

    def world(self, target: Target, *, own: str | None = None) -> World:
        """The world in the target's state. ``own`` names a surface that writes what other surfaces read (an
        exposure, an Ask exchange, a queued request): it gets a copy of its own, so no cell depends on the order
        the surfaces ran in."""

        key = target.state if own is None else f"{target.state}-{own}"
        if key not in self._states:
            root = self._factory.mktemp(f"g6{key}") / "vault"
            self._states[key] = world_in_state(self.base, target.state, root)
        return self._states[key]

    def once(self, world: World, name: str, read: Callable[[], Any]) -> Any:
        """A vault-wide production read, made once per world state (an exception is kept and raised again)."""

        key = (world.state, name)
        if key not in self._memo:
            try:
                self._memo[key] = ("ok", read())
            except Exception as exc:  # noqa: BLE001 - the cell decides what a raise means
                self._memo[key] = ("raised", exc)
        kind, value = self._memo[key]
        if kind == "raised":
            raise value
        return value


@pytest.fixture(scope="module")
def probe_world(tmp_path_factory) -> Probe:
    return Probe(build_world(tmp_path_factory.mktemp("g6matrix") / "vault"), tmp_path_factory)


@pytest.fixture
def probe(probe_world: Probe):
    """The module's world; a sidecar a test opened is closed when it ends, so none of its threads outlives it."""

    yield probe_world
    while probe_world.contexts:
        _state, ctx = probe_world.contexts.popitem()
        ctx.close()


# --- adapters: one per surface, each calling the production function -------------------------------------------

Adapter = Callable[[Probe, Target], str]
ADAPTERS: dict[str, Adapter] = {}


def surface(code: str) -> Callable[[Adapter], Adapter]:
    def register(adapter: Adapter) -> Adapter:
        ADAPTERS[code] = adapter
        return adapter

    return register


def _span(target: Target) -> tuple[str, str]:
    if target.key is None:
        pytest.fail(f"{target.row} has no span")
    return target.key


def _item(world: World, target: Target):
    vault = world.vault()
    return vault, vault.practice_items[target.item_id]


@surface("TE")
def _teaching_exclusions(probe: Probe, target: Target) -> str:
    from learnloop.source_retrieval.corpus import teaching_exclusions

    world = probe.world(target)
    extraction, span = _span(target)
    try:
        excluded = probe.once(world, "TE", lambda: teaching_exclusions(world.vault(), world.repository))
    except Exception:  # noqa: BLE001
        return R
    return W if (extraction, span) in excluded.spans or extraction in excluded.extractions else S


@surface("MR")
def _model_reader_withheld(probe: Probe, target: Target) -> str:
    from learnloop.source_retrieval.corpus import model_reader_withheld

    world = probe.world(target)
    try:
        withheld = model_reader_withheld(world.vault(), world.repository, [_span(target)])
    except Exception:  # noqa: BLE001
        return R
    return W if _span(target) in withheld else S


def _section_rows(world: World, extraction_id: str) -> list[dict[str, Any]]:
    from learnloop.reader.reader_guidance import extraction_sections

    rows, _blocks, _sections = extraction_sections(world.repository.load_document_ir(extraction_id))
    return rows


def _section_of(world: World, target: Target) -> str:
    extraction, span = _span(target)
    return next(str(row["id"]) for row in _section_rows(world, extraction) if span in row["span_ids"])


@surface("GU")
def _guidance_sections(probe: Probe, target: Target) -> str:
    from learnloop.reader.reader_guidance import held_out_sections

    world = probe.world(target)
    extraction, _span_id = _span(target)
    try:
        held = held_out_sections(world.vault(), world.repository, extraction, _section_rows(world, extraction))
    except Exception:  # noqa: BLE001
        return R
    return W if _section_of(world, target) in held else S


@surface("FI")
def _figure_withheld(probe: Probe, target: Target) -> str:
    from learnloop.figures.protection import withheld_message

    world = probe.world(target)
    extraction, span = _span(target)
    try:
        message = withheld_message(world.vault(), world.repository, extraction, [span])
    except Exception:  # noqa: BLE001
        return R
    return W if message else S


@surface("IP")
def _figure_item_passages(probe: Probe, target: Target) -> str:
    from learnloop.figures.protection import item_passages

    world = probe.world(target)
    try:
        found = item_passages(world.vault(), world.repository, clock=CLOCK)
    except Exception:  # noqa: BLE001
        return R
    if found is None:
        return W  # nothing could be read: every prebuild is withheld
    spans, whole = found
    own = _own_passage(world, target)
    return W if own in spans or own[0] in whole else S


def _own_passage(world: World, target: Target) -> tuple[str, str]:
    """The item's own exercise passage (its canonical exercise or block reference): what IP and MC guard."""

    item = world.vault().practice_items[target.item_id]
    keys, whole = EM.item_source_keys(item)
    if keys:
        return sorted(keys)[0]
    if whole:
        return (sorted(whole)[0], "")
    pytest.fail(f"{target.row}'s item names no passage")


@surface("SC")
def _coverage_protection(probe: Probe, target: Target) -> str:
    from learnloop.source_retrieval.section_coverage import read_protection

    world = probe.world(target)
    extraction, span = _span(target)
    try:
        protection = probe.once(world, "SC", lambda: read_protection(world.vault(), world.repository))
    except Exception:  # noqa: BLE001
        return R
    return W if protection.reading_out(extraction) or protection.span_out(extraction, span) else S


def _source_ref(world: World, target: Target) -> Any:
    """The reference a quote of the target carries, as the vault's model (the predicate reads its attributes)."""

    from learnloop.vault.models import SourceRef
    from tests.exam_scope_fixtures import ref

    if target.key is None:
        return world.vault().practice_items[target.item_id].provenance.source_refs[0]
    return SourceRef.model_validate(ref(target.source_id, *target.key))


@surface("SQ")
def _quote_protected(probe: Probe, target: Target) -> str:
    world = probe.world(target)
    try:
        material = EM.exam_material(world.vault(), world.repository)
        protected = EM.source_ref_protected(material, _source_ref(world, target), world.repository)
    except Exception:  # noqa: BLE001
        return R
    return W if protected else S


@surface("BG")
def _book_guide(probe: Probe, target: Target) -> str:
    from learnloop.source_retrieval.reading_paths import ReadingPathError, path_inputs

    world = probe.world(target)
    extraction, span = _span(target)
    try:
        inputs = path_inputs(world.vault(), world.repository, extraction)
    except ReadingPathError:
        return R
    except Exception:  # noqa: BLE001
        return R
    return S if any(span in section.span_ids for section in inputs.sections) else W


@surface("LF")
def _leakage_floor(probe: Probe, target: Target) -> str:
    from learnloop.content.authoring.practice_leakage import build_held_out_inventory, screen_practice_payload

    world = probe.world(target)
    try:
        inventory = probe.once(world, "LF", lambda: build_held_out_inventory(world.vault(), world.repository))
    except Exception:  # noqa: BLE001
        return R
    return W if screen_practice_payload({"prompt": sentence(target.mark)}, inventory) else S


@surface("RF")
def _reserved_questions(probe: Probe, target: Target) -> str:
    from learnloop.content.authoring.practice_leakage import check_leakage, reserved_questions
    from learnloop.learner_protection import withheld_items

    world = probe.world(target)

    def read():
        vault = world.vault()
        return reserved_questions(vault, world.repository, withheld_items(vault, world.repository))

    try:
        reserved = probe.once(world, "RF", read)
    except Exception:  # noqa: BLE001
        return R
    if target.item_id is not None:
        from learnloop.content.authoring.practice_leakage import _normalize_tokens

        prompt = world.vault().practice_items[target.item_id].prompt
        return W if " ".join(_normalize_tokens(prompt)) in reserved.stems else S
    return W if check_leakage(sentence(target.mark), reserved.inventory) else S


@surface("PW")
def _phone_withheld(probe: Probe, target: Target) -> str:
    from learnloop.reader.phone_media import phone_withheld

    world = probe.world(target)
    extraction, span = _span(target)
    withheld = phone_withheld(world.vault(), world.repository, extraction, [span])
    return W if withheld.whole or span in withheld.spans else S


def _media(refusal: Any) -> str:
    if refusal is None:
        return S
    if refusal.code == "held_out_material":
        return R
    return f"refused:{refusal.code}"


@surface("PG")
def _phone_page(probe: Probe, target: Target) -> str:
    from learnloop.reader.phone_media import page_refusal

    world = probe.world(target)
    extraction, _span_id = _span(target)
    digest = _reading_digest(world, extraction)
    return _media(page_refusal(world.vault(), world.repository, digest, int(target.page)))


def _reading_digest(world: World, extraction_id: str) -> str:
    from learnloop.reader.phone_media import digest_of_reading

    digest = digest_of_reading(world.repository, extraction_id)
    assert digest, extraction_id
    return digest


@contextmanager
def _image_original(world: World, revision_id: str):
    """The revision's original, for one call, an image (the phone serves an image original as an asset)."""

    with world.repository.connection() as connection:
        (before,) = connection.execute("SELECT asset_hash FROM source_revisions WHERE id = ?", (revision_id,)).fetchone()
    digest = store_png(world.root, sum(map(ord, revision_id)))
    with world.repository.connection() as connection:
        connection.execute("UPDATE source_revisions SET asset_hash = ? WHERE id = ?", (digest, revision_id))
        connection.commit()
    try:
        yield digest
    finally:
        with world.repository.connection() as connection:
            connection.execute("UPDATE source_revisions SET asset_hash = ? WHERE id = ?", (before, revision_id))
            connection.commit()


@surface("PI")
def _phone_image(probe: Probe, target: Target) -> str:
    from learnloop.reader.phone_media import asset_refusal

    world = probe.world(target)
    with _image_original(world, target.revision_id) as digest:
        return _media(asset_refusal(world.vault(), world.repository, digest))


@surface("CI")
def _canonical_import(probe: Probe, target: Target) -> str:
    from learnloop.content.authoring.source_exercise_import import import_source_exercise

    world = probe.world(target, own="import")
    extraction, span = _span(target)
    outcome = import_source_exercise(world.root, world.repository, extraction_id=extraction, span_ids=[span],
                                     caller="learner", clients={}, clock=CLOCK)
    reason = str(outcome.get("reason") or "")
    if outcome["status"] == "rejected" and reason.startswith("exam_material"):
        return R
    assert outcome.get("practice_item_id") is None, outcome  # no client: nothing is ever written
    return S


# --- serving, measurement and devices ---------------------------------------------------------------------------


@surface("RT")
def _routine(probe: Probe, target: Target) -> str:
    from learnloop.scheduling.serving_exclusions import routine_serving_exclusions, routine_withhold_reason

    world = probe.world(target)
    vault, item = _item(world, target)
    try:
        exclusions = probe.once(world, "RT", lambda: routine_serving_exclusions(vault, world.repository))
    except Exception:  # noqa: BLE001
        return R
    return W if routine_withhold_reason(vault, item, None, exclusions) else S


@surface("OT")
def _out_of_timing(probe: Probe, target: Target) -> str:
    from learnloop.scheduling.serving_exclusions import out_of_timing_serving_exclusions
    from learnloop.serve_eligibility import COLD_FOLLOWUP_TASK_KINDS, COLD_RETRIEVAL_DELAY

    world = probe.world(target)
    vault, item = _item(world, target)
    try:
        exclusions = probe.once(world, "OT", lambda: out_of_timing_serving_exclusions(
            vault, world.repository, cold_followup_kinds=COLD_FOLLOWUP_TASK_KINDS,
            reveal_window=COLD_RETRIEVAL_DELAY, clock=CLOCK))
    except Exception:  # noqa: BLE001
        return R
    return W if item.id in exclusions.out_of_timing_item_ids else S


@surface("PK")
def _pick(probe: Probe, target: Target) -> str:
    from learnloop.instructional.practice import refuse_protected_pick

    world = probe.world(target)
    try:
        refuse_protected_pick(world.repository, target.item_id, vault=world.vault())
    except Exception:  # noqa: BLE001
        return R
    return S


@surface("SS")
def _session_serve(probe: Probe, target: Target) -> str:
    from learnloop_sidecar.serving import refuse_held_out_item

    world = probe.world(target)
    vault, item = _item(world, target)
    try:
        refuse_held_out_item(vault, world.repository, item)
    except Exception:  # noqa: BLE001
        return R
    return S


@surface("DV")
def _device(probe: Probe, target: Target) -> str:
    from learnloop.scheduling.device_eligibility import PHONE, ineligibility_reason

    vault, item = _item(probe.world(target), target)
    return W if ineligibility_reason(vault, item, PHONE) else S


@surface("PF")
def _plan_step(probe: Probe, target: Target) -> str:
    from learnloop.scheduling.device_eligibility import PHONE, DeviceFilter, PlanStepFilter

    vault, item = _item(probe.world(target), target)
    return W if PlanStepFilter(device_filter=DeviceFilter(vault=vault, device_class=PHONE)).holds(item) else S


def _exposed(probe: Probe, target: Target, *, with_held_out: bool) -> str:
    world = probe.world(target)
    vault, item = _item(world, target)
    try:
        exposed = EM.exposed_items(vault, world.repository, [item], with_held_out=with_held_out)
    except Exception:  # noqa: BLE001
        return R
    return W if item.id in exposed else S


@surface("EX")
def _exposed_shown(probe: Probe, target: Target) -> str:
    return _exposed(probe, target, with_held_out=False)


@surface("EH")
def _exposed_held(probe: Probe, target: Target) -> str:
    return _exposed(probe, target, with_held_out=True)


@surface("CO")
def _cold_open(probe: Probe, target: Target) -> str:
    from learnloop.instructional.policy import cold_administration_open

    world = probe.world(target)
    try:
        return W if cold_administration_open(world.repository, target.item_id) else S
    except Exception:  # noqa: BLE001
        return R


@surface("SE")
def _serve_eligibility(probe: Probe, target: Target) -> str:
    from learnloop.serve_eligibility import PROBE, REFUSE, decide, gather

    world = probe.world(target)
    inputs = gather(world.repository, practice_item_id=target.item_id, learning_object_id=LO,
                    at=NOW.isoformat().replace("+00:00", "Z"))
    return R if decide(inputs, PROBE).verdict == REFUSE else S


# --- a model's view of an item ---------------------------------------------------------------------------------


def _withheld(probe: Probe, world: World):
    from learnloop.learner_protection import withheld_items

    return probe.once(world, "LP", lambda: withheld_items(world.vault(), world.repository))


@surface("LP")
def _learner_protection(probe: Probe, target: Target) -> str:
    withheld = _withheld(probe, probe.world(target))
    return W if not withheld.available or withheld.reason(target.item_id) else S


@surface("AP")
def _attempt_protection(probe: Probe, target: Target) -> str:
    from learnloop.learner_protection import attempt_protection

    withheld = _withheld(probe, probe.world(target))
    attempt = {"item": target.item_id, "type": "independent_attempt", "probe": None}
    return W if attempt_protection(withheld, attempt) else S


@surface("AD")
def _ad_protection(probe: Probe, target: Target) -> str:
    from learnloop.adaptive_difficulty.protection import protection

    world = probe.world(target)
    found = probe.once(world, "AD", lambda: protection(world.vault(), world.repository))
    return W if target.item_id in found.ids else S


@surface("LC")
def _learning_context(probe: Probe, target: Target) -> str:
    from learnloop.learner_context import ContextLimits, learning_context

    world = probe.world(target)

    def read():
        return json.dumps(learning_context(world.vault(), world.repository, learning_object_ids=[LO], now=NOW,
                                           limits=ContextLimits(traces=200)), default=str)

    text = probe.once(world, "LC", read)
    item = world.vault().practice_items[target.item_id]
    stem_word = item.prompt.split()[0]
    return S if stem_word in text else W


@surface("FD")
def _followup_door(probe: Probe, target: Target) -> str:
    from learnloop.followup_serve.identity import door_refusal

    return W if door_refusal(probe.world(target).repository, target.item_id) else S


@surface("KY")
def _key_payload(probe: Probe, target: Target) -> str:
    from learnloop_sidecar.handlers.serializers import practice_item_detail

    world = probe.world(target)
    try:
        detail = practice_item_detail(world.vault(), world.repository, target.item_id)
    except Exception:  # noqa: BLE001
        return R
    text = json.dumps(detail, default=str)
    return S if "KEY answer" in text or "expected" in text.lower() else W


# --- the Reader and the phone: the sidecar's own handlers -------------------------------------------------------


class ModelReached(Exception):
    """Raised by :class:`RecordingModel` after it has recorded what it was sent: the request got that far."""


class RecordingModel:
    """A model double for every structured role: it records each prompt and stops the request there."""

    provider_name = "g6_recording_model"
    provider_type = "fake"
    model = "g6-recording"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        return True

    def complete(self, request: Any) -> Any:
        self.prompts.append(str(getattr(request, "prompt", request)))
        raise ModelReached

    def carried(self, mark: str) -> bool:
        return any(mark in prompt for prompt in self.prompts)


def _sidecar(probe: Probe, world: World):
    """A sidecar context on the world, for the current test only: its background workers (the Reader's drain,
    quick checks) are stopped and joined when the test ends (:func:`_close_contexts`)."""

    from learnloop_sidecar.context import SidecarContext

    if world.root not in probe.contexts:
        ctx = SidecarContext()
        ctx.load(world.root, maintenance=False)
        probe.contexts[world.root] = ctx
    return probe.contexts[world.root]


@contextmanager
def _phone(ctx: Any, phone: bool):
    from learnloop_sidecar.request_origin import RequestOrigin

    if not phone:
        yield
        return
    with ctx.acting_as(RequestOrigin(device_id="g6-phone", phone_reader=True)):
        yield


def _call(probe: Probe, target: Target, name: str, params: dict[str, Any], *, phone: bool,
          own: str | None = None) -> Any:
    import learnloop_sidecar.handlers  # noqa: F401 - registers every method
    from learnloop_sidecar.registry import METHOD_REGISTRY

    world = probe.world(target, own=own)
    ctx = _sidecar(probe, world)
    spec = METHOD_REGISTRY[name]
    with _phone(ctx, phone):
        return spec.handler(ctx, spec.params_model.model_validate(params))


def _render(probe: Probe, target: Target, *, phone: bool) -> str:
    extraction, span = _span(target)
    try:
        payload = _call(probe, target, "reader.render_view", {"extraction_id": extraction}, phone=phone)
    except Exception:  # noqa: BLE001
        return R
    block = next((block for block in payload.get("blocks") or [] if block.get("spanId") == span), None)
    return S if block is not None and target.mark in json.dumps(block) else W


@surface("RV")
def _phone_render(probe: Probe, target: Target) -> str:
    return _render(probe, target, phone=True)


@surface("RD")
def _desktop_render(probe: Probe, target: Target) -> str:
    return _render(probe, target, phone=False)


@surface("GP")
def _phone_guide(probe: Probe, target: Target) -> str:
    extraction, _span_id = _span(target)
    try:
        plan = _call(probe, target, "reader.guide_plan", {"extraction_id": extraction}, phone=True)
    except Exception:  # noqa: BLE001
        return R
    return S if target.mark in json.dumps(plan) else W


@contextmanager
def _tutor(model: RecordingModel):
    """The Reader's tutor provider, ready, as the recording model."""

    from types import SimpleNamespace
    from unittest import mock

    import learnloop_sidecar.handlers.reader as reader_handlers

    with mock.patch.object(reader_handlers, "ready_tutor_qa_provider",
                           lambda vault: ("g6", SimpleNamespace(ready=True), model)):
        yield


def _model_answer(model: RecordingModel, mark: str, refused: bool) -> str:
    if model.prompts:
        return S if model.carried(mark) else W
    return R if refused else W


def _ask(probe: Probe, target: Target, *, phone: bool) -> str:
    own = "PA" if phone else "RA"
    extraction, span = _span(target)
    model = RecordingModel()
    refused = False
    with _tutor(model):
        try:
            _call(probe, target, "reader.ask", {"extraction_id": extraction, "span_id": span,
                                                "question": "What does this passage say?"}, phone=phone, own=own)
        except ModelReached:
            pass
        except Exception:  # noqa: BLE001
            refused = True
    return _model_answer(model, target.mark, refused)


@surface("RA")
def _reader_ask(probe: Probe, target: Target) -> str:
    return _ask(probe, target, phone=False)


@surface("PA")
def _phone_ask(probe: Probe, target: Target) -> str:
    return _ask(probe, target, phone=True)


def _stored_exchange(probe: Probe, target: Target, own: str) -> None:
    """One completed Ask exchange anchored on the target, stored before anything is asked of it."""

    world = probe.world(target, own=own)
    extraction, span = _span(target)

    def store():
        payload = {"extraction_id": extraction, "span_id": span, "answer_md": f"{target.mark} answered.",
                   "citations": [{"extraction_id": extraction, "span_id": span, "label": "here"}],
                   "manifest": {"question_md": "why?", "selection": {"span_ids": [span],
                                                                     "quote_md": sentence(target.mark)}}}
        world.repository.append_interaction_event(kind="reader_answer_submitted", origin="learner",
                                                  subject_type="reader_span", subject_id=f"span:{extraction}/{span}",
                                                  payload_json=json.dumps(payload))
        return True

    probe.once(world, f"exchange:{extraction}:{span}", store)


def _history(probe: Probe, target: Target, *, phone: bool) -> str:
    own = "history"
    _stored_exchange(probe, target, own)
    extraction, _span_id = _span(target)
    try:
        history = _call(probe, target, "reader.ask_history", {"extraction_id": extraction}, phone=phone, own=own)
    except Exception:  # noqa: BLE001
        return R
    return S if f"{target.mark} answered" in json.dumps(history) else W


@surface("PH")
def _phone_history(probe: Probe, target: Target) -> str:
    return _history(probe, target, phone=True)


@surface("DH")
def _desktop_history(probe: Probe, target: Target) -> str:
    return _history(probe, target, phone=False)


@surface("AS")
def _as_printed(probe: Probe, target: Target) -> str:
    try:
        view = _call(probe, target, "practice.as_printed", {"practice_item_id": target.item_id}, phone=True)
    except Exception:  # noqa: BLE001
        return R
    return W if view.get("reason") == "held_out_material" else S


@surface("CK")
def _quick_check(probe: Probe, target: Target) -> str:
    return _check(probe, target, {"section_id": None})


def _check(probe: Probe, target: Target, payload: dict[str, Any]) -> str:
    """A Reader check job (section, inquiry or selection scope): R when it refuses before its client is built."""

    from types import SimpleNamespace

    from learnloop.content.pipeline import jobs

    world = probe.world(target, own="check")
    extraction, span = _span(target)
    if "section_id" in payload:
        payload = {"extraction_id": extraction, "section_id": _section_of(world, target)}
    else:
        payload = {"extraction_id": extraction, **{key: (value if value != "@span" else [span])
                                                    for key, value in payload.items()}}
    built: list[str] = []

    def client(_ctx):
        built.append("client")
        raise ModelReached

    ctx = SimpleNamespace(
        payload=payload, repo=world.repository, clock=CLOCK, report=lambda *a, **k: None, vault_root=world.root,
        job={"id": "job_g6_check", "attempt_count": 1}, cancelled=lambda: False, bind_interruptible=lambda c: None,
        services=SimpleNamespace(quick_check_client=client))
    try:
        jobs.handle_reader_quick_check(ctx)
    except ModelReached:
        pass
    except Exception:  # noqa: BLE001
        return S if built else R
    return S if built else W


@surface("PS")
def _preset(probe: Probe, target: Target) -> str:

    world = probe.world(target, own="PS")
    extraction, span = _span(target)
    return probe.once(world, f"PS:{extraction}:{span}", lambda: _preset_once(world, target))


def _preset_once(world: World, target: Target) -> str:
    """One preset per passage: a second request for the same passage and preset is the first one again."""

    from learnloop.reader import reader_requests as RR

    extraction, span = _span(target)
    model = RecordingModel()
    queued = RR.enqueue_request(world.repository, source_id=target.source_id, revision_id=target.revision_id,
                                extraction_id=extraction, span_id=span, preset="alt_explanation")
    try:
        source_sets = world.vault()
        RR.drain_requests(world.repository, synthesize=RR.model_synthesis(model, source_sets=source_sets),
                          clock=CLOCK)
    except Exception:  # noqa: BLE001
        return R if not model.prompts else _model_answer(model, target.mark, True)
    status = RR.request_status(world.repository, request_id=queued["request_id"]) or {}
    return _model_answer(model, target.mark, status.get("status") == "failed")


@surface("RI")
def _reader_import(probe: Probe, target: Target) -> str:
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import IngestRunnerError, JobContext
    from tests.exercise_authoring_helpers import FakeClient
    from tests.protection_matrix_helpers import reader_import_context

    world = probe.world(target, own="import")
    extraction, span = _span(target)
    node = {"spanId": span} if target.camel else {"span_id": span}

    class Author(FakeClient):
        def run_exercise_authoring(self, context):
            self.calls.append(context)
            raise ModelReached

    author = Author()
    ctx = reader_import_context(world.root, world.repository, extraction_id=extraction,
                                nodes=[{**node, "quote": sentence(target.mark)}], client=author,
                                source_id=target.source_id)
    from unittest import mock

    with mock.patch.object(JobContext, "report", lambda self, *a, **k: None):
        try:
            jobs.handle_reader_exercise_import(ctx)
        except ModelReached:
            pass
        except IngestRunnerError:
            if not author.calls:
                return R
        except Exception:  # noqa: BLE001
            if not author.calls:
                return R
    if not author.calls:
        return R
    return S if target.mark in json.dumps(author.calls[0].model_dump(mode="json") if hasattr(
        author.calls[0], "model_dump") else author.calls[0].__dict__, default=str) else W


@surface("LS")
def _library_search(probe: Probe, target: Target) -> str:
    from learnloop.source_retrieval.library import search_library

    world = probe.world(target)
    extraction, span = _span(target)
    try:
        found = search_library(world.vault(), world.repository, query=target.mark.lower() + "alpha")
    except Exception:  # noqa: BLE001
        return R
    return S if any(hit.get("extraction_id") == extraction and hit.get("span_id") == span
                    for hit in found.get("hits") or []) else W


# --- authoring neighbours: a safe exercise selected beside the protected target ----------------------------------


class _Author:
    """The exercise author, recording the context it is sent and stopping there."""

    provider_name = "g6_author"
    provider_type = "fake"
    model = "g6-author"

    def __init__(self) -> None:
        self.seen: list[Any] = []

    def supports(self, capability: str) -> bool:
        return True

    def run_exercise_authoring(self, context: Any) -> Any:
        self.seen.append(context)
        raise ModelReached

    def complete(self, request: Any) -> Any:
        from tests.structured_ai import StructuredClientFake

        return StructuredClientFake.complete(self, request)


def _author_saw(author: _Author, mark: str) -> str:
    if not author.seen:
        return R
    context = author.seen[0]
    text = json.dumps(context.model_dump(mode="json") if hasattr(context, "model_dump") else vars(context),
                      default=str)
    return S if mark in text else W


def _block_text(world: World, extraction_id: str, span_id: str) -> str:
    ir = world.repository.load_document_ir(extraction_id)
    return next(block.text for block in ir.blocks if block.span_id == span_id)


@surface("RN")
def _reader_neighbour(probe: Probe, target: Target) -> str:
    """The Reader's import of the safe exercise beside the target: does the target enter the author's context?"""

    from unittest import mock

    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import JobContext
    from tests.protection_matrix_helpers import reader_import_context

    world = probe.world(target, own="import")
    extraction, _span_id = _span(target)
    author = _Author()
    node = {"spanId": target.neighbor_of} if target.camel else {"span_id": target.neighbor_of}
    node["quote"] = _block_text(world, extraction, target.neighbor_of)
    ctx = reader_import_context(world.root, world.repository, extraction_id=extraction, nodes=[node],
                                client=author, source_id=target.source_id)
    with mock.patch.object(JobContext, "report", lambda self, *a, **k: None):
        try:
            jobs.handle_reader_exercise_import(ctx)
        except ModelReached:
            pass
        except Exception:  # noqa: BLE001
            pass
    return _author_saw(author, target.mark)


@surface("CN")
def _canonical_neighbour(probe: Probe, target: Target) -> str:
    """The canonical import of the safe exercise beside the target: does the target enter the author's context?"""

    from learnloop.content.authoring.source_exercise_import import import_source_exercise

    world = probe.world(target, own="import")
    extraction, _span_id = _span(target)
    author = _Author()
    try:
        outcome = import_source_exercise(world.root, world.repository, extraction_id=extraction,
                                         span_ids=[target.neighbor_of], caller="learner",
                                         clients={"authoring": author}, clock=CLOCK)
    except ModelReached:
        outcome = None
    if outcome is not None and not author.seen:
        return R
    return _author_saw(author, target.mark)


# --- MCP and the Teacher ----------------------------------------------------------------------------------------


@surface("MC")
def _mcp_passages(probe: Probe, target: Target) -> str:
    from learnloop.remote.sources import SourcesUnavailable, find_passages

    world = probe.world(target, own="MC")
    extraction, span = _span(target)
    try:
        result = find_passages(world.vault(), world.repository, sentence(target.mark), call_id=f"g6-{target.row}",
                               clock=CLOCK)
    except SourcesUnavailable:
        return R
    except Exception:  # noqa: BLE001
        return R
    shown = {(passage["citation"]["extraction_id"], passage["citation"]["span_id"])
             for passage in result.payload.get("passages") or []}
    return S if (extraction, span) in shown else W


@surface("ML")
def _mcp_library(probe: Probe, target: Target) -> str:
    from learnloop.remote.runtime import RemoteRuntime
    from learnloop.remote.views import library

    world = probe.world(target)

    def read():
        return library(RemoteRuntime.attach(world.root, load_environment=False), limit=500)

    try:
        listed = probe.once(world, "ML", read)
    except Exception:  # noqa: BLE001
        return R
    return S if any(card["source_id"] == target.source_id for card in listed["sources"]) else W


@surface("TB")
def _teacher_goal(probe: Probe, target: Target) -> str:
    from learnloop.teacher.brief import LessonRefused, resolve_goal

    world = probe.world(target)
    extraction, span = _span(target)
    try:
        resolve_goal(world.vault(), world.repository, entry="reader_selection",
                     selection={"extraction_id": extraction, "span_ids": [span]})
    except LessonRefused as refused:
        return R if refused.code == "protected" else S
    except Exception:  # noqa: BLE001
        return R
    return S


# --- the library: an ask, its kept job, its organizer notes and its pinned tutor --------------------------------


def _key(target: Target) -> str:
    extraction, span = _span(target)
    return f"{extraction}:{span}"


@surface("LA")
def _library_ask(probe: Probe, target: Target) -> str:
    """A library search (no reading anchor) for the target's own words: is the target among its passages?"""


    world = probe.world(target, own="library-search")
    # A search is a span's question, not an item's: an item row asks it of its source span, once.
    return probe.once(world, f"LA:{_key(target)}", lambda: _library_ask_once(probe, world, target))


def _library_ask_once(probe: Probe, world: World, target: Target) -> str:
    from learnloop_sidecar.errors import SidecarError
    from tests.library_ask_fixtures import call

    ctx = _sidecar(probe, world)
    try:
        # The main search only: the expansions search again for neighbouring topics, not for the target.
        asked = call(ctx, "reader.library_ask", {"query": sentence(target.mark), "entry": "library_search",
                                                 "expand": []})
    except SidecarError:
        return R
    return S if _key(target) in {hit["key"] for hit in asked.get("hits") or []} else W


def _stored_ask(probe: Probe, target: Target, *, own: str = "library-kept") -> tuple[Any, str, str]:
    """An ask whose kept result shows the target, as a search made before its mark would have kept it: the
    search is answered with the target's passage. Returns the sidecar, the ask id and its job id."""

    from types import SimpleNamespace
    from unittest import mock

    import learnloop.instructional.sources as service
    from learnloop_sidecar.post_attempt_worker import PostAttemptWorker
    from tests.library_ask_fixtures import ask_rows, call_rpc

    world = probe.world(target, own=own)
    ctx = _sidecar(probe, world)
    ctx.post_attempt_worker = PostAttemptWorker(autostart=False)
    extraction, span = _span(target)
    hit = {"extraction_id": extraction, "span_id": span, "text": sentence(target.mark), "source_id": target.source_id,
           "source_title": target.source_id, "role": "explanation", "block_type": "Text", "page": target.page,
           "section": None}
    before = {row["id"] for row in ask_rows(world.repository)}
    # The search's manifest names what it returned: the stored ask's passages are read from it.
    found = SimpleNamespace(hits=[hit], manifest={"returned": [[extraction, span]]}, status="ok", policy="reading")
    with mock.patch.object(service, "propose_sources", lambda *a, **k: found):
        job = call_rpc(ctx, "reader.library_ask", {"query": "what does this passage say", "entry": "library_search",
                                                   "expand": []})
        kept = ctx.library_ask_jobs.get(job["jobId"])
        assert kept is not None and kept.done.wait(60), "the ask never finished"
    (ask_id,) = {row["id"] for row in ask_rows(world.repository)} - before
    return ctx, ask_id, job["jobId"]


@surface("LJ")
def _kept_job(probe: Probe, target: Target) -> str:
    from learnloop_sidecar.errors import SidecarError
    from tests.library_ask_fixtures import call_rpc

    ctx, _ask_id, job_id = _stored_ask(probe, target)
    try:
        job = call_rpc(ctx, "reader.library_job", {"jobId": job_id})
    except SidecarError:
        return R
    return S if _key(target) in json.dumps(job.get("result")) else W


@surface("OR")
def _organizer(probe: Probe, target: Target) -> str:
    from learnloop_sidecar.errors import SidecarError
    from tests.library_ask_fixtures import OrganizerFake, call

    ctx, ask_id, _job_id = _stored_ask(probe, target)
    ctx.library_organizer_client = OrganizerFake()
    # The current-key check is the organizer's protection; what it does with an admitted pool after it (here an
    # empty pool: a planted kept hit is no library passage of its own) is not a protection answer.
    try:
        call(ctx, "reader.library_ask_notes", {"askId": ask_id})
    except SidecarError as refused:
        return R if refused.code == "exam_material" else f"refused:{refused.code}"
    return S


@surface("PT")
def _pinned_tutor(probe: Probe, target: Target) -> str:


    world = probe.world(target, own="library-kept")
    return probe.once(world, f"PT:{_key(target)}", lambda: _pinned_tutor_once(probe, target))


def _pinned_tutor_once(probe: Probe, target: Target) -> str:
    from types import SimpleNamespace
    from unittest import mock

    import learnloop_sidecar.handlers.ai_providers as providers
    from tests.library_ask_fixtures import call

    ctx, ask_id, _job_id = _stored_ask(probe, target)
    model = RecordingModel()
    refused = False
    with mock.patch.object(providers, "ready_tutor_qa_provider",
                           lambda vault: ("g6", SimpleNamespace(ready=True), model)):
        try:
            call(ctx, "reader.library_ask_tutor", {"askId": ask_id, "pinnedSpanKeys": [_key(target)]})
        except Exception:  # noqa: BLE001 - a refusal, or the recording model stopping the answer
            refused = True
    return _model_answer(model, target.mark, refused)


# --- the cells --------------------------------------------------------------------------------------------------

#: The surfaces the matrix drives, in the table's order.
DRIVEN = [column for column in COLUMNS if column in ADAPTERS]


def _answers(probe: Probe, column: str) -> dict[str, str]:
    return {row: ADAPTERS[column](probe, probe.base.targets[row])
            for (row, cell_column), value in EXPECTED.items() if cell_column == column and value != NA}


# One test per surface, every row of it compared: a test per cell spends most of its time in per-test setup, which
# would make the matrix minutes long. The failure lists every cell that moved, by row.
@pytest.mark.parametrize("column", DRIVEN)
def test_surface_answers_every_fixture_as_pinned(probe: Probe, column: str) -> None:
    actual = _answers(probe, column)
    expected = {row: value for (row, cell_column), value in EXPECTED.items() if cell_column == column and value != NA}
    moved = {row: f"pinned {expected[row]}, now {actual[row]}" for row in expected if actual[row] != expected[row]}
    assert not moved, f"{column}: {moved}"




# --- fail closed: the span authority raises ---------------------------------------------------------------------
# The exam predicate's readers (``exam_material``, ``held_out_material``, ``held_out_partition`` and the readers
# built on them) patched to raise wherever a module bound them, so every surface meets the failure through its own
# import. Each surface is asked about a protected target and a clean one. Fixture 8 (the source-sets file
# unparseable or empty) is the matrix's own rows.

FAILING_READERS = ("exam_material", "held_out_material", "held_out_partition", "held_out_items", "spans_withheld",
                   "exam_withheld", "role_material", "held_out_spans", "source_marks")

#: ``surface: (answer for 3.held or 6.3canonical, answer for 0.control or 6.held-grade)`` with the readers raising.
#: ``S`` on the protected target is a surface open to this fault: the device, eligibility and workflow doors, the
#: shown-material reader and the cold reservation (they read no source set), the MCP library's titles, and the raw
#: local search and history: each answers another question than "is this exam material".
FAULT_EXPECTED: dict[str, tuple[str, str]] = {
    "TE": (R, R), "MR": (R, R), "RA": (R, R), "PS": (R, R), "CK": (R, R), "GU": (R, R), "FI": (R, R),
    "IP": (W, W), "SC": (R, R), "SQ": (R, R), "MC": (R, R), "CI": (R, R), "RI": (R, R), "LF": (R, R),
    "RF": (R, R), "RT": (R, R), "OT": (R, R), "PK": (R, R), "SS": (R, R), "DV": (S, S), "PF": (S, S),
    "EX": (S, S), "EH": (R, R), "CO": (S, S), "SE": (S, S), "LP": (W, W), "AP": (W, W), "AD": (W, W),
    "LC": (W, W), "PW": (W, W), "PG": (R, R), "PI": (R, R), "RV": (R, R), "GP": (R, R), "PA": (R, R),
    "PH": (W, W), "AS": (W, W), "ML": (S, S), "LA": (R, R), "OR": (R, R), "LJ": (R, R), "PT": (R, R),
    "TB": (R, R), "LS": (S, S), "DH": (S, S), "FD": (S, S), "KY": (R, R), "BG": (R, R), "RD": (R, R),
    "RN": (R, NA), "CN": (R, NA),
}

_FAULT_TARGETS = {"span": ("3.held", "0.control"), "item": ("6.3canonical", "6.held-grade")}


def _fault_targets(probe: Probe, column: str) -> tuple[Target, Target]:
    applicable = {row for (row, cell_column), value in EXPECTED.items() if cell_column == column and value != NA}
    kind = "span" if "3.held" in applicable else "item"
    protected, clean = _FAULT_TARGETS[kind]
    return (replace(probe.base.targets[protected], state="fault"), replace(probe.base.targets[clean], state="fault"))


@contextmanager
def _readers_raise():
    import sys
    from unittest import mock

    def fails(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("the exam predicate could not be read")

    originals = {name: getattr(EM, name) for name in FAILING_READERS}
    patches = []
    for module in list(sys.modules.values()):
        if module is None or not getattr(module, "__name__", "").startswith(("learnloop", "tests.")):
            continue
        for name, original in originals.items():
            if getattr(module, name, None) is original:
                patches.append(mock.patch.object(module, name, fails))
    for patch in patches:
        patch.start()
    try:
        yield
    finally:
        for patch in reversed(patches):
            patch.stop()


def _fault_answers(probe: Probe, column: str) -> tuple[str, str]:
    protected, clean = _fault_targets(probe, column)
    with _readers_raise():
        answers = []
        # An authoring neighbour is asked only beside protected material: there is no clean neighbour question.
        for target in (protected,) if column in ("RN", "CN") else (protected, clean):
            try:
                answers.append(ADAPTERS[column](probe, target))
            except Exception as exc:  # noqa: BLE001 - an adapter that itself raised: the surface refused
                answers.append(R if "could not be read" in str(exc) else f"raised:{type(exc).__name__}")
    return answers[0], (answers[1] if len(answers) > 1 else NA)


@pytest.mark.parametrize("column", DRIVEN)
def test_each_surface_with_its_exam_predicate_raising(probe: Probe, column: str) -> None:
    assert _fault_answers(probe, column) == FAULT_EXPECTED[column]



# --- reach: the cases one column can't show ---------------------------------------------------------------------

#: The Reader's other two check callers (CK's column drives the section check): an inquiry's passage check and an
#: active-reading selection question, each anchored on the target. ``row: (inquiry, selection)``.
CHECK_CALLERS: dict[str, tuple[str, str]] = {
    "0.control": (S, S), "1.paper": (S, S), "2.exam": (S, S), "3.held": (R, R), "3.neighbor": (S, S),
    "4.unmarked": (R, R), "5.signal": (R, R),
}


@pytest.mark.parametrize("row", sorted(CHECK_CALLERS))
def test_the_readers_inquiry_and_selection_checks_answer_as_its_section_check(probe: Probe, row: str) -> None:
    from learnloop.reader.reader_quick_check import SELECTION_STYLES

    target = probe.base.targets[row]
    inquiry = _check(probe, target, {"scope_kind": "inquiry", "inquiry_root_event_id": "evt_g6_root",
                                     "anchor_span_ids": "@span"})
    selection = _check(probe, target, {"scope_kind": "selection", "question_style": sorted(SELECTION_STYLES)[0],
                                       "anchor_span_ids": "@span"})
    assert (inquiry, selection) == CHECK_CALLERS[row]


#: A quote's reference to fixture 3's held span, in every form a reference takes, and what the quote rule says.
REFERENCE_FORMS: dict[str, str] = {
    "locator": W, "explicit_spans": W, "namespaced_span": W, "whole_extraction": W, "revision_only": W,
    "source_only": W, "neighbour_block": S,
}


def _reference(form: str, target: Target) -> Any:
    from learnloop.vault.models import SourceRef

    extraction, span = _span(target)
    base = {"ref_type": "canonical_source", "ref_id": target.source_id}
    fields = {
        "locator": {"source_id": target.source_id, "extraction_id": extraction, "locator": f"span:{extraction}/{span}"},
        "explicit_spans": {"source_id": target.source_id, "extraction_id": extraction, "span_ids": [span]},
        "namespaced_span": {"source_id": target.source_id, "span_ids": [f"{extraction}/{span}"]},
        "whole_extraction": {"source_id": target.source_id, "extraction_id": extraction},
        "revision_only": {"revision_id": target.revision_id},
        "source_only": {"source_id": target.source_id},
        "neighbour_block": {"source_id": target.source_id, "extraction_id": extraction, "span_ids": [target.neighbor_of]},
    }[form]
    return SourceRef.model_validate({**base, **fields})


@pytest.mark.parametrize("form", sorted(REFERENCE_FORMS))
def test_a_quotes_reference_in_every_form(probe: Probe, form: str) -> None:
    world = probe.base
    material = EM.exam_material(world.vault(), world.repository)
    protected = EM.source_ref_protected(material, _reference(form, world.targets["3.held"]), world.repository)
    assert (W if protected else S) == REFERENCE_FORMS[form]


#: An ordinary item once presented as a diagnostic probe (a completed presentation, not an open one).
PRESENTED: dict[str, str] = {
    "LP": W, "AP": W, "AD": S, "IP": W, "MC": W, "RF": S, "RT": S, "OT": S, "SE": S, "CO": S, "LC": W, "EX": S,
}


@pytest.mark.parametrize("column", sorted(PRESENTED))
def test_an_item_once_presented_as_a_probe(probe: Probe, column: str) -> None:
    assert ADAPTERS[column](probe, probe.base.targets["6.presented"]) == PRESENTED[column]


def test_a_held_grade_is_held_while_its_question_and_answer_stay_eligible(probe: Probe) -> None:
    from learnloop.held_grades import held_for_review_attempts
    from learnloop.learner_protection import attempt_result

    world = probe.base
    attempt_id = world.notes["attempts"]["6.held-grade"]
    with world.repository.connection() as connection:
        assert attempt_id in held_for_review_attempts(connection, [attempt_id])
    assert attempt_result(1.0, True) == "held_for_review"
    assert _learning_context(probe, world.targets["6.held-grade"]) == S


def test_the_phones_media_lift_admits_no_measurement(probe: Probe) -> None:
    from types import SimpleNamespace
    from unittest import mock

    from learnloop.reader.phone_media import media_predicate
    from learnloop.scheduling import device_eligibility as DE

    world = probe.base
    vault = world.vault()
    digest = world.pdf_digest[world.targets["0.control"].extraction_id]
    prompt = f"Look at [the page](llpdf://localhost/sha256-{digest.split(':', 1)[1]}#page=2)."

    def reason(mode: str) -> str | None:
        item = SimpleNamespace(id="pi_g6_media", practice_mode=mode, teach_back_source=None, error_hunt=None,
                               laddered_stem=None, prompt=prompt, provenance=None, lesson_id=None, lifecycle=None)
        with mock.patch.object(DE, "minted_for_lesson", lambda item: False):
            return DE.ineligibility_reason(vault, item, DE.PHONE, media=True,
                                           served=media_predicate(vault, world.repository))

    assert reason("short_answer") is None
    assert all(reason(mode) is not None for mode in sorted(DE.MEASUREMENT_MODES))


# --- defects: the desired answer, failing first ---------------------------------------------------------------
# Each pinned cell above keeps today's answer; the test below states the answer the ledger row's fix gives, as a
# strict xfail, so the fix turns exactly it green (and must flip the pinned cell in the same commit).


@pytest.mark.xfail(strict=True, reason="G6-P1: a figure prebuild's live-item guard omits exam-pool reservations")
def test_an_exam_reserved_items_own_passage_is_withheld_from_figure_prebuilds(probe: Probe) -> None:
    target = probe.base.targets["6.exam-reserved"]
    assert _figure_withheld(probe, target) == S  # its source is clean: the span filter can't catch it
    assert _figure_item_passages(probe, target) == W


@pytest.mark.xfail(strict=True, reason="G6-P6: the Reader import's held-out check reads only snake_case span_id")
def test_a_camel_case_selection_of_held_out_material_is_refused_before_the_author(probe: Probe) -> None:
    assert _reader_import(probe, probe.base.targets["3.held"]) == R
    assert _reader_import(probe, probe.base.targets["3.camel"]) == R


@pytest.mark.xfail(strict=True, reason="G6-P7: the Reader import's author context adds unchecked neighbours")
def test_the_reader_imports_author_never_sees_a_held_out_neighbour(probe: Probe) -> None:
    assert _reader_neighbour(probe, probe.base.targets["3.held"]) == W


@pytest.mark.xfail(strict=True, reason="G6-P7: the canonical import's author context adds unchecked neighbours")
def test_the_canonical_imports_author_never_sees_an_exam_neighbour(probe: Probe) -> None:
    assert _canonical_neighbour(probe, probe.base.targets["2.exam"]) == W


def _mark_held(world: World, unit: str) -> None:
    """The owner holds one clean-book unit out now, through the production writer."""

    from learnloop.content.synthesis.source_unit_selection import save_unit_selection
    from tests.protection_matrix_helpers import CLEAN_UNITS

    save_unit_selection(world.repository, "ext_g6clean", [f"c_{name}" for name in CLEAN_UNITS],
                        exam_use_modes={unit: "held_out_evaluation"}, clock=CLOCK)


def _completed_pinned_answer(probe: Probe, own: str):
    """A pinned tutor answer over the clean control passage, finished: the sidecar, its job id and the key."""

    from types import SimpleNamespace
    from unittest import mock

    import learnloop_sidecar.handlers.ai_providers as providers
    from tests.library_ask_fixtures import call_rpc, tutor_with_citations

    target = replace(probe.base.targets["0.control"], row=f"0.control-{own}")
    ctx, ask_id, _job = _stored_ask(probe, target, own=own)
    key = _key(target)
    tutor = tutor_with_citations([_span(target)], answer_md="GSIXCLEANCTRL is what your passage says.")
    with mock.patch.object(providers, "ready_tutor_qa_provider",
                           lambda vault: ("g6", SimpleNamespace(ready=True), tutor)):
        job = call_rpc(ctx, "reader.library_ask_tutor", {"askId": ask_id, "pinnedSpanKeys": [key]})
        kept = ctx.library_ask_jobs.get(job["jobId"])
        assert kept is not None and kept.done.wait(60), "the tutor never finished"
    return ctx, job["jobId"], probe.world(target, own=own)


def test_a_completed_pinned_answer_is_returned_after_its_passage_is_held_out(probe: Probe) -> None:
    """Today's answer of the completed tutor job (TJ): no current protection read when it is read again."""

    from tests.library_ask_fixtures import call_rpc

    ctx, job_id, world = _completed_pinned_answer(probe, "tj-today")
    _mark_held(world, "c_ctrl")
    for _poll in range(2):
        result = call_rpc(ctx, "reader.library_job", {"jobId": job_id})["result"]
        assert "GSIXCLEANCTRL" in json.dumps(result)


@pytest.mark.xfail(strict=True, reason="G6-P2: a completed pinned-tutor job is delivered with no current check")
def test_a_completed_pinned_answer_is_refused_once_its_passage_is_held_out(probe: Probe) -> None:
    from learnloop_sidecar.errors import SidecarError
    from tests.library_ask_fixtures import call_rpc

    ctx, job_id, world = _completed_pinned_answer(probe, "tj-desired")
    _mark_held(world, "c_ctrl")
    for _poll in range(2):
        with pytest.raises(SidecarError):
            call_rpc(ctx, "reader.library_job", {"jobId": job_id})


MISSING_KEY = "g6missing_extraction:s1"


def _ask_naming_a_missing_passage(probe: Probe, own: str):
    target = replace(probe.base.targets["0.control"], row=f"0.control-{own}", extraction_id="g6missing_extraction",
                     span_id="s1")
    return _stored_ask(probe, target, own=own)


def test_a_kept_answer_naming_a_passage_that_does_not_exist_is_returned(probe: Probe) -> None:
    """Today's answers of the organizer (OR) and the kept job (LJ) for a well-formed key naming no passage."""

    from tests.library_ask_fixtures import OrganizerFake, call, call_rpc

    ctx, ask_id, job_id = _ask_naming_a_missing_passage(probe, "missing-today")
    assert MISSING_KEY in json.dumps(call_rpc(ctx, "reader.library_job", {"jobId": job_id})["result"])
    ctx.library_organizer_client = OrganizerFake()
    assert call(ctx, "reader.library_ask_notes", {"askId": ask_id})["status"] == "empty_pool"


@pytest.mark.xfail(strict=True, reason="G6-P5: a cached key's protection check does not prove the passage exists")
def test_a_kept_answer_naming_a_passage_that_does_not_exist_is_refused(probe: Probe) -> None:
    from learnloop_sidecar.errors import SidecarError
    from tests.library_ask_fixtures import OrganizerFake, call, call_rpc

    ctx, ask_id, job_id = _ask_naming_a_missing_passage(probe, "missing-desired")
    with pytest.raises(SidecarError):
        call_rpc(ctx, "reader.library_job", {"jobId": job_id})
    ctx.library_organizer_client = OrganizerFake()
    with pytest.raises(SidecarError):
        call(ctx, "reader.library_ask_notes", {"askId": ask_id})


def _legacy_thread_ask(probe: Probe, own: str) -> RecordingModel:
    """Reader Ask with its inquiry branches off: an answer given on the control passage cites its neighbour (the
    reserved item's unit heading); that unit is then held out, and the learner asks again on the same passage."""

    from types import SimpleNamespace
    from unittest import mock

    import learnloop_sidecar.handlers.reader as reader_handlers
    from learnloop.ops.settings_store import apply_config_updates
    from tests.reader_tutor_fakes import LookupTutor

    target = replace(probe.base.targets["0.control"], row=f"0.control-{own}")
    world = probe.world(target, own=own)
    apply_config_updates(world.root / "learnloop.toml", {("reader_inquiry", "enabled"): False})
    extraction, span = _span(target)
    neighbour = "s4"  # the next unit's heading: GSIXCLEANRES
    tutor = LookupTutor(answer_md="As the next section says, GSIXCLEANRES holds the answer.",
                        cite=lambda context: [(extraction, neighbour)])
    params = {"extraction_id": extraction, "span_id": span, "question": "What does this passage say?"}
    with mock.patch.object(reader_handlers, "ready_tutor_qa_provider",
                           lambda vault: ("g6", SimpleNamespace(ready=True), tutor)):
        _call(probe, target, "reader.ask", params, phone=False, own=own)
    assert tutor.contexts and any(entry["span_id"] == neighbour for entry in tutor.contexts[0]["source_spans"])
    _mark_held(world, "c_res")
    model = RecordingModel()
    with _tutor(model):
        with pytest.raises(ModelReached):
            _call(probe, target, "reader.ask", {**params, "question": "And again?"}, phone=False, own=own)
    return model


def test_a_legacy_reader_thread_sends_an_answer_grounded_in_a_passage_held_out_since(probe: Probe) -> None:
    """Today's answer (RA, inquiry branches off): the held-out neighbour is out of the new manifest, but the earlier
    answer that quoted it is in the next model context."""

    model = _legacy_thread_ask(probe, "legacy-today")
    assert model.carried("GSIXCLEANRES")


@pytest.mark.xfail(strict=True, reason="G6-P3: a legacy Reader thread re-sends history with no current admission")
def test_a_legacy_reader_thread_leaves_out_an_answer_grounded_in_held_out_material(probe: Probe) -> None:
    model = _legacy_thread_ask(probe, "legacy-desired")
    assert model.prompts and not model.carried("GSIXCLEANRES")


def test_zz_reach(probe):  # TEMPORARY
    from learnloop.reader.reader_quick_check import SELECTION_STYLES
    out = {"checks": {}, "refs": {}, "presented": {}}
    for row in ("0.control", "1.paper", "2.exam", "3.held", "3.neighbor", "4.unmarked", "5.signal"):
        t = probe.base.targets[row]
        try:
            out["checks"][row] = [_check(probe, t, {"scope_kind": "inquiry", "inquiry_root_event_id": "evt_g6_root", "anchor_span_ids": "@span"}),
                                  _check(probe, t, {"scope_kind": "selection", "question_style": sorted(SELECTION_STYLES)[0], "anchor_span_ids": "@span"})]
        except BaseException as exc:
            out["checks"][row] = repr(exc)[:300]
    w = probe.base
    material = EM.exam_material(w.vault(), w.repository)
    for form in ("locator", "explicit_spans", "namespaced_span", "whole_extraction", "revision_only", "source_only", "neighbour_block"):
        out["refs"][form] = W if EM.source_ref_protected(material, _reference(form, w.targets["3.held"]), w.repository) else S
    for col in ("LP", "AP", "AD", "IP", "MC", "RF", "RT", "OT", "SE", "CO", "LC", "EX"):
        try:
            out["presented"][col] = ADAPTERS[col](probe, probe.base.targets["6.presented"])
        except BaseException as exc:
            out["presented"][col] = repr(exc)[:200]
    path = "/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/6b94db86-fdc3-456a-8767-851c8bf25992/scratchpad/g61/reach.json"
    with open(path, "w") as handle:
        json.dump(out, handle, indent=1)


def test_zz_faults(probe):  # TEMPORARY
    out = {}
    for column in DRIVEN:
        try:
            out[column] = list(_fault_answers(probe, column))
        except BaseException as exc:  # noqa: BLE001
            out[column] = f"ERR {type(exc).__name__}: {str(exc)[:200]}"
    path = "/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/6b94db86-fdc3-456a-8767-851c8bf25992/scratchpad/g61/faults.json"
    with open(path, "w") as handle:
        json.dump(out, handle, indent=1)
