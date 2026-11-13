"""What other test files use from ``tests/test_ad23_contract.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import COUPLED, LO, SEEDED, ProposalLLM, ad23_vault, restamp, set_item
from tests.daily_plan_fakes import MovableClock, make_env, scheduled
from tests.helpers import write_yaml


EXT = "ext_r9"
EXT_CLEAN = "ext_r9_clean"
HELD = ("h1", "h2", "h3", "h4", "h5", "h6")
T0 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
RUN = T0 + timedelta(minutes=30)
PUBLIC = ("pi_p1", "pi_p2", "pi_p3")
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
AD_DERIVED = ("ad_state", "ad_attempt_trace", "item_forecast_scores")
#: Tables whose new rows the differential does not compare (R2: the incumbent and predecessor are
#: out of scope), each named with its reason. That AD reads none of them is the guard's, by
#: construction (``protected_tables``: DENIED, but for the ``mastery_ekf`` carve-out; and
#: ``test_ad_guard.py``), no longer a trace of this harness.
_INCUMBENT_ANSWER = "the incumbent's own answer pipeline, writing from the incumbent's state (which counts the protected answers by design)"
OUT_OF_SCOPE: dict[str, str] = {
    "attempt_completion_work": _INCUMBENT_ANSWER,
    "attempt_debug_payloads": _INCUMBENT_ANSWER,
    "attempt_surprise": _INCUMBENT_ANSWER,
    "hypothesis_recurrence_state": _INCUMBENT_ANSWER,
    "learning_object_mastery": _INCUMBENT_ANSWER + " (read by AD only as the mastery_ekf comparator: the carve-out)",
    "learning_outcome_labels": _INCUMBENT_ANSWER,
    "facet_recall_state": "the incumbent's state sync of every current item, the protected ones included",
    "facet_capability_evidence": "the incumbent's state sync of every current item, the protected ones included",
    # Written from mvp-0.59 on (the per-LO diagnostic posterior): each attempt's posterior is the next one's
    # prior, so the answers on protected items carry into it as they do into the recall state. AD cannot read
    # it: the table is in neither of the guard's registries, and an unclassified table is refused.
    "facet_uncertainty": _INCUMBENT_ANSWER,
}
#: Tables AD reads whose raw rows differ by construction (they hold the protected items' own rows):
#: compared as AD reads them, through the material view, instead of raw (fix round 12, F42).
COMPARED_THROUGH_VIEW: dict[str, str] = {
    "practice_item_state": "out['item_states']: MaterialView.item_states, what AD's admission and generation read",
}
#: The report's protection disclosure: what the view withheld (it differs by construction).
DISCLOSURE = ("protection", "generated_at", "protected_readings")
#: (Round 8: ``protected_readings`` counts the reading events Option B leaves out; the deleted copy
#: has none to count.)
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
    # Source-backed public items for the temporal scenarios (fix round 13): pi_p2 cites sec2_span (its
    # revision is replaced in the run, then that former source is held out), pi_p3 cites sec4_span
    # (held out in the run: a protection change in the subject).
    for item, span in (("pi_p2", "sec2_span"), ("pi_p3", "sec4_span")):
        set_item(paths, item, canonical_exercise={"source_id": "src_r9", "extraction_id": EXT, "span_ids": [span]})
    _owner_defaults(paths)
    _goal(paths)
    _attempt(paths, "pi_hist", at=T0 - timedelta(days=2), latency=90, correct=False)
    # P4 is in the plan's queue and universe (the compose fix round 2): AD's candidates are members of
    # the plan's admitted pool, so a candidate whose only history is a withheld answer must be a member
    # in both copies alike. With the pool classified from the raw item states it is a member only with
    # the answer absent (6 violations); classified with AD's view's states, as every incumbent verdict
    # AD receives, it is a member in both.
    env, _clock = env_for(paths, items=(*PUBLIC, P4))
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
    # A saved historical revision of pi_p1 citing the late span (fix round 13, F45's temporal case:
    # holding that span out changes the subject's protection while every current prompt stays the same).
    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.vault.models import CanonicalExercise

    earlier = load_vault(paths.root).practice_items["pi_p1"].model_copy(update={
        "prompt": "An earlier public revision of the first item.",
        "canonical_exercise": CanonicalExercise(source_id="src_r9", extraction_id=EXT, span_ids=[LATE_SPAN])})
    earlier_hash, earlier_json = item_revision(earlier)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO practice_item_snapshots(content_hash, practice_item_id, item_json, created_at) "
                           "VALUES (?, 'pi_p1', ?, ?)", (earlier_hash, earlier_json, _iso(T0 - timedelta(days=9))))
        connection.commit()
    # Its second public answer, bound to that presentation (the replay reads its frozen loadings).
    _attempt(paths, LOADED, at=T0 - timedelta(days=1, hours=12), latency=90, correct=False,
             presentation_id="pp_load_r11")
    with closing(connect(paths.sqlite_path)) as connection:
        ad_receipts.insert_reading_opportunity(connection, {"protection_epoch": SEEDED,
            "opportunity_key": f"worked_example:{EXT}/public_span:{LO}", "kind": "worked_example",
            "subkind": "in_completed_section", "source_table": "reader_section_progress",
            "source_id": f"{EXT}/public_span", "source_written_at": _iso(T0 - timedelta(days=1)),
            "learning_object_id": LO, "facet_doses": {"recall": 1.0}, "dose_offer_id": None,
            "mapping_version": "ad_reading_map_v1", "sweep": "backfill", "sweep_ref": None,
            "swept_at": _iso(T0 - timedelta(days=1))})
        point = {"complexity": 1, "transfer": "same_context", "scaffolding": "cue", "span": "single_step",
                 "response": "short_constructed"}
        ad_serving.insert_selection(connection, {"protection_epoch": SEEDED,
            "id": BASE_COMMISSION, "decision_key": "commission:recall:retrieval:r9", "kind": "commission",
            "view": "subject", "learning_object_id": LO, "cell_facet": "recall", "cell_capability": "retrieval",
            "mode": "band", "support": [], "excluded": [], "constants": {}, "seed": "s", "u": 0.5,
            "chosen_item_id": None, "chosen_point": rung_features(point), "propensity": 1.0,
            "empty_support": False, "state_hash": "h", "versions": {}, "algorithm_version": "mvp-0.30",
            "created_at": _iso(T0 - timedelta(days=3))})
        connection.commit()
    _base_r12(paths)
    return paths


#: Fix round 12's public material (both copies): the extraction's real document IR and source
#: revision (so the production Reader mapping, not a stand-in, maps it), the LO's provenance into it,
#: Reader telemetry the sweep turns into receipts, a public dose offer to deliver, a serve-time
#: commission for the background worker, and a second goal naming only the protected-only facet.
SECTIONS = {"sec1": ["public_anchor", "public_span", LATE_SPAN], "sec2": ["sec2_span"],
            "sec3": ["sec3_span"], "sec4": ["sec4_span"], "sec5": list(HELD)}
GOAL_PROTECTED = "goal_r12"
PUBLIC_DRAW = "dose_pub_r12"
SERVE_COMMISSION = "sel_serve_commission_r12"
EXPIRING_COMMISSION = "sel_expiring_r13"


def _base_r12(paths) -> None:
    from learnloop.adaptive_difficulty.generation import rung_features
    from learnloop.db.stores import ad_serving
    from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth

    from tests.source_inventory_helpers import _persist

    repository = Repository(paths.sqlite_path)
    made = _iso(T0 - timedelta(days=7))
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, created_at, updated_at) "
                           "VALUES ('src_r9', 'pdf', 'file:///r9.pdf', ?, ?)", (made, made))
        connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) "
                           "VALUES ('rev_r9', 'src_r9', 'sha256:r9', ?)", (made,))
        connection.commit()
    blocks, units = [], []
    for ordinal, (section, spans) in enumerate(SECTIONS.items()):
        for span in spans:
            blocks.append(DocumentBlock.build(span_id=span, block_type="Text", text=f"Public teaching text of {span}.",
                                              ordinal=len(blocks), page=1, section_path=[section]))
        units.append(DocumentUnit(unit_id=section, label=section, ordinal=ordinal, semantic_hash=f"sha256:{section}",
                                  page_start=1, page_end=1, span_ids=list(spans)))
    _persist(repository, DocumentIR(extractor="marker", extractor_version="1", units=units, blocks=blocks, assets=[],
                                    health=ExtractionHealth()), revision_id="rev_r9", extraction_id=EXT)
    # A second, CLEAN reading of the book (round 8, Option B): no withheld block touches it, so AD
    # reads it in both copies and the run's reading stages have an effect to compare.
    clean = [DocumentBlock.build(span_id="clean_span", block_type="Text", text="Clean public teaching text.",
                                 ordinal=0, page=1, section_path=["clean_sec"])]
    _persist(repository, DocumentIR(extractor="marker", extractor_version="2", blocks=clean, assets=[],
                                    units=[DocumentUnit(unit_id="clean_sec", label="clean_sec", ordinal=0,
                                                        semantic_hash="sha256:clean_sec", page_start=1, page_end=1,
                                                        span_ids=["clean_span"])],
                                    health=ExtractionHealth()), revision_id="rev_r9", extraction_id=EXT_CLEAN)
    lo_path = paths.learning_object_path("linear-algebra", LO)
    payload = yaml.safe_load(lo_path.read_text(encoding="utf-8"))
    payload["provenance"] = {"origin": "human", "source_refs": [{
        "ref_type": "canonical_source", "ref_id": "src_r9", "source_id": "src_r9", "extraction_id": EXT,
        "span_ids": ["public_span"], "locator": f"span:{EXT}/public_span"}, {
        "ref_type": "canonical_source", "ref_id": "src_r9", "source_id": "src_r9", "extraction_id": EXT_CLEAN,
        "span_ids": ["clean_span"], "locator": f"span:{EXT_CLEAN}/clean_span"}]}
    write_yaml(lo_path, payload)
    goals = yaml.safe_load(paths.goals_path.read_text(encoding="utf-8"))
    goals["goals"].append({
        "id": GOAL_PROTECTED, "title": "A goal over one facet", "creation_source": "learner", "status": "active",
        "target_recall": 0.85, "due_at": None, "facet_scope": {"concepts": [], "facets": ["SENTINEL_FACET_AX9"]},
        "created_at": "2026-10-01T09:00:00Z", "updated_at": "2026-10-01T09:00:00Z"})
    write_yaml(paths.goals_path, goals)
    repository.insert_source_exposure_event(
        {"context": "reader", "extraction_id": EXT, "span_id": "public_span", "revision_id": "rev_r9",
         "source_id": "src_r9", "entity_type": "reader", "entity_id": "visit_pub",
         "created_at": _iso(T0 - timedelta(hours=5))})
    repository.upsert_reader_section_progress(extraction_id=EXT, section_id="sec2", spans_seen=1, span_count=1,
                                              completed=True, clock=_Frozen(T0 - timedelta(hours=4)))
    repository.insert_source_exposure_event(
        {"context": "reader", "extraction_id": EXT_CLEAN, "span_id": "clean_span", "revision_id": "rev_r9",
         "source_id": "src_r9", "entity_type": "reader", "entity_id": "visit_clean",
         "created_at": _iso(T0 - timedelta(hours=5, minutes=30))})
    point = {"complexity": 1, "transfer": "same_context", "scaffolding": "cue", "span": "single_step",
             "response": "short_constructed"}
    with closing(connect(paths.sqlite_path)) as connection:
        ad_serving.insert_dose_row(connection, {"protection_epoch": SEEDED,
            "id": PUBLIC_DRAW, "row_kind": "draw", "draw_key": f"visit_pub:{EXT}:sec2", "visit_id": "visit_pub",
            "extraction_id": EXT, "section_id": "sec2", "learning_object_ids": [LO],
            "feasible": ["none", "extra_worked_example"], "infeasible": {}, "base_version": "b", "floor": 0.1,
            "propensities": {"none": 0.9, "extra_worked_example": 0.1}, "seed": "s", "u": 0.95,
            "chosen_variant": "extra_worked_example", "content": {"extraction_id": EXT, "span_id": "sec3_span"},
            "forecast_p": None, "detail": {}, "created_at": _iso(T0 - timedelta(hours=4))})
        ad_serving.insert_selection(connection, {"protection_epoch": SEEDED,
            "id": SERVE_COMMISSION, "decision_key": f"commission:serve:{LO}:r12", "kind": "commission",
            "view": "subject", "learning_object_id": LO, "cell_facet": "recall", "cell_capability": "retrieval",
            "mode": "band", "support": [], "excluded": [], "constants": {}, "seed": "s", "u": 0.5,
            "chosen_item_id": None, "chosen_point": rung_features(point), "propensity": 1.0, "empty_support": False,
            "state_hash": "h", "versions": {}, "algorithm_version": "mvp-0.30",
            "created_at": _iso(T0 - timedelta(hours=6))})
        # Fix round 13's expiry boundary: a public commission drawn outside any job expires seven days
        # after its draw, here two and a half hours into the run (inside the advancing clock's span).
        ad_serving.insert_selection(connection, {"protection_epoch": SEEDED,
            "id": EXPIRING_COMMISSION, "decision_key": "commission:apply_pub:retrieval:r13", "kind": "commission",
            "view": "subject", "learning_object_id": LO, "cell_facet": "apply_pub", "cell_capability": "retrieval",
            "mode": "band", "support": [], "excluded": [], "constants": {}, "seed": "s", "u": 0.5,
            "chosen_item_id": None, "chosen_point": rung_features(point), "propensity": 1.0, "empty_support": False,
            "state_hash": "h", "versions": {}, "algorithm_version": "mvp-0.30",
            "created_at": _iso(RUN - timedelta(days=7) + timedelta(hours=2, minutes=30))})
        connection.commit()


def _owner_defaults(paths) -> None:
    """The owner's defaults for the outside forecasters and the feature audit (both on), and a
    daily dose budget of two extras (the default is three) so one draw decides it (F47, round 14)."""

    path = paths.root / "learnloop.toml"
    text = path.read_text(encoding="utf-8")
    assert "outside_forecasters = []" in text and "feature_audit = false" in text
    text = text.replace("outside_forecasters = []", f"outside_forecasters = {OWNER_FORECASTERS}\ndose_daily_offers = 2", 1)
    path.write_text(text.replace("feature_audit = false", "feature_audit = true", 1), encoding="utf-8")


def _goal(paths) -> None:
    """A public goal over the LO's concept (goal practice generation, F37)."""

    concept = load_vault(paths.root).learning_objects[LO].concept
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": [{
        "id": GOAL, "title": "The public goal", "creation_source": "learner", "status": "active",
        "target_recall": 0.85, "due_at": None, "facet_scope": {"concepts": [concept], "facets": []},
        "created_at": "2026-10-01T09:00:00Z", "updated_at": "2026-10-01T09:00:00Z"}]})


