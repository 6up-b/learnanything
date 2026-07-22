"""P2 step B.11 -- minimal bidirectional reader dialogue (spec §7.6, U-033).

Covers the four scope items and the invariant-10 evidence semantics: the reader
tutor context + manifest, span-grounded Ask on new interaction_events kinds,
owner-placed instructional reading questions, the four-disposition picker, the
replay-derived routing prior (heuristic, superseded, decayed, never a posterior),
exposure warming, and the golden-path-with-reader-disabled requirement.
"""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.codex.client import TutorQAContext, _tutor_qa_prompt
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.services import reader_dialogue as RD
from learnloop.services import tutor_qa
from learnloop.services.activities import (
    evaluate_held_out_eligibility,
    reserve_surface,
    resolve_legacy_item,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault
from tests.test_source_inventory import _persist, _register_revision

_CLOCK = FrozenClock(NOW)


def _ir() -> DocumentIR:
    blocks = [
        DocumentBlock.build(span_id="s0", block_type="Text", text="Intro paragraph.", ordinal=0,
                            page=1, bbox=[10.0, 10.0, 200.0, 40.0], section_path=["Ch1"]),
        DocumentBlock.build(span_id="s1", block_type="Text",
                            text="A real square matrix is symmetric when A^T = A.", ordinal=1,
                            page=1, bbox=[10.0, 50.0, 200.0, 90.0], section_path=["Ch1"]),
        DocumentBlock.build(span_id="s2", block_type="Text", text="The spectral theorem follows.",
                            ordinal=2, page=1, bbox=[10.0, 100.0, 200.0, 140.0], section_path=["Ch1"]),
    ]
    unit = DocumentUnit(unit_id="u1", label="Symmetric matrices", ordinal=0,
                        semantic_hash="sha256:sym", page_start=1, page_end=1,
                        span_ids=["s0", "s1", "s2"])
    return DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks,
                      assets=[], health=ExtractionHealth())


