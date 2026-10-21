"""E0 question bank, labels and adjudication with fakes (spec §5.1, §5.2)."""
from __future__ import annotations

from learnloop.experiments.contextual_embeddings import bank as B
from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.budget import E0Ledger
from learnloop.experiments.contextual_embeddings.callers import FakeRoleCaller
from tests.e0_fakes import build_e0_vault, fake_respond


def _snapshot(tmp_path, **kwargs):
    paths, repository = build_e0_vault(tmp_path)
    return C.build_snapshot(C.open_copy(paths.root), **kwargs), paths, repository


def test_the_smoke_bank_has_16_deterministic_cases_from_permitted_text(tmp_path):
    snapshot, _paths, _repository = _snapshot(tmp_path)
    first, stats = B.smoke_bank(snapshot)
    second, _ = B.smoke_bank(snapshot)
    # The tiny test vault cannot fill all 16: the shortfall is recorded, never padded with repeats.
    assert len(first) == stats["count"] <= pins.SMOKE_CASES
    assert stats["shortfall"].get("total", 0) == pins.SMOKE_CASES - len(first)
    assert len({question.query_id for question in first}) == len(first)
    assert [question.query_id for question in first] == [question.query_id for question in second]
    assert sum(1 for question in first if not question.answerable) == 2
    deictic = [question for question in first if question.stratum == "reader_deictic"]
    assert deictic and all(question.selection is not None for question in deictic)
    assert all(question.split == "smoke" for question in first)
    refs = {ref[:2] for question in first for evidence in question.evidence_sets for ref in evidence.required}
    assert all(snapshot.policy.permitted(*key) for key in refs)


def test_seeds_come_only_from_development_families(tmp_path):
    snapshot, _paths, _repository = _snapshot(tmp_path)
    book_family = snapshot.family_of_source["src_book"]
    snapshot.family_status = {**snapshot.family_status, book_family: "reserved"}
    seeds, _shortfall = B.plan_seeds(snapshot, strata={"intent_explain": 3, "direct_lookup": 2})
    assert seeds
    assert all(snapshot.unit(unit_id).source_id != "src_book" for seed in seeds for unit_id in seed.units)


def test_distant_seeds_use_references_then_shared_terms(tmp_path):
    snapshot, _paths, _repository = _snapshot(tmp_path)
    seeds, shortfall = B.plan_seeds(snapshot, strata={"distant_same_source": 1, "reader_deictic": 1})
    distant = [seed for seed in seeds if seed.stratum == "distant_same_source"]
    assert len(distant) == 1 and len(distant[0].units) == 2
    assert distant[0].link in ("reference", "shared_terms")
    assert B.plan_seeds(snapshot, strata={"distant_same_source": 1, "reader_deictic": 1}) == (seeds, shortfall)


def test_the_writer_pipeline_with_a_fake_and_its_admission(tmp_path):
    snapshot, _paths, _repository = _snapshot(tmp_path)
    ledger = E0Ledger(tmp_path / "ledger")
    caller = FakeRoleCaller(fake_respond, ledger)
    seeds, _ = B.plan_seeds(snapshot, strata={"reader_deictic": 2, "no_support": 1, "direct_lookup": 1})
    questions, stats = B.write_questions(snapshot, seeds, caller)
    assert stats["written"] == len(seeds) == len(questions)
    assert all(question.split == "development" and question.origin == "writer" for question in questions)
    assert not next(question for question in questions if question.stratum == "no_support").answerable
    assert all(question.selection is not None for question in questions if question.stratum == "reader_deictic")
    assert ledger.report()["requests"] == stats["calls"]
    assert ledger.report()["committed_usd"] == 0.0  # the writer route is the Codex subscription
    prompt = caller.calls[0][1]
    assert "Solution: apply linearity" not in prompt and "Exam question" not in prompt


def test_logged_questions_keep_their_real_selection_and_never_get_one_invented(tmp_path):
    snapshot, _paths, _repository = _snapshot(tmp_path)
    book = next(block for block in snapshot.blocks["ext_book"] if block.text.startswith("Theorem 1.2"))
    solution = next(block for block in snapshot.blocks["ext_book"] if block.text.startswith("Solution:"))
    events = [
        {"id": "e1", "question_md": "why does this step follow here?", "context": "reader",
         "source_context": {"extraction_id": "ext_book", "span_id": book.span_id}},
        {"id": "e2", "question_md": "what is a basis of a vector space?", "context": "practice", "source_context": {}},
        {"id": "e3", "question_md": "is this the solution to the exercise?", "context": "reader",
         "source_context": {"extraction_id": "ext_book", "span_id": solution.span_id}},
        {"id": "e4", "question_md": "short", "context": "reader", "source_context": {}},
    ]
    questions, counts = B.logged_bank(snapshot, events)
    assert counts["eligible"] == 2 and counts["selection_withheld"] == 1 and counts["too_short"] == 1
    reader = next(question for question in questions if question.stratum == "logged_reader")
    assert reader.selection.span_id == book.span_id
    practice = next(question for question in questions if question.stratum == "logged_practice")
    assert practice.selection is None and practice.scope == "library"


def test_two_blinded_passes_audit_plan_and_adjudication(tmp_path):
    snapshot, _paths, _repository = _snapshot(tmp_path)
    caller = FakeRoleCaller(fake_respond)
    question = B.BankQuestion("q1", "development", None, "writer", "explain", "intent_explain",
                              "Why does a linear map send the additive identity to the unique additive identity?")
    B.freeze_context(question, snapshot)
    pool = [unit.unit_id for unit in snapshot.units][:8]
    labels = B.label_question(question, pool, snapshot, caller)
    assert set(labels.passes[0]) == set(pool) == set(labels.passes[1])
    prompts = [prompt for role, prompt in caller.calls if role.startswith("label")]
    assert prompts[0] != prompts[1]  # different orders and pass numbers
    assert "R4" not in prompts[0] and "arm" not in prompts[0]
    plan = B.audit_plan([labels])
    assert plan.get("q1") in ("disagreement", "set_disagreement", "accepted_set_used_by_primary_endpoint")
    B.adjudicate(question, labels, snapshot, caller)
    assert labels.adjudicated and not labels.unresolved
    sets = B.evidence_sets_from_labels(labels, snapshot)
    assert all(evidence.required for evidence in sets)


def test_the_audit_samples_twenty_percent_of_agreements(tmp_path):
    agreed = [B.QuestionLabels(f"q{i}", ["u1"], [{"u1": "unrelated"}, {"u1": "unrelated"}], [[], []],
                               [False, False]) for i in range(10)]
    plan = B.audit_plan(agreed)
    assert len(plan) == 2 and set(plan.values()) == {"seeded_sample"}
    assert plan == B.audit_plan(agreed)


def test_the_pool_includes_every_arm_proposals_and_seeded_non_hits(tmp_path):
    snapshot, _paths, _repository = _snapshot(tmp_path)
    units = [unit.unit_id for unit in snapshot.units]
    question = B.BankQuestion("q2", "development", None, "writer", "explain", "intent_explain", "a question here",
                              proposed_units=(units[-1],))
    pool = B.pool_for(question, {"R1": units[:2], "R5_grouped": units[2:4]}, snapshot, non_hits=2)
    assert set(units[:4]) <= set(pool) and units[-1] in pool and len(pool) == 7
