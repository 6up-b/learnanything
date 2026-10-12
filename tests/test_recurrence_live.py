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
    # The diagnosis's own repair already differs: nothing else is requested.
    assert escalation["repair_source"] == "diagnosis" and client.escalation_requests == []
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


def test_identical_repairs_three_times_obtain_a_different_one_at_escalation(tmp_path):
    """Review F9 / §3.7: every diagnosis suggests ``elicit_rule``; the third
    answer's escalation ASKS for a different operator and representation,
    given what was shown, and shows it."""

    _paths, vault, repository = _vault(tmp_path)
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"), escalation_operator="worked_contrast")
    first, second, third = _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS)
    shown = {
        repair["operator"]
        for result in (first, second, third)
        for repair in (repository.fetch_attempt_feedback_metadata(result.attempt_id) or {}).get("repair_suggestions") or []
    }
    assert shown == {"elicit_rule"}, "the diagnoser suggested the same repair every time"
    (request,) = client.escalation_requests
    assert {row["operator"] for row in request["earlier_repairs"]} == {"elicit_rule"}
    assert {row["operator"] for row in request["current_repairs"]} == {"elicit_rule"}
    escalation = repository.recurrence_escalation(repository.current_live_diagnosis(third.attempt_id)["id"])
    assert escalation["repair_source"] == "generated" and escalation["different_approach"] is True
    assert escalation["repair_operator"] == "worked_contrast" and escalation["repair"]["representation"] == "worked contrast"
    assert escalation["generation"]["status"] == "used"
    with repository.connection() as connection:
        receipted = {row[0] for row in connection.execute(
            "SELECT purpose FROM model_call_receipts WHERE owner_kind = 'attempt_diagnosis' AND owner_id = ? "
            "AND parent_call_id IS NULL", (third.attempt_id,),
        )}
    assert "recurrence_escalation_repair" in receipted, "the request is receipted under the attempt"
    block = diagnosis_card(vault, repository, third.attempt_id)["escalation"]
    assert block["headline"] == "Third time with this one - trying a different approach"
    assert block["repair"]["operator"] == "worked_contrast" and block["repair_source"] == "generated"
    assert block["approach_note"] is None


@pytest.mark.parametrize(
    "kwargs, config, status",
    [
        ({}, "", "same_operator"),  # the model repeats the operator: refused, not shown as new
        ({"fail_purposes": ("recurrence_escalation_repair",)}, "", "failed"),
        ({"escalation_operator": "worked_contrast"}, "[recurrence]\nescalation_repair_enabled = false", "disabled"),
    ],
)
def test_the_same_repair_again_is_labelled_honestly(tmp_path, kwargs, config, status):
    _paths, vault, repository = _vault(tmp_path, config=config)
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"), **kwargs)
    *_rest, third = _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS)
    escalation = repository.recurrence_escalation(repository.current_live_diagnosis(third.attempt_id)["id"])
    assert escalation["generation"]["status"] == status and escalation["repair_source"] == "diagnosis"
    block = diagnosis_card(vault, repository, third.attempt_id)["escalation"]
    assert block["headline"] == "Third time with this one"
    assert block["different_approach"] is False and "same kind of repair" in block["approach_note"]
    # Asked once unless switched off; nothing new is ever shown as new.
    assert ("recurrence_escalation_repair" in client.calls) is (status != "disabled")


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
    # The learner's tap (authority 1) is below the diagnoser's citation
    # (authority 2) for the pair, so the citation stands and no union is
    # refused (no review row). The tap itself stays in diagnosis_feedback,
    # where the M3 report counts it (group precision).
    groups = repository.recurrence_group_map()
    assert recurrence_key(_heads(repository, first.attempt_id)[0], groups) == recurrence_key(
        _heads(repository, second.attempt_id)[0], groups
    )
    assert repository.recurrence_review("refused_union") == []
    assert [row["response"] for row in repository.diagnosis_feedback_rows(card["diagnosis_id"])] == ["not_same_mistake"]


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

    # The learner's "not the same mistake" on that citation is about THIS
    # answer's cause and the cited answer's: one learner_card "different"
    # between the two classes, not one inside the cited class.
    from learnloop.recurrence import normalize_statement
    from learnloop.substrate.recurrence_groups import compute_groups

    card = diagnosis_card(vault, repository, second.attempt_id)
    record_card_tap(vault, repository, attempt_id=second.attempt_id, diagnosis_id=card["diagnosis_id"],
                    response="not_same_mistake", cited_attempt_id=first.attempt_id)
    with repository.connection() as connection:
        taps = [row for row in compute_groups(connection).labelled if row["judge"] == "learner_card"]
    assert [(row["left_class"], row["right_class"], row["verdict"]) for row in taps] == [
        (normalize_statement(V_REWORDED), normalize_statement(V_SAME), "different")
    ]
    assert not repository.recurrence_review("exact_key_conflict")


