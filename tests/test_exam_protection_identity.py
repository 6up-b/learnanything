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

    from learnloop.vault.models import SourceSet, SourceSetMember, SourceSetScope, scope_seal

    member = SourceSetMember(
        source_id="src_x", revision_id=revision_id, default_role=default_role,
        scope_extraction_id=extraction_id, scope_revision_id=scope_revision_id,
        scope=[SourceSetScope(unit_id=unit, role_override=role) for unit, role in scope])
    member.scope_seal = scope_seal(member)  # as the vault writer seals it
    return [SourceSet(id="set_x", subject_id="linear_algebra", title="Exam prep", members=[member])]


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


@pytest.mark.durability  # the marking's transaction and the backfill, under WAL too
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
    assert loaded.scope_seal and loaded.scope_seal == _yaml_member(root)["scope_seal"]

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
    assert shown["scopeExtractionId"] == "extXA" and shown["scopeRevisionId"] == "rev_x" and shown["scopeSeal"]
    # The desktop re-sends what it was shown (camelCase), and it round-trips.
    again = UpsertSourceSetInput.model_validate({"id": "set_x", "subjectId": "linear-algebra", "members": [shown]})
    upsert_source_set_rpc(ctx, again)
    assert _yaml_member(root)["scope_seal"] == shown["scopeSeal"]
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


# --- migration 204: the ledger, backfilled exactly from the cache ------------------------


@pytest.mark.durability  # the marking's transaction and the backfill, under WAL too
def test_migration_225_backfills_each_signal_on_the_reading_it_was_made_on(blank_book):
    """A cached row never rebound was written by the model run on its own
    extraction: its signals mark that reading. A rebound row (its usage names
    the inventory it was rebound from) or one whose usage cannot be read
    marks no reading, still protects its book, and lets no other signal mark
    a reading beside it (identity review F2). The inventory profile is no
    role: an ``assessment`` row records none (re-review F7); its exam
    membership qualifies it here."""

    import json

    from learnloop.db.migrate import apply_migrations

    repo, clock = blank_book["repo"], blank_book["clock"]
    _persist(repo, _exam_reading_a(), revision_id="rev_x", extraction_id="extXA", clock=clock)
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    with repo.connection() as connection:
        connection.execute("DROP TRIGGER source_held_out_signal_marks_no_update")
        connection.execute("DROP TABLE source_held_out_signal_marks")
        connection.execute("DELETE FROM schema_migrations WHERE version = 204")

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
    # Read before it is migrated (a dry run never migrates): the same protection the backfill gives.
    unmigrated = (EM.source_marks(_exam_sets(default_role="exam", scope=()), repo),
                  EM.held_out_material(_exam_sets(default_role="exam", scope=()), repo))
    assert [migration.version for migration in apply_migrations(repo.sqlite_path)] == [204]
    assert (EM.source_marks(_exam_sets(default_role="exam", scope=()), repo),
            EM.held_out_material(_exam_sets(default_role="exam", scope=()), repo)) == unmigrated

    rows = {row["inventory_id"]: row for row in repo.held_out_signal_marks()}
    assert set(rows) == {"inv_fresh", "inv_null_usage", "inv_rebound", "inv_unreadable"}
    assert (rows["inv_fresh"]["extraction_id"], rows["inv_fresh"]["span_ids"]) == ("extXA", ["x0", "x1"])
    assert rows["inv_null_usage"]["extraction_id"] == "extXA"
    assert rows["inv_rebound"]["extraction_id"] is None and rows["inv_unreadable"]["extraction_id"] is None
    assert all(row["made_as_role"] is None and row["revision_id"] == "rev_x" for row in rows.values()), (
        "the profile is no role")

    sets = _exam_sets(default_role="exam", scope=())
    # The rebound rows may be about any reading: no signal marks one beside them.
    marks = EM.source_marks(sets, repo)["src_x"]
    assert marks.marked == () and set(marks.unmarked) == {"extXA", "extXB"} and marks.ambiguous == ("signal",)
    assert {"extXA", "extXB"} <= EM.held_out_material(sets, repo).extractions
    with pytest.raises(Exception, match="append-only"), repo.connection() as connection:
        connection.execute("UPDATE source_held_out_signal_marks SET extraction_id = 'extXB'")
    with repo.connection() as connection:
        unbound = [dict(row) for row in connection.execute(
            "SELECT * FROM source_held_out_signal_marks WHERE extraction_id IS NULL")]
        connection.execute("DELETE FROM source_held_out_signal_marks WHERE extraction_id IS NULL")
        connection.commit()
    # Without them, each signal marks the reading its model run read.
    marks = EM.source_marks(sets, repo)["src_x"]
    assert marks.marked == ("extXA",) and marks.unmarked == ("extXB",)
    held = EM.held_out_material(sets, repo)
    assert held.covers("extXA", "x1") and not held.covers("extXA", "x3") and "extXB" in held.extractions
    # A rebound row alone still protects its book: no reading is marked by it.
    with repo.connection() as connection:
        connection.execute("DELETE FROM source_held_out_signal_marks")
        for row in unbound:
            connection.execute(f"INSERT INTO source_held_out_signal_marks({', '.join(row)}) "
                               f"VALUES ({', '.join('?' for _ in row)})", list(row.values()))
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


