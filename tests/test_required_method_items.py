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
    method_statement,
    method_targets,
    names_match,
    normalize_required_method,
    prompt_requires_method,
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
    assert prompt_requires_method("Compute det(A) by Cofactor   Expansion.", "cofactor expansion")
    assert not prompt_requires_method("Compute det(A).", "cofactor expansion")
    assert ensure_method_instruction("Compute det(A).", "cofactor expansion") == (
        "Compute det(A).\n\nUse cofactor expansion in your answer.")
    assert ensure_method_instruction("Use cofactor expansion to compute det(A).", "cofactor expansion") == (
        "Use cofactor expansion to compute det(A).")


# Review F2: naming a method is not requiring it.
METHOD_STATEMENTS = [
    ("Compute det(A). Use cofactor expansion in your answer.", "required"),
    ("Compute det(A) by cofactor expansion along the first row.", "required"),
    ("Using cofactor expansion, compute det(A).", "required"),
    ("Apply cofactor-expansion to the first row.", "required"),
    ("Use cofactor expansion, not row reduction.", "required"),
    ("Compute det(A), which is not zero, using cofactor expansion.", "required"),
    ("You may use cofactor expansion or any other method.", "contradicted"),
    ("Compute det(A) without cofactor expansion.", "contradicted"),
    ("Do not use cofactor expansion.", "contradicted"),
    ("Use row reduction instead of cofactor expansion.", "contradicted"),
    ("Compute det(A), e.g. by cofactor expansion.", "contradicted"),
    ("Use cofactor expansion or row reduction.", "contradicted"),
    ("Use row reduction or cofactor expansion.", "contradicted"),
    ("Cofactor expansion is not allowed here.", "contradicted"),
    ("Use cofactor expansion if you like.", "contradicted"),
    ("Compute det(A). Use cofactor expansion in your answer. You can also skip cofactor expansion.", "contradicted"),
    ("Compute det(A) by cofactor expansion along the first row, or by any other method you like.", "contradicted"),
    ("Use cofactor expansion (or any equivalent method).", "contradicted"),
    ("Use any method, for example cofactor expansion.", "contradicted"),
    ("Compute det(A) using cofactor expansion or another valid approach.", "contradicted"),
    ("Use cofactor expansion to decide whether det(A) is zero or some other value.", "required"),
    ("Use cofactor expansion along the first row or any other row.", "required"),
    ("Explain why cofactor expansion along any row gives the same value.", "mentioned"),
    ("Cofactor expansion is one way to compute a determinant. Compute det(A).", "mentioned"),
    ("Compute det(A).", "absent"),
]


@pytest.mark.parametrize("prompt, expected", METHOD_STATEMENTS, ids=[expected + ":" + prompt[:40]
                                                                     for prompt, expected in METHOD_STATEMENTS])
def test_a_mention_is_not_a_requirement(prompt, expected):
    assert method_statement(prompt, "cofactor expansion") == expected
    assert prompt_requires_method(prompt, "cofactor expansion") == (expected == "required")


def test_the_writers_require_an_affirmative_statement(vault_paths):
    """A generated prompt that only mentions the method gets the explicit
    instruction; one that negates it or leaves it optional loses the
    requirement (an instruction would contradict it); a source statement
    that only mentions it is never rewritten, so the requirement is dropped."""

    vault = load_vault(vault_paths.root)
    targets = method_targets(vault, learning_object_id="lo_cofactor")
    rubric = {"criteria": [{"id": "method"}, {"id": "result"}]}

    def payload(prompt):
        return {"prompt": prompt, "grading_rubric": rubric,
                "required_method": {"name": "cofactor expansion", "criterion_ids": ["method"]}}

    mentioned = payload("Explain why cofactor expansion along any row gives det(A).")
    assert normalize_required_method(mentioned, targets) == ["required_method:instruction_added"]
    assert mentioned["prompt"].endswith("\n\nUse cofactor expansion in your answer.")
    for prompt in ("You may use cofactor expansion or any other method.", "Compute det(A) without cofactor expansion."):
        contradicted = payload(prompt)
        assert normalize_required_method(contradicted, targets) == ["required_method:dropped_prompt_contradicts_it"]
        assert contradicted["prompt"] == prompt and "required_method" not in contradicted
    source = payload("Cofactor expansion computes det(A) for A = [[1, 2], [3, 4]].")
    assert normalize_required_method(source, targets, source_statement=True) == [
        "required_method:dropped_source_statement_does_not_state_it"]
    stated_source = payload("Using cofactor expansion, compute det(A).")
    assert normalize_required_method(stated_source, targets, source_statement=True) == []
    assert stated_source["required_method"]["name"] == "cofactor expansion"
    # A variant whose stem leaves the method open is noted (doctor reports it).
    parent = _item(prompt="Compute det(A). Use cofactor expansion in your answer.",
                   required_method={"name": "cofactor expansion", "criterion_ids": ["method"]})
    variant = {"prompt": "Compute det(B) with any method, for example cofactor expansion."}
    assert "required_method:prompt_contradicts_it" in inherit_required_method(variant, parent)


