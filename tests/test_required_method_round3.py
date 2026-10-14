"""Method-explicit items, round 3 (the final verify of method-explicit-2,
Codex job 20261014-113512-OQ2Gd7): finished by design, not by patches.

Every reproduction the verify reopened or raised fails on ``e96075e94``:

* F14 (reopened): a generated update ending with a QUOTATION of the canonical
  sentence ("The previous exercise said:" then "Use cofactor expansion in
  your answer.") was adopted as the instruction. The instruction no longer
  lives in the stored statement at all: it is rendered from the frozen
  ``required_method`` field as a separate block wherever the item is shown
  (the presentation's ``required_method_instruction`` block) or sent (the
  grader's question), so whatever the statement quotes, the learner and the
  grader both see the writer's sentence after it;
* F18/F21 (reopened, new): clearing or renaming a method deleted a sentence
  INSIDE a quotation. Nothing edits the statement any more: the field
  changes, the statement stays verbatim;
* F13/F19 (reopened): a historical contract (no recorded
  ``reference_content_hash``) whose graded revision inherited a default
  rubric that has since changed was rebuilt from today's default, which
  excluded the revision actually graded and left the attempt verified on
  its inline twin. The inherited default at that time cannot be recovered,
  so the binding is ambiguous and the regrade is unverified;
* F17/F20 (reopened): a retry with only a missing judgment was planned as
  the whole pipeline (67 calls, over ``max_calls = 1``) before the resume
  check ran. Resumable jobs are detected before route resolution and budget
  planning, and only the unfinished work is estimated;
* F22 (new): selection was persisted candidate by candidate, so an
  interruption left one ``selected`` row that a rerun took for a finished
  selection, stranding the other chosen candidate. The complete selected
  order and a completion marker are persisted atomically; a rerun resumes
  the judgment only after the marker exists and otherwise finishes the
  selection first.

Fakes only; no network.
"""

from __future__ import annotations

import json
from contextlib import closing

import pytest
import yaml

from learnloop.ai.spend import SpendCaps
from learnloop.attempts.grading import build_grading_context
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.required_method import required_method_problems
from learnloop_sidecar.handlers.serializers import item_presentation

from tests.helpers import create_basic_vault

ITEM = "pi_svd_define_001"
METHOD = "cofactor expansion"
SENTENCE = "Use cofactor expansion in your answer."
STAMP = "2026-10-14T00:00:00Z"

#: The verify's F14 reproduction: a generated update of an existing
#: cofactor-expansion item whose final paragraph QUOTES the sentence.
F14_UPDATE = "Compute det(B). The previous exercise said:\n\nUse cofactor expansion in your answer."
#: The verify's F21 reproduction: the sentence inside a quotation.
F21_BODY = ('Read the old rule: "Compute det(A). Use cofactor expansion in your answer. Then check your work." '
            "Compute det(B).")


def _method_item(tmp_path, prompt: str):
    """The basic vault's item as a generated item requiring cofactor
    expansion, its stored statement ``prompt``."""

    from learnloop.vault.writer import upsert_practice_item

    paths = create_basic_vault(tmp_path / "vault")
    data = load_vault(paths.root).practice_items[ITEM].model_dump(mode="json")
    data["prompt"] = prompt
    data["required_method"] = {"name": METHOD, "criterion_ids": ["correctness"]}
    upsert_practice_item(paths.root, data)
    return paths, Repository(paths.sqlite_path)


def _update_proposal(tmp_path, repository, item_id: str, payload: dict) -> tuple[str, dict]:
    """A generated update of ``item_id`` through the authoring proposal path."""

    from learnloop.clock import FrozenClock
    from learnloop.content.proposals.ai_contracts import AuthoringProposal
    from learnloop.content.proposals.proposals import persist_authoring_proposal
    from tests.helpers import NOW

    proposal = AuthoringProposal.model_validate({
        "summary": "update", "source_refs": [{"ref_type": "manual_context", "ref_id": "manual"}],
        "items": [{"client_item_id": "u1", "item_type": "practice_item", "operation": "update",
                   "target": {"entity_type": "practice_item", "entity_id": item_id},
                   "source_ref_ids": ["manual"], "rationale": "r", "review_route": "review_required",
                   "payload": payload}],
    })
    patch_id = persist_authoring_proposal(tmp_path / "vault", proposal, provider="import", clock=FrozenClock(NOW))
    [row] = repository.proposal_items(patch_id)
    return patch_id, row


