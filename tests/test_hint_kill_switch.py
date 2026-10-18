"""Adaptive hints H2a: kill switches and cold/probe parity (spec_adaptive_hints_v1 H9; G-H1, G-H14).

With ``hints.adaptive_enabled = false`` (or ``hints.telemetry_enabled =
false``, whose rows the hints need) ``practice.request_hint`` answers
``disabled`` with no row and no model call, and the practice RPCs and every
table are byte-identical to a vault where it was never called; with no UI
calling it the screen's RPCs are the same in either state. During a
diagnostic block no request reaches a model. Fakes only.
"""

from __future__ import annotations

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
import learnloop_sidecar.handlers.practice as practice
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.hint_fakes import ChooserFake, WriterFake, assists
from tests.test_hint_telemetry import ITEM, _call, _dump, _scenario, _scrub, _vault, frozen  # noqa: F401

ADAPTIVE_OFF = "[hints]\nadaptive_enabled = false\n"


def _ask(ctx, session_id, *, key: str = "k1"):
    return _call(ctx, "practice.request_hint", {"sessionId": session_id, "practiceItemId": ITEM,
                                                "submissionId": key, "answerMd": "U, Sigma"})


def test_adaptive_off_answers_disabled_writes_nothing_and_asks_nobody(tmp_path):
    for config in (ADAPTIVE_OFF, "[hints]\ntelemetry_enabled = false\n"):
        paths = _vault(tmp_path, name=f"v{len(config)}", config=config)
        ctx = SidecarContext()
        ctx.load(paths.root)
        writer, chooser = WriterFake(), ChooserFake()
        ctx.hint_writer_client, ctx.hint_chooser_client, ctx.hints_inline = writer, chooser, True
        session_id = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
        job = _ask(ctx, session_id)
        assert (job["state"], job["jobId"], job["result"]["status"]) == ("done", None, "disabled")
        answer = _call(ctx, "practice.answer_discriminating", {
            "sessionId": session_id, "practiceItemId": ITEM, "submissionId": "k1", "questionAssistId": "ha_x",
            "answerMd": "0"})
        assert answer["recorded"] is False
        assert writer.calls == 0 and chooser.calls == [] and assists(paths.sqlite_path) == []


def _scenario_with_disabled_request(root, monkeypatch):
    responses = _scenario(root, monkeypatch)
    return responses


def test_the_practice_rpcs_and_tables_are_identical_with_adaptive_hints_on_or_off(tmp_path, frozen, monkeypatch):
    on = _vault(tmp_path, name="on")
    off = _vault(tmp_path, name="off", config=ADAPTIVE_OFF)
    _scenario(_vault(tmp_path, name="warm").root, monkeypatch)
    on_responses = _scenario(on.root, monkeypatch)
    off_responses = _scenario(off.root, monkeypatch)
    assert on_responses == off_responses
    on_dump, off_dump = _dump(on.sqlite_path), _dump(off.sqlite_path)
    assert {table for table in on_dump if on_dump[table] != off_dump[table]} == set()
    on_rows = [_scrub(row, on.root) for row in assists(on.sqlite_path)]
    off_rows = [_scrub(row, off.root) for row in assists(off.sqlite_path)]
    assert on_rows == off_rows  # H0's authored reveals only: the service wrote nothing in either


def test_a_disabled_request_leaves_the_vault_exactly_as_if_never_made(tmp_path, frozen, monkeypatch):
    import hashlib

    paths = _vault(tmp_path, config=ADAPTIVE_OFF)
    ctx = SidecarContext()
    ctx.load(paths.root)
    session_id = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    before = _dump(paths.sqlite_path)
    digest = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    _ask(ctx, session_id)
    assert _dump(paths.sqlite_path) == before
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == digest


def test_no_hint_request_reaches_a_model_during_a_diagnostic_block(tmp_path, monkeypatch):
    paths = _vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    writer, chooser = WriterFake(), ChooserFake()
    ctx.hint_writer_client, ctx.hint_chooser_client, ctx.hints_inline = writer, chooser, True
    session_id = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    monkeypatch.setattr(practice, "_in_diagnostic_block", lambda repository, item: True)
    job = _ask(ctx, session_id)
    assert (job["result"]["status"], job["result"]["reason"]) == ("refused", "diagnostic_block")
    assert writer.calls == 0 and chooser.calls == [] and assists(paths.sqlite_path) == []


