"""Adaptive difficulty's A8 contract: protected == absent (fix round 9 R7; whole-pipeline since fix
round 11 R2).

The whole-pipeline differential test is the guarantee for spec A8 (the per-reader tests below and
the AST scan in ``test_ad23_material_view.py`` stay as regressions and a lint). One vault is built
and copied twice:

* **A, protected**: the copy gets protected material of every class the verifies named:
  - a held-out current item with sentinel stem, facet and surface family, and one sharing the
    public items' LO, facet and family, with answers (extreme latencies) on both;
  - a public item whose earlier ANSWERED revision is held out (snapshot, presentation, frozen serve
    inputs, attempt), with wrong answers that would carry the incumbent's evidence past the legacy
    rung's threshold (F21), a reveal belonging to that answer (F20) and a tutor question asked
    during it, with the reveal it caused (fix round 11);
  - a public, never-attempted candidate (``pi_p4``) whose only history is an answer to its held-out
    revision and the answer display after it, inside the cold delay (F20, round 11);
  - protected completion -> next-serve pairs in an earlier plan (F28's feedback dwell);
  - a commission result on a held-out item, a band-mode serve selection of it and a commission of
    the protected-only facet's cell (F39, round 11);
  - a reading receipt from a held-out span; a Reader question citing one, and three delivered dose
    offers of it, each followed in its visit by a cue-density lowering (F35);
  - relatedness: an adopted run's loading of a public revision onto the protected-only facet and a
    loading of the held-out item's revision, and a public answer's frozen loadings naming the
    protected-only facet (F38, round 11);
  - a grounding link from the LO to a held-out span (the cross-source context, round 11);
* **B, absent**: that material does not exist at all. It is never written into this copy, so no row
  derived from it exists either (the incumbent's own state included); the rows both copies need in
  append-only tables are written into each, B's without the protected parts.

AD's whole pipeline then runs on each copy, at one shared root path, under identical deterministic
ids and frozen clocks: serves with the slot draw (candidates' estimates), the serve hook's receipts,
an answer, the replay and both rebuilds, the outside forecasters (``llm_v3`` dispatched from the
serves' frozen inputs; the feature audit and ``llm_v1:item`` through item preparation), the
commission draw and commissioned post-probe, goal and cross-source generation (each with its repair
request; the cross-source and a Reader-cited request see a grounding span held out while they are in
flight, F34), the relatedness proposal, readiness and the router card, the dose arm and a late uptake
callback, the reading sweep, the report and the CLI's ``ad report`` and ``ad eval``, in the owner's
default configuration and with ``learned_coupling`` on. Asserted: every captured prompt, every new
row of every table but the incumbent's own (``OUT_OF_SCOPE``, each with its reason), the DERIVED
replay tables and every returned figure are identical; no sentinel appears in any captured request;
no request dispatched after a span was held out quotes it. Normalisations and carve-outs are listed
on the test.

Then the same harness with the held-out predicate unavailable (the incumbent serves, no AD model
request, no AD write, late uptake callbacks write nothing), and a no-protection parity case pinning
F30 (a frozen dose on a facet absent from current content stands).

Fix round 10 added protection that changes over time (the per-reader section): a frozen
outside-forecast history dispatched after an answered revision behind it is held out (F33), a
commissioned repair after protection changed or became unavailable mid-call (F34, with the
structural AST test of the one guarded dispatch), and uptake callbacks with AD off, the dose arm
off or the predicate unavailable (F36).

Fakes only: no network, no model call, no paid call.
"""

from __future__ import annotations

import ast
import json
import os
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
HELD = ("h1", "h2", "h3", "h4", "h5", "h6")
T0 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
RUN = T0 + timedelta(minutes=30)
PUBLIC = ("pi_p1", "pi_p2", "pi_p3")
SENTINELS = ("SENTINEL_STEM_AX9", "SENTINEL_FACET_AX9", "SENTINEL_FAMILY_AX9", "SENTINEL_HIST_AX9",
             "pi_secret", "pi_shared", "SENTINEL_QUESTION_AX9", "SENTINEL_SPAN_AX9", "SENTINEL_P4_AX9")
