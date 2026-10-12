import pytest

from learnloop_mobile.allowlist import ALLOWLIST, validate_envelope


def test_m1_allowlist_is_empty_and_frozen():
    assert not ALLOWLIST
    with pytest.raises(TypeError):
        ALLOWLIST["run_cli_command"] = object()


@pytest.mark.parametrize("value", [
    [], None, {"method": 1}, {"method": ""}, {"method": "x", "params": []},
    {"method": "x", "request_id": None}, {"method": "x", "request_id": ""},
    {"method": "x", "jsonrpc": "2.0"}, {"method": "x", "path": "/vault"},
])
def test_envelope_rejects_batches_unknown_fields_and_bad_types(value):
    with pytest.raises(ValueError):
        validate_envelope(value)


def test_all_registered_methods_are_denied():
    from learnloop_sidecar import handlers  # noqa: F401 — populates the registry
    from learnloop_sidecar.registry import METHOD_REGISTRY
    assert METHOD_REGISTRY
    for method in METHOD_REGISTRY:
        assert validate_envelope({"method": method, "params": {}})["method"] not in ALLOWLIST


# Desktop-only capture RPCs (mobile M1) and the sidecar RPCs main gained before
# the mobile merge: daily loop (Today start summary), Slice 1 M2 diagnosis card,
# Phase 5b practice index. Pinned by name so a registry rename cannot make the
# blanket test above vacuous for them.
DESKTOP_ONLY_CAPTURE_RPCS = ("resume_capture_route", "get_capture_media")
MAIN_SIDECAR_RPCS = (
    "get_start_summary",
    "diagnosis_status",
    "record_diagnosis_feedback",
    "find_practice",
    "record_practice_usage",
    "get_practice_coverage",
)


@pytest.mark.parametrize("method", DESKTOP_ONLY_CAPTURE_RPCS + MAIN_SIDECAR_RPCS)
def test_desktop_and_main_rpcs_are_registered_but_never_phone_allowed(method):
    from learnloop_sidecar import handlers  # noqa: F401 — populates the registry
    from learnloop_sidecar.registry import METHOD_REGISTRY
    assert method in METHOD_REGISTRY
    assert method not in ALLOWLIST