def test_the_served_item_and_its_cold_check_fields_are_unchanged_by_the_switch(tmp_path, frozen, monkeypatch):
    def serve(root):
        ctx = SidecarContext()
        ctx.load(root)
        session_id = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
        return _scrub(_call(ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id}), root)

    from tests.test_hint_telemetry import _deterministic_ids

    _deterministic_ids(monkeypatch)
    on = serve(_vault(tmp_path, name="on").root)
    _deterministic_ids(monkeypatch)
    off = serve(_vault(tmp_path, name="off", config=ADAPTIVE_OFF).root)
    assert on == off
    assert METHOD_REGISTRY["practice.request_hint"] is not None


# -- H2b: the app snapshot's switch and the help-style write ---------------------------


def _config_dto(root):
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.context import config_dto

    return config_dto(load_vault(root))


def test_h2b_the_snapshot_names_the_panel_only_while_adaptive_hints_are_on(tmp_path):
    """G-H1: the screen reads a ``hints`` key the sidecar sends only while
    adaptive hints are on (and the telemetry their rows need); off, the app
    snapshot's config is exactly what it was before H2b."""

    on = _config_dto(_vault(tmp_path, name="on").root)
    off = _config_dto(_vault(tmp_path, name="off", config=ADAPTIVE_OFF).root)
    telemetry_off = _config_dto(_vault(tmp_path, name="t", config="[hints]\ntelemetry_enabled = false\n").root)
    assert on["hints"] == {"adaptiveEnabled": True, "authoredOfferAfterSeconds": 4.0, "helpStyle": "balanced"}
    assert "hints" not in off and "hints" not in telemetry_off
    assert {key: value for key, value in on.items() if key != "hints"} == off == telemetry_off


def test_h2b_the_app_snapshot_through_the_sidecar_carries_no_hints_key_when_off(tmp_path):
    paths = _vault(tmp_path, config=ADAPTIVE_OFF)
    ctx = SidecarContext()
    ctx.load(paths.root)
    # What load_vault answers (``ctx.app_snapshot``), as the app reads it.
    snapshot = METHOD_REGISTRY["load_vault"].handler(ctx, None)
    assert "hints" not in snapshot["config"]
    paths_on = _vault(tmp_path, name="on")
    ctx_on = SidecarContext()
    ctx_on.load(paths_on.root)
    assert METHOD_REGISTRY["load_vault"].handler(ctx_on, None)["config"]["hints"]["adaptiveEnabled"] is True


def test_h2b_set_help_style_writes_the_one_stored_preference_and_reloads(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    paths = _vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    toml = paths.root / "learnloop.toml"
    answer = _call(ctx, "practice.set_help_style", {"helpStyle": "guide_me"})
    assert answer["helpStyle"] == "guide_me"
    vault, _repository = ctx.require_vault()
    assert vault.config.hints.help_style == "guide_me"
    assert 'help_style = "guide_me"' in toml.read_text()
    # The same style again writes nothing.
    before = toml.read_bytes()
    assert _call(ctx, "practice.set_help_style", {"helpStyle": "guide_me"})["helpStyle"] == "guide_me"
    assert toml.read_bytes() == before
    # The chooser reads it per request (the state's help style).
    from learnloop.db.repositories import Repository
    from learnloop.hints.state import assemble_state

    item = vault.practice_items[ITEM]
    state = assemble_state(vault, Repository.attach(paths.sqlite_path), item, session_id="s", submission_id="k",
                           work_md="", seconds_on_item=None, now_iso="2026-10-18T09:00:00Z")
    assert state.help_style == "guide_me"
    import pytest
    from pydantic import ValidationError

    with pytest.raises((ValidationError, SidecarError)):
        _call(ctx, "practice.set_help_style", {"helpStyle": "lazy"})
