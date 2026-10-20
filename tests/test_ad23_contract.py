"""Adaptive difficulty's A8 contract: protected == absent (fix round 9, ruling R7).

The metamorphic test is the guarantee for spec A8 (the AST scan in ``test_ad23_material_view.py``
stays as a lint). One vault is built and copied twice:

* **protected**: the copy gets protected material of every kind the verifies used: a held-out
  current item with sentinel stem, facet and surface family; a held-out item sharing the public
  items' LO, facet and family; a public item whose earlier ANSWERED revision is held out (its
  snapshot, presentation, frozen serve inputs and attempt); answers on protected material with
  extreme latencies; a reveal of a held-out item; a reveal on the public item that belongs to the
  answer given to its held-out revision (F20, fix round 10); protected completion -> next-serve
  pairs in an earlier plan (F28's feedback dwell); wrong protected answers that would carry the
  incumbent's evidence count past the legacy rung's uncertainty threshold (F21); a commission result
  on a held-out item; a reading receipt from a held-out span; a Reader question citing a held-out
  span, and three delivered dose offers of it, each followed in its visit by a cue-density lowering
  (F35; the visits and lowerings are in both copies);
* **absent**: the copy where that protected material does not exist at all (rows never written;
  the AD decisions that are not derived from it, the base commission draw and the dose draw, are
  kept).

Every AD entry point then runs on both under identical, deterministic ids and clocks: serves with
the slot draw (candidates' estimates included), the serve hook's receipts and the reading sweep,
landing reconciliation, the replay and both rebuilds, the outside forecasters' prompt building, the
commission draw and the commissioned generation request, the report, the dose arm, the reading
sweep on a Reader map, the relatedness proposal, readiness and the router card, and the CLI's
``ad report`` and ``ad eval``. Asserted:

1. no sentinel (a protected id, stem, facet, surface family or question id) appears in any captured
   model request or prompt input;
2. every forecast, selection, estimate, receipt, report figure and sweep write is identical on the
   two copies (the report's ``protection`` disclosure block aside).

Then the same harness with the held-out predicate unavailable (the incumbent serves, no AD model
request, no AD write, late uptake callbacks write nothing), and a no-protection parity case pinning
F30 (a frozen dose on a facet absent from current content stands).

Fix round 10 adds protection that changes over time (the last section): a frozen outside-forecast
history dispatched after an answered revision behind it is held out (F33), a commissioned repair
after protection changed or became unavailable mid-call (F34, with the structural AST test of the
one guarded dispatch), and uptake callbacks with AD off, the dose arm off or the predicate
unavailable (F36).

Fakes only: no network, no model call, no paid call.
"""

from __future__ import annotations

import ast
import json
import re
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

import learnloop.hints.map_builder  # noqa: F401 - imported up front: it mints ids at import time
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import COUPLED, LO, ProposalLLM, ad23_vault, set_item
from tests.daily_plan_fakes import MovableClock, make_env, scheduled
from tests.helpers import write_yaml

EXT = "ext_r9"
HELD = ("h1", "h2", "h3", "h4", "h5")
T0 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
RUN = T0 + timedelta(minutes=30)
PUBLIC = ("pi_p1", "pi_p2", "pi_p3")
SENTINELS = ("SENTINEL_STEM_AX9", "SENTINEL_FACET_AX9", "SENTINEL_FAMILY_AX9", "SENTINEL_HIST_AX9",
             "pi_secret", "pi_shared", "SENTINEL_QUESTION_AX9")
#: AD's tables a run writes (compared as new rows), and its DERIVED tables (compared whole).
AD_WRITES = ("ad_selections", "ad_commission_results", "ad_dose_offers", "ad_reading_opportunities",
             "forecast_receipts", "item_serve_inputs", "ad_relatedness_runs", "attention_block_events",
             "practice_attempts")
AD_DERIVED = ("ad_state", "ad_attempt_trace", "item_forecast_scores")
#: The report's protection disclosure: what the view withheld (it differs by construction).
DISCLOSURE = ("protection", "generated_at")
#: The incumbent's live forecast (AD1's ``mastery_ekf`` receipt): AD records the non-AD system's own
#: mastery state verbatim as its comparator. That state is evidence the incumbent owns (an exam
#: answer is evidence there by design), it trains and selects nothing in AD, and it quotes no
#: material; it is the one AD write whose inputs are not AD's to filter, so the contract compares
#: everything else.
INCUMBENT = "mastery_ekf"
DOSE_DRAW_ID = "dose_draw_r9"
BASE_COMMISSION = "sel_commission_r9"


# -- the vault -------------------------------------------------------------------------------------------


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _copy_item(paths, source: str, target: str, **fields: Any) -> None:
    payload = yaml.safe_load(paths.practice_item_path("linear-algebra", source).read_text(encoding="utf-8"))
    payload.update({"id": target, **fields})
    write_yaml(paths.practice_item_path("linear-algebra", target), payload)


def _attempt(paths, item_id: str, *, at: datetime, latency: int, correct: bool = True,
             presentation_id: str | None = None) -> str:
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.clock import FrozenClock

    draft = AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.", latency_seconds=latency,
                         session_id=None, plan_presentation_id=presentation_id)
    grade = SelfGradeInput(criterion_points={"correctness": 4.0 if correct else 0.0}, confidence=4)
    return str(complete_self_graded_attempt(load_vault(paths.root), Repository(paths.sqlite_path), draft, grade,
                                            clock=FrozenClock(at)).attempt_id)


def _base(tmp_path) -> Any:
    """The public vault: three new items in a planned block, a public item with public history, a
    public reading receipt and a commission draw for the LO's cell."""

    from learnloop.adaptive_difficulty.generation import rung_features
    from learnloop.db.stores import ad_receipts, ad_serving

    from tests.ad23_fakes import env_for

    # No background work: the hints' approach maps are not built on serve (a thread would mint ids
    # and make model calls at its own pace), and AD's own background jobs are off (``ad23_vault``).
    paths = ad23_vault(tmp_path / "base", items=(*PUBLIC, "pi_hist"), ad=COUPLED,
                       config="[router]\nenabled = false\n[hints.maps]\nbuild_on_serve = false\n")
    for item in (*PUBLIC, "pi_hist"):
        set_item(paths, item, surface_family="fam_public")
    _attempt(paths, "pi_hist", at=T0 - timedelta(days=2), latency=90, correct=False)
    _attempt(paths, "pi_hist", at=T0 - timedelta(days=1, hours=12), latency=90, correct=False)
    env, _clock = env_for(paths, items=PUBLIC)
    from learnloop.daily_plan.engine import build_plan

    build_plan(env, kind="normal", budget=9.0, remembered=9, minutes_source="chip")
    with closing(connect(paths.sqlite_path)) as connection:
        ad_receipts.insert_reading_opportunity(connection, {
            "opportunity_key": f"worked_example:{EXT}/public_span:{LO}", "kind": "worked_example",
            "subkind": "in_completed_section", "source_table": "reader_section_progress",
            "source_id": f"{EXT}/public_span", "source_written_at": _iso(T0 - timedelta(days=1)),
            "learning_object_id": LO, "facet_doses": {"recall": 1.0}, "dose_offer_id": None,
            "mapping_version": "ad_reading_map_v1", "sweep": "backfill", "sweep_ref": None,
            "swept_at": _iso(T0 - timedelta(days=1))})
        point = {"complexity": 1, "transfer": "same_context", "scaffolding": "cue", "span": "single_step",
                 "response": "short_constructed"}
        ad_serving.insert_selection(connection, {
            "id": BASE_COMMISSION, "decision_key": "commission:recall:retrieval:r9", "kind": "commission",
            "view": "subject", "learning_object_id": LO, "cell_facet": "recall", "cell_capability": "retrieval",
            "mode": "band", "support": [], "excluded": [], "constants": {}, "seed": "s", "u": 0.5,
            "chosen_item_id": None, "chosen_point": rung_features(point), "propensity": 1.0,
            "empty_support": False, "state_hash": "h", "versions": {}, "algorithm_version": "mvp-0.28",
            "created_at": _iso(T0 - timedelta(days=3))})
        connection.commit()
    return paths


