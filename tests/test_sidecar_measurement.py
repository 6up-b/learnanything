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
