"""Adaptive difficulty AD2+AD3: the Codex review's findings (docs/reviews/adaptive-difficulty-ad23-codex-review.md).

Each test failed before its fix for the reason the finding names. Fakes only: no
network, no model call, no paid call.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from typing import Any

import pytest

from learnloop.adaptive_difficulty import arms as A
from learnloop.adaptive_difficulty import outcomes as O
from learnloop.adaptive_difficulty import readiness as RD
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import report as REP
from learnloop.attempts.attempts import AttemptDraft, complete_attempt_with_ai_required
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import ad_serving
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import LO, QUIET, ad23_vault, answer, env_for, rows, selections
from tests.split_live_helpers import ReadyRuntime, split_vault
from tests.test_field_split_outcomes import _ZeroEverythingWithoutAttribution
from tests.test_pfc_unverified_unassessed import ITEM as PFC_ITEM
from tests.test_pfc_unverified_unassessed import VERIFYING_ANSWER, _PartialWithoutAttribution

ROUTER_OFF = "[router]\nenabled = false\n"


# -- F1: a wholly unassessed attempt with frozen inputs trains nothing ------------------------------


def _frozen_pfc_attempt(tmp_path, client) -> tuple[Any, Any, Any, str]:
    """A PF-c submission through the live door, bound to a plan presentation whose serve froze
    its inputs (so AD reads it through the frozen-input branch, not field's revision rows)."""

    from learnloop.adaptive_difficulty.serve import record_plan_serve

    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.28", config=QUIET, seed=False)
    vault = load_vault(paths.root)
    served = "2026-11-01T11:00:00Z"
    with repository.connection() as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                           "VALUES ('blk_pfc', 'practice', 10, 'hash', ?)", (served,))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_pfc', 'blk_pfc', ?, 'chooser', ?)", (PFC_ITEM, served))
        connection.commit()
    record = record_plan_serve(vault, repository, presentation_id="pp_pfc", practice_item_id=PFC_ITEM,
                               served_at=served)
    assert record is not None and record.serve_inputs_id, record
    clock = FrozenClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC))
    draft = AttemptDraft(practice_item_id=PFC_ITEM, learner_answer_md=VERIFYING_ANSWER,
                         attempt_type="independent_attempt", plan_presentation_id="pp_pfc")
    result = complete_attempt_with_ai_required(vault, repository, draft, runtime=ReadyRuntime(), ai_client=client,
                                               clock=clock)
    run_post_attempt_pipeline(vault, repository, result=result, session_id=None, clock=clock)
    return paths, vault, repository, str(result.attempt_id)


def _event(paths, vault, repository, attempt_id: str) -> RP.AttemptEvent:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        events = RP.load_events(connection, vault, repository)
    return next(e for e in events.attempts if e.attempt_id == attempt_id)


def test_a_wholly_unassessed_frozen_attempt_trains_nothing_and_tests_no_cell(tmp_path):
    """F1: every criterion PF-c unverified. The attempt schedules as correct (correctness 1.0)
    and keeps its grading rows, but measures nothing: AD reads it through its frozen inputs and
    must still exclude it (no update, no tested cell). Failed before: only the type's mass was
    checked on the frozen branch, so it trained a success and marked its cell tested."""

    paths, vault, repository, attempt_id = _frozen_pfc_attempt(tmp_path, _ZeroEverythingWithoutAttribution())
    attempt = repository.fetch_practice_attempt(attempt_id)
    assert attempt["correctness"] == 1.0
    event = _event(paths, vault, repository, attempt_id)
    assert event.input_status == "frozen"
    assert not event.eligible and event.reason == "unassessed"
    snap = RP.run(RP.load_events(repository.connection(), vault, repository))
    assert not snap.observed_cells and not snap.observed_los
    assert all(row.get("detail", {}).get("excluded") == "unassessed" for row in snap.trace
               if row["attempt_id"] == attempt_id)


def test_a_partly_unverified_frozen_attempt_reads_its_assessed_grade(tmp_path):
    """F1's other side: one criterion unverified, one assessed. The grade over the assessed
    criterion stands, so the attempt still trains (on that grade), as field reads it."""

    paths, vault, repository, attempt_id = _frozen_pfc_attempt(tmp_path, _PartialWithoutAttribution())
    event = _event(paths, vault, repository, attempt_id)
    assert event.input_status == "frozen" and event.eligible and event.category == 2


