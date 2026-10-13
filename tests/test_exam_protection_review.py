"""Exam protection: the Codex review's findings (2026-10-13).

* F1: an item made from material marked held out after its import stays out of
  routine practice (Today's queue, the quick check, ``find_practice``), and a
  pick or a session serve of it is refused.
* F2: held-out marks are source-level. Each one reaches every extraction of the
  source, the ones with marks of their own included; a mark that resolves
  nowhere withholds every extraction of its source.
* F3: one held-out partition (held-out units plus exam units' held-out
  assessment signals) for the Reader's model contexts, imports and the leakage
  gate alike.
* F4: PF never forwards a parent quote that lies in exam or held-out material,
  whether its location is a span id, a namespaced span id or a locator, and
  drops a quote it cannot place inside a partly protected extraction.
* F5: an exam item the learner was shown after its reservation is withdrawn
  (its reservation released, its history kept) before the exam starts; one
  shown while the exam is in progress is set aside at every door of the
  sitting (resume, answer acceptance, finish), its history kept (re-review).
* F6: the serving rules' kill switch, ``goals.held_out_selection``: off, each
  selection is the predecessor's; replay never reads it.

Each F1-F5 test failed on ``883b8da11`` (the stage as reviewed), and each
re-review F5 test on ``bfdf35d21`` (the fixes as re-reviewed), recorded in
``docs/reviews/exam-protection-codex-review.md``.
"""
from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.sources.exam_material import (
    exam_material,
    held_out_material,
    held_out_partition,
)
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.connection import connect
from learnloop.ids import new_ulid
from learnloop.ingest.locators import format_block_span
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.scheduling.serving_exclusions import routine_serving_exclusions
from learnloop.vault.loader import load_vault
from learnloop.vault.models import SourceRef
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault.yaml_io import read_yaml
from tests.source_retrieval_fakes import seed_source
from tests.source_service_fakes import build_textbook_vault, loaded
from tests.test_source_inventory import _block, _ir, _persist

CLOCK = FrozenClock(datetime(2026, 10, 13, tzinfo=UTC))


@pytest.fixture
def textbook(tmp_path):
    return build_textbook_vault(tmp_path / "vault")


def _with_exercise(root, practice_item_id: str, *, source_id: str, extraction_id: str, span_id: str) -> None:
    """Give an item the canonical exercise an import records."""

    vault = load_vault(root)
    path = next(VaultPaths(vault.root, vault.config).root.rglob(f"{practice_item_id}.yaml"))
    payload = read_yaml(path)
    payload["canonical_exercise"] = {"source_id": source_id, "extraction_id": extraction_id,
                                     "span_ids": [span_id], "relation": "verbatim"}
    upsert_practice_item(root, payload, clock=CLOCK)


def _problem_book(repository) -> None:
    """``ext_problems``: a problems unit (``s1`` header, ``s2`` problem) and a notes unit (``s4``, ``s5``)."""

    seed_source(repository, source_id="src_problems", revision_id="rev_problems", extraction_id="ext_problems",
                title="Problem book", units={"ex": ("Problems", [("Problem 1: compute 7 times 6.", 1)]),
                                             "notes": ("Notes", [("Multiplication is repeated addition.", 2)])})


def _hold_out_problems(repository) -> None:
    save_unit_selection(repository, "ext_problems", ["ex", "notes"], exam_use_modes={"ex": "held_out_evaluation"})


def _expose(repository, extraction_id: str, span_id: str) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_exposure_events(id, context, extraction_id, span_id, created_at) VALUES (?,?,?,?,?)",
            ("sxe_" + new_ulid(), "reader", extraction_id, span_id, "2026-10-12T00:00:00Z"))
        connection.commit()


def _reveal(repository, item_id: str) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, source_kind, amount, created_at) VALUES (?,?,?,?,?)",
            ("rev_" + new_ulid(), item_id, "tutor_answer", 1.0, "2026-10-12T00:00:00Z"))
        connection.commit()


def _switch_off(root) -> None:
    """``goals.held_out_selection = false`` (under the vault's ``[goals]`` table when it has one)."""

    config = root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    if "\n[goals]\n" in text:
        text = text.replace("\n[goals]\n", "\n[goals]\nheld_out_selection = false\n", 1)
    else:
        text = text.rstrip("\n") + "\n\n[goals]\nheld_out_selection = false\n"
    config.write_text(text, encoding="utf-8")
    assert load_vault(root).config.goals.held_out_selection is False


# --- F1: held-out material stays out of routine practice -----------------------------------------