def _epoch(paths, *, held: bool = True) -> str:
    """The copy's protection epoch now, with the harness's held-out spans (the AD23 redesign, E2), or
    (``held`` False) before any was held out."""

    from learnloop.adaptive_difficulty.material_view import detached_view
    from learnloop.adaptive_difficulty.operation import epoch_of
    from learnloop.content.sources import exam_material

    with pytest.MonkeyPatch.context() as patch:
        _hold_out(patch)
        if not held:
            patch.setattr(exam_material, "held_out_material", lambda *_a, **_k: exam_material.Material())
        return str(epoch_of(detached_view(load_vault(paths.root), Repository(paths.sqlite_path))))


def _per_copy(paths, *, protected: bool) -> str:
    """Rows both copies have, written in each because their tables are append-only by trigger, with
    the protected copy's protected parts (fix rounds 11-12). Returns the copy's protection epoch.

    * the frozen serve inputs of ``pp_load_r11`` (``pi_hist``'s public bound answer): a public
      loading, and in the protected copy one onto the protected-only facet too (F38's frozen half);
    * an adopted coupling version and its run, proposed at the copy's current protection epoch: a
      public loading of ``pi_p1``'s revision, and in the protected copy a loading of
      it onto the protected-only facet and one of ``pi_secret``'s revision (round 11's per-loading
      revalidation);
    * in the protected copy only, a later run proposed BEFORE the material was protected (it records
      the epoch from before any material was held out): an LO-to-LO coupling and a public-to-public loading (out
      of force at the current epoch: E2);
    * in the protected copy only, the held-out source's canonical note (F40)."""

    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.db.stores import ad_serving
    from learnloop.db.stores.judgments import append_judgment

    if protected:
        # The held-out source's canonical note first (F40): it is part of what the copy withholds, so
        # of the epoch the rows below record.
        with closing(connect(paths.sqlite_path)) as connection:
            connection.execute("UPDATE source_revisions SET note_id = 'note_r12' WHERE id = 'rev_r9'")
            connection.commit()
        from learnloop.vault.yaml_io import write_markdown_with_frontmatter

        write_markdown_with_frontmatter(paths.note_path("linear-algebra", "note_r12"), {
            "schema_version": 1, "id": "note_r12", "subjects": ["linear-algebra"], "related_los": [LO],
            "related_concepts": [], "source_type": "canonical_source",
            "canonical_source": {"kind": "pdf", "canonical_uri": "file:///r9.pdf", "title": "The exam source"},
            "created_at": "2026-10-01T09:00:00Z", "updated_at": "2026-10-01T09:00:00Z"},
            "SENTINEL_NOTE_AX9: the held-out exam source's own text.")
    epoch = _epoch(paths)
    vault = load_vault(paths.root)
    loaded_hash, loaded_json = item_revision(vault.practice_items[LOADED])
    p1_hash = item_revision(vault.practice_items["pi_p1"])[0]
    # AD's frozen loadings at the copy's own epoch (round 2: a frozen row is read only at the epoch it was
    # frozen under, so it can name no facet only withheld material names).
    frozen = {"apply_pub": 0.4}
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT OR IGNORE INTO practice_item_snapshots(content_hash, practice_item_id, item_json, "
                           "created_at) VALUES (?, ?, ?, ?)", (loaded_hash, LOADED, loaded_json, _iso(T0 - timedelta(days=2))))
        connection.execute(
            "INSERT INTO item_serve_inputs(id, receipt_key, presentation_kind, plan_presentation_id, practice_item_id, "
            "learning_object_id, content_hash, served_at, audit_json, signals_json, pre_exposed, resolution_version, "
            "loadings_json, coupling_version, created_at, protection_epoch) VALUES ('isi_load_r11', "
            "'plan_presentation:pp_load_r11', 'plan_presentation', 'pp_load_r11', ?, ?, ?, ?, '{}', '{}', 0, 'r11', ?, "
            f"?, ?, '{SEEDED}')",
            (LOADED, LO, loaded_hash, _iso(T0 - timedelta(days=1, hours=12, minutes=5)),
             json.dumps({"loadings": frozen}), f"{SUBJECT}:v1:r11", _iso(T0 - timedelta(days=1, hours=12, minutes=5))))
        made = _iso(T0 - timedelta(days=2, hours=1))
        common = {"task": "ad_relatedness", "judge": "llm", "judge_model": "fake", "prompt_version": "r11",
                  "input_hash": "r11", "created_at": made}
        judgments = [("jdg_pub_r11", "practice_item_revision", p1_hash, "facet", "apply_pub", 0.5)]
        units = {f"rev:{p1_hash}": p1_hash, "protection:epoch": epoch}
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
        if protected:
            later = _iso(T0 - timedelta(days=1))
            stale = [("jdg_couple_r12", "learning_object", LO, "learning_object", "lo_svd_definition", 0.5),
                     ("jdg_stale_r12", "practice_item_revision", p1_hash, "facet", "apply_pub", 0.9)]
            for judgment_id, left_kind, left_id, right_kind, right_id, score in stale:
                append_judgment(connection, id=judgment_id, left_kind=left_kind, left_id=left_id,
                                right_kind=right_kind, right_id=right_id, verdict=f"{score:g}", score=score,
                                rationale=json.dumps({"run_key": "rel_run_r12", "subject": SUBJECT}),
                                **{**common, "input_hash": "r12", "created_at": later})
            ad_serving.insert_relatedness_run(connection, {
                "id": "rel_run_r12", "run_key": "rel_run_r12", "subject_id": SUBJECT, "input_hash": "r12",
                "units": {f"lo:{LO}": "h", f"rev:{p1_hash}": p1_hash, "protection:epoch": _epoch(paths, held=False)},
                "judgment_ids": [judgment[0] for judgment in stale], "status": "ok", "prompt_version": "r11",
                "judge_model": "fake", "created_at": later})
        connection.commit()
    return epoch


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
            "created_at, protection_epoch) VALUES ('isi_hist_r9', 'plan_presentation:pp_hist_r9', 'plan_presentation', "
            f"'pp_hist_r9', 'pi_hist', ?, ?, ?, '{{}}', '{{}}', 0, 'r9', ?, '{SEEDED}')",
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
            "'x', 'x', 'complete', 'mvp-0.30', 'h', '2026-10-05T09:00:00Z', '2026-10-05T09:00:00Z')")
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
        ad_serving.insert_commission_result(connection, {"protection_epoch": SEEDED,
            "selection_id": BASE_COMMISSION, "practice_item_id": "pi_secret",
            "content_hash": item_revision(secret)[0], "features": {"complexity": 1}, "p_bar": 0.99,
            "status": "realized_out_of_band", "state_hash": "h", "features_match": 1, "landed_after_expiry": 0,
            "created_at": _iso(T0 - timedelta(minutes=35))})
        ad_receipts.insert_reading_opportunity(connection, {"protection_epoch": SEEDED,
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
            "created_at, protection_epoch) VALUES ('isi_p4_r11', 'plan_presentation:pp_p4_r11', 'plan_presentation', "
            f"'pp_p4_r11', ?, ?, ?, ?, '{{}}', '{{}}', 0, 'r11', ?, '{SEEDED}')",
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
                "state_hash": "h", "versions": {}, "algorithm_version": "mvp-0.30"}
        ad_serving.insert_selection(connection, {"protection_epoch": SEEDED,
            **base, "id": "sel_secret_r11", "decision_key": "serve:r11:secret", "kind": "serve", "cell_facet": "recall",
            "mode": "band", "block_id": block_id, "slot_position": 1, "slot_item_id": "pi_secret",
            "support": [{"ref": "pi_secret", "p_bar": 0.75, "p_band": 0.6, "info": 0.1, "propensity": 1.0}],
            "chosen_item_id": "pi_secret", "chosen_point": None, "created_at": _iso(T0 - timedelta(hours=1))})
        # F39 (fix round 12): an empty-support draw of a slot planned with the held-out item.
        ad_serving.insert_selection(connection, {"protection_epoch": SEEDED,
            **base, "id": "sel_empty_r12", "decision_key": "serve:r12:empty", "kind": "serve", "cell_facet": None,
            "cell_capability": None, "mode": "empty_support", "block_id": block_id, "slot_position": 2,
            "slot_item_id": "pi_secret", "chosen_item_id": None, "chosen_point": None, "u": None, "propensity": None,
            "empty_support": True, "created_at": _iso(T0 - timedelta(minutes=55))})
        point = {"complexity": 1, "transfer": "same_context", "scaffolding": "cue", "span": "single_step",
                 "response": "short_constructed"}
        ad_serving.insert_selection(connection, {"protection_epoch": SEEDED,
            **base, "id": "sel_facet_r11", "decision_key": "commission:SENTINEL_FACET_AX9:retrieval:r11",
            "kind": "commission", "cell_facet": "SENTINEL_FACET_AX9", "mode": "band", "chosen_item_id": None,
            "chosen_point": point, "created_at": _iso(T0 - timedelta(hours=2))})
        connection.commit()
    Repository(paths.sqlite_path).insert_entity_source_link(
        entity_type="learning_object", entity_id=LO, locator="h1", relation="primary", source_id="src_r9",
        extraction_id=EXT, link_id="esl_held_r11", created_at=_iso(T0 - timedelta(days=4)))
    _protect_r13(paths)
    _protect_r14(paths)


def _protect_r14(paths) -> None:
    """Fix round 14's protected material (protected copy only):

    * a Reader tutor exchange whose anchor is public but whose recorded context (a source span and a
      citation) quotes a held-out span (F46: the complete recorded context decides);
    * a dose draw made today at a held-out section (its origin) whose extra, a worked example in a
      public section, was delivered (F47: a protected origin removes the draw from the budget)."""

    from learnloop.db.stores import ad_serving

    at = _iso(T0 - timedelta(hours=2))
    context = {"extraction_id": EXT, "span_id": "public_anchor",
               "source_spans": [{"extraction_id": EXT, "span_id": "public_anchor", "label": "anchor"},
                                {"extraction_id": EXT, "span_id": "h5", "label": "secondary"}],
               "citations": [{"extraction_id": EXT, "span_id": "h5"}]}
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO question_events(id, context, note_id, question_md, answer_md, answer_status, answer_mode, "
            "source_context_json, created_at, answered_at) VALUES ('qe_context_r14', 'reader', ?, "
            "'Why does this hold?', 'Because.', 'answered', 'help_me_reason', ?, ?, ?)",
            (f"span:{EXT}/public_anchor", json.dumps(context), at, at))
        draw = ad_serving.insert_dose_row(connection, {"protection_epoch": SEEDED,
            "id": "dose_origin_r14", "row_kind": "draw", "draw_key": f"visit_origin:{EXT}:sec5", "visit_id": "visit_origin",
            "extraction_id": EXT, "section_id": "sec5", "learning_object_ids": [LO],
            "feasible": ["none", "extra_worked_example"], "infeasible": {}, "base_version": "b", "floor": 0.1,
            "propensities": {"none": 0.9, "extra_worked_example": 0.1}, "seed": "s", "u": 0.95,
            "chosen_variant": "extra_worked_example", "content": {"extraction_id": EXT, "span_id": "sec3_span"},
            "forecast_p": None, "detail": {}, "created_at": at})
        ad_serving.insert_dose_row(connection, {"protection_epoch": SEEDED, "row_kind": "delivered", "draw_id": draw, "created_at": at})
        connection.commit()


def _protect_r13(paths) -> None:
    """Fix round 13's protected material (protected copy only):

    * an answered Reader tutor question on the held-out source's canonical note (F43);
    * a passage-view receipt from a held-out span that occupies the LO's one daily passage slot on the
      day a public passage view is waiting for the sweep (F44), with its exposure event;
    * a reading receipt from held-out material stamped exactly as the public one (an ordering tie)."""

    from learnloop.db.stores import ad_receipts

    day = _iso(T0 - timedelta(hours=6))
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO question_events(id, context, note_id, question_md, answer_md, answer_status, answer_mode, "
            "created_at, answered_at) VALUES ('qe_note_r13', 'reader', 'note_r12', ?, 'An answer.', 'answered', "
            "'help_me_reason', ?, ?)", ("SENTINEL_QUESTION_AX9: about the exam source?", day, day))
        connection.execute(
            "INSERT INTO source_exposure_events(id, context, extraction_id, span_id, revision_id, source_id, "
            "entity_type, entity_id, created_at) VALUES ('sxe_held_r13', 'reader', ?, 'h1', 'rev_r9', 'src_r9', "
            "'reader', 'visit_held', ?)", (EXT, day))
        for key, source_table, source_id, kind, subkind, written in (
                (f"reading:passage_viewed:{LO}:{day[:10]}:1", "source_exposure_events", "sxe_held_r13", "reading",
                 "passage_viewed", day),
                (f"worked_example:{EXT}/h2:{LO}", "reader_section_progress", f"{EXT}/h2", "worked_example",
                 "in_completed_section", _iso(T0 - timedelta(days=1)))):
            ad_receipts.insert_reading_opportunity(connection, {"protection_epoch": SEEDED,
                "opportunity_key": key, "kind": kind, "subkind": subkind, "source_table": source_table,
                "source_id": source_id, "source_written_at": written, "learning_object_id": LO,
                "facet_doses": {"recall": 1.0}, "dose_offer_id": None, "mapping_version": "ad_reading_map_v1",
                "sweep": "backfill", "sweep_ref": None, "swept_at": written})
        connection.commit()


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
            draw = ad_serving.insert_dose_row(connection, {"protection_epoch": SEEDED,
                "id": f"{DOSE_DRAW_ID}_{k}", "row_kind": "draw", "draw_key": f"visit_r9_{k}:{EXT}:sec{k + 2}",
                "visit_id": f"visit_r9_{k}", "extraction_id": EXT, "section_id": f"sec{k + 2}",
                "learning_object_ids": [LO], "feasible": ["none", "extra_question"], "infeasible": {}, "base_version": "b",
                "floor": 0.1, "propensities": {"none": 0.9, "extra_question": 0.1}, "seed": "s", "u": 0.95,
                "chosen_variant": "extra_question", "content": {"question_id": question_id, "style": "recall"},
                "forecast_p": None, "detail": {}, "created_at": at})
            ad_serving.insert_dose_row(connection, {"protection_epoch": SEEDED, "row_kind": "delivered", "draw_id": draw, "created_at": at})
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


def _carve_outs(monkeypatch) -> None:
    """The accepted carve-outs, each excluded at its one field by name (R2):

    * the incumbent's live forecast that AD1 records as its comparator (``mastery_ekf``) is evidence
      the incumbent owns; its rows are left out of the compared writes (``INCUMBENT``), and the copy
      ``llm_v3``'s frozen state quotes of it (``learner.incumbent``, read by
      ``outside._incumbent_inputs``) is pinned to one value in both runs, so the hashes derived from
      the state compare everything else (round 9's recorded boundary, kept by the round-10 verify's
      judgment (c) and the round-11 ruling R2)."""

    from learnloop.adaptive_difficulty import outside

    monkeypatch.setattr(outside, "_incumbent_inputs", lambda _connection, _presentation_id, _view=None: {
        "p_success": None, "mastery_state": "carve-out: the incumbent's mastery_ekf comparator"})


#: The harness's ONE operation clock (fix rounds 13-14, F42), frozen at ``RUN`` identically in both
#: copies. Every operation the harness calls reads it: the system clock, the model-call records' clock,
#: and each explicit ``clock=``, ``now=``, ``as_of=`` and ``served_at=`` (``_OP``).
def _now() -> datetime:
    return RUN


class _OperationClock:
    def now(self) -> datetime:
        return _now()


_OP = _OperationClock()


def _deterministic(monkeypatch) -> None:
    """Identical ids and wall-clock reads on both copies: the ULID generator counts from a fixed
    instant, and the system clock reads ``RUN``."""

    import learnloop.clock as clock_module
    import learnloop.ids as ids

    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: 1_790_000_000_000)
    monkeypatch.setattr(ids, "secrets", SimpleNamespace(randbits=lambda bits: 0))
    _reset_ids(monkeypatch)
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: _now())
    # The model-call records' own wall clock (``datetime.now`` in ``ai.execution`` and the model-call
    # store), frozen at the source as the system clock is (fix round 12: no stamp is normalised).
    import learnloop.ai.execution as execution
    import learnloop.db.stores.model_calls as model_calls

    class _Now(datetime):
        @classmethod
        def now(cls, tz=None):
            moment = _now()
            return moment if tz is None else moment.astimezone(tz)

    for module in (execution, model_calls):
        monkeypatch.setattr(module, "datetime", _Now)


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
    # Decision records and traces draw from a stream of their own (arc B fix 3), reset the same way.
    from learnloop import provenance

    records = ids.UlidStream()
    records._last_ms, records._last_randomness = 1_790_000_000_500 + 1_000 * stage, 0
    records._random = SimpleNamespace(getrandbits=lambda bits: 0)
    monkeypatch.setattr(provenance, "_RECORD_IDS", records)
    counter = iter(range(10**6))
    minted = lambda: uuid.UUID(int=(stage << 64) + next(counter))  # noqa: E731
    for module in (judgments, execution):
        if hasattr(module, "uuid4"):
            monkeypatch.setattr(module, "uuid4", minted)