@pytest.mark.parametrize("edit", ["units", "reading"])
def test_a_scope_edited_outside_the_writer_names_no_reading(exam_book, edit):
    """The writer seals a scope to the reading it names. A hand edit of
    ``source_sets.yaml`` that changes the scope's units (B's ``u2`` typed over
    A's ``u1``) or its reading under the old seal never moves protection by
    position: the scope names no reading, and every reading is withheld."""

    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_source_set
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    repo, clock, root = exam_book["repo"], exam_book["clock"], exam_book["root"]
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "title": "Exam prep", "members": [
        {"source_id": "src_x", "revision_id": "rev_x", "default_role": "primary_textbook",
         "scope_extraction_id": "extXA", "scope_revision_id": "rev_x",
         "scope": [{"unit_id": "u1", "role_override": "exam"}]}]})
    material = EM.exam_material(load_vault(root), repo)
    assert material.covers("extXA", "x1") and not material.covers("extXA", "x3"), "sealed: exact"

    path = root / "sources" / "source_sets.yaml"
    data = read_yaml(path)
    member = data["source_sets"][0]["members"][0]
    if edit == "units":
        member["scope"] = [{"unit_id": "u2", "role_override": "exam"}]
    else:
        member["scope_extraction_id"] = "extXB"
    write_yaml(path, data)
    vault = load_vault(root)
    material = EM.exam_material(vault, repo)
    assert _unprotected_copies(repo, material.material, _EXAM_Q) == []
    assert {"extXA", "extXB"} <= material.held_out.extractions
    assert EM.source_marks(vault, repo)["src_x"].ambiguous == ("scope",)
    # A writer re-sending the edited member under its stale seal does not re-seal it.
    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra",
                             "members": [vault.source_sets[0].members[0].model_dump(mode="json")]})
    assert "scope_seal" not in _yaml_member(root) and "scope_extraction_id" not in _yaml_member(root)


# --- the Codex review of extraction identity (docs/reviews/exam-protection-identity-codex-review.md) ---


def _mark_what_is_shown(vault, repo, clock) -> dict:
    """The owner confirms the card's marking exactly as shown."""

    from learnloop.content.pipeline import exam_marking

    shown = exam_marking.mark_plan(vault, repo, "src_x")
    assert shown is not None
    exam_marking.mark_exam_material(vault, repo, "src_x", extraction_id=shown["extraction_id"],
                                    proposal_hash=shown["proposal_hash"], clock=clock)
    return shown


def test_identity_review_f1_a_confirmation_never_covers_an_ambiguous_mark_made_after_it(exam_book):
    """Identity review F1: the owner confirmed B's suggested ``u2``; later an
    exam scope that names no reading (an older client, a hand edit) names
    ``u1``, which on B is Theory. The old confirmation exempted B from every
    ambiguity: B's ``u1`` was released and no fresh marking was offered. A
    confirmation covers the marks it reviewed only: a new or changed one holds
    B back again until the owner marks it again."""

    from learnloop.content.pipeline import exam_marking

    repo, clock = exam_book["repo"], exam_book["clock"]
    _owner_marks(repo, "extXA", ["u1"])
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    plain = NS(source_sets=[])
    _mark_what_is_shown(plain, repo, clock)
    assert EM.source_marks(plain, repo)["src_x"].marked == ("extXA", "extXB")

    later = NS(source_sets=_exam_sets(default_role="primary_textbook", scope=(("u1", "exam"),), reading=None))
    material = EM.exam_material(later, repo)
    assert material.covers("extXB", "y1"), "B's u1, named by the later mark, is never released"
    assert "extXB" in material.held_out.extractions
    plan = exam_marking.mark_plan(later, repo, "src_x")
    assert plan is not None and plan["extraction_id"] == "extXB" and "u1" in plan["held_out_unit_ids"]

    exam_marking.mark_exam_material(later, repo, "src_x", extraction_id="extXB", proposal_hash=plan["proposal_hash"],
                                    clock=clock)
    assert "extXB" in EM.source_marks(later, repo)["src_x"].marked, "reviewed: B is exact again"
    material = EM.exam_material(later, repo)
    assert material.is_held_out("extXB", "y1") and material.is_held_out("extXB", "y3")

    changed = NS(source_sets=_exam_sets(default_role="primary_textbook", scope=(("u1", "exam"), ("u9", "exam")),
                                        reading=None))
    assert "extXB" in EM.exam_material(changed, repo).held_out.extractions, "a changed mark is reviewed again"
    assert exam_marking.mark_plan(changed, repo, "src_x")["extraction_id"] == "extXB"
    # A legacy mark removed takes nothing the owner reviewed away: B stays exact.
    assert "extXB" in EM.source_marks(plain, repo)["src_x"].marked


def _rerun_migration_225(repo: Repository, write_cache) -> None:
    """Back to a database before migration 204 (the ledger dropped), let
    ``write_cache(connection)`` change it as an older build would, then
    migrate: the backfill runs on what is there."""

    from learnloop.db.migrate import apply_migrations

    with repo.connection() as connection:
        connection.execute("DROP TRIGGER source_held_out_signal_marks_no_update")
        connection.execute("DROP TABLE source_held_out_signal_marks")
        connection.execute("DELETE FROM schema_migrations WHERE version = 204")
        connection.commit()
    write_cache(repo)
    assert [migration.version for migration in apply_migrations(repo.sqlite_path)] == [204]