def _due_pool(tmp_path):
    from tests.test_exam_pool import _vault_with_items

    vault, paths, repository = _vault_with_items(tmp_path)
    for item_id in ("pi_pool_recall_easy", "pi_pool_apply_mid", "pi_pool_derive_hard"):
        repository.upsert_practice_item_state(
            item_id, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z", active=True)
    _problem_book(repository)
    _with_exercise(paths.root, "pi_pool_apply_mid", source_id="src_problems", extraction_id="ext_problems",
                   span_id="s2")
    return paths, repository


def _queue(root, repository) -> set[str]:
    from tests.test_exam_pool import NOW

    return {entry.practice_item_id for entry in build_due_queue(load_vault(root), repository, clock=FrozenClock(NOW),
                                                                persist_explanations=False)}


def test_an_item_marked_held_out_after_its_import_leaves_routine_practice(tmp_path):
    paths, repository = _due_pool(tmp_path)
    assert "pi_pool_apply_mid" in _queue(paths.root, repository)

    _hold_out_problems(repository)  # the owner holds the problems out after the import

    assert "pi_pool_apply_mid" not in _queue(paths.root, repository)
    exclusions = routine_serving_exclusions(load_vault(paths.root), repository)
    assert "pi_pool_apply_mid" in exclusions.item_ids and "pi_pool_recall_easy" not in exclusions.item_ids


def test_a_pick_of_an_item_marked_held_out_since_its_proposal_is_refused(textbook):
    from learnloop.instructional.policy import caller_for
    from learnloop.instructional.practice import propose_practice, record_proposal_selection
    from tests.source_service_fakes import FakeServiceLLM

    paths, repository, spans = textbook
    vault = loaded(paths)
    result = propose_practice(vault, repository, "determinant rows swapped sign", {},
                              caller=caller_for(repository, "plan"), rerank_client=FakeServiceLLM())
    picked = result["items"][0]["practice_item_id"]
    _with_exercise(paths.root, picked, source_id="src_text", extraction_id="ext_text",
                   span_id=spans["exercises"][3])
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})

    with pytest.raises(ValueError, match="held out for evaluation"):
        record_proposal_selection(repository, proposal_id=result["proposal_id"], practice_item_id=picked,
                                  vault=loaded(paths))


def _sidecar(tmp_path, monkeypatch):
    import learnloop.clock as clock_module
    import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
    from learnloop_sidecar.context import SidecarContext
    from tests.helpers import create_daily_plan_vault

    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: datetime(2026, 10, 12, 9, 0, tzinfo=UTC))
    paths = create_daily_plan_vault(tmp_path / "vault",
                                    learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]})
    context = SidecarContext()
    context.load(paths.root)
    context.grading_provider_override = "manual"
    return context, paths


def _call(context, name, params):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(context, spec.params_model.model_validate(params))


def test_a_session_serve_of_an_item_marked_held_out_is_refused(tmp_path, monkeypatch):
    from learnloop_sidecar.errors import SidecarError

    context, paths = _sidecar(tmp_path, monkeypatch)
    _vault, repository = context.require_vault()
    _problem_book(repository)
    _with_exercise(paths.root, "pi_extra_1", source_id="src_problems", extraction_id="ext_problems", span_id="s2")
    _hold_out_problems(repository)
    context.load(paths.root)
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    with pytest.raises(SidecarError, match="held out for evaluation"):
        _call(context, "get_practice_item", {"practiceItemId": "pi_extra_1", "sessionId": session_id})
    # A read-only open (feedback, the inspector) still renders it.
    assert _call(context, "get_practice_item", {"practiceItemId": "pi_extra_1"})


# --- F2: held-out marks reach every extraction of the source -------------------------------------


def _second_text_extraction(repository, *, labels=("Chapter 5 Eigenvalues", "Worked examples", "Exercises",
                                                    "Solutions")) -> dict[str, list[str]]:
    """A re-extraction of the textbook under a new revision: ``rev_text_2`` / ``ext_text_2``."""

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_text_2", "src_text", "sha256:text2", None, "2026-02-01T00:00:00Z"))
        connection.commit()
    units, spans, ordinal = [], {}, 1
    for index, label in enumerate(labels):
        unit_id = f"u{index}"
        blocks = [_block(f"s{ordinal}", f"{label} block one"), _block(f"s{ordinal + 1}", f"{label} block two")]
        ordinal += 2
        units.append((unit_id, label, blocks, f"sha256:{unit_id}", 1))
        spans[label] = [block.span_id for block in blocks]
    _persist(repository, _ir(units), revision_id="rev_text_2", extraction_id="ext_text_2")
    return spans


def test_held_out_marks_in_two_extractions_each_reach_the_other(textbook):
    paths, repository, spans = textbook
    second = _second_text_extraction(repository)
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    save_unit_selection(repository, "ext_text_2", ["u0", "u1", "u2", "u3"],
                        exam_use_modes={"u1": "held_out_evaluation"})  # "Worked examples"
    material = exam_material(loaded(paths), repository)

    for span in (spans["exercises"][1], spans["worked"][1]):
        assert material.is_held_out("ext_text", span), span
    for span in (second["Exercises"][0], second["Worked examples"][0]):
        assert material.is_held_out("ext_text_2", span), span
    assert not material.covers("ext_text", spans["ch5"][1])
    assert not material.covers("ext_text_2", second["Chapter 5 Eigenvalues"][0])


