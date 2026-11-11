"""What other test files use from ``tests/test_device_eligibility.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from learnloop_sidecar.request_origin import RequestOrigin

from tests.helpers import NOW, NOW_ISO, create_basic_vault, seed_due_item


PLAIN = "pi_svd_define_001"
HUNT = "pi_phone_hunt"
LADDER = "pi_phone_ladder"
IMAGE = "pi_phone_image"
ORIGIN = RequestOrigin(device_id="dev_phone")
CLOCK = FrozenClock(NOW)


def _call(ctx: SidecarContext, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _payload(item_id: str, **extra) -> dict:
    return {
        "id": item_id,
        "learning_object_id": "lo_svd_definition",
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "prompt": "Define the SVD.",
        "expected_answer": "A factorization into U, Sigma and V transpose.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
            "fatal_errors": [],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
        **extra,
    }


def _world(tmp_path):
    """A vault with due ordinary, error-hunt, laddered and image items."""

    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = seed_due_item(paths)
    items = {
        HUNT: _payload(HUNT, prompt="Correct the worked solution below.", error_hunt={
            "worked_solution_md": "Step 1: S is orthogonal.",
            "planted_errors": [{
                "id": "pe_one", "step_ref": "step 1", "source": "facet_error_signature",
                "error_signature": "S is orthogonal", "required_repair": "S is diagonal", "facet_id": "recall",
            }],
        }),
        LADDER: _payload(LADDER, prompt="Part 2: which factor?", laddered_stem={
            "stem_id": "stem_svd", "part_index": 1, "part_count": 3, "stimulus_md": "Take a 3 by 2 matrix.",
        }),
        IMAGE: _payload(IMAGE, prompt="Which matrix is drawn here?\n\n![the matrix](figures/matrix.png)"),
    }
    for item_id, payload in items.items():
        upsert_practice_item(paths.root, payload, clock=CLOCK)
        repository.upsert_practice_item_state(
            item_id, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z", active=True,
        )
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO mobile_devices (id, label, scope, token_hash, created_at) "
            "VALUES (?, 'Phone', 'app', 'hash', '2026-11-03T00:00:00Z')",
            (ORIGIN.device_id,),
        )
        connection.commit()
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    ctx.grading_provider_override = "manual"
    return paths, repository, ctx


def _ids(queue: dict) -> list[str]:
    return [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]
