"""The shared §3.A2/§3.A3 presentation payload, and its two consumers.

Spec: ``spec_measurement_efficiency_v1.md`` §3.A2/§3.A3, and the Stage 6
adversarial review that found error hunts and laddered stems authored, gated,
stored and audited — with no renderer, so
``learnloop.substrate.instrument_serving`` had to
keep them out of the queue entirely.

What is tested here is not "the field exists". It is the three properties that,
if any one of them slips, put the defect back:

* the payload carries the WHOLE stimulus, not the prompt plus whatever the
  reading surface happened to know to ask for;
* practice and exams read the SAME producer, because the original defect was two
  prompt-only DTOs and fixing one of them fixes half a bug;
* blank content is a typed REFUSAL. An empty worked solution rendered as an empty
  block is the silent failure again: the learner cannot answer, the grader (which
  receives the solution through its own path) marks every planted error missed,
  and the projection banks negative facet mass for a repair nobody was shown the
  material to make. A refusal is louder than that and strictly safer.
"""

from __future__ import annotations

import pytest

from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.errors import SidecarError
from tests.helpers import create_basic_vault, seed_due_item

ITEM = "pi_svd_define_001"
SUBJECT = "linear-algebra"


@pytest.fixture()
def ctx(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    context = SidecarContext()
    context.load(paths.root)
    context.grading_provider_override = "manual"
    context.paths = paths
    return context


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _patch_item(ctx, **fields) -> None:
    path = ctx.paths.practice_item_path(SUBJECT, ITEM)
    document = read_yaml(path)
    document.update(fields)
    write_yaml(path, document)
    ctx.reload(maintenance=False)
    ctx.grading_provider_override = "manual"


def _blocks(presentation) -> list[tuple[str, str]]:
    return [(block["kind"], block["markdown"]) for block in presentation["blocks"]]


def _presentation(ctx) -> dict:
    return _call(ctx, "get_practice_item", {"practiceItemId": ITEM})["presentation"]


# ---------------------------------------------------------------------------
# The payload itself
# ---------------------------------------------------------------------------


def test_an_ordinary_item_presents_exactly_its_prompt(ctx):
    """No instrument contract, no extra blocks — the payload is not a place to
    park optional chrome, it is the answer to "what must be seen"."""

    vault, _repository = ctx.require_vault()

    assert _blocks(_presentation(ctx)) == [("prompt", vault.practice_items[ITEM].prompt)]


def test_an_error_hunt_carries_the_worked_solution_it_asks_the_learner_to_repair(ctx):
    _patch_item(
        ctx,
        error_hunt={
            "worked_solution_md": "Step 1. $A = U\\Sigma V^T$\nStep 2. take the inverse",
            "planted_errors": [],
        },
    )

    blocks = _blocks(_presentation(ctx))

    assert [kind for kind, _ in blocks] == ["prompt", "error_hunt_worked_solution"]
    assert "Step 2. take the inverse" in dict(blocks)["error_hunt_worked_solution"]


def test_the_error_hunt_label_never_declares_that_there_is_an_error(ctx):
    """§3.A3 forbids declaring the error count, and the CLEAN rotation is what
    kills the "there is always an error" strategy. A caption reading "find the
    mistakes" would leak both — over a clean solution it would also be false."""

    _patch_item(
        ctx,
        error_hunt={"worked_solution_md": "a correct derivation", "planted_errors": []},
    )

    label = next(
        block["label"]
        for block in _presentation(ctx)["blocks"]
        if block["kind"] == "error_hunt_worked_solution"
    )

    lowered = (label or "").lower()
    assert not any(word in lowered for word in ("error", "mistake", "wrong", "repair"))


def test_a_laddered_stem_part_carries_the_stimulus_its_parts_climb(ctx):
    _patch_item(
        ctx,
        laddered_stem={
            "stem_id": "stem_svd_001",
            "part_index": 2,
            "part_count": 4,
            "stimulus_md": "Let $A$ be the 3x2 matrix below.",
        },
    )

    blocks = _presentation(ctx)["blocks"]

    assert [block["kind"] for block in blocks] == ["laddered_stem_stimulus", "prompt"]
    assert blocks[0]["markdown"] == "Let $A$ be the 3x2 matrix below."
    # Part identity travels so the caption can say the setup is SHARED rather
    # than looking like a new scenario each time.
    assert blocks[0]["stemId"] == "stem_svd_001"
    assert "3 of 4" in blocks[0]["label"]


def test_every_part_of_a_stem_carries_the_stimulus_not_only_the_first(ctx):
    """Parts are independently scheduled items and nothing sequences a ladder
    run: part 3 can arrive days after part 1, in another session, with parts 1-2
    never served. "Show it once" would serve the rest unanswerable."""

    for part_index in (0, 3):
        _patch_item(
            ctx,
            laddered_stem={
                "stem_id": "stem_svd_001",
                "part_index": part_index,
                "part_count": 4,
                "stimulus_md": "Let $A$ be the 3x2 matrix below.",
            },
        )

        kinds = [block["kind"] for block in _presentation(ctx)["blocks"]]

        assert kinds[0] == "laddered_stem_stimulus"


# ---------------------------------------------------------------------------
# Blank content is a refusal, not an empty render
# ---------------------------------------------------------------------------


def test_an_error_hunt_with_no_worked_solution_is_a_typed_refusal(ctx):
    _patch_item(ctx, error_hunt={"worked_solution_md": "   ", "planted_errors": []})

    with pytest.raises(SidecarError) as exc:
        _presentation(ctx)

    assert exc.value.code == "item_stimulus_unrenderable"
    assert exc.value.details["reason"] == "error_hunt_worked_solution_blank"
    assert exc.value.details["practice_item_id"] == ITEM


def test_a_stem_part_with_no_stimulus_is_a_typed_refusal(ctx):
    """``stimulus_md`` is Optional on the model, so "present" does not imply
    "renderable" — the data-level check has to stay after rendering lands."""

    _patch_item(
        ctx,
        laddered_stem={"stem_id": "stem_svd_001", "part_index": 0, "part_count": 2},
    )

    with pytest.raises(SidecarError) as exc:
        _presentation(ctx)

    assert exc.value.code == "item_stimulus_unrenderable"
    assert exc.value.details["reason"] == "laddered_stem_stimulus_blank"
    assert exc.value.details["stem_id"] == "stem_svd_001"


# ---------------------------------------------------------------------------
# Both consumers, one producer
# ---------------------------------------------------------------------------


def test_the_exam_surface_serves_the_same_payload_as_practice(ctx):
    """Exams had their own prompt-only DTO, which is exactly why fixing only the
    practice screen would have left an error hunt served solution-less in the one
    mode where the measurement is held out and cannot be re-run."""

    from learnloop_sidecar.handlers.serializers import item_presentation

    _patch_item(
        ctx,
        error_hunt={"worked_solution_md": "Step 1. take the inverse", "planted_errors": []},
    )
    vault, _repository = ctx.require_vault()

    from learnloop_sidecar.handlers.exams import _session_snapshot

    snapshot = _session_snapshot(
        ctx,
        {"session_id": "sess_x", "goal_id": "goal_linear_algebra_ml", "status": "in_progress", "item_order": [ITEM]},
    )

    served = snapshot["items"][0]["presentation"]
    assert served == _to_camel(item_presentation(vault.practice_items[ITEM]))
    assert [block["kind"] for block in served["blocks"]] == [
        "prompt",
        "error_hunt_worked_solution",
    ]


def test_an_exam_item_deleted_from_the_vault_still_renders_rather_than_failing(ctx):
    """A reserved item removed mid-session must not make the whole session
    unresumable — the learner still has to be able to finish and be scored."""

    from learnloop_sidecar.handlers.exams import _session_snapshot

    snapshot = _session_snapshot(
        ctx,
        {"session_id": "sess_x", "goal_id": "goal_linear_algebra_ml", "status": "in_progress", "item_order": ["pi_gone"]},
    )

    assert _blocks(snapshot["items"][0]["presentation"]) == [("prompt", "(missing item)")]


def _to_camel(value):
    from learnloop_sidecar.dto import to_camel

    return to_camel(value)


# ---------------------------------------------------------------------------
# A1: the authored observation contract reaches the app
# ---------------------------------------------------------------------------


def test_rubric_criteria_expose_their_authored_targets_and_dependencies(ctx):
    """A criterion's `targets` are what it CLAIMS to observe. Serialized but
    untyped in the app, they could only be checked by reading YAML."""

    path = ctx.paths.practice_item_path(SUBJECT, ITEM)
    document = read_yaml(path)
    document["grading_rubric"] = {
        "max_points": 4,
        "criteria": [
            {
                "id": "correctness",
                "points": 4,
                "description": "States the factorization.",
                "targets": [
                    {"facet": "recall", "capability": "retrieval", "role": "primary"}
                ],
                "depends_on": ["setup"],
            }
        ],
        "fatal_errors": [],
    }
    write_yaml(path, document)
    ctx.reload(maintenance=False)
    ctx.grading_provider_override = "manual"

    rubric = _call(ctx, "get_practice_item", {"practiceItemId": ITEM})["rubric"]

    criterion = rubric["criteria"][0]
    assert criterion["targets"] == [
        {"facet": "recall", "capability": "retrieval", "role": "primary"}
    ]
    assert criterion["dependsOn"] == ["setup"]
