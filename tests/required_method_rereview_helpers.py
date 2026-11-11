"""What other test files use from ``tests/test_required_method_rereview.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from contextlib import closing

import yaml

from learnloop.db.connection import connect

from tests.required_method_authority_helpers import StatementDecider


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
    from tests.reference_gate_imports_helpers import _verified_import

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
