"""The facet span-support check (owner decision 2026-10-13): fakes only, no network.

A model-proposed reword of a registered facet's meaning that cites explanatory
spans applies only when the Decider's top option over those spans and the new
wording is ``supports``; any other option, or no answer, holds it for the
owner's one-tap confirm with the verdict and the spans on the card. Exam-only
support is refused first; the owner's Library edits never reach the check. The
owner's confirm, keep and undo label the check's ledger row.
"""

from __future__ import annotations

import json

import pytest

from learnloop.ai.decisions import ChoiceAnswer, DecisionResult

from tests.test_tier1_decider import Decider, _no_decider, _rows


class SpanDecider(Decider):
    def __init__(self, choice):
        super().__init__()
        self.choice = choice

    def decide(self, state, questions, *, purpose):
        self.calls.append(state)
        assert purpose == "facet_span_support" and len(questions) == 1
        options = next(iter(questions.values())).options
        probabilities = {k: 0.7 if k == self.choice else 0.1 for k in options}
        # The choice field says supports; only the argmax counts.
        return DecisionResult({"verdict": ChoiceAnswer("supports", probabilities)}, self.model, 100, 0, 0.000002)


def _span_vault(tmp_path, monkeypatch, client, *, role="primary_textbook", text="SVD expresses A = U Sigma V^T."):
    from learnloop import decider_judgments as tier1
    from tests.test_facet_identity_actions import _vault_with_duplicate
    from tests.test_facet_reword_confirm import _seed

    paths, _vault, repo = _vault_with_duplicate(tmp_path)
    citation = _seed(paths, repo, role, "cited", text=text)
    monkeypatch.setattr(tier1, "client_for", (lambda *a: client) if client is not None else _no_decider)
    return paths, repo, citation


def _apply_cited_reword(paths, repo, citation):
    from learnloop.content.proposals.patches import apply_accepted_items
    from tests.test_facet_identity_actions import SHARED
    from tests.test_facet_reword_confirm import _proposal, _support
    from tests.test_facet_rewords import NEW_CLAIM

    patch_id = _proposal(repo, {"id": SHARED, "claim": NEW_CLAIM, "meaning_support": _support(citation)})
    apply_accepted_items(paths.root, patch_id)


@pytest.mark.parametrize("choice", ["supports", "partly supports", "does not support", "unrelated", None])
def test_span_support_applies_only_on_supports_else_the_card_shows_verdict_and_span(tmp_path, monkeypatch, choice):
    from learnloop.content.facet_identity import actions
    from learnloop.vault.loader import load_vault
    from tests.test_facet_identity_actions import SHARED
    from tests.test_facet_rewords import NEW_CLAIM, _entry

    client = SpanDecider(choice) if choice else None
    paths, repo, citation = _span_vault(tmp_path, monkeypatch, client)
    before = _entry(paths, SHARED)["claim"]
    _apply_cited_reword(paths, repo, citation)
    pending = actions.pending_reword_confirms(repo, load_vault(paths.root))
    (check,) = _rows(repo, "facet_span_support")
    assert check["judge"] == "decider" and check["left_id"] == SHARED
    if client is not None:
        (state,) = client.calls
        assert [span["text"] for span in state["spans"]] == ["SVD expresses A = U Sigma V^T."]
        assert state["new_wording"]["claim"] == NEW_CLAIM
        assert set(json.loads(check["rationale"])["probabilities"]) == {
            "supports", "partly supports", "does not support", "unrelated"}
    if choice == "supports":
        assert not pending and _entry(paths, SHARED)["claim"] == NEW_CLAIM
        return
    assert _entry(paths, SHARED)["claim"] == before  # held, not written
    (card,) = pending
    assert card["span_support"]["verdict"] == choice
    assert card["span_support"]["status"] == ("ok" if choice else "unavailable")
    assert card["span_support"]["judgment_id"] == check["id"]
    assert card["sources"][0]["excerpt"] == "SVD expresses A = U Sigma V^T."
    assert "confirm" in card["message"]