def _cached_inventory(repo: Repository, inventory_id: str, extraction_id: str, unit_id: str, spans, *,
                      profile: str = "combined", semantic_hash: str | None = None, prompt_version: str = "p",
                      model: str = "f", usage: str = '{"calls": 1}') -> None:
    """A cache row a model run of an older build wrote (no ledger row beside it)."""

    import json

    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_unit_inventories(id, source_revision_id, extraction_id, unit_id, unit_semantic_hash, "
            "inventory_profile, inventory_schema_version, prompt_version, provider, model, inventory_json, usage_json, "
            "created_at) VALUES (?, 'rev_x', ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, '2026-10-14T09:00:00Z')",
            (inventory_id, extraction_id, unit_id, semantic_hash or f"sha256:{inventory_id}", profile, prompt_version,
             model, model, json.dumps({"assessment_signals": [{"held_out": True, "span_ids": list(spans)}]}), usage))
        connection.commit()


_TWO_QUESTIONS = {"x0": ("SectionHeader", 1, ["Question 1"], "Question 1"), "x1": ("Text", 1, ["Question 1"], _Q1),
                  "x2": ("SectionHeader", 2, ["Question 2"], "Question 2"), "x3": ("Text", 2, ["Question 2"], _Q2)}


def test_identity_review_f2_an_unbound_signal_never_lets_a_known_one_mark_its_origin(blank_book):
    """Identity review F2: before migration 204, A's inventories held out Q1
    (u1) and Q2 (u2); a cache hit for B reused only Q2's, which moved that
    cache row to B. The backfill keeps Q1 on A and records Q2's reading as
    unknown; A then counted as marked by Q1 alone and A's Q2 was released
    (the Reader's refusal ``[]``). An unbound signal may be about any reading:
    no known signal marks a reading beside it."""

    from learnloop.content.synthesis.ai_contracts import SOURCE_UNIT_INVENTORY_PROMPT_VERSION
    from learnloop.content.synthesis.source_unit_inventory import prepare_unit_inventory

    repo, clock = blank_book["repo"], blank_book["clock"]
    a = _ir(_TWO_QUESTIONS, [("u1", "Question 1", "sha256:q1", ["x0", "x1"]),
                             ("u2", "Question 2", "sha256:q2", ["x2", "x3"])], extractor="marker")
    _persist(repo, a, revision_id="rev_x", extraction_id="extXA", clock=clock)
    clock.advance()
    a = repo.load_document_ir("extXA")
    b = a.model_copy(deep=True)
    b.extractor = "reread"
    for block in b.blocks:
        block.span_id = block.span_id.replace("x", "y")
    for unit in b.units:
        unit.span_ids = [span.replace("x", "y") for span in unit.span_ids]
    _persist(repo, b, revision_id="rev_x", extraction_id="extXB", clock=clock)

    def older_build(repo: Repository) -> None:
        for unit, span in zip(a.units, ("x1", "x3"), strict=True):
            _cached_inventory(repo, f"inv_{unit.unit_id}", "extXA", unit.unit_id, [span], profile="assessment",
                              semantic_hash=unit.semantic_hash, prompt_version=SOURCE_UNIT_INVENTORY_PROMPT_VERSION,
                              model="fake")
        hit = prepare_unit_inventory(repo, "extXB", "u2", role="exam", profile="assessment", provider="fake",
                                     model="fake")
        assert hit.cache_hit

    _rerun_migration_225(repo, older_build)
    rows = {row["inventory_id"]: row for row in repo.held_out_signal_marks()}
    assert rows["inv_u1"]["extraction_id"] == "extXA" and rows["inv_u2"]["extraction_id"] is None

    sets = _exam_sets(default_role="exam", scope=())
    held = EM.held_out_material(sets, repo)
    assert EM.held_out_among(held, "extXA", ["x1", "x3"]) == ["x1", "x3"], "the Reader refuses both of A's questions"
    assert "extXB" in held.extractions
    marks = EM.source_marks(sets, repo)["src_x"]
    assert marks.marked == () and set(marks.unmarked) == {"extXA", "extXB"} and "signal" in marks.ambiguous


def test_identity_review_a_signal_of_unknown_reading_is_named_plainly(exam_book):
    """The card and doctor say why a book whose only unclear mark is a signal
    of unknown reading is held back, in plain words (LearnLoop found the
    questions; nobody marked them), and offer the marking."""

    from learnloop.content.pipeline import exam_marking
    from learnloop.ops.doctor import run_doctor
    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_source_set

    repo, clock, root = exam_book["repo"], exam_book["clock"], exam_book["root"]
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    _rerun_migration_225(repo, lambda repo: _cached_inventory(
        repo, "inv_q", "extXB", "u2", ["y3"], profile="assessment",
        usage='{"calls": 0, "rebound_from_inventory_id": "inv_old"}'))
    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "title": "Exam prep", "members": [
        {"source_id": "src_x", "revision_id": "rev_x", "default_role": "exam", "scope": []}]})
    vault = load_vault(root)
    assert EM.source_marks(vault, repo)["src_x"].ambiguous == ("signal",)
    assert exam_marking.held_back_details(vault, repo, "src_x") == exam_marking.FOUND_DETAILS
    issues = [issue for issue in run_doctor(root).issues if issue.code == "source:reading_held_back"]
    assert len(issues) == 1 and issues[0].details["ambiguous"] == ["signal"]
    assert "found exam questions in it before it recorded which reading" in issues[0].message
    plan = exam_marking.mark_plan(vault, repo, "src_x")
    assert plan["extraction_id"] == "extXB" and "u2" in plan["held_out_unit_ids"], "suggested where it was found"


