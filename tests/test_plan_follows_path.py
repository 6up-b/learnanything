"""Reader workbench RW7b: the plan follows the reading path (spec_reader_workbench_v1 §10.2; G47).

* **What changes.** At RW7b's tag, with ``reading_paths.plan_uses_path`` and
  the Guide's paths on, DL1's reading block opens the next unfinished
  **core** or **prerequisite** section of the source's path instead of the
  next section in the predecessor's order; enrichment, already shown,
  assumed and a "skip it" are never planned; "read it anyway" makes a section
  core for planning. The labels are the Guide's, honest labels re-applied
  when the plan is built. A source with no path keeps the predecessor's
  order; a withheld (exam) reading plans nothing through its path.
* **Receipts.** ``split_json["reading_path"]`` records the section the
  predecessor's order would have chosen, who chose and each path consulted.
* **G47 parity.** Off (the switch, the Guide's paths, or below the tag) every
  plan build is the predecessor's exactly, on path vaults and on fixture
  copies; a rebuild shows zero projection deltas and never reads a path.
* **AD compose.** The path is read once, when the plan is built; serving,
  AD's slot facts and the reading step read the plan's record.

Fakes only (``PathJudgeFake``); no network, no model in the plan.
"""
from __future__ import annotations

import json
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    READING_PATH_PLAN_VERSIONS,
    SUCCESSOR_CHAIN,
    WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION,
)
from learnloop.daily_plan import engine as E
from learnloop.daily_plan.types import ReadingTarget
from learnloop.db.connection import connect
from learnloop.source_retrieval import reading_paths as RP
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml, set_algorithm_version
from tests.owner_vaults import owner_vault, working_vault_params
from tests.reading_path_fixtures import (
    EXT,
    FixedClock,
    PathJudgeFake,
    call,
    context,
)
from tests.plan_follows_path_helpers import (
    GUIDE_OFF,
    HEAD,
    OFF,
    TAG,
    _fixture_copy,
    _plan_state,
    _split,
    _vault,
)

#: The predecessor as the upgrade names it (one constant; the landing renumbers).
PREDECESSOR = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1]
#: DL1's exact selection: book order, no exam filter (identity review F6).
DL1_ORDER = "[plan]\nreading_from_furthest = false\n[goals]\nheld_out_selection = false\n"


def _step(paths, repository, *, from_furthest=True, exam=None):
    """RW7b's reading step and receipt, as the plan's build computes them."""

    env = E.PlanEnv(load_vault(paths.root), repository)
    return E._reading_on_path(env, extraction_ids=None, from_furthest=from_furthest, exam=exam)


def _complete(repository, *sections):
    for section in sections:
        repository.upsert_reader_section_progress(extraction_id=EXT, section_id=section, completed=True)


# -- the successor's vocabulary and switch ------------------------------------------------------------


def test_the_successor_is_one_constant_after_rw2d():

    # LP-min (a)'s claim fixes (mvp-0.33) and rebuild equivalence (mvp-0.34) and Reader CA2 (mvp-0.35) and the kept replaced claims (mvp-0.36) and mobile PR-4 (mvp-0.37, the latest) landed after it and keep it.
    assert TAG == SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(PREDECESSOR) + 1]
    assert LATEST_ALGORITHM_VERSION == SUCCESSOR_CHAIN[-1] == "mvp-0.59"
    assert PREDECESSOR == WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION
    assert READING_PATH_PLAN_VERSIONS == frozenset({TAG, "mvp-0.33", "mvp-0.34", "mvp-0.35", "mvp-0.36", "mvp-0.37", "mvp-0.38", "mvp-0.39", "mvp-0.40", "mvp-0.41", "mvp-0.42", "mvp-0.43", "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", LATEST_ALGORITHM_VERSION})