def _errors(item, vault) -> list[str]:
    return [problem.code for problem in required_method_problems(item, vault.rubric_for_item(item))
            if problem.severity == "error"]


# -- F14: the instruction is rendered from the field, never adopted from the statement ----------


def test_f14_a_generated_update_quoting_the_sentence_is_stored_verbatim_and_the_block_rendered(tmp_path):
    from learnloop.content.proposals.proposals import accept_items

    paths, repository = _method_item(tmp_path, "Compute det(A).")
    patch_id, _row = _update_proposal(tmp_path, repository, ITEM, {"prompt": F14_UPDATE})
    accept_items(paths.root, patch_id)
    vault = load_vault(paths.root)
    item = vault.practice_items[ITEM]
    # The statement is stored as generated: nothing appended, nothing adopted.
    assert item.prompt == F14_UPDATE
    assert item.required_method.name == METHOD
    # The learner sees the quotation, then the writer's own block.
    blocks = item_presentation(item)["blocks"]
    assert [block["kind"] for block in blocks] == ["prompt", "required_method_instruction"]
    assert blocks[0]["markdown"] == F14_UPDATE
    assert blocks[1]["markdown"] == SENTENCE
    # The grader is sent the same rendered instruction after the statement.
    context = build_grading_context(vault, item, attempt_id="a1", learner_answer_md="x")
    assert context.prompt == f"{F14_UPDATE}\n\n{SENTENCE}"
    # Validation reads no statement text for the instruction.
    assert _errors(item, vault) == []


def test_f14_the_grader_renders_the_instruction_the_frozen_contract_presented(tmp_path):
    """The grader's question comes from the contract the learner answered:
    its statement and its method, whatever the item says now."""

    from learnloop.learner.assessment_contracts import compile_assessment_contract
    from learnloop.vault.writer import upsert_practice_item

    paths, _repository = _method_item(tmp_path, "Compute det(A).")
    vault = load_vault(paths.root)
    item = vault.practice_items[ITEM]
    contract = compile_assessment_contract(vault, item, rubric=vault.rubric_for_item(item))
    data = item.model_dump(mode="json")
    data["required_method"] = None
    upsert_practice_item(paths.root, data)
    vault = load_vault(paths.root)
    cleared = vault.practice_items[ITEM]
    frozen = build_grading_context(vault, cleared, attempt_id="a1", learner_answer_md="x",
                                   assessment_contract=contract)
    assert frozen.prompt == f"Compute det(A).\n\n{SENTENCE}"
    # The item without a method, graded as it is now: no block.
    assert build_grading_context(vault, cleared, attempt_id="a1", learner_answer_md="x").prompt == "Compute det(A)."


def test_every_surface_renders_the_instruction_only_for_a_method_item(tmp_path):
    """The presentation's block, the exam review, the adjudication case and
    the guided redo show the statement then the rendered instruction; an item
    without a required method is shown exactly as before."""

    from learnloop_sidecar.handlers.exams import _item_review_fields
    from learnloop_sidecar.handlers.serializers import PRESENTATION_BLOCK_KINDS

    assert PRESENTATION_BLOCK_KINDS.index("prompt") < PRESENTATION_BLOCK_KINDS.index("required_method_instruction")
    plain_paths = create_basic_vault(tmp_path / "plain")
    plain = load_vault(plain_paths.root).practice_items[ITEM]
    assert item_presentation(plain)["blocks"] == [{"kind": "prompt", "markdown": "Define SVD.", "label": None}]
    assert _item_review_fields(load_vault(plain_paths.root), None, ITEM)["prompt"] == "Define SVD."
    paths, _repository = _method_item(tmp_path, "Compute det(A).")
    vault = load_vault(paths.root)
    assert _item_review_fields(vault, None, ITEM)["prompt"] == f"Compute det(A).\n\n{SENTENCE}"
    assert [block["kind"] for block in item_presentation(vault.practice_items[ITEM])["blocks"]] == [
        "prompt", "required_method_instruction"]


