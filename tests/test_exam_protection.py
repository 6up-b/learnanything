"""Exam protection (2026-10-13): one exam predicate, the five gaps, four sources bugs.

Owner rule: exams and problem sets are assessment material. They may seed
question kinds and rigor, but held-out exam material is never taught, never
shown to a model as teaching or explanation, never leaked into practice, and
never reused as an independent check once the learner has seen it.

* The one predicate (``content.sources.exam_material``) is what main's corpus
  predicates, the facet-meaning resolver and the leakage inventory read: exam
  material in ANY revision of an exam source, held-out units whatever their
  role (in a source set or not), unresolvable units failing closed.
* The gaps the sources merge listed: (a) ``post_attempt`` reopened whole exam
  extractions; (b) ``cold_administration_open`` ignored exam-reserved items;
  (c) a picked practice proposal skipped the exam-reservation check; (d) an
  import trusted a stale proposal; (e) an exposed import could still become an
  exam item or a cold check.
* The sources bugs: ``action_disagreement`` was never set; migration 193's
  comment misdescribed ``router_decision_id``; the daily envelope ignored the
  injected clock; harvest's dry run priced the rerank at the wrong setting.

Each test failed on the base commit (``e8d261405``), recorded in
``docs/reviews/exam-protection.md``.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timedelta, UTC
from decimal import Decimal
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.authoring import source_exercise_import as SEI
from learnloop.content.authoring.practice_leakage import (
    build_cross_source_spans,
    build_held_out_inventory,
    held_out_spans,
    screen_practice_payload,
)
from learnloop.content.facet_identity.authority import CitationResolver
from learnloop.content.sources.exam_material import exam_material, item_exam_status
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.connection import connect
from learnloop.ids import new_ulid
from learnloop.ingest.locators import format_block_span
from learnloop.instructional.exercises import exercise_candidates
from learnloop.instructional.policy import caller_for, cold_administration_open
from learnloop.instructional.practice import propose_practice, record_proposal_selection
from learnloop.source_retrieval.corpus import exam_withheld, teaching_exclusions
from learnloop.source_retrieval.find_sources import find_sources, find_sources_for_caller, scope_for
from learnloop.source_retrieval.policy import PolicyRefused, derive_policy
from learnloop.vault.loader import load_vault
from learnloop.vault.models import CanonicalExercise
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault.yaml_io import read_yaml
from tests.source_retrieval_fakes import EXAM_QUESTION, seed_source
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded, service_clients, set_config
from tests.test_source_inventory import _block, _ir, _persist

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def textbook(tmp_path):
    return build_textbook_vault(tmp_path / "vault")


def _exam_question_span(repository) -> str:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id='ext_exam' AND text LIKE 'Exam question%'"
        ).fetchone()
    return str(row[0])


def _second_exam_revision(repository) -> tuple[str, str]:
    """A re-import of the exam the source set does not pin: ``rev_exam_2`` / ``ext_exam_2``."""

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_exam_2", "src_exam", "sha256:exam2", None, "2026-02-01T00:00:00Z"))
        connection.commit()
    ir = _ir([("exam_q2", "Final problems", [_block("s1", "Exam question 2: invert the matrix [[2,1],[1,1]].")],
               "sha256:exam_q2", 1)])
    _persist(repository, ir, revision_id="rev_exam_2", extraction_id="ext_exam_2")
    return "ext_exam_2", "s1"


# --- the one predicate -------------------------------------------------------------------------


def test_exam_material_in_any_revision_of_an_exam_source_is_exam_to_every_reader(textbook):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    key = _second_exam_revision(repository)

    # The facet-meaning resolver: the unpinned revision's span is exam
    # material, never an "uncited" (confirmable) reword.
    resolver = CitationResolver.for_vault(repository, vault)
    assert resolver.exam_material({"extraction_id": key[0], "span_id": key[1]})
    # main's corpus predicate (it already counted every revision) agrees ...
    assert exam_withheld(vault, repository, [key]) == frozenset({key})
    # ... because both read the one predicate, which says which revision.
    verdict = exam_material(vault, repository).verdict(*key)
    assert verdict.exam and verdict.revision_id == "rev_exam_2" and verdict.source_id == "src_exam"
    assert verdict.pinned_revision_ids == ("rev_exam",) and "exam_member" in verdict.reasons


def test_a_held_out_unit_of_any_role_joins_the_leakage_inventory(textbook):
    paths, repository, spans = textbook
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    vault = loaded(paths)

    keys = {(span.extraction_id, span.span_id) for span in held_out_spans(vault, repository)}
    assert {("ext_text", span) for span in spans["exercises"]} <= keys
    exercise_text = "An eigenvalue t satisfies 3t + 5 = 20; solve 3x + 5 = 20 for x to find the eigenvalue."
    findings = screen_practice_payload({"prompt": exercise_text}, build_held_out_inventory(vault, repository))
    assert any(finding["kind"] == "wording" for finding in findings)


def test_an_unresolvable_held_out_mark_fingerprints_its_whole_extraction(textbook):
    paths, repository, spans = textbook
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"no_such_unit": "held_out_evaluation"})
    vault = loaded(paths)

    keys = {(span.extraction_id, span.span_id) for span in held_out_spans(vault, repository)}
    assert ("ext_text", spans["worked"][1]) in keys  # fail closed: every block of the extraction
    assert "ext_text" in exam_material(vault, repository).held_out.extractions


def test_held_out_and_exam_role_picks_count_outside_any_source_set(textbook):
    paths, repository, _spans = textbook
    seed_source(repository, source_id="src_loose", revision_id="rev_loose", extraction_id="ext_loose",
                title="Loose paper", units={"q": ("Questions", [("Loose question: compute 7 times 6.", 1)])})
    seed_source(repository, source_id="src_picked", revision_id="rev_picked", extraction_id="ext_picked",
                title="Picked paper", units={"p": ("Paper", [("Picked question: compute 8 times 9.", 1)])})
    save_unit_selection(repository, "ext_loose", ["q"], exam_use_modes={"q": "held_out_evaluation"})
    save_unit_selection(repository, "ext_picked", ["p"], role_override="exam")
    vault = loaded(paths)

    loose, picked = ("ext_loose", "s2"), ("ext_picked", "s2")
    assert exam_withheld(vault, repository, [loose, picked]) == frozenset({loose, picked})
    material = exam_material(vault, repository)
    assert material.is_held_out(*loose) and not material.is_held_out(*picked)
    assert "ext_picked" in teaching_exclusions(vault, repository).extractions


def test_cross_source_teaching_spans_never_carry_exam_material(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    exam = ("ext_exam", _exam_question_span(repository))
    taught = ("ext_text", spans["ch5"][1])
    for key in (exam, taught):
        repository.insert_entity_source_link(
            entity_type="learning_object", entity_id="lo_matrices", locator=format_block_span(*key),
            relation="support", extraction_id=key[0], locator_scheme="block_span_v1")

    found = {(span.extraction_id, span.span_id) for span in build_cross_source_spans(vault, repository, "lo_matrices")}
    assert taught in found and exam not in found


def test_an_item_made_from_held_out_material_is_exam_material(textbook):
    paths, repository, spans = textbook
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    vault = loaded(paths)
    item = vault.practice_items["pi_eigen_1"].model_copy(update={"canonical_exercise": CanonicalExercise(
        source_id="src_text", extraction_id="ext_text", span_ids=[spans["exercises"][1]])})
    status = item_exam_status(item, material=exam_material(vault, repository))
    assert status is not None and status.held_out and status.reasons == ("exam_material",)
    reserved = item_exam_status(vault.practice_items["pi_eigen_2"], reserved={"pi_eigen_2"})
    assert reserved is not None and reserved.reasons == ("exam_reserved",)


# --- (a) post_attempt never reopens exam material ------------------------------------------------


def test_post_attempt_never_reopens_an_exam_extraction_or_an_exam_item_s_own_span(textbook):
    paths, repository, _spans = textbook
    exam = ("ext_exam", _exam_question_span(repository))
    # The item names the exam whole (a locator that is not a block) and its
    # question as its own exercise.
    repository.insert_entity_source_link(entity_type="practice_item", entity_id="pi_eigen_1",
                                         locator="heading:Midterm problems", relation="support",
                                         extraction_id="ext_exam")
    repository.insert_entity_source_link(entity_type="practice_item", entity_id="pi_eigen_1",
                                         locator=format_block_span(*exam), relation="exercise",
                                         extraction_id="ext_exam", locator_scheme="block_span_v1")
    vault = loaded(paths)
    item = vault.practice_items["pi_eigen_1"]

    scope = scope_for(vault, repository, policy="post_attempt", scope="teaching", learning_object_ids=[], item=item)
    assert "ext_exam" not in scope.extractions
    hits = find_sources(vault, repository, EXAM_QUESTION, policy="post_attempt", item=item, scope="library")
    assert exam not in {(hit["extraction_id"], hit["span_id"]) for hit in hits.hits}


# --- (b) an exam-reserved item is a cold administration ---------------------------------------------


def _reserve(repository, item_id: str, goal_id: str = "goal_exam") -> None:
    repository.insert_exam_pool_items([{"id": new_ulid(), "goal_id": goal_id, "practice_item_id": item_id,
                                        "facet_id": None, "difficulty_stratum": "mid",
                                        "reserved_at": "2026-10-13T00:00:00Z", "released_at": None}])


def test_an_exam_reserved_item_is_a_cold_administration_for_every_caller(textbook):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    assert not cold_administration_open(repository, "pi_eigen_1")
    _reserve(repository, "pi_eigen_1")

    assert cold_administration_open(repository, "pi_eigen_1")
    caller = caller_for(repository, "plan", item_id="pi_eigen_1", post_attempt=True)
    assert derive_policy(caller) == ("cold_attempt", "the item is reserved for a held-out exam")
    assert find_sources_for_caller(vault, repository, "eigenvalues", caller=caller).status == \
        "empty: cold administration"
    with pytest.raises(PolicyRefused):
        propose_practice(vault, repository, "eigenvalues", {}, caller=caller, rerank_client=FakeServiceLLM())


# --- (c) a picked proposal is re-checked against exam reservations -----------------------------------


def test_a_pick_of_an_item_reserved_since_its_proposal_is_refused_before_anything_is_recorded(textbook):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    result = propose_practice(vault, repository, "determinant rows swapped sign", {},
                              caller=caller_for(repository, "plan"), rerank_client=FakeServiceLLM())
    picked = result["items"][0]["practice_item_id"]
    _reserve(repository, picked)

    with pytest.raises(ValueError, match="reserved for a held-out exam"):
        record_proposal_selection(repository, proposal_id=result["proposal_id"], practice_item_id=picked, vault=vault)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        usage = connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE left_id=? AND right_id=?",
                                   (result["proposal_id"], picked)).fetchone()[0]
    assert usage == 0


# --- (d) an import rechecks exam and held-out status --------------------------------------------------


def test_an_import_rechecks_a_stale_proposal_before_any_paid_call(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    result = propose_practice(vault, repository, "solve for the eigenvalue x", {"kinds": "source_exercises"},
                              caller=caller_for(repository, "plan"), rerank_client=FakeServiceLLM(),
                              exercise_arm=exercise_candidates)
    entry = result["source_exercises"][0]
    # The owner holds the exercises out for evaluation after the proposal.
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    llm = FakeServiceLLM()

    outcome = SEI.import_source_exercise(paths.root, repository, extraction_id=entry["extraction_id"],
                                         span_ids=entry["span_ids"], caller="learner",
                                         proposal_id=result["proposal_id"], clients=service_clients(llm))
    assert outcome["status"] == "rejected" and outcome["reason"].startswith("exam_material"), outcome
    assert outcome["practice_item_id"] is None and llm.calls == []


# --- (e) shown material never becomes an exam item or a cold check -------------------------------------


def _expose(repository, extraction_id: str, span_id: str) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_exposure_events(id, context, extraction_id, span_id, created_at) VALUES (?,?,?,?,?)",
            ("sxe_" + new_ulid(), "reader", extraction_id, span_id, "2026-01-01T00:00:00Z"))
        connection.commit()


def _as_import(root, practice_item_id: str, *, extraction_id: str = "ext_book", span_id: str = "s2") -> None:
    """Give an item the canonical exercise an import records."""

    from learnloop.vault.paths import VaultPaths

    vault = load_vault(root)
    item = vault.practice_items[practice_item_id]
    path = next(VaultPaths(vault.root, vault.config).root.rglob(f"{practice_item_id}.yaml"))
    payload = read_yaml(path)
    payload["canonical_exercise"] = {"source_id": "src_book", "extraction_id": extraction_id,
                                     "span_ids": [span_id], "relation": "verbatim"}
    upsert_practice_item(root, payload, clock=FrozenClock(datetime(2026, 1, 1, tzinfo=UTC)))
    assert item.id == practice_item_id


def test_an_exposed_import_never_becomes_an_exam_item(tmp_path):
    from learnloop.goals.exam_pool import reserve_exam_pool
    from tests.test_exam_pool import NOW, _vault_with_items

    vault, paths, repository = _vault_with_items(tmp_path)
    _as_import(paths.root, "pi_pool_apply_mid")
    _expose(repository, "ext_book", "s2")
    with repository.connection() as connection:  # an answer revealed by the tutor, never attempted
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, source_kind, amount, created_at) VALUES (?,?,?,?,?)",
            ("rev_" + new_ulid(), "pi_pool_derive_hard", "tutor_answer", 1.0, "2026-01-01T00:00:00Z"))
        connection.commit()
    vault = load_vault(paths.root)

    report = reserve_exam_pool(vault, repository, vault.goals[0], item_count=3, clock=FrozenClock(NOW))
    assert "pi_pool_apply_mid" not in report.reserved_item_ids
    assert "pi_pool_derive_hard" not in report.reserved_item_ids
    assert {"apply", "derive"} <= set(report.uncovered_facets)


def test_an_exposed_import_never_becomes_a_certification_cold_probe(tmp_path):
    from learnloop.goals.certification_cold_probe import select_held_out_probe_item
    from tests.test_certification_cold_probe import HELD_OUT_ITEM, _certify

    paths, vault, repository, certificate = _certify(tmp_path)
    assert select_held_out_probe_item(vault, repository, certificate).practice_item_id == HELD_OUT_ITEM
    _as_import(paths.root, HELD_OUT_ITEM)
    _expose(repository, "ext_book", "s2")

    selection = select_held_out_probe_item(load_vault(paths.root), repository, certificate)
    assert selection.practice_item_id is None


def test_a_revealed_item_is_never_the_cold_retry(tmp_path):
    from learnloop.diagnosis.remediation import (
        prescribe_remediation,
        start_remediation_episode,
        start_remediation_treatment,
    )
    from tests.test_remediation_cold_retry import NOW, _setup

    def treat(root):
        vault, repository, misconception_id = _setup(root)
        episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
        prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
        return repository, lambda: start_remediation_treatment(vault, repository, episode["id"],
                                                               clock=FrozenClock(NOW))

    _repository, start = treat(tmp_path / "first")
    cold_item = start()["cold_item_id"]
    assert cold_item is not None

    repository, start = treat(tmp_path / "second")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, source_kind, amount, created_at) VALUES (?,?,?,?,?)",
            ("rev_" + new_ulid(), cold_item, "tutor_answer", 1.0, "2026-01-01T00:00:00Z"))
        connection.commit()
    assert start()["cold_item_id"] != cold_item


# --- the sources bugs --------------------------------------------------------------------------------


def test_a_priced_causal_decision_carries_the_live_repair_class(tmp_path):
    from learnloop.instructional.needs import pending_causal_decision
    from tests.test_causal_orchestrator import LO_ID, _seed_factor, _vault

    vault, repository, _root = _vault(tmp_path)
    factor_id, first, second = _seed_factor(repository)
    set_id = repository.insert_hypothesis_set(
        learning_object_id=LO_ID, probe_phase_id="p", hypotheses=[{"label": first}, {"label": second}],
        prior={first: 0.5, second: 0.4, "H_OTHER": 0.1}, algorithm_version="mvp-0.6",
        prior_basis="support_weighted")
    repository.insert_probe_episode(learning_object_id=LO_ID, status="in_progress", trigger="manual",
                                    hypothesis_set_id=set_id, active_state_segment_id=None,
                                    algorithm_version="mvp-0.6")
    repository.insert_causal_probe_decision_receipt(
        factor_id=factor_id, decision="skip_common_repair", reason="common_repair_cover",
        repair_status="safe_common_repair_available", decision_policy_version="test", formula_version="test",
        inputs={}, parameters={}, repair_class_ids=["repair:method"], attempt_id="att_orchestrator")

    decision = pending_causal_decision(vault, repository, {"attempt_id": "att_orchestrator"})
    assert decision["hypothesis_set_id"] == set_id
    assert decision["action_by_slot"] == {first: "repair:recall", second: "repair:method"}
    assert decision["live_repair_class"] == "repair:method"


def test_migration_193_describes_router_decision_id_as_the_serving_block_s_decision():
    lines = (REPO / "migrations" / "193_retrieval_interventions.sql").read_text(encoding="utf-8").splitlines()
    column = next(index for index, line in enumerate(lines) if line.strip().startswith("router_decision_id TEXT"))
    above = []
    for line in reversed(lines[:column]):
        if not line.strip().startswith("--"):
            break
        above.insert(0, line.strip().removeprefix("--").strip())
    comment = " ".join(above)
    assert "learner_pick row" not in comment
    assert "served the pick" in comment and "never looked up by matching" in comment


def test_the_daily_envelope_stamps_its_rows_with_the_injected_clock(textbook):
    from learnloop.source_retrieval.service_spend import daily_envelope

    paths, repository, _spans = textbook
    set_config(paths, "source_service", llm_price_per_million=1.0)
    clock = FrozenClock(datetime(2026, 3, 4, 5, 6, 7, tzinfo=UTC))
    envelope = daily_envelope(loaded(paths), repository, clock)
    handle = envelope.reserve(Decimal("0.01"))
    envelope.charge(Decimal("0.02"), handle)
    envelope.settle(handle)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = connection.execute("SELECT day, created_at, updated_at FROM source_service_spend WHERE id=?",
                                 (handle,)).fetchone()
    assert row[0] == "2026-03-04"
    assert str(row[1]).startswith("2026-03-04T05:06:07") and str(row[2]).startswith("2026-03-04T05:06:07")
    assert envelope.report()["metered_usd"] >= 0.01


def test_harvest_dry_run_prices_the_rerank_at_its_own_setting(textbook):
    from learnloop.instructional.harvest import harvest

    paths, repository, _spans = textbook
    set_config(paths, "source_service", llm_price_per_million=10.0)
    set_config(paths, "practice_index", rerank_price_per_million=2.0)
    report = harvest(loaded(paths), repository, dry_run=True, max_cost_usd=None, facet_ids=("facet_eigen",))
    rerank = report["targets"][0]["estimate"]["rerank"]
    assert rerank["usd"] == pytest.approx(round(rerank["tokens"] * 2.0 / 1_000_000, 6))
    assert report["estimate"]["rerank_price_per_million"] == 2.0


def test_a_reader_import_of_held_out_material_is_refused_before_any_model_call(tmp_path, monkeypatch):
    """Whoever selects it, held-out material never becomes practice: the
    Reader's own import job refuses it before authoring."""

    from learnloop.content.authoring.source_exercise_import import selection_for_region
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import IngestRunnerError, JobContext, RunnerServices

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    # The selection made while it was still practice (RW4b fix round 5: the
    # one statement reader refuses to read it once it is held out).
    selection = selection_for_region(repository, "ext_text", [spans["exercises"][1]], vault=load_vault(paths.root))
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    with pytest.raises(Exception, match="cannot be read"):
        selection_for_region(repository, "ext_text", [spans["exercises"][1]], vault=load_vault(paths.root))
    llm = FakeServiceLLM()
    ctx = JobContext(repo=repository, vault_root=paths.root,
                     job={"id": "job_1", "attempt_count": 1,
                          "payload": {"extraction_id": "ext_text", "source_id": "src_text",
                                      "raw_selection": selection}},
                     clock=FrozenClock(datetime(2026, 10, 13, tzinfo=UTC)), worker_id="w",
                     services=RunnerServices(exercise_import_client_factory=lambda _ctx: llm,
                                             background_key_checks=False))
    monkeypatch.setattr(JobContext, "report", lambda self, *a, **k: None)
    with pytest.raises(IngestRunnerError) as raised:
        jobs.handle_reader_exercise_import(ctx)
    assert raised.value.code == "exam_material" and llm.calls == []