@pytest.mark.parametrize("qualified_by", ["outline_pick", "outline_pick_after_upgrade"])
def test_identity_review_f3_an_upgraded_exam_signal_survives_its_qualification_leaving(blank_book, qualified_by):
    """Identity review F3 (the database side): a signal backfilled by 204
    named no role, so it protected only while its book was exam material,
    and it was released without any decision once that ended. An inventory
    on a book with an outline exam pick is recorded as exam material by the
    upgrade; a pick removed after the upgrade records it first. (Its
    ``assessment_profile`` case is gone: the profile is no role, re-review
    F7.)"""

    repo, clock = blank_book["repo"], blank_book["clock"]
    _persist(repo, _exam_reading_a(), revision_id="rev_x", extraction_id="extXA", clock=clock)
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)

    def pick(repo: Repository, role: str | None) -> None:
        repo.upsert_unit_selection(extraction_id="extXA", source_id="src_x", revision_id="rev_x",
                                   selected_unit_ids=["u1", "u2"], role_override=role)

    def older_build(repo: Repository) -> None:
        _cached_inventory(repo, "inv_q", "extXA", "u1", ["x1"])
        if qualified_by == "outline_pick":
            pick(repo, "exam")

    _rerun_migration_225(repo, older_build)
    if qualified_by == "outline_pick_after_upgrade":
        pick(repo, "exam")
        assert EM.held_out_material([], repo).covers("extXA", "x1")
    pick(repo, "primary_textbook")  # the pick is changed: the book is no longer exam material

    held = EM.held_out_material([], repo)
    assert held.covers("extXA", "x1"), "the question stays held out"
    assert "extXB" in held.extractions
    assert EM.source_marks([], repo)["src_x"].unmarked == ("extXB",)


@pytest.mark.parametrize("change", ["re_role", "remove", "scope_removed"])
def test_identity_review_f3_a_legacy_signal_survives_its_exam_membership_changing(exam_book, change):
    """Identity review F3 (the vault side): a backfilled signal on an exam
    member (or a book with an exam scope) stopped counting once the member
    left the set, was re-roled or lost its scope. The vault writer records
    the book's role-unrecorded signals as exam material before it writes a
    change that ends the book's exam membership in the set."""

    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_source_set

    repo, clock, root = exam_book["repo"], exam_book["clock"], exam_book["root"]
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    _rerun_migration_225(repo, lambda repo: _cached_inventory(repo, "inv_q", "extXA", "u1", ["x1"]))
    assert [row["made_as_role"] for row in repo.held_out_signal_marks()] == [None]

    member = {"source_id": "src_x", "revision_id": "rev_x", "default_role": "exam", "scope": []}
    if change == "scope_removed":
        member = {**member, "default_role": "primary_textbook", "scope_extraction_id": "extXA",
                  "scope_revision_id": "rev_x", "scope": [{"unit_id": "u1", "role_override": "exam"}]}
    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "title": "Exam prep", "members": [member]})
    assert EM.held_out_material(load_vault(root), repo).covers("extXA", "x1")

    after = {"re_role": [{**member, "default_role": "primary_textbook"}], "remove": [],
             "scope_removed": [{**member, "scope": []}]}[change]
    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "members": after})
    vault = load_vault(root)
    held = EM.held_out_material(vault, repo)
    assert held.covers("extXA", "x1"), "the question stays held out after the membership change"
    assert "extXB" in held.extractions
    assert "src_x" in EM.source_marks(vault, repo)


def test_identity_review_f3_an_unchanged_membership_records_nothing(exam_book):
    """The writer records nothing for a book that never is exam material
    (the owner's textbook signals keep protecting nothing), nor while its
    exam membership stays as it is. A write that makes it exam material
    records its signals once (re-review F3)."""

    from learnloop.vault.writer import upsert_source_set

    repo, root = exam_book["repo"], exam_book["root"]
    _rerun_migration_225(repo, lambda repo: _cached_inventory(repo, "inv_q", "extXA", "u1", ["x1"]))
    textbook = {"source_id": "src_x", "revision_id": "rev_x", "default_role": "primary_textbook", "scope": []}
    for members in ([textbook], [], [textbook]):
        upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "title": "T", "members": members})
    assert [row["made_as_role"] for row in repo.held_out_signal_marks()] == [None]
    for _ in range(2):
        upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "title": "T",
                                 "members": [{**textbook, "default_role": "exam"}]})
    assert sorted(row["made_as_role"] or "" for row in repo.held_out_signal_marks()) == ["", "exam"]


