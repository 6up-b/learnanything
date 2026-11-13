"""K1-9: a damaged source_sets.yaml reaches the learner as one typed, actionable refusal on every door.

Every exam-material reader raises ``SourceSetsUnreadable`` (K1-1). Each adapter turns it into the same
refusal in one place: the sidecar's request handler (which the phone host's ``/rpc`` also goes through),
and the MCP tool wrapper. The message names the file, says why work stopped and names ``learnloop doctor``;
it carries nothing of the file."""

from __future__ import annotations

import pytest

pytest.importorskip("starlette")
from starlette.testclient import TestClient

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.content.sources import exam_material as EM
from learnloop_mobile.host import create_app
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.server import _handle
from tests.helpers import create_basic_vault
from tests.mobile_host_helpers import HOSTNAME, Phone, config_for, pair, seeded_vault

#: Text a damaged file might contain; it must never come back in a message.
SECRET = "learner-private-text-in-the-file"
DAMAGED = f"source_sets:\n  - id: sset\n    note: {SECRET}\n    members: not-a-list\n"


def _three_parts(message: str) -> None:
    assert "sources/source_sets.yaml" in message
    assert "can't tell protected exam material from teaching material" in message
    assert "learnloop doctor" in message
    assert SECRET not in message


def _damage(paths) -> None:
    paths.source_sets_path.parent.mkdir(parents=True, exist_ok=True)
    paths.source_sets_path.write_text(DAMAGED, encoding="utf-8")


def test_the_message_names_the_file_the_cause_and_the_fix():
    _three_parts(EM.SOURCE_SETS_UNREADABLE_MESSAGE)
    assert str(EM.SourceSetsUnreadable(["the file said " + SECRET])) == EM.SOURCE_SETS_UNREADABLE_MESSAGE


def test_the_sidecar_answers_a_typed_error_where_exam_material_is_read(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    paths = create_basic_vault(tmp_path / "vault")
    _damage(paths)
    ctx = SidecarContext()
    ctx.load(paths.root, maintenance=False)

    def rpc(method, params=None):
        return _handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})

    session = rpc("start_session", {"energy": "medium"})["result"]["sessionId"]
    for method, params in (("get_today_queue", {"sessionId": session}), ("get_daily_plan", {}),
                           ("get_practice_item", {"practiceItemId": "pi_svd_define_001", "sessionId": session})):
        error = rpc(method, params)["error"]
        assert error["data"]["code"] == "source_sets_unreadable", method
        assert error["data"]["retryable"] is False
        _three_parts(error["message"])


def test_a_method_that_reads_no_exam_material_is_unaffected(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    paths = create_basic_vault(tmp_path / "vault")
    _damage(paths)
    ctx = SidecarContext()
    ctx.load(paths.root, maintenance=False)
    assert "result" in _handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": "get_today_headline", "params": {}})


def test_the_phone_host_answers_the_same_typed_error(tmp_path):
    paths, repository = seeded_vault(tmp_path / "vault")
    _damage(paths)
    device = pair(repository)
    with TestClient(create_app(config_for(paths.root)), base_url=f"https://{HOSTNAME}") as client:
        phone = Phone(client, device)
        session = phone.start()["sessionId"]
        status, error = phone.error("get_today_queue", {"sessionId": session})
    assert error["code"] == "source_sets_unreadable"
    assert status >= 400
    _three_parts(error["message"])
    assert error["retryable"] is False


def test_the_chat_host_gets_the_same_code_and_message(tmp_path, monkeypatch):
    """The MCP tools already refuse before exam material is read (protection_unreadable); a reader that
    still raises reaches the host as the same typed refusal, not "failed"."""

    import anyio
    from mcp import Client

    from learnloop_mcp import server as mcp_server
    from learnloop.remote.runtime import RemoteRuntime
    from learnloop_mcp.server import build_server
    from tests.source_retrieval_fakes import build_retrieval_vault

    paths, _repository = build_retrieval_vault(tmp_path / "vault", embeddings=False)

    def raises(*args, **kwargs):
        raise EM.SourceSetsUnreadable(["yaml:invalid"])

    monkeypatch.setattr(mcp_server, "find_passages", raises)
    server = build_server(RemoteRuntime.attach(paths.root, load_environment=False))

    async def call():
        async with Client(server) as client:
            return await client.call_tool("find_sources", {"query": "eigenvalues", "intent": "explain"})

    result = anyio.run(call)
    text = "".join(getattr(c, "text", "") for c in result.content)
    assert result.is_error
    _three_parts(text)


@pytest.mark.parametrize("text", [DAMAGED, "source_sets:\n  - id: s\n    members: [{source_id: a\n", ""],
                         ids=["schema_invalid", "unparseable", "empty"])
def test_doctor_names_a_damaged_source_sets_file(tmp_path, monkeypatch, text):
    from learnloop.ops.doctor import run_doctor

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    paths = create_basic_vault(tmp_path / "vault")
    paths.source_sets_path.parent.mkdir(parents=True, exist_ok=True)
    paths.source_sets_path.write_text(text, encoding="utf-8")
    report = run_doctor(paths.root)
    named = [issue for issue in report.issues if "source_sets.yaml" in (issue.message + str(issue.path))]
    assert named and all(issue.severity == "error" for issue in named)
