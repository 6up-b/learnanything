from __future__ import annotations

import pytest

from learnloop_sidecar.errors import SidecarError
from tests.helpers import create_basic_vault, seed_due_item


@pytest.fixture()
def ctx(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    context = SidecarContext()
    context.load(paths.root)
    return context


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_measurement_health_exposes_stage_zero_through_five_producers(ctx):
    result = _call(ctx, "get_measurement_health", {})

    assert result["version"] == 1
    assert {
        "scoreboard",
        "reachability",
        "inferencePrecheck",
        "coldProbes",
        "missingVocabulary",
        "causalHealth",
        "personaGate",
        "facetMintGate",
        "integrationBackfill",
        "causalProbeReview",
    } <= set(result)
    assert len(result["scoreboard"]["metrics"]) == 15
    assert result["reachability"]["summary"]["cellCount"] >= 0
    assert result["reachability"]["summary"]["learningObjectsTotal"] >= 1
    assert result["inferencePrecheck"]["summary"]["capabilityDominance"]["cellsConverted"] >= 0
    assert result["inferencePrecheck"]["summary"]["prerequisiteEntailment"]["cellsConverted"] >= 0
    assert result["inferencePrecheck"]["summary"]["combined"]["cellsConverted"] >= 0
    assert "certificatesUnscheduled" in result["coldProbes"]["coverage"]
    assert result["personaGate"]["availability"] in {
        "available",
        "no_data",
        "no_producer",
        "unmeasured",
        "requires_replay",
    }
    assert result["facetMintGate"]["originalSpecComplete"] is False
    assert result["facetMintGate"]["implementationStatus"] == "structural_proxy"


def test_cold_probe_scheduler_is_available_through_the_sidecar(ctx):
    result = _call(
        ctx,
        "schedule_certification_cold_probes",
        {"learningObjectId": None},
    )

    assert result["version"] == 1
    assert "counts" in result["schedule"]
    assert "decisions" in result["schedule"]


def test_causal_probe_review_transition_returns_a_typed_sidecar_error(ctx):
    with pytest.raises(SidecarError) as exc:
        _call(
            ctx,
            "transition_causal_probe_candidate",
            {
                "candidateId": "cpc_missing",
                "toStatus": "registered",
                "reviewer": None,
                "reason": None,
            },
        )

    assert exc.value.code == "invalid_causal_probe_transition"


def test_integration_backfill_requires_explicit_confirmation(ctx):
    with pytest.raises(SidecarError) as exc:
        _call(ctx, "apply_integration_backfill", {"confirm": False})

    assert exc.value.code == "confirmation_required"


def test_confirmed_empty_integration_backfill_is_safe_and_reloadable(ctx):
    result = _call(ctx, "apply_integration_backfill", {"confirm": True})

    assert result["version"] == 1
    assert result["applied"]["edits"] == []
    assert result["integrationBackfill"]["summary"]["integrationComponentCount"] == 0


# -- Wave-2 visibility: the commissioning trigger and the nav badge counts ------


def _commissioning_ctx(tmp_path):
    """A context whose commissioning queue has one authorable cell.

    ``background=False`` re-binds the job manager so ``enqueue_practice_expansion``
    persists the job and stops. That is the whole point of testing an enqueue
    handler: the model-backed authoring lives in the runner, so the handler is
    exercised end to end without a provider ever being constructed -- no fake
    client is needed because no client is reachable from this code path.
    """

    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    from tests.helpers import create_basic_vault
    from tests.test_contract_commissioning import _write_blueprint

    paths = create_basic_vault(tmp_path / "vault")
    _write_blueprint(paths, [("uninstrumented_facet", "procedure_execution", "hard")])
    context = SidecarContext()
    context.load(paths.root)
    context.ingest_jobs.bind(context.repository, context.vault_root, background=False)
    return context, paths


def test_generate_commissioning_practice_enqueues_the_whole_queue(tmp_path):
    ctx, _paths = _commissioning_ctx(tmp_path)

    result = _call(ctx, "generate_commissioning_practice", {})

    assert result["batchId"] is not None
    # The default path targets the commissioning queue, not whatever the panel
    # happened to render.
    assert result["learningObjectIds"] == ["lo_svd_definition"]
    assert result["commissionableCellCount"] >= 1
    _vault, repository = ctx.require_vault()
    jobs = repository.ingest_jobs_for_batch(result["batchId"])
    assert len(jobs) == 1
    assert jobs[0]["payload"]["learning_object_ids"] == ["lo_svd_definition"]
    assert jobs[0]["payload"]["reason"] == "commissioning_queue_gap"


def test_generate_commissioning_practice_treats_an_empty_queue_as_success(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    from tests.helpers import create_basic_vault

    # No blueprints => no contract cells => nothing to commission. A surface that
    # raised here would report the good outcome as a failure.
    paths = create_basic_vault(tmp_path / "vault")
    context = SidecarContext()
    context.load(paths.root)
    context.ingest_jobs.bind(context.repository, context.vault_root, background=False)

    result = _call(context, "generate_commissioning_practice", {})

    assert result["batchId"] is None
    assert result["learningObjectIds"] == []
    assert result["commissionableCellCount"] == 0


def test_generate_commissioning_practice_rejects_unknown_learning_objects(tmp_path):
    ctx, _paths = _commissioning_ctx(tmp_path)

    with pytest.raises(SidecarError) as excinfo:
        _call(ctx, "generate_commissioning_practice", {"learningObjectIds": ["lo_nope"]})

    assert excinfo.value.code == "not_found"


def test_generate_commissioning_practice_limit_takes_the_queue_head(tmp_path):
    ctx, _paths = _commissioning_ctx(tmp_path)

    result = _call(ctx, "generate_commissioning_practice", {"limit": 1})

    assert len(result["learningObjectIds"]) == 1


def test_review_counts_start_empty_and_follow_the_maintain_queues(ctx):
    counts = _call(ctx, "get_review_counts", {})

    assert counts["proposalsBadge"] == 0
    assert counts["maintainBadge"] == 0
    for key in (
        "pendingProposals",
        "unreviewedProbeCandidates",
        "openSourceConflicts",
        "actionNeededNotices",
        "pendingClarifications",
    ):
        assert counts[key] == 0

    _vault, repository = ctx.require_vault()
    repository.upsert_maintenance_notice(
        notice_type="stale_source",
        dedup_key="src1",
        title="A source revision drifted.",
        action={"action": "refresh_revision"},
        aging_policy="auto_resolution",
        severity="action_needed",
    )
    # An info-severity notice is live but not action_needed: the badge counts what
    # is waiting on the learner, not everything the feed holds.
    repository.upsert_maintenance_notice(
        notice_type="stale_source",
        dedup_key="src2",
        title="Informational only.",
        action={"action": "refresh_revision"},
        aging_policy="auto_resolution",
        severity="info",
    )

    refreshed = _call(ctx, "get_review_counts", {})
    assert refreshed["actionNeededNotices"] == 1
    assert refreshed["maintainBadge"] == 1
    # Maintain and Proposals count disjoint queues, so one never inflates the other.
    assert refreshed["proposalsBadge"] == 0
