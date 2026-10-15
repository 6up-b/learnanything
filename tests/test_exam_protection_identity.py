"""Exam protection bound to the reading each mark was made on
(docs/reviews/exam-protection-identity.md).

Every exam or held-out protection mark names the extraction (reading) it was
made on, and is resolved there and nowhere else:

* a source-set exam scope: ``scope_extraction_id`` (and ``scope_revision_id``)
  on its member in ``source_sets.yaml``;
* a held-out mark in a unit selection, and the owner's "Mark exam material on
  this reading": ``marks_made_on`` in the selection's paper metadata;
* a held-out inventory signal: the append-only ``source_held_out_signal_marks``
  ledger, written only by a model run on that reading (a reused inventory
  writes none).

A legacy mark that names no reading is ambiguous: its book is protected and
every reading of it not marked exactly is withheld whole, and the card and
doctor say so. The final verify's reproductions (F2, F12-F15) are each written
to fail on 808dc9c01.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace as NS

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.content.sources import exam_material as EM
from learnloop.db.repositories import Repository
from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
from learnloop.ingest.ir import IR_SCHEMA_VERSION

from tests.test_reread_safety import (  # noqa: F401 -- fixtures are used by name
    _EXAM_Q,
    _Q1,
    _Q2,
    _clock,
    _exam_reading_a,
    _exam_reading_b,
    _exam_sets,
    _held_out_inventory,
    _ir,
    _paper_a,
    _paper_b_with_duplicates,
    _persist,
    _second_revision,
    _unprotected_copies,
    exam_book,
    paper_book,
)


def _exact_sets(extraction_id: str, *, default_role: str = "primary_textbook", scope=(("u1", "exam"),),
                revision_id: str = "rev_x", scope_revision_id: str | None = "rev_x"):
    """A source set whose exam scope names the reading it was made on."""

    from learnloop.vault.models import SourceSet, SourceSetMember, SourceSetScope

    return [SourceSet(id="set_x", subject_id="linear_algebra", title="Exam prep", members=[SourceSetMember(
        source_id="src_x", revision_id=revision_id, default_role=default_role,
        scope_extraction_id=extraction_id, scope_revision_id=scope_revision_id,
        scope=[SourceSetScope(unit_id=unit, role_override=role) for unit, role in scope])])]


def _owner_marks(repo: Repository, extraction_id: str, unit_ids, *, selected=None) -> None:
    """The owner holds units out on a reading (the study map's save with exam use modes)."""

    from learnloop.content.synthesis.source_unit_selection import save_unit_selection

    ir = repo.load_document_ir(extraction_id)
    save_unit_selection(repo, extraction_id, list(selected or [unit.unit_id for unit in ir.units]),
                        exam_use_modes={unit_id: "held_out_evaluation" for unit_id in unit_ids})


def _legacy_marks(repo: Repository, extraction_id: str, unit_ids, *, revision_id: str = "rev_x") -> None:
    """A held-out mark written before marks named their reading (no ``marks_made_on``)."""

    ir = repo.load_document_ir(extraction_id)
    repo.upsert_unit_selection(extraction_id=extraction_id, source_id="src_x", revision_id=revision_id,
                               selected_unit_ids=[unit.unit_id for unit in ir.units],
                               exam_use_modes={unit_id: "held_out_evaluation" for unit_id in unit_ids})


def _source_action(vault, repo, **params):
    from learnloop_sidecar.handlers.first_run import SourceActionInput, source_action

    ctx = NS(require_vault=lambda: (vault, repo))
    return source_action(ctx, SourceActionInput.model_validate({"source_id": "src_x", **params}))


# --- F2: inventory reuse never moves or erases protection --------------------------------


def _fresh_signal(repo: Repository, *, extraction_id: str, unit_id: str, span_ids, semantic_hash: str,
                  role: str = "exam") -> None:
    """An inventory a model run made on ``extraction_id`` with a held-out signal."""

    from learnloop.content.synthesis.ai_contracts import (
        SOURCE_UNIT_INVENTORY_PROMPT_VERSION,
        InventoryAssessmentSignal,
        SourceUnitInventory,
    )

    inventory = SourceUnitInventory(unit_id=unit_id, semantic_hash=semantic_hash, assessment_signals=[
        InventoryAssessmentSignal(held_out=True, task_family="proof", span_ids=list(span_ids))])
    repo.insert_unit_inventory(
        id=f"inv_{extraction_id}_{unit_id}", source_revision_id="rev_x", extraction_id=extraction_id,
        unit_id=unit_id, unit_semantic_hash=semantic_hash, inventory_profile="assessment",
        inventory_schema_version=1, prompt_version=SOURCE_UNIT_INVENTORY_PROMPT_VERSION, provider="fake",
        model="fake", inventory=inventory.model_dump(), made_as_role=role)


def test_f2_a_reused_inventory_never_releases_duplicate_or_fragment_copies(paper_book):
    """Final verify F2: A's inventory holds out x1 (both questions); B has an
    exact copy y1 and fragments y3 (Q1) and y4 (Q2). A cache hit re-anchored
    the signal onto y1 and bound the inventory to B, which then counted as
    marked: y3 and y4 were released and the Reader refused neither. Now
    reuse carries no marking authority: B stays withheld whole."""

    from learnloop.content.synthesis.source_unit_inventory import prepare_unit_inventory

    repo, clock = paper_book["repo"], paper_book["clock"]
    _paper_a(repo, clock)
    a = repo.load_document_ir("extPA")
    _fresh_signal(repo, extraction_id="extPA", unit_id="u1", span_ids=["x1"], semantic_hash=a.units[0].semantic_hash)
    _paper_b_with_duplicates(repo, clock)
    b = repo.load_document_ir("extPB")
    b.units[0].semantic_hash = a.units[0].semantic_hash  # the unchanged Exam unit
    repo.persist_document_ir("extPB", b)
    sets = _exam_sets(default_role="exam", scope=())
    before = EM.held_out_material(sets, repo)
    assert all(before.covers("extPB", span) for span in ("y1", "y3", "y4"))

    hit = prepare_unit_inventory(repo, "extPB", "u1", role="exam", profile="assessment", provider="fake",
                                 model="fake")
    assert hit.cache_hit
    after = EM.held_out_material(sets, repo)
    assert _unprotected_copies(repo, after, _Q1, _Q2) == []
    assert EM.held_out_among(after, "extPB", ["y3", "y4"]) == ["y3", "y4"], "the Reader refuses the fragments"
    assert after.covers("extPA", "x1"), "the origin keeps its signal"
    assert EM.source_marks(sets, repo)["src_x"].marked == ("extPA",), "marked where the model read it"


@pytest.mark.parametrize("protection", ["exact_scope", "exam_member"])
def test_f2_reuse_never_erases_the_origins_signal(exam_book, protection):
    """Final verify F2 (second part): with A's own held-out signal, a cache
    hit for B rebound the cache row to B and A's signal left A's Reader
    refusal partition. The origin keeps its signal; B stays withheld whole."""

    from learnloop.content.synthesis.source_unit_inventory import prepare_unit_inventory

    repo, clock = exam_book["repo"], exam_book["clock"]
    a = repo.load_document_ir("extXA")
    _fresh_signal(repo, extraction_id="extXA", unit_id="u1", span_ids=["x1"], semantic_hash=a.units[0].semantic_hash)
    sets = _exact_sets("extXA") if protection == "exact_scope" else _exam_sets(default_role="exam", scope=())
    b = a.model_copy(deep=True)
    b.extractor = "reread"
    for block in b.blocks:
        block.span_id = block.span_id.replace("x", "y")
    for unit in b.units:
        unit.span_ids = [span.replace("x", "y") for span in unit.span_ids]
    _persist(repo, b, revision_id="rev_x", extraction_id="extXB", clock=clock)
    assert EM.held_out_material(sets, repo).covers("extXA", "x1")

    hit = prepare_unit_inventory(repo, "extXB", "u1", role="exam", profile="assessment", provider="fake", model="fake")
    assert hit.cache_hit
    after = EM.held_out_material(sets, repo)
    assert after.covers("extXA", "x1"), "A's own signal survives the reuse"
    assert EM.held_out_among(after, "extXA", ["x1"]) == ["x1"]
    assert "extXB" in after.extractions, "the reused inventory marks nothing on B"
    assert _unprotected_copies(repo, after, _EXAM_Q) == []


# --- F12: a scope names its reading; a legacy scope fails closed -------------------------


def test_f12_a_legacy_scope_over_reversed_unit_ids_withholds_every_reading(exam_book):
    """Final verify F12: A has u1=Exam, u2=Theory; B reverses the ids. A scope
    hand-edited to B's u2 (no reading named) was read on A: A's Theory was
    protected and A's question released, and find_sources' post-attempt
    library scope reopened it for an item citing it. A legacy scope is
    ambiguous now: every reading of the book is withheld whole."""

    from learnloop.source_retrieval.corpus import exam_withheld, teaching_exclusions
    from learnloop.source_retrieval.find_sources import scope_for
    from learnloop.vault.models import SourceRef

    repo, clock = exam_book["repo"], exam_book["clock"]
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    sets = _exam_sets(default_role="primary_textbook", scope=(("u2", "exam"),), reading=None)
    material = EM.exam_material(sets, repo)
    assert _unprotected_copies(repo, material.material, _EXAM_Q) == []
    assert material.covers("extXA", "x1")
    exclusions = teaching_exclusions(NS(source_sets=sets), repo)
    assert "extXA" in exclusions.extractions or ("extXA", "x1") in exclusions.spans
    assert exam_withheld(NS(source_sets=sets), repo, [("extXA", "x1")]) == {("extXA", "x1")}
    ref = SourceRef(ref_type="canonical_source", ref_id="src_x", source_id="src_x", revision_id="rev_x",
                    extraction_id="extXA", span_ids=["x1"])
    item = NS(id="itemA", learning_object_id="lo1", provenance=NS(source_refs=[ref]))
    scope = scope_for(NS(source_sets=sets), repo, policy="post_attempt", scope="library", learning_object_ids=[],
                      item=item)
    assert "extXA" not in scope.extractions or ("extXA", "x1") in scope.excluded
    marks = EM.source_marks(sets, repo)["src_x"]
    assert marks.marked == () and set(marks.unmarked) == {"extXA", "extXB"}


def _interrupted_older_reading(repo: Repository, clock) -> None:
    """``extOld`` starts first and is interrupted; ``extFirstCompleted`` (A)
    completes; then ``extOld`` (B's text) completes, older by ``created_at``."""

    old = _exam_reading_b()
    request = extraction_request_hash(revision_id="rev_x", extractor=old.extractor,
                                      extractor_version=old.extractor_version, page_selection=None,
                                      ir_schema_version=IR_SCHEMA_VERSION)
    repo.insert_extraction_run(id="extOld", revision_id="rev_x", extractor=old.extractor,
                               extractor_version=old.extractor_version, extraction_request_hash=request,
                               ir_schema_version=IR_SCHEMA_VERSION, status="running", clock=clock)
    clock.advance()
    _persist(repo, _exam_reading_a(), revision_id="rev_x", extraction_id="extFirstCompleted", clock=clock)
    clock.advance()
    repo.persist_document_ir("extOld", old)
    repo.complete_extraction_run("extOld", extraction_result_hash=extraction_result_hash(request, old), clock=clock)


@pytest.fixture
def blank_book(tmp_path):
    from tests.helpers import create_basic_vault
    from tests.test_source_inventory import _register_revision

    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src_x", revision_id="rev_x")
    repo.set_source_current_revision("src_x", "rev_x")
    return {"repo": repo, "clock": _clock(), "root": paths.root}


def test_f12_a_scope_stays_on_its_reading_when_an_older_one_completes_later(blank_book):
    """Final verify F12 (second part): the scope was read on the first
    completed reading by ``created_at``; an interrupted older reading that
    completed later became "first" and took the scope (its Theory protected,
    its question released). A scope bound to its reading never moves."""

    repo, clock = blank_book["repo"], blank_book["clock"]
    _interrupted_older_reading(repo, clock)
    sets = _exact_sets("extFirstCompleted")
    marks = EM.source_marks(sets, repo)["src_x"]
    assert marks.marked == ("extFirstCompleted",) and marks.unmarked == ("extOld",)
    material = EM.exam_material(sets, repo)
    assert material.covers("extFirstCompleted", "x1") and not material.covers("extFirstCompleted", "x3")
    assert _unprotected_copies(repo, material.material, _EXAM_Q) == []


def test_f12_a_legacy_scope_never_follows_creation_order(blank_book):
    """The same reorder under a legacy scope (no reading named): every reading
    is withheld whole, so the retried reading's question is protected."""

    repo, clock = blank_book["repo"], blank_book["clock"]
    _interrupted_older_reading(repo, clock)
    sets = _exam_sets(default_role="primary_textbook", reading=None)
    material = EM.exam_material(sets, repo)
    assert material.covers("extOld", "y3") and material.covers("extFirstCompleted", "x1")
    assert _unprotected_copies(repo, material.material, _EXAM_Q) == []


def test_f12_an_exact_scope_protects_the_units_of_the_reading_it_names(exam_book):
    """A scope made on B (``u2`` is B's Exam) protects B's question exactly and
    leaves B's Theory usable; A, with no mark of its own, is withheld whole."""

    repo, clock = exam_book["repo"], exam_book["clock"]
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    sets = _exact_sets("extXB", scope=(("u2", "exam"),))
    material = EM.exam_material(sets, repo)
    assert material.covers("extXB", "y3") and not material.covers("extXB", "y1")
    assert "extXA" in material.held_out.extractions
    assert _unprotected_copies(repo, material.material, _EXAM_Q) == []


@pytest.mark.parametrize("named", ["extNowhere", "other_source", "wrong_revision"])
def test_a_scope_naming_a_reading_it_cannot_be_on_fails_closed(exam_book, named):
    """A scope naming a reading that does not exist, belongs to another book or
    to another revision than it says, is as ambiguous as a legacy one."""

    from tests.test_source_inventory import _register_revision

    repo, clock = exam_book["repo"], exam_book["clock"]
    extraction, scope_revision = "extNowhere", "rev_x"
    if named == "other_source":
        _register_revision(repo, source_id="src_other", revision_id="rev_other")
        _persist(repo, _exam_reading_a(), revision_id="rev_other", extraction_id="extOther", clock=clock)
        extraction = "extOther"
    elif named == "wrong_revision":
        extraction, scope_revision = "extXA", "rev_elsewhere"
    sets = _exact_sets(extraction, scope_revision_id=scope_revision)
    material = EM.exam_material(sets, repo)
    assert "extXA" in material.held_out.extractions
    assert EM.source_marks(sets, repo)["src_x"].ambiguous


# --- F13: the owner's confirmation is bound to the reading and the proposal ---------------


def test_f13_a_confirmation_made_for_another_reading_returns_a_fresh_one(exam_book):
    """Final verify F13: the card proposed B's u2; reading C completed before
    the owner confirmed; ``confirmed`` marked C with an empty selection and
    released it whole. A confirmation is bound to the reading and the
    proposal: anything else returns a fresh confirmation and writes nothing."""

    repo, clock = exam_book["repo"], exam_book["clock"]
    _owner_marks(repo, "extXA", ["u1"])
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    vault = NS(source_sets=[])
    first = _source_action(vault, repo, action="mark_exam_material")
    shown = first["confirmation"]
    assert first["needsConfirmation"] and shown["extractionId"] == "extXB" and shown["heldOutUnitIds"] == ["u2"]
    assert repo.get_unit_selection("extXB") is None
    clock.advance()
    c = _ir({"c1": ("Text", 9, ["Exercises"], "Prove: a self adjoint operator cannot have a nonreal eigenvalue.")},
            [("u9", "Exercises", "sha256:c", ["c1"])], extractor="third")
    _persist(repo, c, revision_id="rev_x", extraction_id="extXC", clock=clock)

    for binding in ({}, {"confirmed_extraction_id": "extXB",
                         "confirmed_proposal_hash": shown.get("proposalHash", "")}):
        again = _source_action(vault, repo, action="mark_exam_material", confirmed=True, **binding)
        assert again.get("needsConfirmation") is True and "marked" not in again
        assert again["confirmation"]["extractionId"] == "extXC"
        assert repo.get_unit_selection("extXC") is None and repo.get_unit_selection("extXB") is None
        held = EM.held_out_material(vault, repo)
        assert held.covers("extXC", "c1") and "extXB" in held.extractions


def test_f13_a_changed_proposal_returns_a_fresh_confirmation(exam_book):
    """The owner holds out more on A after the card showed B's proposal: the
    old confirmation no longer matches, so nothing is written."""

    from learnloop.content.pipeline import exam_marking

    repo, clock = exam_book["repo"], exam_book["clock"]
    _owner_marks(repo, "extXA", ["u1"])
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    vault = NS(source_sets=[])
    shown = exam_marking.mark_plan(vault, repo, "src_x")
    _owner_marks(repo, "extXA", ["u1", "u2"])
    with pytest.raises(exam_marking.StaleMarkConfirmation) as stale:
        exam_marking.mark_exam_material(vault, repo, "src_x", extraction_id=shown["extraction_id"],
                                        proposal_hash=shown["proposal_hash"], clock=clock)
    assert stale.value.plan["held_out_unit_ids"] == ["u1", "u2"]
    assert repo.get_unit_selection("extXB") is None


def test_f13_the_confirmed_proposal_is_applied_exactly_and_bound_to_its_reading(exam_book):
    from learnloop.content.pipeline import exam_marking

    repo, clock = exam_book["repo"], exam_book["clock"]
    _owner_marks(repo, "extXA", ["u1"])
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    vault = NS(source_sets=[])
    shown = _source_action(vault, repo, action="mark_exam_material")["confirmation"]
    done = _source_action(vault, repo, action="mark_exam_material", confirmed=True,
                          confirmed_extraction_id=shown["extractionId"],
                          confirmed_proposal_hash=shown["proposalHash"])
    assert done["marked"]["extractionId"] == "extXB" and done["marked"]["heldOutUnitIds"] == ["u2"]
    selection = repo.get_unit_selection("extXB")
    assert selection["exam_use_modes"] == {"u2": "held_out_evaluation"}
    assert selection["exam_paper_metadata"][EM.MARKS_MADE_ON_KEY] == {"extraction_id": "extXB", "revision_id": "rev_x"}
    material = EM.exam_material(vault, repo)
    assert material.is_held_out("extXB", "y3") and not material.covers("extXB", "y1")
    assert exam_marking.held_back_reading(vault, repo, "src_x") is None
    with pytest.raises(exam_marking.StaleMarkConfirmation):  # nothing left to confirm: never a second write
        exam_marking.mark_exam_material(vault, repo, "src_x", extraction_id="extXB",
                                        proposal_hash=shown["proposalHash"], clock=clock)


# --- F14: protection is found across every revision, whatever the membership ------------


def test_f14_a_refresh_never_drops_signal_only_protection(exam_book):
    """Final verify F14: an exam member pinned R1, whose inventory holds out
    A's question; R2's reading B is unmarked; the refresh advanced the
    member and signal discovery read only R2's inventories, so the leakage
    gate, the Reader's refusal on R2's question and the held-out partition
    all came back empty. Signals are found on every revision now."""

    from learnloop.content.authoring.practice_leakage import build_held_out_inventory, check_leakage
    from learnloop.content.pipeline import revision_refresh as RR
    from learnloop.vault.models import SourceSet

    repo, clock = exam_book["repo"], exam_book["clock"]
    _held_out_inventory(repo, extraction_id="extXA", unit_id="u1", span_ids=["x1"])
    sets = _exam_sets(default_role="exam", scope=())
    _second_revision(repo)
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x2", extraction_id="extXB", clock=clock)
    vault = NS(source_sets=sets)
    assert check_leakage(_EXAM_Q, build_held_out_inventory(vault, repo))

    def capture(root, payload, **kwargs):
        vault.source_sets = [SourceSet.model_validate(payload)]

    original = RR.upsert_source_set
    RR.upsert_source_set = capture
    try:
        RR._advance_membership(Path("/nonexistent"), vault, "set_x", "src_x", "rev_x", "rev_x2", clock)
    finally:
        RR.upsert_source_set = original
    assert vault.source_sets[0].members[0].revision_id == "rev_x2"
    assert check_leakage(_EXAM_Q, build_held_out_inventory(vault, repo)), "the gate still knows the question"
    held = EM.held_out_material(vault, repo)
    assert EM.held_out_among(held, "extXB", ["y3"]) == ["y3"], "the Reader refuses R2's question"
    assert held.covers("extXA", "x1")
    assert _unprotected_copies(repo, held, _EXAM_Q) == []


def test_f14_a_signal_made_on_an_exam_unit_protects_after_its_member_leaves(exam_book):
    """Membership-independent: an inventory made as exam material keeps its
    book protected after the member leaves every set (its pin and role gone)."""

    repo, clock = exam_book["repo"], exam_book["clock"]
    a = repo.load_document_ir("extXA")
    _fresh_signal(repo, extraction_id="extXA", unit_id="u1", span_ids=["x1"], semantic_hash=a.units[0].semantic_hash)
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    held = EM.held_out_material([], repo)
    assert held.covers("extXA", "x1") and "extXB" in held.extractions
    assert _unprotected_copies(repo, held, _EXAM_Q) == []


# --- F15: settings order the reading step, never protection ------------------------------


@pytest.mark.parametrize("from_furthest", [True, False])
def test_f15_no_reading_order_offers_a_held_back_reading(exam_book, from_furthest):
    """Final verify F15: with ``plan.reading_from_furthest = false`` the plan
    offered B's Theory section on a reading held back whole."""

    from learnloop.daily_plan.reading import next_reading_target
    from learnloop.source_retrieval.corpus import exam_exclusions

    repo, clock = exam_book["repo"], exam_book["clock"]
    _owner_marks(repo, "extXA", ["u1"])
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    exam = exam_exclusions(NS(source_sets=[]), repo)
    assert next_reading_target(repo, extraction_ids=["extXB"], from_furthest=from_furthest, exam=exam) is None
    target = next_reading_target(repo, extraction_ids=["extXA"], from_furthest=from_furthest, exam=exam)
    assert target is not None and target.section_id == "u2", "A's Theory, never its held-out Exam"


@pytest.mark.parametrize("toml", ["", "[plan]\nreading_from_furthest = false\n"], ids=["u4", "dl1"])
def test_f15_the_plans_reading_step_never_offers_held_out_material_in_either_order(tmp_path, monkeypatch, toml):
    """The plan itself (``set_plan_minutes``): the book's Contents section is
    held out; DL1's order (the switch off) served it anyway."""

    from datetime import UTC, datetime

    import learnloop.clock as clock_module
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection
    from learnloop_sidecar.context import SidecarContext
    from tests.helpers import create_daily_plan_vault
    from tests.test_reread_safety import call
    from tests.test_ux_phase1_round2_review import _seed_book

    paths = create_daily_plan_vault(tmp_path / "vault", plan_toml=toml or None)
    extraction_id = _seed_book(paths)
    repo = Repository(paths.sqlite_path)
    ir = repo.load_document_ir(extraction_id)
    contents = next(unit.unit_id for unit in ir.units if "contents" in str(unit.label).lower())
    save_unit_selection(repo, extraction_id, [unit.unit_id for unit in ir.units],
                        exam_use_modes={contents: "held_out_evaluation"})
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: datetime(2026, 10, 12, 9, 0, tzinfo=UTC))
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    plan = call(ctx, "set_plan_minutes", {"minutes": 60})["plan"]
    steps = [row["readingTitle"] for row in plan["projected"] if row["readingTitle"]]
    assert steps and "contents" not in [str(step).lower() for step in steps]


