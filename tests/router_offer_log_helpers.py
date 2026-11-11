"""What other test files use from ``tests/test_router_offer_log.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json

from tests.helpers import add_followup_item, append_config_toml, create_basic_vault, seed_due_item


SECOND_ITEM = "pi_svd_define_002"


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _context(root):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    context = SidecarContext()
    context.load(root)
    context.grading_provider_override = "manual"
    return context


def _decisions(repository, kind: str | None = None) -> list[dict]:
    with repository.connection() as connection:
        rows = [dict(row) for row in connection.execute("SELECT * FROM router_decisions ORDER BY created_at, id")]
    for row in rows:
        for column in ("candidates_json", "exclusions_json", "detail_json"):
            row[column] = json.loads(row[column])
    return [row for row in rows if kind is None or row["decision_kind"] == kind]


def _served(queue) -> list[str]:
    return [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]


def _two_due_items(tmp_path, *, toml: str | None = None):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    add_followup_item(paths.root, SECOND_ITEM)
    repository.upsert_practice_item_state(
        SECOND_ITEM, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=True,
    )
    if toml:
        append_config_toml(paths.root, toml)
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=20, notes_md_path=None)
    return paths, repository, _context(paths.root), session_id


_TEACH_BACK_ITEM = {
    "id": "pi_svd_teach_back",
    "learning_object_id": "lo_svd_definition",
    "subjects": None,
    "practice_mode": "teach_back",
    "attempt_types_allowed": ["teach_back"],
    "evidence_facets": ["recall"],
    "evidence_weights": {"recall": 1.0},
    "criterion_facet_weights": {"core_definition": {"recall": 1.0}},
    "prompt": "Teach the singular value decomposition to a curious student.",
    "expected_answer": "U, Sigma and V transpose.",
    "grading_rubric": {
        "max_points": 1,
        "criteria": [{"id": "core_definition", "points": 1.0, "tier": "core", "description": "States U, Sigma, V."}],
        "fatal_errors": [],
    },
    "created_at": "2026-05-19T12:00:00Z",
    "updated_at": "2026-05-19T12:00:00Z",
}
