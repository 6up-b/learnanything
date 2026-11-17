"""Synthetic diagnosis journeys and lossless row snapshots for the move guard."""
from __future__ import annotations

import re
import json
import zlib
from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.table_roles import TABLE_ROLES
from learnloop.diagnosis import machine_checks
from learnloop.diagnosis import causal_orchestrator as causal
from learnloop.diagnosis import probe_completion as completion
from learnloop.diagnosis import probe_episodes as probes
from learnloop.diagnosis import probe_controls
from learnloop.diagnosis import probe_presentations as presentations

from tests.figure_build_golden_helpers import (
    DURATION_KEYS, _TIME, _Tokens, freeze_ids, freeze_wall, written,
)
from tests.helpers import NOW, admit_probe_instrument_card
from tests import pinned_draws

CLOCK = FrozenClock(NOW)
LO = "lo_svd_definition"
# A superset avoids silently excluding writes delegated to another package.
TABLES = tuple(sorted(TABLE_ROLES))
# Only identifier-shaped strings may vary between the two ID sequences. Numbers,
# including seeds and scores, must agree; fixed-input hashes remain literal.
IDENTITY = re.compile(
    r"(?<![a-zA-Z0-9])(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|"
    r"[0-9A-HJKMNP-TV-Z]{26}|[0-9a-hjkmnp-tv-z]{26}|"
    r"[0-9a-f]{64}|[0-9a-f]{32}|[0-9a-f]{26}|[0-9a-f]{16}|[0-9a-f]{12}|[0-9a-f]{8})(?![a-zA-Z0-9])"
)


def snapshot(repository):
    def decoded(key, value):
        if isinstance(value, bytes):
            if key == "state_z":
                state = json.loads(zlib.decompress(value))
                # A decision-state receipt names the checkout's commit, which changes with every landing.
                if isinstance(state, dict) and isinstance(state.get("versions"), dict) and "code" in state["versions"]:
                    state["versions"]["code"] = "<code-version>"
                return {"zlib_json": state}
            return {"hex": value.hex()}
        if isinstance(value, str) and key.endswith("_json"):
            try:
                return json.loads(value)
            except ValueError:
                pass
        return value

    with repository.connection() as connection:
        return {table: {int(row["_rowid"]): {k: decoded(k, row[k]) for k in row.keys() if k != "_rowid"}
                        for row in connection.execute(f'SELECT rowid AS _rowid, * FROM "{table}" ORDER BY rowid')}
                for table in TABLES}


class Journey:
    def __init__(self, repository):
        self.repository = repository
        # The vault's own seed (applied migrations, calibration priors, route and ladder tables) is not the journey.
        # Recording its rows made a third of the golden and would rewrite every case with each new migration.
        self.before = snapshot(repository)
        self.stages = [{"stage": "setup", "written": {}}]

    def capture(self, stage):
        after = snapshot(self.repository)
        self.stages.append({"stage": stage, "written": written(self.before, after)})
        self.before = after


def _wall(value, root, key=None):
    if key in DURATION_KEYS | {"latency_seconds", "waited_ms", "fit_ms"} and isinstance(value, (int, float)):
        return "<ms>"
    if isinstance(value, dict):
        return {str(k): _wall(v, root, str(k)) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_wall(v, root) for v in value]
    if isinstance(value, str):
        return _TIME.sub(_Tokens()._time, value.replace(str(root), "<root>"))
    return value


