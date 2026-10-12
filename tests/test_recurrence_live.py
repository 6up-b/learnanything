"""Slice 2 T1 §3.2 and §3.7: the live same-cause judge, the K=3 escalation, the card."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.diagnosis.split.card import CardError, diagnosis_card, record_card_tap
from learnloop.recurrence import recurrence_key
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import FakeEmbeddingClient
from tests.recurrence_fakes import StatementFake, different, shares_word
from tests.split_live_helpers import append_config, at, drain_jobs, enable_embeddings, split_vault, submit

V_SAME = "Believes V and V transpose are the same matrix."
V_REWORDED = "Thinks the last SVD factor never needs transposing."
V_THIRD = "Writes V where the transpose of V belongs."
STATEMENTS = {"first": V_SAME, "second": V_REWORDED, "third": V_THIRD}


def _vault(tmp_path, *, version="mvp-0.11", config: str = ""):
    paths, _vault, repository = split_vault(tmp_path, version=version, seed=False, config=config)
    enable_embeddings(paths.root)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("dimensions = 4096", "dimensions = 16"), encoding="utf-8")
    return paths, load_vault(paths.root), repository


def _run(vault, repository, client, embedder, answers):
    results = []
    for offset, (item_id, answer) in enumerate(answers):
        result = submit(vault, repository, client, item_id=item_id, answer=answer, when=at(10 + 2 * offset))
        drain_jobs(vault, repository, client, embedding=embedder, judge_factory=lambda: client,
                   clock=FrozenClock(at(11 + 2 * offset)))
        results.append(result)
    return results


ANSWERS = [
    ("pi_svd_compute_001", "A = U Sigma V first"),
    ("pi_svd_compute_002", "B = U Sigma V second"),
    ("pi_svd_compute_001", "A = U Sigma V third"),
]


def _heads(repository, attempt_id):
    return [row for row in repository.causal_hypotheses_for_attempt(attempt_id)
            if row["status"] != "open_set" and row["cause_scope"] == "learner_state"]


def test_the_judge_merges_reworded_recurrences_and_the_third_escalates(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"), operators={"third": "worked_contrast"})
    embedder = FakeEmbeddingClient()
    first, second, third = _run(vault, repository, client, embedder, ANSWERS)

    assert client.judged, "the shortlisted earlier hypotheses reach the judge"
    with repository.connection() as connection:
        verdicts = connection.execute(
            "SELECT left_kind, right_kind, judge, verdict, prompt_version FROM judgment_ledger WHERE task = 'same_cause'"
        ).fetchall()
    assert verdicts and {tuple(row[:3]) for row in verdicts} == {("hypothesis", "hypothesis", "llm")}
    groups = repository.recurrence_group_map()
    keys = {recurrence_key(_heads(repository, result.attempt_id)[0], groups) for result in (first, second, third)}
    assert len(keys) == 1

    escalation = repository.recurrence_escalation(repository.current_live_diagnosis(third.attempt_id)["id"])
    assert escalation is not None and escalation["recurrence_count"] == 3
    assert escalation["earlier_attempt_ids"] == [second.attempt_id, first.attempt_id]
    assert escalation["different_approach"] is True and escalation["repair_operator"] == "worked_contrast"
    assert escalation["prior_operators"] == ["elicit_rule"]
    # Nothing escalates before the third time.
    assert repository.recurrence_escalation(repository.current_live_diagnosis(second.attempt_id)["id"]) is None

    card = diagnosis_card(vault, repository, third.attempt_id)
    block = card["escalation"]
    assert block["headline"] == "Third time with this one - trying a different approach"
    assert [row["attempt_id"] for row in block["earlier_answers"]] == [second.attempt_id, first.attempt_id]
    assert block["repair"]["operator"] == "worked_contrast" and block["approach_note"] is None
    assert [row["response"] for row in block["responses"]] == [
        "escalation:helped", "escalation:didnt_help", "escalation:not_sure",
    ]
    record_card_tap(vault, repository, attempt_id=third.attempt_id, diagnosis_id=card["diagnosis_id"],
                    response="escalation:helped")
    again = diagnosis_card(vault, repository, third.attempt_id)
    assert again["escalation"]["recorded_response"] == "escalation:helped"
    # The escalation tap is not the card's own diagnosis tap.
    assert again["recorded_response"] is None
    rows = repository.diagnosis_feedback_rows(card["diagnosis_id"])
    assert [row["response"] for row in rows] == ["escalation:helped"]


def test_the_same_repair_again_is_labelled_honestly(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"))
    *_rest, third = _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS)
    block = diagnosis_card(vault, repository, third.attempt_id)["escalation"]
    assert block["headline"] == "Third time with this one"
    assert block["different_approach"] is False and "same kind of repair" in block["approach_note"]


def test_a_judge_that_says_different_merges_nothing(tmp_path):
    """R1: shortlisted by embedding, rejected by the judge: no group, no escalation."""

    _paths, vault, repository = _vault(tmp_path)
    client = StatementFake(STATEMENTS, decide=different)
    results = _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS)
    assert client.judged
    assert repository.recurrence_group_map() == {}
    assert all(
        repository.recurrence_escalation(repository.current_live_diagnosis(result.attempt_id)["id"]) is None
        for result in results
    )


def test_the_judge_switch_and_the_embedding_switch_keep_the_judge_silent(tmp_path):
    _paths, vault, repository = _vault(tmp_path, config="[recurrence]\njudge_enabled = false")
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"))
    _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS)
    assert client.judged == [] and repository.recurrence_group_map() == {}


def test_a_validated_citation_merges_without_any_judge_call(tmp_path):
    _paths, vault, repository = _vault(tmp_path, config="[recurrence]\njudge_enabled = false")
    client = StatementFake(STATEMENTS, cite=True)
    first, second = _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS[:2])
    receipt = repository.diagnosis_context_receipt(repository.current_live_diagnosis(second.attempt_id)["id"])
    assert receipt["validated_citations"], "the fake's citation validated"
    groups = repository.recurrence_group_map()
    assert recurrence_key(_heads(repository, first.attempt_id)[0], groups) == recurrence_key(
        _heads(repository, second.attempt_id)[0], groups
    )
    members = repository.recurrence_groups()
    assert {row["joined_by"] for row in members} >= {"root", "citation"}


def test_a_not_the_same_mistake_tap_records_and_refreshes_without_blocking_a_citation(tmp_path):
    _paths, vault, repository = _vault(tmp_path, config="[recurrence]\njudge_enabled = false")
    client = StatementFake(STATEMENTS, cite=True)
    first, second = _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS[:2])
    card = diagnosis_card(vault, repository, second.attempt_id)
    record_card_tap(vault, repository, attempt_id=second.attempt_id, diagnosis_id=card["diagnosis_id"],
                    response="not_same_mistake", cited_attempt_id=first.attempt_id)
    # The learner's tap (authority 1) is logged against the diagnoser's
    # citation (authority 2) for the pair; the higher authority stands.
    groups = repository.recurrence_group_map()
    assert recurrence_key(_heads(repository, first.attempt_id)[0], groups) == recurrence_key(
        _heads(repository, second.attempt_id)[0], groups
    )


def test_escalation_ratings_need_an_escalation(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    client = StatementFake(STATEMENTS, decide=different)
    (first,) = _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS[:1])
    card = diagnosis_card(vault, repository, first.attempt_id)
    assert card["escalation"] is None
    with pytest.raises(CardError):
        record_card_tap(vault, repository, attempt_id=first.attempt_id, diagnosis_id=card["diagnosis_id"],
                        response="escalation:helped")


def test_below_the_successor_there_is_no_judge_and_no_escalation(tmp_path):
    _paths, vault, repository = _vault(tmp_path, version="mvp-0.10")
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"))
    results = _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS)
    assert client.judged == []
    assert repository.recurrence_group_map() == {} and repository.recurrence_escalations() == []
    assert diagnosis_card(vault, repository, results[-1].attempt_id)["escalation"] is None


def test_the_escalation_card_switch_hides_the_block(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"))
    *_rest, third = _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS)
    append_config(paths.root, "[recurrence]\nescalation_card_enabled = false")
    assert diagnosis_card(load_vault(paths.root), repository, third.attempt_id)["escalation"] is None



@pytest.mark.parametrize("decide, promoted", [(shares_word("transpos"), True), (different, False)])
def test_holding_pen_promotion_counts_a_merged_group_across_reworded_answers(tmp_path, decide, promoted):
    """Arm (b) needs two independent surfaces: two reworded answers on two
    items are one recurring belief only once the judge merged them."""

    _paths, vault, repository = _vault(tmp_path)
    client = StatementFake(STATEMENTS, decide=decide)
    _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS[:2])
    durable = repository.misconceptions_for_learning_object(
        "lo_svd_compute", statuses=("active", "resolving", "resolved")
    )
    assert bool(durable) is promoted
    if promoted:
        assert durable[0].promotion_reason == "independent_surface"


class ContinuingFake(StatementFake):
    """Claims an EXISTING hypothesis (by id), as the real diagnoser did live:
    the claim's ``hypothesis_ref`` is a prior hypothesis id and the event's
    ``prior_hypothesis_id`` names the same one. Two learner-state causes per
    event, so only that link can pick the diagnosed attempt's class."""

    def _diagnosis(self, request, context):
        from learnloop.ai.schemas import CandidateCause
        from learnloop.diagnosis.split.contract import Citation, PatternClaim

        result = super()._diagnosis(request, context)
        prior = [row for row in context.get("prior_hypotheses") or [] if row.get("statement") == V_SAME]
        history = context.get("history") or context.get("failure_history") or []
        failures = [row for row in history if row.get("outcome") == "non_pass" and row.get("first_divergence_quotes")]
        events = []
        for event in result.event_diagnoses:
            causes = [*event.candidate_causes, CandidateCause(statement="Confuses rows and columns.", cause_scope="learner_state", prior_weight=1.0)]
            events.append(event.model_copy(update={
                "candidate_causes": causes,
                "prior_hypothesis_id": prior[0]["id"] if prior else None,
            }))
        claims = [
            PatternClaim(
                hypothesis_ref=prior[0]["id"], relation="same_mechanism",
                cited=[Citation(attempt_id=failures[0]["attempt_id"], quote=failures[0]["first_divergence_quotes"][0])],
            )
        ] if prior and failures else []
        return result.model_copy(update={
            "event_diagnoses": events,
            "pattern_claims": claims,
            "evidence_attempt_ids": [row["attempt_id"] for row in failures[:1]],
        })


def test_a_citation_of_an_existing_hypothesis_resolves_through_prior_hypothesis_id(tmp_path):
    _paths, vault, repository = _vault(tmp_path, config="[recurrence]\njudge_enabled = false")
    client = ContinuingFake(STATEMENTS)
    first, second = _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS[:2])
    receipt = repository.diagnosis_context_receipt(repository.current_live_diagnosis(second.attempt_id)["id"])
    assert receipt["validated_citations"], "the existing-hypothesis citation validated"
    groups = repository.recurrence_group_map()
    first_key = recurrence_key(next(row for row in _heads(repository, first.attempt_id) if row["statement"] == V_SAME), groups)
    second_key = recurrence_key(next(row for row in _heads(repository, second.attempt_id) if row["statement"] == V_REWORDED), groups)
    assert first_key == second_key
    # The other learner-state cause of the diagnosed attempt is not dragged in.
    other = next(row for row in _heads(repository, second.attempt_id) if row["statement"] == "Confuses rows and columns.")
    assert recurrence_key(other, groups) != first_key
    assert not repository.recurrence_review("unresolved_link")