def test_an_unresolvable_mark_withholds_every_extraction_of_its_source(textbook):
    paths, repository, spans = textbook
    _second_text_extraction(repository)
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"no_such_unit": "held_out_evaluation"})
    material = exam_material(loaded(paths), repository)

    assert {"ext_text", "ext_text_2"} <= material.held_out.extractions
    assert "ext_text_2" in held_out_partition(loaded(paths), repository).extractions


_TWO_LABELS = ("Chapter 1", "Exercises", "Chapter 2", "Exercises")


def _two_extractions(repository, source_id: str, *, second_hash: str = "sha256:c{index}") -> list[str]:
    """``ext_<id>`` (units c0-c3: s1-s2, s4-s5, s7-s8, s10-s11) and ``ext_<id>_b``
    (c0-c3: s1-s4) of one source, whose units are labelled "Chapter 1",
    "Exercises", "Chapter 2", "Exercises". ``second_hash`` sets the second
    extraction's content hashes (the first's are ``sha256:c<n>``)."""

    seed_source(repository, source_id=source_id, revision_id=f"rev_{source_id}", extraction_id=f"ext_{source_id}",
                title=source_id, units={f"c{index}": (label, [(f"{label} text {index}", 1)])
                                        for index, label in enumerate(_TWO_LABELS)})
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            (f"rev_{source_id}_b", source_id, f"sha256:{source_id}_b", None, "2026-02-01T00:00:00Z"))
        connection.commit()
    _persist(repository, _ir([(f"c{index}", label, [_block(f"s{index + 1}", f"{label} b {index}")],
                               second_hash.format(index=index), 1) for index, label in enumerate(_TWO_LABELS)]),
             revision_id=f"rev_{source_id}_b", extraction_id=f"ext_{source_id}_b")
    return [f"c{index}" for index in range(4)]


def test_the_same_unit_marked_in_two_extractions_withholds_only_that_unit(textbook):
    """Two "Exercises" units: the same one (same occurrence, same content)
    marked in both extractions stays one unit; marks that disagree on which
    one withhold both (the label is ambiguous)."""

    paths, repository, _spans = textbook
    units = _two_extractions(repository, "two")
    save_unit_selection(repository, "ext_two", units, exam_use_modes={"c1": "held_out_evaluation"})
    save_unit_selection(repository, "ext_two_b", units, exam_use_modes={"c1": "held_out_evaluation"})
    material = exam_material(loaded(paths), repository).held_out
    assert material.covers("ext_two", "s5") and not material.covers("ext_two", "s11")
    assert material.covers("ext_two_b", "s2") and not material.covers("ext_two_b", "s4")

    save_unit_selection(repository, "ext_two_b", units, exam_use_modes={"c3": "held_out_evaluation"})
    material = exam_material(loaded(paths), repository).held_out
    assert material.covers("ext_two", "s5") and material.covers("ext_two", "s11")
    assert material.covers("ext_two_b", "s2") and material.covers("ext_two_b", "s4")
    assert not material.covers("ext_two", "s2") and not material.covers("ext_two", "s8")
    assert not material.covers("ext_two_b", "s1") and not material.covers("ext_two_b", "s3")


def test_the_same_occurrence_with_other_content_is_not_the_same_unit(textbook):
    """Marks on the n-th "Exercises" of two extractions whose content differs
    may be different units: every "Exercises" unit is withheld in both."""

    paths, repository, _spans = textbook
    units = _two_extractions(repository, "three", second_hash="sha256:changed{index}")
    save_unit_selection(repository, "ext_three", units, exam_use_modes={"c1": "held_out_evaluation"})
    save_unit_selection(repository, "ext_three_b", units, exam_use_modes={"c1": "held_out_evaluation"})
    material = exam_material(loaded(paths), repository).held_out
    assert material.covers("ext_three", "s5") and material.covers("ext_three", "s11")
    assert material.covers("ext_three_b", "s2") and material.covers("ext_three_b", "s4")
    assert not material.covers("ext_three", "s2") and not material.covers("ext_three_b", "s3")


# --- F3: one held-out partition -----------------------------------------------------------------


def _held_out_signal(repository, span_id: str) -> None:
    """The exam's inventory marks its question a held-out assessment signal (no unit mark)."""

    repository.insert_unit_inventory(
        id="inv_" + new_ulid(), source_revision_id="rev_exam", extraction_id="ext_exam", unit_id="exam_q",
        unit_semantic_hash="sha256:exam_q", inventory_profile="exam", inventory_schema_version=1,
        prompt_version="test", provider="fake", model="fake",
        inventory={"assessment_signals": [{"signal_id": "sig_1", "held_out": True, "span_ids": [span_id]}]})


