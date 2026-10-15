"""Method-explicit items, the reopened verify (Codex job 20261014-013257-ASCzCS).

The redesign made the item's ``required_method`` field the one authority and
had writers make the text agree with it. The verify found five ways the text,
the ledger or the certification status could still drift from that field:

* F14: a canonical sentence QUOTED inside generated text counted as the
  instruction. Its tests are retired by round 3, which renders the
  instruction from the field and stores none in the statement
  (``tests/test_required_method_round3.py``);
* F15: a generated update proposal could replace a source statement while
  the item kept the judgment made on the OLD statement. Such an edit is now
  refused (a judged statement is never rewritten through a proposal); a
  generated item's new prompt is stored as generated;
* F13: a frozen regrade of an edited item skipped verification binding, so a
  later dispute of the revision it graded never lowered the attempt. The
  regrade now binds the revision it graded;
* F16: an accepted owner override reached the YAML but not
  ``judgment_ledger``. Acceptance now appends the owner's verdict, write-ahead
  and idempotently, superseding the prior verdict on the same question;
* F17: a transient failure of the PF publication judgment marked the run's
  mint request admitted, stranding paid, verified candidates. The request now
  stays retryable until every selected variant has a verdict, and a rerun of
  the round resumes from checkpoints without regenerating anything.

Fakes only; no network.
"""

from __future__ import annotations

import json
from contextlib import closing

import pytest

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.required_method import presented_prompt

from tests.helpers import create_basic_vault
from tests.test_required_method_authority import (
    REQUIRES,
    SOURCE_REPRODUCTIONS,
    SVD,
    StatementDecider,
    _import,
    _ledger,
)

# -- F15: a judged statement is never rewritten through a proposal ------------------------------


def _update_proposal(tmp_path, repository, item_id: str, payload: dict) -> tuple[str, dict]:
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


def _judged_source_item(tmp_path):
    from learnloop.content.proposals.method_statement_judge import LazyStatementJudge, resolve_statement_judge

    def judge():
        return resolve_statement_judge(load_vault(tmp_path / "vault"), clients=StatementDecider(REQUIRES))

    item, _result, repository = _import(tmp_path, SOURCE_REPRODUCTIONS["which_clause"],
                                        method_judge=LazyStatementJudge(judge))
    assert (item.required_method.statement, item.required_method.decided_by) == ("source", "judgment")
    return item, repository


def test_f15_a_generated_update_that_rewrites_a_judged_source_statement_is_refused(tmp_path):
    """The verify's reproduction: the update proposes a new statement and a new
    method. The method key was already dropped; the statement edit is now
    invalid, never merged with the old field and its judgment."""

    from learnloop.content.proposals.patches import PatchApplicationError
    from learnloop.content.proposals.proposals import accept_items

    item, _repository = _judged_source_item(tmp_path)
    judgment = item.required_method.judgment_id
    patch_id, row = _update_proposal(tmp_path, _repository, item.id, {
        "prompt": "Factor A using row reduction.",
        "required_method": {"name": "row reduction", "criterion_ids": ["factorization"]},
    })
    assert "required_method" not in row["payload"]
    assert row["validation_status"] == "invalid"
    assert "required_method:source_statement_edited" in row["validation_errors"]
    with pytest.raises(PatchApplicationError):
        accept_items(tmp_path / "vault", patch_id)
    after = load_vault(tmp_path / "vault").practice_items[item.id]
    assert after.prompt == SOURCE_REPRODUCTIONS["which_clause"]
    assert after.required_method.judgment_id == judgment


def test_f15_an_owner_edit_of_a_pending_update_cannot_rewrite_the_statement_either(tmp_path):
    from learnloop.content.proposals.patches import PatchApplicationError, compile_proposal_item
    from learnloop.content.proposals.proposals import edit_proposal_item

    item, _repository = _judged_source_item(tmp_path)
    patch_id, row = _update_proposal(tmp_path, _repository, item.id, {"hints": ["Start from A^T A."]})
    assert row["validation_status"] != "invalid", row["validation_errors"]
    edited = edit_proposal_item(tmp_path / "vault", patch_id, row["id"],
                                {**row["payload"], "prompt": "Factor A using row reduction."})
    assert edited["validation_status"] == "invalid"
    assert "required_method:source_statement_edited" in edited["validation_errors"]
    # The apply chokepoint refuses it whatever the row's recorded status.
    forced = {**edited, "validation_status": "valid"}
    with pytest.raises(PatchApplicationError, match="source statement"):
        compile_proposal_item(load_vault(tmp_path / "vault"), forced)