# --- legacy marks fail closed, plainly, and the owner's marking makes one exact ----------


def test_a_legacy_held_out_mark_withholds_every_reading_until_marked_exactly(exam_book):
    """A held-out mark written before marks named their reading cannot be
    placed: every reading of the book is withheld whole (A's own included),
    the card and doctor say why in plain words, and the owner's marking makes
    the reading the Reader opens exact."""

    from learnloop.content.pipeline import exam_marking

    repo, clock = exam_book["repo"], exam_book["clock"]
    _legacy_marks(repo, "extXA", ["u1"])
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    vault = NS(source_sets=[])
    held = EM.held_out_material(vault, repo)
    assert {"extXA", "extXB"} <= held.extractions
    marks = EM.source_marks(vault, repo)["src_x"]
    assert marks.ambiguous == ("selection",) and marks.marked == ()
    assert exam_marking.held_back_reading(vault, repo, "src_x") == "extXB"
    assert exam_marking.held_back_details(vault, repo, "src_x") == exam_marking.AMBIGUOUS_DETAILS
    assert "which reading" in exam_marking.AMBIGUOUS_DETAILS

    shown = exam_marking.mark_plan(vault, repo, "src_x")
    assert shown["extraction_id"] == "extXB" and "u2" in shown["held_out_unit_ids"]
    exam_marking.mark_exam_material(vault, repo, "src_x", extraction_id=shown["extraction_id"],
                                    proposal_hash=shown["proposal_hash"], clock=clock)
    material = EM.exam_material(vault, repo)
    assert material.is_held_out("extXB", "y3") and not material.covers("extXB", "y1")
    assert "extXA" in material.held_out.extractions, "the legacy reading stays withheld until marked"
    assert _unprotected_copies(repo, material.material, _EXAM_Q) == []