# -- F2: a stuck learner who wrote an answer is graded on it ---------------------------------------


@pytest.mark.parametrize(("answer_md", "correctness", "expected"), [
    ("A full answer.", 1.0, 2),
    ("A partial answer.", 0.6, 1),
    ("   ", 1.0, 0),
    ("", 0.0, 0),
])
def test_a_stuck_answer_is_forced_to_fail_only_when_empty(answer_md, correctness, expected):
    """F2: §5.3's override is "an empty 'I'm stuck'". Failed before: any declared-stuck answer
    was category 0 whatever its grade."""

    attempt = {"attempt_type": "independent_attempt", "declared_stuck": 1, "learner_answer_md": answer_md}
    facts = O.AttemptFacts(correctness=correctness, stuck=RP.forced_failure(attempt))
    assert O.category(facts) == expected


def test_an_i_dont_know_answer_still_fails_whatever_its_grade():
    for attempt in ({"attempt_type": "dont_know", "learner_answer_md": "x"},
                    {"attempt_type": "independent_attempt", "declared_dont_know": 1, "learner_answer_md": "x"}):
        assert RP.forced_failure(attempt)
        assert O.category(O.AttemptFacts(correctness=1.0, stuck=True)) == 0


# -- F3: the live cache never outlives a change to what the replay reads -----------------------------