def _paths(root: Path) -> Any:
    from tests.helpers import VaultPaths

    return VaultPaths(root, load_vault(root).config)


def _protect(paths) -> dict[str, Any]:
    """Every kind of protected material, written into this copy only."""

    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.db.stores import ad_receipts, ad_serving

    exercise = lambda span: {"source_id": "src_r9", "extraction_id": EXT, "span_ids": [span]}  # noqa: E731
    _copy_item(paths, "pi_p1", "pi_secret", prompt="SENTINEL_STEM_AX9: a held-out exam question about bases.",
               evidence_facets=["SENTINEL_FACET_AX9"], evidence_weights={"SENTINEL_FACET_AX9": 1.0},
               surface_family="SENTINEL_FAMILY_AX9", canonical_exercise=exercise("h1"))
    _copy_item(paths, "pi_p2", "pi_shared", prompt="A held-out question sharing the public facet and family.",
               canonical_exercise=exercise("h2"))
    # Protected answers: correct, with extreme latencies, on shared LO, facet and family.
    _attempt(paths, "pi_secret", at=T0 - timedelta(hours=3), latency=60000)
    _attempt(paths, "pi_shared", at=T0 - timedelta(hours=2), latency=60000, correct=False)
    _attempt(paths, "pi_shared", at=T0 - timedelta(hours=1, minutes=30), latency=60000, correct=False)
    _attempt(paths, "pi_shared", at=T0 - timedelta(hours=1, minutes=15), latency=60000, correct=False)
    # A public item's earlier answered revision, cut from held-out material.
    vault = load_vault(paths.root)
    from learnloop.vault.models import CanonicalExercise

    historical = vault.practice_items["pi_hist"].model_copy(update={
        "prompt": "SENTINEL_HIST_AX9: the earlier held-out revision.",
        "canonical_exercise": CanonicalExercise(**exercise("h3"))})
    content_hash, item_json = item_revision(historical)
    with closing(connect(paths.sqlite_path)) as connection:
        (block_id,) = connection.execute("SELECT id FROM attention_blocks ORDER BY rowid LIMIT 1").fetchone()
        connection.execute("INSERT INTO practice_item_snapshots(content_hash, practice_item_id, item_json, created_at) "
                           "VALUES (?, 'pi_hist', ?, ?)", (content_hash, item_json, _iso(T0 - timedelta(hours=1))))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_hist_r9', ?, 'pi_hist', 'chooser', ?)",
                           (block_id, _iso(T0 - timedelta(hours=1))))
        connection.execute(
            "INSERT INTO item_serve_inputs(id, receipt_key, presentation_kind, plan_presentation_id, practice_item_id, "
            "learning_object_id, content_hash, served_at, audit_json, signals_json, pre_exposed, resolution_version, "
            "created_at) VALUES ('isi_hist_r9', 'plan_presentation:pp_hist_r9', 'plan_presentation', 'pp_hist_r9', "
            "'pi_hist', ?, ?, ?, '{}', '{}', 0, 'r9', ?)",
            (LO, content_hash, _iso(T0 - timedelta(hours=1)), _iso(T0 - timedelta(hours=1))))
        connection.commit()
    # Wrong, so the incumbent's evidence on the LO reaches three with a low ability: the legacy rung
    # would drop its uncertainty step (Codex verify F21's threshold transition, fix round 10).
    hist_attempt = _attempt(paths, "pi_hist", at=T0 - timedelta(minutes=50), latency=60000,
                            presentation_id="pp_hist_r9", correct=False)
    repository = Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, "
                           "basis, created_at) VALUES ('rv_r9', 'pi_secret', ?, 'tutor_answer', 1.0, 'overlap', ?)",
                           (LO, _iso(T0 - timedelta(minutes=40))))
        # A reveal on the PUBLIC item, belonging to the answer given to its held-out revision (F20).
        connection.execute("INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, "
                           "basis, attempt_id, created_at) VALUES ('rv_hist_r9', 'pi_hist', ?, 'answer_display', 1.0, "
                           "'overlap', ?, ?)", (LO, hist_attempt, _iso(T0 - timedelta(minutes=45))))
        # Protected completion -> next-serve pairs on an earlier plan (F28): five-minute feedback dwell.
        secret_attempt = connection.execute(
            "SELECT id FROM practice_attempts WHERE practice_item_id = 'pi_secret'").fetchone()[0]
        connection.execute(
            "INSERT INTO daily_plans(id, local_date, kind, minutes_budget, remembered_minutes, minutes_source, "
            "split_json, admission_json, estimator_version, source, chooser, status, algorithm_version, config_hash, "
            "created_at, updated_at) VALUES ('plan_old_r9', '2026-10-05', 'normal', 60, 60, 'chip', '{}', '{}', 'x', "
            "'x', 'x', 'complete', 'mvp-0.28', 'h', '2026-10-05T09:00:00Z', '2026-10-05T09:00:00Z')")
        connection.execute(
            "INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at, daily_plan_id, "
            "plan_ordinal) VALUES ('blk_old_r9', 'practice', 60, 'h', '2026-10-05T09:00:00Z', 'plan_old_r9', 1)")
        for k in range(10):
            done = datetime(2026, 10, 5, 9, 0, tzinfo=UTC) + timedelta(minutes=10 * k)
            connection.execute(
                "INSERT INTO attention_block_events(id, block_id, event_ordinal, kind, detail_json, created_at) "
                "VALUES (?, 'blk_old_r9', ?, 'item_done', ?, ?)",
                (f"ev_done_r9_{k}", 2 * k, json.dumps({"practice_item_id": "pi_secret", "attempt_id": secret_attempt,
                                                       "done_at": _iso(done)}), _iso(done)))
            connection.execute(
                "INSERT INTO attention_block_events(id, block_id, event_ordinal, kind, detail_json, created_at) "
                "VALUES (?, 'blk_old_r9', ?, 'item_served', ?, ?)",
                (f"ev_served_r9_{k}", 2 * k + 1, json.dumps({"practice_item_id": "pi_shared"}),
                 _iso(done + timedelta(minutes=5))))
        secret = load_vault(paths.root).practice_items["pi_secret"]
        ad_serving.insert_commission_result(connection, {
            "selection_id": BASE_COMMISSION, "practice_item_id": "pi_secret",
            "content_hash": item_revision(secret)[0], "features": {"complexity": 1}, "p_bar": 0.99,
            "status": "realized_out_of_band", "state_hash": "h", "features_match": 1, "landed_after_expiry": 0,
            "created_at": _iso(T0 - timedelta(minutes=35))})
        ad_receipts.insert_reading_opportunity(connection, {
            "opportunity_key": f"worked_example:{EXT}/h5:{LO}", "kind": "worked_example",
            "subkind": "in_completed_section", "source_table": "reader_section_progress",
            "source_id": f"{EXT}/h5", "source_written_at": _iso(T0 - timedelta(minutes=20)),
            "learning_object_id": LO, "facet_doses": {"SENTINEL_FACET_AX9": 1.0}, "dose_offer_id": None,
            "mapping_version": "ad_reading_map_v1", "sweep": "backfill", "sweep_ref": None,
            "swept_at": _iso(T0 - timedelta(minutes=20))})
        connection.commit()
    question = repository.insert_reader_authored_question(fields={
        "extraction_id": EXT, "section_id": "sec1", "source_id": "src_r9",
        "question_md": "SENTINEL_QUESTION_AX9: what does the held-out passage say?", "expected_answer_md": "x",
        "span_ids": ["h4"], "prompt_version": "qc-v1", "scope_kind": "inquiry", "question_style": "recall",
        "anchor_span_ids": ["public_anchor"], "inquiry_root_event_id": "root-r9"}, clock=_Frozen(T0))
    # An answered question with a public anchor citing a held-out span (Codex verify F31), and its
    # self-check verdict: the sweep must write nothing for either.
    from learnloop.reader import reader_quick_check as RQC

    answered = repository.insert_reader_authored_question(fields={
        "extraction_id": EXT, "section_id": "sec1", "source_id": "src_r9",
        "question_md": "SENTINEL_QUESTION_AX9: and why?", "expected_answer_md": "x", "span_ids": ["h4"],
        "prompt_version": "qc-v1", "scope_kind": "inquiry", "question_style": "recall",
        "anchor_span_ids": ["public_anchor"], "inquiry_root_event_id": "root-r9-answered"}, clock=_Frozen(T0))
    RQC.record_inquiry_action(repository, question_id=answered, action="answered", response_md="my words",
                              clock=_Frozen(T0 + timedelta(minutes=1)))
    RQC.record_inquiry_action(repository, question_id=answered, action="self_checked", self_check="partly",
                              clock=_Frozen(T0 + timedelta(minutes=2)))
    return {"question": question}


