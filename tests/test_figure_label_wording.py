"""Reader follow-ups Nov 1b, item 1: RW5d §9b.4's free-text label rule (P2b ruling R2).

Ruling R2 (``docs/reviews/reader-rw5d-p2b-manim.md``): "The §9b.4 rule that
model-written free text (narration, title, what it shows, assumptions) must
not read like a check label is not built in this stage. Queued as a
follow-up to land before the owner gives the Manim opt-in." Before this
follow-up, a figure's ``demonstrates`` reading "matches the book's equation
(checked)", a Manim title "✓ verified by LearnLoop" or a tier reason in badge
words was stored and shown as written. Only identifiers were covered (the
sketch tier's ``impersonates``).

Now :mod:`learnloop.figures.labels` matches the code-owned label vocabulary
structurally: the label constants and their check segments, check words in
badge form, and check-mark glyphs. Ordinary prose (*check that*, *we
verified*) is not matched. On a hit, the author's one repair call gets code's
own words. A spec or sketch that still violates is shown without that text.
A Manim figure that still violates is refused (stored failed, never shown).

Fakes only: no model, Manim or bubblewrap runs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from learnloop.figures import labels as L
from learnloop.figures import rich as RICH
from learnloop.figures import service as FS
from learnloop.vault.loader import load_vault
from tests import rich_fixtures as RF
from tests import sketch_fixtures as F
from tests.figure_fixtures import EXTRACTION, AuthorFake, build_figure_vault, flagship, rows
from tests.test_figure_rich_job import WHY, _Rig

ROOT = Path(__file__).resolve().parents[1]
FIGURES_TS = ROOT / "apps/learnloop-tauri/src/screens/reader/figures"
CLAIM = "matches the book's equation (checked)"
CLEAN_ASSUMPTION = {"text": "λ > 0 and 0 < p < 1", "span_id": "p2", "quote": "0 < p < 1 and \\lambda > 0"}


# -- the matcher ---------------------------------------------------------------


@pytest.mark.parametrize("text", [
    CLAIM, "✓ checked", "Verified", "verified by LearnLoop", "LearnLoop has checked this curve",
    "Checked: the area is 1", "the area · checked", "[verified] the density", "Tested ✔",
    "AI-made video · not checked", "this curve is checked against the book", "CHECKED BY LEARNLOOP: every value",
    "the video itself is not checked frame by frame", "AI-written simulation · nothing in it checked",
    "ＣＨＥＣＫＥＤ ｂｙ ＬｅａｒｎＬｏｏｐ",  # NFKC: fullwidth forms fold to the label
])
def test_label_like_text_is_matched(text):
    assert L.label_like(text) is not None


@pytest.mark.parametrize("text", [
    "check that the area under the curve is 1", "we verified the identity by expanding both sides",
    "the box is checked when the event happens", "a checked step", "the sum is verified.",
    "how verification works", "the density of the two-sided exponential", "", None,
    L.REASON_WITHHELD,
])
def test_ordinary_prose_is_not_matched(text):
    assert L.label_like(text) is None


def test_the_vocabulary_comes_from_the_code_owned_labels():
    """Every code-owned badge and check line is matched as written, and the
    tiers' constants are the labels module's own (no second hand list)."""

    for label in L.CODE_OWNED_LABELS:
        assert L.label_like(label) is not None, label
        assert L.label_like(f"the figure: {label.upper()}") is not None, label
    assert FS.SKETCH_LABEL is L.SKETCH_LABEL and FS.SKETCH_UNCHECKED_LABEL is L.SKETCH_UNCHECKED_LABEL
    assert FS.SKETCH_NOT_FROM_BOOKS_LABEL is L.SKETCH_NOT_FROM_BOOKS_LABEL
    assert FS.NOT_FROM_BOOKS_LABEL is L.NOT_FROM_BOOKS_LABEL and FS.LABELS["illustrative"] is L.ILLUSTRATIVE_LABEL
    assert RICH.MANIM_LABEL is L.MANIM_LABEL and RICH.MANIM_UNCHECKED_LABEL is L.MANIM_UNCHECKED_LABEL
    assert RICH.MANIM_NOT_FROM_BOOKS_LABEL is L.MANIM_NOT_FROM_BOOKS_LABEL
    assert RICH.MANIM_NOT_COVERED is L.MANIM_NOT_COVERED
    assert L.CHECK_LABEL_WORDS == ("checked", FS.store.VERIFIED_RW5C)


def _frame(name: str, frame: str) -> dict[str, str]:
    source = (FIGURES_TS / name).read_text(encoding="utf-8")
    body = source[source.index(f"export const {frame} = {{"):]
    body = body[:body.index("} as const;")]
    return dict(re.findall(r'^\s+(\w+): "((?:[^"\\]|\\.)*)",?$', body, flags=re.MULTILINE))


def test_the_desktop_frames_carry_the_same_label_strings():
    """The badge slot and check lines are drawn by the desktop from its own
    frames: the Python labels the desktop draws are its strings, character
    for character, and every badge-slot or check-line string the desktop
    draws reads as a label to the rule (so a model can't reproduce it)."""

    figure = _frame("FigureInline.tsx", "FIGURE_FRAME")
    sketch = _frame("sketch/SketchFigure.tsx", "SKETCH_FRAME")
    rich = _frame("RichFigure.tsx", "RICH_FRAME")
    assert figure["illustration"] == L.ILLUSTRATIVE_LABEL and figure["checksLead"] == L.CHECKS_LEAD
    assert (sketch["badge"], sketch["unchecked"], sketch["notFromBooks"], sketch["checksLead"]) == (
        L.SKETCH_LABEL, L.SKETCH_UNCHECKED_LABEL, L.SKETCH_NOT_FROM_BOOKS_LABEL, L.CHECKS_LEAD)
    assert (rich["manim"], rich["manimUnchecked"], rich["manimNotFromBooks"], rich["notCovered"]) == (
        L.MANIM_LABEL, L.MANIM_UNCHECKED_LABEL, L.MANIM_NOT_FROM_BOOKS_LABEL, L.MANIM_NOT_COVERED)
    drawn = [figure["illustration"], figure["notFromBooks"], figure["checksLead"], *sketch.values(),
             rich["manim"], rich["manimUnchecked"], rich["notCovered"]]
    for text in drawn:
        if "checked" in text:
            assert L.label_like(text) is not None, text


def test_problems_are_in_codes_words_and_name_the_field():
    (problem,) = L.label_problems([("spec_json.demonstrates", CLAIM), ("spec_json.assumptions[0]", "a < 0")])
    assert problem.startswith("spec_json.demonstrates reads like one of LearnLoop's check labels ('(checked)')")
    assert "your own words" in problem


def test_strip_json_leaves_out_only_the_label_like_text():
    raw = json.dumps({"demonstrates": CLAIM, "assumptions": [CLEAN_ASSUMPTION, {"text": "✓ verified"}, "a < 0"],
                      "panels": [{"label": "checked"}]})
    stripped = json.loads(L.strip_json(raw))
    assert stripped["demonstrates"] == "" and stripped["assumptions"] == [CLEAN_ASSUMPTION, "a < 0"]
    assert stripped["panels"] == [{"label": "checked"}]  # labels inside the frame: not this rule's fields
    clean = json.dumps({"demonstrates": "the density", "assumptions": [CLEAN_ASSUMPTION]})
    assert L.strip_json(clean) is clean and L.strip_json("not json") == "not json"


# -- the grammar tier ----------------------------------------------------------


def _build(tmp_path, answers, *, sketch=False):
    paths, repository = build_figure_vault(tmp_path / "vault", sketch=sketch)
    author = AuthorFake(answers)
    outcome = FS.build_figure(load_vault(paths.root), repository,
                              FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]), author_client=author)
    return outcome, author, repository


