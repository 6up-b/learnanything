"""Supplementary labels for the v2 arms' new candidates: which units count as
new, blinded passes, mandatory audits, malformed sets, merging. Fakes only."""
from __future__ import annotations

from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings.bank import BankQuestion, QuestionLabels
from learnloop.experiments.contextual_embeddings.callers import FakeRoleCaller
from learnloop.experiments.contextual_embeddings.e1 import supplement as S
from tests.e0_fakes import build_e0_vault
from tests.e1_fakes import _context, refs_in


def _setup(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    units = [unit.unit_id for unit in snapshot.units]
    question = BankQuestion("q1", "development", "fam", "writer", "explain", "reader_deictic",
                            "Why does the span of a list of vectors form a subspace?", ())
    from learnloop.experiments.contextual_embeddings.bank import freeze_context

    freeze_context(question, snapshot)
    labels = QuestionLabels("q1", units[:3], [{}, {}], [[], []], [False, False],
                            final={units[0]: "required", units[1]: "unrelated", units[2]: "helpful"},
                            final_sets=[frozenset({units[0]})], answerable=True)
    return snapshot, units, question, labels


def test_only_unjudged_units_in_a_v2_top_ten_are_new(tmp_path):
    _snapshot, units, question, labels = _setup(tmp_path)
    rankings = {"V2_grouped": {"q1": [units[0], units[3], units[4]] + units[5:20]},
                "V2_singleton": {"q1": [units[4], units[1], units[5]]}}
    found = S.new_candidates(question, labels, rankings)
    assert units[0] not in found and units[1] not in found and found[:3] == [units[3], units[4], units[5]]
    assert len(found) == len(set(found)) and all(unit in units[3:13] for unit in found)
    labels.unresolved = True
    assert S.new_candidates(question, labels, rankings) == []


def _respond(sets_by_role):
    """Each pass labels the candidate whose text sorts first ``required`` and
    the rest ``background``; refs are passed sorted by text, so both passes
    (which see different orders and refs) name the same units."""

    def respond(role, prompt, model):
        context = _context(prompt)
        if model.__name__ == "SupplementPass":
            candidates = [item["ref"] for item in sorted(context["candidates"], key=lambda item: item["text"])]
            judged = [item["ref"] for item in sorted(context["judged"], key=lambda item: item["text"])]
            return {"labels": [{"ref": ref, "relevance": "required" if index == 0 else "background"}
                               for index, ref in enumerate(candidates)],
                    "new_sets": sets_by_role(role, candidates, judged)}
        return {"labels": [{"ref": item["ref"], "relevance": context["pass_1"].get(item["ref"]) or "unrelated"}
                           for item in context["candidates"]], "new_sets": context["pass_1_sets"],
                "unresolved": False}

    return respond


def test_passes_are_blinded_new_sets_are_audited_and_merged(tmp_path):
    snapshot, units, question, labels = _setup(tmp_path)
    caller = FakeRoleCaller(_respond(lambda _role, candidates, judged: [[candidates[0], judged[0]]]),
                            role_pins=S.E1_ROLE_PINS)
    new = [units[3], units[4]]
    outcome = S.supplement_all(snapshot, [question], {"q1": labels}, {"V2_grouped": {"q1": new}}, caller)
    item = outcome["items"]["q1"]
    roles = [role for role, _prompt in caller.calls]
    assert roles == ["label_a", "label_b", "adjudicator"]
    # Blinded: no arm, rank or score in any prompt; judged support shown with its final label.
    for _role, prompt in caller.calls:
        assert "V2_grouped" not in prompt and "rank" not in prompt.lower()
        assert set(refs_in(prompt)) >= {"n1", "n2"}
    assert item.audit_reason == "new_set_used_by_primary_endpoint" and item.adjudicated and not item.unresolved
    counts = S.merge(snapshot, [question], {"q1": labels}, outcome["items"])
    assert counts["sets_added"] == 1 and counts["labels_added"] == 2
    assert sorted(labels.final[unit] for unit in new) == ["background", "required"]
    assert len(labels.final_sets) == 2 and labels.answerable and len(question.evidence_sets) == 2
    assert outcome["agreement"]["agreement"]["n"] == 2


def test_a_set_without_a_new_candidate_or_with_a_background_member_is_malformed(tmp_path):
    snapshot, units, question, labels = _setup(tmp_path)
    caller = FakeRoleCaller(_respond(lambda role, candidates, judged: [[judged[0]]] if role == "label_a"
                                     else [[candidates[1]]]), role_pins=S.E1_ROLE_PINS)
    outcome = S.supplement_all(snapshot, [question], {"q1": labels}, {"V2_grouped": {"q1": [units[3], units[4]]}},
                               caller)
    item = outcome["items"]["q1"]
    assert item.malformed == [1, 1] and item.pass_sets == [[], []]
    assert item.audit_reason == "set_disagreement"


def test_an_unresolved_verdict_leaves_the_new_candidates_unknown(tmp_path):
    snapshot, units, question, labels = _setup(tmp_path)

    def respond(role, prompt, model):
        if model.__name__ == "SupplementVerdict":
            return {"labels": [], "new_sets": [], "unresolved": True}
        return _respond(lambda _r, candidates, _j: [[candidates[0]]])(role, prompt, model)

    outcome = S.supplement_all(snapshot, [question], {"q1": labels}, {"V2_grouped": {"q1": [units[3]]}},
                               FakeRoleCaller(respond, role_pins=S.E1_ROLE_PINS))
    before = dict(labels.final)
    counts = S.merge(snapshot, [question], {"q1": labels}, outcome["items"])
    assert counts["unresolved_left_unknown"] == 1 and labels.final == before and len(labels.final_sets) == 1


def test_the_e1_roles_are_e0s_metered_messages_api_pins_with_e1_prompt_versions():
    from learnloop.experiments.contextual_embeddings import pins

    for role, pin in S.E1_ROLE_PINS.items():
        e0 = pins.ROLE_PINS[role]
        assert (pin.model, pin.transport, pin.billing, pin.max_output_tokens) == (
            e0.model, e0.transport, e0.billing, e0.max_output_tokens)
        assert pin.prompt_version.startswith("e1-") and pin.price_verified.verified
    assert S.RELEVANCE_RUBRIC in S.SUPPLEMENT_INSTRUCTIONS
