"""Method-explicit items (owner rule 2026-10-13): the item contract, validation,
doctor and the generation writers.

Rubric criteria name the fact a step establishes, not the method; an item
whose target IS a method states it in its prompt ("Use {method} in your
answer.") and records it as ``PracticeItem.required_method``. Every writer
holds a generated item to that (``learnloop.vault.required_method``), and
doctor reports what an existing item breaks. Fakes only; no network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from learnloop.clock import FrozenClock
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.content.proposals.proposals import accept_items, build_authoring_context, persist_authoring_proposal
from learnloop.db.repositories import Repository
from learnloop.ops.doctor import run_doctor
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_vault
from learnloop.vault.models import PracticeItem, RequiredMethod, Rubric
from learnloop.vault.required_method import (
    CRITERIA_BY_FACT_GUIDANCE,
    ensure_method_instruction,
    inherit_required_method,
    method_phrase,
    method_targets,
    names_match,
    normalize_required_method,
    prompt_states_method,
    required_method_instruction,
    required_method_problems,
)
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault

STAMP = "2026-10-13T00:00:00Z"


def _item(**overrides) -> PracticeItem:
    data = {
        "id": "pi_x", "learning_object_id": "lo_svd_definition", "practice_mode": "short_answer",
        "prompt": "Compute det(A).", "expected_answer": "13",
        "grading_rubric": {"criteria": [
            {"id": "method", "points": 2, "description": "Uses cofactor expansion along the first row."},
            {"id": "result", "points": 2, "description": "Establishes det(A) = 13."},
        ]},
        "created_at": STAMP, "updated_at": STAMP,
    }
    data.update(overrides)
    return PracticeItem.model_validate(data)


# -- the item contract -------------------------------------------------------------------


def test_an_item_without_a_required_method_serializes_and_hashes_as_before():
    plain = _item()
    assert "required_method" not in plain.model_dump(mode="json", exclude_none=False)
    with_method = _item(prompt="Compute det(A). Use cofactor expansion in your answer.",
                        required_method={"name": "cofactor expansion", "criterion_ids": ["method"]})
    dumped = with_method.model_dump(mode="json", exclude_none=False)
    # Unset links are omitted too.
    assert dumped["required_method"] == {"name": "cofactor expansion", "criterion_ids": ["method"]}
    assert practice_item_hash(with_method) != practice_item_hash(with_method.model_copy(update={"required_method": None}))
    # The hash of an item without one is computed from exactly the old fields.
    from learnloop.vault.hashes import content_hash

    legacy = content_hash({key: getattr(plain, key) for key in (
        "learning_object_id", "practice_mode", "attempt_types_allowed", "evidence_facets", "evidence_weights",
        "prompt", "expected_answer", "difficulty", "hints", "hint_policy", "grading_rubric")})
    assert practice_item_hash(plain) == legacy
    with pytest.raises(ValueError):
        RequiredMethod(name="")


def test_the_explicit_instruction():
    assert required_method_instruction("cofactor  expansion") == "Use cofactor expansion in your answer."
    assert prompt_states_method("Compute det(A) by Cofactor   Expansion.", "cofactor expansion")
    assert not prompt_states_method("Compute det(A).", "cofactor expansion")
    assert ensure_method_instruction("Compute det(A).", "cofactor expansion") == (
        "Compute det(A).\n\nUse cofactor expansion in your answer.")
    assert ensure_method_instruction("Use cofactor expansion to compute det(A).", "cofactor expansion") == (
        "Use cofactor expansion to compute det(A).")


@pytest.mark.parametrize("description, method", [
    ("Uses cofactor expansion along the first row to compute det(A).", "cofactor expansion"),
    ("Applies the chain rule correctly.", "chain rule"),
    ("Finds the probability by the complement rule.", "complement rule"),
    ("Proves the claim by induction on n.", "induction"),
    ("Uses Bayes' theorem to compute P(A|B).", "Bayes' theorem"),
    ("Establishes det(A) = 13.", None),
    ("Computes each 2x2 minor and its cofactor sign correctly.", None),  # presupposes, names no method
    ("Uses a valid method to evaluate the determinant (for example cofactor expansion).", None),
    ("Applies an appropriate rule.", None),
    ("Uses independence to justify the product.", None),
    ("Concludes by stating the value.", None),
])
def test_the_conservative_heuristic(description, method):
    phrase = method_phrase(description)
    assert (phrase.method if phrase else None) == method


def test_method_names_match_on_content_tokens():
    assert names_match("cofactor expansion along the first row", "Cofactor expansion")
    assert names_match("cofactors", "cofactor expansion")
    assert not names_match("chain rule", "product rule")  # 'rule' is generic
    assert not names_match("row reduction", "cofactor expansion")


# -- method targets from metadata -------------------------------------------------------


def _add_concept_and_lo(paths, concept_id: str, concept_type: str, lo_id: str) -> None:
    concepts = yaml.safe_load(paths.concepts_path.read_text(encoding="utf-8"))
    concepts["concepts"][concept_id] = {
        "title": concept_id.replace("_", " ").title(), "type": concept_type, "aliases": [], "description": "d",
        "tags": [], "created_at": NOW_ISO, "updated_at": NOW_ISO,
    }
    write_yaml(paths.concepts_path, concepts)
    write_yaml(paths.learning_object_path("linear-algebra", lo_id), {
        "schema_version": 1, "id": lo_id, "title": lo_id, "subjects": ["linear-algebra"], "concept": concept_id,
        "knowledge_type": "concept", "status": "active", "summary": "s", "created_at": NOW_ISO, "updated_at": NOW_ISO,
    })


def _write_facets(paths, facets: list[dict]) -> None:
    write_yaml(paths.root / "facets.yaml", {"schema_version": 2, "facets": facets})


@pytest.fixture()
def vault_paths(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _add_concept_and_lo(paths, "cofactor_expansion", "procedure", "lo_cofactor")
    _add_concept_and_lo(paths, "determinant", "concept", "lo_determinant")
    _write_facets(paths, [
        {"id": "facet_laplace", "title": "Laplace expansion", "kind": "procedure_contract", "aliases": ["cofactor expansion"]},
        {"id": "facet_det_zero", "title": "Zero determinant", "kind": "proposition"},
    ])
    return paths


def test_a_target_is_a_method_by_its_concept_type_or_facet_kind(vault_paths):
    vault = load_vault(vault_paths.root)
    [concept] = method_targets(vault, learning_object_id="lo_cofactor")
    assert (concept.basis, concept.concept_id, concept.name) == ("concept_type", "cofactor_expansion", "Cofactor Expansion")
    assert method_targets(vault, learning_object_id="lo_determinant") == []
    [facet] = method_targets(vault, learning_object_id="lo_determinant", facet_ids=["facet_laplace", "facet_det_zero"])
    assert (facet.basis, facet.facet_id) == ("facet_kind", "facet_laplace") and facet.matches("cofactor expansion")
    # An item measuring method selection leaves the method to the learner.
    assert method_targets(vault, learning_object_id="lo_cofactor", capability="method_selection") == []


def test_the_writer_check_keeps_a_required_method_only_on_its_target(vault_paths):
    vault = load_vault(vault_paths.root)
    targets = method_targets(vault, learning_object_id="lo_cofactor")
    rubric = {"criteria": [{"id": "method"}, {"id": "result"}]}

    kept = {"prompt": "Compute det(A).", "grading_rubric": rubric,
            "required_method": {"name": "cofactor expansion", "criterion_ids": ["method", "ghost"]}}
    notes = normalize_required_method(kept, targets)
    assert kept["required_method"] == {"name": "cofactor expansion", "criterion_ids": ["method"],
                                       "learning_object_id": "lo_cofactor", "concept_id": "cofactor_expansion"}
    assert kept["prompt"] == "Compute det(A).\n\nUse cofactor expansion in your answer."
    assert notes == ["required_method:dropped_unknown_criteria", "required_method:instruction_added"]

    not_a_method = {"prompt": "Compute det(A).", "grading_rubric": rubric,
                    "required_method": {"name": "cofactor expansion", "criterion_ids": ["method"]}}
    assert normalize_required_method(not_a_method, []) == ["required_method:dropped_not_a_method_target"]
    assert "required_method" not in not_a_method and not_a_method["prompt"] == "Compute det(A)."

    another = {"prompt": "Compute det(A).", "grading_rubric": rubric,
               "required_method": {"name": "row reduction", "criterion_ids": ["method"]}}
    assert normalize_required_method(another, targets) == ["required_method:dropped_unmatched_target"]
    assert "required_method" not in another

    # A source statement (a textbook stem) is never rewritten.
    source = {"prompt": "Compute det(A).", "grading_rubric": rubric,
              "required_method": {"name": "cofactor expansion", "criterion_ids": ["method"]}}
    assert normalize_required_method(source, targets, source_statement=True) == [
        "required_method:dropped_source_statement_does_not_state_it"]
    assert source["prompt"] == "Compute det(A)." and "required_method" not in source
    stated = {"prompt": "Compute det(A) by cofactor expansion.", "grading_rubric": rubric,
              "required_method": {"name": "cofactor expansion", "criterion_ids": ["method"]}}
    assert normalize_required_method(stated, targets, source_statement=True) == []
    assert stated["prompt"] == "Compute det(A) by cofactor expansion." and stated["required_method"]["criterion_ids"] == ["method"]


def test_a_variant_inherits_its_parents_required_method():
    parent = _item(prompt="Compute det(A). Use cofactor expansion in your answer.",
                   required_method={"name": "cofactor expansion", "criterion_ids": ["method"]})
    variant = {"prompt": "Compute det(B) for B = [[2, 1], [1, 2]]."}
    assert inherit_required_method(variant, parent) == ["required_method:inherited", "required_method:instruction_added"]
    assert variant["prompt"].endswith("Use cofactor expansion in your answer.")
    assert variant["required_method"]["name"] == "cofactor expansion"
    plain = {"prompt": "Compute det(B)."}
    assert inherit_required_method(plain, _item()) == [] and plain == {"prompt": "Compute det(B)."}


# -- validation and doctor ---------------------------------------------------------------


def test_validation_names_each_problem():
    rubric = Rubric.model_validate({"criteria": [
        {"id": "method", "points": 2, "description": "Uses cofactor expansion along the first row."},
        {"id": "result", "points": 2, "description": "Establishes det(A) = 13."},
    ]})
    codes = lambda item: [(p.code, p.criterion_id) for p in required_method_problems(item, rubric)]  # noqa: E731
    assert codes(_item()) == [("criterion:method_phrased", "method")]
    stated = _item(prompt="Compute det(A). Use cofactor expansion in your answer.",
                   required_method={"name": "cofactor expansion", "criterion_ids": ["method"]})
    assert codes(stated) == []
    unstated = _item(required_method={"name": "cofactor expansion", "criterion_ids": ["method", "ghost"]})
    assert codes(unstated) == [("required_method:not_stated", None), ("required_method:unknown_criterion", "ghost")]


def _write_item(paths, item_id: str, lo_id: str, prompt: str, criteria: list[dict], **extra) -> None:
    write_yaml(paths.practice_item_path("linear-algebra", item_id), {
        "schema_version": 1, "id": item_id, "learning_object_id": lo_id, "practice_mode": "short_answer",
        "prompt": prompt, "expected_answer": "13",
        "grading_rubric": {"max_points": sum(c["points"] for c in criteria), "criteria": criteria},
        "created_at": NOW_ISO, "updated_at": NOW_ISO, **extra,
    })


def test_doctor_reports_method_phrased_criteria_and_malformed_required_methods(vault_paths):
    det = [{"id": "method", "points": 2, "description": "Uses cofactor expansion along the first row."},
           {"id": "result", "points": 2, "description": "Establishes det(A) = 13."}]
    _write_item(vault_paths, "pi_phrased", "lo_determinant", "Compute det(A).", det)
    _write_item(vault_paths, "pi_unstated", "lo_cofactor", "Compute det(A).", det,
                required_method={"name": "cofactor expansion", "criterion_ids": ["method"]})
    _write_item(vault_paths, "pi_wrong_target", "lo_determinant", "Compute det(A). Use cofactor expansion in your answer.",
                det, required_method={"name": "cofactor expansion", "criterion_ids": ["method"]})
    _write_item(vault_paths, "pi_good", "lo_cofactor", "Compute det(A). Use cofactor expansion in your answer.",
                det, required_method={"name": "cofactor expansion", "criterion_ids": ["method"]})
    _write_item(vault_paths, "pi_retired", "lo_determinant", "Compute det(A).", det, status="retired")
    issues = [issue for issue in run_doctor(vault_paths.root).issues
              if issue.code.startswith(("criterion:method_phrased", "required_method"))]
    found = {(issue.entity_id, issue.code, issue.severity) for issue in issues}
    assert found == {
        ("pi_phrased", "criterion:method_phrased", "warning"),
        ("pi_unstated", "required_method:not_stated", "error"),
        ("pi_wrong_target", "required_method:not_a_method_target", "warning"),
    }
    phrased = next(issue for issue in issues if issue.code == "criterion:method_phrased")
    # Doctor says which judge read it: the conservative heuristic (no model call).
    assert phrased.details["judge"] == "heuristic" and phrased.details["method"] == "cofactor expansion"


def test_doctor_is_quiet_on_a_vault_with_fact_phrased_criteria(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    codes = {issue.code for issue in run_doctor(paths.root).issues}
    assert not {code for code in codes if code.startswith(("required_method", "criterion:method_phrased"))}


# -- generation: the authoring-proposal family ---------------------------------------------


def test_authoring_prompts_carry_the_rule_and_moved_their_versions():
    from learnloop.content.authoring.ai_contracts import (
        EXERCISE_AUTHORING_PROMPT,
        EXERCISE_AUTHORING_PROMPT_VERSION,
    )
    from learnloop.content.authoring.pf_contracts import (
        GENERATOR_PROGRAM_PROMPT,
        PROPOSER_PROMPT,
        SINGLE_SHOT_PROMPT,
        SOURCE_ANCHORED_PROMPT,
        generator_program_prompt,
        proposer_prompt,
        source_anchored_prompt,
    )
    from learnloop.content.pipeline.ai_contracts import (
        CANONICAL_INGEST_PROMPT_VERSION,
        CanonicalIngestContext,
        canonical_ingest_prompt,
    )
    from learnloop.content.proposals.ai_contracts import (
        AUTHORING_PROMPT_VERSION,
        DIAGNOSTIC_AUTHORING_PROMPT_VERSION,
        PRACTICE_GENERATION_PROMPT_VERSION,
        AuthoringContext,
        authoring_prompt,
    )
    from learnloop.content.synthesis.ai_contracts import (
        APPEND_RECONCILIATION_FACET_IDENTITY_PROMPT_VERSION,
        APPEND_RECONCILIATION_PROMPT,
        APPEND_RECONCILIATION_PROMPT_VERSION,
        SOURCE_SET_SYNTHESIS_FACET_IDENTITY_PROMPT_VERSION,
        SOURCE_SET_SYNTHESIS_PROMPT,
        SOURCE_SET_SYNTHESIS_PROMPT_VERSION,
    )
    from learnloop.tutor.ai_contracts import TEACH_BACK_AUTHORING_PROMPT_VERSION, _TEACH_BACK_AUTHORING_TASK
    from learnloop.vault.required_method import REQUIRED_METHOD_VARIANT_GUIDANCE

    assert CRITERIA_BY_FACT_GUIDANCE in authoring_prompt(AuthoringContext(vault_root="v", source_ids=[]))
    context = CanonicalIngestContext(vault_root="v", source_kind="website_page", canonical_source={}, chunks=[])
    assert CRITERIA_BY_FACT_GUIDANCE in canonical_ingest_prompt(context)
    assert CRITERIA_BY_FACT_GUIDANCE in EXERCISE_AUTHORING_PROMPT
    assert CRITERIA_BY_FACT_GUIDANCE in SOURCE_SET_SYNTHESIS_PROMPT and CRITERIA_BY_FACT_GUIDANCE in APPEND_RECONCILIATION_PROMPT
    assert "CRITERIA BY FACT" in _TEACH_BACK_AUTHORING_TASK
    parent = {"id": "p", "prompt": "q", "rubric": None}
    for prompt in (generator_program_prompt(parent=parent, family={}, skeleton={}, relation="isomorph",
                                            previous_failure=None),
                   proposer_prompt(parent=parent, family={}, skeleton={}, relation="isomorph", count=2,
                                   generation_seed="0"),
                   source_anchored_prompt(passages=[], parent=parent, family={}, count=2, generation_seed="0")):
        assert REQUIRED_METHOD_VARIANT_GUIDANCE in prompt
    versions = (
        AUTHORING_PROMPT_VERSION, DIAGNOSTIC_AUTHORING_PROMPT_VERSION, PRACTICE_GENERATION_PROMPT_VERSION,
        CANONICAL_INGEST_PROMPT_VERSION, EXERCISE_AUTHORING_PROMPT_VERSION, SOURCE_SET_SYNTHESIS_PROMPT_VERSION,
        SOURCE_SET_SYNTHESIS_FACET_IDENTITY_PROMPT_VERSION, APPEND_RECONCILIATION_PROMPT_VERSION,
        APPEND_RECONCILIATION_FACET_IDENTITY_PROMPT_VERSION, TEACH_BACK_AUTHORING_PROMPT_VERSION,
    )
    assert all(version.endswith("criteria-by-fact") for version in versions), versions
    assert (GENERATOR_PROGRAM_PROMPT, PROPOSER_PROMPT, SINGLE_SHOT_PROMPT, SOURCE_ANCHORED_PROMPT) == (
        "pf-generator-program-v7", "pf-ensemble-propose-v3", "pf-single-shot-v3", "pf-source-anchored-v3")


def test_the_authoring_context_names_method_targets_only_where_they_are(vault_paths):
    vault = load_vault(vault_paths.root)
    entries = {entry["id"]: entry for entry in build_authoring_context(vault).learning_objects}
    assert entries["lo_cofactor"]["required_method_targets"] == [
        {"name": "Cofactor Expansion", "basis": "concept_type", "concept_id": "cofactor_expansion"}]
    assert "required_method_targets" not in entries["lo_determinant"]


def _proposal(lo_id: str, required_method: dict | None, prompt: str = "Compute det(A).") -> AuthoringProposal:
    payload = {
        "learning_object_id": lo_id, "practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt"],
        "prompt": prompt, "expected_answer": "13",
        "grading_rubric": {"max_points": 4, "criteria": [
            {"id": "method", "points": 2, "description": "Uses cofactor expansion along the first row."},
            {"id": "result", "points": 2, "description": "Establishes det(A) = 13."},
        ]},
    }
    if required_method is not None:
        payload["required_method"] = required_method
    return AuthoringProposal.model_validate({
        "summary": "one item", "source_refs": [{"ref_type": "manual_context", "ref_id": "manual"}],
        "items": [{"client_item_id": "pi_1", "item_type": "practice_item", "operation": "create",
                   "proposed_entity_id": f"pi_{lo_id}_det", "source_ref_ids": ["manual"], "rationale": "r",
                   "review_route": "review_required", "payload": payload}],
    })


@pytest.mark.parametrize("lo_id, kept", [("lo_cofactor", True), ("lo_determinant", False)])
def test_an_authoring_proposal_keeps_a_required_method_only_on_a_method_target(vault_paths, lo_id, kept):
    root = vault_paths.root
    method = {"name": "cofactor expansion", "criterion_ids": ["method"]}
    patch_id = persist_authoring_proposal(root, _proposal(lo_id, method), provider="import", clock=FrozenClock(NOW))
    [row] = Repository(vault_paths.sqlite_path).proposal_items(patch_id)
    payload = row["payload"]
    if kept:
        assert payload["required_method"] == {"name": "cofactor expansion", "criterion_ids": ["method"],
                                              "learning_object_id": "lo_cofactor", "concept_id": "cofactor_expansion"}
        assert payload["prompt"] == "Compute det(A).\n\nUse cofactor expansion in your answer."
    else:
        assert "required_method" not in payload and payload["prompt"] == "Compute det(A)."
    accept_items(root, patch_id)
    item = load_vault(root).practice_items[f"pi_{lo_id}_det"]
    assert (item.required_method is not None) == kept
    if kept:
        assert item.required_method.concept_id == "cofactor_expansion"
        assert prompt_states_method(item.prompt, item.required_method.name)


# -- generation: the other writers ---------------------------------------------------------


def test_pf_publication_keeps_the_parents_required_method_and_states_it():
    from learnloop.ops.pf_publish import build_item_payload

    parent = _item(prompt="Compute det(A). Use cofactor expansion in your answer.",
                   required_method={"name": "cofactor expansion", "criterion_ids": ["method"]})
    row = {"payload_json": json.dumps({"stem": "Compute det(B) for B = [[2, 1], [1, 2]].", "final_answer": "3",
                                       "solution": "2*2 - 1*1 = 3"}),
           "final_relation": "isomorph", "declared_relation": "isomorph", "difficulty": None,
           "generation_path": "ensemble", "id": "cand1", "family_id": "fam1"}
    payload = build_item_payload(None, parent, row, item_id="pi_pf_x", now_iso=STAMP)
    assert payload["required_method"]["criterion_ids"] == ["method"]
    assert payload["prompt"].endswith("Use cofactor expansion in your answer.")
    plain = build_item_payload(None, _item(), row, item_id="pi_pf_y", now_iso=STAMP)
    assert "required_method" not in plain and plain["prompt"] == "Compute det(B) for B = [[2, 1], [1, 2]]."


def test_synthesis_keeps_a_required_method_only_on_a_procedure_target(vault_paths):
    from types import SimpleNamespace

    from learnloop.content.synthesis.source_set_synthesis import _method_target_view

    vault = load_vault(vault_paths.root)
    rows = [
        {"item_type": "concept", "payload": {"id": "c_gauss", "type": "procedure", "title": "Gaussian elimination"}},
        {"item_type": "learning_object", "payload": {"id": "lo_gauss", "concept_id": "c_gauss"}},
        {"item_type": "concept", "payload": {"id": "c_rank", "type": "concept", "title": "Rank"}},
        {"item_type": "learning_object", "payload": {"id": "lo_rank", "concept_id": "c_rank"}},
    ]
    view = _method_target_view(vault, rows)
    assert isinstance(view, SimpleNamespace)
    [target] = method_targets(view, learning_object_id="lo_gauss")
    assert target.concept_id == "c_gauss"
    assert method_targets(view, learning_object_id="lo_rank") == []
    # Registry targets stay visible beside the batch's.
    assert method_targets(view, learning_object_id="lo_cofactor")[0].concept_id == "cofactor_expansion"


@pytest.mark.parametrize("name, kept, note", [
    ("singular value decomposition", True, None),
    ("SVD", False, "required_method:dropped_source_statement_does_not_state_it"),
    ("Gram-Schmidt", False, "required_method:dropped_unmatched_target"),
], ids=["stated", "not_stated", "not_the_target"])
def test_an_imported_exercise_keeps_a_required_method_only_when_its_statement_states_it(tmp_path, name, kept, note):
    """Source exercise authoring/imports: the book's statement is never
    rewritten, so a required method is kept only when the statement itself
    names it and the mapped object is that method."""

    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from learnloop.content.proposals.ai_contracts import RequiredMethodPayload

    from tests.test_exercise_authoring import FakeClient, _item as exercise_item, _run, _write_facet_registry
    from tests.test_reader_guidance import _setup

    _vault, repository = _setup(tmp_path)
    _write_facet_registry(tmp_path)
    entry = exercise_item(required_method=RequiredMethodPayload(name=name, criterion_ids=["factorization"]))
    result = _run(tmp_path, repository, FakeClient(ExerciseAuthoring(items=[entry])))
    [summary] = result["items"]
    item = load_vault(tmp_path / "vault").practice_items[summary["practice_item_id"]]
    assert item.prompt == "singular value decomposition writes A"  # never rewritten
    if kept:
        assert item.required_method is not None and item.required_method.criterion_ids == ["factorization"]
        assert item.required_method.concept_id == "singular_value_decomposition"
    else:
        assert item.required_method is None
        assert any(note in warning for warning in result.get("warnings", []) + summary.get("warnings", []))