#: A public, never-attempted candidate whose only history is an answer to a held-out revision and the
#: reveal that followed it (Codex verify F20, fix round 11: exposure and recent-reveal checks).
P4 = "pi_p4"
#: A public item whose bound public answer has frozen relatedness loadings (F38, fix round 11).
LOADED = "pi_hist"
GOAL = "goal_r11"
#: A public grounding span held out while the cross-source request is in flight (F34's time-varying
#: case, in both copies): no request dispatched after that may quote it. ``LATE`` holds it then.
LATE_SPAN = "late_span"
LATE: list[str] = []
SUBJECT = "linear-algebra"
RUN_R11 = "rel_run_r11"
#: The owner's defaults for AD1's outside forecasters and feature audit (both ON, decided 2026-10-18),
#: which ``ad23_vault`` turns off for the other suites; the differential contract runs them (fakes).
OWNER_FORECASTERS = '["llm_v1:item", "llm_v3:llm", "llm_v3:decider"]'
#: AD's tables a run writes (compared as new rows), and its DERIVED tables (compared whole).
AD_WRITES = ("ad_selections", "ad_commission_results", "ad_dose_offers", "ad_reading_opportunities",
             "forecast_receipts", "item_serve_inputs", "ad_relatedness_runs", "attention_block_events",
             "practice_attempts")
AD_DERIVED = ("ad_state", "ad_attempt_trace", "item_forecast_scores")
#: Tables whose new rows the differential does not compare (R2: the incumbent and predecessor are
#: out of scope except where AD reads them). Each is named with its reason, from the first run's
#: differences, never by pattern; no AD module reads any of them (``grep`` over
#: ``adaptive_difficulty/`` and ``daily_plan/ad_slot.py``, fix round 11), and the one incumbent
#: state AD does read, ``mastery_ekf``'s, is the carve-out ``INCUMBENT``/``_carve_outs``.
_INCUMBENT_ANSWER = "the incumbent's own answer pipeline, writing from the incumbent's state (which counts the protected answers by design)"
OUT_OF_SCOPE: dict[str, str] = {
    "attempt_completion_work": _INCUMBENT_ANSWER,
    "attempt_debug_payloads": _INCUMBENT_ANSWER,
    "attempt_surprise": _INCUMBENT_ANSWER,
    "hypothesis_recurrence_state": _INCUMBENT_ANSWER,
    "learning_object_mastery": _INCUMBENT_ANSWER + " (its mastery_ekf reading is the carve-out)",
    "learning_outcome_labels": _INCUMBENT_ANSWER,
    "practice_item_state": "the incumbent's state sync of every current item, the protected ones included",
    "facet_recall_state": "the incumbent's state sync of every current item, the protected ones included",
    "facet_capability_evidence": "the incumbent's state sync of every current item, the protected ones included",
}
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


def _base(tmp_path, *, coupled: bool = True) -> Any:
    """The public vault: three new items in a planned block, a public item with public history, a
    public reading receipt and a commission draw for the LO's cell. Fix round 11 adds: a fourth
    never-attempted candidate (``pi_p4``), a goal over the LO, a public grounding link, a public
    answer bound to a presentation (its frozen loadings are written per copy), the owner's default
    outside forecasters and feature audit, and ``learned_coupling`` as the run's config asks."""

    from learnloop.adaptive_difficulty.generation import rung_features
    from learnloop.db.stores import ad_receipts, ad_serving

    from tests.ad23_fakes import env_for

    # No background work: the hints' approach maps are not built on serve (a thread would mint ids
    # and make model calls at its own pace), and AD's own background jobs are off (``ad23_vault``).
    paths = ad23_vault(tmp_path / "base", items=(*PUBLIC, "pi_hist", P4), ad=COUPLED if coupled else "",
                       config="[router]\nenabled = false\n[hints.maps]\nbuild_on_serve = false\n")
    for item in (*PUBLIC, "pi_hist", P4):
        set_item(paths, item, surface_family="fam_public")
    # A second public facet, so a relatedness loading has somewhere public to land (F38).
    set_item(paths, LOADED, evidence_facets=["recall", "apply_pub"], evidence_weights={"recall": 0.5, "apply_pub": 0.5})
    _owner_defaults(paths)
    _goal(paths)
    _attempt(paths, "pi_hist", at=T0 - timedelta(days=2), latency=90, correct=False)
    env, _clock = env_for(paths, items=PUBLIC)
    from learnloop.daily_plan.engine import build_plan

    build_plan(env, kind="normal", budget=9.0, remembered=9, minutes_source="chip")
    repository = Repository(paths.sqlite_path)
    # A completed (legacy) probe phase, so the cross-source route admits the LO (the same in both).
    repository.upsert_probe_state(learning_object_id=LO, status="complete", algorithm_version="mvp-0.7",
                                  probe_phase_id=f"probe_{LO}", hypothesis_set_id=f"hyp_{LO}",
                                  probe_attempts_completed=3, probe_attempts_target=3,
                                  completed_at=_iso(T0 - timedelta(days=6)), clock=_Frozen(T0 - timedelta(days=6)))
    repository.insert_entity_source_link(entity_type="learning_object", entity_id=LO, locator="public_span",
                                         relation="primary", source_id="src_r9", extraction_id=EXT,
                                         link_id="esl_public_r11", created_at=_iso(T0 - timedelta(days=5)))
    repository.insert_entity_source_link(entity_type="learning_object", entity_id=LO, locator=LATE_SPAN,
                                         relation="support", source_id="src_r9", extraction_id=EXT,
                                         link_id="esl_late_r11", created_at=_iso(T0 - timedelta(days=5)))
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                           "VALUES ('blk_load_r11', 'practice', 10, 'h', ?)", (_iso(T0 - timedelta(days=1, hours=13)),))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_load_r11', 'blk_load_r11', ?, 'chooser', ?)",
                           (LOADED, _iso(T0 - timedelta(days=1, hours=12, minutes=5))))
        connection.commit()
    # Its second public answer, bound to that presentation (the replay reads its frozen loadings).
    _attempt(paths, LOADED, at=T0 - timedelta(days=1, hours=12), latency=90, correct=False,
             presentation_id="pp_load_r11")
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