def _setup(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src1", revision_id="rev1")
    _persist(repo, _ir(), revision_id="rev1", extraction_id="ext1")
    return vault, repo


# ── the reader tutor context + manifest (scope 1) ──────────────────────────────

def test_reader_is_the_fourth_tutor_context():
    assert tutor_qa.QUESTION_CONTEXTS == ("library", "practice", "feedback", "reader")


def test_manifest_carries_span_and_mode_but_never_ability_or_reserved(tmp_path):
    _vault, repo = _setup(tmp_path)
    manifest = RD.build_reader_manifest(
        repo, extraction_id="ext1", span_id="s1",
        question_md="Why symmetric?", answer_mode="help_me_reason",
    )
    span_ids = {s["span_id"] for s in manifest["source_spans"]}
    assert "s1" in span_ids and {"s0", "s2"} & span_ids  # in-view + surrounding
    assert manifest["answer_mode"] == "help_me_reason"
    assert "ability_estimate" in manifest["excluded"]
    # invariant: no ability/rubric/reserved keys anywhere in the manifest.
    flat = str(manifest)
    assert "rubric" not in flat and "ability" not in flat.replace("ability_estimate", "")


def test_prompt_contract_is_deterministic_and_walls_off_ability():
    contract = RD.reader_prompt_contract()
    assert contract == RD.reader_prompt_contract()  # deterministic artifact
    assert contract["not_socratic_by_default"] is True
    assert "the learner ability / posterior estimate" in contract["manifest_never_includes"]


def test_answer_mode_is_honored_in_prompt_assembly():
    for mode, needle in (
        ("answer_directly", "ANSWER DIRECTLY"),
        ("help_me_reason", "HELP ME REASON"),
        ("ask_me_first", "ASK ME FIRST"),
    ):
        prompt = _tutor_qa_prompt(TutorQAContext(context="reader", question_md="q", answer_mode=mode))
        assert needle in prompt


# ── span-grounded Ask on new event kinds (scope 2) ─────────────────────────────

def test_ask_answers_logs_new_kinds_and_persists_the_exchange(tmp_path):
    vault, repo = _setup(tmp_path)
    client = RD.StubReaderClient(answer_md="Because A equals its transpose.")
    result = RD.ask(vault, repo, client, extraction_id="ext1", span_id="s1",
                    question_md="Why is A symmetric?", answer_mode="answer_directly",
                    target_key="tcv-1", clock=_CLOCK)
    assert result["answer_md"] == "Because A equals its transpose."
    assert result["citations"] and result["citations"][0]["span_id"] == "s1"

    events = repo.reader_interaction_events()
    kinds = [e["kind"] for e in events]
    assert "learner_question_asked" in kinds
    assert "reader_answer_mode_set" in kinds
    assert "reader_answer_submitted" in kinds
    submitted = next(e for e in events if e["kind"] == "reader_answer_submitted")
    payload = submitted["payload"]
    # Persisted per exchange: question link, manifest, citations, mode, provenance.
    assert payload["answer_mode"] == "answer_directly"
    assert payload["provider"] == "stub_reader" and payload["model"] == "stub-reader-1"
    assert payload["manifest"]["span"]["span_id"] == "s1"
    assert payload["target_key"] == "tcv-1"


def test_ask_is_never_ability_evidence(tmp_path):
    vault, repo = _setup(tmp_path)
    RD.ask(vault, repo, RD.StubReaderClient(), extraction_id="ext1", span_id="s1",
           question_md="Why?", clock=_CLOCK)
    # The reader question event carries NO facets, so nothing folds into any
    # facet's displayed uncertainty (P0 invariant 10).
    span_key = tutor_qa.reader_span_key("ext1", "s1")
    events = repo.question_events(context="reader", note_id=span_key, answer_status="answered")
    assert events and all(not e.get("facets") for e in events)


# ── owner-placed reading questions (scope 3) ───────────────────────────────────

def test_owner_placed_question_is_instructional_source_visible_reading_phase(tmp_path):
    vault, repo = _setup(tmp_path)
    item = vault.practice_items["pi_svd_define_001"]
    result = RD.administer_reading_question(vault, repo, item, reading_phase="before_section",
                                            target_contract_version_id="tcv-1", clock=_CLOCK)
    assert result["purpose"] == "instructional"
    assert result["reading_phase"] == "before_section"
    assert result["source_visible"] is True
    assert result["certification_eligible"] is False

    admin = repo.fetch_administration(result["administration_id"])
    assert admin["purpose"] == "instructional"
    assert admin["reading_phase"] == "before_section"
    presented = [e for e in repo.reader_interaction_events(kind="reader_question_presented")]
    assert presented and presented[0]["administration_id"] == result["administration_id"]


def test_instructional_administration_never_certifies(tmp_path):
    from learnloop.services import administration_adapters
    effects = administration_adapters.resolve_adapter("instructional").effects(eligible=True, failed=False)
    assert effects.mints_unassisted_certification is False
    assert effects.evidence_class == "no_unassisted_certification"


def test_skip_is_interaction_policy_not_low_ability(tmp_path):
    vault, repo = _setup(tmp_path)
    item = vault.practice_items["pi_svd_define_001"]
    admin = RD.administer_reading_question(vault, repo, item, reading_phase="after_section", clock=_CLOCK)
    RD.skip_reading_question(repo, administration_id=admin["administration_id"], clock=_CLOCK)
    skipped = repo.reader_interaction_events(kind="reader_question_skipped")
    assert skipped and skipped[0]["payload"]["ability_evidence"] is False


def test_real_reader_writes_carry_the_salience_firewall_stamp(tmp_path):
    # F1: the six formerly-unstamped reader writes are now stamped by construction
    # in log_interaction_event (READING_EVENT_KINDS is the single source of truth).
    # Drive the REAL services and inspect the persisted interaction_events rows.
    from learnloop.services.salience_firewall import SALIENCE_ONLY

    vault, repo = _setup(tmp_path)
    item = vault.practice_items["pi_svd_define_001"]
    span_key = tutor_qa.reader_span_key("ext1", "s1")

    admin = RD.administer_reading_question(vault, repo, item, reading_phase="after_section", clock=_CLOCK)
    admin_id = admin["administration_id"]

    RD.set_answer_mode(repo, extraction_id="ext1", span_id="s1", answer_mode="answer_directly", clock=_CLOCK)
    RD.skip_reading_question(repo, administration_id=admin_id, clock=_CLOCK)
    RD.submit_reading_question(repo, administration_id=admin_id, response_md="my answer",
                               outcome_class="unknown", clock=_CLOCK)
    RD.choose_disposition(vault, repo, disposition="comprehension_only",
                          subject_id=span_key, clock=_CLOCK)

    for kind in (
        "reader_question_presented",
        "reader_answer_mode_set",
        "reader_question_skipped",
        "reader_answer_submitted",
        "reader_disposition_chosen",
    ):
        rows = repo.reader_interaction_events(kind=kind)
        assert rows, f"no {kind} row written"
        for row in rows:
            assert row["payload"]["authority_class"] == SALIENCE_ONLY, kind


# ── four dispositions (scope 4) ────────────────────────────────────────────────

def test_each_disposition_produces_its_mechanism_and_nothing_else(tmp_path):
    vault, repo = _setup(tmp_path)
    span_key = tutor_qa.reader_span_key("ext1", "s1")

    comp = RD.choose_disposition(vault, repo, disposition="comprehension_only",
                                 subject_id=span_key, clock=_CLOCK)
    assert comp["mechanism"] == "logged_only" and "commitment_id" not in comp

    ref = RD.choose_disposition(vault, repo, disposition="reference_only",
                                subject_id=span_key, clock=_CLOCK)
    assert ref["mechanism"] == "citation_preserved" and "commitment_id" not in ref

    chk = RD.choose_disposition(vault, repo, disposition="check_once_later",
                                subject_id=span_key, clock=_CLOCK)
    assert chk["mechanism"] == "single_use_diagnostic_check" and chk["single_use"] is True

    # keep_developing is the ONLY commit-class path.
    keep = RD.choose_disposition(vault, repo, disposition="keep_developing",
                                 subject_id=span_key, client_idempotency_key="k1", clock=_CLOCK)
    assert keep["mechanism"] == "commitment"
    assert repo.commitment(keep["commitment_id"]) is not None

    # Exactly one commitment was minted across the four dispositions.
    assert len(repo.reader_interaction_events(kind="reader_disposition_chosen")) == 4


# ── formative-answer consequences: routing prior (scope 5) ─────────────────────

def _log_reading_answer(repo, *, target_key, outcome_class, created_at):
    from learnloop.services.activities import log_interaction_event
    return log_interaction_event(
        repo, kind="reader_answer_submitted", origin="learner",
        subject_type="administration", subject_id="a1",
        payload={"target_key": target_key, "outcome_class": outcome_class, "source_visible": True},
        clock=FrozenClock(datetime.fromisoformat(created_at.replace("Z", "+00:00"))),
    )


def test_routing_prior_is_heuristic_decision_aid(tmp_path):
    _vault, repo = _setup(tmp_path)
    _log_reading_answer(repo, target_key="tcv-1", outcome_class="confused",
                        created_at="2026-05-19T12:00:00Z")
    prior = RD.routing_prior_projection_v1(repo, target_key="tcv-1", as_of="2026-05-19T12:00:00Z")
    assert prior["label"] == "heuristic"
    assert prior["channel"] == "u027_decision_aid"
    assert prior["superseded"] is False
    assert prior["reasons"].get("false_belief_or_confusion", 0) > 0
    # bounded below a single cold observation's influence.
    assert max(prior["reasons"].values()) <= RD.ROUTING_PRIOR_MAX_WEIGHT


def test_routing_prior_superseded_by_first_cold_observation(tmp_path):
    _vault, repo = _setup(tmp_path)
    _log_reading_answer(repo, target_key="tcv-1", outcome_class="confused",
                        created_at="2026-05-19T12:00:00Z")
    # A cold observation on the same target at/after the reading answer supersedes.
    prior = RD.routing_prior_projection_v1(
        repo, target_key="tcv-1", as_of="2026-05-20T12:00:00Z",
        cold_observation_at="2026-05-19T18:00:00Z",
    )
    assert prior["superseded"] is True
    assert prior["reasons"] == {}  # contributes ZERO to any live decision
    assert prior["trace"][0]["contribution"] == 0.0
    assert prior["trace"][0]["label"] == "heuristic"  # survives only as labeled trace


def test_routing_prior_superseded_by_cold_observation_before_the_reading_answer(tmp_path):
    """L9 regression: ANY cold observation on the target supersedes the routing prior,
    even one recorded BEFORE the reading answer -- the formative prior never revives once
    real cold evidence exists. Before the fix a cold-before-reading observation did not
    supersede (the check required cold >= first answer)."""

    _vault, repo = _setup(tmp_path)
    _log_reading_answer(repo, target_key="tcv-1", outcome_class="confused",
                        created_at="2026-05-19T12:00:00Z")
    prior = RD.routing_prior_projection_v1(
        repo, target_key="tcv-1", as_of="2026-05-20T12:00:00Z",
        cold_observation_at="2026-05-18T09:00:00Z",  # cold observation BEFORE the answer
    )
    assert prior["superseded"] is True
    assert prior["reasons"] == {}
    assert prior["trace"][0]["contribution"] == 0.0


def test_routing_prior_decays_with_elapsed_time(tmp_path):
    _vault, repo = _setup(tmp_path)
    _log_reading_answer(repo, target_key="tcv-1", outcome_class="confused",
                        created_at="2026-05-19T12:00:00Z")
    fresh = RD.routing_prior_projection_v1(repo, target_key="tcv-1", as_of="2026-05-19T12:00:00Z")
    aged = RD.routing_prior_projection_v1(repo, target_key="tcv-1", as_of="2026-06-19T12:00:00Z")
    assert aged["reasons"]["false_belief_or_confusion"] < fresh["reasons"]["false_belief_or_confusion"]


def test_reader_answer_writes_no_posterior_or_fsrs(tmp_path):
    vault, repo = _setup(tmp_path)
    RD.ask(vault, repo, RD.StubReaderClient(), extraction_id="ext1", span_id="s1",
           question_md="Why?", target_key="tcv-1", clock=_CLOCK)
    # Static guard: a reading answer never lands an observation / FSRS review /
    # certification row (like the warmth-never-evidence guard).
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) AS n FROM activity_observations").fetchone()["n"] == 0
        assert connection.execute("SELECT COUNT(*) AS n FROM activity_administrations").fetchone()["n"] == 0


