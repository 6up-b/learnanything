"""What other test files use from ``tests/test_pfc_unverified_unassessed.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import split_vault


#: The reference's final answer, reached by a different route: PF-c's
#: final-answer check verifies it.
VERIFYING_ANSWER = "A different route.\nFinal answer: U Sigma V^T"
ITEM = "pi_svd_compute_001"  # setup (2, measures compute) + result (2, measures recall)
CLOCK = FrozenClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC))


class _PartialWithoutAttribution(ReviewFakeClient):
    """Gives ``result`` half its points on any answer, naming no error.

    On a verifying answer the gate records ``result`` unverified while the
    grader's own sum is 3/4: the kept point is what must no longer count."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={"points_awarded": 1.0}) if row.criterion_id == "result" else row
            for row in result.criterion_evidence
        ]
        return result.model_copy(
            update={
                "criterion_evidence": evidence,
                "rubric_score": int(sum(row.points_awarded for row in evidence)),
                "error_attributions": [],
            }
        )


def _mapped_split_vault(tmp_path, version: str = "mvp-0.10"):
    """The split vault with its SVD items' criteria authored onto their facets
    (``setup`` -> compute, ``result`` -> recall), so the attempt step and the
    learner field use the same criterion -> facet map the projection compiles
    from the criteria's targets."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    paths, _vault, repository = split_vault(tmp_path, version=version)
    for item_id in (ITEM, "pi_svd_compute_002"):
        item_path = paths.practice_item_path("linear-algebra", item_id)
        item = read_yaml(item_path)
        item["criterion_facet_weights"] = {"setup": {"compute": 1.0}, "result": {"recall": 1.0}}
        write_yaml(item_path, item)
    return paths, load_vault(paths.root), repository


def _mass(repository, facet: str) -> tuple[float, float]:
    """(positive, negative) projected mass on ``facet``, over capabilities."""

    cells = [cell for cell in repository.facet_capability_evidence_all() if cell.facet_id == facet]
    positive = sum(cell.direct_positive_mass + cell.embedded_positive_mass for cell in cells)
    negative = sum(cell.direct_negative_mass + cell.embedded_negative_mass for cell in cells)
    return positive, negative


def _support(repository, attempt_id: str) -> dict:
    return repository.latest_blind_grade_record(attempt_id)["record"]["grading_support"]