def test_r2_a_label_like_demonstrates_gets_codes_words_in_the_repair_call(tmp_path):
    outcome, author, _repository = _build(tmp_path, [flagship(kind="illustrative", demonstrates=CLAIM),
                                                     flagship(kind="illustrative")])
    assert author.calls == 2
    problems = author.contexts[1]["problems_with_the_last_attempt"]
    assert problems[0].startswith("spec_json.demonstrates reads like one of LearnLoop's check labels")
    view = outcome.view
    assert view["verification"] == "illustrative" and view["demonstrates"] == flagship()["demonstrates"]


def test_r2_a_spec_still_label_like_after_the_repair_is_shown_without_that_text(tmp_path):
    bad = flagship(kind="illustrative", demonstrates=CLAIM,
                   assumptions=[CLEAN_ASSUMPTION, {"text": "✓ verified by LearnLoop"}])
    outcome, author, repository = _build(tmp_path, [bad, bad])
    assert author.calls == 2
    view = outcome.view
    assert view["verification"] == "illustrative"
    assert view["demonstrates"] == "" and [a["text"] for a in view["assumptions"]] == [CLEAN_ASSUMPTION["text"]]
    (row,) = rows(repository, "interactive_figures")
    stored = json.loads(row["spec_json"])
    assert stored["demonstrates"] == "" and len(stored["assumptions"]) == 1
    assert "checked" not in row["spec_json"] and "✓" not in row["spec_json"]


