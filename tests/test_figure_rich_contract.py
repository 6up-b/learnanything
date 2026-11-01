"""RW5d P2b: the author's V3 contract, the neutral tier menu and tiers_allowed
(spec_reader_show_me_figures_v1 §7.2, §8.4; G-SM20).

* V3 off (``figures.rich_tiers_enabled`` off, or no rich tier available
  here): the author's contract, prompt and reuse key are V2's (or V1's) byte
  for byte.
* ``tiers_allowed`` leaves out each unavailable tier: Manim missing, off
  Linux, no ``bwrap``, no standing opt-in, and the JS build flag (G-SM14 not
  passed: ``js_animation`` is never on a menu in this build).
* The menu states facts, never a preference (a golden prompt test).

Fakes only: no model, Manim or bubblewrap is reached.
"""

from __future__ import annotations

import pytest

from learnloop.figures import rich as RICH
from learnloop.figures import routes as R
from learnloop.figures import service as FS
from learnloop.vault.loader import load_vault
from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, AuthorFake, build_figure_vault, flagship, set_config


def _vault(tmp_path, *, rich=True, opt_in="standing", sketch=False):
    paths, repository = build_figure_vault(tmp_path / "vault", sketch=sketch, rich=rich)
    if opt_in is not None:
        set_config(paths, "figures", manim_opt_in=opt_in)
    return paths, repository, load_vault(paths.root)


GOLDEN_MENU = (
    'Media you may answer with: "spec": a declarative figure. Ready in seconds; every number checked by LearnLoop; '
    'sliders, predictions and a values table come with it; reusable and accessible. "sketch": a small sealed program '
    'drawing shapes. Ready in tens of seconds; stated claims checked; interactive; summaries rather than thousands of '
    'objects. "manim": a narrated video rendered on this computer. Takes a few minutes to write and render; not '
    'interactive; only its declared functions can be checked; desktop only. Choose the medium that best explains this '
    'idea to this request, and say why in why_this_tier. If you choose a rich medium and a spec or sketch can show a '
    'useful part of it now, also write that one. status is the medium you chose: "spec" with spec_json, "sketch" with '
    'sketch_json, "manim" with rich_json (and spec_json or sketch_json for the optional quick figure); if no medium on '
    'the list can express it, status "unsupported" with its kind and why, and why_this_tier \'\'. Leave every field the '
    "status doesn't use ''."
)
RANKING_WORDS = ("prefer", "preferred", "instead", "fallback", "last resort", "cheaper", "better", "worse",
                 "only for what", "only when")


def test_the_menu_is_neutral_facts_in_order_golden():
    """G-SM20: one neutral sentence per offered medium, in the spec's order, no ranking word."""

    text = R.tier_menu_text(("grammar", "sketch", "manim"))
    assert text == GOLDEN_MENU
    menu = text.split(" Choose the medium")[0].lower()
    for word in RANKING_WORDS:
        assert word not in menu, word
    # An unavailable medium is absent, never described as worse.
    without_sketch = R.tier_menu_text(("grammar", "manim"))
    assert '"sketch"' not in without_sketch and "sketch_json" not in without_sketch
    assert "js_animation" not in text


def test_v3_instructions_replace_the_preference_and_carry_the_rich_brief():
    instructions = R.author_instructions(sketch=True, tiers=("grammar", "sketch", "manim"))
    assert R.STATUS_V2 not in instructions  # rev 1's "prefer the grammar" sentence is gone
    assert "Write a sketch only for what it cannot express" not in instructions
    assert "RICH (rich_json" in instructions and "SketchProgramV1" in instructions
    assert R.author_prompt_version(sketch=True, tiers=("grammar", "sketch", "manim")) == \
        R.AUTHOR_PROMPT_VERSION + R.SKETCH_SUFFIX + "+rich-v1[grammar,sketch,manim]"
    assert R.output_model(sketch=True, tiers=("grammar", "sketch", "manim")) is R.FigureAuthorOutputV3
    fields = set(R.FigureAuthorOutputV3.model_fields)
    assert {"status", "why_this_tier", "rich_json", "spec_json", "sketch_json"} <= fields


@pytest.mark.parametrize("tiers", [None, ("grammar",), ("grammar", "sketch")])
def test_with_no_rich_tier_on_the_menu_the_contract_is_v2s_byte_for_byte(tiers):
    """G-SM20 (off): no rich tier on the menu is P2's (or RW5b's) contract, prompt and version exactly."""

    for sketch in (False, True):
        assert R.author_instructions(sketch=sketch, tiers=tiers) == R.author_instructions(sketch=sketch)
        assert R.author_prompt_version(sketch=sketch, tiers=tiers) == R.author_prompt_version(sketch=sketch)
        assert R.output_model(sketch=sketch, tiers=tiers) is R.output_model(sketch=sketch)
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
    context = FS.SourceContext()
    assert FS.request_hash(request, context, None, tiers=tiers) == FS.request_hash(request, context, None)


def test_the_reuse_key_names_the_menu_and_the_rich_versions():
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
    context = FS.SourceContext()
    plain = FS.request_hash(request, context, None)
    rich = FS.request_hash(request, context, None, tiers=("grammar", "manim"), rich_runtime="manim 0.19; v1")
    assert rich != plain
    assert rich != FS.request_hash(request, context, None, tiers=("grammar", "manim"), rich_runtime="manim 0.20; v1")
    assert rich != FS.request_hash(request, context, None, tiers=("grammar", "sketch", "manim"),
                                   rich_runtime="manim 0.19; v1")


