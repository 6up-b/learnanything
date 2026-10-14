"""Method-explicit items, the second re-review (Codex job 20261014-094127-Volan7).

The re-review reopened F14, F13 and F17 and raised three new defects:

* F14 (reopened): the writer still took a final paragraph of GENERATED text
  for its block ("The previous exercise said:" then the sentence, indented as
  a quotation). The writer now renders the block itself onto generated text
  and never takes anything the text says for it; the generation guidance no
  longer asks the model for the sentence (LearnLoop appends it). Validation of
  a stored prompt reads only the block as the writer renders it (its own
  paragraph, at column 0);
* F18: clearing or renaming a method whose instruction was written inline
  under the earlier rule ("Compute det(A). Use X in your answer.") left the
  instruction behind. The writer now removes such a legacy instruction (a
  standalone sentence, never a quoted one) when it clears or renames;
* F19 (F13 reopened): a frozen regrade rebuilt the graded revision from the
  first rubric representation whose contract matched, so an inherited
  default rubric later written inline bound the wrong revision. A
  method-explicit contract now records the revision's reference-content hash
  and the regrade binds exactly that; a historical contract keeps every
  matching representation (fail closed among the checked ones);
* F20 (F17 reopened): a rerun after a partial PF judgment re-ran the whole
  pipeline, and the variants published meanwhile changed its freshness and
  selection requests, so checkpoints missed and paid work repeated. A job
  whose selection already finished now resumes at the judgment and
  publication step.

Fakes only; no network.
"""

from __future__ import annotations

import json
from contextlib import closing
from types import SimpleNamespace

import pytest
import yaml

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.models import Rubric
from learnloop.vault.required_method import (
    has_method_instruction,
    inherit_required_method,
    normalize_required_method,
    required_method_problems,
    strip_method_instruction,
)

from tests.helpers import create_basic_vault
from tests.test_required_method_authority import FROZEN, METHOD, SENTENCE, SVD, StatementDecider, _item, _targets

# -- F14 (reopened): the writer renders its block; generated text never stands for it ----------

#: The re-review's reproduction and its neighbours: generated text whose own
#: final paragraph is (or quotes) the canonical sentence.
GENERATED_FINAL = {
    "indented_quotation": f"Compute det(B). The previous exercise said:\n\n    {SENTENCE}",
    "blockquote": f"Compute det(B). The previous exercise said:\n\n> {SENTENCE}",
    "after_a_colon": f"Compute det(B). The previous exercise said:\n\n{SENTENCE}",
    "introduced_quotation": f"Compute det(B). The previous exercise ended as follows.\n\n{SENTENCE}",
    "model_wrote_the_block": f"Compute det(B).\n\n{SENTENCE}",
}


@pytest.mark.parametrize("case", list(GENERATED_FINAL))
def test_f14_the_writer_renders_its_block_whatever_the_generated_text_ends_with(case):
    prompt = GENERATED_FINAL[case]
    payload = {"prompt": prompt, "grading_rubric": {"criteria": [{"id": "method"}, {"id": "result"}]},
               "required_method": dict(FROZEN)}
    assert normalize_required_method(payload, _targets()) == ["required_method:instruction_added"]
    assert payload["prompt"] == f"{prompt}\n\n{SENTENCE}"
    # The PF variant writer, likewise.
    variant = {"prompt": prompt}
    inherit_required_method(variant, SimpleNamespace(required_method=_item("x", FROZEN).required_method))
    assert variant["prompt"] == f"{prompt}\n\n{SENTENCE}"


