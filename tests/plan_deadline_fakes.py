"""Deterministic SSE bytes through the real reader and timer, without a socket."""
from collections import deque
import json
from types import SimpleNamespace

from learnloop.ai.chatgpt_plan import responses
from learnloop.ai.providers import chatgpt_plan


class Clock:
    def __init__(self):
        self.now = 0.0
        self.timers = []

    def monotonic(self):
        return self.now

    def advance(self, until):
        while pending := [t for t in self.timers if t.active and t.at <= until]:
            timer = min(pending, key=lambda t: t.at)
            self.now = timer.at
            timer.active = False
            timer.function(*timer.args)
        self.now = until

    def Timer(self, interval, function, args=()):
        clock = self

        class Timer:
            active = False
            at = clock.now + interval

            def start(self):
                self.active = True
                clock.timers.append(self)

            def cancel(self):
                self.active = False

        timer = Timer()
        timer.function, timer.args = function, args
        return timer


class Session:
    def check_usable(self, **kwargs):
        return None

    def access_token(self, **kwargs):
        return "fake-token"

    def note_success(self, pause):
        pass


def install_stream(monkeypatch, events, *, interrupt_at=None, detach_socket=False):
    clock = Clock()
    requests = []
    connections = []

    class Connection:
        def __init__(self, *args, **kwargs):
            self.sock = self
            self.closed = False
            self.shutdown_at = None
            self.lines = deque()
            connections.append(self)
            start = clock.now
            request_events = events(len(connections)) if callable(events) else events
            for at, event in request_events:
                if event is None:
                    self.lines.append((start + at, b""))
                    continue
                self.lines.append((start + at, b"data: " + json.dumps(event).encode() + b"\n"))
                self.lines.append((start + at, b"\n"))

        def request(self, method, path, *, body, headers):
            requests.append(json.loads(body))

        def getresponse(self):
            if detach_socket:
                self.sock = None
            return SimpleNamespace(status=200, headers={"x-request-id": "fake-request"},
                                   readline=self.readline, close=lambda: None)

        def readline(self):
            at, line = self.lines.popleft() if self.lines else (clock.now + 2000, b"")
            clock.advance(at)
            if interrupt_at is not None:
                interrupt_at(clock.now)
            if self.closed:
                raise OSError("closed")
            return line

        def shutdown(self, _how):
            self.shutdown_at = clock.now
            self.closed = True

        def close(self):
            self.closed = True

    monkeypatch.setattr(responses, "time", clock)
    monkeypatch.setattr(responses.threading, "Timer", clock.Timer)
    monkeypatch.setattr(responses.http.client, "HTTPConnection", Connection)
    monkeypatch.setattr(chatgpt_plan, "_monotonic", clock.monotonic)
    return clock, requests, connections


def delta(text="x", kind="response.output_text.delta"):
    return {"type": kind, "delta": text}


def completed():
    return {"type": "response.completed", "response": {
        "status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": '{"ok": true}'}]}],
        "usage": {"input_tokens": 10, "output_tokens": 20}}}