def test_f15_a_whitespace_only_restatement_keeps_the_verbatim_statement_and_applies(tmp_path):
    from learnloop.content.proposals.proposals import accept_items

    item, _repository = _judged_source_item(tmp_path)
    patch_id, row = _update_proposal(tmp_path, _repository, item.id, {
        "prompt": "  " + SOURCE_REPRODUCTIONS["which_clause"].replace(" ", "  ") + "\n", "hints": ["A hint."],
    })
    assert row["validation_status"] != "invalid" and "prompt" not in row["payload"]
    accept_items(tmp_path / "vault", patch_id)
    after = load_vault(tmp_path / "vault").practice_items[item.id]
    assert after.prompt == SOURCE_REPRODUCTIONS["which_clause"] and after.hints == ["A hint."]
    assert after.required_method.judgment_id == item.required_method.judgment_id


def test_f15_a_generated_items_new_prompt_is_stored_as_generated(tmp_path):
    """A generated (instruction) item: an update that rewrites the prompt is
    stored exactly as generated (round 3: the instruction is rendered from
    the field, never written into the statement), and the item keeps its
    field."""

    from learnloop.content.proposals.proposals import accept_items
    from learnloop.content.proposals.required_method_override import propose_required_method_override

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    proposed = propose_required_method_override(load_vault(paths.root), repository, "pi_svd_define_001",
                                                name=SVD, criterion_ids=["correctness"])
    accept_items(paths.root, proposed["proposal_id"])
    assert load_vault(paths.root).practice_items["pi_svd_define_001"].prompt == "Define SVD."
    patch_id, row = _update_proposal(tmp_path, repository, "pi_svd_define_001",
                                     {"prompt": "Define the SVD of a 2x2 matrix A."})
    assert row["payload"]["prompt"] == "Define the SVD of a 2x2 matrix A."
    assert row["validation_status"] != "invalid", row["validation_errors"]
    accept_items(paths.root, patch_id)
    item = load_vault(paths.root).practice_items["pi_svd_define_001"]
    assert item.prompt == "Define the SVD of a 2x2 matrix A." and item.required_method.name == SVD
    assert presented_prompt(item.prompt, item.required_method) == (
        f"Define the SVD of a 2x2 matrix A.\n\nUse {SVD} in your answer.")


def test_f15_a_generated_update_renaming_the_method_changes_only_the_field(tmp_path):
    from learnloop.content.proposals.proposals import accept_items
    from learnloop.content.proposals.required_method_override import propose_required_method_override

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    proposed = propose_required_method_override(load_vault(paths.root), repository, "pi_svd_define_001",
                                                name=SVD, criterion_ids=["correctness"])
    accept_items(paths.root, proposed["proposal_id"])
    before = load_vault(paths.root).practice_items["pi_svd_define_001"]
    renamed = "the singular value decomposition"
    _patch_id, row = _update_proposal(tmp_path, repository, before.id, {
        "required_method": {"name": renamed, "criterion_ids": ["correctness"]}})
    assert row["payload"]["required_method"]["name"] == renamed
    assert "prompt" not in row["payload"]
    # A method the item's targets do not name is dropped: the item keeps its
    # field and its prompt untouched.
    _patch_id, row = _update_proposal(tmp_path, repository, before.id, {
        "required_method": {"name": "row reduction", "criterion_ids": ["correctness"]}})
    assert "required_method" not in row["payload"] and "prompt" not in row["payload"]


# -- F13: a frozen regrade binds the revision it graded -----------------------------------------


def _dispute(repository, item, check_id: str) -> str:
    from learnloop.db.stores.source_service import insert_key_check, reference_content_hash

    content = reference_content_hash(item)
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            insert_key_check(connection, id=check_id, practice_item_id=item.id, content_hash=content,
                             key_status="disputed", rung="test", trigger="verify",
                             started_at="2099-01-01T00:00:00Z", created_at="2099-01-01T00:00:00Z")
    return content


def test_f13_a_later_dispute_of_the_graded_revision_lowers_a_frozen_regrade(gated_successor):
    """The verify's reproduction: graded verified, its revision disputed, the
    item edited; the frozen regrade binds the revision it graded, so the
    dispute lowers the attempt (and the binding names that revision)."""

    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _attempt, _bindings, _edit_key, _regrade, _status
    from tests.test_required_method_authority import _verified_method_import

    paths, repository, spans = gated_successor
    item_id, criterion = _verified_method_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    assert _status(repository, attempt.attempt_id) == "verified"
    graded = _dispute(repository, loaded(paths).practice_items[item_id], "rkc_disputed_graded")
    _edit_key(paths, repository, item_id)
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
    [binding] = _bindings(repository, attempt.attempt_id)
    assert (binding["right_kind"], binding["right_id"], binding["input_hash"]) == (
        "reference_content", graded, graded)
    assert "graded_revision=frozen" in binding["rationale"]