def test_validation_reports_a_requirement_its_prompt_contradicts():
    rubric = Rubric.model_validate({"criteria": [
        {"id": "method", "points": 2, "description": "Uses cofactor expansion along the first row."},
        {"id": "result", "points": 2, "description": "Establishes det(A) = 13."},
    ]})
    method = {"name": "cofactor expansion", "criterion_ids": ["method"]}
    codes = lambda prompt: [p.code for p in required_method_problems(  # noqa: E731
        _item(prompt=prompt, required_method=method), rubric)]
    assert codes("You may use cofactor expansion or any other method.") == ["required_method:contradicted"]
    assert codes("Compute det(A) without cofactor expansion.") == ["required_method:contradicted"]
    assert codes("Explain why cofactor expansion works, then compute det(A).") == ["required_method:not_stated"]
    assert codes("Compute det(A). Use cofactor expansion in your answer.") == []


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
        assert prompt_requires_method(item.prompt, item.required_method.name)


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


REQUIRING_STATEMENT = "Using singular value decomposition, write A as U Sigma V transpose."


def _setup_requiring_statement(tmp_path):
    """``tests.test_reader_guidance._setup`` with a source statement that
    REQUIRES the method (review F2: a statement that only names it does not)."""

    from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth

    from tests.test_source_inventory import _persist, _register_revision

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _register_revision(repository, source_id="src1", revision_id="rev1")
    blocks = [DocumentBlock.build(span_id="s1", block_type="Text", text=REQUIRING_STATEMENT, ordinal=0, page=1,
                                  section_path=["SVD"])]
    ir = DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(unit_id="u1", label="SVD", ordinal=0, semantic_hash="sha256:svd", page_start=1,
                            page_end=1, span_ids=["s1"])],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )
    _persist(repository, ir, revision_id="rev1", extraction_id="ext1")
    return repository


@pytest.mark.parametrize("name, requiring, kept, note", [
    ("singular value decomposition", True, True, None),
    ("singular value decomposition", False, False, "required_method:dropped_source_statement_does_not_state_it"),
    ("SVD", False, False, "required_method:dropped_source_statement_does_not_state_it"),
    ("Gram-Schmidt", False, False, "required_method:dropped_unmatched_target"),
], ids=["required", "only_named", "not_stated", "not_the_target"])
def test_an_imported_exercise_keeps_a_required_method_only_when_its_statement_states_it(
        tmp_path, name, requiring, kept, note):
    """Source exercise authoring/imports: the book's statement is never
    rewritten, so a required method is kept only when the statement itself
    requires it (naming it is not enough: review F2) and the mapped object is
    that method."""

    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from learnloop.content.proposals.ai_contracts import RequiredMethodPayload

    from tests.test_exercise_authoring import FakeClient, _item as exercise_item, _run, _write_facet_registry
    from tests.test_reader_guidance import _setup

    method = RequiredMethodPayload(name=name, criterion_ids=["factorization"])
    if requiring:
        repository = _setup_requiring_statement(tmp_path)
        _write_facet_registry(tmp_path)
        statement = "Using singular value decomposition, write A"
        entry = exercise_item(required_method=method, statement_md=statement)
        result = EX.import_exercises(
            tmp_path / "vault", repository, FakeClient(ExerciseAuthoring(items=[entry])), extraction_id="ext1",
            raw_selection={"nodes": [{"spanId": "s1", "quote": statement}]}, source_id="src1",
        )
    else:
        _vault, repository = _setup(tmp_path)
        _write_facet_registry(tmp_path)
        statement = "singular value decomposition writes A"
        entry = exercise_item(required_method=method)
        result = _run(tmp_path, repository, FakeClient(ExerciseAuthoring(items=[entry])))
    [summary] = result["items"]
    item = load_vault(tmp_path / "vault").practice_items[summary["practice_item_id"]]
    assert item.prompt == statement  # never rewritten
    if kept:
        assert item.required_method is not None and item.required_method.criterion_ids == ["factorization"]
        assert item.required_method.concept_id == "singular_value_decomposition"
    else:
        assert item.required_method is None
        assert any(note in warning for warning in result.get("warnings", []) + summary.get("warnings", []))


