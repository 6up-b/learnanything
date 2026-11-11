"""Method-explicit items, the second re-review (Codex job 20261014-094127-Volan7).

The re-review reopened F14, F13 and F17 and raised three new defects. Its F14
and F18 tests (the writer's block, legacy inline instructions) are retired by
round 3, which stores no instruction in the statement at all
(``tests/test_required_method_round3.py``); the guidance test stays. What
stays here:

* F19 (F13 reopened): a frozen regrade rebuilt the graded revision from the
  first rubric representation whose contract matched, so an inherited
  default rubric later written inline bound the wrong revision. A
  method-explicit contract now records the revision's reference-content hash
  and the regrade binds exactly that; a historical contract keeps every
  matching representation (fail closed among the checked ones; round 3: an
  inherited default that cannot be recovered binds unverified);
* F20 (F17 reopened): a rerun after a partial PF judgment re-ran the whole
  pipeline, and the variants published meanwhile changed its freshness and
  selection requests, so checkpoints missed and paid work repeated. A job
  whose selection already finished now resumes at the judgment and
  publication step.

Fakes only; no network.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tests.required_method_authority_helpers import FROZEN, StatementDecider, _item
from tests.required_method_rereview_helpers import (
    FailingOnceDecider,
    _check,
    _edit_and_materialize,
    _inherited_rubric_item,
    _make_historical,
)

# -- F14 (re-review): the generation guidance leaves the sentence to LearnLoop -------------------


def test_f14_the_generation_guidance_leaves_the_sentence_to_the_writer():
    """The model is never asked to write the sentence: LearnLoop shows it
    after the statement (round 3: rendered from the field, never stored), so
    nothing the model writes is ever taken for it. Every prompt that carries
    the guidance moved its version."""

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


@pytest.mark.parametrize("historical", [False, True], ids=["recorded", "historical"])
def test_f19_an_inherited_rubric_written_inline_later_never_unverifies_the_attempt(gated_successor, historical):
    """The re-review's first consequence: the graded revision is the
    inherited-rubric one, verified; the current inline rubric resolves the
    same contract but is another revision, never checked."""

    from tests.reference_gate_imports_helpers import _attempt, _bindings, _regrade, _status

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
    from tests.reference_gate_imports_helpers import _attempt, _bindings, _regrade, _status

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


def test_f20_a_partial_judgment_resumes_without_any_paid_pipeline_work(tmp_path):
    """Two variants are selected; one is judged and published, the other's
    judgment times out. The rerun of the round resumes at the judgment: no
    generation, freshness or selection call (the published variant would
    change their requests), one judgment, and the second variant publishes."""

    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop.content.authoring.pf_sandbox import sandbox_available
    from tests.pf_fakes import clients, enable_pf
    from tests.pf_generation_helpers import all_calls, rows, run
    from tests.required_method_authority_helpers import VARIANT_CONSISTENT, _pf_method_vault
    from tests.required_method_reopened_helpers import _mint_status

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