def test_a_held_out_mark_copied_onto_another_reading_is_never_exact(exam_book):
    """Marks copied from A's selection onto B's (their ``marks_made_on`` still
    names A) are A's, not B's: B is withheld whole, never protected by
    positional unit ids."""

    repo, clock = exam_book["repo"], exam_book["clock"]
    _owner_marks(repo, "extXA", ["u1"])
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    copied = repo.get_unit_selection("extXA")
    repo.upsert_unit_selection(extraction_id="extXB", source_id="src_x", revision_id="rev_x",
                               selected_unit_ids=["u1", "u2"], exam_use_modes=copied["exam_use_modes"],
                               exam_paper_metadata=copied["exam_paper_metadata"])
    material = EM.exam_material([], repo)
    assert "extXB" in material.held_out.extractions
    assert material.is_held_out("extXA", "x1") and not material.covers("extXA", "x3"), "A exactly as marked"


def test_doctor_names_a_legacy_mark_plainly(exam_book):
    from learnloop.ops.doctor import run_doctor

    repo, clock, root = exam_book["repo"], exam_book["clock"], exam_book["root"]
    from learnloop.vault.writer import upsert_source_set

    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "title": "Exam prep", "members": [
        {"source_id": "src_x", "revision_id": "rev_x", "default_role": "primary_textbook",
         "scope": [{"unit_id": "u1", "role_override": "exam"}]}]})
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    issues = [issue for issue in run_doctor(root).issues if issue.code == "source:reading_held_back"]
    assert len(issues) == 1
    assert "which reading" in issues[0].message and issues[0].details["ambiguous"] == ["scope"]