# -- the enclosing command's spend controls (review F1) ------------------------------------


def _third_queued(tmp_path, **fake):
    from datetime import timedelta

    _paths, vault, repository = _vault(tmp_path)
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"), **fake)
    embedder = FakeEmbeddingClient()
    _run(vault, repository, client, embedder, ANSWERS[:2])
    third = submit(vault, repository, client, item_id=ANSWERS[2][0], answer=ANSWERS[2][1], when=at(14))
    return vault, repository, client, embedder, third, FrozenClock(at(15) + timedelta(minutes=1))


def _drain_on(vault, repository, client, embedder, spend, clock, cancelled=None):
    from learnloop.diagnosis.split.jobs import DIAGNOSE_KIND, drain

    return drain(
        vault, repository, owner="cli", kinds=(DIAGNOSE_KIND,), client_factory=lambda: client,
        embedding_factory=lambda: embedder, judge_factory=lambda: client, spend=spend, cancelled=cancelled,
        clock=clock,
    )


def test_the_dry_run_plans_the_recurrence_work_on_the_same_caps(tmp_path):
    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.split.jobs import command_spend, plan_diagnosis_jobs

    vault, repository, client, embedder, _third, _clock = _third_queued(tmp_path)
    caps = SpendCaps(max_candidates=50, max_pairs=0, max_retries=5, max_calls=50, max_total_tokens=1_000_000, max_estimated_usd=1.0)
    plan = plan_diagnosis_jobs(vault, repository, spend=command_spend(vault, caps))
    recurrence = plan["recurrence"]
    assert recurrence["by_part"]["judge"]["calls"] == vault.config.recurrence.judge_max_pairs_per_attempt
    assert recurrence["by_part"]["embedding"]["calls"] == 1 and recurrence["by_part"]["escalation_repair"]["calls"] == 1
    assert recurrence["routes"]["judge"]["billing"] == "subscription" and recurrence["fits"] is True
    tight = SpendCaps(max_candidates=50, max_pairs=0, max_retries=5, max_calls=plan["calls"], max_total_tokens=1_000_000,
                      max_estimated_usd=1.0)
    assert plan_diagnosis_jobs(vault, repository, spend=command_spend(vault, tight))["recurrence"]["fits"] is False


def test_the_judge_runs_on_the_commands_budget_and_shows_in_its_summary(tmp_path):
    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.split.jobs import command_spend

    vault, repository, client, embedder, third, clock = _third_queued(tmp_path)
    before = len(client.judged)
    caps = SpendCaps(max_candidates=50, max_pairs=0, max_retries=5, max_calls=50, max_total_tokens=1_000_000, max_estimated_usd=1.0)
    spend = command_spend(vault, caps)
    outcomes = _drain_on(vault, repository, client, embedder, spend, clock)
    assert [outcome.state for outcome in outcomes] == ["done"]
    judged = len(client.judged) - before
    assert judged >= 1
    routes = spend.summary()["routes"]
    assert routes["same_cause_judge"]["calls"] == judged, "the judge calls are the command's"
    assert spend.budget.used.calls <= caps.max_calls
    with repository.connection() as connection:
        owners = {row[0] for row in connection.execute(
            "SELECT owner_id FROM model_call_receipts WHERE purpose = 'same_cause_judgment' AND parent_call_id IS NULL"
        )}
    assert third.attempt_id in owners, "receipted under the attempt they judged for"