def _exam_question_span(repository) -> str:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id='ext_exam' AND text LIKE 'Exam question%'"
        ).fetchone()
    return str(row[0])


def test_a_held_out_assessment_signal_is_held_out_for_the_reader_and_the_gate_alike(textbook):
    from learnloop.tutor.tutor_qa import HeldOutMaterialRefused, ask_question
    from tests.test_exam_protection import _RecordingReaderTutor

    paths, repository, _spans = textbook
    question = _exam_question_span(repository)
    _held_out_signal(repository, question)
    vault = loaded(paths)

    assert held_out_partition(vault, repository).covers("ext_exam", question)
    assert exam_material(vault, repository).is_held_out("ext_exam", question)
    tutor = _RecordingReaderTutor()
    with pytest.raises(HeldOutMaterialRefused):
        ask_question(vault, repository, tutor, context="reader", question_md="How do I start?",
                     extraction_id="ext_exam", span_id=question, clock=CLOCK)
    assert tutor.contexts == []
    assert held_out_material(vault, repository).covers("ext_exam", question)


def test_a_reader_import_of_a_held_out_signal_is_refused(textbook, monkeypatch):
    from learnloop.content.authoring.source_exercise_import import selection_for_region
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import IngestRunnerError, JobContext, RunnerServices
    from tests.source_service_fakes import FakeServiceLLM

    paths, repository, _spans = textbook
    question = _exam_question_span(repository)
    _held_out_signal(repository, question)
    llm = FakeServiceLLM()
    ctx = JobContext(repo=repository, vault_root=paths.root,
                     job={"id": "job_1", "attempt_count": 1,
                          "payload": {"extraction_id": "ext_exam", "source_id": "src_exam",
                                      "raw_selection": selection_for_region(repository, "ext_exam", [question])}},
                     clock=CLOCK, worker_id="w",
                     services=RunnerServices(exercise_import_client_factory=lambda _ctx: llm,
                                             background_key_checks=False))
    monkeypatch.setattr(JobContext, "report", lambda self, *a, **k: None)
    with pytest.raises(IngestRunnerError) as raised:
        jobs.handle_reader_exercise_import(ctx)
    assert raised.value.code == "exam_material" and llm.calls == []


# --- F4: PF's parent quotes ---------------------------------------------------------------------


def _pf_passages(vault, repository, parent):
    from learnloop.ops.pf_generation import _FamilyRun

    run = SimpleNamespace(ctx=SimpleNamespace(vault=vault, repository=repository), parent=parent)
    return _FamilyRun._passages(run)


@pytest.mark.parametrize("shape", ["locator", "namespaced", "unlocated"])
def test_pf_never_forwards_a_held_out_parent_quote(textbook, shape):
    paths, repository, spans = textbook
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    vault = loaded(paths)
    held = spans["exercises"][1]
    location = {
        "locator": {"extraction_id": "ext_text", "locator": format_block_span("ext_text", held)},
        "namespaced": {"span_ids": [f"ext_text:{held}"]},
        "unlocated": {"extraction_id": "ext_text"},
    }[shape]
    quote = "An eigenvalue t satisfies 3t + 5 = 20; solve 3x + 5 = 20 for x to find the eigenvalue."
    refs = [SourceRef(ref_type="canonical_source", ref_id="ref_held", quote=quote, **location),
            SourceRef(ref_type="canonical_source", ref_id="ref_taught", extraction_id="ext_text",
                      span_ids=[spans["ch5"][1]], quote="Eigenvalues are the roots of the characteristic polynomial.")]
    item = vault.practice_items["pi_eigen_1"]
    parent = item.model_copy(update={"provenance": item.provenance.model_copy(update={"source_refs": refs})})

    texts = [passage["text"] for passage in _pf_passages(vault, repository, parent)]
    assert quote not in texts
    assert "Eigenvalues are the roots of the characteristic polynomial." in texts


# --- F5: an exam item exposed after its reservation ---------------------------------------------


def _reserved_pool(tmp_path):
    from learnloop.goals.exam_pool import reserve_exam_pool
    from tests.test_exam_pool import NOW, _vault_with_items

    vault, paths, repository = _vault_with_items(tmp_path)
    _problem_book(repository)
    _with_exercise(paths.root, "pi_pool_apply_mid", source_id="src_problems", extraction_id="ext_problems",
                   span_id="s2")
    vault = load_vault(paths.root)
    report = reserve_exam_pool(vault, repository, vault.goals[0], item_count=3, clock=FrozenClock(NOW))
    assert {"pi_pool_apply_mid", "pi_pool_derive_hard"} <= set(report.reserved_item_ids)
    return paths, repository