# --- the scope's reading round-trips through every writer of source_sets.yaml -----------


def _yaml_member(root: Path, source_id: str = "src_x") -> dict:
    from learnloop.vault.yaml_io import read_yaml

    data = read_yaml(root / "sources" / "source_sets.yaml")
    return next(member for source_set in data["source_sets"] for member in source_set["members"]
                if member["source_id"] == source_id)


def test_the_scopes_reading_round_trips_through_the_writers(exam_book):
    from learnloop.content.pipeline import revision_refresh as RR
    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_source_set

    repo, root = exam_book["repo"], exam_book["root"]
    member = {"source_id": "src_x", "revision_id": "rev_x", "default_role": "primary_textbook",
              "scope_extraction_id": "extXA", "scope_revision_id": "rev_x",
              "scope": [{"unit_id": "u1", "role_override": "exam"}]}
    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "title": "Exam prep",
                             "members": [member]})
    assert _yaml_member(root)["scope_extraction_id"] == "extXA"
    loaded = load_vault(root).source_sets[0].members[0]
    assert (loaded.scope_extraction_id, loaded.scope_revision_id) == ("extXA", "rev_x")

    # A writer that re-sends the member without the field (an older desktop)
    # keeps it for the same scope; a changed scope names no reading.
    plain = {key: value for key, value in member.items() if not key.startswith("scope_")}
    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "members": [plain]})
    assert _yaml_member(root)["scope_extraction_id"] == "extXA"
    changed = {**plain, "scope": [{"unit_id": "u2", "role_override": "exam"}]}
    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "members": [changed]})
    assert _yaml_member(root).get("scope_extraction_id") is None
    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "members": [member]})

    # Revision refresh keeps it whether the member stays pinned (an exam scope) or not.
    _second_revision(repo)
    RR._advance_membership(root, load_vault(root), "set_x", "src_x", "rev_x", "rev_x2", None)
    assert _yaml_member(root)["scope_extraction_id"] == "extXA"
    textbook = {**member, "scope": [{"unit_id": "u1", "role_override": "problem_set"}]}
    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "members": [textbook]})
    RR._advance_membership(root, load_vault(root), "set_x", "src_x", "rev_x", "rev_x2", None)
    advanced = _yaml_member(root)
    assert advanced["revision_id"] == "rev_x2" and advanced["scope_extraction_id"] == "extXA"