def test_an_exhausted_command_budget_stops_the_judge(tmp_path):
    """The command's caps fit its diagnosis and nothing more: the recurrence
    step must not open a fresh budget of its own."""

    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.split.jobs import command_spend, plan_diagnosis_jobs

    vault, repository, client, embedder, _third, clock = _third_queued(tmp_path)
    before, embeds = len(client.judged), embedder.calls
    big = SpendCaps(max_candidates=50, max_pairs=0, max_retries=5, max_calls=50, max_total_tokens=1_000_000, max_estimated_usd=1.0)
    plan = plan_diagnosis_jobs(vault, repository, spend=command_spend(vault, big))
    needed = plan["calls"] + ((plan.get("retrieval") or {}).get("calls") or 0)
    caps = SpendCaps(max_candidates=50, max_pairs=0, max_retries=5, max_calls=needed, max_total_tokens=1_000_000,
                     max_estimated_usd=1.0)
    spend = command_spend(vault, caps)
    outcomes = _drain_on(vault, repository, client, embedder, spend, clock)
    assert [outcome.state for outcome in outcomes] == ["done"]
    assert len(client.judged) == before, "no judge call past the command's caps"
    assert spend.budget.used.calls <= caps.max_calls
    assert embedder.calls - embeds <= max(0, needed - plan["calls"])


def test_a_cancelled_command_stops_the_judge(tmp_path):
    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.split.jobs import command_spend

    flag = {"stop": False}

    def on_diagnosis(answer):
        flag["stop"] = flag["stop"] or "third" in answer

    vault, repository, client, embedder, _third, clock = _third_queued(tmp_path, on_diagnosis=on_diagnosis)
    before = len(client.judged)
    caps = SpendCaps(max_candidates=50, max_pairs=0, max_retries=5, max_calls=50, max_total_tokens=1_000_000, max_estimated_usd=1.0)
    spend = command_spend(vault, caps, cancelled=lambda: flag["stop"])
    outcomes = _drain_on(vault, repository, client, embedder, spend, clock, cancelled=lambda: flag["stop"])
    assert [outcome.state for outcome in outcomes] == ["done"], "the diagnosis that was already paid completes"
    assert len(client.judged) == before, "cancellation reaches the recurrence step"


# -- second review: what the K=3 count counts, and what a hidden card pays for ------------


def _answer(vault, repository, client, embedder, offset, answer):
    result = submit(vault, repository, client, item_id=answer[0], answer=answer[1], when=at(10 + 2 * offset))
    drain_jobs(vault, repository, client, embedding=embedder, judge_factory=lambda: client,
               clock=FrozenClock(at(11 + 2 * offset)))
    return result


def _with_status(repository, head, status):
    """Append a new version of an episode head with another status (a refutation)."""

    repository.append_causal_hypothesis(
        episode_key=str(head["episode_key"]), attempt_id=str(head["attempt_id"]),
        learning_object_id=str(head["learning_object_id"]), cause_scope=str(head["cause_scope"]),
        statement=str(head["statement"]), statement_normalized=str(head["statement_normalized"]),
        error_event_id=head.get("error_event_id"), mechanism=head.get("mechanism"), operation=head.get("operation"),
        target_ref=head.get("target_ref"), evidence=head.get("evidence"), status=status,
    )