def test_an_exam_item_exposed_after_its_reservation_is_withdrawn_before_the_exam_starts(tmp_path):
    from learnloop.goals.exam_session import start_exam
    from tests.test_exam_pool import NOW

    paths, repository = _reserved_pool(tmp_path)
    _expose(repository, "ext_problems", "s2")  # its exercise read in the Reader
    _reveal(repository, "pi_pool_derive_hard")  # its answer revealed by the tutor

    vault = load_vault(paths.root)
    session = start_exam(vault, repository, vault.goals[0].id, clock=FrozenClock(NOW))
    assert "pi_pool_apply_mid" not in session["item_order"]
    assert "pi_pool_derive_hard" not in session["item_order"] and session["item_order"]
    withdrawn = {entry["practice_item_id"]: entry["reasons"] for entry in session["withdrawn_items"]}
    assert withdrawn == {"pi_pool_apply_mid": ["source_exposed"], "pi_pool_derive_hard": ["revealed"]}
    assert "already seen" in session["withdrawn_note"]
    # The reservation history is kept: the rows are released, not deleted.
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = dict(connection.execute(
            "SELECT practice_item_id, released_at FROM exam_pool_items WHERE practice_item_id IN (?, ?)",
            ("pi_pool_apply_mid", "pi_pool_derive_hard")).fetchall())
    assert set(rows) == {"pi_pool_apply_mid", "pi_pool_derive_hard"} and all(rows.values())
    assert {"pi_pool_apply_mid", "pi_pool_derive_hard"}.isdisjoint(repository.reserved_exam_pool_item_ids())


def test_a_pool_every_item_of_which_was_exposed_is_reserved_afresh(tmp_path):
    from learnloop.goals.exam_pool import reserve_exam_pool
    from tests.test_exam_pool import NOW

    paths, repository = _reserved_pool(tmp_path)
    first = set(repository.reserved_exam_pool_item_ids())
    for item_id in first:
        _reveal(repository, item_id)
    vault = load_vault(paths.root)
    report = reserve_exam_pool(vault, repository, vault.goals[0], item_count=3, clock=FrozenClock(NOW))
    assert not report.already_reserved and set(report.reserved_item_ids).isdisjoint(first)
    assert {entry["practice_item_id"] for entry in report.withdrawn} == first


# --- F6: the kill switch ------------------------------------------------------------------------


def test_with_the_switch_off_routine_practice_serves_held_out_material_as_before(tmp_path, monkeypatch):
    paths, repository = _due_pool(tmp_path)
    _hold_out_problems(repository)
    _switch_off(paths.root)

    assert "pi_pool_apply_mid" in _queue(paths.root, repository)
    assert routine_serving_exclusions(load_vault(paths.root), repository).held_out_item_ids == frozenset()


def test_with_the_switch_off_picks_and_session_serves_are_not_refused(tmp_path, monkeypatch):
    context, paths = _sidecar(tmp_path, monkeypatch)
    _vault, repository = context.require_vault()
    _problem_book(repository)
    _with_exercise(paths.root, "pi_extra_1", source_id="src_problems", extraction_id="ext_problems", span_id="s2")
    _hold_out_problems(repository)
    _switch_off(paths.root)
    context.load(paths.root)
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    assert _call(context, "get_practice_item", {"practiceItemId": "pi_extra_1", "sessionId": session_id})

    from learnloop.instructional.practice import refuse_protected_pick

    refuse_protected_pick(repository, "pi_extra_1", vault=load_vault(paths.root))  # no refusal


def test_with_the_switch_off_shown_material_is_selected_as_before(tmp_path):
    """The exam pool, the certification cold probe and the cold retry each
    choose what the stage's predecessor chose."""

    from learnloop.goals.certification_cold_probe import select_held_out_probe_item
    from learnloop.goals.exam_pool import reserve_exam_pool
    from tests.test_certification_cold_probe import HELD_OUT_ITEM, _certify
    from tests.test_exam_pool import NOW, _vault_with_items

    vault, paths, repository = _vault_with_items(tmp_path / "pool")
    _problem_book(repository)
    _with_exercise(paths.root, "pi_pool_apply_mid", source_id="src_problems", extraction_id="ext_problems",
                   span_id="s2")
    _expose(repository, "ext_problems", "s2")
    _reveal(repository, "pi_pool_derive_hard")
    _switch_off(paths.root)
    vault = load_vault(paths.root)
    report = reserve_exam_pool(vault, repository, vault.goals[0], item_count=3, clock=FrozenClock(NOW))
    assert {"pi_pool_apply_mid", "pi_pool_derive_hard"} <= set(report.reserved_item_ids)

    probe_paths, _vault, probe_repository, certificate = _certify(tmp_path / "probe")
    _problem_book(probe_repository)
    _with_exercise(probe_paths.root, HELD_OUT_ITEM, source_id="src_problems", extraction_id="ext_problems",
                   span_id="s2")
    _expose(probe_repository, "ext_problems", "s2")
    assert select_held_out_probe_item(load_vault(probe_paths.root), probe_repository,
                                      certificate).practice_item_id is None
    _switch_off(probe_paths.root)
    assert select_held_out_probe_item(load_vault(probe_paths.root), probe_repository,
                                      certificate).practice_item_id == HELD_OUT_ITEM


