"""Process-boundary behavior for the NDJSON sidecar server."""

from __future__ import annotations

import io
import json
from typing import Any

import pytest

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams
from learnloop_sidecar.registry import METHOD_REGISTRY, MethodSpec, method
from learnloop_sidecar.server import _handle, _write, serve


def _serve(*messages: Any) -> list[dict[str, Any]]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def test_non_string_method_is_rejected_without_crashing_the_server() -> None:
    responses = _serve(
        {"jsonrpc": "2.0", "id": 1, "method": ["not", "hashable"]},
        {"jsonrpc": "2.0", "id": 2, "method": "rpc.ping"},
    )

    assert responses[0]["error"]["data"]["code"] == "invalid_request"
    assert responses[1]["result"]["ready"] is True


def test_params_must_be_an_object_and_validation_does_not_echo_input() -> None:
    secret = "sk-do-not-return-this"
    responses = _serve(
        {"jsonrpc": "2.0", "id": 1, "method": "rpc.ping", "params": []},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "rpc.ping",
            "params": {"apiKey": secret},
        },
    )

    for response in responses:
        assert response["error"]["data"]["code"] == "validation_error"
        assert secret not in json.dumps(response)
        for error in response["error"]["data"]["details"]["errors"]:
            assert set(error) == {"location", "message", "type"}


def test_unexpected_handler_failure_marks_the_commit_outcome_unknown(monkeypatch) -> None:
    def fail(_ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]:
        raise RuntimeError("private implementation detail")

    monkeypatch.setitem(
        METHOD_REGISTRY,
        "test.failure",
        MethodSpec("test.failure", EmptyParams, fail),
    )

    response = _handle(
        SidecarContext(),
        {"jsonrpc": "2.0", "id": 7, "method": "test.failure"},
    )

    assert response is not None
    error = response["error"]
    assert error["data"] == {
        "code": "internal",
        "retryable": False,
        "details": {"method": "test.failure", "outcome": "unknown"},
    }
    assert "Check the current state" in error["message"]
    assert "private implementation detail" not in json.dumps(response)


def test_non_serializable_handler_result_becomes_a_protocol_error_response() -> None:
    stdout = io.StringIO()

    _write(stdout, {"jsonrpc": "2.0", "id": 9, "result": {"bad": {1, 2}}})

    response = json.loads(stdout.getvalue())
    assert response["id"] == 9
    assert response["error"]["data"]["code"] == "internal"
    assert response["error"]["data"]["retryable"] is False
    assert response["error"]["data"]["details"]["phase"] == "serialize_response"
    assert response["error"]["data"]["details"]["outcome"] == "unknown"


def test_duplicate_method_registration_fails_loudly() -> None:
    name = "test.duplicate-registration"

    def first(_ctx: SidecarContext, _params: EmptyParams) -> None:
        return None

    def replacement(_ctx: SidecarContext, _params: EmptyParams) -> None:
        return None

    method(name)(first)
    try:
        with pytest.raises(RuntimeError, match="Duplicate sidecar method"):
            method(name)(replacement)
        assert METHOD_REGISTRY[name].handler is first
    finally:
        METHOD_REGISTRY.pop(name, None)