def test_tiers_allowed_needs_the_switch_linux_bwrap_manim_and_the_standing_opt_in(tmp_path, monkeypatch):
    import learnloop.content.authoring.concept_animation as CA

    _paths, _repository, vault = _vault(tmp_path)
    RF.ready_manim(monkeypatch)
    assert RICH.tiers_allowed(vault, sketch=False) == ("grammar", "manim")
    assert RICH.tiers_allowed(vault, sketch=True) == ("grammar", "sketch", "manim")
    # js_animation is behind its build flag (G-SM14 not passed in this build).
    assert RICH.JS_ANIMATION_BUILD_FLAG is False
    assert "js_animation" not in RICH.tiers_allowed(vault, sketch=True)
    monkeypatch.undo()

    # Off Linux, no bwrap, no Manim: absent (the real probe, with each cause faked).
    monkeypatch.setattr(RICH.sys, "platform", "darwin")
    assert RICH.manim_runtime_state(vault)["reason"] == "off_linux"
    assert RICH.tiers_allowed(vault, sketch=False) == ("grammar",)
    monkeypatch.setattr(RICH.sys, "platform", "linux")
    monkeypatch.setattr(RICH.R, "models_off", lambda: False)
    monkeypatch.setattr(CA, "_sandbox_bwrap_path", lambda: None)
    assert RICH.manim_runtime_state(vault)["reason"] == "no_bwrap"
    assert RICH.tiers_allowed(vault, sketch=False) == ("grammar",)
    monkeypatch.setattr(CA, "_sandbox_bwrap_path", lambda: "/usr/bin/bwrap")
    monkeypatch.setattr(CA, "manim_runtime", lambda **kwargs: {"available": False, "version": None,
                                                                "reason": "manim executable not found"})
    RICH._MANIM_PROBE.clear()
    assert RICH.manim_runtime_state(vault)["reason"] == "no_manim"
    assert RICH.tiers_allowed(vault, sketch=False) == ("grammar",)
    RICH._MANIM_PROBE.clear()


@pytest.mark.parametrize("opt_in", [None, "declined"])
def test_without_the_standing_opt_in_manim_is_not_on_the_menu(tmp_path, monkeypatch, opt_in):
    _paths, _repository, vault = _vault(tmp_path, opt_in=opt_in)
    RF.ready_manim(monkeypatch)
    assert RICH.tiers_allowed(vault, sketch=False) == ("grammar",)
    assert RICH.manim_opt_in_needed(vault) is (opt_in is None)


def test_switched_off_no_rich_tier_and_no_ask(tmp_path, monkeypatch):
    _paths, _repository, vault = _vault(tmp_path, rich=False, opt_in=None)
    RF.ready_manim(monkeypatch)
    assert RICH.tiers_allowed(vault, sketch=True) == ("grammar", "sketch")
    assert RICH.manim_opt_in_needed(vault) is False
    _paths, _repository, standing = _vault(tmp_path / "standing", rich=False, opt_in="standing")
    assert RICH.tiers_allowed(standing, sketch=False) == ("grammar",)


def test_a_build_with_manim_on_the_menu_sends_v3_and_records_the_menu(tmp_path, monkeypatch):
    paths, repository, vault = _vault(tmp_path)
    RF.ready_manim(monkeypatch)
    author = AuthorFake([flagship(kind="illustrative")])
    spawned: list[dict] = []
    outcome = FS.build_figure(vault, repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]),
                              author_client=author, spawn_rich=lambda payload: spawned.append(payload) or "job")
    assert outcome.view["verification"] == "illustrative" and outcome.view["tier"] == "grammar"
    assert outcome.view["fuller"] is None and spawned == []
    prompt = author.prompts[0]
    assert "a narrated video rendered on this computer" in prompt and "+rich-v1[grammar,manim]" in prompt
    assert "why_this_tier" in prompt
    from tests.figure_fixtures import rows

    (asked,) = rows(repository, "figure_requests")
    assert asked["tiers_allowed_json"] == '["grammar", "manim"]'
    tier = [row for row in rows(repository, "judgment_ledger") if row["task"] == "figure_tier"]
    assert [row["verdict"] for row in tier] == ["spec"]
    assert tier[0]["rationale"] == "a declarative figure shows this exactly"


def test_without_a_way_to_start_the_job_no_rich_tier_is_offered(tmp_path, monkeypatch):
    """The CLI and other hosts with no durable queue: the menu is P2's."""

    paths, repository, vault = _vault(tmp_path)
    RF.ready_manim(monkeypatch)
    author = AuthorFake([flagship(kind="illustrative")])
    FS.build_figure(vault, repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]),
                    author_client=author)
    assert "manim" not in author.prompts[0] and "+rich-v1" not in author.prompts[0]


def test_v3_a_status_off_the_menu_or_with_no_reason_gets_the_second_attempt(tmp_path, monkeypatch):
    paths, repository, vault = _vault(tmp_path)
    RF.ready_manim(monkeypatch)
    author = AuthorFake([("rich", "js_animation", RF.brief(tier="js_animation"), "WebGL"),
                         flagship(kind="illustrative")])
    outcome = FS.build_figure(vault, repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]),
                              author_client=author, spawn_rich=lambda payload: "job")
    assert author.calls == 2 and outcome.view["verification"] == "illustrative"
    assert any("not one of the media offered" in problem
               for problem in author.contexts[1]["problems_with_the_last_attempt"])