def test_the_reader_quick_check_and_the_tutors_practice_tool_render_the_instruction(tmp_path):
    """The Reader's placed quick check (an answering surface) and the
    tutor's typed practice tool (a chat read path that shows stems) show the
    statement then the rendered instruction, and an item without a required
    method exactly as before."""

    from types import SimpleNamespace

    from learnloop.instructional.tools import _practice_view, _Withhold
    from learnloop.reader.reader_guidance import build_guide_plan
    from learnloop.vault.models import RequiredMethod
    from tests.test_reader_guidance import _place_question, _setup

    vault, repository = _setup(tmp_path)
    _place_question(repository)
    item = vault.practice_items[ITEM]
    withhold = _Withhold(vault, SimpleNamespace(item_id=None))
    listed = {"items": [{"practice_item_id": ITEM}]}
    assert build_guide_plan(vault, repository, extraction_id="ext1")["sections"][0]["question"]["prompt"] == \
        item.prompt
    assert _practice_view(vault, listed, withhold)["items"][0]["prompt"] == item.prompt
    item.required_method = RequiredMethod(name=METHOD, criterion_ids=["correctness"])
    question = build_guide_plan(vault, repository, extraction_id="ext1")["sections"][0]["question"]
    assert question["prompt"] == f"{item.prompt}\n\n{SENTENCE}"
    assert _practice_view(vault, listed, withhold)["items"][0]["prompt"] == f"{item.prompt} {SENTENCE}"


def test_a_published_pf_variant_is_presented_with_the_parents_instruction(tmp_path):
    """The variant's stem is stored as generated; the instruction comes from
    the field it inherited."""

    from tests.pf_fakes import clients
    from tests.test_pf_generation import run
    from tests.test_required_method_authority import VARIANT_CONSISTENT, StatementDecider, _pf_method_vault

    _needs_bwrap()
    _repository, paths = _pf_method_vault(tmp_path)
    report = run(paths, publish=True, select=1,
                 fakes=clients(required_method_judge=StatementDecider(VARIANT_CONSISTENT)))
    [item_id] = report["published_item_ids"]
    item = load_vault(paths.root).practice_items[item_id]
    assert "in your answer" not in item.prompt and item.required_method.name == "substitution"
    blocks = item_presentation(item)["blocks"]
    assert blocks[-1] == {"kind": "required_method_instruction", "markdown": "Use substitution in your answer.",
                          "label": None}


# -- F21 (F18 reopened): clearing or renaming never edits the statement --------------------------


@pytest.mark.parametrize("stored", [F21_BODY, f"{F21_BODY}\n\n{SENTENCE}"], ids=["statement", "legacy_block"])
def test_f21_clearing_or_renaming_never_edits_the_statement(tmp_path, stored):
    from learnloop.content.proposals.proposals import accept_items
    from learnloop.content.proposals.required_method_override import (
        override_payload, propose_required_method_override,
    )

    paths, repository = _method_item(tmp_path, stored)
    vault = load_vault(paths.root)
    cleared = override_payload(vault, ITEM, clear=True)
    assert cleared["to"] is None and "prompt" not in cleared["payload"]
    renamed = override_payload(vault, ITEM, name="row reduction", criterion_ids=["correctness"])
    assert renamed["to"]["name"] == "row reduction" and "prompt" not in renamed["payload"]
    proposed = propose_required_method_override(vault, repository, ITEM, clear=True)
    accept_items(paths.root, proposed["proposal_id"])
    after = load_vault(paths.root).practice_items[ITEM]
    # The quotation (and a legacy line, if any) is left exactly as stored.
    assert after.prompt == stored and after.required_method is None
    assert 'Use cofactor expansion in your answer. Then check your work."' in after.prompt


# -- F13/F19: a historical binding whose inherited default cannot be recovered fails closed ------


def _write_default(paths, mode: str, rubric: dict, prefix: str) -> None:
    changed = json.loads(json.dumps(rubric))
    for criterion in changed["criteria"]:
        criterion["description"] = prefix + criterion["description"]
    (paths.root / "rubrics").mkdir(exist_ok=True)
    (paths.root / "rubrics" / f"{mode}.yaml").write_text(yaml.safe_dump({
        "schema_version": 1, "id": f"default_{mode}", "applies_to": {"practice_mode": mode}, "rubric": changed,
    }, sort_keys=False), encoding="utf-8")