@pytest.mark.parametrize("prompt", [
    GENERATED_FINAL["indented_quotation"],
    GENERATED_FINAL["blockquote"],
    f"Compute det(B).\n\n  {SENTENCE}",
    f"Compute det(B).\n\n\t{SENTENCE}",
], ids=["indented_quotation", "blockquote", "two_spaces", "tab"])
def test_f14_validation_reads_only_the_block_as_the_writer_renders_it(prompt):
    """An indented paragraph is a code block or a quotation, never the
    writer's block: the stored prompt is ``not_stated``."""

    assert not has_method_instruction(prompt, METHOD)
    rubric = Rubric.model_validate(_item(prompt).grading_rubric.model_dump(mode="json"))
    errors = [problem.code for problem in required_method_problems(_item(prompt, FROZEN), rubric)
              if problem.severity == "error"]
    assert errors == ["required_method:not_stated"]
    # The block as the writer renders it (blank lines of any length, CRLF) is stated.
    for stated in (f"Compute det(B).\n\n{SENTENCE}", f"Compute det(B).\n\n\n{SENTENCE}\n",
                   f"Compute det(B).\r\n\r\n{SENTENCE}", SENTENCE):
        assert has_method_instruction(stated, METHOD), stated


def test_f14_the_generation_guidance_leaves_the_sentence_to_the_writer():
    """The model is no longer asked to write the sentence: LearnLoop appends
    it, so nothing the model writes is ever taken for it. Every prompt that
    carries the guidance moved its version."""

    from learnloop.content.authoring.ai_contracts import EXERCISE_AUTHORING_PROMPT_VERSION
    from learnloop.content.authoring.pf_contracts import (
        GENERATOR_PROGRAM_PROMPT, PROPOSER_PROMPT, SINGLE_SHOT_PROMPT, SOURCE_ANCHORED_PROMPT,
    )
    from learnloop.content.pipeline.ai_contracts import CANONICAL_INGEST_PROMPT_VERSION
    from learnloop.content.proposals.ai_contracts import (
        AUTHORING_PROMPT_VERSION, DIAGNOSTIC_AUTHORING_PROMPT_VERSION, PRACTICE_GENERATION_PROMPT_VERSION,
        PracticeItemPatchPayload, RequiredMethodPayload,
    )
    from learnloop.content.proposals.method_phrasing import JUDGE_PROMPT_VERSION
    from learnloop.content.synthesis.ai_contracts import (
        APPEND_RECONCILIATION_FACET_IDENTITY_PROMPT_VERSION, APPEND_RECONCILIATION_PROMPT_VERSION,
        SOURCE_SET_SYNTHESIS_FACET_IDENTITY_PROMPT_VERSION, SOURCE_SET_SYNTHESIS_PROMPT_VERSION,
    )
    from learnloop.vault.required_method import (
        CRITERIA_BY_FACT_GUIDANCE, CRITERIA_BY_FACT_RULE_VERSION, REQUIRED_METHOD_VARIANT_GUIDANCE,
    )

    for guidance in (CRITERIA_BY_FACT_GUIDANCE, REQUIRED_METHOD_VARIANT_GUIDANCE,
                     PracticeItemPatchPayload.model_fields["required_method"].description,
                     RequiredMethodPayload.model_fields["name"].description):
        assert "LearnLoop appends" in guidance, guidance
        assert "write the sentence" not in guidance and "must say" not in guidance, guidance
    assert CRITERIA_BY_FACT_RULE_VERSION == "criteria-by-fact-v2"
    versions = (
        AUTHORING_PROMPT_VERSION, DIAGNOSTIC_AUTHORING_PROMPT_VERSION, PRACTICE_GENERATION_PROMPT_VERSION,
        CANONICAL_INGEST_PROMPT_VERSION, EXERCISE_AUTHORING_PROMPT_VERSION, SOURCE_SET_SYNTHESIS_PROMPT_VERSION,
        SOURCE_SET_SYNTHESIS_FACET_IDENTITY_PROMPT_VERSION, APPEND_RECONCILIATION_PROMPT_VERSION,
        APPEND_RECONCILIATION_FACET_IDENTITY_PROMPT_VERSION,
    )
    assert all(version.endswith("criteria-by-fact-v2") for version in versions), versions
    assert (GENERATOR_PROGRAM_PROMPT, PROPOSER_PROMPT, SINGLE_SHOT_PROMPT, SOURCE_ANCHORED_PROMPT) == (
        "pf-generator-program-v8", "pf-ensemble-propose-v4", "pf-single-shot-v4", "pf-source-anchored-v4")
    assert JUDGE_PROMPT_VERSION == "rubric-phrasing-judge-v2"