def test_with_the_switch_off_the_cold_retry_is_the_predecessor_s(tmp_path):
    from learnloop.diagnosis.remediation import (
        prescribe_remediation,
        start_remediation_episode,
        start_remediation_treatment,
    )
    from tests.test_remediation_cold_retry import NOW, _setup

    def treat(root, *, reveal=None, switch_off=False):
        vault, repository, misconception_id = _setup(root)
        if reveal:
            _reveal(repository, reveal)
        if switch_off:
            _switch_off(vault.root)
            vault = load_vault(vault.root)
        episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
        prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
        return start_remediation_treatment(vault, repository, episode["id"], clock=FrozenClock(NOW))["cold_item_id"]

    cold_item = treat(tmp_path / "first")
    assert cold_item is not None
    assert treat(tmp_path / "second", reveal=cold_item) != cold_item
    assert treat(tmp_path / "third", reveal=cold_item, switch_off=True) == cold_item


def test_with_the_switch_off_an_exposed_exam_item_is_administered_as_before(tmp_path):
    from learnloop.goals.exam_session import start_exam
    from tests.test_exam_pool import NOW

    paths, repository = _reserved_pool(tmp_path)
    _expose(repository, "ext_problems", "s2")
    _switch_off(paths.root)
    vault = load_vault(paths.root)
    session = start_exam(vault, repository, vault.goals[0].id, clock=FrozenClock(NOW))
    assert "pi_pool_apply_mid" in session["item_order"] and session["withdrawn_items"] == []
    assert session["withdrawn_note"] is None


def test_the_switch_never_reaches_what_a_model_is_shown(textbook):
    """The switch is the serving rules' only: the Reader still refuses held-out material."""

    from learnloop.tutor.tutor_qa import HeldOutMaterialRefused, ask_question
    from tests.test_exam_protection import _RecordingReaderTutor

    paths, repository, spans = textbook
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"worked": "held_out_evaluation"})
    _switch_off(paths.root)
    with pytest.raises(HeldOutMaterialRefused):
        ask_question(loaded(paths), repository, _RecordingReaderTutor(), context="reader", question_md="How?",
                     extraction_id="ext_text", span_id=spans["worked"][1], clock=CLOCK)


def test_replay_never_reads_the_switch(tmp_path):
    """On the migration-head fixture at the latest tag: rebuilds with the
    switch on and off leave every DERIVED table the same."""

    from pathlib import Path

    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
    from learnloop.db.copies import copy_tree_with_databases
    from learnloop.db.repositories import Repository
    from learnloop.db.table_roles import TableRole, tables_for_role
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from tests.helpers import _set_algorithm_version_at

    head = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_201"
    root = tmp_path / "head"
    copy_tree_with_databases(head, root)
    _set_algorithm_version_at(root, LATEST_ALGORITHM_VERSION)
    repository = Repository(root / "state.sqlite")
    derived = sorted(tables_for_role(TableRole.DERIVED))

    def snapshot():
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            return {table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
                    for table in derived}

    rebuild_all_derived_state(load_vault(root), repository, clock=CLOCK)
    rebuild_all_derived_state(load_vault(root), repository, clock=CLOCK)
    switched_on = snapshot()
    _switch_off(root)
    rebuild_all_derived_state(load_vault(root), repository, clock=CLOCK)
    assert snapshot() == switched_on


# --- re-review F5: an exam item exposed while its exam is in progress ----------------------------


def _started_exam(tmp_path):
    from learnloop.goals.exam_session import start_exam
    from tests.test_exam_pool import NOW

    paths, repository = _reserved_pool(tmp_path)
    vault = load_vault(paths.root)
    session = start_exam(vault, repository, vault.goals[0].id, clock=FrozenClock(NOW))
    assert {"pi_pool_apply_mid", "pi_pool_derive_hard"} <= set(session["item_order"])
    return paths, repository, session


