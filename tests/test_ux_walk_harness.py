"""The UX walk harness's plain logic (scripts/ux_walk/; docs/reviews/ux-walk-harness.md).

No browser here: the command table against the Rust shell's source, the
observation's text rendering on small static pages, the file protocol's order
and timeouts, the fake model's answers and the bridge's helpers. The one test
that drives Chromium is marked ``ux_walk_browser`` and runs only when
``LEARNLOOP_UX_WALK_BROWSER=1``, so neither gate starts a browser.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WALK = ROOT / "scripts" / "ux_walk"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"ux_walk_{name}", WALK / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


commands = _load("walk_commands")
perceive = _load("walk_perceive")
protocol = _load("walk_protocol")
client = _load("walk_client")
fake = _load("fake_model")


# -- the command table ---------------------------------------------------------------------------


def test_every_registered_command_has_a_classified_route():
    table = commands.load_table()
    registered = commands.registered_commands(commands.MAIN_RS.read_text(encoding="utf-8"))
    assert list(table) == registered
    assert {command.kind for command in table.values()} <= {"passthrough", "forward", "special"}
    assert {name for name, command in table.items() if command.kind == "special"} == set(commands.SPECIAL_COMMANDS)
    assert table["load_vault"].watches_vault and table["select_vault"].watches_vault


def test_every_command_the_frontend_calls_is_in_the_table():
    source = (ROOT / "apps" / "learnloop-tauri" / "src" / "api" / "client.ts").read_text(encoding="utf-8")
    called = set(re.findall(r'\bcall(?:<[^\n]*?>)?\(\s*"([a-z0-9_]+)"', source))
    assert len(called) > 300
    assert called - set(commands.load_table()) == set()


def test_forward_arguments_follow_the_rust_signature():
    table = commands.load_table()
    feedback = table["get_feedback"]
    assert feedback.params_for({"attemptId": "a1"}) == {"attemptId": "a1", "recordOpen": True}
    assert feedback.params_for({"attemptId": "a1", "recordOpen": False}) == {"attemptId": "a1", "recordOpen": False}
    item = table["get_practice_item"].params_for({"practiceItemId": "p"})
    assert item == {"practiceItemId": "p", "sessionId": None, "proposalId": None, "sourceExerciseImportId": None}
    with pytest.raises(commands.MissingArgument, match="missing required key sessionId"):
        table["get_session"].params_for({})
    assert table["reader_ask"].method == "reader.ask"
    assert table["reader_ask"].params_for({"input": {"q": 1}}) == {"q": 1}
    with pytest.raises(commands.MissingArgument):
        table["reader_ask"].params_for({})


def test_a_command_whose_body_is_not_a_plain_forward_stops_the_bridge(tmp_path):
    rust = commands.COMMANDS_RS.read_text(encoding="utf-8") + '''
#[tauri::command]
pub async fn open_in_finder(
    path: String,
    sidecar: State<'_, SidecarManager>,
) -> Result<Value, CommandError> {
    reveal(&path)?;
    blocking_sidecar_call(sidecar, "note_reveal", json!({"path": path})).await
}
'''
    main = commands.MAIN_RS.read_text(encoding="utf-8").replace("reader_pause_arc\n", "reader_pause_arc,\n open_in_finder\n")
    (tmp_path / "commands.rs").write_text(rust, encoding="utf-8")
    (tmp_path / "main.rs").write_text(main, encoding="utf-8")
    assert commands.parse_commands(rust)["open_in_finder"].kind == "unknown"
    with pytest.raises(ValueError, match="open_in_finder"):
        commands.load_table(tmp_path / "commands.rs", tmp_path / "main.rs")
    plain = rust.replace("    reveal(&path)?;\n", "")
    (tmp_path / "commands.rs").write_text(plain, encoding="utf-8")
    assert commands.load_table(tmp_path / "commands.rs", tmp_path / "main.rs")["open_in_finder"].kind == "forward"
    renamed = plain.replace('json!({"path": path})', 'json!({"target": other})')
    assert commands.parse_commands(renamed)["open_in_finder"].kind == "unknown"


def test_tauri_names_arguments_in_camel_case():
    assert commands.camel("source_exercise_import_id") == "sourceExerciseImportId"
    assert commands.camel("path") == "path"


# -- the observation's text ------------------------------------------------------------------------

PAGE = """
<html><head><title>LearnLoop</title><style>.x{}</style></head><body>
<nav><button class="nav-btn" data-testid="tab-today" aria-current="page">Today</button>
<a href="#lib">Library</a></nav>
<main>
  <h1>Good morning</h1>
  <p>You have <b>3</b> questions due.</p>
  <span hidden>secret hidden text</span>
  <div style="display: none">also hidden</div>
  <ul><li>First thing</li><li>Second thing</li></ul>
  <label for="answer">Your answer</label>
  <input id="answer" type="text" value="12" data-walk-focused>
  <input id="other" type="text" placeholder="search all sources…">
  <label><input type="checkbox" checked> Quick checks</label>
  <span id="lbl">Minutes</span><select aria-labelledby="lbl"><option>25 m</option></select>
  <button disabled>Submit</button>
  <button aria-expanded="false" aria-label="More options"><svg></svg></button>
  <div role="status">Saved</div>
  <img src="x.png" alt="A diagram of two vectors">