def _preserve_snapshot(repository, item) -> None:
    """The item exactly as it was graded, as a scheduler snapshot records it."""

    from learnloop.vault.hashes import practice_item_hash

    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            connection.execute(
                "INSERT OR IGNORE INTO practice_item_snapshots(content_hash, practice_item_id, item_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (practice_item_hash(item), item.id, json.dumps(item.model_dump(mode="json"), sort_keys=True), STAMP),
            )


@pytest.mark.parametrize("disputed", [True, False], ids=["graded_revision_disputed", "graded_revision_verified"])
@pytest.mark.parametrize("historical", [True, False], ids=["historical", "recorded"])
def test_f19_a_changed_inherited_default_leaves_a_historical_regrade_unverified(gated_successor, historical,
                                                                                disputed):
    """The verify's reproduction: graded under the inherited rubric R (its
    snapshot preserved), the default later changed to R2, the item edited and
    R written inline; the inline-R twin of the graded statement is checked
    verified (and the revision graded is disputed). A historical contract
    cannot recover the default at that time, so the regrade is unverified;
    a recorded contract binds the revision graded exactly."""

    from learnloop.db.stores.source_service import reference_content_hash
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _attempt, _bindings, _regrade, _status
    from tests.test_required_method_rereview import (
        _check, _edit_and_materialize, _inherited_rubric_item, _make_historical,
    )

    paths, repository, spans = gated_successor
    item_id, criterion, default = _inherited_rubric_item(paths, repository, spans)
    item = loaded(paths).practice_items[item_id]
    graded = reference_content_hash(item)
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    assert _status(repository, attempt.attempt_id) == "verified"
    _preserve_snapshot(repository, item)
    if historical:
        _make_historical(repository, attempt.attempt_id)
    _write_default(paths, item.practice_mode, default.model_dump(mode="json"), "Revised default: ")
    graded_inline, _current = _edit_and_materialize(paths, item_id, default)
    _check(repository, item_id, graded_inline, "book_solution", "rkc_inline_twin", "2026-02-01T00:00:00Z")
    if disputed:
        _check(repository, item_id, graded, "disputed", "rkc_graded_disputed", "2099-01-01T00:00:00Z")
    _regrade(paths, repository, attempt.attempt_id)
    if historical or disputed:
        assert _status(repository, attempt.attempt_id) == "unverified"
        [binding] = _bindings(repository, attempt.attempt_id)
        assert binding["right_id"] == graded
        assert ("graded_revision=ambiguous" if historical else "graded_revision=frozen") in binding["rationale"]
    else:
        # The recorded revision graded is verified: the regrade stays verified.
        assert _status(repository, attempt.attempt_id) == "verified"
        assert _bindings(repository, attempt.attempt_id) == []


@pytest.fixture
def gated_successor(tmp_path, monkeypatch):
    from learnloop.algorithm_versions import METHOD_EXPLICIT_ALGORITHM_VERSION
    from learnloop.content.authoring import pf_sandbox
    from tests.helpers import set_algorithm_version
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_algorithm_version(paths, METHOD_EXPLICIT_ALGORITHM_VERSION)
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    return paths, repository, spans


# -- F17/F20: a resumable job is planned as its unfinished work only -----------------------------

GENEROUS_BUT_ONE_CALL = SpendCaps(max_candidates=100, max_pairs=2000, max_calls=1, max_total_tokens=100_000_000,
                                  max_estimated_usd=10_000)


def _needs_bwrap():
    from learnloop.content.authoring.pf_sandbox import sandbox_available

    if not sandbox_available():
        pytest.skip("bubblewrap is not installed")