def test_the_scopes_reading_round_trips_through_the_sidecar(exam_book):
    from learnloop_sidecar.handlers.ingest import (
        SourceSetRefInput,
        UpsertSourceSetInput,
        get_source_set,
        upsert_source_set_rpc,
    )
    from learnloop.vault.loader import load_vault

    root = exam_book["root"]
    state = {"vault": load_vault(root)}
    ctx = NS(require_vault=lambda: (state["vault"], exam_book["repo"]),
             reload=lambda maintenance=False: state.update(vault=load_vault(root)))
    params = UpsertSourceSetInput.model_validate({
        "id": "set_x", "subjectId": "linear-algebra", "title": "Exam prep", "members": [{
            "sourceId": "src_x", "revisionId": "rev_x", "defaultRole": "primary_textbook",
            "scopeExtractionId": "extXA", "scopeRevisionId": "rev_x",
            "scope": [{"unitId": "u1", "roleOverride": "exam"}]}]})
    upsert_source_set_rpc(ctx, params)
    shown = get_source_set(ctx, SourceSetRefInput(source_set_id="set_x"))["sourceSet"]["members"][0]
    assert shown["scopeExtractionId"] == "extXA" and shown["scopeRevisionId"] == "rev_x"
    # The desktop re-sends what it was shown (camelCase), and it round-trips.
    again = UpsertSourceSetInput.model_validate({"id": "set_x", "subjectId": "linear-algebra", "members": [shown]})
    upsert_source_set_rpc(ctx, again)
    assert _yaml_member(root)["scope_extraction_id"] == "extXA"