def test_an_exam_item_exposed_during_the_exam_is_withdrawn_on_resume_and_its_answer_refused(tmp_path):
    """Codex re-review F5: reserve, start, read an unanswered item's exercise
    in the Reader, resume. The item is no longer served, its answer is refused
    at both doors, its history (frozen order, prediction, reservation) is kept,
    and the report names it without scoring it."""

    from learnloop.goals.exam_session import (
        ExamItemWithdrawnError,
        finish_exam,
        queue_exam_answer,
        record_exam_answer,
        start_exam,
    )
    from tests.test_exam_pool import NOW
    from tests.test_exam_session import _grade

    paths, repository, session = _started_exam(tmp_path)
    session_id = session["session_id"]
    _expose(repository, "ext_problems", "s2")  # pi_pool_apply_mid's exercise, read mid-exam

    vault = load_vault(paths.root)
    resumed = start_exam(vault, repository, vault.goals[0].id, clock=FrozenClock(NOW))
    assert resumed["session_id"] == session_id and resumed["already_started"] is True
    assert resumed["item_order"] == [item for item in session["item_order"] if item != "pi_pool_apply_mid"]
    assert resumed["withdrawn_items"] == [{"practice_item_id": "pi_pool_apply_mid", "reasons": ["source_exposed"]}]
    assert "already seen" in resumed["withdrawn_note"]

    with pytest.raises(ExamItemWithdrawnError, match="set aside"):
        queue_exam_answer(vault, repository, session_id, "pi_pool_apply_mid", answer_md="42")
    with pytest.raises(ExamItemWithdrawnError, match="set aside"):
        record_exam_answer(vault, repository, session_id, "pi_pool_apply_mid", answer_md="42",
                           resolved_grade=_grade(4))
    assert repository.exam_answer(session_id, "pi_pool_apply_mid") is None

    # The history stays: the frozen order, the frozen prediction, the reservation row.
    assert repository.exam_session(session_id)["item_order"] == session["item_order"]
    assert "pi_pool_apply_mid" in {row["practice_item_id"] for row in repository.exam_predictions(session_id)}
    assert "pi_pool_apply_mid" in repository.reserved_exam_pool_item_ids()

    for item_id in resumed["item_order"]:
        record_exam_answer(vault, repository, session_id, item_id, answer_md="A", resolved_grade=_grade(4))
    report = finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    assert "pi_pool_apply_mid" not in {entry["practice_item_id"] for entry in report["items"]}
    assert report["withdrawn_items"] == [{"practice_item_id": "pi_pool_apply_mid", "reasons": ["source_exposed"]}]
    assert "already seen" in report["withdrawn_note"]
    assert report["item_count"] == report["answered_count"] == len(resumed["item_order"])
    assert "pi_pool_apply_mid" not in repository.reserved_exam_pool_item_ids()  # released with the pool


def test_an_exam_answer_given_before_its_item_was_exposed_stands(tmp_path):
    from learnloop.goals.exam_session import finish_exam, queue_exam_answer, record_exam_answer, start_exam
    from tests.test_exam_pool import NOW
    from tests.test_exam_session import _grade

    paths, repository, session = _started_exam(tmp_path)
    session_id = session["session_id"]
    vault = load_vault(paths.root)
    queue_exam_answer(vault, repository, session_id, "pi_pool_apply_mid", answer_md="42")
    _expose(repository, "ext_problems", "s2")

    resumed = start_exam(vault, repository, vault.goals[0].id, clock=FrozenClock(NOW))
    assert resumed["item_order"] == session["item_order"] and resumed["withdrawn_items"] == []
    # The grade of an answer accepted before the exposure still lands.
    for item_id in session["item_order"]:
        record_exam_answer(vault, repository, session_id, item_id, answer_md="42" if item_id == "pi_pool_apply_mid"
                           else "A", resolved_grade=_grade(4))
    report = finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    assert "pi_pool_apply_mid" in {entry["practice_item_id"] for entry in report["items"]}
    assert report["withdrawn_items"] == [] and report["withdrawn_note"] is None