def test_f20_a_missing_judgment_alone_fits_max_calls_one(tmp_path):
    """The verify's reproduction: a partially published two-candidate request
    with one missing judgment, retried with ``max_calls = 1`` and otherwise
    generous caps. The plan counts the missing judgment alone (no route of
    the pipeline is resolved) and the retry admits the request."""

    from learnloop.ai.errors import AIProviderUnavailable
    from tests.pf_fakes import clients, enable_pf
    from tests.test_pf_generation import all_calls, rows, run
    from tests.test_required_method_authority import VARIANT_CONSISTENT, StatementDecider, _pf_method_vault
    from tests.test_required_method_reopened import _mint_status
    from tests.test_required_method_rereview import FailingOnceDecider

    _needs_bwrap()
    repository, paths = _pf_method_vault(tmp_path)
    enable_pf(paths.root, max_published_per_day=5)
    first = run(paths, publish=True, select=2, fakes=clients(
        required_method_judge=FailingOnceDecider(VARIANT_CONSISTENT, AIProviderUnavailable("timed out"))))
    [family] = first["families"]
    assert family["status"] == "judgment_incomplete" and len(family["published_item_ids"]) == 1
    [waiting] = rows(repository, "status='selected'")
    dry = run(paths, publish=True, select=2, caps=GENEROUS_BUT_ONE_CALL, dry_run=True,
              fakes=clients(required_method_judge=StatementDecider(VARIANT_CONSISTENT)))
    assert dry["status"] == "dry_run", dry.get("reason")
    assert dry["estimate"]["metered"]["calls"] + dry["estimate"]["subscription"]["calls"] == 1
    resumed_fakes = clients(required_method_judge=StatementDecider(VARIANT_CONSISTENT))
    second = run(paths, publish=True, select=2, caps=GENEROUS_BUT_ONE_CALL, fakes=resumed_fakes)
    assert second["status"] == "complete", second.get("reason")
    [family] = second["families"]
    assert family["status"] == "complete" and family["resumed"] == "required_method_judgment"
    assert len(resumed_fakes["required_method_judge"].calls) == 1
    assert all_calls({key: value for key, value in resumed_fakes.items() if key != "required_method_judge"}) == 0
    assert _mint_status(repository) == ["admitted"]
    assert waiting["id"] in {row["id"] for row in rows(repository, "status='published'")}


def test_f20_a_resumable_job_resolves_no_pipeline_route_and_plans_no_pipeline_work(tmp_path):
    """Only the unfinished work is planned: no skeleton, generation, panel,
    freshness or selection call, and no pipeline route resolved (none is
    reported), so a route the rerun does not need cannot refuse it."""

    from learnloop.ai.errors import AIProviderUnavailable
    from tests.pf_fakes import clients, enable_pf
    from tests.test_pf_generation import run
    from tests.test_required_method_authority import VARIANT_CONSISTENT, StatementDecider, _pf_method_vault
    from tests.test_required_method_rereview import FailingOnceDecider

    _needs_bwrap()
    _repository, paths = _pf_method_vault(tmp_path)
    enable_pf(paths.root, max_published_per_day=5)
    run(paths, publish=True, select=2, fakes=clients(
        required_method_judge=FailingOnceDecider(VARIANT_CONSISTENT, AIProviderUnavailable("timed out"))))
    dry = run(paths, publish=True, select=2, dry_run=True,
              fakes=clients(required_method_judge=StatementDecider(VARIANT_CONSISTENT)))
    [plan] = dry["plan"]
    assert plan["roles"] == {} and plan["candidates"] == 0 and plan["freshness_pairs"] == 0
    assert plan["resume"]["stage"] == "judgment" and plan["resume"]["missing_judgments"] == 1
    assert plan["required_method_judgment"]["calls"] == 1
    assert dry["routes"] == {}
    [state] = dry["resumable"].values()
    assert state["stage"] == "judgment" and state["missing_judgments"] == 1


# -- F22: selection is persisted whole, with a completion marker --------------------------------


def _family_rows(repository):
    from tests.test_pf_generation import rows

    return [row for row in rows(repository) if row["generation_path"] != "single_shot"]


