"""Adaptive difficulty's A8 contract: protected == absent (fix round 9, ruling R7).

The metamorphic test is the guarantee for spec A8 (the AST scan in ``test_ad23_material_view.py``
stays as a lint). One vault is built and copied twice:

* **protected**: the copy gets protected material of every kind the verifies used: a held-out
  current item with sentinel stem, facet and surface family; a held-out item sharing the public
  items' LO, facet and family; a public item whose earlier ANSWERED revision is held out (its
  snapshot, presentation, frozen serve inputs and attempt); answers on protected material with
  extreme latencies and correct grades; a reveal of a held-out item; a commission result on a
  held-out item; a reading receipt from a held-out span; a Reader question citing a held-out span
  and a dose draw that offered it;
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
request, no AD write), and a no-protection parity case pinning F30 (a frozen dose on a facet absent
from current content stands).

Fakes only: no network, no model call, no paid call.
"""

from __future__ import annotations

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
    _attempt(paths, "pi_hist", at=T0 - timedelta(days=2), latency=90)
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
    _attempt(paths, "pi_shared", at=T0 - timedelta(hours=2), latency=60000)
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
    _attempt(paths, "pi_hist", at=T0 - timedelta(minutes=50), latency=60000, presentation_id="pp_hist_r9")
    repository = Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, "
                           "basis, created_at) VALUES ('rv_r9', 'pi_secret', ?, 'tutor_answer', 1.0, 'overlap', ?)",
                           (LO, _iso(T0 - timedelta(minutes=40))))
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


def _dose_draw(paths, question_id: str) -> None:
    from learnloop.db.stores import ad_serving

    with closing(connect(paths.sqlite_path)) as connection:
        ad_serving.insert_dose_row(connection, {
            "id": DOSE_DRAW_ID, "row_kind": "draw", "draw_key": f"visit_old:{EXT}:sec1", "visit_id": "visit_old",
            "extraction_id": EXT, "section_id": "sec1", "learning_object_ids": [LO],
            "feasible": ["none", "extra_question"], "infeasible": {}, "base_version": "b", "floor": 0.1,
            "propensities": {"none": 0.9, "extra_question": 0.1}, "seed": "s", "u": 0.95,
            "chosen_variant": "extra_question", "content": {"question_id": question_id, "style": "recall"},
            "forecast_p": None, "detail": {}, "created_at": _iso(T0 - timedelta(minutes=10))})
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
    out["dose"] = [fresh.as_dict(), old.as_dict()]

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
    seeded = _protect(protected_paths)
    _dose_draw(protected_paths, seeded["question"])
    _dose_draw(absent_paths, seeded["question"])
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