# --- what stays as it was ------------------------------------------------------------------


def test_a_textbook_with_held_out_signals_made_as_a_textbook_is_unaffected(exam_book):
    """Signals count where an exam role made them (or the book is exam material
    now): a textbook inventory's model-chosen held-out flag protects nothing."""

    repo, clock = exam_book["repo"], exam_book["clock"]
    a = repo.load_document_ir("extXA")
    _fresh_signal(repo, extraction_id="extXA", unit_id="u1", span_ids=["x1"], semantic_hash=a.units[0].semantic_hash,
                  role="primary_textbook")
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    sets = [NS(id="set_t", subject_id="linear-algebra", members=[NS(
        source_id="src_x", revision_id="rev_x", default_role="primary_textbook", scope=[],
        scope_extraction_id=None, scope_revision_id=None)])]
    assert EM.source_marks(sets, repo) == {}
    assert EM.exam_material(sets, repo).material.empty


# --- migration 225: the ledger, backfilled exactly from the cache ------------------------


def test_migration_225_backfills_each_signal_on_the_reading_it_was_made_on(blank_book):
    """A cached row never rebound was written by the model run on its own
    extraction: its signals mark that reading. A rebound row (its usage names
    the inventory it was rebound from) or one whose usage cannot be read
    marks no reading, and still protects its book."""

    import json

    from learnloop.db.migrate import apply_migrations

    repo, clock = blank_book["repo"], blank_book["clock"]
    _persist(repo, _exam_reading_a(), revision_id="rev_x", extraction_id="extXA", clock=clock)
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    with repo.connection() as connection:
        connection.execute("DROP TRIGGER source_held_out_signal_marks_no_update")
        connection.execute("DROP TABLE source_held_out_signal_marks")
        connection.execute("DELETE FROM schema_migrations WHERE version = 225")

        def cached(inventory_id, extraction_id, unit_id, spans, usage, held_out=True):
            inventory = {"assessment_signals": [{"held_out": held_out, "span_ids": spans},
                                                {"held_out": False, "span_ids": ["x9"]}]}
            connection.execute(
                "INSERT INTO source_unit_inventories(id, source_revision_id, extraction_id, unit_id, "
                "unit_semantic_hash, inventory_profile, inventory_schema_version, prompt_version, provider, model, "
                "inventory_json, usage_json, created_at) VALUES (?, 'rev_x', ?, ?, ?, 'assessment', 1, 'p', 'f', 'f', "
                "?, ?, '2026-10-14T09:00:00Z')",
                (inventory_id, extraction_id, unit_id, f"sha256:{inventory_id}", json.dumps(inventory), usage))

        cached("inv_fresh", "extXA", "u1", ["x1", "x0"], json.dumps({"calls": 1}))
        cached("inv_null_usage", "extXA", "u3", ["x1"], None)
        cached("inv_rebound", "extXB", "u2", ["y3"], json.dumps({"calls": 0, "rebound_from_inventory_id": "inv_old"}))
        cached("inv_unreadable", "extXB", "u4", ["y3"], "{not json")
        cached("inv_nothing_held", "extXA", "u5", ["x3"], json.dumps({"calls": 1}), held_out=False)
        connection.commit()
    assert [migration.version for migration in apply_migrations(repo.sqlite_path)] == [225]

    rows = {row["inventory_id"]: row for row in repo.held_out_signal_marks()}
    assert set(rows) == {"inv_fresh", "inv_null_usage", "inv_rebound", "inv_unreadable"}
    assert (rows["inv_fresh"]["extraction_id"], rows["inv_fresh"]["span_ids"]) == ("extXA", ["x0", "x1"])
    assert rows["inv_null_usage"]["extraction_id"] == "extXA"
    assert rows["inv_rebound"]["extraction_id"] is None and rows["inv_unreadable"]["extraction_id"] is None
    assert all(row["made_as_role"] is None and row["revision_id"] == "rev_x" for row in rows.values())

    sets = _exam_sets(default_role="exam", scope=())
    marks = EM.source_marks(sets, repo)["src_x"]
    assert marks.marked == ("extXA",) and marks.unmarked == ("extXB",)
    held = EM.held_out_material(sets, repo)
    assert held.covers("extXA", "x1") and not held.covers("extXA", "x3") and "extXB" in held.extractions
    with pytest.raises(Exception, match="append-only"), repo.connection() as connection:
        connection.execute("UPDATE source_held_out_signal_marks SET extraction_id = 'extXB'")
    # A rebound row alone still protects its book: no reading is marked by it.
    with repo.connection() as connection:
        connection.execute("DELETE FROM source_held_out_signal_marks WHERE extraction_id IS NOT NULL")
        connection.commit()
    marks = EM.source_marks(sets, repo)["src_x"]
    assert marks.marked == () and set(marks.unmarked) == {"extXA", "extXB"}