def test_f22_an_interrupted_selection_is_finished_before_any_judgment(tmp_path, monkeypatch):
    """The verify's reproduction: the run stops after the first candidate's
    selection update commits. The rerun never takes that for a finished
    selection: every chosen candidate is judged and published, none is left
    a survivor."""

    from learnloop.ai.errors import AIInterrupted
    from learnloop.ops import pf_generation
    from tests.pf_fakes import clients, enable_pf
    from tests.test_pf_generation import rows, run
    from tests.test_required_method_authority import VARIANT_CONSISTENT, StatementDecider, _pf_method_vault
    from tests.test_required_method_reopened import _mint_status

    _needs_bwrap()
    repository, paths = _pf_method_vault(tmp_path)
    enable_pf(paths.root, max_published_per_day=5)
    original = pf_generation.store.update_candidate
    seen = {"selection_writes": 0}

    def interrupting(connection, candidate_id, **fields):
        if fields.get("status") in ("selected", "not_selected"):
            seen["selection_writes"] += 1
            if seen["selection_writes"] == 2:
                raise AIInterrupted("stopped after the first candidate's selection update")
        return original(connection, candidate_id, **fields)

    monkeypatch.setattr(pf_generation.store, "update_candidate", interrupting)
    first = run(paths, publish=True, select=2, fakes=clients(required_method_judge=StatementDecider(VARIANT_CONSISTENT)))
    assert first["status"] == "cancelled"
    # The selection is persisted whole or not at all: no partial selection.
    assert [row["id"] for row in _family_rows(repository) if row["selection_json"]] == []
    monkeypatch.setattr(pf_generation.store, "update_candidate", original)
    judge = StatementDecider(VARIANT_CONSISTENT)
    second = run(paths, publish=True, select=2, fakes=clients(required_method_judge=judge))
    assert second["status"] == "complete", second.get("reason")
    [family] = second["families"]
    assert family["status"] == "complete"
    assert len(family.get("published_item_ids", [])) == 2, family
    assert len(judge.calls) == 2
    assert [row for row in _family_rows(repository) if row["status"] in ("survivor", "selected")] == []
    assert _mint_status(repository) == ["admitted"]
    assert len(rows(repository, "status='published'")) == 2


def test_f22_a_partial_selection_left_by_an_earlier_run_is_finished_first(tmp_path):
    """The state the verify reproduced, written directly: one ``selected``
    row with ``selection_json`` and the other chosen candidate a survivor
    without it (no completion marker). The rerun finishes the selection,
    then judges and publishes both chosen candidates."""

    from learnloop.ai.errors import AIProviderUnavailable
    from tests.pf_fakes import clients, enable_pf
    from tests.test_pf_generation import all_calls, run
    from tests.test_required_method_authority import VARIANT_CONSISTENT, StatementDecider, _pf_method_vault
    from tests.test_required_method_reopened import FailingDecider, _mint_status

    _needs_bwrap()
    repository, paths = _pf_method_vault(tmp_path)
    enable_pf(paths.root, max_published_per_day=5)
    first = run(paths, publish=True, select=2,
                fakes=clients(required_method_judge=FailingDecider(AIProviderUnavailable("timed out"))))
    [family] = first["families"]
    assert family["status"] == "judgment_incomplete"
    chosen = [row for row in _family_rows(repository) if row["status"] == "selected"]
    assert len(chosen) == 2
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            for row in _family_rows(repository):
                if row["id"] == chosen[0]["id"]:
                    selection = json.loads(row["selection_json"])
                    for marker in ("selected_order", "selection_complete"):
                        selection.pop(marker, None)
                    connection.execute("UPDATE pf_candidates SET selection_json=? WHERE id=?",
                                       (json.dumps(selection, sort_keys=True), row["id"]))
                elif row["status"] in ("selected", "not_selected"):
                    connection.execute(
                        "UPDATE pf_candidates SET status='survivor', selection_json=NULL WHERE id=?", (row["id"],))
    judge = StatementDecider(VARIANT_CONSISTENT)
    resumed_fakes = clients(required_method_judge=judge)
    second = run(paths, publish=True, select=2, fakes=resumed_fakes)
    assert second["status"] == "complete", second.get("reason")
    [family] = second["families"]
    assert family["status"] == "complete" and family["resumed"] == "selection"
    assert len(family.get("published_item_ids", [])) == 2, family
    assert len(judge.calls) == 2
    # Only the selection is finished: its judge's request is the checkpointed
    # one, and nothing upstream (generation, panel, freshness) runs again.
    assert all_calls({key: value for key, value in resumed_fakes.items() if key != "required_method_judge"}) == 0
    assert [row for row in _family_rows(repository) if row["status"] in ("survivor", "selected")] == []
    assert _mint_status(repository) == ["admitted"]