def test_f14_an_authored_item_quoting_the_sentence_gets_the_writers_block_end_to_end(tmp_path):
    """The re-review's reproduction through the authoring proposal path: the
    persisted payload, the accepted item and doctor all agree, and the text
    ends with a block the writer rendered."""

    from learnloop.clock import FrozenClock
    from learnloop.content.proposals.proposals import accept_items, persist_authoring_proposal
    from tests.helpers import NOW
    from tests.test_required_method_items import _add_concept_and_lo, _proposal

    paths = create_basic_vault(tmp_path / "vault")
    _add_concept_and_lo(paths, "cofactor_expansion", "procedure", "lo_cofactor")
    quoted = GENERATED_FINAL["indented_quotation"]
    patch_id = persist_authoring_proposal(paths.root, _proposal("lo_cofactor", dict(FROZEN), prompt=quoted),
                                          provider="import", clock=FrozenClock(NOW))
    [row] = Repository(paths.sqlite_path).proposal_items(patch_id)
    assert row["payload"]["prompt"] == f"{quoted}\n\n{SENTENCE}"
    accept_items(paths.root, patch_id)
    item = load_vault(paths.root).practice_items["pi_lo_cofactor_det"]
    assert item.prompt == f"{quoted}\n\n{SENTENCE}"
    rubric = load_vault(paths.root).rubric_for_item(item)
    assert [problem for problem in required_method_problems(item, rubric) if problem.severity == "error"] == []


def _generated_method_item(tmp_path, prompt: str | None = None):
    """The basic vault's SVD item as a generated item that requires the SVD,
    its prompt ``prompt`` (default: the writer's block appended by the owner's
    override)."""

    from learnloop.content.proposals.proposals import accept_items
    from learnloop.content.proposals.required_method_override import propose_required_method_override
    from learnloop.vault.writer import upsert_practice_item

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    if prompt is None:
        proposed = propose_required_method_override(load_vault(paths.root), repository, "pi_svd_define_001",
                                                    name=SVD, criterion_ids=["correctness"])
        accept_items(paths.root, proposed["proposal_id"])
    else:
        data = load_vault(paths.root).practice_items["pi_svd_define_001"].model_dump(mode="json")
        data["prompt"] = prompt
        data["required_method"] = {"name": SVD, "criterion_ids": ["correctness"]}
        upsert_practice_item(paths.root, data)
    return paths, repository, load_vault(paths.root).practice_items["pi_svd_define_001"]


def test_f14_a_generated_update_keeps_one_block_and_never_adopts_a_quotation(tmp_path):
    """An update of a generated item revises a prompt that already carries
    the writer's block: a revision that keeps that block keeps exactly one;
    a revision that ends with a quotation of the sentence gets the block
    rendered after it."""

    from tests.test_required_method_reopened import _update_proposal

    block = f"Use {SVD} in your answer."
    paths, repository, item = _generated_method_item(tmp_path)
    _patch, row = _update_proposal(tmp_path, repository, item.id,
                                   {"prompt": f"Define the SVD of a 2x2 matrix A.\n\n{block}"})
    assert row["payload"]["prompt"] == f"Define the SVD of a 2x2 matrix A.\n\n{block}"
    quoted = f"Define the SVD of A. The previous card said:\n\n    {block}"
    _patch, row = _update_proposal(tmp_path, repository, item.id, {"prompt": quoted})
    assert row["payload"]["prompt"] == f"{quoted}\n\n{block}"


# -- F18: clearing or renaming a legacy inline instruction -------------------------------------

LEGACY = f"Compute det(A). {SENTENCE}"


@pytest.mark.parametrize("prompt, cleared", [
    (LEGACY, "Compute det(A)."),
    (f"{SENTENCE} Compute det(A).", "Compute det(A)."),
    (f"Compute det(A). {SENTENCE} Show each step.", "Compute det(A). Show each step."),
    (f"Compute det(A).\n{SENTENCE}", "Compute det(A)."),
    (f"Compute det(A).\n\n{SENTENCE}\n\nShow each step.", "Compute det(A).\n\nShow each step."),
    (f"Compute det(A).\n\n{SENTENCE}", "Compute det(A)."),
    (f"{SENTENCE} Compute det(A).\n\n{SENTENCE}", "Compute det(A)."),
], ids=["trailing", "leading", "mid", "own_line", "own_paragraph", "block", "standalone_and_block"])
def test_f18_clearing_removes_a_legacy_inline_instruction(prompt, cleared):
    assert strip_method_instruction(prompt, METHOD) == cleared


