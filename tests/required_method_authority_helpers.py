"""What other test files use from ``tests/test_required_method_authority.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import closing
from types import SimpleNamespace

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.models import PracticeItem

from tests.helpers import create_basic_vault


STAMP = "2026-10-14T00:00:00Z"
METHOD = "cofactor expansion"
FROZEN = {"name": METHOD, "criterion_ids": ["method"]}


def _item(prompt: str, required_method: dict | None = None, **extra) -> PracticeItem:
    data = {
        "id": "pi_x", "learning_object_id": "lo_svd_definition", "practice_mode": "short_answer",
        "prompt": prompt, "expected_answer": "13",
        "grading_rubric": {"criteria": [
            {"id": "method", "points": 2, "description": "Uses cofactor expansion along the first row."},
            {"id": "result", "points": 2, "description": "Establishes det(A) = 13."},
        ]},
        "created_at": STAMP, "updated_at": STAMP, **extra,
    }
    if required_method is not None:
        data["required_method"] = required_method
    return PracticeItem.model_validate(data)


class StatementDecider:
    """A Decider double for the statement questions: probabilities per stem."""

    provider_name = "openrouter_decider"
    provider_type = "decider"
    model = "perplexity/pplx-decider-v1.2"
    settings = SimpleNamespace(price_per_million_input=0.02)

    def __init__(self, probabilities):
        self.probabilities = probabilities
        self.calls: list[tuple[str, dict]] = []

    def decide(self, state, questions, *, purpose):
        from learnloop.ai.decisions import ChoiceAnswer, DecisionResult
        from learnloop.ai.execution import model_call, report_call_usage

        self.calls.append((state, dict(questions)))
        probabilities = self.probabilities(state) if callable(self.probabilities) else dict(self.probabilities)
        with model_call(self, purpose=purpose, prompt=state):
            report_call_usage({"input_tokens": 150, "output_tokens": 1, "cost": 0.000003})
            answers = {name: ChoiceAnswer(choice=max(probabilities, key=probabilities.get),
                                          probabilities=probabilities) for name in questions}
            return DecisionResult(answers=answers, model=self.model, input_tokens=150, output_tokens=1,
                                  cost=0.000003, response_id="r", provider="Fake")


REQUIRES = {"requires": 0.81, "allows": 0.17, "prohibits": 0.02}
ALLOWS = {"requires": 0.22, "allows": 0.71, "prohibits": 0.07}


def _ledger(repository, task="required_method_statement"):
    with connect(repository.sqlite_path, read_only=True) as connection:
        connection.row_factory = __import__("sqlite3").Row
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = ? ORDER BY created_at, id", (task,))]


SVD = "singular value decomposition"
#: The verify's source reproductions, on the basic vault's method target
#: (``lo_svd_definition``: the singular value decomposition, a procedure).
SOURCE_REPRODUCTIONS = {
    "worked_example": "In the worked example, using singular value decomposition gives A = U S V^T. Factor B.",
    "without_having_to_use": "Factor A without having to use singular value decomposition.",
    "latex_wrapped": "Factor A using \\(\\text{singular value decomposition}\\).",
    "reference_link": "Factor A using [singular value decomposition][svd].\n\n[svd]: https://example.org/svd",
    "which_clause": "Determine which factor is orthogonal using singular value decomposition.",
}


def _setup_statement(tmp_path, text: str):
    from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
    from tests.source_inventory_helpers import _persist, _register_revision

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _register_revision(repository, source_id="src1", revision_id="rev1")
    blocks = [DocumentBlock.build(span_id="s1", block_type="Text", text=text, ordinal=0, page=1,
                                  section_path=["SVD"])]
    ir = DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(unit_id="u1", label="SVD", ordinal=0, semantic_hash="sha256:svd", page_start=1,
                            page_end=1, span_ids=["s1"])],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )
    _persist(repository, ir, revision_id="rev1", extraction_id="ext1")
    return paths, repository


def _import(tmp_path, statement: str, **kwargs):
    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from learnloop.content.proposals.ai_contracts import RequiredMethodPayload
    from tests.exercise_authoring_helpers import FakeClient, _item as exercise_item, _write_facet_registry

    paths, repository = _setup_statement(tmp_path, statement)
    _write_facet_registry(tmp_path)
    entry = exercise_item(required_method=RequiredMethodPayload(name=SVD, criterion_ids=["factorization"]),
                          statement_md=statement)
    result = EX.import_exercises(
        tmp_path / "vault", repository, FakeClient(ExerciseAuthoring(items=[entry])), extraction_id="ext1",
        raw_selection={"nodes": [{"spanId": "s1", "quote": statement}]}, source_id="src1", **kwargs,
    )
    [summary] = result["items"]
    item = load_vault(tmp_path / "vault").practice_items[summary["practice_item_id"]]
    return item, result, repository


def _pf_method_vault(tmp_path):
    from learnloop.vault.writer import upsert_practice_item
    from tests.pf_fakes import seed_pf_vault

    _vault, repository, paths = seed_pf_vault(tmp_path / "vault")
    parent = load_vault(paths.root).practice_items["pi_linear_001"].model_dump(mode="json")
    parent["required_method"] = {"name": "substitution", "criterion_ids": ["setup"]}
    upsert_practice_item(paths.root, parent)
    return repository, paths


VARIANT_CONSISTENT = {"consistent": 0.93, "contradicts": 0.07}


def _verified_method_import(paths, repository, spans):
    from learnloop.vault.writer import upsert_practice_item
    from tests.source_service_fakes import loaded
    from tests.reference_gate_imports_helpers import _verified_import

    item_id = _verified_import(paths, repository, spans)
    data = loaded(paths).practice_items[item_id].model_dump(mode="json")
    [criterion] = data["grading_rubric"]["criteria"][:1]
    data["required_method"] = {"name": "the characteristic polynomial", "criterion_ids": [criterion["id"]],
                               "statement": "source", "decided_by": "owner"}
    upsert_practice_item(paths.root, data)
    # The required method is part of the answer key's identity (method-
    # explicit-3 review F1): requiring a method makes another revision, whose
    # key is checked like any other.
    from learnloop.db.stores.source_service import insert_key_check, reference_content_hash

    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            insert_key_check(connection, id="rkc_method_revision", practice_item_id=item_id,
                             content_hash=reference_content_hash(loaded(paths).practice_items[item_id]),
                             key_status="book_solution", rung="test", trigger="verify",
                             started_at="2026-01-01T00:00:00Z", created_at="2026-01-01T00:00:00Z")
    return item_id, criterion["id"]