@pytest.mark.durability  # the verdict and the marking in one transaction, under WAL too
def test_identity_review_f5_the_owners_marking_is_an_owner_verdict_in_the_judgment_ledger(exam_book, monkeypatch):
    """Identity review F5: the owner's confirmed marking wrote only the
    selection's mutable metadata; ``judgment_ledger`` had no row. It appends
    one owner verdict in the marking's transaction (the reading, its
    revision, the proposal, the units held out, when), once."""

    import json

    from learnloop.content.pipeline import exam_marking

    repo, clock = exam_book["repo"], exam_book["clock"]
    _owner_marks(repo, "extXA", ["u1"])
    clock.advance()
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    vault = NS(source_sets=[])
    shown = exam_marking.mark_plan(vault, repo, "src_x")

    def refused(*args, **kwargs):
        raise RuntimeError("the ledger refused the verdict")

    monkeypatch.setattr(exam_marking, "append_judgment", refused, raising=False)
    with pytest.raises(RuntimeError, match="refused"):
        exam_marking.mark_exam_material(vault, repo, "src_x", extraction_id=shown["extraction_id"],
                                        proposal_hash=shown["proposal_hash"], clock=clock)
    assert repo.get_unit_selection("extXB") is None, "no marking without its verdict"
    monkeypatch.undo()

    exam_marking.mark_exam_material(vault, repo, "src_x", extraction_id=shown["extraction_id"],
                                    proposal_hash=shown["proposal_hash"], clock=clock)

    def verdicts() -> list[dict]:
        with repo.connection() as connection:
            return [dict(row) for row in connection.execute(
                "SELECT * FROM judgment_ledger WHERE task = ?", (exam_marking.MARK_JUDGMENT_TASK,))]

    rows = verdicts()
    assert len(rows) == 1
    row = rows[0]
    assert (row["judge"], row["verdict"], row["left_kind"], row["left_id"], row["right_kind"], row["right_id"]) == (
        "owner", "marked", "extraction", "extXB", "source", "src_x")
    assert row["input_hash"] == shown["proposal_hash"]
    recorded = json.loads(row["rationale"])
    assert recorded["extraction_id"] == "extXB" and recorded["revision_id"] == "rev_x"
    assert recorded["proposal_hash"] == shown["proposal_hash"] and recorded["held_out_unit_ids"] == ["u2"]
    assert recorded["at"] == row["created_at"]
    with pytest.raises(exam_marking.StaleMarkConfirmation):  # a retry writes no second verdict
        exam_marking.mark_exam_material(vault, repo, "src_x", extraction_id=shown["extraction_id"],
                                        proposal_hash=shown["proposal_hash"], clock=clock)
    assert len(verdicts()) == 1


def _plan_with_a_held_out_contents(tmp_path, monkeypatch, toml: str | None, *, switch_off: bool):
    import json
    from datetime import UTC, datetime

    import learnloop.clock as clock_module
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection
    from learnloop_sidecar.context import SidecarContext
    from tests.helpers import create_daily_plan_vault
    from tests.test_exam_protection_review import _switch_off
    from tests.test_reread_safety import call
    from tests.test_ux_phase1_round2_review import _seed_book

    paths = create_daily_plan_vault(tmp_path / "vault", plan_toml=toml)
    if switch_off:
        _switch_off(paths.root)
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
    with repo.connection() as connection:
        split = json.loads(connection.execute(
            "SELECT split_json FROM daily_plans ORDER BY created_at DESC LIMIT 1").fetchone()[0])
    return repo, plan, split


@pytest.mark.parametrize("toml", [None, "[plan]\nreading_from_furthest = false\n"], ids=["u4", "dl1"])
def test_identity_review_f6_the_kill_switch_restores_the_predecessors_reading_step(tmp_path, monkeypatch, toml):
    """Identity review F6: protection in DL1's order changed the offered
    reading (and the minutes admitted) with no switch restoring the
    predecessor. ``goals.held_out_selection`` (the serving rules' kill
    switch) now covers it: off, the reading step is the predecessor's exactly
    (DL1's order unfiltered; U4's order kept its own filter), and each plan
    records the rule that chose its step."""

    from learnloop.daily_plan.reading import next_reading_target
    from learnloop.source_retrieval.corpus import exam_exclusions
    from learnloop.vault.loader import load_vault

    dl1 = toml is not None
    repo, plan, split = _plan_with_a_held_out_contents(tmp_path / "off", monkeypatch, toml, switch_off=True)
    vault = load_vault(repo.sqlite_path.parent)
    predecessor = next_reading_target(repo, from_furthest=not dl1, exam=None if dl1 else exam_exclusions(vault, repo))
    steps = [row["readingTitle"] for row in plan["projected"] if row["readingTitle"]]
    assert predecessor is not None and steps and steps[0] == predecessor.section_title
    assert split["reading"]["section_id"] == predecessor.section_id
    assert split["reading_rule"] == ("dl1" if dl1 else "furthest")

    _repo, plan, split = _plan_with_a_held_out_contents(tmp_path / "on", monkeypatch, toml, switch_off=False)
    steps = [row["readingTitle"] for row in plan["projected"] if row["readingTitle"]]
    assert steps and "contents" not in [str(step).lower() for step in steps]
    assert split["reading_rule"] == ("book_order" if dl1 else "furthest")