def test_synthesis_publishes_a_required_method_only_with_an_affirmative_instruction(tmp_path):
    """The study-map writer end to end (normalization, gates, apply): on a
    method target, an item whose prompt only mentions the method is published
    with the explicit instruction; one whose prompt leaves it optional loses
    the requirement, with a review diagnostic (review F2)."""

    from learnloop.content.synthesis.ai_contracts import SynthRequiredMethod
    from learnloop.content.synthesis.source_set_synthesis import create_study_map

    from tests.test_source_set_synthesis import _CLOCK, FakeSynthesisClient, _default_payload, _setup

    def builder(context, _calls):
        payload = _default_payload(context)
        concepts = [concept.model_copy(update={"type": "procedure", "title": "Orthogonal diagonalization"})
                    for concept in payload.concepts]
        mentioned, optional = payload.practice_items
        mentioned = mentioned.model_copy(update={
            "prompt": "Explain how orthogonal diagonalization applies to A.",
            "required_method": SynthRequiredMethod(name="orthogonal diagonalization",
                                                   criterion_ids=["identifies_symmetry"]),
        })
        optional = optional.model_copy(update={
            "prompt": "Diagonalize A; you may use orthogonal diagonalization or any other method.",
            "required_method": SynthRequiredMethod(name="orthogonal diagonalization",
                                                   criterion_ids=["selects_spectral"]),
        })
        return payload.model_copy(update={"concepts": concepts, "practice_items": [mentioned, optional]})

    root, repo = _setup(tmp_path)
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(builder=builder), brief={"depth": "intro"},
                              repository=repo, clock=_CLOCK, apply=True)
    assert result.applied is True
    vault = load_vault(root)
    published = vault.practice_items["pi_identify_symmetry"]
    assert published.required_method is not None
    assert published.required_method.criterion_ids == ["identifies_symmetry"]
    assert published.prompt.endswith("\n\nUse orthogonal diagonalization in your answer.")
    assert prompt_requires_method(published.prompt, published.required_method.name)
    dropped = vault.practice_items["pi_select_spectral"]
    assert dropped.required_method is None
    assert dropped.prompt == "Diagonalize A; you may use orthogonal diagonalization or any other method."
    assert any(d["gate"] == "required_method" and "dropped_prompt_contradicts_it" in d["message"]
               for d in result.gate_diagnostics)


# -- re-review (Codex 2026-10-13) -----------------------------------------------------------

# F2 (reopened): a descriptive clause is not an instruction, and "not required to
# use" negates; F9: inline formatting never hides an explicit instruction.
RE_REVIEW_STATEMENTS = [
    ("You are not required to use cofactor expansion. Compute det(A).", "contradicted"),
    ("It is not necessary to use cofactor expansion.", "contradicted"),
    ("You do not need to use cofactor expansion.", "contradicted"),
    ("You don't have to apply cofactor expansion.", "contradicted"),
    ("There is no need to use cofactor expansion here.", "contradicted"),
    ("The worked example uses cofactor expansion. Compute det(A).", "mentioned"),
    ("The worked example computes det(A) by cofactor expansion. Compute det(B).", "mentioned"),
    ("In the worked example, we use cofactor expansion. Compute det(B).", "mentioned"),
    ("In the worked example, the authors, using cofactor expansion, compute det(A). Compute det(B).", "mentioned"),
    ("Explain why the worked example uses cofactor expansion.", "mentioned"),
    ("Explain how to use cofactor expansion.", "mentioned"),
    ("Compute det(A), which the worked example finds by cofactor expansion.", "mentioned"),
    ("Recall that the textbook applies cofactor expansion. Compute det(A).", "mentioned"),
    ("For the matrix A below, compute det(A) by cofactor expansion.", "required"),
    ("Given A = [[1, 2], [3, 4]], compute det(A) using cofactor expansion.", "required"),
    ("(a) Compute det(A) by cofactor expansion.", "required"),
    ("In part (b), use cofactor expansion.", "required"),
    ("You must use cofactor expansion.", "required"),
    ("Your answer should use cofactor expansion.", "required"),
    ("Show, using cofactor expansion, that det(A) = 0.", "required"),
    ("Cofactor expansion must be used.", "required"),
    ("Please compute det(A) and verify it by cofactor expansion.", "required"),
    ("Compute det(A) using **cofactor expansion**.", "required"),
    ("Compute det(A) using *cofactor expansion*.", "required"),
    ("Compute det(A) using __cofactor expansion__.", "required"),
    ("Compute det(A) using `cofactor expansion`.", "required"),
    ("**Use cofactor expansion** in your answer.", "required"),
    ("Compute det(A) using [cofactor expansion](https://example.org/cofactor).", "required"),
    ("Compute det(A) using <b>cofactor expansion</b>.", "required"),
    ("Compute det(A) without **cofactor expansion**.", "contradicted"),
    ("You may use *cofactor expansion* or any other method.", "contradicted"),
]