def _owner_defaults(paths) -> None:
    """The owner's defaults for the outside forecasters and the feature audit (both on)."""

    path = paths.root / "learnloop.toml"
    text = path.read_text(encoding="utf-8")
    assert "outside_forecasters = []" in text and "feature_audit = false" in text
    text = text.replace("outside_forecasters = []", f"outside_forecasters = {OWNER_FORECASTERS}", 1)
    path.write_text(text.replace("feature_audit = false", "feature_audit = true", 1), encoding="utf-8")


def _goal(paths) -> None:
    """A public goal over the LO's concept (goal practice generation, F37)."""

    concept = load_vault(paths.root).learning_objects[LO].concept
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": [{
        "id": GOAL, "title": "The public goal", "creation_source": "learner", "status": "active",
        "target_recall": 0.85, "due_at": None, "facet_scope": {"concepts": [concept], "facets": []},
        "created_at": "2026-10-01T09:00:00Z", "updated_at": "2026-10-01T09:00:00Z"}]})


def _per_copy(paths, *, protected: bool) -> None:
    """Rows both copies have, written in each because their tables are append-only by trigger, with
    the protected copy's protected parts (fix round 11):

    * the frozen serve inputs of ``pp_load_r11`` (``pi_hist``'s public bound answer): a public
      loading, and in the protected copy one onto the protected-only facet too (F38's frozen half);
    * an adopted coupling version and its run: a public loading of ``pi_p1``'s revision, and in the
      protected copy a loading of it onto the protected-only facet and one of ``pi_secret``'s
      revision (F38's saved half)."""

    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.db.stores import ad_serving
    from learnloop.db.stores.judgments import append_judgment

    vault = load_vault(paths.root)
    loaded_hash, loaded_json = item_revision(vault.practice_items[LOADED])
    p1_hash = item_revision(vault.practice_items["pi_p1"])[0]
    frozen = {"apply_pub": 0.4, **({"SENTINEL_FACET_AX9": 0.3} if protected else {})}
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT OR IGNORE INTO practice_item_snapshots(content_hash, practice_item_id, item_json, "
                           "created_at) VALUES (?, ?, ?, ?)", (loaded_hash, LOADED, loaded_json, _iso(T0 - timedelta(days=2))))
        connection.execute(
            "INSERT INTO item_serve_inputs(id, receipt_key, presentation_kind, plan_presentation_id, practice_item_id, "
            "learning_object_id, content_hash, served_at, audit_json, signals_json, pre_exposed, resolution_version, "
            "loadings_json, coupling_version, created_at) VALUES ('isi_load_r11', 'plan_presentation:pp_load_r11', "
            "'plan_presentation', 'pp_load_r11', ?, ?, ?, ?, '{}', '{}', 0, 'r11', ?, ?, ?)",
            (LOADED, LO, loaded_hash, _iso(T0 - timedelta(days=1, hours=12, minutes=5)),
             json.dumps({"loadings": frozen}), f"{SUBJECT}:v1:r11", _iso(T0 - timedelta(days=1, hours=12, minutes=5))))
        made = _iso(T0 - timedelta(days=2, hours=1))
        common = {"task": "ad_relatedness", "judge": "llm", "judge_model": "fake", "prompt_version": "r11",
                  "input_hash": "r11", "created_at": made}
        judgments = [("jdg_pub_r11", "practice_item_revision", p1_hash, "facet", "apply_pub", 0.5)]
        units = {f"rev:{p1_hash}": p1_hash}
        if protected:
            secret_hash = item_revision(vault.practice_items["pi_secret"])[0]
            judgments += [("jdg_facet_r11", "practice_item_revision", p1_hash, "facet", "SENTINEL_FACET_AX9", 0.6),
                          ("jdg_secret_r11", "practice_item_revision", secret_hash, "facet", "recall", 0.7)]
            units[f"rev:{secret_hash}"] = secret_hash
        for judgment_id, left_kind, left_id, right_kind, right_id, score in judgments:
            append_judgment(connection, id=judgment_id, left_kind=left_kind, left_id=left_id, right_kind=right_kind,
                            right_id=right_id, verdict=f"{score:g}", score=score,
                            rationale=json.dumps({"run_key": RUN_R11, "subject": SUBJECT}), **common)
        ad_serving.insert_relatedness_run(connection, {
            "id": RUN_R11, "run_key": RUN_R11, "subject_id": SUBJECT, "input_hash": "r11", "units": units,
            "judgment_ids": [judgment[0] for judgment in judgments], "status": "ok", "prompt_version": "r11",
            "judge_model": "fake", "created_at": made})
        ad_serving.insert_coupling_version(connection, {
            "id": "cv_r11", "subject_id": SUBJECT, "version": 1, "coupling_version": f"{SUBJECT}:v1:r11",
            "run_ids": [RUN_R11], "adopted_by": "owner", "note": None, "adopted_at": _iso(T0 - timedelta(days=2))})
        connection.commit()


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
    _protect_r11(paths, hist_attempt=hist_attempt)
    return {"question": question}


