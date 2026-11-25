"""The probe doors ask the session serve's exam verdict (G2-R21, G2-R22: the probe router's fix round 3).

Every door that picks or serves a probe instrument shows its item in the session, so it reads the ``session_serve`` row
of ``exam_material.SURFACE_SETS`` through the one verdict (``exam_material.serve_refusals``) before anything is
priced, reserved or marked served: instrument selection (``probe_episodes.item_refusals`` inside
``eligible_instruments``), the learner lane's offer and its reread (``candidate_unservable``), and the serve itself
(``serve_presentation``), which retires a pin that became protected. A protected item reads as an absent one.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.exam_protection_review_helpers import _problem_book, _with_exercise
from tests.probe_router_authority_helpers import PROBE_ITEM, call
from tests.probe_router_owned_helpers import SECOND, grading_ready, selected


def _hold_out(case, item_id: str = PROBE_ITEM) -> None:
    """Mark the passage ``item_id`` was made from held out for evaluation, after the pin (the owner's later mark)."""

    _problem_book(case.repository)
    _with_exercise(case.root, item_id, source_id="src_problems", extraction_id="ext_problems", span_id="s2")
    save_unit_selection(case.repository, "ext_problems", ["ex", "notes"],
                        exam_use_modes={"ex": "held_out_evaluation"})
    case.vault = load_vault(case.root)
    case.ctx.load(case.root)


def _presentation(case):
    return case.repository.probe_presentation(case.offer["presentationId"])


def _absent(vault, item_id: str):
    """The vault as if ``item_id`` were not in it (the absent copy a protected item must read as)."""

    return replace(vault, practice_items={key: value for key, value in vault.practice_items.items() if key != item_id})


def test_a_pin_held_out_after_it_was_accepted_is_never_marked_served_by_the_contract_request(tmp_path, monkeypatch):
    """The split request: the item request refuses the held-out item and the contract request, separately, must not
    mark its presentation served. It ends the pin unshown and answers why."""

    from learnloop_sidecar.errors import SidecarError

    case = selected(tmp_path, monkeypatch)
    _hold_out(case)
    grading_ready(monkeypatch)
    with pytest.raises(SidecarError) as refused:
        call(case.ctx, "get_practice_item", {"practiceItemId": PROBE_ITEM, "sessionId": "sess"})
    assert refused.value.code == "held_out_material"
    contract = call(case.ctx, "get_probe_contract", {"practiceItemId": PROBE_ITEM, "sessionId": "sess"})
    assert contract["active"] is False and contract["reason"] == "probe_item_protected"
    presentation = _presentation(case)
    assert presentation.status == "ended" and presentation.end_reason == "invalidated"
    assert presentation.served_at is None


def test_an_item_reserved_for_a_held_out_exam_is_never_served_as_a_probe(tmp_path, monkeypatch):
    case = selected(tmp_path, monkeypatch)
    monkeypatch.setattr(Repository, "reserved_exam_pool_item_ids", lambda _self: {PROBE_ITEM})
    grading_ready(monkeypatch)
    contract = call(case.ctx, "get_probe_contract", {"practiceItemId": PROBE_ITEM, "sessionId": "sess"})
    assert contract["active"] is False and contract["reason"] == "probe_item_protected"
    assert _presentation(case).served_at is None


def test_instrument_selection_reads_a_protected_item_as_an_absent_one(tmp_path, monkeypatch):
    from learnloop.diagnosis.probe_episodes import eligible_instruments

    case = selected(tmp_path, monkeypatch)
    episode = case.repository.probe_episode(_presentation(case).probe_episode_id)
    # The accepted pin reserves its episode for its own item: release it to ask what selection ranks.
    case.repository.end_probe_presentation(case.offer["presentationId"], end_reason="abandoned")
    before = [entry.item.id for entry in eligible_instruments(case.vault, case.repository, episode)]
    assert SECOND in before
    _hold_out(case, SECOND)
    protected = [entry.item.id for entry in eligible_instruments(case.vault, case.repository, episode)]
    absent = [entry.item.id for entry in eligible_instruments(_absent(case.vault, SECOND), case.repository, episode)]
    assert SECOND not in protected
    assert protected == absent


def test_the_learner_lanes_offer_never_names_a_protected_instrument(tmp_path, monkeypatch):
    """Protected after the selection: the status reads the selection void and acceptance pins nothing."""

    from learnloop.diagnosis.causal_orchestrator import candidate_unservable

    case = selected(tmp_path, monkeypatch)
    monkeypatch.setattr(Repository, "reserved_exam_pool_item_ids", lambda _self: {PROBE_ITEM})
    candidate = {"practice_item_id": PROBE_ITEM}
    assert candidate_unservable(case.vault, case.repository, candidate) == "probe_item_protected"


# --- "Keep as practice": the copy keeps its source's locators (G2-R22) ------------------------------------------


KEPT_PROBE = "pi_diag_keepworthy"


def _answered_probe(tmp_path, monkeypatch):
    """A diagnostic probe made from a book's exercise (not protected yet), administered once."""

    from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.writer import upsert_practice_item

    from tests.helpers import NOW_ISO, create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    root = paths.root
    upsert_practice_item(root, {
        "id": KEPT_PROBE, "learning_object_id": "lo_svd_definition", "subjects": None,
        "practice_mode": "diagnostic_probe", "attempt_types_allowed": ["diagnostic_probe", "dont_know"],
        "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
        "prompt": "Problem 1: compute 7 times 6.", "expected_answer": "42", "difficulty": 0.6,
        "difficulty_source": "author", "tags": ["diagnostic"],
        "grading_rubric": {"max_points": 4, "criteria": [{"id": "correctness", "points": 4,
                                                           "description": "Correct."}], "fatal_errors": []},
        "created_at": NOW_ISO, "updated_at": NOW_ISO})
    repository = Repository(paths.sqlite_path)
    _problem_book(repository)
    _with_exercise(root, KEPT_PROBE, source_id="src_problems", extraction_id="ext_problems", span_id="s2")
    vault = load_vault(root)
    sync_vault_state(vault, repository)
    apply_attempt(vault, repository, ApplyAttemptInput(
        draft=AttemptDraft(practice_item_id=KEPT_PROBE, learner_answer_md="42", attempt_type="diagnostic_probe"),
        attempt_id="att_kept", grade=ResolvedGrade(
            rubric_score=4, criterion_points={"correctness": 4}, evidence_rows=[], error_attributions=[],
            grader_confidence=0.9, confidence=3, manual_review_reason=None)))
    return SimpleNamespace(root=root, vault=load_vault(root), repository=repository), "att_kept"


def test_a_kept_copy_is_protected_when_its_passage_is_held_out_later(tmp_path, monkeypatch):
    from learnloop.content.sources import exam_material as EM
    from learnloop.diagnosis.probe_remint import remint_probe_as_practice_item

    case, attempt_id = _answered_probe(tmp_path, monkeypatch)
    kept = remint_probe_as_practice_item(case.root, case.vault, case.repository, attempt_id=attempt_id)
    save_unit_selection(case.repository, "ext_problems", ["ex", "notes"],
                        exam_use_modes={"ex": "held_out_evaluation"})
    vault = load_vault(case.root)
    copy = vault.practice_items[kept["practice_item_id"]]
    assert copy.canonical_exercise is not None
    assert kept["practice_item_id"] in EM.held_out_items(vault, case.repository)
    assert EM.serve_refusals(vault, case.repository, [copy], surface="session_serve") == {
        copy.id: EM.HELD_OUT_MATERIAL}


def test_a_probe_made_from_held_out_material_is_not_kept_as_practice(tmp_path, monkeypatch):
    from learnloop.diagnosis.probe_remint import ProbeRemintError, remint_probe_as_practice_item

    case, attempt_id = _answered_probe(tmp_path, monkeypatch)
    save_unit_selection(case.repository, "ext_problems", ["ex", "notes"],
                        exam_use_modes={"ex": "held_out_evaluation"})
    with pytest.raises(ProbeRemintError) as refused:
        remint_probe_as_practice_item(case.root, load_vault(case.root), case.repository, attempt_id=attempt_id)
    assert refused.value.code == "protected_exam_material"


def test_a_copy_kept_before_the_fix_is_named_by_doctor_and_repaired_by_fix_state(tmp_path, monkeypatch):
    """A remint written the old way (only the probe's id): doctor names it (an error once the passage is protected),
    and ``--fix-state`` copies the locators in, after which the copy is protected."""

    from learnloop.content.sources import exam_material as EM
    from learnloop.diagnosis.probe_remint import _remint_payload
    from learnloop.ops.doctor import run_doctor
    from learnloop.vault.writer import upsert_practice_item

    case, attempt_id = _answered_probe(tmp_path, monkeypatch)
    source = case.vault.practice_items[KEPT_PROBE]
    old = _remint_payload(source, new_id="pi_remint_old", attempt_id=attempt_id, now_iso="2026-11-01T00:00:00Z")
    old.pop("canonical_exercise")
    old["provenance"]["source_refs"] = old["provenance"]["source_refs"][:1]
    upsert_practice_item(case.root, old)
    save_unit_selection(case.repository, "ext_problems", ["ex", "notes"],
                        exam_use_modes={"ex": "held_out_evaluation"})
    assert "pi_remint_old" not in EM.held_out_items(load_vault(case.root), case.repository)
    named = [issue for issue in run_doctor(case.root).issues if issue.code == "remint:missing_source_locators"]
    assert [(issue.entity_id, issue.severity) for issue in named] == [("pi_remint_old", "error")]
    run_doctor(case.root, fix_state=True)
    assert "pi_remint_old" in EM.held_out_items(load_vault(case.root), case.repository)
    assert not [issue for issue in run_doctor(case.root).issues if issue.code == "remint:missing_source_locators"]