def test_the_owners_confirm_and_undo_label_the_check(tmp_path, monkeypatch):
    from learnloop.content.facet_identity import actions
    from learnloop.vault.loader import load_vault
    from tests.test_facet_identity_actions import SHARED
    from tests.test_facet_rewords import NEW_CLAIM, _entry

    paths, repo, citation = _span_vault(tmp_path, monkeypatch, SpanDecider("partly supports"))
    _apply_cited_reword(paths, repo, citation)
    (card,) = actions.pending_reword_confirms(repo, load_vault(paths.root))
    actions.confirm_reword(paths.root, repo, card["action_id"])
    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM
    actions.undo_action(paths.root, repo, card["action_id"])
    labels = [row for row in _rows(repo, "facet_span_support") if row["judge"] == "owner"]
    assert [row["verdict"] for row in labels] == ["supports", "does not support"]
    check = card["span_support"]["judgment_id"]
    assert [json.loads(row["rationale"])["label_for"] for row in labels] == [check, check]
    assert [json.loads(row["rationale"])["origin"] for row in labels] == ["confirm", "undo"]


def test_the_owners_undo_of_a_reword_the_check_let_apply_labels_it(tmp_path, monkeypatch):
    """A "supports" check applies the reword at once; the owner's undo is the label that says otherwise."""

    from learnloop.content.facet_identity import actions
    from tests.test_facet_identity_actions import SHARED
    from tests.test_facet_rewords import NEW_CLAIM, _entry

    paths, repo, citation = _span_vault(tmp_path, monkeypatch, SpanDecider("supports"))
    before = _entry(paths, SHARED)["claim"]
    _apply_cited_reword(paths, repo, citation)
    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM
    (check,) = _rows(repo, "facet_span_support")
    (record,) = [row for row in actions.list_actions(repo, limit=None)
                 if row["action"] == "reword" and row["survivor_facet_id"] == SHARED]
    assert record["detail"]["span_support"]["judgment_id"] == check["id"]
    actions.undo_action(paths.root, repo, record["id"])
    assert _entry(paths, SHARED)["claim"] == before
    (label,) = [row for row in _rows(repo, "facet_span_support") if row["judge"] == "owner"]
    assert label["verdict"] == "does not support" and label["input_hash"] == check["input_hash"]
    assert json.loads(label["rationale"])["label_for"] == check["id"]


def test_the_check_reads_each_cited_span_once(tmp_path, monkeypatch):
    from learnloop.content.facet_identity import authority
    from learnloop.vault.loader import load_vault
    from tests.test_facet_identity_actions import SHARED
    from tests.test_facet_rewords import NEW_CLAIM, _entry

    client = SpanDecider("supports")
    paths, repo, citation = _span_vault(tmp_path, monkeypatch, client)
    vault = load_vault(paths.root, load_environment=False)
    before = _entry(paths, SHARED)
    resolver = authority.CitationResolver.for_vault(repo, vault).with_span_support(vault, repo)
    twice = [*authority.contributions([citation], label="first"), *authority.contributions([citation], label="second")]
    verdict = authority.check_meaning_write(SHARED, before=before, after={**before, "claim": NEW_CLAIM},
                                            registered=True, contributions=twice, resolver=resolver)
    assert verdict.allowed and verdict.span_support["verdict"] == "supports"
    (state,) = client.calls
    assert len(state["spans"]) == 1


def test_keeping_the_current_wording_labels_the_check_does_not_support(tmp_path, monkeypatch):
    from learnloop.content.facet_identity import actions
    from learnloop.vault.loader import load_vault

    paths, repo, citation = _span_vault(tmp_path, monkeypatch, None)
    _apply_cited_reword(paths, repo, citation)
    (card,) = actions.pending_reword_confirms(repo, load_vault(paths.root))
    actions.keep_current_wording(paths.root, repo, card["action_id"])
    (label,) = [row for row in _rows(repo, "facet_span_support") if row["judge"] == "owner"]
    assert label["verdict"] == "does not support"


