"""Follow-ups batch 6 (G1): teacher TE1b's router card preference lines.

A pending card's "Not now" (``released``, after a Start whose lesson never opened) is the learner's
answer, in its own words after the Start's line, never folded into a decline's "not now on X"; an
``expired`` reservation (set aside by the app) is not the learner's answer and is not shown.

Every model is a fake; no network.
"""

from __future__ import annotations

from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.router.card import SUGGESTION_SECTION
from learnloop.vault.loader import load_vault
from tests.teacher_te1b_landing_r2_helpers import _start, _today, _without
from tests.teacher_te1b_review_fixes_helpers import _card
from tests.teacher_te1b_suggestions_helpers import _clock, _rows, _vault, no_network, shown  # noqa: F401


# --- (1) the preference lines ------------------------------------------------------------------------


def test_not_now_on_a_pending_card_is_its_own_line_after_the_start(tmp_path, shown, no_network):
    paths, repository = _vault(tmp_path)
    card, lesson = _start(paths, repository)
    title = card["suggestion"]["title"]
    SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="released",
               clock=_clock(hours=3))
    after = _card(paths, repository, "2026-11-03T09:00:00Z")
    entries = after.json["evidence_sections"][SUGGESTION_SECTION]
    assert [entry["response"] for entry in entries] == ["released", "accepted"]  # newest first
    assert entries[0]["topics"] == entries[1]["topics"] == [title]
    assert f"2026-11-02 let the started lesson on {title} go before it opened (not now)" in after.text
    assert f"2026-11-02 started the suggested lesson on {title}" in after.text
    assert f"not now on {title}" not in after.text.replace("(not now)", "")  # never read as a decline


def test_a_declined_suggestion_keeps_its_not_now_line(tmp_path, shown, no_network):
    paths, repository = _vault(tmp_path)
    card = _today(load_vault(paths.root), repository, _clock())
    SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="declined",
               clock=_clock(hours=1))
    after = _card(paths, repository, "2026-11-03T09:00:00Z")
    assert [e["response"] for e in after.json["evidence_sections"][SUGGESTION_SECTION]] == ["declined"]
    assert f"2026-11-02 not now on {card['suggestion']['title']}" in after.text


def test_a_reservation_the_app_set_aside_is_not_a_learner_answer(tmp_path, shown, no_network):
    paths, repository = _vault(tmp_path)
    card, lesson = _start(paths, repository)
    _today(_without(paths, lesson["learning_object_ids"]), repository, _clock(hours=2))  # set aside: expired
    responses = _rows(repository, "SELECT response FROM router_suggestion_responses ORDER BY responded_at, id")
    assert [row["response"] for row in responses] == ["accepted", "expired"]
    after = _card(paths, repository, "2026-11-03T09:00:00Z")
    assert [e["response"] for e in after.json["evidence_sections"][SUGGESTION_SECTION]] == ["accepted"]
    assert "expired" not in after.text and "set aside" not in after.text
