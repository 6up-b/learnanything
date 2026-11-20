"""The socket wakeup half of the deadline contract; only a local fake server."""
import threading
import time

import pytest

from learnloop.ai.chatgpt_plan.responses import ResponsesStream
from learnloop.ai.errors import AIInterrupted, AITurnTimeout
from learnloop.ai.execution import background_model_work, single_request
from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient
from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import execute_structured_operation
from learnloop.config.schema import ChatGPTPlanProviderConfig
from tests.chatgpt_plan_fakes import Reply, fake_chatgpt, run_in_thread
from tests.plan_deadline_fakes import Session, completed, delta


class Answer(WireModel):
    ok: bool


@pytest.mark.parametrize("stop", ["idle", "interrupt"])
def test_background_blocked_read_wakes_on_idle_or_interrupt(monkeypatch, stop):
    reached = threading.Event()
    original_read = ResponsesStream._read_stream

    def read(stream, response, **kwargs):
        observe = kwargs["on_event"]

        def on_event(kind, event):
            observe(kind, event)
            if kind == "response.output_text.delta":
                reached.set()

        return original_read(stream, response, **{**kwargs, "on_event": on_event})

    monkeypatch.setattr(ResponsesStream, "_read_stream", read)
    with fake_chatgpt() as server:
        server.access_tokens.add("fake-token")
        server.replies.append(Reply(events=[delta(), completed()], stall=10))
        transport = ChatGPTPlanProviderClient("plan", ChatGPTPlanProviderConfig(
            model="fake", base_url=server.base_url, timeout_seconds=180), session=Session(),
            idle_timeout_seconds=0.5 if stop == "idle" else 10)

        def ask():
            with background_model_work(), single_request():
                return execute_structured_operation(transport, purpose="probe", prompt="unchanged",
                                                    result_model=Answer, timeout_seconds=0.1)

        thread, out = run_in_thread(ask)
        try:
            assert reached.wait(2)
            # The old total limit passes while the real socket is blocked.
            time.sleep(0.2)
            assert thread.is_alive()
            if stop == "interrupt":
                transport.interrupt()
            thread.join(1.5)
            assert not thread.is_alive()
            expected = AIInterrupted if stop == "interrupt" else AITurnTimeout
            assert isinstance(out.get("error"), expected), out
            if stop == "idle":
                assert out["error"].reason == "idle"
            assert len(server.requests) == 1
        finally:
            transport.interrupt()
            thread.join(2)