class _Frozen:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def now(self) -> datetime:
        return self.at


def _protected_offers(paths, question_id: str) -> None:
    """Three dose draws that offered the protected question, each delivered in its own visit (F35).
    They are derived from protected material, so the absent copy never has them."""

    from learnloop.db.stores import ad_serving

    with closing(connect(paths.sqlite_path)) as connection:
        for k in range(3):
            at = _iso(T0 - timedelta(days=3 - k, minutes=-5))
            draw = ad_serving.insert_dose_row(connection, {
                "id": f"{DOSE_DRAW_ID}_{k}", "row_kind": "draw", "draw_key": f"visit_r9_{k}:{EXT}:sec{k + 2}",
                "visit_id": f"visit_r9_{k}", "extraction_id": EXT, "section_id": f"sec{k + 2}",
                "learning_object_ids": [LO], "feasible": ["none", "extra_question"], "infeasible": {}, "base_version": "b",
                "floor": 0.1, "propensities": {"none": 0.9, "extra_question": 0.1}, "seed": "s", "u": 0.95,
                "chosen_variant": "extra_question", "content": {"question_id": question_id, "style": "recall"},
                "forecast_p": None, "detail": {}, "created_at": at})
            ad_serving.insert_dose_row(connection, {"row_kind": "delivered", "draw_id": draw, "created_at": at})
        connection.commit()


def _visits_with_lowerings(paths) -> None:
    """Reader telemetry in both copies: three visits, each with a cue-density lowering after the time
    an offer was (in the protected copy) delivered. Not protected material: the extraction is not held
    out as a whole."""

    with closing(connect(paths.sqlite_path)) as connection:
        for k in range(3):
            start = T0 - timedelta(days=3 - k)
            events = (("reader_view_opened", {"visit_id": f"visit_r9_{k}", "extraction_id": EXT}, start),
                      ("reader_action_invoked", {"event": "cue_density_changed", "from": "normal", "to": "fewer",
                                                 "extraction_id": EXT}, start + timedelta(minutes=6)),
                      ("reader_view_closed", {"visit_id": f"visit_r9_{k}", "active_seconds": 60},
                       start + timedelta(minutes=30)))
            for kind, payload, at in events:
                connection.execute(
                    "INSERT INTO interaction_events(id, kind, origin, subject_type, subject_id, payload_json, created_at) "
                    "VALUES (?, ?, 'learner', 'reader', ?, ?, ?)",
                    (f"ev_{kind}_{k}_r9", kind, EXT, json.dumps(payload), _iso(at)))
        connection.commit()


def _hold_out(monkeypatch) -> None:
    from learnloop.content.sources import exam_material

    material = exam_material.Material(spans=frozenset((EXT, span) for span in HELD))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)


def _predicate_raises(monkeypatch) -> None:
    from learnloop.content.sources import exam_material

    def broken(*_args, **_kwargs):
        raise RuntimeError("held-out source sets unreadable")

    monkeypatch.setattr(exam_material, "held_out_material", broken)


# -- deterministic runs ----------------------------------------------------------------------------------


def _deterministic(monkeypatch) -> None:
    """Identical ids and wall-clock reads on both copies: the ULID generator counts from a fixed
    instant, and the system clock reads ``RUN``."""

    import learnloop.clock as clock_module
    import learnloop.ids as ids

    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: 1_790_000_000_000)
    monkeypatch.setattr(ids, "secrets", SimpleNamespace(randbits=lambda bits: 0))
    _reset_ids(monkeypatch)
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: RUN)