@pytest.mark.parametrize("prompt, expected", RE_REVIEW_STATEMENTS, ids=[expected + ":" + prompt[:48]
                                                                        for prompt, expected in RE_REVIEW_STATEMENTS])
def test_rereview_an_instruction_is_read_through_descriptions_negations_and_formatting(prompt, expected):
    assert method_statement(prompt, "cofactor expansion") == expected
    assert prompt_requires_method(prompt, "cofactor expansion") == (expected == "required")


# F2/F9 (cont.): an instruction whose verb is not on the imperative list, or
# that follows a fronted condition, still requires the method (dropping it from
# a source statement would silently disable enforcement); a description with
# math in it, a conditional use and "whether to use" never do.
RE_REVIEW_NAMED_STATEMENTS = [
    ("Proceed by induction on n.", "induction", "required"),
    ("Prove the claim. Proceed by induction on n.", "induction", "required"),
    ("Fit the model using least squares.", "least squares", "required"),
    ("Fit f(x) to the data using least squares.", "least squares", "required"),
    ("Rank the matrix using row echelon form.", "row echelon form", "required"),
    ("Tabulate the values by cofactor expansion.", "cofactor expansion", "required"),
    ("Solve Ax = b by Gaussian elimination.", "gaussian elimination", "required"),
    ("If A is invertible, compute A^{-1} by row reduction.", "row reduction", "required"),
    ("Since A is symmetric, diagonalize it by orthogonal diagonalization.", "orthogonal diagonalization", "required"),
    ("As in part (a), use cofactor expansion.", "cofactor expansion", "required"),
    ("Determine whether the vectors are independent by row reduction.", "row reduction", "required"),
    ("Your task is to compute det(A) using cofactor expansion.", "cofactor expansion", "required"),
    ("x^2 + 6x + 5 = 0, solve it by completing the square.", "completing the square", "required"),
    ("The worked example solves Ax = b by Gaussian elimination.", "gaussian elimination", "mentioned"),
    ("Students solve Ax = b by Gaussian elimination.", "gaussian elimination", "mentioned"),
    ("When using cofactor expansion, expand along a row with zeros.", "cofactor expansion", "mentioned"),
    ("If using cofactor expansion, show each minor.", "cofactor expansion", "mentioned"),
    ("Decide whether to use cofactor expansion.", "cofactor expansion", "mentioned"),
    ("Note that the worked example computes det(A) by cofactor expansion. Compute det(B).", "cofactor expansion",
     "mentioned"),
    ("Earlier the example computed det(A) by cofactor expansion. Compute det(B).", "cofactor expansion", "mentioned"),
]


@pytest.mark.parametrize("prompt, name, expected", RE_REVIEW_NAMED_STATEMENTS,
                         ids=[expected + ":" + prompt[:48] for prompt, _name, expected in RE_REVIEW_NAMED_STATEMENTS])
def test_rereview_instructions_beyond_the_imperative_list_and_descriptions_with_math(prompt, name, expected):
    assert method_statement(prompt, name) == expected