def test_f13_a_dispute_of_the_edited_revision_never_lowers_the_frozen_regrade(gated_successor):
    """Historical verification against unrelated revisions stands: the
    dispute is of the CURRENT (edited) content, not the content graded."""

    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _attempt, _bindings, _edit_key, _regrade, _status
    from tests.test_required_method_authority import _verified_method_import

    paths, repository, spans = gated_successor
    item_id, criterion = _verified_method_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    _edit_key(paths, repository, item_id)
    _dispute(repository, loaded(paths).practice_items[item_id], "rkc_disputed_current")
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    assert _bindings(repository, attempt.attempt_id) == []


@pytest.mark.parametrize("disputed", [False, True], ids=["all_verified", "graded_revision_disputed"])
def test_f13_when_the_graded_revision_cannot_be_rebuilt_it_needs_a_fresh_check(gated_successor, disputed):
    """The rubric changed too, so the graded revision's key hash cannot be
    rebuilt from a HISTORICAL frozen method contract (one frozen before
    contracts recorded the hash, review F19). Its binding is ambiguous
    (method-explicit-3 final verify): the checked revisions include the
    question before its method was set, so none of them decides it, verified
    or disputed. It needs a fresh check: the regrade is lowered either way."""

    from learnloop.vault.writer import upsert_practice_item
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _attempt, _bindings, _regrade, _status
    from tests.test_required_method_authority import _verified_method_import
    from tests.test_required_method_rereview import _make_historical

    paths, repository, spans = gated_successor
    item_id, criterion = _verified_method_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    _make_historical(repository, attempt.attempt_id)
    if disputed:
        _dispute(repository, loaded(paths).practice_items[item_id], "rkc_disputed_unrebuilt")
    data = loaded(paths).practice_items[item_id].model_dump(mode="json")
    data["grading_rubric"]["criteria"][-1]["description"] += " (reworded)"
    data["expected_answer"] = "x = 6"
    upsert_practice_item(paths.root, data)
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
    [binding] = _bindings(repository, attempt.attempt_id)
    assert binding["right_id"].startswith("unrebuilt:")
    assert "key_status=changed_since_check" in binding["rationale"]
    assert "graded_revision=ambiguous_method" in binding["rationale"]


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


# -- F16: an accepted owner override is the owner's verdict in judgment_ledger -------------------


def _owner_rows(repository):
    return [row for row in _ledger(repository) if row["judge"] == "owner"]


def test_f16_an_accepted_override_appends_the_owners_verdict_superseding_the_judgment(tmp_path):
    from learnloop.content.proposals.method_statement_judge import TASK, statement_input_hash
    from learnloop.content.proposals.proposals import accept_items
    from learnloop.content.proposals.required_method_override import (
        OVERRIDE_VERSION,
        propose_required_method_override,
    )

    item, repository = _judged_source_item(tmp_path)
    root = tmp_path / "vault"
    [judgment] = _ledger(repository)
    proposed = propose_required_method_override(load_vault(root), repository, item.id, name=SVD,
                                                criterion_ids=["factorization"])
    assert _owner_rows(repository) == []  # nothing until accepted
    accept_items(root, proposed["proposal_id"])
    [owner] = _owner_rows(repository)
    assert (owner["task"], owner["left_kind"], owner["left_id"], owner["right_kind"], owner["right_id"]) == (
        TASK, "practice_item", item.id, "required_method", SVD)
    assert (owner["verdict"], owner["prompt_version"], owner["judge_model"]) == ("requires", OVERRIDE_VERSION, None)
    assert owner["supersedes_id"] == judgment["id"]
    assert owner["input_hash"] == statement_input_hash("source", item.prompt, SVD)
    rationale = json.loads(owner["rationale"])
    assert rationale["statement"] == "source" and rationale["prior_judgment_id"] == judgment["id"]
    assert rationale["proposal_id"] == proposed["proposal_id"] and rationale["criterion_ids"] == ["factorization"]

    cleared = propose_required_method_override(load_vault(root), repository, item.id, clear=True)
    accept_items(root, cleared["proposal_id"])
    rows = _owner_rows(repository)
    assert len(rows) == 2
    [clear] = [row for row in rows if row["id"] != owner["id"]]
    assert (clear["verdict"], clear["right_id"], clear["supersedes_id"]) == ("not_required", SVD, owner["id"])