def test_r2_ordinary_prose_costs_no_repair_call(tmp_path):
    outcome, author, _repository = _build(tmp_path, [flagship(
        kind="illustrative", demonstrates="check that the area left of zero is p; we verified it by integrating")])
    assert author.calls == 1 and outcome.view["demonstrates"].startswith("check that the area")


# -- the sketch tier -----------------------------------------------------------


def test_r2_a_sketch_still_label_like_after_the_repair_is_shown_without_that_text(tmp_path):
    bad = F.walk(demonstrates="Verified: the spread grows like sqrt(n)",
                 assumptions=[{"text": "steps of +1 or -1"}, {"text": "(checked) independent steps"}])
    outcome, author, _repository = _build(tmp_path, [("sketch", bad, "the grammar has no random process"),
                                                     ("sketch", bad, "the grammar has no random process")],
                                          sketch=True)
    assert author.calls == 2
    assert author.contexts[1]["problems_with_the_last_attempt"][0].startswith("sketch_json.demonstrates reads like")
    view = outcome.view
    assert view["tier"] == "sketch" and view["verification"] == "illustrative"
    assert view["demonstrates"] in ("", None) and [a["text"] for a in view["assumptions"]] == ["steps of +1 or -1"]


def test_r2_a_label_like_tier_reason_is_repaired_then_left_out_of_the_receipt(tmp_path):
    reason = "✓ checked: a random process needs a simulation"
    _outcome, author, repository = _build(tmp_path, [("sketch", F.walk(), reason), ("sketch", F.walk(), reason)],
                                          sketch=True)
    assert author.contexts[1]["problems_with_the_last_attempt"][0].startswith("why_not_spec reads like")
    (tier,) = [row for row in rows(repository, "judgment_ledger") if row["task"] == "figure_tier"]
    assert tier["verdict"] == "sketch" and tier["rationale"] == L.REASON_WITHHELD


# -- the rich tier: the brief, the tier reason, the Manim figure's own text ------


def test_r2_a_rich_brief_and_reason_still_label_like_are_left_out(tmp_path, monkeypatch):
    bad_brief = RF.brief(demonstrates="the spiral · checked by LearnLoop", assumptions=[{"text": "a < 0"},
                                                                                       {"text": "[verified]"}])
    answer = ("rich", "manim", bad_brief, "LearnLoop verified this needs motion")
    rig = _Rig(tmp_path, monkeypatch, [answer, answer])
    rig.build()
    assert rig.author.calls == 2
    problems = rig.author.contexts[1]["problems_with_the_last_attempt"]
    assert any(problem.startswith("why_this_tier reads like") for problem in problems)
    assert any(problem.startswith("rich_json.demonstrates reads like") for problem in problems)
    rig.ingest.drain()
    (line,) = rig.listed()
    assert line["tier"] == "manim" and line["verification"] == "illustrative"
    spec = json.loads(rows(rig.repository, "interactive_figures")[0]["spec_json"])
    assert spec["demonstrates"] == "" and [a["text"] for a in spec["assumptions"]] == ["a < 0"]
    (tier,) = [row for row in rows(rig.repository, "judgment_ledger") if row["task"] == "figure_tier"]
    assert tier["rationale"] == L.REASON_WITHHELD
    assert rig.rich_author.contexts[0]["brief"]["demonstrates"] == ""


def test_r2_a_label_like_manim_title_gets_codes_words_in_the_repair_call(tmp_path, monkeypatch):
    bad = {**RF.scene_output(), "title": "✓ Verified by LearnLoop: why it spirals"}
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [bad, RF.scene_output()])
    rig.build()
    rig.ingest.drain()
    assert rig.rich_author.calls == 2
    problems = rig.rich_author.contexts[1]["problems_with_the_last_attempt"]
    assert problems[0].startswith("title reads like one of LearnLoop's check labels")
    (line,) = rig.listed()
    assert line["verification"] == "illustrative" and line["manim"]["title"] == "Why the trajectory spirals"


def test_r2_a_manim_narration_still_label_like_is_refused(tmp_path, monkeypatch):
    bad = {**RF.scene_output(), "narration_md": "The spiral below is checked against the book."}
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [bad, bad])
    rig.build()
    rig.ingest.drain()
    assert rig.rich_author.calls == 2 and rig.renders.calls == []
    (row,) = rows(rig.repository, "interactive_figures")
    assert row["verification"] == "failed" and row["spec_json"] is None
    assert json.loads(row["verification_report_json"])["reason"].startswith("narration_md reads like")
    assert "The spiral below is checked" not in json.dumps(rig.listed())