def _reset_ids(monkeypatch, stage: int = 0) -> None:
    """Each entry point mints ids from its own fixed millisecond, so a non-AD write an earlier
    entry point made only in one copy (state sync of the protected items) never shifts the ids
    of a later one, and no two stages mint the same id."""

    import learnloop.ids as ids

    monkeypatch.setattr(ids, "_last_timestamp_ms", 1_790_000_000_000 + 1_000 * stage)
    monkeypatch.setattr(ids, "_last_randomness", 0)


class _ReadingMap:
    """The Reader's mapping for the harness's extraction: one section on the LO."""

    def __init__(self, view: Any) -> None:
        self.view = view

    def los_for_section(self, extraction_id, section_id):
        return [LO] if (extraction_id, section_id) == (EXT, "sec1") else []

    def los_for_span(self, extraction_id, span_id):
        return [LO] if extraction_id == EXT else []

    def section_spans(self, extraction_id, section_id):
        return ["public_anchor", "public_span"]

    def worked_example_spans(self, extraction_id):
        return {"public_span"}

    def withheld(self, extraction_id, span_id):
        return self.view.material_withheld(extraction_id, span_id)

    def los_for_note(self, note_id):
        return []

    def lo_for_item(self, practice_item_id):
        return self.view.lo_for_item(practice_item_id)

    def facets_for_lo(self, learning_object_id):
        lo = self.view.vault.learning_objects.get(learning_object_id)
        return self.view.lo_facets(lo) if lo is not None else []


def _rows(path, table: str) -> list[tuple]:
    with closing(connect(path, read_only=True)) as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (table,)).fetchone() is None:
            return []
        cursor = connection.execute(f"SELECT * FROM {table}")
        return sorted((tuple(row) for row in cursor.fetchall()), key=repr)


def _strip(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip(v) for k, v in value.items() if k not in DISCLOSURE}
    if isinstance(value, list):
        return [_strip(v) for v in value]
    return value


class _Generator:
    """The commissioned generation's model client: records the serialized authoring request."""

    provider_name = "codex"
    provider_type = "test"
    model = "fake-generator"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def run_authoring_proposal(self, context):
        from learnloop.content.proposals.ai_contracts import AuthoringProposal
        from learnloop.content.proposals.proposals import authoring_prompt

        self.prompts.append(authoring_prompt(context))
        return AuthoringProposal.model_validate({"summary": "nothing", "source_refs": [], "items": []})


def _structured(generator: _Generator) -> Any:
    from tests.structured_ai import StructuredClientFake

    class Client(StructuredClientFake):
        provider_name = "codex"
        provider_type = "test"
        model = "fake-generator"

        def run_authoring_proposal(self, context):
            return generator.run_authoring_proposal(context)

    return Client()


def _run(paths, monkeypatch) -> dict[str, Any]:
    """Every AD entry point on this copy; returns what each produced (and every captured prompt)."""

    from typer.testing import CliRunner

    from learnloop.adaptive_difficulty import dose as D
    from learnloop.adaptive_difficulty import readiness as RD
    from learnloop.adaptive_difficulty import relatedness as R
    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty import report as REP
    from learnloop.adaptive_difficulty import scoring
    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.adaptive_difficulty.outside import history_card, item_view
    from learnloop.adaptive_difficulty.reading import sweep
    from learnloop.cli.app import app
    from learnloop.content.authoring.practice_generation import generate_post_probe_practice_proposal
    from learnloop.daily_plan import ad_slot
    from learnloop.daily_plan.engine import advance

    _reset_ids(monkeypatch)
    RP.clear_cache()
    out: dict[str, Any] = {"prompts": []}
    before = {table: set(_rows(paths.sqlite_path, table)) for table in AD_WRITES}

    # Serves: the slot draw (with its candidates' estimates), the serve hook, an answer, a second serve.
    requests: list[Any] = []
    real_build = ad_slot.build_request

    def spy(*args, **kwargs):
        request = real_build(*args, **kwargs)
        requests.append([(c.practice_item_id, list(c.failed), c.est_minutes) for c in request.candidates])
        return request

    monkeypatch.setattr(ad_slot, "build_request", spy)
    vault = load_vault(paths.root)
    clock = MovableClock(RUN)
    env = make_env(paths.root, [scheduled(item, LO, forgetting_risk=0.6) for item in PUBLIC], clock=clock,
                   session_id=None)
    steps = []
    for _ in range(2):
        _record, step = advance(env, serve=True)
        steps.append({k: step.get(k) for k in ("kind", "practice_item_id", "adaptive_difficulty")})
        if step.get("kind") == "item":
            clock.advance(3)
            _attempt(paths, step["practice_item_id"], at=clock.now(), latency=120, presentation_id=step["presentation_id"])
            clock.advance(1)
    monkeypatch.setattr(ad_slot, "build_request", real_build)
    out["steps"], out["estimates"] = steps, requests

    # The replay, its rebuild and the forecast-score rebuild.
    _reset_ids(monkeypatch, 1)
    RP.clear_cache()
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    RP.rebuild(vault, repository)
    scoring.rebuild(vault, repository)

    # The outside forecasters' prompt inputs for a public item.
    view = material_view(vault, repository)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        card = history_card(vault, connection, vault.practice_items["pi_p3"], served_at=_iso(RUN), view=view,
                            incumbent=None)
    out["outside"] = json.dumps({"item": item_view(vault, vault.practice_items["pi_p3"]), "card": card},
                                sort_keys=True, default=str)
    out["prompts"].append(out["outside"])

    # The commission draw and the commissioned generation request.
    _reset_ids(monkeypatch, 2)
    generator = _Generator()
    try:
        generate_post_probe_practice_proposal(paths.root, _structured(generator), learning_object_ids=[LO],
                                              require_completed_probe=False, target_items_per_lo=9,
                                              max_new_per_lo=1)
    except Exception as exc:  # noqa: BLE001 - the outcome is compared, whatever it is
        out["generation_error"] = type(exc).__name__ + ": " + str(exc)
    out["generation"] = generator.prompts
    out["prompts"] += generator.prompts

    # The relatedness proposal (its request is captured, never sent).
    _reset_ids(monkeypatch, 3)
    llm = ProposalLLM({"items": [], "learning_objects": []})
    vault = load_vault(paths.root)
    out["relatedness_inputs"] = json.dumps(R.subject_inputs(vault, repository, "linear-algebra")["payload"],
                                           sort_keys=True)
    out["relatedness"] = R.propose_subject(vault, repository, "linear-algebra", client=llm).status
    out["prompts"] += [out["relatedness_inputs"], *llm.prompts]

    # Readiness and the router card.
    RP.clear_cache()
    out["readiness"] = RD.lo_readiness(vault, repository, LO)
    out["card"] = RD.card_fields(vault, repository, LO)

    # The dose arm: a fresh boundary, and the boundary of the earlier draw that offered the question.
    _reset_ids(monkeypatch, 4)
    dose_view = material_view(vault, repository)
    fresh = D.decide(vault, repository, D.Boundary(visit_id="visit_new", extraction_id=EXT, section_id="sec1"),
                     clock=_Frozen(RUN), reading_map=_ReadingMap(dose_view), view=dose_view)
    old = D.decide(vault, repository, D.Boundary(visit_id="visit_old", extraction_id=EXT, section_id="sec1"),
                   clock=_Frozen(RUN), reading_map=_ReadingMap(dose_view), view=dose_view)
    out["dose"] = [fresh.as_dict()]
    out["dose_old_boundary"] = old.as_dict()
    # A late uptake callback for each earlier offer (protected in one copy, absent in the other).
    out["uptake"] = [D.record_uptake(vault, repository, f"{DOSE_DRAW_ID}_{k}", "taken", clock=_Frozen(RUN))
                     if _has_draw(paths, f"{DOSE_DRAW_ID}_{k}") else None for k in range(3)]

    # The reading sweep (a backfill: every source).
    _reset_ids(monkeypatch, 5)
    out["sweep"] = sweep(vault, repository, as_of=_iso(RUN), sweep_kind="backfill",
                         reading_map=_ReadingMap(dose_view), view=dose_view).as_dict()

    # The report and the CLI's figures.
    RP.clear_cache()
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        out["report"] = _strip(json.loads(json.dumps(REP.build(vault, repository, connection, sensitivity=True,
                                                               now=_iso(RUN)), default=str)))
    runner = CliRunner()
    for command in (["ad", "report", "--json", "--vault", str(paths.root)],
                    ["ad", "eval", "--json", "--vault", str(paths.root)]):
        RP.clear_cache()
        result = runner.invoke(app, command)
        out[" ".join(command[:2])] = _strip(json.loads(result.stdout)) if result.stdout.strip().startswith("{") \
            else result.stdout

    out["writes"] = {table: [row for row in sorted(set(_rows(paths.sqlite_path, table)) - before[table], key=repr)
                             if INCUMBENT not in row] for table in AD_WRITES}
    out["derived"] = {table: [row for row in _rows(paths.sqlite_path, table) if INCUMBENT not in row]
                      for table in AD_DERIVED}
    return out