def _protect_r11(paths, *, hist_attempt: str) -> None:
    """Fix round 11's protected material (the classes the round-10 verify named):

    * ``pi_p4`` (public, never attempted in the absent copy): an answer to its held-out earlier
      revision (``h6``) and the answer display that followed it, inside the cold retrieval delay
      and above the auto-prime threshold (F20: pre-exposure and the recent-reveal exclusion);
    * a tutor question asked during ``pi_hist``'s held-out-revision answer, and the reveal it caused
      (a reveal resolved through its question's attempt);
    * a band-mode serve selection that chose ``pi_secret``, and a commission of a cell on the
      protected-only facet (F39: the report's selection cohort);
    * a grounding link from the LO to a held-out span (the cross-source generation context)."""

    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.db.stores import ad_serving
    from learnloop.vault.models import CanonicalExercise

    vault = load_vault(paths.root)
    historical = vault.practice_items[P4].model_copy(update={
        "prompt": "SENTINEL_P4_AX9: the earlier held-out revision of the fourth item.",
        "canonical_exercise": CanonicalExercise(source_id="src_r9", extraction_id=EXT, span_ids=["h6"])})
    content_hash, item_json = item_revision(historical)
    answered_at = T0 - timedelta(minutes=25)
    with closing(connect(paths.sqlite_path)) as connection:
        (block_id,) = connection.execute("SELECT id FROM attention_blocks ORDER BY rowid LIMIT 1").fetchone()
        connection.execute("INSERT INTO practice_item_snapshots(content_hash, practice_item_id, item_json, created_at) "
                           "VALUES (?, ?, ?, ?)", (content_hash, P4, item_json, _iso(answered_at - timedelta(minutes=5))))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_p4_r11', 'blk_old_r9', ?, 'chooser', ?)",
                           (P4, _iso(answered_at - timedelta(minutes=5))))
        connection.execute(
            "INSERT INTO item_serve_inputs(id, receipt_key, presentation_kind, plan_presentation_id, practice_item_id, "
            "learning_object_id, content_hash, served_at, audit_json, signals_json, pre_exposed, resolution_version, "
            "created_at) VALUES ('isi_p4_r11', 'plan_presentation:pp_p4_r11', 'plan_presentation', 'pp_p4_r11', ?, ?, "
            "?, ?, '{}', '{}', 0, 'r11', ?)",
            (P4, LO, content_hash, _iso(answered_at - timedelta(minutes=5)), _iso(answered_at - timedelta(minutes=5))))
        connection.commit()
    p4_attempt = _attempt(paths, P4, at=answered_at, latency=300, correct=False, presentation_id="pp_p4_r11")
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, "
                           "basis, attempt_id, created_at) VALUES ('rv_p4_r11', ?, ?, 'answer_display', 1.0, "
                           "'overlap', ?, ?)", (P4, LO, p4_attempt, _iso(answered_at + timedelta(minutes=2))))
        connection.execute("INSERT INTO question_events(id, context, practice_item_id, attempt_id, question_md, "
                           "created_at) VALUES ('qe_hist_r11', 'practice', 'pi_hist', ?, ?, ?)",
                           (hist_attempt, "SENTINEL_QUESTION_AX9: a tutor question during the held-out answer?",
                            _iso(T0 - timedelta(minutes=48))))
        connection.execute("INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, "
                           "basis, question_event_id, created_at) VALUES ('rv_tutor_r11', 'pi_hist', ?, "
                           "'tutor_answer', 1.0, 'overlap', 'qe_hist_r11', ?)", (LO, _iso(T0 - timedelta(minutes=47))))
        base = {"view": "subject", "learning_object_id": LO, "cell_capability": "retrieval", "support": [],
                "excluded": [], "constants": {}, "seed": "s", "u": 0.5, "propensity": 1.0, "empty_support": False,
                "state_hash": "h", "versions": {}, "algorithm_version": "mvp-0.28"}
        ad_serving.insert_selection(connection, {
            **base, "id": "sel_secret_r11", "decision_key": "serve:r11:secret", "kind": "serve", "cell_facet": "recall",
            "mode": "band", "block_id": block_id, "slot_position": 1, "slot_item_id": "pi_secret",
            "support": [{"ref": "pi_secret", "p_bar": 0.75, "p_band": 0.6, "info": 0.1, "propensity": 1.0}],
            "chosen_item_id": "pi_secret", "chosen_point": None, "created_at": _iso(T0 - timedelta(hours=1))})
        point = {"complexity": 1, "transfer": "same_context", "scaffolding": "cue", "span": "single_step",
                 "response": "short_constructed"}
        ad_serving.insert_selection(connection, {
            **base, "id": "sel_facet_r11", "decision_key": "commission:SENTINEL_FACET_AX9:retrieval:r11",
            "kind": "commission", "cell_facet": "SENTINEL_FACET_AX9", "mode": "band", "chosen_item_id": None,
            "chosen_point": point, "created_at": _iso(T0 - timedelta(hours=2))})
        connection.commit()
    Repository(paths.sqlite_path).insert_entity_source_link(
        entity_type="learning_object", entity_id=LO, locator="h1", relation="primary", source_id="src_r9",
        extraction_id=EXT, link_id="esl_held_r11", created_at=_iso(T0 - timedelta(days=4)))


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
    """The held-out spans, as both predicates read them: AD's (``held_out_material``) and the exam
    predicate the teaching contexts use (``exam_material``, held-out material being exam material).
    Span text comes from a fixed table (the harness has no document IR): a held-out span's text is a
    sentinel."""

    from learnloop.content.authoring import practice_leakage
    from learnloop.content.sources import exam_material

    LATE.clear()

    def material(*_args, **_kwargs):
        return exam_material.Material(spans=frozenset((EXT, span) for span in (*HELD, *LATE)))

    monkeypatch.setattr(exam_material, "held_out_material", material)
    monkeypatch.setattr(exam_material, "exam_material", lambda *_args, **_kwargs: exam_material.ExamMaterial(
        material=material(), held_out=material(), runs={}))

    def text(_repository, extraction_id, span_id):
        if span_id in HELD:
            return f"SENTINEL_SPAN_AX9 held-out text of {span_id}."
        if span_id == LATE_SPAN:
            return "SENTINEL_LATE_AX9: public when the request is built, held out before its repair."
        return f"Public teaching text of {span_id}."

    monkeypatch.setattr(practice_leakage, "_span_text", text)