def test_the_ledgers_exam_roles_are_the_role_authoritys(tmp_path):
    """The infrastructure layer's copy of the exam roles (it may not import
    the role authority) stays the role authority's, and the migration
    coordinator's source sets path (it may not import the vault) the vault's."""

    from learnloop.content.sources.role_authority import ASSESSMENT_ONLY_ROLES
    from learnloop.db.stores.held_out_signals import EXAM_ROLES
    from learnloop.migration_coordinator import SOURCE_SETS_PATH
    from tests.helpers import create_basic_vault

    assert EXAM_ROLES == ASSESSMENT_ONLY_ROLES
    paths = create_basic_vault(tmp_path / "vault")
    assert paths.source_sets_path == paths.root / SOURCE_SETS_PATH


# --- Codex re-review of extraction identity ------------------------------------------------


def _older_build_with_membership(exam_book, member, *, profile: str = "combined") -> None:
    """A vault an older build wrote: no ledger (migration 204 not applied), a
    cache row with a held-out signal on A's Exam unit, and B read; the book's
    membership in ``source_sets.yaml`` is ``member`` (None: no set)."""

    from learnloop.vault.writer import upsert_source_set

    repo, clock, root = exam_book["repo"], exam_book["clock"], exam_book["root"]
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    with repo.connection() as connection:
        connection.execute("DROP TRIGGER source_held_out_signal_marks_no_update")
        connection.execute("DROP TABLE source_held_out_signal_marks")
        connection.execute("DELETE FROM schema_migrations WHERE version = 204")
        connection.commit()
    _cached_inventory(repo, "inv_q", "extXA", "u1", ["x1"], profile=profile)
    if member is not None:
        upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "title": "Exam prep",
                                 "members": [member]})


def _hand_edit_members(root: Path, members) -> None:
    """The owner edits ``sources/source_sets.yaml`` in a text editor: no vault writer runs."""

    import yaml

    path = root / "sources" / "source_sets.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["source_sets"][0]["members"] = members
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


_EXAM_MEMBER = {"source_id": "src_x", "revision_id": "rev_x", "default_role": "exam", "scope": []}
_SCOPED_MEMBER = {"source_id": "src_x", "revision_id": "rev_x", "default_role": "primary_textbook",
                  "scope_extraction_id": "extXA", "scope_revision_id": "rev_x",
                  "scope": [{"unit_id": "u1", "role_override": "exam"}]}


@pytest.mark.parametrize("upgrade", ["by_the_app", "path_only_then_opened"])
@pytest.mark.parametrize("change", ["re_role", "remove", "scope_removed"])
def test_identity_rereview_f3_a_hand_edit_never_releases_a_signal_its_membership_qualified(exam_book, upgrade,
                                                                                           change):
    """Codex re-review F3: a ``combined``-profile signal backfilled by 204
    names no role, so it protected A's question only while its book was exam
    material in ``source_sets.yaml``. The vault writer recorded it before a
    write that ended that membership, but a hand edit of the file bypasses the
    writer, and A's question, B and the book's marks were all released. The
    app records the signals its vault's exam membership qualifies whenever it
    migrates or opens the vault (the upgrade first), while that membership is
    known."""

    from learnloop.db.migrate import apply_migrations
    from learnloop.migration_coordinator import migrate_vault
    from learnloop.vault.loader import load_vault

    repo, root = exam_book["repo"], exam_book["root"]
    member = _SCOPED_MEMBER if change == "scope_removed" else _EXAM_MEMBER
    _older_build_with_membership(exam_book, member)
    if upgrade == "by_the_app":
        assert [migration.version for migration in migrate_vault(root, repo.sqlite_path)] == [204]
    else:
        assert [migration.version for migration in apply_migrations(repo.sqlite_path)] == [204]
        assert migrate_vault(root, repo.sqlite_path) == []  # the app opens the vault: nothing left to migrate
    assert EM.held_out_material(load_vault(root), repo).covers("extXA", "x1")

    after = {"re_role": [{**member, "default_role": "primary_textbook"}], "remove": [],
             "scope_removed": [{**member, "scope": []}]}[change]
    _hand_edit_members(root, after)
    vault = load_vault(root)
    held = EM.held_out_material(vault, repo)
    assert held.covers("extXA", "x1"), "A's question stays held out after the hand edit"
    assert "extXB" in held.extractions, "B stays withheld until protection is marked on it"
    assert "src_x" in EM.source_marks(vault, repo)
    assert {row["made_as_role"] for row in repo.held_out_signal_marks()} == {None, "exam"}, "an appended copy"


