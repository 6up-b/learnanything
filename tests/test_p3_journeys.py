"""P3 slice 3 acceptance -- Journeys 1/2/7, annotation survival across re-extraction,
and replay determinism (spec §15.7/§15.8/§15.9/§15.10).

Driven end-to-end through the real reader services on a fixture vault with the model
worker OFF (deterministic stubs where an LLM would render). Reading never becomes
mastery/diagnosis (the salience firewall is asserted throughout).
"""

from __future__ import annotations

from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.services import annotations as ANN
from learnloop.services import commitment_arcs as ARC
from learnloop.services import reader_authoring as AUTH
from learnloop.services import reader_capture as RC
from learnloop.services import reader_dialogue as RD
from learnloop.services import reader_restoration as REST
from learnloop.services import salience_firewall as SF
from learnloop.services.salience_firewall import SalienceEvidenceRejected, reject_salience
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault
from tests.test_source_inventory import _persist, _register_revision

_CLOCK = FrozenClock(NOW)


def _ir(blocks, extractor_version="1"):
    return DocumentIR(
        extractor="marker", extractor_version=extractor_version,
        units=[DocumentUnit(unit_id="u1", label="Symmetric matrices", ordinal=0,
                            semantic_hash="sha256:s", span_ids=[b.span_id for b in blocks])],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )


def _blocks():
    return [
        DocumentBlock.build(span_id="s1", block_type="Text",
                            text="A real square matrix is symmetric when A^T = A.", ordinal=1,
                            page=0, bbox=[10, 50, 300, 90], section_path=["Ch1"]),
        DocumentBlock.build(span_id="s2", block_type="Text",
                            text="The spectral theorem gives real eigenvalues.", ordinal=2,
                            page=0, bbox=[10, 100, 300, 140], section_path=["Ch1"]),
    ]