</main>
</body></html>
"""


def _seen(html: str) -> object:
    return perceive.perceive(perceive.dump_static_html(html))


def test_the_screen_reads_in_order_with_roles_names_and_states():
    seen = _seen(PAGE)
    text = seen.text
    assert seen.title == "LearnLoop"
    order = ["Today", "Library", "# Good morning", "You have 3 questions due.", "- First thing", "- Second thing",
             'textbox "Your answer"', "Quick checks", 'combobox "Minutes"', 'button "Submit" (disabled)',
             'button "More options" (collapsed)', "Saved", "[image: A diagram of two vectors]"]
    positions = [text.index(fragment) for fragment in order]
    assert positions == sorted(positions)
    assert '[1] button "Today" (current)' in text
    assert '[2] link "Library"' in text
    assert 'textbox "Your answer" (focused) value "12"' in text
    assert 'textbox placeholder "search all sources…"' in text
    assert 'checkbox "Quick checks" (checked)' in text
    assert seen.focus == '[3] textbox "Your answer" (focused)'
    assert seen.notices == ["status: Saved"]
    numbers = [element.number for element in seen.elements]
    assert numbers == list(range(1, len(numbers) + 1))


def test_nothing_imperceptible_reaches_the_observation():
    rendered = perceive.render_observation(_seen(PAGE), header=["Step 1: look"])
    for hidden in ("secret hidden text", "also hidden", "nav-btn", "tab-today", "data-testid", "id=", "class",
                   ".x{}", "lbl", "x.png"):
        assert hidden not in rendered


def test_a_modal_dialog_is_read_first_and_named():
    html = """<html><body><h1>Behind</h1><button>Under</button>
    <div role="dialog" aria-modal="true" aria-labelledby="t"><h2 id="t">Add to your library</h2>
    <button>Choose a file…</button></div></body></html>"""
    seen = _seen(html)
    assert seen.dialogs == ['dialog "Add to your library" (modal)']
    lines = seen.text.splitlines()
    assert lines.index("--- behind the dialog ---") > lines.index('[1] button "Choose a file…"')
    assert '[2] button "Under"' in seen.text


def test_math_reads_as_its_tex_and_scrolling_is_announced():
    dump = {"title": "t", "nodes": [
        {"i": 0, "parent": -1, "tag": "body", "attrs": {}, "visible": True, "display": "block"},
        {"i": 1, "parent": 0, "tag": "p", "attrs": {}, "visible": True, "display": "block",
         "scroll": {"top": 0, "height": 900, "client": 300}},
        {"i": 2, "parent": 1, "text": "Write ", "visible": True},
        {"i": 3, "parent": 1, "tag": "span", "attrs": {}, "visible": True, "display": "inline", "math": "A=QDQ^T"},
        {"i": 4, "parent": 1, "text": "below the fold", "visible": False},
    ], "pageScroll": {"top": 0, "height": 880, "client": 880}}
    seen = perceive.perceive(dump)
    assert seen.text == "Write $A=QDQ^T$"
    assert seen.more == ["More below (scroll down)."]


def test_an_indeterminate_progress_bar_is_busy_and_a_value_is_not():
    busy = _seen('<html><body><div role="progressbar" aria-label="Loading"></div></body></html>')
    assert busy.busy == ["progress Loading"]
    reading = _seen('<html><body><div role="progressbar" aria-label="Read" aria-valuenow="40"></div></body></html>')
    assert reading.busy == [] and '[progress "Read" 40]' in reading.text


# -- the file protocol ----------------------------------------------------------------------------


def test_concurrent_steps_take_distinct_numbers_and_run_in_order(tmp_path):
    channel = tmp_path / "channel"
    numbers: list[int] = []
    lock = threading.Lock()

    def submit(index: int) -> None:
        seq = client.submit(channel, {"verb": "say", "text": str(index)})
        with lock:
            numbers.append(seq)

    threads = [threading.Thread(target=submit, args=(index,)) for index in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(numbers) == list(range(1, 13))
    done = 0
    order = []
    while (found := protocol.next_action(channel, done)) is not None:
        seq, action = found
        assert action["seq"] == seq
        order.append(seq)
        done = seq
    assert order == list(range(1, 13))
    assert not list(channel.glob(".pending-*"))


def test_a_gap_is_reported_not_skipped(tmp_path):
    channel = tmp_path / "channel"
    channel.mkdir()
    (channel / "action-0002.json").write_text(json.dumps({"verb": "look", "seq": 2}), encoding="utf-8")
    seq, action = protocol.next_action(channel, 0)
    assert seq == 2 and action["verb"] == "_malformed" and "step 1 is missing" in action["error"]


def test_a_finished_step_is_read_whole_and_a_dead_driver_is_named(tmp_path):
    channel = tmp_path / "channel"
    channel.mkdir()
    protocol.heartbeat(channel, last=0)
    assert client.driver_alive(channel)
    seq = client.submit(channel, {"verb": "look"})
    protocol.write_done(channel, seq, {"ok": True, "observation": "observations/0001.txt"})
    assert client.wait_done(channel, seq, limit=2)["observation"] == "observations/0001.txt"
    assert protocol.last_done(channel) == 1

    started = time.monotonic()
    second = client.submit(channel, {"verb": "look"})
    with pytest.raises(client.WalkError, match="No answer from the screen after 0 s"):
        client.wait_done(channel, second, limit=0.3)
    assert time.monotonic() - started < 2

    (channel / "driver.json").write_text(json.dumps({"beat": time.time() - 60}), encoding="utf-8")
    assert not client.driver_alive(channel)
    with pytest.raises(client.WalkError, match="driver is not running"):
        client.wait_done(channel, second, limit=5)


def test_the_walk_command_line():
    assert client.parse(["click", "7"]) == {"verb": "click", "target": {"number": 7}}
    assert client.parse(["click", "Start", "session"]) == {"verb": "click", "target": {"text": "Start session"}}
    assert client.parse(["click", "--role", "button", "Next"])["target"] == {"role": "button", "name": "Next"}
    typed = client.parse(["type", "my answer", "--into", "4", "--enter"])
    assert typed == {"verb": "type", "text": "my answer", "enter": True, "clear": False, "into": {"number": 4}}
    assert client.parse(["wait", "--for", "Saved", "--limit", "20"]) == {"verb": "wait", "text": "Saved", "limit": 20.0}
    assert client.parse(["upload", "--folder", "lib"]) == {"verb": "upload", "folder": "lib"}
    assert client.parse(["resize", "phone"]) == {"verb": "resize", "preset": "phone"}
    assert client.limit_for({"verb": "wait", "limit": 20}) == 20 + client.MARGIN_SECONDS
    with pytest.raises(client.WalkError):
        client.parse(["dance"])


def test_select_takes_a_phrase_a_span_or_an_element():
    assert client.parse(["select", "the spectral", "theorem"]) == {"verb": "select",
                                                                   "target": {"text": "the spectral theorem"}}
    assert client.parse(["select", "A symmetric matrix", "--to", "real eigenvalues."]) == {
        "verb": "select", "target": {"text": "A symmetric matrix"}, "to": "real eigenvalues."}
    assert client.parse(["select", "--to", "end.", "Start"]) == {"verb": "select", "target": {"text": "Start"},
                                                                "to": "end."}
    assert client.parse(["select", "14"]) == {"verb": "select", "target": {"number": 14}}
    for bad in (["select"], ["select", "--to", "x"], ["select", "14", "--to", "x"], ["select", "a", "--to", " "]):
        with pytest.raises(client.WalkError):
            client.parse(bad)
    assert "walk select" in (client.__doc__ or "")


def test_the_selection_is_in_the_observation_while_one_exists():
    dump = perceive.dump_static_html("<html><body><p>Some text</p></body></html>")
    assert "Selection:" not in perceive.render_observation(perceive.perceive(dump), header=["Step 1: look"])
    dump["selection"] = "  A symmetric\n matrix  "
    rendered = perceive.render_observation(perceive.perceive(dump), header=["Step 1: look"])
    assert 'Selection: "A symmetric matrix"' in rendered
    assert rendered.index("Focus:") < rendered.index("Selection:") < rendered.index("--- screen ---")
    dump["selection"] = "word " * 100
    line = next(line for line in perceive.render_observation(perceive.perceive(dump), header=[]).splitlines()
                if line.startswith("Selection: "))
    assert len(line) == len('Selection: ""') + perceive.SELECTION_LIMIT and line.endswith('…"')


def test_every_verb_the_client_sends_is_in_the_protocols_table():
    examples = [["look"], ["click", "1"], ["select", "x"], ["type", "x"], ["key", "Enter"], ["scroll"], ["back"],
                ["hover", "1"], ["wait"], ["upload", "--cancel"], ["resize", "phone"], ["say", "x"]]
    assert {client.parse(argv)["verb"] for argv in examples} == set(protocol.VERBS)


@pytest.fixture(scope="module")
def driver_module():
    saved_path = list(sys.path)
    try:
        yield _load("driver")
    finally:
        sys.path[:] = saved_path
        for name in ("walk_perceive", "walk_protocol"):
            sys.modules.pop(name, None)


class _RecordingWebDriver:
    def __init__(self):
        self.requests = []

    def request(self, method, path, body=None, timeout=120):
        self.requests.append((method, path))
        return None


def _offline_driver(driver_module, tmp_path, viewport):
    import argparse

    args = argparse.Namespace(walk_root=str(tmp_path / viewport), url="http://127.0.0.1:9/", bridge="http://127.0.0.1:9",
                              viewport=viewport, chromedriver="", chromium="", settle=0.0)
    driver = driver_module.Driver(args)
    driver.bridge_state = lambda: {}
    driver.webdriver = _RecordingWebDriver()
    return driver


def test_back_is_refused_on_the_desktop_and_is_the_phones_back(driver_module, tmp_path):
    assert protocol.refusal("back", "desktop") == protocol.DESKTOP_HAS_NO_BACK
    assert protocol.refusal("back", "phone") is None and protocol.refusal("click", "desktop") is None
    assert "Escape" in protocol.DESKTOP_HAS_NO_BACK and "no Back button" in protocol.DESKTOP_HAS_NO_BACK
    desktop = _offline_driver(driver_module, tmp_path, "desktop")
    with pytest.raises(driver_module.StepFailed, match="no Back button"):
        desktop.run({"verb": "back"})
    assert desktop.webdriver.requests == []
    phone = _offline_driver(driver_module, tmp_path, "phone")
    assert phone.run({"verb": "back"}) == ("back", {})
    assert phone.webdriver.requests == [("POST", "/back")]


def test_a_date_field_takes_the_date_a_person_would_pick(driver_module):
    value = driver_module.native_value
    us, uk = ["month", "day", "year"], ["day", "month", "year"]
    assert value("date", "2026-12-09", us) == "2026-12-09"
    assert value("date", "12/09/2026", us) == "2026-12-09"
    assert value("date", "9/12/2026", uk) == "2026-12-09"
    assert value("date", "December 9, 2026", us) == "2026-12-09"
    assert value("date", "9 Dec 2026", us) == "2026-12-09"
    assert value("month", "2026-12") == value("month", "12/2026") == value("month", "December 2026") == "2026-12"
    assert value("time", "14:30") == value("time", "2:30 PM") == "14:30"
    assert value("datetime-local", "2026-12-09T14:30") == value("datetime-local", "12/09/2026, 2:30 pm", us) \
        == "2026-12-09T14:30"
    for kind, text in (("date", "13/45/2026"), ("date", "261209"), ("time", "25:00"), ("month", "soon")):
        with pytest.raises(ValueError):
            value(kind, text, us)
    assert driver_module.shown_format("date", us) == "mm/dd/yyyy"


# -- start.py --------------------------------------------------------------------------------------


@pytest.fixture()
def start_module():
    return _load("start")


def test_a_phone_walk_refuses_before_the_vault_when_the_phone_app_is_not_built(start_module, tmp_path, monkeypatch):
    monkeypatch.setattr(start_module, "PHONE_APP_INDEX", tmp_path / "app" / "index.html")
    with pytest.raises(SystemExit) as refused:
        start_module.main(["p1", "--from", "established", "--phone", "--walks-dir", str(tmp_path / "walks")])
    message = str(refused.value)
    assert "phone app is not built" in message and "npm ci" in message and "npm run build" in message
    assert "apps/learnloop-mobile" in message
    assert not (tmp_path / "walks").exists()
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "index.html").write_text("<html></html>", encoding="utf-8")
    assert start_module.phone_app_refusal() is None


def test_a_walk_without_files_gets_every_sample_document(start_module):
    names = [path.name for path in start_module.default_files()]
    on_disk = sorted(path.name for path in (ROOT / "samples").rglob("*") if path.is_file())
    assert "NOTICE" not in names and sorted(names + ["NOTICE"]) == on_disk
    assert "mit-18.06-spring-2010-quiz1-solutions.pdf" in names


def test_the_decider_choice_needs_a_live_walk(start_module, tmp_path, capsys):
    with pytest.raises(SystemExit) as refused:
        start_module.main(["d1", "--from", "fresh", "--decider", "perplexity", "--walks-dir", str(tmp_path)])
    assert refused.value.code == 2 and "--models live" in capsys.readouterr().err
    assert not (tmp_path / "d1").exists()


def test_the_perplexity_decider_is_written_and_its_routes_classified(bridge, tmp_path, monkeypatch):
    from learnloop.config import load_config
    from learnloop.ops.settings_store import apply_config_updates
    from tests.helpers import create_basic_vault

    vault = create_basic_vault(tmp_path / "vault").root
    # The fake-model mode's machinery: walk_fake active and forced, as the bridge sets it up.
    apply_config_updates(vault / "learnloop.toml", fake.provider_table("http://127.0.0.1:9/fake-model/v1"))
    apply_config_updates(vault / "learnloop.toml", bridge.decider_table("perplexity"))
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", fake.FAKE_PROFILE)
    config = load_config(vault / "learnloop.toml", load_environment=False)
    profile = config.ai.providers["perplexity_decider"]
    assert (profile.type, profile.api, profile.model, profile.base_url, profile.api_key_env) == (
        "decider", "perplexity", "pplx-decider-v1.3", "https://api.perplexity.ai", "PERPLEXITY_API_KEY")
    assert {task: getattr(config.ai.routing, task) for task in bridge.DECIDER_TASKS} == dict.fromkeys(
        bridge.DECIDER_TASKS, "perplexity_decider")

    route_check = _load("route_check")
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    unreachable = route_check.classify(vault, fake.FAKE_PROFILE)
    for task in bridge.DECIDER_TASKS:
        route = unreachable["routes"][task]
        assert (route["provider"], route["kind"]) == ("perplexity_decider", "unreachable")
        assert "PERPLEXITY_API_KEY" in route["message"]
    assert not set(bridge.DECIDER_TASKS) & set(unreachable["live"])

    monkeypatch.setenv("PERPLEXITY_API_KEY", "walk-test-not-a-key")
    live = route_check.classify(vault, fake.FAKE_PROFILE)
    assert set(bridge.DECIDER_TASKS) <= set(live["live"])
    for task in bridge.DECIDER_TASKS:
        assert live["routes"][task] == {"provider": "perplexity_decider", "kind": "live", "status": "ready"}
    assert all("message" not in route for route in live["routes"].values() if route["kind"] == "live")


def test_a_replayed_step_names_its_element_by_role_and_name():
    sys.path.insert(0, str(WALK))
    try:
        replay = _load("replay")
    finally:
        sys.path.remove(str(WALK))
        sys.modules.pop("walk_client", None)
    record = {"step": 4, "action": {"verb": "click", "target": {"number": 19}, "seq": 4},
              "detail": {"target": '[19] button "Submit ^↵" (focused)'}}
    assert replay.replayable(record) == {"verb": "click", "target": {"role": "button", "name": "Submit ^↵"}}
    assert replay.replayable({"action": {"verb": "say", "text": "hm", "seq": 2}}) == {"verb": "say", "text": "hm"}
    assert replay.replayable({"action": {"verb": "_malformed"}}) is None


# -- the fake model --------------------------------------------------------------------------------


def test_the_fake_model_answers_any_strict_schema_and_echoes_the_request():
    schema = {
        "type": "object", "additionalProperties": False,
        "required": ["attempt_id", "kind", "score", "confidence", "note", "items", "detail"],
        "properties": {
            "attempt_id": {"type": "string"},
            "kind": {"type": "string", "enum": ["miss", "hit"]},
            "score": {"type": "integer", "minimum": 0, "maximum": 4},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "note": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "items": {"type": "array", "items": {"type": "string"}},
            "detail": {"$ref": "#/$defs/Detail"},
        },
        "$defs": {"Detail": {"type": "object", "properties": {"why": {"type": "string", "minLength": 3}},
                             "required": ["why"], "additionalProperties": False}},
    }
    body = {"model": "m", "messages": [{"role": "user", "content": 'Grade this: {"attempt_id": "att_9"}'}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "Probe", "schema": schema}}}
    completion, record = fake.FakeModel().answer(body)
    answer = json.loads(completion["choices"][0]["message"]["content"])
    assert answer == {"attempt_id": "att_9", "kind": "miss", "score": 2, "confidence": 0.5, "note": None,
                      "items": [], "detail": {"why": "[walk fake model: why]"}}
    assert record["schema"] == "Probe"


def test_a_grade_covers_the_rubric_and_decision_routes_are_declined():
    rubric = {"rubric": {"criteria": [{"id": "correctness", "points": 3}, {"id": "reasoning", "points": 1}]}}
    schema = {"type": "object", "properties": {
        "criterion_evidence": {"type": "array", "items": {"type": "object", "properties": {}}},
        "rubric_score": {"type": "integer", "minimum": 0}, "grader_confidence": {"type": "number"}}}
    body = {"messages": [{"role": "user", "content": json.dumps(rubric)}],
            "response_format": {"json_schema": {"name": "BlindGradingProposal", "schema": schema}}}
    answer = json.loads(fake.FakeModel().answer(body)[0]["choices"][0]["message"]["content"])
    assert [entry["criterion_id"] for entry in answer["criterion_evidence"]] == ["correctness", "reasoning"]
    assert answer["rubric_score"] == 1 and answer["grader_confidence"] == 0.9
    declined = {"messages": [], "response_format": {"json_schema": {"name": "RouterLLMChoiceV3", "schema": {}}}}
    with pytest.raises(fake.Declined):
        fake.FakeModel().answer(declined)


def test_the_fake_profile_is_an_ordinary_openai_chat_profile():
    table = fake.provider_table("http://127.0.0.1:9/fake-model/v1")
    assert table[("ai", "active_provider")] == fake.FAKE_PROFILE
    assert table[("ai", "providers", fake.FAKE_PROFILE, "type")] == "openai_chat"
    assert table[("ai", "providers", fake.FAKE_PROFILE, "base_url")].startswith("http://127.0.0.1:")
    assert 'active_provider = "walk_fake"' in fake.ai_defaults_toml("http://127.0.0.1:9/fake-model/v1")


# -- the bridge's helpers --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bridge():
    # bridge.py imports its siblings by name; leave neither the path nor those modules behind.
    saved_path = list(sys.path)
    try:
        yield _load("bridge")
    finally:
        sys.path[:] = saved_path
        for name in ("fake_model", "walk_commands"):
            sys.modules.pop(name, None)


def test_the_apps_csp_maps_its_schemes_onto_the_bridge(bridge):
    conf = (ROOT / "apps" / "learnloop-tauri" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
    csp = bridge._browser_csp(conf)
    assert "llpdf:" not in csp and "ipc:" not in csp and "tauri://" not in csp
    assert "connect-src 'self'" in csp and "script-src 'self' 'wasm-unsafe-eval'" in csp
    html = "<script>let a = 1;</script><script src='/x.js'></script>"
    hashes = bridge.inline_script_hashes(html)
    assert len(hashes) == 1 and hashes[0].startswith("'sha256-")
    assert bridge.csp_with_hashes(csp, hashes).count("'sha256-") == 1


def test_media_ranges_match_the_rust_handler(bridge):
    assert bridge.slice_range(100, None) is None
    assert bridge.slice_range(100, "chunks=0-1") is None
    assert bridge.slice_range(100, "bytes=0-10,20-30") is None
    assert bridge.slice_range(100, "bytes=0-49") == (0, 49)
    assert bridge.slice_range(100, "bytes=50-") == (50, 99)
    assert bridge.slice_range(100, "bytes=-10") == (90, 99)
    assert bridge.slice_range(100, "bytes=90-500") == (90, 99)
    assert bridge.slice_range(100, "bytes=100-") is False
    assert bridge.slice_range(100, "bytes=30-10") is False
    assert bridge.slice_range(0, "bytes=-5") is False


def test_the_watcher_reports_what_the_rust_watcher_would(bridge, tmp_path):
    (tmp_path / "subjects" / "s").mkdir(parents=True)
    (tmp_path / "canonical-sources" / "raw").mkdir(parents=True)
    (tmp_path / "subjects" / "s" / "a.yaml").write_text("x", encoding="utf-8")
    (tmp_path / "canonical-sources" / "raw" / "b.json").write_text("x", encoding="utf-8")
    (tmp_path / "state.sqlite").write_text("x", encoding="utf-8")
    (tmp_path / "learnloop.toml").write_text("x", encoding="utf-8")
    before = bridge.scan(tmp_path)
    assert set(before) == {"subjects/s/a.yaml", "learnloop.toml"}
    (tmp_path / "subjects" / "s" / "a.yaml").write_text("longer", encoding="utf-8")
    (tmp_path / "subjects" / "s" / "a.yaml.tmp").write_text("x", encoding="utf-8")
    (tmp_path / "learnloop.toml").unlink()
    assert bridge.changed(before, bridge.scan(tmp_path)) == {"subjects/s/a.yaml", "learnloop.toml"}


def test_the_bridge_refuses_a_vault_outside_the_walk(tmp_path):
    result = subprocess.run(
        [sys.executable, str(WALK / "bridge.py"), "--walk-root", str(tmp_path / "walk"), "--vault",
         str(tmp_path / "elsewhere"), "--port", "1"], capture_output=True, text=True, timeout=60)
    assert result.returncode == 2 and "inside the walk directory" in result.stderr
    live = subprocess.run(
        [sys.executable, str(WALK / "bridge.py"), "--walk-root", str(tmp_path), "--vault", str(tmp_path / "v"),
         "--port", "1", "--models", "live"], capture_output=True, text=True, timeout=60)
    assert live.returncode == 2 and "--allow-live-route" in live.stderr


# -- a real walk (Chromium): never in the gates ----------------------------------------------------


@pytest.mark.ux_walk_browser
@pytest.mark.skipif(os.environ.get("LEARNLOOP_UX_WALK_BROWSER") != "1",
                    reason="drives Chromium; set LEARNLOOP_UX_WALK_BROWSER=1 to run it")
def test_an_empty_walk_shows_the_first_run_screen_and_its_file_chooser(tmp_path):
    name = f"test-{os.getpid()}"
    walks = tmp_path / "walks"
    start = subprocess.run([sys.executable, str(WALK / "start.py"), name, "--from", "empty", "--walks-dir",
                            str(walks)], capture_output=True, text=True, timeout=600)
    try:
        assert start.returncode == 0, start.stderr[-2000:]
        persona = walks / name / "persona"
        walk = [sys.executable, str(persona / "walk")]
        first = subprocess.run([*walk, "look"], capture_output=True, text=True, timeout=200)
        assert first.returncode == 0 and "Choose a file" in first.stdout
        chooser = subprocess.run([*walk, "click", "Choose a file…"], capture_output=True, text=True, timeout=200)
        assert "is open over the app" in chooser.stdout
        cancelled = subprocess.run([*walk, "upload", "--cancel"], capture_output=True, text=True, timeout=200)
        assert cancelled.returncode == 0 and "is open over the app" not in cancelled.stdout
    finally:
        subprocess.run([sys.executable, str(WALK / "stop.py"), name, "--walks-dir", str(walks)], timeout=120)