def test_identity_rereview_f3_opening_records_only_what_membership_qualifies(exam_book):
    """Opening records nothing for a book its membership does not make exam
    material (the owner's textbook signals keep protecting nothing), and an
    exam book's signal once, however often the vault opens."""

    from learnloop.migration_coordinator import migrate_vault

    repo, root = exam_book["repo"], exam_book["root"]
    textbook = {**_EXAM_MEMBER, "default_role": "primary_textbook"}
    _older_build_with_membership(exam_book, textbook)
    assert [migration.version for migration in migrate_vault(root, repo.sqlite_path)] == [204]
    migrate_vault(root, repo.sqlite_path)
    assert [row["made_as_role"] for row in repo.held_out_signal_marks()] == [None]
    _hand_edit_members(root, [_EXAM_MEMBER])
    for _ in range(3):
        migrate_vault(root, repo.sqlite_path)
    assert sorted(row["made_as_role"] or "" for row in repo.held_out_signal_marks()) == ["", "exam"]


@pytest.mark.parametrize("read", ["migrated", "not_yet_migrated"])
def test_identity_rereview_f7_an_assessment_profile_is_not_an_exam_role(exam_book, read):
    """Codex re-review F7: the inventory profile is configurable apart from
    the role (``learnloop inventory --role primary_textbook --profile
    assessment``). The 204 backfill took an ``assessment`` profile for the
    exam role: a textbook's held-out signal protected it, and its other
    reading was withheld whole, theory included. Only role evidence (an exam
    membership, an outline exam pick) qualifies a backfilled signal."""

    from learnloop.db.migrate import apply_migrations

    repo, root = exam_book["repo"], exam_book["root"]
    textbook = {**_EXAM_MEMBER, "default_role": "primary_textbook"}
    _older_build_with_membership(exam_book, textbook, profile="assessment")
    if read == "migrated":
        assert [migration.version for migration in apply_migrations(repo.sqlite_path)] == [204]
        assert [row["made_as_role"] for row in repo.held_out_signal_marks()] == [None]
    sets = _exam_sets(default_role="primary_textbook", scope=())
    assert EM.source_marks(sets, repo) == {}
    material = EM.exam_material(sets, repo)
    assert not material.held_out.extractions and material.material.empty
    assert not EM.held_out_material(sets, repo).covers("extXA", "x1")
    # With exam role evidence, the same row protects (membership; an outline pick).
    assert EM.held_out_material(_exam_sets(default_role="exam", scope=()), repo).covers("extXA", "x1")


@pytest.mark.parametrize("member", ["exam_role", "exam_scope"])
def test_identity_rereview_f3_exam_membership_the_writer_adds_survives_a_hand_edit(exam_book, member):
    """Re-review F3, within one session: the book was a textbook at the
    upgrade (its backfilled signal unrecorded), the owner makes it exam
    material through the app (the vault writer), then removes that in a text
    editor before the app opens the vault again. The writer records the
    book's unrecorded signals when its write makes the book exam material, as
    it does when one ends it."""

    from learnloop.migration_coordinator import migrate_vault
    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_source_set

    repo, root = exam_book["repo"], exam_book["root"]
    textbook = {**_EXAM_MEMBER, "default_role": "primary_textbook"}
    _older_build_with_membership(exam_book, textbook)
    assert [migration.version for migration in migrate_vault(root, repo.sqlite_path)] == [204]
    assert [row["made_as_role"] for row in repo.held_out_signal_marks()] == [None]

    exam = _EXAM_MEMBER if member == "exam_role" else _SCOPED_MEMBER
    upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "members": [exam]})
    assert EM.held_out_material(load_vault(root), repo).covers("extXA", "x1")
    _hand_edit_members(root, [textbook])
    vault = load_vault(root)
    held = EM.held_out_material(vault, repo)
    assert held.covers("extXA", "x1"), "A's question stays held out after the hand edit"
    assert "extXB" in held.extractions and "src_x" in EM.source_marks(vault, repo)


def test_identity_rereview_f3_the_running_app_records_hand_edited_exam_membership(exam_book):
    """Re-review F3 through the desktop app's own path: the app upgrades the
    vault when it loads it (the book a textbook then), the owner makes the
    book exam material in a text editor, the watcher reloads the vault, and
    the owner then removes the membership in the editor. Every load the app
    serves from goes through the vault's open, which records the signals the
    membership it read qualifies, so the second edit releases nothing."""

    from learnloop_sidecar.context import SidecarContext

    root = exam_book["root"]
    textbook = {**_EXAM_MEMBER, "default_role": "primary_textbook"}
    _older_build_with_membership(exam_book, textbook)
    context = SidecarContext()
    context.load(root, maintenance=False)
    vault, repository = context.require_vault()
    assert [row["made_as_role"] for row in repository.held_out_signal_marks()] == [None], "upgraded, nothing qualified"
    assert not EM.held_out_material(vault, repository).covers("extXA", "x1")

    for members in ([_EXAM_MEMBER], [textbook]):  # the owner's two hand edits, each picked up by the watcher
        _hand_edit_members(root, members)
        assert context.refresh_vault_files(["sources/source_sets.yaml"], expected_root=root)["mode"] != "stale"
    vault, repository = context.require_vault()
    assert vault.source_sets[0].members[0].default_role == "primary_textbook", "the app serves the edited vault"
    held = EM.held_out_material(vault, repository)
    assert held.covers("extXA", "x1"), "A's question stays held out after the second hand edit"
    assert "extXB" in held.extractions and "src_x" in EM.source_marks(vault, repository)