def test_an_exact_mark_never_resolves_a_reading_a_legacy_mark_may_also_be_about(exam_book):
    """A legacy exam scope may be about any reading, and a legacy held-out mark
    is about its own: an exact mark on the same reading does not resolve it,
    so the reading stays withheld whole (the legacy part is never released)
    until the owner's marking action marks it, after reviewing every mark."""

    from learnloop.content.pipeline import exam_marking

    repo, clock = exam_book["repo"], exam_book["clock"]
    # An exact scope on A (its Exam unit) and a legacy held-out mark on A's Theory.
    sets = _exact_sets("extXA")
    _legacy_marks(repo, "extXA", ["u2"])
    material = EM.exam_material(sets, repo)
    assert "extXA" in material.held_out.extractions, "A's legacy Theory mark is never released"
    marks = EM.source_marks(sets, repo)["src_x"]
    assert marks.marked == () and marks.ambiguous == ("selection",)
    shown = exam_marking.mark_plan(sets, repo, "src_x")
    assert shown["extraction_id"] == "extXA" and shown["held_out_unit_ids"] == ["u1", "u2"]
    exam_marking.mark_exam_material(sets, repo, "src_x", extraction_id="extXA", proposal_hash=shown["proposal_hash"],
                                    clock=clock)
    material = EM.exam_material(sets, repo)
    assert material.is_held_out("extXA", "x3") and material.covers("extXA", "x1")
    assert EM.source_marks(sets, repo)["src_x"].marked == ("extXA",)


def test_an_exact_held_out_mark_under_a_legacy_scope_waits_for_the_owners_marking(exam_book):
    from learnloop.content.pipeline import exam_marking

    repo, clock = exam_book["repo"], exam_book["clock"]
    _owner_marks(repo, "extXA", ["u1"])
    sets = _exam_sets(default_role="primary_textbook", scope=(("u2", "exam"),), reading=None)
    assert "extXA" in EM.exam_material(sets, repo).held_out.extractions
    shown = exam_marking.mark_plan(sets, repo, "src_x")
    assert set(shown["held_out_unit_ids"]) == {"u1", "u2"}, "the legacy scope's units, suggested by their ids"
    exam_marking.mark_exam_material(sets, repo, "src_x", extraction_id="extXA", proposal_hash=shown["proposal_hash"],
                                    clock=clock)
    assert EM.source_marks(sets, repo)["src_x"].marked == ("extXA",)
    assert EM.exam_material(sets, repo).is_held_out("extXA", "x3")