def test_the_switch_is_on_by_default_classified_and_acts_only_at_the_tag_with_the_guide_on(tmp_path):
    from learnloop.config.schema import ReadingPathsConfig
    from learnloop.params import parameter_registry as registry
    from tests.helpers import create_daily_plan_vault

    assert ReadingPathsConfig().plan_uses_path is True
    assert registry.classify_config_path("reading_paths.plan_uses_path") is not None
    paths = create_daily_plan_vault(tmp_path / "v", version=TAG)
    assert E.reading_path_plan_active(load_vault(paths.root))
    set_algorithm_version(paths, PREDECESSOR)
    assert not E.reading_path_plan_active(load_vault(paths.root))
    set_algorithm_version(paths, TAG)
    append_config_toml(paths.root, GUIDE_OFF)
    assert not E.reading_path_plan_active(load_vault(paths.root))
    other = create_daily_plan_vault(tmp_path / "w", version=TAG, plan_toml=None)
    append_config_toml(other.root, OFF)
    assert not E.reading_path_plan_active(load_vault(other.root))
    plan_off = create_daily_plan_vault(tmp_path / "x", version=TAG)
    append_config_toml(plan_off.root, "[plan]\nenabled = false\n")
    assert not E.reading_path_plan_active(load_vault(plan_off.root))


# -- what changes (fail-first: the predecessor opens 1 Eigenvalues) ------------------------------------


def test_the_reading_block_opens_the_next_core_or_prerequisite_section_and_the_receipt_has_the_old_one(
        tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch,
                                  labels={"sec_eigen": "enrichment", "sec_spectral": "prerequisite"})
    plan = call(context(paths.root), "get_daily_plan", {})
    split = _split(repository)
    assert (split["reading"]["section_id"], split["reading"]["path_label"]) == ("sec_spectral", "prerequisite")
    receipt = split["reading_path"]
    assert receipt["predecessor"]["section_id"] == "sec_eigen"  # the predecessor's order: book order here
    assert (receipt["chosen_by"], receipt["label"], receipt["same_as_predecessor"]) == ("path", "prerequisite", False)
    assert receipt["version"] == E.READING_PATH_RECEIPT_VERSION
    assert [(p["extraction_id"], p["status"], p["depth"], p["fresh"]) for p in receipt["paths"]] == [
        (EXT, "path", "learn_to_use_it", True)]
    # The block names the section the path chose and why (UX §4.11).
    projected = [row for row in plan["plan"]["projected"] if row.get("readingTitle")]
    assert projected and projected[0]["readingTitle"] == "2 The spectral theorem"
    assert projected[0]["why"].endswith("prerequisite on your reading path")


def test_core_follows_book_order_and_finished_sections_are_passed(tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels={"sec_spectral": "enrichment"})
    reading, receipt = _step(paths, repository)
    assert (reading.section_id, reading.path_label, receipt["same_as_predecessor"]) == ("sec_eigen", "core", True)
    _complete(repository, "sec_eigen")
    reading, receipt = _step(paths, repository)
    assert (reading.section_id, receipt["predecessor"]["section_id"]) == ("sec_diag", "sec_spectral")


def test_enrichment_already_shown_and_assumed_are_never_planned_and_nothing_left_offers_no_reading(
        tmp_path, monkeypatch):
    from tests.reading_paths_helpers import _assume, _demonstrate

    _demonstrate(monkeypatch, "lo_eigen_basics")
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels={
        "sec_eigen": "already_shown", "sec_spectral": "assumed", "sec_diag": "core", "sec_history": "enrichment"},
        before_judge=lambda repository: _assume(repository, "lo_spectral"))
    labels = RP.plan_path(load_vault(paths.root), repository, EXT).labels
    assert labels == {"sec_eigen": "already_shown", "sec_spectral": "assumed", "sec_diag": "core",
                      "sec_history": "enrichment"}
    reading, receipt = _step(paths, repository)
    assert (reading.section_id, receipt["predecessor"]["section_id"]) == ("sec_diag", "sec_eigen")
    _complete(repository, "sec_diag")
    reading, receipt = _step(paths, repository)
    # Only enrichment, already shown and assumed are left: the path plans no reading;
    # the predecessor would have opened the first unfinished section.
    assert reading is None and receipt["predecessor"]["section_id"] == "sec_history"
    assert receipt["chosen_by"] is None and receipt["same_as_predecessor"] is False