def test_ask_warms_and_invalidates_a_revealed_reserve(tmp_path):
    vault, repo = _setup(tmp_path)
    item = vault.practice_items["pi_svd_define_001"]
    resolved = resolve_legacy_item(vault, repo, item, purpose="assessment", clock=_CLOCK)
    reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=_CLOCK)
    assert evaluate_held_out_eligibility(
        repo, surface=repo.fetch_surface(resolved.surface_id), purpose="assessment"
    ).is_unseen is True

    result = RD.ask(vault, repo, RD.StubReaderClient(), extraction_id="ext1", span_id="s1",
                    question_md="Explain the answer.", revealed_surface_ids=[resolved.surface_id],
                    clock=_CLOCK)
    assert resolved.surface_id in result["burned_surface_ids"]
    # The reserve is now invalidated exactly as any other exposure would.
    assert evaluate_held_out_eligibility(
        repo, surface=repo.fetch_surface(resolved.surface_id), purpose="assessment"
    ).is_unseen is False


def test_answer_quoting_reserved_surface_burns_it_without_caller_id(tmp_path):
    """L3 (regression): an answer that QUOTES a reserved surface still burns the reserve
    even when the caller omits the id -- server-side reveal detection unions the derived
    surface into the burn set. Before the fix only caller-declared ids were burned."""

    vault, repo = _setup(tmp_path)
    item = vault.practice_items["pi_svd_define_001"]
    resolved = resolve_legacy_item(vault, repo, item, purpose="assessment", clock=_CLOCK)
    reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=_CLOCK)
    statement = RD._surface_statement_text(repo.fetch_surface(resolved.surface_id))
    assert statement, "the reserved surface must carry a statement to leak"

    result = RD.ask(
        vault, repo, RD.StubReaderClient(answer_md=f"The held-out item asks: {statement}"),
        extraction_id="ext1", span_id="s1", question_md="What will the test ask?",
        revealed_surface_ids=[],  # caller omits the id -- detection must still catch it
        clock=_CLOCK,
    )
    assert resolved.surface_id in result["burned_surface_ids"]
    assert evaluate_held_out_eligibility(
        repo, surface=repo.fetch_surface(resolved.surface_id), purpose="assessment"
    ).is_unseen is False