@pytest.mark.parametrize("prompt", [
    f'The previous exercise said "{SENTENCE}" Compute det(B).',
    f"Compute det(B). Last week's exercise ended with: {SENTENCE}",
    f"Compute det(B). The previous exercise said:\n\n    {SENTENCE}",
    f"Compute det(B). The previous exercise said:\n\n> {SENTENCE}",
    f"Compute det(B). The previous exercise said:\n{SENTENCE}",
    f"Compute det(B) ({SENTENCE})",
], ids=["double_quotes", "after_a_colon", "indented", "blockquote", "colon_then_line", "parenthesis"])
def test_f18_a_quoted_occurrence_survives_clearing(prompt):
    assert strip_method_instruction(prompt, METHOD) == prompt


def test_f18_the_owner_clears_or_renames_a_legacy_instruction_end_to_end(tmp_path):
    """The re-review's scenario through ``override_payload``: a generated item
    whose prompt carries the instruction inline (valid under the earlier
    rule). Clearing removes it; renaming replaces it with the new block."""

    from learnloop.content.proposals.proposals import accept_items
    from learnloop.content.proposals.required_method_override import (
        override_payload, propose_required_method_override,
    )

    legacy = f"Define the SVD of A. Use {SVD} in your answer."
    paths, repository, item = _generated_method_item(tmp_path, prompt=legacy)
    cleared = override_payload(load_vault(paths.root), item.id, clear=True)
    assert cleared["payload"].get("prompt") == "Define the SVD of A."
    renamed = override_payload(load_vault(paths.root), item.id, name="row reduction",
                               criterion_ids=["correctness"])
    assert renamed["payload"]["prompt"] == "Define the SVD of A.\n\nUse row reduction in your answer."
    # Setting the same method again turns the legacy instruction into the block.
    restated = override_payload(load_vault(paths.root), item.id, name=SVD, criterion_ids=["correctness"])
    assert restated["payload"]["prompt"] == f"Define the SVD of A.\n\nUse {SVD} in your answer."
    proposed = propose_required_method_override(load_vault(paths.root), repository, item.id, clear=True)
    accept_items(paths.root, proposed["proposal_id"])
    after = load_vault(paths.root).practice_items[item.id]
    assert after.prompt == "Define the SVD of A." and after.required_method is None


def test_f18_a_generated_update_renaming_a_legacy_method_replaces_its_instruction(tmp_path):
    from tests.test_required_method_reopened import _update_proposal

    legacy = f"Define the SVD of A. Use {SVD} in your answer."
    paths, repository, item = _generated_method_item(tmp_path, prompt=legacy)
    renamed = "the singular value decomposition"
    _patch, row = _update_proposal(tmp_path, repository, item.id, {
        "required_method": {"name": renamed, "criterion_ids": ["correctness"]}})
    assert row["payload"]["prompt"] == f"Define the SVD of A.\n\nUse {renamed} in your answer."


# -- F19: the frozen regrade binds the revision's own reference-content hash ------------------


def test_f19_a_method_contract_records_the_reference_content_hash():
    from learnloop.learner.assessment_contracts import compile_assessment_contract
    from learnloop.vault.hashes import reference_content_hash

    vault = SimpleNamespace(learning_objects={}, rubric_for_item=lambda item: item.grading_rubric)
    with_method = _item("Compute det(A).", FROZEN)
    contract = compile_assessment_contract(vault, with_method, rubric=with_method.grading_rubric)
    assert contract["reference_content_hash"] == reference_content_hash(with_method)
    # Every other contract (and its hash) is unchanged.
    plain = _item("Compute det(A).")
    assert "reference_content_hash" not in compile_assessment_contract(vault, plain, rubric=plain.grading_rubric)


def _contract_version_id(repository, attempt_id: str) -> str:
    return next(row.assessment_contract_version_id for row in repository.fetch_grading_evidence(attempt_id)
                if row.assessment_contract_version_id is not None)