def test_read_it_anyway_makes_a_section_core_and_skip_it_leaves_one_out(tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels={"sec_eigen": "enrichment"},
                                  overrides=[("sec_eigen", "read_anyway"), ("sec_spectral", "skip")])
    reading, _receipt = _step(paths, repository)
    assert (reading.section_id, reading.path_label) == ("sec_eigen", "core")
    _complete(repository, "sec_eigen")
    reading, receipt = _step(paths, repository)
    assert reading.section_id == "sec_diag" and receipt["predecessor"]["section_id"] == "sec_spectral"
    # Skip it marks nothing known: the LO behind the skipped section is as it was.
    statuses = RP.lo_statuses(load_vault(paths.root), repository, ["lo_spectral"])
    assert statuses["lo_spectral"].status == "new"


def test_a_stored_already_shown_that_no_longer_holds_leaves_the_stale_path_to_the_order(tmp_path, monkeypatch):
    """Codex review F2: the evidence behind "already shown" no longer holds,
    so the learner state (and the path's key) moved: the stored judgment is
    stale and the plan keeps the predecessor's order there (recorded), which
    opens the section; it never re-judges."""

    from tests.reading_paths_helpers import _demonstrate

    with monkeypatch.context() as patched:
        _demonstrate(patched, "lo_eigen_basics")
        paths, repository, _ = _vault(tmp_path, monkeypatch, labels={"sec_eigen": "already_shown"})
        assert not RP.plan_path(load_vault(paths.root), repository, EXT).plannable("sec_eigen")
    path = RP.plan_path(load_vault(paths.root), repository, EXT)
    assert (path.status, path.fresh, path.follows) == ("stale", False, False)
    reading, receipt = _step(paths, repository)
    assert (reading.section_id, reading.path_label) == ("sec_eigen", None)
    assert (receipt["chosen_by"], receipt["paths"][0]["status"], receipt["paths"][0]["fresh"]) == (
        "order", "stale", False)


def test_a_source_without_a_depth_or_a_judged_path_keeps_the_predecessors_order(tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, depth=None)
    statuses = []
    real = RP.plan_path
    monkeypatch.setattr(RP, "plan_path", lambda *a, **k: statuses.append(real(*a, **k).status) or real(*a, **k))
    reading, receipt = _step(paths, repository)
    # No path in play: the predecessor's step and no receipt (the plan is stored as the predecessor's).
    assert (reading.section_id, reading.path_label, receipt, statuses) == ("sec_eigen", None, None, ["no_depth"])
    RP.set_depth(repository, "src_text", "fluency")  # a depth, never judged at it
    reading, receipt = _step(paths, repository)
    assert (reading.section_id, receipt, statuses[-1]) == ("sec_eigen", None, "not_judged")
    call(context(paths.root), "get_daily_plan", {})
    assert "reading_path" not in _split(repository) and _split(repository)["reading"]["section_id"] == "sec_eigen"


def test_a_path_that_cannot_be_read_leaves_the_reading_to_the_order(tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels={"sec_eigen": "enrichment"})

    def broken(*_args, **_kwargs):
        raise RuntimeError("no")

    monkeypatch.setattr(RP, "plan_path", broken)
    reading, receipt = _step(paths, repository)
    assert reading.section_id == "sec_eigen" and [p["status"] for p in receipt["paths"]] == ["unreadable"]