@pytest.mark.parametrize("status", ["retired", "demoted"])
def test_a_refuted_earlier_cause_does_not_count_toward_the_escalation(tmp_path, status):
    """Second review F8: an earlier answer whose cause was rejected (its head
    retired or demoted) is not a recurrence of it."""

    _paths, vault, repository = _vault(tmp_path)
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"), operators={"third": "worked_contrast"})
    embedder = FakeEmbeddingClient()
    first, _second = (_answer(vault, repository, client, embedder, offset, answer) for offset, answer in enumerate(ANSWERS[:2]))
    _with_status(repository, _heads(repository, first.attempt_id)[0], status)
    third = _answer(vault, repository, client, embedder, 2, ANSWERS[2])
    diagnosis = repository.current_live_diagnosis(third.attempt_id)
    assert repository.recurrence_escalation(diagnosis["id"]) is None, "two live recurrences are not three"


def test_a_content_scoped_cause_in_the_group_does_not_count_toward_the_escalation(tmp_path):
    """Second review F8: only learner-state heads count. An item-defect cause
    of an earlier answer, even with the same statement, is not a recurrence
    of the learner's belief."""

    _paths, vault, repository = _vault(tmp_path)
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"), operators={"third": "worked_contrast"})
    embedder = FakeEmbeddingClient()
    first, _second = (_answer(vault, repository, client, embedder, offset, answer) for offset, answer in enumerate(ANSWERS[:2]))
    head = _heads(repository, first.attempt_id)[0]
    repository.append_causal_hypothesis(
        episode_key=f"{head['episode_key']}:content", attempt_id=str(head["attempt_id"]),
        learning_object_id=str(head["learning_object_id"]), cause_scope="item_contract",
        statement=str(head["statement"]), statement_normalized=str(head["statement_normalized"]),
        target_ref=head.get("target_ref"), status="candidate",
    )
    _with_status(repository, head, "retired")
    third = _answer(vault, repository, client, embedder, 2, ANSWERS[2])
    diagnosis = repository.current_live_diagnosis(third.attempt_id)
    assert repository.recurrence_escalation(diagnosis["id"]) is None


def test_a_hidden_escalation_card_pays_for_no_escalated_repair(tmp_path):
    """Second review F9: with the card switched off nobody sees the repair,
    so none is requested; the receipt still records the recurrence."""

    _paths, vault, repository = _vault(tmp_path, config="[recurrence]\nescalation_card_enabled = false")
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"), escalation_operator="worked_contrast")
    *_rest, third = _run(vault, repository, client, FakeEmbeddingClient(), ANSWERS)
    assert "recurrence_escalation_repair" not in client.calls
    escalation = repository.recurrence_escalation(repository.current_live_diagnosis(third.attempt_id)["id"])
    assert escalation is not None and escalation["repair_source"] == "diagnosis"
    assert escalation["generation"]["status"] == "card_disabled"


def test_a_hidden_escalation_card_plans_no_escalated_repair(tmp_path):
    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.split.jobs import command_spend, plan_diagnosis_jobs

    vault, repository, *_rest = _third_queued(tmp_path)
    append_config(vault.root, "[recurrence]\nescalation_card_enabled = false")
    vault = load_vault(vault.root)
    caps = SpendCaps(max_candidates=50, max_pairs=0, max_retries=5, max_calls=50, max_total_tokens=1_000_000, max_estimated_usd=1.0)
    plan = plan_diagnosis_jobs(vault, repository, spend=command_spend(vault, caps))
    assert plan["recurrence"]["by_part"]["escalation_repair"]["calls"] == 0


# -- second review F7: T1 work never outlives the diagnose job's lease --------------------


class _MovingClock:
    def __init__(self, start):
        self.value = start

    def now(self):
        return self.value


