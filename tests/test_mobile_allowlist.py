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