def test_the_path_never_opens_a_held_out_section_even_where_dl1s_exact_selection_would(tmp_path, monkeypatch):
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection

    paths, repository, spans = _vault(tmp_path, monkeypatch, config=DL1_ORDER, labels={"sec_eigen": "enrichment"})
    save_unit_selection(repository, EXT, list(spans), exam_use_modes={"sec_spectral": "held_out_evaluation"})
    # The held-out section leaves the sendable list (a new state): the Guide re-judges it.
    ctx = context(paths.root, reading_path_judge_client=PathJudgeFake({"sec_eigen": "enrichment"}),
                  reading_path_inline=True)
    assert call(ctx, "reader.reading_path", {"extractionId": EXT})["status"] == "ready"
    assert E.reading_step_rule(load_vault(paths.root)) == E.READING_RULE_DL1
    reading, receipt = _step(paths, repository, from_furthest=False)
    assert receipt["predecessor"]["section_id"] == "sec_eigen"
    assert reading.section_id == "sec_diag"


def test_an_exam_reading_plans_nothing_through_its_path(tmp_path, monkeypatch):
    from learnloop.content.sources import exam_material as EM

    paths, repository, _ = _vault(tmp_path, monkeypatch, config=DL1_ORDER)
    real = EM.exam_material

    class Whole:
        def __init__(self, inner):
            self.inner = inner

        def covers(self, extraction_id, span_id=None):
            return extraction_id == EXT or self.inner.covers(extraction_id, span_id)

        def withheld(self, keys):
            return frozenset(tuple(key) for key in keys)

    monkeypatch.setattr(EM, "exam_material", lambda vault, repo: Whole(real(vault, repo)))
    path = RP.plan_path(load_vault(paths.root), repository, EXT)
    assert path.status == "withheld" and path.follows and not path.plannable("sec_eigen")
    reading, receipt = _step(paths, repository, from_furthest=False)
    assert reading is None and receipt["predecessor"]["section_id"] == "sec_eigen"


def test_the_why_names_the_path_and_stays_plain():
    from learnloop.daily_plan.staged_frame import reason_code
    from learnloop.router import why

    assert reason_code("new", [], reading=True) == "reading"
    assert reason_code("new", [], reading=True, path_label="core") == "reading_path_core"
    assert reason_code("new", [], reading=True, path_label="prerequisite") == "reading_path_prerequisite"
    for code in ("reading_path_core", "reading_path_prerequisite"):
        text = why.sentence(code, section="5.4 Mixtures")
        assert text.startswith("Next on your reading path: 5.4 Mixtures") and not why.jargon_in(text)


def test_a_reading_target_is_stored_as_the_predecessors_unless_the_path_chose_it():
    plain = ReadingTarget(source_id="s", extraction_id="e", section_id="x", section_title="X", words_left=3)
    assert plain.as_dict() == {"source_id": "s", "extraction_id": "e", "section_id": "x", "section_title": "X",
                               "words_left": 3, "partial": False}
    chosen = ReadingTarget(source_id="s", extraction_id="e", section_id="x", section_title="X", words_left=3,
                           path_label="core")
    assert chosen.as_dict()["path_label"] == "core"


# -- G47: off is the predecessor, byte for byte ---------------------------------------------------------


_LABELS = {"sec_eigen": "enrichment", "sec_spectral": "prerequisite"}


@pytest.mark.parametrize("variant", ["switch_off", "guide_off"])
def test_g47_off_every_plan_build_is_the_predecessors(tmp_path, monkeypatch, variant):
    base, _, _ = _vault(tmp_path, monkeypatch, "base", version=PREDECESSOR, labels=_LABELS)
    off, _, _ = _vault(tmp_path, monkeypatch, "off", version=TAG, labels=_LABELS)
    append_config_toml(off.root, OFF if variant == "switch_off" else GUIDE_OFF)
    baseline = _plan_state(base)
    assert baseline["stored"]["daily_plans"] and "reading_path" not in json.dumps(baseline)
    assert _plan_state(off) == baseline
    # The same vault with the successor on is not (the test can see the change).
    on, _, _ = _vault(tmp_path, monkeypatch, "on", version=TAG, labels=_LABELS)
    assert _plan_state(on) != baseline