def _make_historical(repository, attempt_id: str) -> None:
    """The attempt's contract as one frozen before it recorded the hash."""

    version_id = _contract_version_id(repository, attempt_id)
    stored = repository.fetch_assessment_contract_version(version_id)
    contract = dict(stored["contract"])
    contract.pop("reference_content_hash", None)
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            connection.execute("UPDATE assessment_contract_versions SET contract_json=? WHERE id=?",
                               (json.dumps(contract, sort_keys=True), version_id))


def _check(repository, item_id: str, content: str, status: str, check_id: str, created_at: str) -> None:
    from learnloop.db.stores.source_service import insert_key_check

    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            insert_key_check(connection, id=check_id, practice_item_id=item_id, content_hash=content,
                             key_status=status, rung="test", trigger="verify", started_at=created_at,
                             created_at=created_at)


def _inherited_rubric_item(paths, repository, spans):
    """A verified method exercise graded under the INHERITED default rubric
    (``grading_rubric = None``), its key checked for that revision."""

    from learnloop.attempts.grading import resolved_rubric
    from learnloop.db.stores.source_service import reference_content_hash
    from learnloop.vault.writer import upsert_practice_item
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _verified_import

    item_id = _verified_import(paths, repository, spans)
    data = loaded(paths).practice_items[item_id].model_dump(mode="json")
    # The vault's default rubric for the mode (same criteria, its own wording:
    # no check of the import's own revision covers it); the item inherits it.
    default_rubric = json.loads(json.dumps(data["grading_rubric"]))
    for criterion in default_rubric["criteria"]:
        criterion["description"] = "Default: " + criterion["description"]
    (paths.root / "rubrics").mkdir(exist_ok=True)
    (paths.root / "rubrics" / f"{data['practice_mode']}.yaml").write_text(yaml.safe_dump({
        "schema_version": 1, "id": f"default_{data['practice_mode']}",
        "applies_to": {"practice_mode": data["practice_mode"]}, "rubric": default_rubric,
    }, sort_keys=False), encoding="utf-8")
    data["grading_rubric"] = None
    upsert_practice_item(paths.root, data)
    default = resolved_rubric(loaded(paths), loaded(paths).practice_items[item_id])
    criterion = default.criteria[0].id
    data["required_method"] = {"name": "the characteristic polynomial", "criterion_ids": [criterion],
                               "statement": "source", "decided_by": "owner"}
    upsert_practice_item(paths.root, data)
    item = loaded(paths).practice_items[item_id]
    _check(repository, item_id, reference_content_hash(item), "book_solution", "rkc_inherited_verified",
           "2026-01-01T00:00:00Z")
    return item_id, criterion, default


def _edit_and_materialize(paths, item_id, default) -> tuple[str, str]:
    """Edit the statement and write the SAME default rubric inline. Returns
    the reference hashes of the graded statement under the inline rubric and
    of the current item."""

    from learnloop.db.stores.source_service import reference_content_hash
    from learnloop.vault.models import PracticeItem
    from learnloop.vault.writer import upsert_practice_item
    from tests.source_service_fakes import loaded

    data = loaded(paths).practice_items[item_id].model_dump(mode="json")
    graded_inline = reference_content_hash(PracticeItem.model_validate(
        {**data, "grading_rubric": default.model_dump(mode="json")}))
    data["prompt"] = data["prompt"] + " (Reworded.)"
    data["grading_rubric"] = default.model_dump(mode="json")
    upsert_practice_item(paths.root, data)
    return graded_inline, reference_content_hash(loaded(paths).practice_items[item_id])