def test_exam_only_support_is_refused_before_the_decider_and_the_owner_edit_bypasses_it(tmp_path, monkeypatch):
    from learnloop import decider_judgments as tier1
    from learnloop.content.facet_identity import authority
    from learnloop.vault.loader import load_vault
    from tests.test_facet_identity_actions import SHARED, _vault_with_duplicate
    from tests.test_facet_reword_confirm import _seed
    from tests.test_facet_rewords import NEW_CLAIM, _entry

    paths, _, repo = _vault_with_duplicate(tmp_path)
    citation = _seed(paths, repo, "exam", "exam", text="Never send this exam")
    vault = load_vault(paths.root, load_environment=False)
    monkeypatch.setattr(tier1, "client_for", lambda *a: pytest.fail("exam/owner must not call the Decider"))
    resolver = authority.CitationResolver.for_vault(repo, vault).with_span_support(vault, repo)
    before = _entry(paths, SHARED)
    after = {**before, "claim": NEW_CLAIM}
    verdict = authority.check_meaning_write(SHARED, before=before, after=after, registered=True,
                                            contributions=authority.contributions([citation]), resolver=resolver)
    assert verdict.code == "exam_authority" and not verdict.confirmable
    owner = authority._check_basis(SHARED, before, after, authority.OwnerEdit("owner-receipt"), {SHARED: before},
                                   resolver)
    assert owner.allowed and owner.code == "owner"
    assert not _rows(repo, "facet_span_support")


def test_only_a_registered_facets_meaning_is_checked(tmp_path, monkeypatch):
    """An in-run join (a candidate, not a registered facet) and a worked example never ask."""

    from learnloop import decider_judgments as tier1
    from learnloop.content.facet_identity import authority
    from learnloop.vault.loader import load_vault
    from tests.test_facet_identity_actions import SHARED, _vault_with_duplicate
    from tests.test_facet_reword_confirm import _seed
    from tests.test_facet_rewords import NEW_CLAIM, _entry

    paths, _, repo = _vault_with_duplicate(tmp_path)
    citation = _seed(paths, repo, "primary_textbook", "text", text="SVD.")
    vault = load_vault(paths.root, load_environment=False)
    monkeypatch.setattr(tier1, "client_for", lambda *a: pytest.fail("no span check expected"))
    resolver = authority.CitationResolver.for_vault(repo, vault).with_span_support(vault, repo)
    before = _entry(paths, SHARED)
    support = authority.contributions([citation])
    joined = authority.check_meaning_write(SHARED, before=before, after={**before, "claim": NEW_CLAIM},
                                           registered=False, contributions=support, resolver=resolver)
    example = authority.check_meaning_write(
        SHARED, before=before, after={**before, "positive_examples": [*before["positive_examples"], "A 3x3 SVD"]},
        registered=True, contributions=support, resolver=resolver)
    assert joined.allowed and example.allowed
    # A resolver for synthesis, an undo or a confirm carries no check at all.
    plain = authority.CitationResolver.for_vault(repo, vault)
    assert plain.span_checker is None
    assert authority.check_meaning_write(SHARED, before=before, after={**before, "claim": NEW_CLAIM},
                                         registered=True, contributions=support, resolver=plain).allowed


def test_the_span_switch_restores_the_cited_reword_and_reword_confirm_off_refuses(tmp_path, monkeypatch):
    from learnloop.content.facet_identity import authority
    from learnloop.vault.loader import load_vault
    from tests.test_facet_identity_actions import SHARED
    from tests.test_facet_rewords import NEW_CLAIM, _entry

    paths, repo, citation = _span_vault(tmp_path, monkeypatch, SpanDecider("does not support"))
    vault = load_vault(paths.root, load_environment=False)
    before = _entry(paths, SHARED)
    support = authority.contributions([citation])
    vault.config.decider_routes.facet_span_support = False
    off = authority.CitationResolver.for_vault(repo, vault).with_span_support(vault, repo)
    assert authority.check_meaning_write(SHARED, before=before, after={**before, "claim": NEW_CLAIM},
                                         registered=True, contributions=support, resolver=off).allowed
    assert not _rows(repo, "facet_span_support")
    vault.config.decider_routes.facet_span_support = True
    on = authority.CitationResolver.for_vault(repo, vault).with_span_support(vault, repo)
    refused = authority.check_meaning_write(SHARED, before=before, after={**before, "claim": NEW_CLAIM},
                                            registered=True, contributions=support, resolver=on,
                                            policy=authority.EXPLANATORY_ONLY)
    # With the reword confirm switched off nothing can hold it: refused, not applied.
    assert not refused.allowed and not refused.confirmable and refused.code == "span_support"