def test_a_held_out_textbook_unit_never_feeds_synthesis_as_teaching(tmp_path):
    """Synthesis reads the one predicate too: a textbook unit held out for
    evaluation is assessment only (its inventory out of the context, its spans
    fed to the leakage gate), as an exam unit is."""

    from learnloop.content.synthesis.source_set_synthesis import _collect_inputs
    from learnloop.db.repositories import Repository
    from tests.test_source_set_synthesis import _setup as synthesis_vault

    root, repo = synthesis_vault(tmp_path, with_exam=False)
    vault = load_vault(root)
    source_set = vault.source_sets[0]
    before = _collect_inputs(repo, vault, source_set)
    assert [entry["unit_id"] for entry in before.unit_inventories] == ["chapter_symmetry"]

    save_unit_selection(repo, "ext_text", ["chapter_symmetry"],
                        exam_use_modes={"chapter_symmetry": "held_out_evaluation"})
    after = _collect_inputs(Repository(repo.sqlite_path), load_vault(root), source_set)
    assert after.unit_inventories == []
    assert {"ext_text:s1", "ext_text:s2"} <= after.held_out_span_ids


def test_the_exam_half_of_a_split_unit_is_exam_material_and_its_theory_half_still_teaches(tmp_path):
    """A split child overridden to ``exam`` resolves to the blocks under its own
    heading where its extraction's boundary overrides define it (the facet
    rule's split semantics), for every reader: main's corpus withheld the
    whole extraction because it read raw units only."""

    from tests.test_facet_authority_review import _add_split_chapter
    from tests.test_source_set_synthesis import _setup as synthesis_vault

    root, repo = synthesis_vault(tmp_path, with_exam=False)
    resolver = _add_split_chapter(repo, root, [{"unit_id": "chapter#Theory"},
                                               {"unit_id": "chapter#Exam", "role_override": "exam"}])
    vault = load_vault(root)

    assert exam_withheld(vault, repo, [("ext_split", "s1"), ("ext_split", "s2")]) == frozenset({("ext_split", "s2")})
    exclusions = teaching_exclusions(vault, repo)
    assert ("ext_split", "s2") in exclusions.spans and ("ext_split", "s1") not in exclusions.spans
    assert "ext_split" not in exclusions.extractions
    assert resolver.resolve({"extraction_id": "ext_split", "unit_id": "chapter#Theory", "span_id": "s1"}).role == \
        "primary_textbook"
    assert resolver.exam_material({"extraction_id": "ext_split", "span_id": "s2"})