def _normalized(out: dict[str, Any], root: Path) -> dict[str, Any]:
    """The copy's own path is the only text that differs by construction."""

    return json.loads(json.dumps(out, default=str).replace(str(root), "<vault>"))


def _has_draw(paths, draw_id: str) -> bool:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return connection.execute("SELECT 1 FROM ad_dose_offers WHERE id = ?", (draw_id,)).fetchone() is not None


def _sentinel_hits(texts: list[str]) -> list[str]:
    return [f"{token} in a captured request" for token in SENTINELS for text in texts
            if re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", text)]


@pytest.fixture
def copies(tmp_path, monkeypatch):
    base = _base(tmp_path)
    protected, absent = tmp_path / "protected", tmp_path / "absent"
    copy_tree_with_databases(base.root, protected)
    copy_tree_with_databases(base.root, absent)
    protected_paths, absent_paths = _paths(protected), _paths(absent)
    for paths in (protected_paths, absent_paths):
        _visits_with_lowerings(paths)
    seeded = _protect(protected_paths)
    _protected_offers(protected_paths, seeded["question"])
    return protected_paths, absent_paths


def _diff(left: Any, right: Any, path: str = "") -> list[str]:
    if isinstance(left, dict) and isinstance(right, dict):
        out = []
        for key in sorted(set(left) | set(right), key=str):
            out += _diff(left.get(key), right.get(key), f"{path}.{key}")
        return out
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        out = []
        for index, (a, b) in enumerate(zip(left, right)):
            out += _diff(a, b, f"{path}[{index}]")
        return out
    if isinstance(left, str) and isinstance(right, str) and left != right:
        at = next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), min(len(left), len(right)))
        return [f"{path}: strings differ at {at}: {left[max(0, at - 150):at + 150]!r} != "
                f"{right[max(0, at - 150):at + 150]!r}"]
    return [] if left == right else [f"{path}: {left!r} != {right!r}"[:600]]


# -- the contract ----------------------------------------------------------------------------------------


def test_protected_material_is_indistinguishable_from_absent_material(copies, monkeypatch):
    """A8's contract (R7): with every kind of protected material present and protected, every AD
    entry point produces exactly what it produces when that material does not exist, and no
    captured model request quotes any of it."""

    protected, absent = copies
    _hold_out(monkeypatch)
    _deterministic(monkeypatch)
    seen = _normalized(_run(protected, monkeypatch), protected.root)
    want = _normalized(_run(absent, monkeypatch), absent.root)
    assert _sentinel_hits(seen["prompts"]) == []
    assert seen["steps"][0]["kind"] == "item" and seen["estimates"], "the slot draw ran"
    assert seen["generation"], "the commissioned request was built"
    differences = _diff(seen, want)
    assert differences == [], "\n".join(differences[:40])


def test_with_the_predicate_unavailable_ad_does_nothing_and_the_incumbent_serves(copies, monkeypatch):
    """R7, unavailable: the incumbent serves the planned items, no AD model request is built, and
    no AD row is written."""

    protected, _absent = copies
    _predicate_raises(monkeypatch)
    _deterministic(monkeypatch)
    seen = _run(protected, monkeypatch)
    assert [step["kind"] for step in seen["steps"]] == ["item", "item"]
    assert all(step.get("adaptive_difficulty") is None for step in seen["steps"])
    assert seen["estimates"] == []
    writes = seen["writes"]
    for table in ("ad_selections", "ad_commission_results", "ad_dose_offers", "ad_reading_opportunities",
                  "item_serve_inputs", "ad_relatedness_runs"):
        assert writes[table] == [], table
    assert all("item_unassisted_success" not in json.dumps(row, default=str) for row in writes["forecast_receipts"])
    assert seen["relatedness"] == "unavailable" and seen["dose"][0]["reason"] == "protection_unavailable"
    assert seen["sweep"]["written"] == 0
    assert seen["uptake"] == [None, None, None], "a late uptake callback writes nothing (F36)"
    # Generation takes the predecessor's target: no AD contract text, no commission.
    from learnloop.adaptive_difficulty.generation import CONTRACT_TEXT

    assert all(CONTRACT_TEXT not in prompt for prompt in seen["generation"])
    assert _sentinel_hits([seen["outside"], seen["relatedness_inputs"]]) == []
    assert seen["report"]["selection"] == {"suppressed": "held_out_predicate_unavailable"}
    assert seen["report"]["records"] == 0