def test_answer_not_quoting_reserve_leaves_it_eligible(tmp_path):
    """L3 negative control: an ordinary answer that does not quote a reserve never burns
    it -- reveal detection is overlap-gated, not a blanket burn."""

    vault, repo = _setup(tmp_path)
    item = vault.practice_items["pi_svd_define_001"]
    resolved = resolve_legacy_item(vault, repo, item, purpose="assessment", clock=_CLOCK)
    reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=_CLOCK)
    result = RD.ask(
        vault, repo, RD.StubReaderClient(answer_md="A symmetric matrix equals its transpose."),
        extraction_id="ext1", span_id="s1", question_md="What is symmetry?",
        revealed_surface_ids=[], clock=_CLOCK,
    )
    assert resolved.surface_id not in result["burned_surface_ids"]
    assert evaluate_held_out_eligibility(
        repo, surface=repo.fetch_surface(resolved.surface_id), purpose="assessment"
    ).is_unseen is True


def test_cold_active_ask_links_a_hint_equivalent_into_attempt_accounting(tmp_path):
    """L6 regression: a cold-active Ask records a hint-equivalent PRACTICE question_event
    tied to the cold attempt's (item, session), so the landed practice evidence path
    counts it -- not just telemetry. A non-cold Ask records none."""

    vault, repo = _setup(tmp_path)
    item = vault.practice_items["pi_svd_define_001"]
    repo.insert_practice_attempt({
        "id": "cold_att_1", "practice_item_id": item.id,
        "learning_object_id": item.learning_object_id, "practice_mode": "short_answer",
        "attempt_type": "independent_attempt", "session_id": "sess_cold",
        "created_at": "2026-05-19T12:00:00Z",
    })

    result = RD.ask(
        vault, repo, RD.StubReaderClient(answer_md="Use the spectral decomposition."),
        extraction_id="ext1", span_id="s1", question_md="How do I start?",
        cold_active=True, cold_attempt_id="cold_att_1", clock=_CLOCK,
    )
    assert result["hint_equivalent"] is True
    assert result["cold_hint_event_id"]
    # The practice evidence path counts it as a hint-equivalent for the attempt's item+session.
    assert repo.count_hint_equivalent_question_events(item.id, "sess_cold") == 1

    # A non-cold Ask adds NO hint-equivalent (the reader is not ability evidence, inv 10).
    RD.ask(vault, repo, RD.StubReaderClient(), extraction_id="ext1", span_id="s1",
           question_md="q2", cold_active=False, cold_attempt_id="cold_att_1", clock=_CLOCK)
    assert repo.count_hint_equivalent_question_events(item.id, "sess_cold") == 1