def _setup(tmp_path: Path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src1", revision_id="rev1")
    _persist(repo, _ir(_blocks()), revision_id="rev1", extraction_id="ext1")
    return vault, repo


_SEL = {"nodes": [{"span_id": "s1", "quote": "symmetric"}]}


def _no_reading_evidence(repo: Repository) -> None:
    """Assert the firewall holds: every reader/reading event is salience-only and is
    rejected by the evidence chokepoint (no mastery/diagnosis from reading).

    F8: this must actually BITE -- with the enlarged READING_EVENT_KINDS (F1) the
    journeys write real reader rows, so we require a nonzero row count rather than
    letting an empty log make the assertion vacuous."""

    checked = 0
    for kind in SF.READING_EVENT_KINDS:
        for ev in repo.reader_interaction_events(kind=kind):
            checked += 1
            assert SF.is_salience_only(ev)  # the row itself carries the stamp
            with __import__("pytest").raises(SalienceEvidenceRejected):
                reject_salience(ev)
    assert checked > 0, "no reader/reading rows were checked -- firewall assertion was vacuous"


# ── Journey 2: quick insight capture (§15.7) ──────────────────────────────────

def test_journey2_quick_insight_capture(tmp_path):
    _vault, repo = _setup(tmp_path)
    # 1-2: select a passage + interpretation, choose help_me_remember.
    receipt = RC.invoke_preset(
        repo, preset="help_me_remember", source_id="src1", revision_id="rev1",
        extraction_id="ext1", client_idempotency_key="j2", raw_selection=_SEL,
        learner_text="symmetry forces real eigenvalues", subject_id="s1", clock=_CLOCK,
    )
    # 3: durable acknowledgement + a VISIBLE arc immediately.
    assert receipt["receipt"] == "acknowledged"
    assert receipt["commitment_id"] and receipt["arc_id"]
    assert receipt["arc"]["current_stage"] == "comprehend"
    assert repo.annotation_head(receipt["annotation_id"]) is not None
    # 4: continue reading while ONE bounded proposal job runs.
    RC.drain_outbox(repo)
    assert len(repo.reader_requests_for_source("src1")) == 1
    # 5: accept the activity with a single confirmation (idempotent replay = same).
    again = RC.invoke_preset(
        repo, preset="help_me_remember", source_id="src1", revision_id="rev1",
        extraction_id="ext1", client_idempotency_key="j2", raw_selection=_SEL,
        learner_text="symmetry forces real eigenvalues", subject_id="s1", clock=_CLOCK,
    )
    assert again["deduplicated"] is True and again["commitment_id"] == receipt["commitment_id"]
    # 6-7: after a (simulated) delayed cold retrieval, restore exact source + annotation.
    restored = REST.restore(repo, source_id="src1", extraction_id="ext1")
    entry = restored["annotations"][0]
    assert entry["learner_text"] == "symmetry forces real eigenvalues"
    assert entry["source_text"] == "A real square matrix is symmetric when A^T = A."
    _no_reading_evidence(repo)


# ── Journey 1: reading-first first session (§15.8) ────────────────────────────

def test_journey1_reading_first_session(tmp_path):
    vault, repo = _setup(tmp_path)
    # Open the source: render view works with the model worker OFF.
    from learnloop.services import source_render_views as RV
    view = RV.resolve_or_create_render_view(repo, extraction_id="ext1", revision_id="rev1")
    payload = RV.render_payload(repo, view["id"])
    assert payload["blocks"]
    # One Ask (deterministic stub, no live model).
    ask = RD.ask(vault, repo, RD.StubReaderClient(answer_md="Because A = A^T."),
                 extraction_id="ext1", span_id="s1", question_md="Why real eigenvalues?",
                 clock=_CLOCK)
    assert ask["answer_md"]
    # One commit -> leaves with a durable annotation + commitment + arc.
    receipt = RC.invoke_preset(
        repo, preset="test_me_later", source_id="src1", revision_id="rev1", extraction_id="ext1",
        client_idempotency_key="j1", raw_selection=_SEL, subject_id="s1", clock=_CLOCK,
    )
    assert receipt["commitment_id"] and receipt["arc_id"]
    # test_me_later defaults to hold_at_target (§16); its arc never auto-activates.
    arc = ARC.project_arc(repo, arc_id=receipt["arc_id"])
    assert arc["policy"] == "hold_at_target"
    # No mastery/diagnosis is claimed from reading behavior.
    _no_reading_evidence(repo)


# ── Journey 7: tutor exchange -> durable knowledge (§15.9) ─────────────────────

def test_journey7_tutor_exchange_to_durable(tmp_path):
    vault, repo = _setup(tmp_path)
    # Ask from a span -> citation-valid answer (stub).
    ask = RD.ask(vault, repo, RD.StubReaderClient(answer_md="A symmetric matrix equals its transpose."),
                 extraction_id="ext1", span_id="s1", question_md="Define symmetric.",
                 answer_mode="answer_directly", clock=_CLOCK)
    assert ask["citations"]  # citation-valid
    # Add the learner's OWN Q+A, explicitly commit it -> pinned learner-authored card.
    authored = AUTH.author_qa(
        repo, question="When is A symmetric?", answer="When A^T = A.",
        source_id="src1", revision_id="rev1", client_idempotency_key="j7", clock=_CLOCK,
    )
    assert authored["authorship"] == "learner" and authored["pinned"] is True
    # An AI transfer sibling never impersonates the learner.
    sibling = AUTH.mint_ai_sibling(
        repo, family_id=authored["family_id"],
        predecessor_card_version_id=authored["card_version_id"],
        question="transfer variant", answer="...", clock=_CLOCK,
    )
    assert sibling["authorship"] == "ai"
    # Later cold review with the exchange hidden, then restore with provenance distinct.
    restored = REST.restore(repo, source_id="src1", extraction_id="ext1")
    assert restored["observation_mutated"] is False
    _no_reading_evidence(repo)


# ── Annotation survival across re-extraction (end-to-end) ──────────────────────

def test_annotation_survival_across_reextraction(tmp_path):
    _vault, repo = _setup(tmp_path)
    # Capture (annotate) a sub-block through the reader spine.
    RC.capture(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
               action="interpretation", client_idempotency_key="a1", raw_selection=_SEL,
               learner_text="note", clock=_CLOCK)
    # A second annotation whose text will DRIFT away on re-extraction.
    tr = ANN.translate_selection(repo, extraction_id="ext1",
                                 raw_selection={"nodes": [{"span_id": "s2", "quote": "spectral"}]})
    ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                          annotation_type="highlight", translation=tr, clock=_CLOCK)
    # Re-extract with a modified marker output: s1 text stable (new span id), s2 replaced.
    drift = [
        DocumentBlock.build(span_id="n1", block_type="Text",
                            text="A real square matrix is symmetric when A^T = A.", ordinal=1),
        DocumentBlock.build(span_id="n2", block_type="Text",
                            text="Completely rewritten paragraph about determinants.", ordinal=2),
    ]
    _persist(repo, _ir(drift, extractor_version="2"), revision_id="rev1", extraction_id="ext2")
    summary = ANN.reanchor_annotations_for_source(
        repo, source_id="src1", new_extraction_id="ext2", review_batch=10,
    )
    # The stable annotation survives (reanchored); the drifted one enters review.
    assert summary["reanchored"] == 1
    assert summary["needs_reanchor"] == 1
    review = REST.restore(repo, source_id="src1", extraction_id="ext2")["anchor_needs_review"]
    assert len(review) == 1  # the flagged annotation surfaces for manual review