def _rows(path, table: str) -> list[tuple]:
    with closing(connect(path, read_only=True)) as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (table,)).fetchone() is None:
            return []
        cursor = connection.execute(f"SELECT * FROM {table}")
        return sorted((tuple(row) for row in cursor.fetchall()), key=repr)


def _disclosed(paths, table: str, row: tuple) -> tuple:
    """The protection epoch (E2: a digest of the protected material, so it differs by construction)
    is compared by what it means, whether it is the copy's current epoch, never by value: in a
    relatedness run's units and key, a relatedness claim's or model call's key, and a frozen
    outside-forecast state. Those fields, by name, are the only ones rewritten. A decision record's
    ``created_at`` is the wall clock, not the frozen run clock (ADR-017), so the two copies' records are
    compared by everything else. A grade record's ``facts.fsrs`` (refactor B8) is the incumbent's own FSRS
    review, copied from what ``attempt_surprise`` and ``practice_item_state`` hold (both the incumbent's, outside
    this comparison), so it is set aside by name, as those tables are."""

    columns = [name for name, *_ in _columns(paths.sqlite_path, table)]
    values = dict(zip(columns, row, strict=True))
    if table == "decision_records":
        values["created_at"] = "<wall clock>"
        if values.get("kind") == "grade" and values.get("facts_json"):
            facts = json.loads(values["facts_json"])
            if "fsrs" in facts:
                facts["fsrs"] = "<the incumbent's FSRS review>"
                values["facts_json"] = json.dumps(facts, sort_keys=True)
    epoch = _epoch(paths)
    for name, value in list(values.items()):
        if isinstance(value, str) and epoch in value and table not in ("ad_relatedness_runs", "item_forecast_payloads"):
            values[name] = value.replace(epoch, "<current epoch>")
    if table == "item_forecast_payloads" and values.get("content_json"):
        content = json.loads(values["content_json"])
        if isinstance(content, dict) and "protection_epoch" in content:
            content["protection_epoch"] = f"current={content['protection_epoch'] == epoch}"
            values["content_json"] = json.dumps(content, sort_keys=True)
            # The payload's content hash covers the epoch, so it is named, as the epoch is.
            values["content_hash"] = "<the hash of the epoch-stamped content>"
    if table == "ad_relatedness_runs":
        units = json.loads(values["units_json"])
        if "protection:epoch" in units:
            units["protection:epoch"] = f"current={units['protection:epoch'] == epoch}"
        values["units_json"] = json.dumps(units, sort_keys=True)
        values["run_key"] = str(values["run_key"]).replace(epoch, "<current epoch>")
    return tuple(values[name] for name in columns)