def test_g47_a_rebuild_shows_zero_projection_deltas_and_never_reads_a_path(tmp_path, monkeypatch):
    from learnloop.db.table_roles import TableRole, tables_for_role
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths, repository, _ = _vault(tmp_path, monkeypatch, labels=_LABELS)
    call(context(paths.root), "get_daily_plan", {})
    reads = []
    real = RP.plan_path
    monkeypatch.setattr(RP, "plan_path", lambda *a, **k: reads.append(a) or real(*a, **k))
    derived = sorted(tables_for_role(TableRole.DERIVED))

    def snapshot():
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            return {table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
                    for table in derived}

    clock = FixedClock(monkeypatch)
    from learnloop.clock import FrozenClock

    frozen = FrozenClock(clock.moment)
    rebuild_all_derived_state(load_vault(paths.root), repository, clock=frozen)
    switched_on = snapshot()
    append_config_toml(paths.root, OFF)
    rebuild_all_derived_state(load_vault(paths.root), repository, clock=frozen)
    assert snapshot() == switched_on and reads == []


# -- AD composes: the path is read once, at the build --------------------------------------------------


def test_the_path_is_read_only_when_the_plan_is_built_and_ad_slot_facts_read_the_record(tmp_path, monkeypatch):
    """AD reads only SlotFacts, and the plan computes them from its record
    (``_context`` reads ``split["reading"]``), so the admitted pool AD draws
    from is the plan's whatever chose the reading. Serving the plan (AD's
    slot phases included) and opening it again never read a path."""

    from learnloop.daily_plan import slot_facts

    paths, repository, _ = _vault(tmp_path, monkeypatch, labels=_LABELS)
    ctx = context(paths.root)
    call(ctx, "get_daily_plan", {})
    reads, facts = [], []
    real_path, real_slot = RP.plan_path, slot_facts.for_slot
    monkeypatch.setattr(RP, "plan_path", lambda *a, **k: reads.append(a) or real_path(*a, **k))

    def for_slot(env, record, *args, **kwargs):
        before = len(reads)
        found = real_slot(env, record, *args, **kwargs)
        facts.append((record.split.get("reading", {}).get("section_id"), len(reads) - before))
        return found

    monkeypatch.setattr(slot_facts, "for_slot", for_slot)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    for _ in range(2):
        step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
        assert step["kind"] == "item"
    call(ctx, "get_daily_plan", {})
    ctx.map_builds.close()
    assert facts, "AD's slot phase never ran: the compose check would be vacuous"
    assert reads == []
    assert all(read == 0 for _section, read in facts)
    assert all(section == "sec_spectral" for section, _read in facts)
    assert _split(repository)["reading"]["section_id"] == "sec_spectral"


# -- G47 on fixture copies -----------------------------------------------------------------------------

FROZEN = datetime(2026, 10, 12, 9, 30, tzinfo=UTC)


def _fixture_parity(tmp_path, monkeypatch, source: Path) -> None:
    import learnloop.clock as clock_module

    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    baseline = _plan_state(_fixture_copy(tmp_path, source, "base", version=PREDECESSOR))
    assert _plan_state(_fixture_copy(tmp_path, source, "off", version=TAG, toml=OFF)) == baseline
    assert _plan_state(_fixture_copy(tmp_path, source, "guide_off", version=TAG, toml=GUIDE_OFF)) == baseline
    # On, with no reading path judged on the copy: the predecessor's plan too
    # (the successor changes only a reading block a path chose).
    assert _plan_state(_fixture_copy(tmp_path, source, "on", version=TAG)) == baseline


def test_g47_off_is_the_predecessor_on_the_head_fixture_copy(tmp_path, monkeypatch):
    _fixture_parity(tmp_path, monkeypatch, HEAD)


@pytest.mark.parametrize("fixture", working_vault_params())
def test_g47_off_is_the_predecessor_on_working_fixture_copies(tmp_path, monkeypatch, fixture):
    if not (owner_vault(fixture) / "state.sqlite").exists():
        pytest.skip(f"{fixture} fixture absent")
    _fixture_parity(tmp_path, monkeypatch, owner_vault(fixture))


# -- the upgrade ---------------------------------------------------------------------------------------