# ── Replay / operations (§15.10) ──────────────────────────────────────────────

def test_arc_and_salience_heads_rebuild_deterministically(tmp_path):
    # F7: a REAL §15.10 rebuild -- corrupt the durable log / cached inputs, rebuild
    # from events, and assert equality with the pre-corruption projection (not the
    # vacuous f(x) == f(x)).
    import random

    _vault, repo = _setup(tmp_path)
    receipt = RC.invoke_preset(
        repo, preset="help_me_remember", source_id="src1", revision_id="rev1", extraction_id="ext1",
        client_idempotency_key="r1", raw_selection=_SEL, subject_id="s1", clock=_CLOCK,
    )
    arc_id = receipt["arc_id"]
    # Advance one stage so the arc head is a non-trivial projection over the log.
    ARC.advance_arc(
        repo, arc_id=arc_id, stage="comprehend",
        evidence_receipt={"evidence_receipt": "e1", "decision_id": "d1"}, clock=_CLOCK,
    )
    pre = ARC.project_arc(repo, arc_id=arc_id)  # pre-corruption head
    assert "comprehend" in pre["reached_stages"]

    # Corrupt the append-only arc log with rows a naive materialized head might have
    # folded in: a spurious DUPLICATE of an already-reached stage (bypassing the
    # receipt-key dedup) and an unknown-kind row. A pure dedup-fold ignores both.
    with repo.connection() as c:
        c.execute(
            "INSERT INTO commitment_arc_events(id, arc_id, event_ordinal, kind, "
            "detail_json, receipt_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("junk_dup", arc_id, 900, "stage_reached", '{"stage": "comprehend"}', None,
             "2099-01-01T00:00:00Z"),
        )
        c.execute(
            "INSERT INTO commitment_arc_events(id, arc_id, event_ordinal, kind, "
            "detail_json, receipt_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("junk_kind", arc_id, 901, "prime_offered", '{"stage": "transfer"}', None,
             "2099-01-01T00:00:00Z"),
        )
        c.commit()
    rebuilt = ARC.project_arc(repo, arc_id=arc_id)  # rebuild from the corrupted log
    assert rebuilt == pre  # the spurious/unknown rows are inert on rebuild

    # Salience head is a pure fold over the reader event stream (§8.2). Seed a few
    # reader signals so the log is non-trivial, then assert an order-invariant rebuild.
    from learnloop.services.activities import log_interaction_event
    for subject in ("s1", "s2", "s1"):
        log_interaction_event(repo, kind="reader_highlight", subject_type="reader_span",
                              subject_id=subject, clock=_CLOCK)
    log_interaction_event(repo, kind="reader_view_opened", subject_type="reader_span",
                          subject_id="s2", clock=_CLOCK)
    events = repo.reader_interaction_events()
    assert len(events) >= 4
    pre_sal = SF.salience_projection_v1(events)
    shuffled = list(events)
    random.Random(7).shuffle(shuffled)
    assert shuffled != events  # the log order actually changed
    assert SF.salience_projection_v1(shuffled) == pre_sal  # order-invariant rebuild
    assert pre_sal["authority_class"] == SF.SALIENCE_ONLY