def test_a_repair_never_teaches_from_an_exam_passage(textbook):
    """The repair overlay's fallback (the facet's first linked span) skips a
    link into exam material and teaches from the next one."""

    from learnloop.diagnosis.remediation import prescribe_remediation, start_remediation_episode

    paths, repository, spans = textbook
    exam = ("ext_exam", _exam_question_span(repository))
    taught = ("ext_text", spans["ch5"][1])
    for key, created in ((exam, "2026-01-01T00:00:00Z"), (taught, "2026-01-02T00:00:00Z")):
        repository.insert_entity_source_link(
            entity_type="facet", entity_id="facet_eigen", locator=format_block_span(*key), relation="support",
            extraction_id=key[0], locator_scheme="block_span_v1", created_at=created)
    misconception = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="Eigenvalues are the diagonal entries of any matrix",
        target_facet="facet_eigen", severity=0.9)
    vault = loaded(paths)
    episode = start_remediation_episode(repository, misconception, vault=vault)
    prescribed = prescribe_remediation(vault, repository, episode["id"])
    shown = [(entry["span_view"]["extraction_id"], entry["span_view"]["span_id"])
             for entry in prescribed["passages_shown"]]
    assert shown == [taught]


# --- the Reader's model contexts (held-out material is never explained) -----------------------