def paired(first, second):
    """Discover changed IDs in aligned strings, then replace them everywhere.

    Unlike blanket hex scrubbing, a hash of fixed synthetic content is evidence.
    A bijection also catches references accidentally pointing at different rows.
    """
    left, right = {}, {}
    compressed_sizes = set()
    unordered = {"blind_bundle_ids", "blind_bundle_ids_json"}

    def token_text(value, tokens):
        return IDENTITY.sub(lambda m: tokens.get(m[0], m[0]), value)

    def discover(a, b, where):
        if isinstance(a, dict) and isinstance(b, dict):
            assert len(a) == len(b), f"{where}: mapping length differs"
            for (ka, va), (kb, vb) in zip(
                sorted(a.items(), key=lambda kv: token_text(kv[0], left)),
                sorted(b.items(), key=lambda kv: token_text(kv[0], right)), strict=True):
                discover(ka, kb, where + '.key')
                discover(va, vb, where + '.' + ka)
        elif isinstance(a, list) and isinstance(b, list):
            assert len(a) == len(b), f"{where}: row/list count differs"
            if where.rsplit(".", 1)[-1] in unordered:
                a = sorted(a, key=lambda v: token_text(v, left))
                b = sorted(b, key=lambda v: token_text(v, right))
            for i, (va, vb) in enumerate(zip(a, b, strict=True)):
                discover(va, vb, f"{where}[{i}]")
        elif isinstance(a, str) and isinstance(b, str) and a != b:
            assert IDENTITY.split(a) == IDENTITY.split(b), f"{where}: non-ID differs: {a!r} / {b!r}"
            for va, vb in zip(IDENTITY.findall(a), IDENTITY.findall(b), strict=True):
                if va == vb:
                    continue
                token = left.setdefault(va, f"<id:{len(left) + 1}>")
                assert right.setdefault(vb, token) == token, f"{where}: reference differs"
                assert sum(t == token for t in right.values()) == 1, f"{where}: ID alias differs"
        elif a != b and ".decision_state_receipts." in where and where.endswith(".stored_bytes"):
            # The compressed JSON is compared in full; changing only IDs changes
            # zlib's byte count too. Scores and ordinary numeric fields stay exact.
            compressed_sizes.add(where)
        else:
            assert a == b, f"{where}: value differs: {a!r} / {b!r}"

    def replace(value, tokens, key=None, where="journey"):
        if where in compressed_sizes:
            return "<id-compressed-bytes>"
        if isinstance(value, dict):
            return {replace(k, tokens): replace(v, tokens, k, where + "." + k) for k, v in value.items()}
        if isinstance(value, list):
            result = [replace(v, tokens, where=f"{where}[{i}]") for i, v in enumerate(value)]
            return sorted(result) if key in unordered else result
        if isinstance(value, str):
            return IDENTITY.sub(lambda m: tokens.get(m[0], m[0]), value)
        return value

    discover(first, second, "journey")
    a, b = replace(first, left), replace(second, right)
    assert a == b, "ID replacement must preserve all references"
    return a


def recorded_twice(case, root):
    import pytest

    records = []
    for seed in (104, 401):
        path = root / str(seed)
        path.mkdir()
        with pytest.MonkeyPatch.context() as patch:
            freeze_wall(patch)
            freeze_ids(patch, seed)
            pin_journey_draws(patch, case)
            pushed = pinned_draws.push(f"diagnosis-journey:{case}")
            try:
                journey = run_case(case, path, patch)
                records.append(_wall({"stages": journey.stages}, path))
            finally:
                if pushed:
                    pinned_draws.pop()
    return paired(*records)


def pin_journey_draws(patch, case):
    from learnloop.diagnosis import robust_composition
    from learnloop.adaptive_difficulty import history_forecast

    # These additional draw families seed on minted IDs. Pin at the RNG seed
    # boundary, keeping every resulting seed and score literal in the golden.
    original = robust_composition._seed_int
    seen = {}

    def seed(model, context):
        index = seen.setdefault((model, context), len(seen))
        return original(model, f"journey:{case}:{index}")

    patch.setattr(robust_composition, "_seed_int", seed)
    from learnloop.diagnosis.split import prior_analysis
    assign = prior_analysis.assign
    patch.setattr(prior_analysis, "assign", lambda setting, _attempt: assign(setting, f"journey:{case}"))
    from learnloop import delayed_checks
    pick = delayed_checks.pick_with_receipt
    picks = {}

    def pinned_pick(*args, seed_key, **kwargs):
        index = picks.setdefault(seed_key, len(picks))
        return pick(*args, seed_key=f"journey:{case}:{index}", **kwargs)

    patch.setattr(delayed_checks, "pick_with_receipt", pinned_pick)
    from learnloop.matching import judge
    patch.setattr(judge, "ordered", lambda left, right: tuple(sorted((left, right), key=lambda s: (s.kind, s.content_hash))))
    draw = history_forecast.draw
    patch.setattr(history_forecast, "draw", lambda _presentation: draw(f"journey:{case}"))