class _SlowJudge(StatementFake):
    """Each judge call takes ``seconds`` on ``clock``; ``on_escalation`` runs
    when the escalated repair is requested (what another worker would see)."""

    def __init__(self, *args, clock, seconds, on_judge=None, on_escalation=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.clock, self.seconds = clock, seconds
        self.on_judge, self.on_escalation = on_judge, on_escalation

    def _same_cause_judgment(self, request, context):
        from datetime import timedelta

        self.clock.value += timedelta(seconds=self.seconds)
        if self.on_judge is not None:
            self.on_judge()
        return super()._same_cause_judgment(request, context)

    def _recurrence_escalation_repair(self, request, context):
        if self.on_escalation is not None:
            self.on_escalation()
        return super()._recurrence_escalation_repair(request, context)


def _third_with_slow_judge(tmp_path, *, seconds, on_judge=None, on_escalation=None):
    _paths, vault, repository = _vault(tmp_path)
    clock = _MovingClock(at(15))
    client = _SlowJudge(STATEMENTS, decide=shares_word("transpos"), escalation_operator="worked_contrast",
                        clock=clock, seconds=0)
    embedder = FakeEmbeddingClient()
    _run(vault, repository, client, embedder, ANSWERS[:2])
    third = submit(vault, repository, client, item_id=ANSWERS[2][0], answer=ANSWERS[2][1], when=at(14))
    client.seconds, client.on_judge, client.on_escalation = seconds, on_judge, on_escalation
    return vault, repository, client, embedder, third, clock


def test_slow_judging_renews_the_lease_so_no_second_worker_repeats_the_paid_repair(tmp_path):
    """Two judge calls of 700 s each outlast the 1,200 s lease taken before the
    diagnosis. The lease is renewed before every paid call, so when the
    escalated repair is requested no other worker can take the job."""

    from learnloop.diagnosis.split.jobs import DIAGNOSE_KIND, DIAGNOSE_LEASE_SECONDS

    seen: dict[str, object] = {}
    holder: dict[str, object] = {}

    def other_worker_tries():
        seen["stolen"] = holder["repository"].lease_next_post_attempt_job(
            kind=DIAGNOSE_KIND, owner="sidecar", lease_seconds=DIAGNOSE_LEASE_SECONDS, clock=holder["clock"],
        )

    vault, repository, client, embedder, third, clock = _third_with_slow_judge(
        tmp_path, seconds=700, on_escalation=other_worker_tries,
    )
    holder.update(repository=repository, clock=clock)
    judged_before = len(client.judged)
    outcomes = drain_jobs(vault, repository, client, embedding=embedder, judge_factory=lambda: client, clock=clock)
    assert len(client.judged) - judged_before >= 2, "the slow judge ran twice (1,400 s)"
    assert len(client.escalation_requests) == 1
    assert seen["stolen"] is None, "the job's lease was still held when the repair was requested"
    assert [outcome.state for outcome in outcomes if outcome.kind == DIAGNOSE_KIND] == ["done"]


def test_a_lost_lease_stops_the_t1_calls_of_the_old_worker(tmp_path):
    """Another worker took the job while the first was judging: the first
    makes no further paid call (its judge stops, no escalated repair)."""

    from datetime import timedelta

    from learnloop.diagnosis.split.jobs import DIAGNOSE_KIND, DIAGNOSE_LEASE_SECONDS

    holder: dict[str, object] = {}

    def steal():
        if holder.get("stolen") is None:
            clock = holder["clock"]
            clock.value += timedelta(seconds=DIAGNOSE_LEASE_SECONDS + 1)
            holder["stolen"] = holder["repository"].lease_next_post_attempt_job(
                kind=DIAGNOSE_KIND, owner="sidecar", lease_seconds=DIAGNOSE_LEASE_SECONDS, clock=clock,
            )

    vault, repository, client, embedder, third, clock = _third_with_slow_judge(tmp_path, seconds=0, on_judge=steal)
    holder.update(repository=repository, clock=clock)
    judged_before = len(client.judged)
    outcomes = drain_jobs(vault, repository, client, embedding=embedder, judge_factory=lambda: client, clock=clock)
    assert holder["stolen"] is not None, "the other worker took the expired lease"
    assert len(client.judged) - judged_before == 1, "no judge call after the lease was lost"
    assert client.escalation_requests == [], "no escalated repair paid by a worker that lost its lease"
    assert [outcome.state for outcome in outcomes if outcome.kind == DIAGNOSE_KIND] == ["lease_lost"]
    diagnosis = repository.current_live_diagnosis(third.attempt_id)
    assert repository.recurrence_escalation(diagnosis["id"]) is None, "the new lease holder writes the receipt"
