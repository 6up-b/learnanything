"""RW1c's kill switches restore today's Reader tutor byte for byte (spec §4.6, §12).

With ``reader_tutor.retrieval_enabled`` and ``reader_tutor.offers_enabled``
both off, the Reader's Ask is the selection-and-neighbours tutor of before
RW1c: the tutor's prompt, its result model, the ``reader.ask`` response, the
stored question and exchange, ``reader.ask_history`` and the prompt contract
are exactly what the base tree (``fab576ac1``) produced. The golden file was
recorded on that tree, before any RW1c code existed
(``RW1C_WRITE_GOLDEN=1 uv run pytest tests/test_reader_tutor_switch_off.py``
wrote it there); ULIDs are replaced by their order of appearance.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

from tests.library_ask_fixtures import build_library_vault, call, context, set_config
from tests.source_service_fakes import tool_tutor

GOLDEN = Path(__file__).parent / "fixtures" / "reader_tutor_switch_off.json"
WRITE = os.environ.get("RW1C_WRITE_GOLDEN") == "1"
_ULID = re.compile(r"[0-9A-HJKMNP-TV-Z]{26}")


def _normalized(value: Any) -> Any:
    """``value`` with every ULID replaced by its order of appearance."""

    text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    seen: dict[str, str] = {}

    def swap(match: re.Match[str]) -> str:
        return seen.setdefault(match.group(0), f"<ULID{len(seen)}>")

    return json.loads(_ULID.sub(swap, text))


def _without(value: Any, keys: set[str]) -> Any:
    if isinstance(value, dict):
        return {key: _without(item, keys) for key, item in value.items() if key not in keys}
    if isinstance(value, list):
        return [_without(item, keys) for item in value]
    return value


def _record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, offers: bool = False) -> dict[str, Any]:
    import learnloop_sidecar.handlers.reader as reader_handler

    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    if not WRITE:
        # Recorded on the base tree, which has no [reader_tutor] section.
        set_config(paths, "reader_tutor", retrieval_enabled=False, offers_enabled=offers)
        # RW7a (landed after this golden was recorded): off, so its contract key
        # and Orient's "what matters here?" are absent; these pins are RW1c's.
        set_config(paths, "reading_paths", enabled=False)
    ctx = context(paths.root)
    tutor = tool_tutor(answer_md="The determinant vanishes there, so t is a root.")

    class Ready:
        ready = True

    monkeypatch.setattr(reader_handler, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    root = call(ctx, "reader.ask", {
        "extractionId": "ext_text", "spanId": "t2", "question": "why is an eigenvalue a root?",
        "selectionSpanIds": ["t2"], "selectionQuote": "the roots of the characteristic polynomial",
    })
    follow = call(ctx, "reader.ask", {
        "extractionId": "ext_text", "spanId": "t2", "question": "and for a diagonal matrix?",
        "parentExchangeId": root["readerAnswerEventId"],
    })
    history = call(ctx, "reader.ask_history", {"extractionId": "ext_text"})
    contract = call(ctx, "reader.prompt_contract", {})
    if not WRITE:
        # RW4b (landed onto main after this golden was recorded on the base
        # tree) adds its own key at its defaults; these pins are about RW1c's
        # switches, so everything else stays byte for byte (RW4b landing).
        assert contract.pop("libraryExercises") == {"fallback": False}
        # RW4d (after this golden too): its own key at its defaults (the tutor's comparison can be kept).
        assert contract.pop("compareKeep") == {"library": True, "tutor": True, "perspectives": True,
                                               "maxPerspectives": 4}
    events = [
        {"kind": event["kind"], "payload": event.get("payload")}
        for kind in ("reader_answer_submitted", "learner_question_asked", "reader_answer_mode_set")
        for event in repository.reader_interaction_events(kind=kind)
    ]
    questions = [
        {key: row.get(key) for key in ("context", "note_id", "question_md", "answer_md", "answer_status",
                                       "answer_mode", "source_context", "facets", "hint_equivalent")}
        for row in repository.question_events(context="reader")
    ]
    return _normalized(_without({
        "prompts": tutor.prompts, "result_models": tutor.result_models,
        "root": root, "follow": follow, "history": history, "contract": contract,
        "events": events, "questions": questions,
    }, {"createdAt", "created_at", "answered_at"}))


def test_both_switches_off_is_the_base_tutor_byte_for_byte(tmp_path, monkeypatch):
    recorded = _record(tmp_path, monkeypatch)
    if WRITE:
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(recorded, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                          encoding="utf-8")
        pytest.skip("golden written")
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for key in golden:
        assert recorded[key] == golden[key], key
    assert recorded == golden


def test_retrieval_off_keeps_the_base_tutor_and_offers_only_add_their_buttons(tmp_path, monkeypatch):
    """Retrieval off, offers on: the tutor's prompt, rows and history are the
    base's; the answers only gain ``tutorOffers`` and the contract ``readerTutor``."""

    if WRITE:
        pytest.skip("the golden is written by the switch-off case")
    recorded = _record(tmp_path, monkeypatch, offers=True)
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for key in ("prompts", "result_models", "history", "events", "questions"):
        assert recorded[key] == golden[key], key
    for key in ("root", "follow"):
        assert recorded[key].pop("tutorOffers") == {"buttons": []}
        assert recorded[key] == golden[key], key
    tutor = recorded["contract"].pop("readerTutor")
    assert tutor["offers"] is True and tutor["retrieval"] is False and tutor["anotherWay"] is False
    assert recorded["contract"] == golden["contract"]