def status_case(kind, root):
    from tests.causal_orchestrator_helpers import _vault, _seed_factor, _activate_probe_candidate, PROBE_ITEM

    vault, repo, _ = _vault(root, with_probe_item=True)
    journey = Journey(repo)
    repairs = {"deferred_machine_checks": ("repair:recall", None),
               "safe_common_repair_available": ("repair:recall", "repair:recall")}
    first, second = repairs.get(kind, ("repair:recall", "repair:method"))
    factor, a, b = _seed_factor(repo, first_repair=first, second_repair=second)
    if kind in {"needs_disambiguation", "started", "decline"}:
        admit_probe_instrument_card(repo, items=(PROBE_ITEM,))
        _activate_probe_candidate(repo, factor, a, b)
    journey.capture("factor_and_instrument")
    if kind == "started":
        status = causal.request_teaching_now(vault, repo, misconception_id=a, factor_id=factor, clock=CLOCK)
    else:
        status = causal.causal_repair_status(vault, repo, misconception_id=a, clock=CLOCK)
    assert status.status == ("needs_disambiguation" if kind == "decline" else kind)
    journey.capture("status")
    if kind == "deferred_machine_checks":
        machine_checks.sweep_machine_checks(vault, repo, LO, clock=CLOCK)
        journey.capture("backfill_pending")
        repo.resolve_unresolved_cause_factor(factor, resolution_observation_ids=[], clock=CLOCK)
        assert machine_checks.sweep_machine_checks(vault, repo, LO, clock=CLOCK) == []
        journey.capture("backfill_closed")
    if kind == "blocked_pending_review":
        checks = machine_checks.sweep_machine_checks(vault, repo, LO, clock=CLOCK)
        assert checks
        journey.capture("commissioning_pending")
        machine_checks.resolve_machine_check(repo, checks[0]["id"], resolution={"basis": "owner_review"}, clock=CLOCK)
        journey.capture("commissioning_resolved")
    if kind == "decline":
        causal.defer_probe_offer(repo, factor_id=factor, clock=CLOCK)
        status = causal.causal_repair_status(vault, repo, misconception_id=a, clock=CLOCK)
        assert status.probe_decision == "defer_learner_preference"
        journey.capture("declined")
    return journey


def cold_case(root, success):
    from tests.causal_p2_acceptance_helpers import (
        _acceptance_vault, _divergent_failure, _mint_reviewed_candidate, PROBE_ITEM,
    )
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.diagnosis.remediation import prescribe_remediation, start_remediation_treatment
    from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup

    vault, repo, _ = _acceptance_vault(root, toml="[placement]\nenabled = false\n")
    journey = Journey(repo)
    admit_probe_instrument_card(repo, learning_object_id=LO, items=(PROBE_ITEM,))
    _divergent_failure(vault, repo)
    factor = repo.open_unresolved_cause_factors(learning_object_id=LO)[0]
    a, b = [c["hypothesis_id"] for c in factor["candidate_causes"] if not c.get("open_set")]
    _mint_reviewed_candidate(repo, factor_id=factor["id"], first_id=a, second_id=b)
    status = causal.causal_repair_status(vault, repo, misconception_id=a, clock=CLOCK)
    assert status.status == "needs_disambiguation"
    journey.capture("offered")
    offer = causal.accept_probe_offer(vault, repo, factor_id=factor["id"],
                                     decision_receipt_id=status.decision_receipt_id, clock=CLOCK)
    assert offer.accepted and offer.as_dict()["accepted"]
    journey.capture("accepted")
    observation = causal.record_probe_classification(repo, presentation_id=offer.presentation_id,
                    observed_features={"names_transpose": False}, feature_source="model_extracted", clock=CLOCK)
    assert observation.admitted and observation.resolved_factor
    assert observation.as_dict()["observation_id"]
    journey.capture("matched_and_resolved")
    status = causal.causal_repair_status(vault, repo, misconception_id=a, clock=CLOCK)
    assert status.status == "started"
    prescribe_remediation(vault, repo, status.episode["id"], clock=CLOCK)
    treatment = start_remediation_treatment(vault, repo, status.episode["id"], clock=CLOCK)
    complete_self_graded_attempt(vault, repo,
        AttemptDraft(practice_item_id=treatment["primed_item_id"], learner_answer_md="U Sigma Q", primed=True),
        SelfGradeInput(criterion_points={c.id: 0.0 for c in vault.practice_items[treatment["primed_item_id"]].grading_rubric.criteria}, confidence=4),
        clock=CLOCK)
    journey.capture("repair")
    later = FrozenClock(NOW + timedelta(days=2))
    item = treatment["cold_item_id"]
    result = complete_self_graded_attempt(vault, repo,
        AttemptDraft(practice_item_id=item, learner_answer_md="U Sigma V transpose" if success else "U Sigma Q"),
        SelfGradeInput(criterion_points={c.id: c.points if success else 0.0 for c in vault.practice_items[item].grading_rubric.criteria}, confidence=5),
        clock=later)
    evaluate_attempt_intervention_followup(vault, repo, result=result, clock=later)
    assert repo.causal_cold_verification_for_attempt(result.attempt_id)["success"] is success
    journey.capture("cold_pass" if success else "cold_fail")
    return journey