def _columns(path, table: str) -> list[tuple]:
    with closing(connect(path, read_only=True)) as connection:
        return [(row[1],) for row in connection.execute(f"PRAGMA table_info({table})")]


def _open_commissions(paths) -> list[str]:
    """The commissions open now, as AD's view sees them (the expiry boundary, fix round 13)."""

    from learnloop.adaptive_difficulty.material_view import detached_view as material_view
    from learnloop.clock import utc_now_iso

    view = material_view(load_vault(paths.root), Repository(paths.sqlite_path))
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return sorted(str(row["id"]) for row in view.open_commissions(connection, now=utc_now_iso()))


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
        from tests.proposal_persistence_helpers import _generated_practice_proposal_payload

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
    from learnloop.adaptive_difficulty.material_view import detached_view as material_view
    from learnloop.adaptive_difficulty.outside import history_card, item_view
    from learnloop.adaptive_difficulty.reading import sweep
    from learnloop.cli.app import app
    from learnloop.content.authoring.practice_generation import generate_post_probe_practice_proposal
    from learnloop.daily_plan import ad_slot
    from learnloop.daily_plan.engine import advance

    _reset_ids(monkeypatch)
    RP.clear_cache()
    out: dict[str, Any] = {"prompts": [], "open_commissions": [_open_commissions(paths)]}
    before = {table: set(_rows(paths.sqlite_path, table)) for table in _tables(paths.sqlite_path)}

    # Serves: the slot draw (with its candidates' estimates), the serve hook, an answer, a second serve.
    requests: list[Any] = []
    real_build = ad_slot._request

    def spy(*args, **kwargs):
        request = real_build(*args, **kwargs)
        requests.append([(c.practice_item_id, list(c.failed), c.est_minutes) for c in request.candidates])
        return request

    monkeypatch.setattr(ad_slot, "_request", spy)
    vault = load_vault(paths.root)
    clock = MovableClock(_now())
    env = make_env(paths.root, [scheduled(item, LO, forgetting_risk=0.6) for item in (*PUBLIC, P4)], clock=clock,
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
    monkeypatch.setattr(ad_slot, "_request", real_build)
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
        card = history_card(vault, connection, vault.practice_items["pi_p3"], served_at=_iso(_now()), view=view,
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
        vault, repository, presentation_id, clients=Clients(llm=llm, decider=decider), clock=_OP)]
        for presentation_id in presentations]
    _reset_ids(monkeypatch, 7)
    # The public ids (a caller names the same items in both copies; a withheld id's own handling is
    # AD1's tested ``protected`` outcome).
    # pi_p3 is left out: never audited, it is never snapshotted (F38's temporal case needs a revision
    # that only the relatedness run's recorded context remembers, as with the feature audit off).
    out["preparation"] = _strip_ids(prepare_items(vault, repository, ["pi_p1", "pi_p2", "pi_hist", P4],
                                                  clients=Clients(llm=llm, decider=decider),
                                                  decider_factory=lambda: decider, clock=_OP))
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
                max_new_per_lo=1, source_refs=cited)),
            # F37 (fix round 12): a goal whose only facet only a protected item measures has no scope.
            (11, "goal_protected", lambda client: generate_goal_practice_proposal(
                paths.root, client, goal_id=GOAL_PROTECTED, target_items_per_lo=9, max_new_per_lo=1))):
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

    # The background commission queue and its worker (fix round 12, F42): the serve-time commission
    # queued on the vault's durable job queue and generated by the ingest worker, in the foreground.
    import learnloop.content.pipeline.jobs as J
    from learnloop.adaptive_difficulty.generation import schedule_commission_generation
    from learnloop.content.pipeline.runner import RunnerServices

    _reset_ids(monkeypatch, 12)
    worker = _Generator()
    jobs = J.DurableIngestJobs()
    jobs.bind(Repository(paths.sqlite_path), paths.root, background=False,
              services=RunnerServices(synthesis_client_factory=lambda _ctx: _structured(worker)))

    def enqueue(commission_id: str, learning_object_id: str) -> str:
        return jobs.enqueue_practice_expansion(learning_object_ids=[learning_object_id], ad_commission_id=commission_id)

    out["queued"] = schedule_commission_generation(load_vault(paths.root), Repository(paths.sqlite_path), enqueue)
    out["worker"] = [(job["status"], (job.get("result") or {}).get("ad_commission_id"))
                     for commission in out["queued"]
                     for job in Repository(paths.sqlite_path).ingest_jobs_for_batch(J.ad_commission_batch_id(commission))]
    out["worker_generation"] = worker.prompts
    out["prompts"] += worker.prompts

    # The relatedness proposal (its request is captured, never sent).
    _reset_ids(monkeypatch, 3)
    llm = ProposalLLM({"items": [], "learning_objects": []})
    vault = load_vault(paths.root)
    out["relatedness_inputs"] = json.dumps(R.subject_inputs(vault, repository, "linear-algebra")["payload"],
                                           sort_keys=True)
    proposed = R.propose_subject(vault, repository, "linear-algebra", client=llm)
    out["relatedness"], out["relatedness_hash"] = proposed.status, proposed.input_hash
    out["prompts"] += [out["relatedness_inputs"], *llm.prompts]

    # Readiness and the router card.
    RP.clear_cache()
    out["readiness"] = RD.lo_readiness(vault, repository, LO)
    out["card"] = RD.card_fields(vault, repository, LO)

    # The dose arm: a fresh boundary, and the boundary of the earlier draw that offered the question.
    _reset_ids(monkeypatch, 4)
    dose_view = material_view(vault, repository)
    # The production Reader mapping (fix round 12, F42): no stand-in.
    fresh = D.decide(vault, repository, D.Boundary(visit_id="visit_new", extraction_id=EXT_CLEAN,
                                                   section_id="clean_sec"), clock=_OP, view=dose_view)
    old = D.decide(vault, repository, D.Boundary(visit_id="visit_old", extraction_id=EXT_CLEAN,
                                                 section_id="clean_sec"), clock=_OP, view=dose_view)
    # The mixed reading's boundary: ineligible before any draw in both copies (Option B, round 8).
    out["dose_mixed"] = D.decide(vault, repository, D.Boundary(visit_id="visit_mixed", extraction_id=EXT,
                                                               section_id="sec1"), clock=_OP, view=dose_view).as_dict()
    out["dose"] = [fresh.as_dict()]
    out["dose_old_boundary"] = old.as_dict()
    # A late uptake callback for each earlier offer (protected in one copy, absent in the other).
    out["uptake"] = [D.record_uptake(vault, repository, f"{DOSE_DRAW_ID}_{k}", "taken", clock=_OP)
                     if _has_draw(paths, f"{DOSE_DRAW_ID}_{k}") else None for k in range(3)]
    # The public offer's delivery. Its reading holds withheld blocks, so (Option B, round 8) the draw
    # is withheld in the protected copy and deleted with its reading in the absent one: no delivery
    # is recorded in either.
    out["delivery"] = D.record_uptake(vault, repository, PUBLIC_DRAW, "delivered", clock=_OP) \
        if _has_draw(paths, PUBLIC_DRAW) else None

    # The reading sweep (a backfill: every source).
    _reset_ids(monkeypatch, 5)
    out["sweep"] = sweep(vault, repository, as_of=_iso(_now()), sweep_kind="backfill", view=dose_view).as_dict()

    # The report and the CLI's figures.
    RP.clear_cache()
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        out["report"] = _strip(json.loads(json.dumps(REP.build(vault, repository, connection, sensitivity=True,
                                                               now=_iso(_now())), default=str)))
    runner = CliRunner()
    for command in (["ad", "report", "--json", "--vault", str(paths.root)],
                    ["ad", "eval", "--json", "--vault", str(paths.root)]):
        RP.clear_cache()
        result = runner.invoke(app, command)
        out[" ".join(command[:2])] = _strip(json.loads(result.stdout)) if result.stdout.strip().startswith("{") \
            else result.stdout

    out["open_commissions"].append(_open_commissions(paths))

    # Every table's new rows (fix round 11, R2: not a hand-kept list, so the next writer is compared
    # too), less the incumbent's own tables (``OUT_OF_SCOPE``, each with its reason).
    out["writes"] = {table: sorted((_disclosed(paths, table, row)
                                    for row in set(_rows(paths.sqlite_path, table)) - before.get(table, set())
                                    if INCUMBENT not in row), key=repr)
                     for table in _tables(paths.sqlite_path)
                     if table not in OUT_OF_SCOPE and table not in COMPARED_THROUGH_VIEW}
    out["derived"] = {table: [row for row in _rows(paths.sqlite_path, table) if INCUMBENT not in row]
                      for table in AD_DERIVED}
    # ``practice_item_state`` as AD reads it (fix round 12, F42: AD's admission and generation read
    # it, so it is compared, through the view's reader, for every item the absent copy also has).
    view = material_view(load_vault(paths.root), Repository(paths.sqlite_path))
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        if hasattr(view, "item_states"):
            states = view.item_states(connection)
        else:  # a commit before round 12 (a fail-before run): what AD read then, the raw states
            states = {key: state for key, state in Repository(paths.sqlite_path).practice_item_states().items()
                      if not view.withheld(key)}
    out["item_states"] = {item_id: [state.difficulty, state.stability, state.retrievability, state.due_at,
                                    state.active, state.last_attempt_at]
                          for item_id, state in sorted(states.items())}
    return out


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