def test_f16_a_generated_items_override_is_ledgered_and_the_write_is_idempotent(tmp_path):
    from learnloop.content.proposals.apply_protocol import _perform_side_effect
    from learnloop.content.proposals.patches import compile_proposal_item
    from learnloop.content.proposals.proposals import accept_items
    from learnloop.content.proposals.required_method_override import propose_required_method_override

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    proposed = propose_required_method_override(load_vault(paths.root), repository, "pi_svd_define_001",
                                                name=SVD, criterion_ids=["correctness"])
    [row] = repository.proposal_items(proposed["proposal_id"])
    compiled = compile_proposal_item(load_vault(paths.root), row)
    assert compiled.db_side_effect["kind"] == "required_method_owner_verdict"
    accept_items(paths.root, proposed["proposal_id"])
    [owner] = _owner_rows(repository)
    assert (owner["verdict"], owner["supersedes_id"]) == ("requires", None)
    assert json.loads(owner["rationale"])["statement"] == "instruction"
    # Recovery re-runs the side effect harmlessly (the id is fixed in the intent).
    side_effect = {"kind": compiled.db_side_effect["kind"],
                   "row": {**compiled.db_side_effect["row"], "patch_id": proposed["proposal_id"]}}
    _perform_side_effect(repository, side_effect, owner["created_at"], None)
    assert len(_owner_rows(repository)) == 1


def test_f16_a_generated_update_is_no_owner_verdict(tmp_path):
    from learnloop.content.proposals.proposals import accept_items

    item, repository = _judged_source_item(tmp_path)
    patch_id, row = _update_proposal(tmp_path, repository, item.id, {"hints": ["A hint."]})
    accept_items(tmp_path / "vault", patch_id)
    assert _owner_rows(repository) == []


# -- F17: a PF judgment failure leaves the job retryable -----------------------------------------


class FailingDecider(StatementDecider):
    def __init__(self, error):
        super().__init__(REQUIRES)
        self.error = error

    def decide(self, state, questions, *, purpose):
        self.calls.append((state, dict(questions)))
        raise self.error


def _mint_status(repository):
    with repository.connection() as connection:
        return [row[0] for row in connection.execute("SELECT status FROM surface_mint_requests")]


@pytest.mark.parametrize("error", ["timeout", "spend"])
def test_f17_a_failed_judgment_leaves_the_job_retryable_and_a_rerun_resumes_without_regenerating(tmp_path, error):
    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop.ai.spend import SpendLimitExceeded
    from learnloop.content.authoring.pf_sandbox import sandbox_available
    from learnloop.ops.pf_generation import publish_backlog
    from tests.pf_fakes import clients
    from tests.test_pf_generation import NEXT_DAY, all_calls, rows, run
    from tests.test_required_method_authority import VARIANT_CONSISTENT, _pf_method_vault

    if not sandbox_available():
        pytest.skip("bubblewrap is not installed")
    repository, paths = _pf_method_vault(tmp_path)
    failure = AIProviderUnavailable("timed out") if error == "timeout" else SpendLimitExceeded("calls exceeds max")
    first = run(paths, publish=False, select=1, fakes=clients(required_method_judge=FailingDecider(failure)))
    [selected] = rows(repository, "status='selected'")
    if error == "spend":
        assert first["status"] == "over_budget"
        assert _mint_status(repository) == ["pending"]
    else:
        [family] = first["families"]
        assert family["status"] == "judgment_incomplete"
        assert family["required_method_judgments"] == {"unjudged": 1}
        assert _mint_status(repository) == ["failed"]
    # The same round resumes: every paid generation call is a checkpoint hit,
    # and only the missing judgment is asked.
    resumed_fakes = clients(required_method_judge=StatementDecider(VARIANT_CONSISTENT))
    second = run(paths, publish=False, select=1, fakes=resumed_fakes)
    assert second["status"] == "complete"
    assert second["families"][0]["required_method_judgments"] == {"consistent": 1}
    assert all_calls({key: value for key, value in resumed_fakes.items() if key != "required_method_judge"}) == 0
    assert len(resumed_fakes["required_method_judge"].calls) == 1
    assert _mint_status(repository) == ["admitted"]
    assert [row["id"] for row in rows(repository, "status='selected'")] == [selected["id"]]
    outcome = publish_backlog(load_vault(paths.root), clock=NEXT_DAY)
    assert len(outcome["published_item_ids"]) == 1


def test_f17_a_cancellation_during_the_judgment_is_not_swallowed(tmp_path):
    from learnloop.ai.errors import AIInterrupted
    from learnloop.content.authoring.pf_sandbox import sandbox_available
    from tests.pf_fakes import clients
    from tests.test_pf_generation import run
    from tests.test_required_method_authority import _pf_method_vault

    if not sandbox_available():
        pytest.skip("bubblewrap is not installed")
    repository, paths = _pf_method_vault(tmp_path)
    report = run(paths, publish=False, select=1,
                 fakes=clients(required_method_judge=FailingDecider(AIInterrupted("stop"))))
    assert report["status"] == "cancelled"
    assert _mint_status(repository) == ["pending"]