def _predicate_raises(monkeypatch) -> None:
    from learnloop.content.sources import exam_material

    def broken(*_args, **_kwargs):
        raise RuntimeError("held-out source sets unreadable")

    monkeypatch.setattr(exam_material, "held_out_material", broken)


# -- deterministic runs ----------------------------------------------------------------------------------


def _carve_outs(monkeypatch) -> None:
    """The accepted carve-outs, each excluded at its one field by name (R2):

    * the incumbent's live forecast that AD1 records as its comparator (``mastery_ekf``) is evidence
      the incumbent owns; its rows are left out of the compared writes (``INCUMBENT``), and the copy
      ``llm_v3``'s frozen state quotes of it (``learner.incumbent``, read by
      ``outside._incumbent_inputs``) is pinned to one value in both runs, so the hashes derived from
      the state compare everything else (round 9's recorded boundary, kept by the round-10 verify's
      judgment (c) and the round-11 ruling R2)."""

    from learnloop.adaptive_difficulty import outside

    monkeypatch.setattr(outside, "_incumbent_inputs", lambda _connection, _presentation_id: {
        "p_success": None, "mastery_state": "carve-out: the incumbent's mastery_ekf comparator"})


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
    of a later one, and no two stages mint the same id. The same holds for the uuid4 ids the
    judgment ledger and the model-call records mint (fix round 11)."""

    import uuid

    import learnloop.ai.execution as execution
    import learnloop.db.stores.judgments as judgments
    import learnloop.ids as ids

    monkeypatch.setattr(ids, "_last_timestamp_ms", 1_790_000_000_000 + 1_000 * stage)
    monkeypatch.setattr(ids, "_last_randomness", 0)
    counter = iter(range(10**6))
    minted = lambda: uuid.UUID(int=(stage << 64) + next(counter))  # noqa: E731
    for module in (judgments, execution):
        if hasattr(module, "uuid4"):
            monkeypatch.setattr(module, "uuid4", minted)


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


def _tables(path) -> list[str]:
    with closing(connect(path, read_only=True)) as connection:
        return [str(row[0]) for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]


def _strip(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip(v) for k, v in value.items() if k not in DISCLOSURE}
    if isinstance(value, list):
        return [_strip(v) for v in value]
    return value


class _Generator:
    """The commissioned generation's model client: records the serialized authoring request.
    ``repair``: every answer carries one invalid item, so the one-shot repair request is made too
    (fix round 11: the repair dispatch is part of the pipeline)."""

    provider_name = "codex"
    provider_type = "test"
    model = "fake-generator"

    def __init__(self, *, repair: bool = False, during_first: Any = None) -> None:
        self.prompts: list[str] = []
        self.repair = repair
        self.during_first = during_first
        #: Requests dispatched after ``during_first`` ran (protection changed mid-call).
        self.after_change: list[str] = []

    def run_authoring_proposal(self, context):
        from learnloop.content.proposals.ai_contracts import AuthoringProposal
        from learnloop.content.proposals.proposals import authoring_prompt

        self.prompts.append(authoring_prompt(context))
        if len(self.prompts) > 1 and self.during_first is not None:
            self.after_change.append(self.prompts[-1])
        if len(self.prompts) == 1 and self.during_first is not None:
            self.during_first()
        if not self.repair:
            return AuthoringProposal.model_validate({"summary": "nothing", "source_refs": [], "items": []})
        from tests.test_proposal_persistence import _generated_practice_proposal_payload

        broken = _generated_practice_proposal_payload({"learning_object_id": LO, "evidence_facets": ["recall"],
                                                       "evidence_weights": {"recall": 1.0}})
        broken["items"][0]["audit"] = {"audit_type": "deterministic_validator", "status": "not_applicable_with_trace",
                                       "summary": "Conceptual item; no numeric validation."}
        return AuthoringProposal.model_validate(broken)


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
    before = {table: set(_rows(paths.sqlite_path, table)) for table in _tables(paths.sqlite_path)}

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
    presentations: list[str] = []
    for _ in range(2):
        _record, step = advance(env, serve=True)
        steps.append({k: step.get(k) for k in ("kind", "practice_item_id", "adaptive_difficulty")})
        if step.get("presentation_id"):
            presentations.append(str(step["presentation_id"]))
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

    # Fix round 11 (R2): the outside forecasters dispatched from the serves' frozen inputs, and the
    # item preparation (the feature audit, then ``llm_v1:item``) over every item id, all on fakes.
    from learnloop.adaptive_difficulty.background import prepare_items
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation

    from tests.ad_fakes import AuditDecider, ForecastLLM

    _reset_ids(monkeypatch, 6)
    llm, decider = ForecastLLM(audit={}), AuditDecider()
    out["forecasts"] = [[outcome.status for outcome in forecast_presentation(
        vault, repository, presentation_id, clients=Clients(llm=llm, decider=decider), clock=_Frozen(RUN))]
        for presentation_id in presentations]
    _reset_ids(monkeypatch, 7)
    # The public ids (a caller names the same items in both copies; a withheld id's own handling is
    # AD1's tested ``protected`` outcome).
    out["preparation"] = _strip_ids(prepare_items(vault, repository, [*PUBLIC, "pi_hist", P4],
                                                  clients=Clients(llm=llm, decider=decider),
                                                  decider_factory=lambda: decider, clock=_Frozen(RUN)))
    out["outside_prompts"] = [*llm.prompts, *(call["body"] for call in decider.calls)]
    out["prompts"] += out["outside_prompts"]

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

    # Fix round 11 (R2): goal practice (its focus facets, F37) and cross-source practice (its
    # grounding spans, F34), each answered with an invalid item so the repair request is made too.
    from learnloop.content.authoring.practice_generation import (
        generate_cross_source_practice_proposal,
        generate_goal_practice_proposal,
    )

    # A Reader citation of the late span: a source ref the request (and its repair) quotes.
    cited = [{"ref_type": "canonical_source", "ref_id": "ref_late_r11", "source_id": "src_r9", "extraction_id": EXT,
              "span_ids": [LATE_SPAN], "quote": "SENTINEL_LATE_AX9: public when the request is built.",
              "learning_object_ids": [LO]}]
    for stage, name, call in (
            (8, "goal", lambda client: generate_goal_practice_proposal(paths.root, client, goal_id=GOAL,
                                                                       target_items_per_lo=9, max_new_per_lo=1)),
            (9, "cross_source", lambda client: generate_cross_source_practice_proposal(
                paths.root, client, learning_object_ids=[LO], target_items_per_lo=9, max_new_per_lo=1)),
            (10, "cited", lambda client: generate_post_probe_practice_proposal(
                paths.root, client, learning_object_ids=[LO], require_completed_probe=False, target_items_per_lo=9,
                max_new_per_lo=1, source_refs=cited))):
        _reset_ids(monkeypatch, stage)
        # Cross-source and cited: the late span is held out while the first request is in flight (F34).
        repairing = _Generator(repair=True, during_first=(lambda: LATE.append(LATE_SPAN))
                               if name in ("cross_source", "cited") else None)
        try:
            call(_structured(repairing))
        except Exception as exc:  # noqa: BLE001 - the outcome is compared, whatever it is
            out[f"{name}_error"] = type(exc).__name__ + ": " + str(exc)
        out[f"{name}_generation"] = repairing.prompts
        out["prompts"] += repairing.prompts
        out["after_late_protection"] = out.get("after_late_protection", []) + repairing.after_change
        LATE.clear()

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

    # Every table's new rows (fix round 11, R2: not a hand-kept list, so the next writer is compared
    # too), less the incumbent's own tables (``OUT_OF_SCOPE``, each with its reason).
    out["writes"] = {table: [row for row in sorted(set(_rows(paths.sqlite_path, table)) - before.get(table, set()),
                                                   key=repr) if INCUMBENT not in row]
                     for table in _tables(paths.sqlite_path) if table not in OUT_OF_SCOPE}
    out["derived"] = {table: [row for row in _rows(paths.sqlite_path, table) if INCUMBENT not in row]
                      for table in AD_DERIVED}
    return out


#: A wall-clock stamp with sub-second digits: the model-call records' own clock (``ai.execution``),
#: which the harness's frozen clocks do not drive. The ONE normalisation besides the carve-outs
#: (R2): every other id and stamp is made identical at the source (``_deterministic``, ``_reset_ids``,
#: the frozen clocks, and both copies run at one root path).
WALL_CLOCK = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+\+00:00")


def _normalized(out: dict[str, Any]) -> dict[str, Any]:
    return json.loads(WALL_CLOCK.sub("<wall-clock>", json.dumps(out, default=str)))


def _run_at_common_root(paths, monkeypatch) -> dict[str, Any]:
    """Run a copy at one shared root path (each copy is moved there for its run and back), so no
    path, or hash over a path (an authoring context's ``vault_root``), differs between the copies."""

    common = paths.root.parent / "run"
    paths.root.rename(common)
    try:
        return _run(_paths(common), monkeypatch)
    finally:
        common.rename(paths.root)


def _has_draw(paths, draw_id: str) -> bool:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return connection.execute("SELECT 1 FROM ad_dose_offers WHERE id = ?", (draw_id,)).fetchone() is not None


def _strip_ids(value: Any) -> Any:
    """Plain data for comparison (dataclasses and objects as their public fields)."""

    return json.loads(json.dumps(value, default=lambda obj: getattr(obj, "__dict__", str(obj)), sort_keys=True))


def _sentinel_hits(texts: list[str]) -> list[str]:
    return [f"{token} in a captured request" for token in SENTINELS for text in texts
            if re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", text)]


#: The two configurations the differential contract runs in (R2): the owner's default
#: (``learned_coupling`` off) and with learned coupling on.
CONFIGS = ("default", "coupled")


@pytest.fixture(params=["coupled"])
def copies(request, tmp_path, monkeypatch):
    """One base vault copied twice: protected material is written into one copy only, so it is
    physically absent from the other (never written, so nothing derived from it exists there
    either, the incumbent's own state included)."""

    base = _base(tmp_path, coupled=request.param == "coupled")
    protected, absent = tmp_path / "protected", tmp_path / "absent"
    copy_tree_with_databases(base.root, protected)
    copy_tree_with_databases(base.root, absent)
    protected_paths, absent_paths = _paths(protected), _paths(absent)
    for paths in (protected_paths, absent_paths):
        _visits_with_lowerings(paths)
    seeded = _protect(protected_paths)
    _protected_offers(protected_paths, seeded["question"])
    _per_copy(protected_paths, protected=True)
    _per_copy(absent_paths, protected=False)
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


@pytest.mark.parametrize("copies", CONFIGS, indirect=True)
def test_protected_material_is_indistinguishable_from_absent_material(copies, monkeypatch):
    """A8's contract (R7; whole-pipeline since fix round 11, R2): with every kind of protected
    material present and protected (copy A), AD's whole pipeline produces exactly what it produces
    with that material physically absent (copy B), in the owner's default configuration and with
    learned coupling on; no captured model request quotes protected material, including one
    dispatched after a span was held out mid-call.

    Compared: every prompt the fakes captured, every new row of every table (the incumbent's own
    tables aside, ``OUT_OF_SCOPE``), the DERIVED replay tables whole, and every returned figure
    (report JSON, ``ad report``/``ad eval``, estimates, steps, forecasts, preparation, dose, sweep).
    Normalised: wall-clock stamps with sub-second digits (``WALL_CLOCK``) and the report's
    ``protection`` disclosure and ``generated_at`` (``DISCLOSURE``). Carve-outs (``_carve_outs``,
    ``INCUMBENT``): the incumbent's ``mastery_ekf`` comparator. Nothing else."""

    protected, absent = copies
    _hold_out(monkeypatch)
    _deterministic(monkeypatch)
    _carve_outs(monkeypatch)
    seen = _normalized(_run_at_common_root(protected, monkeypatch))
    want = _normalized(_run_at_common_root(absent, monkeypatch))
    violations = [
        *_diff(seen, want),
        *_sentinel_hits(seen["prompts"]),
        # F34: once the late span is held out, no request may quote it.
        *(f"a request dispatched after the late span was held out quotes it: {text[:80]!r}"
          for text in seen["after_late_protection"] if "SENTINEL_LATE_AX9" in text),
    ]
    for name in ("cross_source", "cited"):
        if not seen.get(f"{name}_error", "").startswith("AuthoringRequestRefused"):
            violations.append(f"{name}: the late-protected repair was not refused: {seen.get(f'{name}_error')!r}")
    if os.environ.get("AD23_CONTRACT_DIFF"):
        # Every violation, for counting (the review's fail-before figures); never set in a gate.
        with open(os.environ["AD23_CONTRACT_DIFF"], "a", encoding="utf-8") as handle:
            handle.write("".join(f"{line}\n" for line in violations))
    # The pipeline ran every stage the comparison claims: nothing is equal by absence.
    assert seen["steps"][0]["kind"] == "item" and seen["estimates"], "the slot draw ran"
    assert any(P4 in [candidate[0] for candidate in request] for request in seen["estimates"])
    assert seen["generation"], "the commissioned request was built"
    assert len(seen["goal_generation"]) == 2, "goal: the first request and its repair"
    assert "Public teaching text of public_span" in seen["cross_source_generation"][0]
    assert "SENTINEL_LATE_AX9" in seen["cross_source_generation"][0], "the late span was public then"
    assert "SENTINEL_LATE_AX9" in seen["cited_generation"][0], "the cited span was public then"
    assert seen["forecasts"] and all(seen["forecasts"]) and seen["preparation"] and seen["outside_prompts"]
    assert violations == [], "\n".join(violations[:40])


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
        assert "**_ad_request_options(plan" in body, generator


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