# --- F3 final: only the coordinator upgrades a vault's database -----------------------------------------


#: CLI commands that opened the vault's database with a bare ``Repository(path)`` at bbe340ce9, which
#: applied the ledger migration (225 on the branch, 204 on main) without recording what the vault's
#: exam membership qualifies: a command that built the repository itself, one whose library call
#: built it, and one that reads its ledger first.
_CLI_UPGRADES = {
    "facets_actions": ["facets", "actions", "--json"],
    "proposals": ["proposals", "--json"],
    "families_undo": ["families", "undo", "fam_none", "--json"],
}


@pytest.mark.parametrize("command", sorted(_CLI_UPGRADES))
def test_f3_final_a_cli_upgrade_records_what_membership_qualifies_before_a_hand_edit(exam_book, command):
    """F3 final (the final verify's reproduction): before 204, a legacy
    ``combined`` inventory holds A's question out, the book is an exam member
    in ``source_sets.yaml``, and B is read. A CLI command upgrades the vault;
    the owner then removes the membership in a text editor; the app opens the
    vault. At bbe340ce9 the CLI's bare ``Repository(path)`` applied 225 (now 204) and
    recorded nothing, so the open appended no row and A's and B's questions,
    the book's marks and the post-attempt scope were all released. Every
    upgrade now runs through the coordinator, which records the membership it
    read."""

    from typer.testing import CliRunner

    from learnloop.cli import app
    from learnloop.db.migrate import applied_versions
    from learnloop.source_retrieval.find_sources import scope_for
    from learnloop.vault.loader import load_vault
    from learnloop.vault.models import SourceRef
    from learnloop.vault.repository import open_vault_repository

    repo, root = exam_book["repo"], exam_book["root"]
    _older_build_with_membership(exam_book, _EXAM_MEMBER)
    assert 204 not in applied_versions(repo.sqlite_path)

    result = CliRunner().invoke(app, [*_CLI_UPGRADES[command], "--vault", str(root)])
    assert result.exception is None or isinstance(result.exception, SystemExit), result.output
    assert 204 in applied_versions(repo.sqlite_path), "the CLI command upgraded the vault"

    _hand_edit_members(root, [])
    repository = open_vault_repository(root, repo.sqlite_path)  # the app opens the vault normally
    vault = load_vault(root)
    held = EM.held_out_material(vault, repository)
    assert EM.held_out_among(held, "extXA", ["x1"]) == ["x1"], "A's question stays held out"
    assert held.covers("extXB", "y3") and "extXB" in held.extractions, "B's question stays held out"
    assert "src_x" in EM.source_marks(vault, repository)
    ref = SourceRef(ref_type="canonical_source", ref_id="src_x", source_id="src_x", revision_id="rev_x",
                    extraction_id="extXA", span_ids=["x1"])
    item = NS(id="itemA", learning_object_id="lo1", provenance=NS(source_refs=[ref]))
    scope = scope_for(vault, repository, policy="post_attempt", scope="library", learning_object_ids=[], item=item)
    assert "extXA" not in scope.extractions or ("extXA", "x1") in scope.excluded, (
        "post-attempt retrieval never admits A's question")
    assert sorted(row["made_as_role"] or "" for row in repository.held_out_signal_marks()) == ["", "exam"], (
        "the CLI's upgrade recorded the signal its exam membership qualified (an appended copy)")


@pytest.mark.parametrize("vault_was", ["upgraded_by_the_app", "a_textbook_upgraded_by_the_cli"])
def test_f3_final_a_cli_open_changes_nothing_else(exam_book, vault_was):
    """Controls. A vault the app already upgraded is attached by every CLI
    command as before: its ledger gains nothing. A book that is not exam
    material (the owner's vaults: a video's ``combined`` inventory) records
    nothing when a CLI command upgrades it, and protects nothing."""

    from typer.testing import CliRunner

    from learnloop.cli import app
    from learnloop.migration_coordinator import migrate_vault
    from learnloop.vault.loader import load_vault

    repo, root = exam_book["repo"], exam_book["root"]
    textbook = {**_EXAM_MEMBER, "default_role": "primary_textbook"}
    _older_build_with_membership(exam_book, _EXAM_MEMBER if vault_was == "upgraded_by_the_app" else textbook)
    before = None
    if vault_was == "upgraded_by_the_app":
        assert [migration.version for migration in migrate_vault(root, repo.sqlite_path)] == [204]
        before = sorted((row["id"], row["made_as_role"] or "") for row in repo.held_out_signal_marks())

    for command in sorted(_CLI_UPGRADES):
        result = CliRunner().invoke(app, [*_CLI_UPGRADES[command], "--vault", str(root)])
        assert result.exception is None or isinstance(result.exception, SystemExit), result.output
    rows = sorted((row["id"], row["made_as_role"] or "") for row in repo.held_out_signal_marks())
    if vault_was == "upgraded_by_the_app":
        assert rows == before and [role for _, role in rows] == ["", "exam"]
    else:
        assert [role for _, role in rows] == [""], "a textbook's signal is recorded as nothing"
        vault = load_vault(root)
        assert EM.source_marks(vault, repo) == {}
        assert not EM.held_out_material(vault, repo).covers("extXA", "x1")