def test_the_exam_screen_stops_serving_an_item_exposed_mid_exam_and_refuses_its_answer(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.errors import SidecarError

    paths, repository = _reserved_pool(tmp_path)
    context = SidecarContext()
    context.load(paths.root)
    goal_id = context.require_vault()[0].goals[0].id
    try:
        started = _call(context, "start_exam", {"goalId": goal_id})
        assert "pi_pool_apply_mid" in {item["practiceItemId"] for item in started["items"]}
        _expose(repository, "ext_problems", "s2")

        resumed = _call(context, "start_exam", {"goalId": goal_id})
        assert resumed["sessionId"] == started["sessionId"]
        served = [item["practiceItemId"] for item in resumed["items"]]
        assert "pi_pool_apply_mid" not in served and served
        assert [item["total"] for item in resumed["items"]] == [len(served)] * len(served)
        assert resumed["withdrawnItems"] == [{"practiceItemId": "pi_pool_apply_mid", "reasons": ["source_exposed"]}]
        assert "already seen" in resumed["withdrawnNote"]

        with pytest.raises(SidecarError) as refused:
            _call(context, "submit_exam_answer", {"sessionId": started["sessionId"],
                                                  "practiceItemId": "pi_pool_apply_mid", "answerMd": "42"})
        assert refused.value.code == "exam_item_withdrawn"
        assert "set aside" in refused.value.message
        assert refused.value.details["reasons"] == ["source_exposed"]
        assert repository.exam_answer(started["sessionId"], "pi_pool_apply_mid") is None
    finally:
        context.exam_grading.shutdown()
        context.ingest_jobs.shutdown()


def test_the_cli_refuses_an_answer_to_an_item_exposed_mid_exam_before_grading_it(tmp_path):
    """The CLI grades before it records: the refusal comes first, so no
    grading call is spent on an answer the sitting would refuse (with no
    grader configured, a later refusal would read ``exam_grading_unavailable``)."""

    import json

    from typer.testing import CliRunner

    from learnloop.cli import app

    paths, repository, session = _started_exam(tmp_path)
    _expose(repository, "ext_problems", "s2")
    result = CliRunner().invoke(app, ["exam", "answer", "pi_pool_apply_mid", "--session", session["session_id"],
                                      "--answer", "42", "--json", "--vault", str(paths.root)])
    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["error"] == "exam_item_withdrawn" and "set aside" in payload["message"]
    assert repository.exam_answer(session["session_id"], "pi_pool_apply_mid") is None


def test_a_sitting_every_unanswered_item_of_which_was_exposed_is_closed_and_its_pool_released(tmp_path):
    """Nothing answered and nothing left to serve: the sitting is closed
    (abandoned, its rows kept), its items rejoin practice, and the next
    reservation holds out a fresh pool."""

    from learnloop.goals.exam_pool import reserve_exam_pool
    from learnloop.goals.exam_session import ExamSessionError, start_exam
    from tests.test_exam_pool import NOW

    paths, repository, session = _started_exam(tmp_path)
    session_id = session["session_id"]
    for item_id in session["item_order"]:
        _reveal(repository, item_id)

    vault = load_vault(paths.root)
    goal = vault.goals[0]
    with pytest.raises(ExamSessionError, match="none is a fair test"):
        start_exam(vault, repository, goal.id, clock=FrozenClock(NOW))
    stored = repository.exam_session(session_id)
    assert stored["status"] == "abandoned" and stored["item_order"] == session["item_order"]
    assert {entry["practice_item_id"] for entry in stored["report"]["withdrawn_items"]} == set(session["item_order"])
    assert len(repository.exam_predictions(session_id)) == len(session["item_order"])
    assert repository.exam_session_in_progress_for_goal(goal.id) is None
    assert set(session["item_order"]).isdisjoint(repository.reserved_exam_pool_item_ids())

    report = reserve_exam_pool(vault, repository, goal, item_count=3, clock=FrozenClock(NOW))
    assert not report.already_reserved and set(report.reserved_item_ids).isdisjoint(session["item_order"])


def test_the_report_of_an_automatically_closed_sitting_is_its_closure_report(tmp_path):
    """Codex final verify F7: ``exam_report`` of a sitting closed because every
    item was set aside returns the persisted closure report (why it closed,
    which items were set aside and why), never a rebuilt progress view that
    claims nothing was withdrawn."""

    from learnloop.goals.exam_session import ExamSessionError, exam_report, start_exam
    from tests.test_exam_pool import NOW

    paths, repository, session = _started_exam(tmp_path)
    session_id = session["session_id"]
    for item_id in session["item_order"]:
        _reveal(repository, item_id)
    vault = load_vault(paths.root)
    with pytest.raises(ExamSessionError, match="none is a fair test"):
        start_exam(vault, repository, vault.goals[0].id, clock=FrozenClock(NOW))
    stored = repository.exam_session(session_id)
    assert stored["status"] == "abandoned"

    report = exam_report(load_vault(paths.root), repository, session_id)
    assert report == stored["report"]
    assert report["closed_reason"] == "every_item_withdrawn"
    withdrawn = {entry["practice_item_id"]: entry["reasons"] for entry in report["withdrawn_items"]}
    assert set(withdrawn) == set(session["item_order"])
    assert all(withdrawn.values())
    assert report["withdrawn_note"]


def test_with_the_switch_off_an_item_exposed_mid_exam_is_administered_as_before(tmp_path):
    from learnloop.goals.exam_session import queue_exam_answer, start_exam
    from tests.test_exam_pool import NOW

    paths, repository, session = _started_exam(tmp_path)
    _expose(repository, "ext_problems", "s2")
    _switch_off(paths.root)
    vault = load_vault(paths.root)
    resumed = start_exam(vault, repository, vault.goals[0].id, clock=FrozenClock(NOW))
    assert resumed["item_order"] == session["item_order"] and resumed["withdrawn_items"] == []
    queue_exam_answer(vault, repository, session["session_id"], "pi_pool_apply_mid", answer_md="42")
    assert repository.exam_answer(session["session_id"], "pi_pool_apply_mid") is not None
