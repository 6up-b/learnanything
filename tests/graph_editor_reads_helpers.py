"""What other test files use from ``tests/test_graph_editor_reads.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, write_facets
from tests.km3_projections_helpers import COMP_A, COMP_B, INTEG, build_blueprint_vault


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _blueprint_ctx(root: Path):
    """A canonical (mvp-0.7) composite-LO vault with a valid facet registry.

    ``build_blueprint_vault`` writes an invalid ``kind: procedure`` facet, so we
    rewrite the registry with the real v2 contract (valid kinds, an alias, all
    the drawer fields) before loading, then demonstrate the two components.
    """

    import learnloop_sidecar.handlers  # noqa: F401 — registers methods
    from learnloop_sidecar.context import SidecarContext

    paths = build_blueprint_vault(root)
    write_facets(
        paths,
        [
            {
                "id": COMP_A,
                "kind": "procedure_contract",
                "title": "Component A",
                "claim": "Execute component A.",
                "preconditions": ["needs x"],
                "positive_examples": ["a good case"],
                "negative_examples": ["a bad case"],
                "non_goals": ["not this"],
                "error_signatures": ["typical slip"],
                "aliases": ["comp_a_alias"],
                "status": "reviewed",
            },
            {"id": COMP_B, "kind": "definition", "claim": "Component B schema."},
            {"id": INTEG, "kind": "procedure_contract", "claim": "Coordinate the components."},
        ],
    )
    vault = load_vault(paths.root)
    assert not any(issue.code == "yaml:invalid" for issue in vault.issues), vault.issues
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    for item_id, points in (("pi_comp_a", 4), ("pi_comp_b", 4)):
        complete_self_graded_attempt(
            vault,
            repository,
            AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="An answer.",
                attempt_type="independent_attempt",
                hints_used=0,
            ),
            SelfGradeInput(criterion_points={"c1": points}, fatal_errors=[], confidence=4),
            clock=FrozenClock(NOW),
        )
    context = SidecarContext()
    context.load(paths.root)
    return context