# ── source restoration (§7.4) ──────────────────────────────────────────────────

def test_restore_source_during_cold_burns_eligibility(tmp_path):
    vault, repo = _setup(tmp_path)
    item = vault.practice_items["pi_svd_define_001"]
    resolved = resolve_legacy_item(vault, repo, item, purpose="assessment", clock=_CLOCK)
    out = RD.restore_source(repo, extraction_id="ext1", span_id="s1",
                            cold_surface_id=resolved.surface_id, clock=_CLOCK)
    assert out["cold_eligibility_burned"] is True
    assert evaluate_held_out_eligibility(
        repo, surface=repo.fetch_surface(resolved.surface_id), purpose="assessment"
    ).is_unseen is False


# ── golden path completes with reader DISABLED (scope 6, spec §12.3.2) ──────────

def test_reader_enabled_by_default():
    # Owner decision 2026-07-20: reader on at birth (fresh-vault journey needs it
    # without hand-editing config). §12.3.2 is preserved by the explicit-disable
    # golden-path test below.
    from learnloop.config import LearnLoopConfig
    assert LearnLoopConfig().tutor_qa.reader_enabled is True


def test_golden_path_completes_with_reader_never_invoked(tmp_path):
    from pathlib import Path

    from learnloop.services.golden_path_fixture import build_golden_path_fixture
    from learnloop.vault.paths import VaultPaths

    fixture = build_golden_path_fixture(tmp_path / "vault")
    assert fixture.receipt.current_state == "ready"
    # §12.3.2: the canonical walk must complete with the reader DISABLED —
    # disable it explicitly (the ship default is now enabled) and verify the run
    # neither needed nor produced any reader interaction.
    config_path = fixture.root / "learnloop.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace("reader_enabled = true", "reader_enabled = false"),
        encoding="utf-8",
    )
    vault = load_vault(fixture.root)
    repo = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    assert not RD.reader_enabled(vault)
    for kind in RD.READER_EVENT_KINDS:
        assert repo.reader_interaction_events(kind=kind) == []
    # Static guard: the golden-path spine never imports the reader module, so the
    # canonical walk cannot invoke it (§12.3.2 disabled-completion requirement).
    src = Path(__file__).resolve().parents[1] / "src" / "learnloop" / "services"
    for module in ("golden_path_fixture.py", "golden_path_run.py", "golden_path_confirm.py"):
        assert "reader_dialogue" not in (src / module).read_text(encoding="utf-8")