def make_copies(tmp_path, *, coupled: bool):
    """One base vault copied twice: protected material is written into one copy only, so it is
    physically absent from the other (never written, so nothing derived from it exists there
    either, the incumbent's own state included)."""

    base = _base(tmp_path, coupled=coupled)
    protected, absent = tmp_path / "protected", tmp_path / "absent"
    copy_tree_with_databases(base.root, protected)
    copy_tree_with_databases(base.root, absent)
    protected_paths, absent_paths = _paths(protected), _paths(absent)
    for paths in (protected_paths, absent_paths):
        _visits_with_lowerings(paths)
    seeded = _protect(protected_paths)
    _protected_offers(protected_paths, seeded["question"])
    _per_copy(absent_paths, protected=False)
    _per_copy(protected_paths, protected=True)
    # Option B (round 8): the protected copy's one reading holds withheld blocks, so it is absent
    # for AD's reading signals; the absent copy is the row deletion of that reading (its blocks,
    # units, assets and reading events; its items kept).
    from tests.ad_ingest_fakes import delete_reading

    delete_reading(absent_paths.sqlite_path, EXT)
    # AD's own seeded rows were written under each copy's protection as it stands now (round 2).
    for paths in (protected_paths, absent_paths):
        restamp(paths, _epoch(paths))
    return protected_paths, absent_paths
