"""Adaptive hints H2a: the round-4 verify's item (docs/reviews/hints-h2a-codex-review.md, fix round 4).

A hint on the reference route (``book_way``, from the givens) names the
reference route and a target on it explicitly, whatever its kind: an empty
route or target is no exemption. Fakes only (no model is reached).
"""

from __future__ import annotations

import json

from learnloop.hints import service as S
from learnloop.hints.contracts import Target, check_output
from learnloop.hints.state import assemble_state
from learnloop.hints.writer import HintWriterOutputV1
from tests.hint_fakes import ITEM, WORK, assists, good_answer
from tests.test_hint_h2a_review_round2 import _ask, _setup


def _walkthrough(start: str, route: str, target: str, *, valid: bool = False):
    def answer(context):
        out = good_answer(context)
        # The placement is on the reference route at ``start``; the OUTPUT names ``route``.
        out["placement"] = {**out["placement"], "reached_node_id": start, "route_id": "r_ref", "stands_quote": "",
                            "work_matches_a_route": valid, "work_valid_so_far": valid}
        out["route_id"], out["target_node_id"] = route, target
        return out
    return answer


def _rounds(paths) -> list[dict]:
    return json.loads(assists(paths.sqlite_path)[-1]["contract_failures_json"])["rounds"]


def test_r4_an_answer_at_the_givens_with_no_route_fails_the_strict_recheck(tmp_path):
    """AT_GIVENS: the empty route reads as the reference's, but the strict
    from-givens recheck needs it named; the re-ask from the givens too."""

    paths, vault, repository = _setup(tmp_path)
    result, writer = _ask(vault, repository, "walkthrough@L5",
                          [_walkthrough("g", "", ""), _walkthrough("g", "", ""),
                           _walkthrough("g", "r_ref", "goal")], taken_level=5)
    rounds = _rounds(paths)
    assert "rule4_not_reference_route" in rounds[0]["from_givens_failures"]
    assert rounds[0]["switched_to"] == "from_givens"
    assert "rule4_not_reference_route" in rounds[1]["failures"]
    assert (result.status, result.kind, writer.calls) == (S.READY, "walkthrough", 3)
    row = assists(paths.sqlite_path)[-1]
    assert (row["route_id"], row["target_node_id"]) == ("r_ref", "goal")


def test_r4_a_from_givens_re_ask_needs_the_route_and_a_target_on_it(tmp_path):
    """FROM_GIVENS: placed off the givens, re-asked; the re-ask with the route
    but no target, then with no route, fails; a named route and target serves."""

    paths, vault, repository = _setup(tmp_path)
    result, writer = _ask(vault, repository, "walkthrough@L5",
                          [_walkthrough("cdf", "r_ref", "goal"), _walkthrough("g", "r_ref", ""),
                           _walkthrough("g", "r_ref", "goal")], taken_level=5)
    rounds = _rounds(paths)
    assert rounds[0]["switched_to"] == "from_givens"
    assert "rule4_target_not_on_reference_route" in rounds[1]["failures"]
    assert (result.status, writer.calls) == (S.READY, 3)
    assert assists(paths.sqlite_path)[-1]["target_node_id"] == "goal"


def test_r4_the_reference_route_rule_for_every_kind_and_no_map_unchanged(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    item = vault.practice_items[ITEM]
    state = assemble_state(vault, repository, item, session_id="s1", submission_id="k9", work_md=WORK)
    target = Target("walkthrough", 5, reference_route=True, from_givens=True, request="more")

    def output(route: str, node: str):
        payload = _walkthrough("g", route, node)({"chosen": {"kind": "walkthrough", "level": 5},
                                                  "learner_work": WORK, "approach_map": True})
        return HintWriterOutputV1.model_validate(payload)

    assert "rule4_not_reference_route" in check_output(output("", ""), target=target, state=state,
                                                       item=item).failures
    assert "rule4_not_reference_route" in check_output(output("new_route", "goal"), target=target, state=state,
                                                       item=item).failures
    assert "walkthrough_target_not_the_goal" in check_output(output("r_ref", "cdf"), target=target, state=state,
                                                             item=item).failures
    assert check_output(output("r_ref", "goal"), target=target, state=state, item=item).failures == []
    # Without a map the route rule does not apply (as before).
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from tests.hint_fakes import hint_vault

    bare = hint_vault(tmp_path / "no_map")
    bare_vault, bare_repository = load_vault(bare.root), Repository.attach(bare.sqlite_path)
    no_map = assemble_state(bare_vault, bare_repository, bare_vault.practice_items[ITEM], session_id="s1",
                            submission_id="k9", work_md=WORK)
    assert no_map.map is None
    assert "rule4_not_reference_route" not in check_output(output("", ""), target=target, state=no_map,
                                                           item=item).failures