def test_rereview_source_normalization_and_grading_read_the_instruction_not_its_formatting(vault_paths):
    """F9: a formatted explicit source instruction keeps its requirement through
    the writer check and the grader's policy; F2: an explanatory mention in a
    source statement is not one, so the requirement is dropped (the statement
    is never rewritten)."""

    from learnloop.attempts.grading_support import required_method_policy

    vault = load_vault(vault_paths.root)
    targets = method_targets(vault, learning_object_id="lo_cofactor")
    rubric = {"criteria": [{"id": "method"}, {"id": "result"}]}

    def payload(prompt):
        return {"prompt": prompt, "grading_rubric": rubric,
                "required_method": {"name": "cofactor expansion", "criterion_ids": ["method"]}}

    formatted = payload("Compute det(A) using **cofactor expansion**.")
    assert normalize_required_method(formatted, targets, source_statement=True) == []
    assert formatted["required_method"]["criterion_ids"] == ["method"]
    assert formatted["prompt"] == "Compute det(A) using **cofactor expansion**."
    item = _item(prompt=formatted["prompt"], required_method={"name": "cofactor expansion", "criterion_ids": ["method"]})
    policy = required_method_policy(item, ["method", "result"], presented_prompt=item.prompt)
    assert policy == {"name": "cofactor expansion", "criterion_ids": ["method"]}
    assert required_method_problems(item, item.grading_rubric) == []
    described = payload("The worked example uses cofactor expansion. Compute det(A).")
    assert normalize_required_method(described, targets, source_statement=True) == [
        "required_method:dropped_source_statement_does_not_state_it"]
    assert "required_method" not in described
    assert described["prompt"] == "The worked example uses cofactor expansion. Compute det(A)."
    negated = payload("You are not required to use cofactor expansion. Compute det(A).")
    assert normalize_required_method(negated, targets) == ["required_method:dropped_prompt_contradicts_it"]
    assert "required_method" not in negated and negated["prompt"].startswith("You are not required")


def test_rereview_a_contradicting_variant_gains_no_instruction_and_is_never_published():
    """F10: a variant stem that negates the parent's method gets no appended
    instruction (it would contradict the statement); publication refuses it."""

    from learnloop.ops.pf_publish import PublishRefused, VariantContradictsRequiredMethod, build_item_payload

    parent = _item(prompt="Compute det(A). Use cofactor expansion in your answer.",
                   required_method={"name": "cofactor expansion", "criterion_ids": ["method"]})
    variant = {"prompt": "Compute det(B) without cofactor expansion."}
    notes = inherit_required_method(variant, parent)
    assert "required_method:prompt_contradicts_it" in notes
    assert "required_method:instruction_added" not in notes
    assert variant["prompt"] == "Compute det(B) without cofactor expansion."
    row = {"payload_json": json.dumps({"stem": "Compute det(B) without cofactor expansion.", "final_answer": "3",
                                       "solution": "2*2 - 1*1 = 3"}),
           "final_relation": "isomorph", "declared_relation": "isomorph", "difficulty": None,
           "generation_path": "ensemble", "id": "cand1", "family_id": "fam1"}
    with pytest.raises(VariantContradictsRequiredMethod, match="cofactor expansion") as refused:
        build_item_payload(None, parent, row, item_id="pi_pf_x", now_iso=STAMP)
    assert isinstance(refused.value, PublishRefused)


def test_rereview_publication_rejects_a_selected_variant_that_contradicts_the_parents_method(tmp_path):
    """F10 end to end: a selected variant whose stem negates the parent's
    required method is refused at publication (ledgered, the candidate
    rejected so the next run regenerates), never published with a
    contradictory appended instruction."""

    from learnloop.content.authoring.pf_sandbox import sandbox_available
    from learnloop.db.stores import pf as store
    from learnloop.ops.pf_generation import publish_backlog
    from learnloop.vault.writer import upsert_practice_item

    from tests.pf_fakes import seed_pf_vault
    from tests.test_pf_generation import NEXT_DAY, ledger, rows, run

    if not sandbox_available():
        pytest.skip("bubblewrap is not installed")
    _vault, repository, paths = seed_pf_vault(tmp_path / "vault")
    parent = load_vault(paths.root).practice_items["pi_linear_001"].model_dump(mode="json")
    parent["prompt"] = "Solve 2x + 4 = 10 for x. Use substitution in your answer."
    parent["required_method"] = {"name": "substitution", "criterion_ids": ["setup"]}
    upsert_practice_item(paths.root, parent)
    run(paths, publish=False, select=1)
    [selected] = rows(repository, "status='selected'")
    payload = json.loads(selected["payload_json"])
    payload["stem"] = "Solve 3x + 2 = 11 for x without substitution."
    with repository.connection() as connection:
        store.update_candidate(connection, selected["id"], payload_json=json.dumps(payload))
    outcome = publish_backlog(load_vault(paths.root), clock=NEXT_DAY)
    assert outcome["published_item_ids"] == [] and outcome["refused_candidates"] == 1
    [row] = rows(repository, "id=?", (selected["id"],))
    assert row["status"] == "rejected" and row["rejection_filter"] == "required_method_contradicted"
    refusals = [entry for entry in ledger(repository, "pf_publish") if entry["verdict"] == "refuse_contradicts_required_method"]
    assert len(refusals) == 1 and refusals[0]["left_id"] == selected["id"]
    assert not any("pf_generated" in item.tags for item in load_vault(paths.root).practice_items.values())