def probe_case(kind, root, patch):
    from tests.voi_stopping_helpers import _long_probe_vault, _minutes, _answer_probe
    from tests.probe_episodes_helpers import _setup, _commit, ITEM_ID
    from tests.probe_block_end_helpers import _submit
    from tests.held_grade_evidence_helpers import _held_apply, attempt_grade_held

    if kind in {"value_stop", "budget_stop"}:
        vault, repo = _long_probe_vault(root, "mvp-0.21", "[voi_stopping]\nenabled = false\n" if kind == "budget_stop" else "")
        journey = Journey(repo)
        _minutes(patch, 10_000 if kind == "value_stop" else 0.0001)
        for index in range(1 if kind == "value_stop" else 4):
            episode = _answer_probe(vault, repo)
            journey.capture(f"answer_{index + 1}")
        assert episode.completion_reason == ("value_of_information_stop" if kind == "value_stop" else "observation_budget_exhausted")
        return journey
    if kind == "mid_check":
        from tests.probe_block_end_helpers import _setup as block_setup, _misconception_attribution
        from tests.helpers import append_config_toml
        from learnloop.vault.loader import load_vault
        from learnloop.attempts.post_attempt import run_post_attempt_pipeline
        vault, repo = block_setup(root)
        append_config_toml(vault.root, "[probe.block]\ndefault_block_observations = 3")
        vault = load_vault(vault.root)
        journey = Journey(repo)
        episode = probes.enter_episode(vault, repo, LO, clock=CLOCK)
        answers = []
        for item in (ITEM_ID, "pi_svd_define_002"):
            presentation = _commit(vault, repo, episode, item_id=item)
            result = _submit(vault, repo, item_id=item, presentation_id=presentation.id, score=1,
                             error_attributions=[_misconception_attribution()])
            assert result.probe_block_end is None
            run_post_attempt_pipeline(vault, repo, result=result, clock=CLOCK)
            answers.append(result.attempt_id)
            journey.capture(f"answered_{item}")
        stopped = probe_controls.stop_diagnosing_and_teach(vault, repo, LO, clock=CLOCK)
        assert stopped is not None and repo.probe_episode(episode.id).status == "converted_to_tutoring"
        assert {row["attempt_id"] for row in stopped.released_feedback} == set(answers)
        journey.capture("stopped_and_settled")
        return journey
    _, vault, repo = _setup(root, extra_item=True)
    journey = Journey(repo)
    episode = probes.enter_episode(vault, repo, LO, clock=CLOCK)
    assert probe_controls.episode_contract(vault, repo, LO)["forced_attempt_type"] == "diagnostic_probe"
    eligible = probe_controls.next_probe_item(vault, repo, LO)
    assert eligible is not None
    assert presentations.probe_serving_block_reason(vault, repo, session_id="journey") is None
    presentations.probe_value_block_reason(vault, repo, episode, ITEM_ID, session_id="journey")
    presentation = presentations.commit_item_presentation(vault, repo, episode, vault.practice_items[ITEM_ID],
                                                  probes.episode_hypothesis_set(repo, episode), clock=CLOCK)
    assert presentation is not None
    presentations.serve_presentation(repo, presentation.id, clock=CLOCK)
    journey.capture("presented")
    if kind == "held_release":
        from learnloop.attempts.grade_resolution import append_adjudication_evidence_revision
        result = _held_apply(vault, repo, ITEM_ID, {"correctness": 0.0}, attempt_id="att_held_probe",
                            when=NOW, attempt_type="diagnostic_probe", presentation_id=presentation.id)
        assert attempt_grade_held(repo, result.attempt_id)
        assert not repo.probe_observation_for_attempt(result.attempt_id).updates_belief
        journey.capture("held")
        revision = append_adjudication_evidence_revision(repo, attempt_id=result.attempt_id, resolved_fraction=1.0,
            adjudication_id="adj_probe", adjudicator_source="human_owner", rationale="valid route", vault=vault,
            clock=FrozenClock(NOW + timedelta(hours=1)))
        assert revision["status"] == "revised" and not attempt_grade_held(repo, result.attempt_id)
        journey.capture("released")
        completion.close_diagnostic_segment(repo, episode.id, clock=CLOCK)
        assert completion.close_diagnostic_segment(repo, episode.id, clock=CLOCK) is None
        journey.capture("segment_closed")
    else:
        result = _submit(vault, repo, item_id=ITEM_ID, presentation_id=presentation.id, score=1)
        journey.capture("answered")
        from tests.regrade_contract_replay_helpers import _regrade
        _regrade(vault, repo, result.attempt_id, {"correctness": 4.0}, when=NOW + timedelta(hours=1))
        assert repo.fetch_practice_attempt(result.attempt_id)["rubric_score"] == 4
        journey.capture("regraded")
    return journey