def test_with_no_protection_a_frozen_dose_on_an_absent_facet_stands(tmp_path):
    """R7's no-protection parity (Codex verify F30): a reading receipt's dose on a facet that only a
    since-deleted item named stands as recorded (round 7's behaviour); nothing is protected."""

    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.db.stores import ad_receipts

    paths = ad23_vault(tmp_path, items=("pi_keep", "pi_gone"), config="[router]\nenabled = false\n")
    set_item(paths, "pi_gone", evidence_facets=["f_only_gone"], evidence_weights={"f_only_gone": 1.0})
    with closing(connect(paths.sqlite_path)) as connection:
        ad_receipts.insert_reading_opportunity(connection, {
            "opportunity_key": f"worked_example:{EXT}/w1:{LO}", "kind": "worked_example",
            "subkind": "in_completed_section", "source_table": "reader_section_progress",
            "source_id": f"{EXT}/w1", "source_written_at": "2026-10-01T09:00:00Z", "learning_object_id": LO,
            "facet_doses": {"f_only_gone": 1.0}, "dose_offer_id": None, "mapping_version": "ad_reading_map_v1",
            "sweep": "backfill", "sweep_ref": None, "swept_at": "2026-10-01T09:00:00Z"})
        connection.commit()
    paths.practice_item_path("linear-algebra", "pi_gone").unlink()
    RP.clear_cache()
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        events = RP.load_events(connection, load_vault(paths.root), Repository(paths.sqlite_path))
    (opportunity,) = events.opportunities
    assert opportunity.facet_doses == {"f_only_gone": 1.0}


# -- fix round 10 (R8): protection that changes over time --------------------------------------------
#
# The scenarios above compare two copies at one moment. These pin what happens when protection
# changes between two moments of one operation: a frozen history dispatched later (F33), a repair
# requested after the first request (F34), and a late uptake callback (F36).


def _hold(monkeypatch, spans) -> None:
    from learnloop.content.sources import exam_material

    material = exam_material.Material(spans=frozenset((EXT, span) for span in spans))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)


# -- F33 ---------------------------------------------------------------------------------------------


def test_a_frozen_history_is_refused_once_an_answered_revision_behind_it_is_held_out(tmp_path, monkeypatch):
    """R4: the history card is frozen while ``pi_hist``'s earlier answered revision (span ``h3``) is
    public: its entry records the attempt and that revision's source identity. ``h3`` is then held
    out; dispatching the frozen request is refused for both forecasters and nothing reaches the
    model (failed before: only the current revision's identity was frozen, so it was sent)."""

    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation, freeze_presentation_inputs
    from learnloop.adaptive_difficulty.switches import LLM_V3_DECIDER, LLM_V3_LLM

    from tests.ad_fakes import AuditDecider, ForecastLLM

    paths = _base(tmp_path)
    _protect(paths)
    _hold(monkeypatch, [span for span in HELD if span != "h3"])
    vault = load_vault(paths.root)
    vault.config.adaptive_difficulty.outside_forecasters = [LLM_V3_LLM, LLM_V3_DECIDER]
    repository = Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path)) as connection:
        (block_id,) = connection.execute("SELECT id FROM attention_blocks ORDER BY rowid LIMIT 1").fetchone()
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_target_r10', ?, 'pi_p3', 'chooser', ?)", (block_id, _iso(RUN)))
        view = material_view(vault, repository)
        key = freeze_presentation_inputs(vault, connection, vault.practice_items["pi_p3"],
                                         presentation_id="pp_target_r10", served_at=_iso(RUN),
                                         protected=view.protection, view=view)
        connection.commit()
    assert key is not None
    from learnloop.db.stores import ad_receipts

    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        (frozen,) = [row["content"] for row in ad_receipts.payloads(connection, [key])]
    identities = frozen["protection_identities"]
    assert identities["history_attempts"], "the history quotes the held-out revision's answer"
    assert any(identity.get("attempt_id") and ["ext_r9", "h3"] in identity.get("keys", [])
               for identity in identities["history"])
    _hold(monkeypatch, HELD)  # h3 is held out now
    llm = ForecastLLM()
    outcomes = forecast_presentation(vault, repository, "pp_target_r10", clients=Clients(llm=llm, decider=AuditDecider()))
    assert {outcome.status for outcome in outcomes} == {"protected"} and llm.prompts == []


# -- F34 ---------------------------------------------------------------------------------------------


def _flipping_client(monkeypatch, flip):
    from learnloop.content.proposals.ai_contracts import AuthoringProposal

    from tests.test_proposal_persistence import _QueueAuthoringClient, _generated_practice_proposal_payload

    broken = _generated_practice_proposal_payload({"evidence_facets": ["application"],
                                                   "evidence_weights": {"application": 1.0}})
    broken["items"][0]["audit"] = {"audit_type": "deterministic_validator", "status": "not_applicable_with_trace",
                                   "summary": "Conceptual item; no numeric validation."}

    class Flipping(_QueueAuthoringClient):
        def run_authoring_proposal(self, context):
            proposal = super().run_authoring_proposal(context)
            flip()  # protection changes while the first request runs
            return proposal

    return Flipping([AuthoringProposal.model_validate(broken), AuthoringProposal.model_validate(broken)])


@pytest.mark.parametrize("change", ["held_out", "unavailable"])
def test_a_commissioned_repair_after_protection_changed_mid_call_is_refused(tmp_path, monkeypatch, change):
    """R5: the first commissioned request passes its guard; during it a context item becomes held
    out (or the predicate becomes unreadable), and its answer has an invalid item, so a repair is
    due. The repair goes through the one guarded dispatch with protection read afresh: refused,
    propagated as a refusal, and never sent (failed before: the repair was sent with the protected
    context, or a guard failure was swallowed as a repair failure)."""

    import yaml

    from learnloop.adaptive_difficulty.generation import CommissionedRequestGuard
    from learnloop.clock import FrozenClock
    from learnloop.content.proposals.proposals import AuthoringRequestRefused, generate_authoring_proposal

    from tests.helpers import create_basic_vault, write_yaml

    paths = create_basic_vault(tmp_path / "vault")
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    payload = yaml.safe_load(item_path.read_text(encoding="utf-8"))
    payload["canonical_exercise"] = {"source_id": "src_r9", "extraction_id": EXT, "span_ids": ["h_mid"]}
    write_yaml(item_path, payload)
    _hold(monkeypatch, [])

    def flip() -> None:
        if change == "held_out":
            _hold(monkeypatch, ["h_mid"])
        else:
            _predicate_raises(monkeypatch)

    client = _flipping_client(monkeypatch, flip)
    guard = CommissionedRequestGuard()
    with pytest.raises(AuthoringRequestRefused):
        generate_authoring_proposal(paths.root, client, vault_view=guard.vault_view, request_guard=guard,
                                    clock=FrozenClock(T0))
    assert len(client.contexts) == 1, "the repair request was never sent"


