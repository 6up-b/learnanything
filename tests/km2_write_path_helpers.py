"""What other test files use from ``tests/test_km2_write_path.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW_ISO, create_basic_vault, set_algorithm_version, write_facets


SHARED = "facet_svd_factorization"
SELECT = "facet_svd_method_selection"


def _rubric(criterion_id, targets, *, points=4, correlation_group=None, depends_on=None):
    crit = {
        "id": criterion_id,
        "points": points,
        "description": f"{criterion_id} criterion.",
        "targets": targets,
    }
    if correlation_group is not None:
        crit["correlation_group"] = correlation_group
    if depends_on is not None:
        crit["depends_on"] = depends_on
    return {"max_points": points, "criteria": [crit], "fatal_errors": []}


def _item(item_id, lo_id, *, evidence_facets, rubric, fingerprint=None):
    payload = {
        "schema_version": 1,
        "id": item_id,
        "learning_object_id": lo_id,
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": evidence_facets,
        "evidence_weights": {f: 1.0 for f in evidence_facets},
        "prompt": f"Prompt for {item_id}.",
        "expected_answer": "An answer.",
        "difficulty": 0.5,
        "grading_rubric": rubric,
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    if fingerprint is not None:
        payload["evidence_fingerprint"] = fingerprint
    return payload


def _lo(lo_id, title, summary):
    return {
        "schema_version": 1,
        "id": lo_id,
        "title": title,
        "subjects": ["linear-algebra"],
        "concept": "singular_value_decomposition",
        "knowledge_type": "definition",
        "status": "active",
        "contradicts": None,
        "summary": summary,
        "prerequisites": [],
        "confusables": [],
        "difficulty_prior": 0.55,
        "tags": [],
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


# The tag a few tests still pin: they read what the canonical-state path stamps (the consuming projection version,
# the near-clone discount's surface groups) and the head's path differs (D6 retires the tag's path).
KM2_OLD_TAG = "mvp-0.7"


def build_shared_facet_vault(root: Path, *, version: str = LATEST_ALGORITHM_VERSION):
    """A minimal fixture at ``version`` (the head by default): one shared canonical facet across two LOs."""

    paths = create_basic_vault(root)
    # No goal, so certified scope does not lock the facet during grace-window work.
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    write_facets(
        paths,
        [
            {"id": SHARED, "kind": "definition", "claim": "SVD factorizes into U, Sigma, V^T."},
            {"id": SELECT, "kind": "applicability_condition", "claim": "When SVD applies."},
            {"id": "recall", "kind": "definition", "claim": "SVD recall."},
        ],
    )
    # LO 1 already exists (lo_svd_definition). Re-author its item to target the
    # shared canonical facet at retrieval capability.
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_001"),
        _item(
            "pi_svd_define_001",
            "lo_svd_definition",
            evidence_facets=[SHARED],
            rubric=_rubric(
                "correctness",
                [{"facet": SHARED, "capability": "retrieval", "role": "primary"}],
                correlation_group="svd_definition",
            ),
            fingerprint={"source_family": "chapter3-definition"},
        ),
    )
    # LO 2: a second learning object on the same concept, whose item exercises
    # the SAME shared canonical facet -> one shared belief parent.
    write_yaml(
        paths.learning_object_path("linear-algebra", "lo_svd_application"),
        _lo("lo_svd_application", "SVD application", "Applying SVD in practice."),
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_apply_001"),
        _item(
            "pi_svd_apply_001",
            "lo_svd_application",
            evidence_facets=[SHARED],
            rubric=_rubric(
                "uses_factorization",
                [{"facet": SHARED, "capability": "retrieval", "role": "primary"}],
                correlation_group="svd_application",
            ),
            fingerprint={"source_family": "chapter5-application"},
        ),
    )
    # A near-clone under LO 2 sharing LO 1's item's source-example family: it
    # must NOT mint a fresh independent surface group (§6).
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_clone_001"),
        _item(
            "pi_svd_clone_001",
            "lo_svd_application",
            evidence_facets=[SHARED],
            rubric=_rubric(
                "uses_factorization",
                [{"facet": SHARED, "capability": "retrieval", "role": "primary"}],
                correlation_group="svd_definition",
            ),
            fingerprint={"source_family": "chapter3-definition"},  # same as define item
        ),
    )
    # An item whose single whole-item criterion maps to several candidate facets
    # with no resolving attribution: a wrong answer is an unresolved cause set.
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_ambiguous_001"),
        _item(
            "pi_svd_ambiguous_001",
            "lo_svd_definition",
            evidence_facets=[SHARED, SELECT],
            rubric=_rubric(
                "whole_item",
                [
                    {"facet": SHARED, "capability": "retrieval", "role": "primary"},
                    {"facet": SELECT, "capability": "method_selection", "role": "primary"},
                ],
            ),
            fingerprint={"source_family": "chapter7-ambiguous"},
        ),
    )
    if version != LATEST_ALGORITHM_VERSION:
        set_algorithm_version(paths, version)
    return paths


def _attempt(vault, repository, item_id, points, clock, *, hints_used=0):
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="An answer.",
            attempt_type="independent_attempt",
            hints_used=hints_used,
        ),
        SelfGradeInput(criterion_points=points, fatal_errors=[], confidence=4),
        clock=clock,
    )