def deterministic_case(root):
    from tests.causal_p2_acceptance_helpers import _acceptance_vault, _offered_probe, PROBE_ITEM
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup

    vault, repo, _ = _acceptance_vault(root)
    journey = Journey(repo)
    _, factor, first, _, offer = _offered_probe(vault, repo, features=(
        {"criterion:correctness:full_credit": False}, {"criterion:correctness:full_credit": True}))
    journey.capture("accepted")
    result = complete_self_graded_attempt(vault, repo,
        AttemptDraft(practice_item_id=PROBE_ITEM, learner_answer_md="U Sigma Q", attempt_type="diagnostic_probe",
                     probe_presentation_id=offer.presentation_id),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=3), clock=CLOCK)
    evaluate_attempt_intervention_followup(vault, repo, result=result, clock=CLOCK)
    observation, = repo.causal_discriminating_observations(factor_id=factor)
    assert observation["classified_as"] == [first] and observation["support_authority"] == "validator_owned"
    journey.capture("auto_classified_and_resolved")
    evaluate_attempt_intervention_followup(vault, repo, result=result, clock=CLOCK)
    assert len(repo.causal_discriminating_observations(factor_id=factor)) == 1
    journey.capture("hook_repeated")
    return journey


def fg1_case(kind, root, patch):
    from learnloop_sidecar import handlers  # noqa: F401 - register direct handler entry points
    from tests.followup_journey_helpers import _journey, _generate, _answer, _call, _forced
    from tests.followup_serve_helpers import AuthorFake
    from learnloop.followup_serve import workflow as wf
    from learnloop.followup_run import router

    ctx, _, repo, result, outcome = _journey(root, patch)
    journey = Journey(repo)
    if kind == "wait":
        _forced(patch, router.WAIT)
    fake = AuthorFake()
    _generate(ctx, repo, fake=fake)
    assert fake.calls == 1
    row = wf.get(repo, outcome.workflow_id)
    assert row["state"] == (wf.READY if kind == "ask_now" else wf.WAITING)
    journey.capture("authored_ready" if kind == "ask_now" else "authored_waiting")
    step = _call(ctx, "followup_next", {"attemptId": result.attempt_id})
    assert step["action"] == ("open" if kind == "ask_now" else "continue")
    if kind == "wait":
        assert row["exposed_at"] and row["release_reason"] == wf.RELEASE_WAIT
        assert wf.waiting_still_valid(repo, row)
        wf.move(repo, outcome.workflow_id, to_state=wf.READY, reason="boundary", clock=CLOCK)
    _call(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    contract = _call(ctx, "get_probe_contract", {"practiceItemId": row["practice_item_id"]})
    assert contract["presentationId"] == row["presentation_id"]
    journey.capture("opened")
    _answer(ctx, repo, row, points={"fact_0": 0, "fact_1": 2})
    observation = repo.causal_discriminating_observations(factor_id=row["factor_id"])[0]
    assert observation["admitted"] is (kind == "ask_now")
    assert repo.unresolved_cause_factor(row["factor_id"])["status"] == ("resolved" if kind == "ask_now" else "open")
    journey.capture("answered_and_released")
    return journey


def gap_case(root):
    from tests.learner_text_gaps_helpers import _vault, _ask, _run
    from tests.text_gap_fakes import GapTutor, GapLLMFake, always, seed_proposal
    from learnloop.tutor.ai_contracts import LearnerGap
    from learnloop.vault.loader import add_note

    vault_root, repo = _vault(root)
    journey = Journey(repo)
    add_note(vault_root, "linear-algebra", "la_source", "Diagonalization source",
             "A matrix with n independent eigenvectors diagonalizes.", source_type="canonical_source",
             related_los=["lo_diag"], clock=CLOCK)
    tutor = GapTutor(LearnerGap(prerequisite_name="Eigenvectors", prerequisite_line="Vectors a matrix only scales.", kind="prerequisite"))
    event = _ask(vault_root, repo, tutor, question="What even is an eigenvector?")
    journey.capture("asked")
    row = _run(vault_root, repo, event["event_id"], tutor=tutor,
               llm=GapLLMFake(decide=always("different"), proposal=seed_proposal()))
    assert row["action"] == "created_prerequisite"
    journey.capture("prerequisite_created")
    return journey


def recurrence_case(root):
    from tests.recurrence_live_helpers import _vault, STATEMENTS
    from tests.recurrence_fakes import StatementFake, shares_word
    from tests.diagnosis_fakes import FakeEmbeddingClient
    from tests.split_live_helpers import submit, drain_jobs, at

    _, vault, repo = _vault(root)
    journey = Journey(repo)
    client = StatementFake(STATEMENTS, decide=shares_word("transpos"), operators={"third": "worked_contrast"})
    for offset, (item, answer) in enumerate((("pi_svd_compute_001", "A = U Sigma V first"),
            ("pi_svd_compute_002", "B = U Sigma V second"), ("pi_svd_compute_001", "A = U Sigma V third"))):
        result = submit(vault, repo, client, item_id=item, answer=answer, when=at(10 + 2 * offset))
        drain_jobs(vault, repo, client, embedding=FakeEmbeddingClient(), judge_factory=lambda: client,
                   clock=FrozenClock(at(11 + 2 * offset)))
        journey.capture(f"diagnosed_{offset + 1}")
    assert client.judged and repo.recurrence_group_map()
    escalation = repo.recurrence_escalation(repo.current_live_diagnosis(result.attempt_id)["id"])
    assert escalation["recurrence_count"] == 3
    return journey


CASES = (
    "causal_deferred_machine_checks", "causal_safe_common_repair_available", "causal_blocked_pending_review",
    "causal_needs_disambiguation", "causal_started", "causal_decline", "cold_pass", "cold_fail",
    "fg1_ask_now", "fg1_wait", "value_stop", "budget_stop", "mid_check", "held_release", "regrade",
    "text_prerequisite", "recurrence_judge", "deterministic_classification",
)


def run_case(case, root, patch):
    if case == "deterministic_classification":
        return deterministic_case(root)
    if case.startswith("causal_"):
        return status_case(case.removeprefix("causal_"), root)
    if case.startswith("cold_"):
        return cold_case(root, case == "cold_pass")
    if case.startswith("fg1_"):
        return fg1_case(case.removeprefix("fg1_"), root, patch)
    if case == "text_prerequisite":
        return gap_case(root)
    if case == "recurrence_judge":
        return recurrence_case(root)
    return probe_case(case, root, patch)