def test_request_authoring_proposal_is_called_from_the_guarded_dispatch_only():
    """R5 (structural): the authoring model request is made in one function,
    ``dispatch_authoring_request``; every plan-based generator that can carry an AD commission
    passes AD's request options, and the only unguarded caller is the diagnostic authoring path
    (never commissioned)."""

    root = Path(__file__).resolve().parents[1] / "src" / "learnloop"
    callers: list[tuple[str, str]] = []
    unguarded: list[tuple[str, str]] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            for node in ast.walk(function):
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
                if name == "request_authoring_proposal":
                    callers.append((path.name, function.name))
                if name == "dispatch_authoring_request" and not any(k.arg == "request_guard" for k in node.keywords):
                    unguarded.append((path.name, function.name))
    assert set(callers) == {("proposals.py", "dispatch_authoring_request")}
    assert set(unguarded) == {("proposals.py", "generate_diagnostic_proposal")}, unguarded
    source = (root / "content" / "authoring" / "practice_generation.py").read_text(encoding="utf-8")
    for generator in ("generate_post_probe_practice_proposal", "generate_goal_practice_proposal",
                      "generate_cross_source_practice_proposal"):
        body = source[source.index(f"def {generator}("):]
        body = body[:body.index("\ndef ", 1)]
        assert "**_ad_request_options(plan)" in body, generator


# -- F36 ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["ad_off", "dose_off", "unavailable"])
def test_a_late_uptake_callback_writes_nothing_when_ad_cannot_record_it(tmp_path, monkeypatch, state):
    """R7: an offer exists; then AD is turned off, the dose arm is turned off, or the predicate
    becomes unavailable. The callback writes no row and answers a no-op (failed before: it appended
    ``taken`` whatever the switches)."""

    from learnloop.adaptive_difficulty import dose as D
    from learnloop.db.stores import ad_serving

    from tests.test_ad3_dose_arm import _arm, _boundary, _draws, _mapping
    from tests.test_ad1_reading_opportunities import _question, at

    paths, vault, repo = _arm(tmp_path)
    _question(repo, "recall", 1, answer=False)
    with closing(connect(paths.sqlite_path)) as connection:
        draw = ad_serving.insert_dose_row(connection, {
            "row_kind": "draw", "draw_key": "visit_r10:ext1:u1", "visit_id": "visit_r10", "extraction_id": "ext1",
            "section_id": "u1", "learning_object_ids": ["lo_svd_definition"], "feasible": ["none", "extra_worked_example"],
            "infeasible": {}, "base_version": "b", "floor": 0.1,
            "propensities": {"none": 0.9, "extra_worked_example": 0.1}, "seed": "s", "u": 0.95,
            "chosen_variant": "extra_worked_example", "content": {"extraction_id": "ext1", "span_id": "we2"},
            "forecast_p": None, "detail": {}, "created_at": "2026-10-12T09:00:00Z"})
        connection.commit()
    if state == "ad_off":
        vault.config.adaptive_difficulty.enabled = False
    elif state == "dose_off":
        vault.config.adaptive_difficulty.reading_dose_offers = False
    else:
        _predicate_raises(monkeypatch)
    assert D.record_uptake(vault, repo, draw, "taken", clock=at(3)) is None
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert [row for row in ad_serving.dose_rows(connection) if row["row_kind"] != "draw"] == []


def test_the_sidecar_uptake_callback_answers_a_no_op_with_ad_off(tmp_path):
    """R7 at the RPC: ``reader.dose_offer_event`` for an existing offer after AD is turned off
    records nothing and says so (``recorded: false``); with AD on it records (failed before: the
    handler wrote ``taken`` whatever the switches)."""

    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop.db.stores import ad_serving
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    from tests.test_ad3_dose_arm import _arm

    paths, _vault, _repo = _arm(tmp_path)
    with closing(connect(paths.sqlite_path)) as connection:
        draws = [ad_serving.insert_dose_row(connection, {
            "row_kind": "draw", "draw_key": f"visit_s{k}:ext1:u1", "visit_id": f"visit_s{k}", "extraction_id": "ext1",
            "section_id": "u1", "learning_object_ids": ["lo_svd_definition"], "feasible": ["none", "extra_worked_example"],
            "infeasible": {}, "base_version": "b", "floor": 0.1,
            "propensities": {"none": 0.9, "extra_worked_example": 0.1}, "seed": "s", "u": 0.95,
            "chosen_variant": "extra_worked_example", "content": {"extraction_id": "ext1", "span_id": "we2"},
            "forecast_p": None, "detail": {}, "created_at": "2026-10-12T09:00:00Z"}) for k in range(2)]
        connection.commit()
    spec = METHOD_REGISTRY["reader.dose_offer_event"]
    ctx = SidecarContext()
    ctx.load(paths.root)
    try:
        on = spec.handler(ctx, spec.params_model.model_validate({"drawId": draws[0], "event": "taken"}))
        vault, _repository = ctx.require_vault()
        vault.config.adaptive_difficulty.enabled = False
        off = spec.handler(ctx, spec.params_model.model_validate({"drawId": draws[1], "event": "taken"}))
    finally:
        ctx.map_builds.close()
    assert on["recorded"] is True and on["rowId"]
    assert off["recorded"] is False and off["rowId"] is None
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert [row["draw_id"] for row in ad_serving.dose_rows(connection) if row["row_kind"] == "taken"] == [draws[0]]


# -- F28 (R3): a serve withheld with its presentation ---------------------------------------------------


def test_feedback_dwell_skips_a_serve_withheld_with_its_presentation(tmp_path, monkeypatch):
    """R3: plan events name no presentation, so a serve of a PUBLIC item whose presentation froze a
    held-out revision is found by its block and item. AD's dwell skips it, and the completion that
    follows it, as if neither were written: done(pi_p1) -> served(pi_p2) is one 4-minute pair, as on
    a copy without them; the incumbent's default reader still pairs every event (1 and 1 minute).
    Failed before: AD's estimator had no event rule (the plan's raw dwell)."""

    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.daily_plan.estimates import load_duration_evidence

    paths = _base(tmp_path)
    _protect(paths)
    _hold_out(monkeypatch)
    with closing(connect(paths.sqlite_path)) as connection:
        (content_hash,) = connection.execute(
            "SELECT content_hash FROM item_serve_inputs WHERE id = 'isi_hist_r9'").fetchone()
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_hist_old_r10', 'blk_old_r9', 'pi_hist', 'chooser', '2026-10-05T12:01:00Z')")
        connection.execute(
            "INSERT INTO item_serve_inputs(id, receipt_key, presentation_kind, plan_presentation_id, practice_item_id, "
            "learning_object_id, content_hash, served_at, audit_json, signals_json, pre_exposed, resolution_version, "
            "created_at) VALUES ('isi_hist_old_r10', 'plan_presentation:pp_hist_old_r10', 'plan_presentation', "
            "'pp_hist_old_r10', 'pi_hist', ?, ?, '2026-10-05T12:01:00Z', '{}', '{}', 0, 'r10', "
            "'2026-10-05T12:01:00Z')", (LO, content_hash))
        events = (("item_done", {"practice_item_id": "pi_p1", "done_at": "2026-10-05T12:00:00Z"}, "12:00"),
                  ("item_served", {"practice_item_id": "pi_hist"}, "12:01"),
                  ("item_done", {"practice_item_id": "pi_hist", "done_at": "2026-10-05T12:03:00Z"}, "12:03"),
                  ("item_served", {"practice_item_id": "pi_p2"}, "12:04"))
        for ordinal, (kind, detail, at) in enumerate(events, start=100):
            connection.execute(
                "INSERT INTO attention_block_events(id, block_id, event_ordinal, kind, detail_json, created_at) "
                "VALUES (?, 'blk_old_r9', ?, ?, ?, ?)",
                (f"ev_r10_{ordinal}", ordinal, kind, json.dumps(detail), f"2026-10-05T{at}:00Z"))
        connection.commit()
    repository = Repository(paths.sqlite_path)
    view = material_view(load_vault(paths.root), repository)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert view.presentation(connection, "pp_hist_old_r10") is None, "the presentation froze a held-out revision"
        with repository.connection() as live:
            filtered = load_duration_evidence(repository, latency_cap_minutes=30.0,
                                              attempt_rows=view.attempts(live),
                                              event_visible=view.plan_event_visible(live))
    raw = load_duration_evidence(repository, latency_cap_minutes=30.0)
    assert list(filtered.feedback_dwell) == [4.0]
    assert sorted(raw.feedback_dwell)[:2] == [1.0, 1.0] and len(raw.feedback_dwell) == 12