def _answered_vault(tmp_path, steps: int = 3):
    items = ("pi_c1", "pi_c2", "pi_c3")
    paths = ad23_vault(tmp_path, items=items, config=ROUTER_OFF)
    env, clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    for k in range(steps):
        _record, step = advance(env, serve=True)
        if step["kind"] != "item":
            break
        clock.advance(2)
        answer(paths, step["practice_item_id"], correct=k != 1, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    return paths


def _fresh_hash(vault, repository) -> str:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        events = RP.load_events(connection, vault, repository)
    return RP.run(events, RP.ReplaySettings.from_config(vault.config), trace=False).state_hash()


def test_the_live_cache_follows_replacements_updates_and_other_connections(tmp_path):
    """F3: the cache was keyed by each table's COUNT(*) and MAX(rowid). Replacing the
    init-wizard claim with the existing delete-and-insert API reuses the freed rowid (same
    count, same max), an in-place update changes neither, and the interpretations behind
    quarantine were not in the list at all: each left the old posterior live while a fresh
    rebuild read the change. Now every live snapshot equals an uncached replay."""

    paths = _answered_vault(tmp_path)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    RP.clear_cache()
    claim = {"claim_type": "self_rating", "scope_type": "global", "claimed_level": 0.2, "prior_pseudo_count": 1.0,
             "source": "init_wizard", "created_at": "2026-10-01T00:00:00Z"}
    repository.insert_learner_claim(claim)
    first = RP.snapshot(vault, repository)
    assert first.state_hash() == _fresh_hash(vault, repository)

    def counts() -> tuple:
        with closing(sqlite3.connect(paths.sqlite_path)) as connection:
            return connection.execute("SELECT COUNT(*), MAX(rowid) FROM learner_claims").fetchone()

    before = counts()
    # The init wizard's replace seam: delete, then insert the new level.
    repository.delete_learner_claims(source="init_wizard", scope_type="global")
    repository.insert_learner_claim({**claim, "claimed_level": 0.95})
    assert counts() == before  # the old fingerprint could not see this
    replaced = RP.snapshot(vault, repository)
    assert replaced.state_hash() == _fresh_hash(vault, repository) != first.state_hash()

    # An in-place update, written from another connection.
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE learner_claims SET claimed_level = 0.5")
        connection.commit()
    updated = RP.snapshot(vault, repository)
    assert updated.state_hash() == _fresh_hash(vault, repository) != replaced.state_hash()

    # A quarantine (an interpretation table the old list never read).
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE grade_interpretations SET quarantine_state = 'quarantined'")
        connection.commit()
    quarantined = RP.snapshot(vault, repository)
    assert quarantined.state_hash() == _fresh_hash(vault, repository) != updated.state_hash()
    assert not quarantined.observed_cells
    # Unchanged inputs still hit the cache.
    assert RP.snapshot(vault, repository) is quarantined


# -- F4: a draw reads the reading recorded since the last serve -----------------------------------


class _ReadingMap:
    """The Reader's mapping, fixed: worked example ``we1`` of ``ext1`` is on the slot LO."""

    def __init__(self, facets: list[str]) -> None:
        self.facets = facets

    def los_for_section(self, extraction_id, section_id):
        return []

    def los_for_span(self, extraction_id, span_id):
        return [LO] if (extraction_id, span_id) == ("ext1", "we1") else []

    def section_spans(self, extraction_id, section_id):
        return []

    def worked_example_spans(self, extraction_id):
        return {"we1"} if extraction_id == "ext1" else set()

    def withheld(self, extraction_id, span_id):
        return False

    def los_for_note(self, note_id):
        return []

    def lo_for_item(self, practice_item_id):
        return None

    def facets_for_lo(self, learning_object_id):
        return list(self.facets) if learning_object_id == LO else []


def test_a_draw_reads_reading_recorded_since_the_last_serve(tmp_path, monkeypatch):
    """F4: a worked example studied between two presentations. The draw scored its support on
    the state before the reading (only the serve hook, after the draw, swept it) while its
    receipts read the state after it. Now the draw's sweep records it first: the selection's
    state hash is the state with the reading, and the serve receipt reads the same state."""

    import learnloop.adaptive_difficulty.reading as reading

    items = ("pi_r1", "pi_r2", "pi_r3")
    paths = ad23_vault(tmp_path, items=items, config=ROUTER_OFF)
    vault = load_vault(paths.root)
    facets = sorted({f for i in items for f in (vault.practice_items[i].evidence_facets or [])})
    monkeypatch.setattr(reading, "VaultReadingMap", lambda _vault, _repository: _ReadingMap(facets))
    env, clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _record, step = advance(env, serve=True)
    clock.advance(2)
    answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"], clock=clock)
    clock.advance(3)
    # The learner studies a worked example on the LO (no sweep is run by hand).
    Repository(paths.sqlite_path).insert_source_exposure_event(
        {"context": "reader", "extraction_id": "ext1", "span_id": "we1", "revision_id": "rev1", "source_id": "src1",
         "entity_type": "reader", "entity_id": "visit1"}, clock=FrozenClock(clock.now()))
    clock.advance(3)
    _record, second = advance(env, serve=True)
    assert second["kind"] == "item"
    opportunities = rows(paths.sqlite_path, "SELECT * FROM ad_reading_opportunities ORDER BY swept_at, id")
    assert opportunities and opportunities[-1]["sweep_ref"].startswith("serve:")  # the draw's own sweep
    draw = [row for row in selections(paths, kind="serve")][-1]
    RP.clear_cache()
    with_reading = RP.snapshot(load_vault(paths.root), Repository(paths.sqlite_path))
    assert draw["state_hash"] == with_reading.state_hash()
    receipt = rows(paths.sqlite_path, "SELECT inputs_json FROM forecast_receipts WHERE forecaster = "
                                      "'ad_threshold@subject' AND plan_presentation_id = ?",
                   (second["presentation_id"],))
    assert receipt and json.loads(receipt[0]["inputs_json"])["state_hash"] == draw["state_hash"]


# -- F5: a serve-time commission is generated in the background ------------------------------------


def test_a_serve_commission_queues_its_generation_once_at_its_point(tmp_path):
    """F5: no pool item reaches the band, so the serve draw commissions a point. Its generation
    is queued on the durable job queue (named by the commission: once, however often the
    schedule runs) and asks the ordinary generation path, here with a fake generator, for one
    item at exactly that point and capability (its landing receipt is §7.4's, tested in
    test_ad2_serving). Failed before: nothing consumed the commission, and it suppressed every
    later one for its cell."""

    from learnloop.adaptive_difficulty.generation import rung_features, schedule_commission_generation
    from learnloop.content.pipeline import jobs as J
    from learnloop.content.pipeline.runner import RunnerServices
    from learnloop.content.proposals.ai_contracts import AuthoringProposal

    from tests.structured_ai import StructuredClientFake

    HARD = {"complexity": 3, "transfer": "far", "scaffolding": "none", "span": "multi_step",
            "response": "long_constructed", "tools": ["closed_book"]}
    items = ("pi_k1", "pi_k2")
    paths = ad23_vault(tmp_path, items=items, features={i: HARD for i in items}, config=ROUTER_OFF)
    env, clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    (commission,) = selections(paths, kind="commission")
    assert ":serve:" in commission["decision_key"] and commission["chosen_point"]

    class _Generator(StructuredClientFake):
        provider_name = "codex"
        provider_type = "test"
        model = "fake-generator"

        def __init__(self) -> None:
            self.contexts: list[Any] = []

        def run_authoring_proposal(self, context):
            self.contexts.append(context)
            return AuthoringProposal.model_validate({"summary": "commissioned", "source_refs": [], "items": []})

    generator = _Generator()
    repository = Repository(paths.sqlite_path)
    jobs = J.DurableIngestJobs()
    jobs.bind(repository, paths.root, background=False,
              services=RunnerServices(synthesis_client_factory=lambda _ctx: generator))
    queued: list[str] = []

    def enqueue(commission_id: str, learning_object_id: str) -> str:
        batch = jobs.enqueue_practice_expansion(learning_object_ids=[learning_object_id],
                                                ad_commission_id=commission_id)
        queued.append(batch)
        return batch

    vault = load_vault(paths.root)
    assert schedule_commission_generation(vault, repository, enqueue) == [commission["id"]]
    assert schedule_commission_generation(vault, repository, enqueue) == [commission["id"]]
    assert len(set(queued)) == 1 and queued[0] == J.ad_commission_batch_id(commission["id"])
    (job,) = repository.ingest_jobs_for_batch(queued[0])
    assert job["payload"]["ad_commission_id"] == commission["id"] and job["status"] == "completed"
    # The generator was asked for one item at exactly the commissioned point.
    assert len(generator.contexts) == 1
    instructions = generator.contexts[0].instructions or ""
    from learnloop.adaptive_difficulty.generation import CONTRACT_TEXT

    assert CONTRACT_TEXT in instructions and commission["id"] in instructions
    import ast

    line = next(text for text in instructions.splitlines() if text.startswith("Targets: "))
    (target,) = [t for t in ast.literal_eval(line[len("Targets: "):]) if t.get("ad_commission_id") == commission["id"]]
    assert target["requested_new_items"] == 1
    assert target["capability"] == commission["cell_capability"] and target["rung_source"] == "ad_commission"
    assert target["target_task_features"] == rung_features(commission["chosen_point"])
    result = job.get("result") or json.loads(job.get("result_json") or "{}")
    assert result.get("ad_commission_id") == commission["id"] and result.get("commissioned_targets") == 1


def test_the_sidecar_queues_a_serve_commission_after_the_serve(tmp_path, monkeypatch):
    """F5's wiring: the plan's serve RPC hands each open serve-time commission to the queue after
    its response is built; with ``LEARNLOOP_AD_MODELS=off`` and nothing injected it queues nothing."""

    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop import clock as clock_module
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    HARD = {"complexity": 3, "transfer": "far", "scaffolding": "none", "span": "multi_step",
            "response": "long_constructed", "tools": ["closed_book"]}
    items = ("pi_k1", "pi_k2")
    paths = ad23_vault(tmp_path, items=items, features={i: HARD for i in items}, config=ROUTER_OFF)
    monkeypatch.setattr(clock_module.SystemClock, "now",
                        lambda _self: datetime(2026, 10, 12, 9, 0, tzinfo=UTC))

    def call(ctx, name: str, params: dict):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    ctx = SidecarContext()
    ctx.load(paths.root)
    queued: list[tuple[str, str]] = []
    ctx.ad_commission_enqueue = lambda commission_id, lo: queued.append((commission_id, lo))
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert step["kind"] == "item"
    commissions = selections(paths, kind="commission")
    assert commissions, "no commission drawn: the pool should have no item in the band"
    assert queued == [(commissions[0]["id"], commissions[0]["learning_object_id"])]
    ctx.ad_commission_enqueue = None
    from learnloop_sidecar.handlers.daily_plan import _commission_enqueue

    assert _commission_enqueue(ctx) is None  # the suite runs with LEARNLOOP_AD_MODELS=off
    ctx.map_builds.close()


# -- F6: the extra question is the one the draw chose ------------------------------------------------


def test_the_offer_names_the_sections_other_question_and_its_answer_is_the_extra(tmp_path, monkeypatch):
    """F6: with the section's ordinary check named as on show, the draw's extra is the other
    question, the RPC returns that exact question (prompt and answer) for the Reader to show,
    and answering it through the Reader's own action records the reading opportunity that
    names the offer. Failed before: the RPC returned only an id the Reader ignored, and the
    Reader reopened the ordinary check (and never named it as on show)."""

    import learnloop.adaptive_difficulty.reading as reading
    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop.adaptive_difficulty.reading import sweep
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    from tests.test_ad1_reading_opportunities import _question, _setup
    from tests.test_ad3_dose_arm import QUIET as DOSE_QUIET
    from tests.test_ad3_dose_arm import _mapping

    paths, _vault, repo = _setup(tmp_path, config=DOSE_QUIET + "dose_floor = 0.3\ndose_daily_offers = 100\n")
    ordinary = _question(repo, "recall", 1, answer=False)
    extra = _question(repo, "why_step", 1, answer=False)
    mapping = _mapping(examples={"ext1": {"we1"}})  # only the question extra is feasible
    monkeypatch.setattr(reading, "VaultReadingMap", lambda _vault, _repository: mapping)

    def call(ctx, name: str, params: dict):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    ctx = SidecarContext()
    ctx.load(paths.root)
    for visit in range(60):
        result = call(ctx, "reader.dose_offer", {"extractionId": "ext1", "sectionId": "u1", "visitId": f"v{visit}",
                                                 "showingQuestionId": ordinary})
        if result["offer"]:
            break
    else:  # pragma: no cover
        pytest.fail("no extra question offered")
    offer = result["offer"]
    assert offer["variant"] == "extra_question"
    assert offer["content"]["questionId"] == extra
    assert offer["question"]["questionId"] == extra and offer["question"]["prompt"] == "A why_step question?"
    assert offer["question"]["expectedAnswer"] == "The answer."
    call(ctx, "reader.dose_offer_event", {"drawId": offer["drawId"], "event": "delivered"})
    call(ctx, "reader.dose_offer_event", {"drawId": offer["drawId"], "event": "taken"})
    call(ctx, "reader.authored_question_action", {"questionId": extra, "action": "answered", "response": "mine"})
    sweep(load_vault(paths.root), repo, as_of="2099-01-01T00:00:00Z", sweep_kind="serve", reading_map=mapping)
    (opportunity,) = rows(paths.sqlite_path, "SELECT * FROM ad_reading_opportunities WHERE source_id = ?", (extra,))
    assert opportunity["dose_offer_id"] == offer["drawId"]
    assert rows(paths.sqlite_path, "SELECT * FROM ad_reading_opportunities WHERE source_id = ?", (ordinary,)) == []
    ctx.map_builds.close()


# -- F7: the grid comparator is prequential -----------------------------------------------------------


def test_the_grid_arm_never_reads_a_later_answer(tmp_path):
    """F7: appending or changing later outcomes leaves every earlier ``:grid`` forecast
    unchanged. Failed before: its shared means came from a replay of the whole history, so a
    later outcome moved the first forecast (0.168 -> 0.229 in the review's reproduction)."""

    from learnloop.adaptive_difficulty import relatedness as R
    from learnloop.adaptive_difficulty.state import ItemSpec

    def events(outcomes: list[int]) -> RP.Events:
        attempts = []
        for k, category in enumerate(outcomes):
            spec = ItemSpec(f"i{k}", "L", "s", "retrieval", {"f": 1.0}, features={"complexity": k % 3},
                            signals={"z_origin": 1.0})
            attempts.append(RP.AttemptEvent(
                f"a{k}", f"2026-10-0{k + 1}T00:00:00Z", float(k), "L", f"i{k}", "s", "independent_attempt", True,
                None, "frozen", spec, category, 0.0, f"2026-10-0{k + 1}T00:00:00Z", None, None, ("f",)))
        return RP.Events(attempts, [], [], R.VaultStructure(facet_los={"f": ["L"]}, lo_facets={"L": ["f"]}),
                         {"L": "s"}, {"L": ["f"]})

    def grid(outcomes: list[int]) -> list[float]:
        sink: dict[str, A.Record] = {}
        settings = RP.ReplaySettings()
        A._run(events(outcomes), settings, base=True, sink=sink, names={"subject": A.SUBJECT, "lo": A.LO},
               grid=A._GridArm())
        return [sink[f"a{k}"].p[A.GRID] for k in range(len(outcomes))]

    base = grid([2, 0, 2])
    assert grid([2, 0, 2, 0, 0, 0])[:3] == base
    assert grid([2, 0, 2, 2, 2, 2])[:3] == base
    changed = grid([2, 0, 0, 0, 0, 0])
    assert changed[:3][:2] == base[:2]


# -- F8: both report-history conditions fire through the production report ---------------------------


def _record(k: int, p: float, y: float) -> A.Record:
    return A.Record(f"a{k:03d}", "L", ("f", "retrieval"), "retrieval", y, 2 if y else 0, 0.0, False, False, False,
                    False, f"2026-10-01T00:{k // 60:02d}:{k % 60:02d}Z", p={A.SUBJECT: p})


def test_readiness_errors_read_each_report_window():
    """F8: one report per 200 AD selections; each window scores the records up to its last
    selection, then this run. Failed before: the CLI passed no history, so the
    two-consecutive-reports flag could never fire."""

    # Forecasts at 0.75 that never come true: a band-region error far above 0.05 in every window.
    records = [_record(k, 0.75, 0.0) for k in range(120)]
    times = [r.created_at for r in records]
    errors = REP.readiness_errors(records, times, every=40)
    assert len(errors) == 3 and all(e is not None and e > 0.05 for e in errors)
    # Extra records past the last window are this run's own report.
    assert len(REP.readiness_errors(records, times[:100], every=40)) == 3
    assert REP.readiness_errors(records[:30], times[:30], every=40) == [
        REP.arm_scores(records[:30], A.SUBJECT, None).get("band_region_error")]


def _offer(connection, *, key: str, visit: str, at: str) -> None:
    draw = ad_serving.insert_dose_row(connection, {
        "row_kind": "draw", "draw_key": key, "visit_id": visit, "extraction_id": "ext1", "section_id": "u1",
        "learning_object_ids": [LO], "feasible": ["none", "extra_question"], "infeasible": {}, "base_version": "b",
        "floor": 0.3, "propensities": {"none": 0.7, "extra_question": 0.3}, "seed": "s", "u": 0.1,
        "chosen_variant": "extra_question", "content": {"question_id": "q"}, "forecast_p": None, "detail": {},
        "created_at": at})
    ad_serving.insert_dose_row(connection, {"row_kind": "delivered", "draw_id": draw, "created_at": at})


def _envelope(connection, kind: str, payload: dict, at: str) -> None:
    connection.execute(
        "INSERT INTO interaction_events(id, kind, origin, subject_type, subject_id, payload_json, created_at) "
        "VALUES (?, ?, 'learner', 'reader', 'ext1', ?, ?)", (f"ev_{kind}_{at}_{payload.get('to', '')}", kind,
                                                           json.dumps(payload), at))


def test_density_lowerings_join_offers_to_their_visits(tmp_path):
    """F8: a lowering of the cue density counts when it falls after a delivered extra offer
    and inside that offer's visit; three in 14 days fire the burden flag through ``build``.
    Failed before: ``build`` passed no lowerings at all."""

    paths = _answered_vault(tmp_path, steps=2)
    with closing(connect(paths.sqlite_path)) as connection:
        for k, day in enumerate(("10", "11", "12")):
            start, offered, lowered, end = (f"2026-10-{day}T10:00:00Z", f"2026-10-{day}T10:05:00Z",
                                            f"2026-10-{day}T10:06:00Z", f"2026-10-{day}T10:30:00Z")
            _envelope(connection, "reader_view_opened", {"visit_id": f"v{k}", "extraction_id": "ext1"}, start)
            _offer(connection, key=f"k{k}", visit=f"v{k}", at=offered)
            _envelope(connection, "reader_action_invoked", {"event": "cue_density_changed", "from": "normal",
                                                            "to": "fewer", "via": "footer", "extraction_id": "ext1"},
                      lowered)
            _envelope(connection, "reader_view_closed", {"visit_id": f"v{k}", "active_seconds": 60}, end)
        # Not counted: a raise; a lowering after the visit closed; a lowering before any offer.
        _envelope(connection, "reader_action_invoked", {"event": "cue_density_changed", "from": "fewer",
                                                        "to": "more", "extraction_id": "ext1"}, "2026-10-12T10:07:00Z")
        _envelope(connection, "reader_action_invoked", {"event": "cue_density_changed", "from": "more",
                                                        "to": "off", "extraction_id": "ext1"}, "2026-10-12T11:00:00Z")
        _envelope(connection, "reader_action_invoked", {"event": "cue_density_changed", "from": "more",
                                                        "to": "normal", "extraction_id": "ext1"}, "2026-10-09T09:00:00Z")
        connection.commit()
        assert REP.density_lowerings(connection) == ["2026-10-10T10:06:00Z", "2026-10-11T10:06:00Z",
                                                     "2026-10-12T10:06:00Z"]
    vault = load_vault(paths.root)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        report = REP.build(vault, Repository(paths.sqlite_path), connection, sensitivity=False,
                           now="2026-10-13T00:00:00Z")
    (flag,) = [f for f in report["auto_flags"] if f["flag"] == "dose_offers_a_burden"]
    assert flag["fires"] and flag["detail"]["density_lowerings_14d"] == 3


def test_repeated_reports_fire_the_readiness_flag_through_build(tmp_path, monkeypatch):
    """F8: the production report reads its own earlier windows: with the windows' errors above
    0.05 the flag fires on a plain ``build`` (no history passed in), and stays quiet when only
    this run's report is miscalibrated."""

    paths = _answered_vault(tmp_path, steps=3)
    vault = load_vault(paths.root)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        quiet = REP.build(vault, Repository(paths.sqlite_path), connection, sensitivity=False, report_every=1000)
    (flag,) = [f for f in quiet["auto_flags"] if f["flag"] == "readiness_miscalibrated"]
    assert not flag["fires"] and len(flag["detail"]["errors"]) <= 1
    monkeypatch.setattr(REP, "arm_scores", lambda records, arm, split: {
        "n": len(records), "band_region_error": 0.2, "log_loss": 0.0, "brier": 0.0, "reliability": []})
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        windows = len([r for r in ad_serving.selections(connection) if r["kind"] == "serve"])
        assert windows >= 2
        fired = REP.build(vault, Repository(paths.sqlite_path), connection, sensitivity=False, report_every=1)
    (flag,) = [f for f in fired["auto_flags"] if f["flag"] == "readiness_miscalibrated"]
    assert flag["fires"] and flag["detail"]["errors"] == [0.2, 0.2]


# -- F9: a partly untested LO is never "likely ready" ---------------------------------------------


def test_a_partly_untested_lo_never_reads_likely_ready():
    """F9: two cells, one tested at 0.9, one never answered. Failed before: the line dropped
    the untested cell and read "likely ready"."""

    tested = {"untested": False, "label": RD.LIKELY}
    untested = {"untested": True, "label": RD.UNTESTED}
    line = RD.aggregate_line([tested, untested])
    assert RD.LIKELY not in line and "1 of 2 parts untested" in line and "(a prediction" in line
    assert RD.aggregate_line([tested, tested]).endswith(f"{RD.LIKELY} (a prediction)")
    assert RD.aggregate_line([untested, untested]) == f"Top level for this goal: {RD.UNTESTED}"
    assert RD.LIKELY not in RD.aggregate_line([tested, {"untested": False, "label": RD.NOT_YET}])