@pytest.mark.parametrize("historical", [False, True], ids=["recorded", "historical"])
def test_f19_an_inherited_rubric_written_inline_later_never_unverifies_the_attempt(gated_successor, historical):
    """The re-review's first consequence: the graded revision is the
    inherited-rubric one, verified; the current inline rubric resolves the
    same contract but is another revision, never checked."""

    from tests.test_reference_gate_imports import _attempt, _bindings, _regrade, _status

    paths, repository, spans = gated_successor
    item_id, criterion, default = _inherited_rubric_item(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    assert _status(repository, attempt.attempt_id) == "verified"
    if historical:
        _make_historical(repository, attempt.attempt_id)
    _edit_and_materialize(paths, item_id, default)
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    assert _bindings(repository, attempt.attempt_id) == []


@pytest.mark.parametrize("historical", [False, True], ids=["recorded", "historical"])
def test_f19_a_dispute_of_the_graded_revision_lowers_despite_a_verified_inline_twin(gated_successor, historical):
    """The re-review's second consequence: the inline twin of the graded
    statement was checked verified; the revision actually graded (inherited
    rubric) is disputed later. The regrade is lowered."""

    from learnloop.db.stores.source_service import reference_content_hash
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _attempt, _bindings, _regrade, _status

    paths, repository, spans = gated_successor
    item_id, criterion, default = _inherited_rubric_item(paths, repository, spans)
    graded = reference_content_hash(loaded(paths).practice_items[item_id])
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    if historical:
        _make_historical(repository, attempt.attempt_id)
    graded_inline, _current = _edit_and_materialize(paths, item_id, default)
    _check(repository, item_id, graded_inline, "book_solution", "rkc_inline_twin", "2026-02-01T00:00:00Z")
    _check(repository, item_id, graded, "disputed", "rkc_graded_disputed", "2099-01-01T00:00:00Z")
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
    [binding] = _bindings(repository, attempt.attempt_id)
    assert binding["right_id"] == graded
    assert ("graded_revision=ambiguous" if historical else "graded_revision=frozen") in binding["rationale"]


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


# -- F20: a rerun resumes at the judgment and publication step ---------------------------------


class FailingOnceDecider(StatementDecider):
    """Judges the first stem it is asked about; every later ask times out."""

    def __init__(self, probabilities, error):
        super().__init__(probabilities)
        self.error = error

    def decide(self, state, questions, *, purpose):
        if self.calls:
            self.calls.append((state, dict(questions)))
            raise self.error
        return super().decide(state, questions, purpose=purpose)


def test_f20_a_partial_judgment_resumes_without_any_paid_pipeline_work(tmp_path):
    """Two variants are selected; one is judged and published, the other's
    judgment times out. The rerun of the round resumes at the judgment: no
    generation, freshness or selection call (the published variant would
    change their requests), one judgment, and the second variant publishes."""

    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop.content.authoring.pf_sandbox import sandbox_available
    from tests.pf_fakes import clients, enable_pf
    from tests.test_pf_generation import all_calls, rows, run
    from tests.test_required_method_authority import VARIANT_CONSISTENT, _pf_method_vault
    from tests.test_required_method_reopened import _mint_status

    if not sandbox_available():
        pytest.skip("bubblewrap is not installed")
    repository, paths = _pf_method_vault(tmp_path)
    enable_pf(paths.root, max_published_per_day=5)
    first_judge = FailingOnceDecider(VARIANT_CONSISTENT, AIProviderUnavailable("timed out"))
    first = run(paths, publish=True, select=2, fakes=clients(required_method_judge=first_judge))
    [family] = first["families"]
    assert family["status"] == "judgment_incomplete", family
    assert family["required_method_judgments"] == {"consistent": 1, "unjudged": 1}
    assert len(family["published_item_ids"]) == 1
    assert _mint_status(repository) == ["failed"]
    [waiting] = rows(repository, "status='selected'")
    resumed_fakes = clients(required_method_judge=StatementDecider(VARIANT_CONSISTENT))
    second = run(paths, publish=True, select=2, fakes=resumed_fakes)
    [family] = second["families"]
    assert second["status"] == "complete" and family["status"] == "complete", second
    assert all_calls({key: value for key, value in resumed_fakes.items() if key != "required_method_judge"}) == 0
    assert family["resumed"] == "required_method_judgment"
    assert len(resumed_fakes["required_method_judge"].calls) == 1
    assert _mint_status(repository) == ["admitted"]
    assert family["published_item_ids"] and rows(repository, "status='selected'") == []
    assert {row["id"] for row in rows(repository, "status='published'")} >= {waiting["id"]}