# -- fix round 10's self-audit: readers that bypassed the view ------------------------------------------


def test_withheld_dose_offers_neither_spend_the_budget_nor_count_as_taken(tmp_path, monkeypatch):
    """Self-audit (dose budget, taken offers, the report's visits): an offer whose extra is withheld
    now is, for AD, an offer never made, so it neither spends the section's budget nor tags a
    reading receipt as taken; a Reader visit to an extraction held out as a whole is not a report
    visit. With nothing held out the same rows count (failed before: the three readers took no
    view and read the raw rows)."""

    from learnloop.adaptive_difficulty import dose as D
    from learnloop.adaptive_difficulty import report as REP
    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.content.sources import exam_material
    from learnloop.db.stores import ad_serving

    from tests.test_ad3_dose_arm import _arm

    paths, vault, repo = _arm(tmp_path)
    with closing(connect(paths.sqlite_path)) as connection:
        draw = ad_serving.insert_dose_row(connection, {
            "row_kind": "draw", "draw_key": "visit_a:ext1:u1", "visit_id": "visit_a", "extraction_id": "ext1",
            "section_id": "u1", "learning_object_ids": ["lo_svd_definition"], "feasible": ["none", "extra_worked_example"],
            "infeasible": {}, "base_version": "b", "floor": 0.1,
            "propensities": {"none": 0.9, "extra_worked_example": 0.1}, "seed": "s", "u": 0.95,
            "chosen_variant": "extra_worked_example", "content": {"extraction_id": "ext1", "span_id": "we2"},
            "forecast_p": None, "detail": {}, "created_at": "2026-10-12T09:00:00Z"})
        ad_serving.insert_dose_row(connection, {"row_kind": "taken", "draw_id": draw,
                                                "created_at": "2026-10-12T09:01:00Z"})
        for event_id, kind, payload, at in (
                ("ev_open_r10", "reader_view_opened", {"visit_id": "visit_w", "extraction_id": "ext_whole"},
                 "2026-10-12T08:00:00Z"),
                ("ev_close_r10", "reader_view_closed", {"visit_id": "visit_w", "active_seconds": 120},
                 "2026-10-12T08:30:00Z")):
            connection.execute(
                "INSERT INTO interaction_events(id, kind, origin, subject_type, subject_id, payload_json, created_at) "
                "VALUES (?, ?, 'learner', 'reader', 'ext_whole', ?, ?)", (event_id, kind, json.dumps(payload), at))
        connection.commit()

    def view_of(material):
        monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)
        return material_view(vault, repo)

    public = view_of(exam_material.Material())
    held = view_of(exam_material.Material(extractions=frozenset({"ext_whole"}), spans=frozenset({("ext1", "we2")})))
    snapshot = SimpleNamespace(events=SimpleNamespace(opportunities=[]))
    budget = {"extraction_id": "ext1", "section_id": "u1", "now": "2026-10-12T10:00:00Z", "daily": 5}
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert D.budget(connection, **budget, view=public) == "section_offered"
        assert D.budget(connection, **budget, view=held) is None
        assert D.taken_offers(connection, view=public) == {"span:ext1/we2": draw}
        assert D.taken_offers(connection, view=held) == {}
        assert [visit["visit_id"] for visit in REP._visits(connection, snapshot, view=public)] == ["visit_w"]
        assert REP._visits(connection, snapshot, view=held) == []


def test_the_commissioned_generation_path_reads_no_incumbent_diagnosis_or_probe_counts(tmp_path, monkeypatch):
    """Self-audit (R2's neighbours): under AD's view the rung selection skips the probe episode's
    hypothesis (the incumbent's diagnosis, which can count withheld answers), a commissioned
    target's request carries no probe counts, and the post-generation gates compare against the
    vault AD sees. The predecessor's reads are unchanged (failed before: ``select_rung`` had no
    switch, the counts were in the request and the gates read the whole vault)."""

    import learnloop.curriculum.depth_rungs as depth_rungs
    from learnloop.content.authoring.practice_generation import PracticeExpansionTarget, _ad_gate_vault
    from learnloop.curriculum.depth_rungs import select_rung

    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    monkeypatch.setattr(depth_rungs, "_rung_from_episode_hypothesis", lambda *_args: "select_method")
    lo = sorted(vault.learning_objects)[0]
    diagnosed = select_rung(vault, repository, learning_object_id=lo, mastery_mean=None)
    blind = select_rung(vault, repository, learning_object_id=lo, mastery_mean=None, episode_hypotheses=False)
    assert diagnosed.waypoint_slug == "select_method" and blind.waypoint_slug != "select_method"

    target = PracticeExpansionTarget(
        learning_object_id=lo, title="t", subjects=["s"], concept="c", existing_practice_items=0,
        requested_new_items=1, probe_attempts_completed=3, probe_attempts_target=4, mastery_mean=0.2,
        recommended_difficulty_band=(0.0, 1.0))
    assert target.as_dict()["probe_attempts_completed"] == 3, "the predecessor's request keeps its counts"
    from dataclasses import replace

    commissioned = replace(target, ad_commission_id="sel_r10").as_dict()
    assert not {"probe_attempts_completed", "probe_attempts_target", "mastery_mean"} & set(commissioned)

    seen = SimpleNamespace(vault_view=lambda: "the view's vault")
    assert _ad_gate_vault(SimpleNamespace(material_view=seen), vault) == "the view's vault"
    assert _ad_gate_vault(SimpleNamespace(material_view=None), vault) is vault
