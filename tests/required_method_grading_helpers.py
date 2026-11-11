"""What other test files use from ``tests/test_required_method_grading.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

import yaml

from learnloop.algorithm_versions import METHOD_EXPLICIT_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault

from tests.split_live_helpers import split_vault


VERSION = METHOD_EXPLICIT_ALGORITHM_VERSION
ITEM = "pi_svd_compute_001"  # setup (2) + result (2); its LO's concept (SVD) is a procedure
METHOD = "singular value decomposition"
CLOCK = FrozenClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC))


def _require_method(paths, item_id: str = ITEM, criterion_ids=("setup",)) -> None:
    """Make ``item_id`` a method item: the required method (round 3: its
    instruction is rendered from the field, the statement is unchanged)."""

    path = paths.practice_item_path("linear-algebra", item_id)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["required_method"] = {"name": METHOD, "criterion_ids": list(criterion_ids),
                               "learning_object_id": data["learning_object_id"]}
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _method_vault(tmp_path, *, version=VERSION, config="", seed=True):
    paths, _vault, repository = split_vault(tmp_path, version=version, config=config, seed=seed)
    _require_method(paths)
    return paths, load_vault(paths.root), repository


def _support(repository, attempt_id):
    return repository.latest_blind_grade_record(attempt_id)["record"]["grading_support"]


def _projection(repository):
    return sorted(
        (cell.facet_id, cell.capability, round(cell.direct_positive_mass, 12),
         round(cell.direct_negative_mass, 12), round(cell.certification_credit, 12))
        for cell in repository.facet_capability_evidence_all()
    )


def _edit_item(paths, *, prompt: str | None = None, setup_description: str | None = None,
               item_id: str = ITEM) -> None:
    path = paths.practice_item_path("linear-algebra", item_id)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if prompt is not None:
        data["prompt"] = prompt
    if setup_description is not None:
        [setup] = [criterion for criterion in data["grading_rubric"]["criteria"] if criterion["id"] == "setup"]
        setup["description"] = setup_description
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