class _RecordingReaderTutor:
    """A reader tutor that records every request's manifest spans."""

    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-tutor"

    def __init__(self) -> None:
        self.contexts: list = []
        self._fake = None

    def supports(self, capability: str) -> bool:
        from tests.structured_ai import StructuredClientFake

        return StructuredClientFake().supports(capability)

    def complete(self, request):
        from tests.structured_ai import StructuredClientFake
        from learnloop.tutor.ai_contracts import TutorAnswer

        owner = self

        class _Answer(StructuredClientFake):
            def run_tutor_qa(self, context):
                owner.contexts.append(context)
                return TutorAnswer(answer_md="Read the worked example again.", question_type="clarification",
                                   facets=[])

        return _Answer().complete(request)

    def consume_usage(self):
        from tests.structured_ai import StructuredClientFake

        return StructuredClientFake().consume_usage()


def _held_out_exercises(textbook):
    paths, repository, spans = textbook
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    return paths, repository, spans


def test_a_reader_question_about_held_out_material_is_refused_before_anything_is_sent(textbook):
    """Reader Ask (and RW1a's dialogue, which asks through it): a question
    about a held-out passage is refused with the reason before anything is
    written or sent; a question beside it never carries a held-out neighbour."""

    from learnloop.tutor.tutor_qa import HeldOutMaterialRefused, TutorQAError, ask_question

    paths, repository, spans = textbook
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"worked": "held_out_evaluation"})
    vault = loaded(paths)
    tutor = _RecordingReaderTutor()
    clock = FrozenClock(datetime(2026, 10, 13, tzinfo=UTC))
    with pytest.raises(HeldOutMaterialRefused, match="held out for evaluation") as refused:
        ask_question(vault, repository, tutor, context="reader", question_md="How is this one solved?",
                     extraction_id="ext_text", span_id=spans["worked"][1], clock=clock)
    assert isinstance(refused.value, TutorQAError)
    with pytest.raises(HeldOutMaterialRefused):
        ask_question(vault, repository, tutor, context="reader", question_md="And these two?",
                     extraction_id="ext_text", span_id=spans["exercises"][1],
                     selection_span_ids=[spans["exercises"][1], spans["worked"][1]], clock=clock)
    assert tutor.contexts == [] and repository.question_events(context="reader") == []
    # RW1a's dialogue refuses it before any signal (answer mode, "asked") lands.
    from learnloop.reader import reader_dialogue as RD

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        before = connection.execute("SELECT COUNT(*) FROM interaction_events").fetchone()[0]
    with pytest.raises(HeldOutMaterialRefused):
        RD.ask(vault, repository, tutor, extraction_id="ext_text", span_id=spans["worked"][1],
               question_md="Explain this example", clock=clock)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM interaction_events").fetchone()[0] == before
    assert tutor.contexts == []

    # The exercise right after the held-out worked example: its manifest's
    # neighbours (the example's blocks on the base) leave the example out.
    beside = ask_question(vault, repository, tutor, context="reader", question_md="Where do I start?",
                          extraction_id="ext_text", span_id=spans["exercises"][1], clock=clock)
    assert beside["event_id"] and len(tutor.contexts) == 1
    manifest = {span["span_id"] for span in tutor.contexts[0].source_spans}
    assert spans["exercises"][1] in manifest and not manifest & set(spans["worked"])


def test_a_reader_preset_on_held_out_material_fails_before_any_model_call(textbook):
    """A demand-paged preset (worked example, another explanation, ...) on a
    held-out passage fails with the reason when it is sent, with no call."""

    from learnloop.reader import reader_requests as RR

    paths, repository, spans = _held_out_exercises(textbook)

    class _NoCalls:
        provider_name = "fake"
        provider_type = "fake"
        model = "fake"
        calls: list = []

        def supports(self, capability: str) -> bool:
            return True

        def complete(self, request):
            self.calls.append(request.purpose)
            raise AssertionError("no model call for held-out material")

    client = _NoCalls()
    queued = RR.enqueue_request(repository, source_id="src_text", revision_id="rev_text", extraction_id="ext_text",
                                span_id=spans["exercises"][1], preset="alt_explanation")
    drained = RR.drain_requests(repository, synthesize=RR.model_synthesis(client, source_sets=loaded(paths)))
    assert drained["failed"] == [queued["request_id"]] and client.calls == []
    request = RR.request_status(repository, request_id=queued["request_id"])
    assert "held out for evaluation" in json_text(request)


def json_text(value) -> str:
    import json

    return json.dumps(value, default=str)


def test_a_reader_check_over_held_out_material_is_refused_before_any_model_call(textbook):
    """A section quick check or an inquiry's passage check over held-out
    material is refused (``exam_material``) before a client is even built."""

    from types import SimpleNamespace

    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import IngestRunnerError
    from learnloop.reader.reader_guidance import extraction_sections

    paths, repository, spans = _held_out_exercises(textbook)
    built: list[str] = []
    section_rows, _blocks, _sections = extraction_sections(repository.load_document_ir("ext_text"))
    section = next(row["id"] for row in section_rows if spans["exercises"][1] in row["span_ids"])
    payloads = [
        {"extraction_id": "ext_text", "section_id": section},
        {"extraction_id": "ext_text", "scope_kind": "inquiry", "inquiry_root_event_id": "evt_root",
         "anchor_span_ids": [spans["exercises"][1]]},
    ]
    for payload in payloads:
        ctx = SimpleNamespace(
            payload=payload, repo=repository, clock=FrozenClock(datetime(2026, 10, 13, tzinfo=UTC)),
            report=lambda *a, **k: None, vault_root=paths.root, job={"id": "job_1", "attempt_count": 1},
            cancelled=lambda: False, bind_interruptible=lambda client: None,
            services=SimpleNamespace(quick_check_client=lambda ctx: built.append("client") or object()))
        with pytest.raises(IngestRunnerError) as refused:
            jobs.handle_reader_quick_check(ctx)
        assert refused.value.code == "exam_material", payload
    assert built == []
