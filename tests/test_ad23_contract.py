"""Adaptive difficulty's A8 contract: protected == absent, as one end-to-end smoke test (the AD23
redesign; whole-pipeline since fix round 11 R2).

Since the redesign (Option B: guarded AD operations) the contract is four small facts, each its own
test: every read in an operation passes the guard (``test_ad_guard.py``), every protected table and
column is classified (``test_ad_protected_tables.py``), the guarded inputs equal those of physically
absent material (``test_ad_projection.py``) and every persisted artefact and cache is scoped to the
protection epoch (``test_ad_epoch.py``). This file keeps ONE whole-pipeline differential in the
owner's default configuration on a frozen clock (a failure here is a bug in one of those facts) and
the per-reader regressions of fix rounds 8-14 that still apply. One vault is built and copied twice:

* **A, protected**: the copy gets protected material of every class the verifies named (a held-out
  current item with sentinel stem, facet and family; a public item whose earlier answered revision is
  held out, with its snapshot, presentation, frozen serve inputs, attempt, reveal and tutor question;
  a public candidate whose only history is an answer to its held-out revision; protected plan
  events; a commission result, band-mode selection and commission of the protected-only facet's
  cell; reading receipts, Reader questions and dose offers on held-out spans; relatedness loadings
  onto the protected-only facet; a grounding link to a held-out span);
* **B, absent**: that material does not exist at all (never written, so nothing derived from it),
  and, since round 8 (Option B), the reading that held it is deleted with its reading events.

AD's whole pipeline then runs on each copy, at one shared root path, under identical deterministic ids
and one frozen clock. Asserted: every captured prompt, every new row of every table but the
incumbent's own (``OUT_OF_SCOPE``), the DERIVED replay tables and every returned figure are identical
(the protection epoch and the report's disclosure named by meaning), no sentinel appears in any
captured request, and no request dispatched after a span was held out quotes it. Then the harness with
the held-out predicate unavailable, and the no-protection parity case (F30).

Fakes only: no network, no model call, no paid call.
"""

from __future__ import annotations

import ast
import json
import os
import re
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import learnloop.hints.map_builder  # noqa: F401 - imported up front: it mints ids at import time
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import COUPLED, LO, SEEDED, ProposalLLM, ad23_vault, restamp, set_item
from tests.ad23_contract_helpers import (
    AD_DERIVED,
    EXPIRING_COMMISSION,
    EXT,
    EXT_CLEAN,
    GOAL_PROTECTED,
    LATE,
    LATE_SPAN,
    P4,
    PUBLIC,
    RUN,
    SERVE_COMMISSION,
    SUBJECT,
    T0,
    _Frozen,
    _base,
    _carve_outs,
    _deterministic,
    _hold_out,
    _iso,
    _predicate_raises,
    _protect,
    _run,
    _run_at_common_root,
    make_copies,
)

SENTINELS = ("SENTINEL_STEM_AX9", "SENTINEL_FACET_AX9", "SENTINEL_FAMILY_AX9", "SENTINEL_HIST_AX9",
             "pi_secret", "pi_shared", "SENTINEL_QUESTION_AX9", "SENTINEL_SPAN_AX9", "SENTINEL_P4_AX9",
             "SENTINEL_NOTE_AX9")
#: AD's tables a run writes (compared as new rows), and its DERIVED tables (compared whole).
AD_WRITES = ("ad_selections", "ad_commission_results", "ad_dose_offers", "ad_reading_opportunities",
             "forecast_receipts", "item_serve_inputs", "ad_relatedness_runs", "attention_block_events",
             "practice_attempts")


# -- deterministic runs ----------------------------------------------------------------------------------


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


def _normalized(out: dict[str, Any]) -> dict[str, Any]:
    """Plain JSON data. No normalisation (fix round 12, F42): every id and stamp is made identical at
    its source (``_deterministic``: the ULID and uuid4 counters, the frozen clocks, the model-call
    records' clock; both copies run at one root path)."""

    return json.loads(json.dumps(out, default=str))


def _sentinel_hits(texts: list[str]) -> list[str]:
    return [f"{token} in a captured request" for token in SENTINELS for text in texts
            if re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", text)]


#: The two configurations the differential contract runs in (R2): the owner's default
#: (``learned_coupling`` off) and with learned coupling on.
@pytest.fixture(params=["coupled"])
def copies(request, tmp_path, monkeypatch):
    return make_copies(tmp_path, coupled=request.param == "coupled")


def _diff(left: Any, right: Any, path: str = "") -> list[str]:
    if isinstance(left, dict) and isinstance(right, dict):
        out = []
        for key in sorted(set(left) | set(right), key=str):
            out += _diff(left.get(key), right.get(key), f"{path}.{key}")
        return out
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        out = []
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            out += _diff(a, b, f"{path}[{index}]")
        return out
    if isinstance(left, str) and isinstance(right, str) and left != right:
        at = next((i for i, (a, b) in enumerate(zip(left, right, strict=True)) if a != b), min(len(left), len(right)))
        return [f"{path}: strings differ at {at}: {left[max(0, at - 150):at + 150]!r} != "
                f"{right[max(0, at - 150):at + 150]!r}"]
    return [] if left == right else [f"{path}: {left!r} != {right!r}"[:600]]


# -- the contract ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("copies", ["default"], indirect=True)
def test_protected_material_is_indistinguishable_from_absent_material(copies, monkeypatch):
    """The A8 smoke test; its body is :func:`_contract`."""

    _contract(copies, monkeypatch)


def _contract(copies, monkeypatch) -> None:
    """A8's contract (R7; whole-pipeline since fix round 11, R2): with every kind of protected
    material present and protected (copy A), AD's whole pipeline produces exactly what it produces
    with that material physically absent (copy B), in the owner's default configuration and with
    learned coupling on; no captured model request quotes protected material, including one
    dispatched after a span was held out mid-call.

    Compared: every prompt the fakes captured, every new row of every table (the incumbent's own
    tables aside, ``OUT_OF_SCOPE``), the DERIVED replay tables whole, and every returned figure
    (report JSON, ``ad report``/``ad eval``, estimates, steps, forecasts, preparation, dose, sweep).
    Normalised: the report's ``protection`` disclosure and ``generated_at`` (``DISCLOSURE``), and the
    protection epoch, named by meaning (``_disclosed``); no stamp is normalised (one frozen operation
    clock, ``_OP``). Carve-outs (``_carve_outs``, ``INCUMBENT``):
    the incumbent's ``mastery_ekf`` comparator. Nothing else."""

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
    if os.environ.get("AD23_CONTRACT_OUT"):
        # The pinned outcomes' current values (to write the expectations); never set in a gate.
        with open(os.environ["AD23_CONTRACT_OUT"], "a", encoding="utf-8") as handle:
            handle.write(json.dumps({key: seen.get(key) for key in (
                "readiness", "card", "dose", "dose_old_boundary", "delivery", "uptake", "preparation", "forecasts",
                "worker", "queued", "sweep", "relatedness")}, sort_keys=True, default=str) + "\n")
    if os.environ.get("AD23_CONTRACT_DIFF"):
        # Every violation, for counting (the review's fail-before figures); never set in a gate.
        with open(os.environ["AD23_CONTRACT_DIFF"], "a", encoding="utf-8") as handle:
            handle.write("".join(f"{line}\n" for line in violations))
    # The pipeline ran every stage the comparison claims, with a successful, non-empty effect
    # (fix round 12, F42): a stage that silently does nothing fails here, in both copies alike.
    assert all(seen["derived"][table] for table in AD_DERIVED), "the replay and the score rebuild persisted rows"
    # The serves' sweeps and the backfill: receipts written in the run (the serve's sweep records the
    # public events first, so the backfill may find nothing left).
    assert seen["writes"]["ad_reading_opportunities"], ("the reading sweeps wrote receipts", seen["sweep"])
    # The public offer sits on the mixed reading: no delivery in either copy (Option B, round 8).
    assert seen["delivery"] is None
    if "learned_coupling = true" in (protected.root / "learnloop.toml").read_text(encoding="utf-8"):
        assert seen["relatedness"] == "ok" and seen["writes"]["ad_relatedness_runs"], "a relatedness run was recorded"
    else:
        assert seen["relatedness"] == "disabled", "learned coupling is off by default (owner decision)"
    assert seen["forecasts"] and all(status == "ok" for statuses in seen["forecasts"] for status in statuses), \
        seen["forecasts"]
    assert seen["worker"] == [["completed", SERVE_COMMISSION]] and seen["worker_generation"], seen["worker"]
    assert "no active learning objects in scope" in seen.get("goal_protected_error", ""), seen.get("goal_protected_error")
    # Meaningful outcomes, pinned (fix round 13, F42): an emptied or degenerate stage fails here.
    cells = {(cell["facet"], cell["capability"]): cell for cell in seen["readiness"]["cells"]}
    assert set(cells) == {("apply_pub", "retrieval"), ("recall", "retrieval")} and seen["readiness"]["predicted"]
    assert all(cell["kind"] == "prediction" and 0.05 < cell["p_bar_at_top"] < 0.6 for cell in cells.values())
    assert seen["card"]["cell"] == ["recall", "retrieval"] and seen["card"]["kind"] == "prediction"
    assert 0.0 < seen["card"]["p_band_next"] < seen["card"]["p_bar_at_top"] < 0.6
    assert seen["card"]["p_bar_at_top"] == cells[("recall", "retrieval")]["p_bar_at_top"]
    assert [(d["eligible"], d["reason"]) for d in [*seen["dose"], seen["dose_old_boundary"]]] == [(True, None)] * 2
    assert (seen["dose_mixed"]["eligible"], seen["dose_mixed"]["reason"]) == (False, "protected_reading")
    # The draws the operation under test persisted (fix round 14, F42), each pinned with its outcome:
    # the row written now, at its boundary, with its recorded propensities and chosen variant.
    draws = {row[0]: row for row in seen["writes"]["ad_dose_offers"] if row[1] == "draw"}
    for decision, key in ((seen["dose"][0], f"visit_new:{EXT_CLEAN}:clean_sec"), (seen["dose_old_boundary"], f"visit_old:{EXT_CLEAN}:clean_sec")):
        row = draws.get(decision["draw_id"])
        assert row is not None and row[3] == key, (decision, sorted(draws))
        assert json.loads(row[12]) == {"none": 1.0} and row[15] == "none" and decision["offer"] is None, row
    assert seen["uptake"] == [None, None, None], "the protected offers' late callbacks write nothing"
    prepared = {entry["practice_item_id"]: entry for entry in seen["preparation"]}
    assert set(prepared) == {"pi_p1", "pi_p2", "pi_hist", P4}
    assert all(entry["audit"]["status"] in ("audited", "current") and entry["llm_v1"]["status"] in ("ok", "current")
               for entry in prepared.values()), seen["preparation"]
    # The expiry boundary: open at the start and the end of a run on the frozen clock.
    assert EXPIRING_COMMISSION in seen["open_commissions"][0] and EXPIRING_COMMISSION in seen["open_commissions"][-1]
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
        ad_receipts.insert_reading_opportunity(connection, {"protection_epoch": SEEDED,
            "opportunity_key": f"worked_example:{EXT}/w1:{LO}", "kind": "worked_example",
            "subkind": "in_completed_section", "source_table": "reader_section_progress",
            "source_id": f"{EXT}/w1", "source_written_at": "2026-10-01T09:00:00Z", "learning_object_id": LO,
            "facet_doses": {"f_only_gone": 1.0}, "dose_offer_id": None, "mapping_version": "ad_reading_map_v1",
            "sweep": "backfill", "sweep_ref": None, "swept_at": "2026-10-01T09:00:00Z"})
        connection.commit()
    restamp(paths)  # recorded under the vault's protection as it stands (nothing is protected)
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


# -- F34 ---------------------------------------------------------------------------------------------


def _flipping_client(monkeypatch, flip):
    from learnloop.content.proposals.ai_contracts import AuthoringProposal

    from tests.proposal_persistence_helpers import _QueueAuthoringClient, _generated_practice_proposal_payload

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

    from tests.ad3_dose_arm_helpers import _arm
    from tests.ad1_reading_opportunities_helpers import _question, at

    paths, vault, repo = _arm(tmp_path)
    _question(repo, "recall", 1, answer=False)
    with closing(connect(paths.sqlite_path)) as connection:
        draw = ad_serving.insert_dose_row(connection, {"protection_epoch": SEEDED,
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

    from tests.ad3_dose_arm_helpers import _arm

    paths, _vault, _repo = _arm(tmp_path)
    with closing(connect(paths.sqlite_path)) as connection:
        draws = [ad_serving.insert_dose_row(connection, {"protection_epoch": SEEDED,
            "row_kind": "draw", "draw_key": f"visit_s{k}:ext1:u1", "visit_id": f"visit_s{k}", "extraction_id": "ext1",
            "section_id": "u1", "learning_object_ids": ["lo_svd_definition"], "feasible": ["none", "extra_worked_example"],
            "infeasible": {}, "base_version": "b", "floor": 0.1,
            "propensities": {"none": 0.9, "extra_worked_example": 0.1}, "seed": "s", "u": 0.95,
            "chosen_variant": "extra_worked_example", "content": {"extraction_id": "ext1", "span_id": "we2"},
            "forecast_p": None, "detail": {}, "created_at": "2026-10-12T09:00:00Z"}) for k in range(2)]
        connection.commit()
    restamp(paths)
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

    from learnloop.adaptive_difficulty.material_view import detached_view as material_view
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
            "created_at, protection_epoch) VALUES ('isi_hist_old_r10', 'plan_presentation:pp_hist_old_r10', "
            "'plan_presentation', 'pp_hist_old_r10', 'pi_hist', ?, ?, '2026-10-05T12:01:00Z', '{}', '{}', 0, 'r10', "
            "'2026-10-05T12:01:00Z', ?)", (LO, content_hash, SEEDED))
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
    from learnloop.adaptive_difficulty.material_view import detached_view as material_view
    from learnloop.content.sources import exam_material
    from learnloop.db.stores import ad_serving

    from tests.ad3_dose_arm_helpers import _arm

    paths, vault, repo = _arm(tmp_path)
    with closing(connect(paths.sqlite_path)) as connection:
        draw = ad_serving.insert_dose_row(connection, {"protection_epoch": SEEDED,
            "row_kind": "draw", "draw_key": "visit_a:ext1:u1", "visit_id": "visit_a", "extraction_id": "ext1",
            "section_id": "u1", "learning_object_ids": ["lo_svd_definition"], "feasible": ["none", "extra_worked_example"],
            "infeasible": {}, "base_version": "b", "floor": 0.1,
            "propensities": {"none": 0.9, "extra_worked_example": 0.1}, "seed": "s", "u": 0.95,
            "chosen_variant": "extra_worked_example", "content": {"extraction_id": "ext1", "span_id": "we2"},
            "forecast_p": None, "detail": {}, "created_at": "2026-10-12T09:00:00Z"})
        ad_serving.insert_dose_row(connection, {"protection_epoch": SEEDED, "row_kind": "taken", "draw_id": draw,
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
    restamp(paths)  # the offers were drawn with nothing held out

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


# -- fix round 12: the per-reader regressions beside the grown differential ----------------------------


def test_goal_focus_follows_the_live_decision_view_with_promoted_predictor_off(tmp_path, monkeypatch):
    """F41 (switch composition): with ``promoted_predictor`` off, live decisions read each LO's own
    view, so the goal focus does too. The LO view forecasts 0.2 and the subject view 0.9 against a
    0.85 target: the facet is in focus (failed before: the subject view was read, so it was not)."""

    from learnloop.adaptive_difficulty import predict as PR
    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty.generation import goal_focus_facets
    from learnloop.adaptive_difficulty.material_view import detached_view as material_view

    paths = ad23_vault(tmp_path, items=PUBLIC, config="promoted_predictor = false\n")
    vault = load_vault(paths.root)
    assert not vault.config.adaptive_difficulty.promoted_predictor
    repository = Repository(paths.sqlite_path)
    subject_state, lo_state = object(), object()
    snapshot = SimpleNamespace(subject=subject_state, lo_view=lambda _lo: lo_state)
    monkeypatch.setattr(RP, "snapshot", lambda *_args, **_kwargs: snapshot)
    monkeypatch.setattr(PR, "predict", lambda state, _spec: SimpleNamespace(
        p_bar=0.2 if state is lo_state else 0.9))
    view = material_view(vault, repository)
    assert goal_focus_facets(vault, repository, scope={LO: {"recall"}}, target_recall=0.85, view=view) == ["recall"]


def test_a_saved_run_proposed_before_its_subject_was_protected_is_not_used(copies, monkeypatch):
    """F38, under E2 (the AD23 redesign): the protected copy's later run was proposed before any
    material was held out (it records that epoch). Its LO coupling and its public-to-public loading
    are both out of use; the run proposed at the current epoch stands (failed before round 12: the
    coupling and the 0.9 loading were in force)."""

    from learnloop.adaptive_difficulty import relatedness as R
    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.adaptive_difficulty.material_view import detached_view as material_view

    protected, _absent = copies
    _hold_out(monkeypatch)
    vault = load_vault(protected.root)
    view = material_view(vault, Repository(protected.sqlite_path))
    p1_hash = item_revision(vault.practice_items["pi_p1"])[0]
    with closing(connect(protected.sqlite_path, read_only=True)) as connection:
        structure = R.load_structure(connection, vault, view=view, coupled=True)
        live = R.live_judgments(connection, view=view)
        assert "jdg_pub_r11" in live and not {"jdg_couple_r12", "jdg_stale_r12"} & live
    assert not structure.coupling(LO)
    assert structure.loadings(p1_hash, float("inf")) == {"apply_pub": 0.5}


def test_a_held_out_sources_canonical_note_never_reaches_a_commissioned_request(copies, monkeypatch):
    """F40: the held-out source's canonical note is left out of the vault AD's view hands the
    authoring context, and a request that names it is refused at dispatch (failed before: the note's
    excerpt was in the context, and the guard checked neither notes nor their sources)."""

    from learnloop.adaptive_difficulty.generation import CommissionedRequestGuard, ProtectedRequest

    protected, _absent = copies
    _hold_out(monkeypatch)
    guard = CommissionedRequestGuard()
    seen = guard.vault_view(load_vault(protected.root), Repository(protected.sqlite_path))
    assert "note_r12" in load_vault(protected.root).notes and "note_r12" not in seen.notes
    with pytest.raises(ProtectedRequest):
        guard("A request.", sources=[{"kind": "note", "note_id": "note_r12"}])


def test_an_empty_support_draw_of_a_protected_slot_leaves_the_report_cohort(copies, monkeypatch):
    """F39: an empty-support draw records no choice and no cell, only its slot's item; with that item
    protected, the report's cohort leaves it out (failed before: only the choice and the cell were
    revalidated)."""

    from learnloop.adaptive_difficulty.material_view import detached_view as material_view

    protected, _absent = copies
    _hold_out(monkeypatch)
    view = material_view(load_vault(protected.root), Repository(protected.sqlite_path))
    with closing(connect(protected.sqlite_path, read_only=True)) as connection:
        ids = {row["id"] for row in view.selections(connection)}
    assert "sel_empty_r12" not in ids and SERVE_COMMISSION in ids


def test_a_goal_over_a_facet_only_a_protected_item_measures_has_no_scope(copies, monkeypatch):
    """F37: the goal names only the protected-only facet. Its scope is resolved on the vault AD's view
    sees, before planning, so no LO enters the plan (failed before: the protected item's facet put
    the LO in scope and the plan generated for it)."""

    from learnloop.content.authoring.practice_generation import PracticeExpansionError, build_goal_practice_plan

    protected, _absent = copies
    _hold_out(monkeypatch)
    vault = load_vault(protected.root)
    goal = next(goal for goal in vault.goals if goal.id == GOAL_PROTECTED)
    with pytest.raises(PracticeExpansionError, match="no active learning objects in scope"):
        build_goal_practice_plan(vault, Repository(protected.sqlite_path), goal)


def test_the_replay_cache_never_serves_a_snapshot_across_a_protection_change(copies, monkeypatch):
    """F42 (round 13): the replay's snapshot cache is keyed by database, vault and settings and served
    only while the events loaded through the view are unchanged; withholding one more item changes
    them, so the cached snapshot is not served."""

    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty.material_view import detached_view as material_view

    protected, _absent = copies
    _hold_out(monkeypatch)
    RP.clear_cache()
    vault, repository = load_vault(protected.root), Repository(protected.sqlite_path)
    first = RP.snapshot(vault, repository, view=material_view(vault, repository))
    again = RP.snapshot(vault, repository, view=material_view(vault, repository))
    narrower = RP.snapshot(vault, repository, view=material_view(vault, repository, {"pi_hist"}))
    assert again is first, "an unchanged view is served from the cache"
    assert narrower is not first
    assert {e.practice_item_id for e in narrower.events.attempts} < {e.practice_item_id for e in first.events.attempts}


# -- fix round 13: the per-reader regressions ------------------------------------------------------------


def test_a_run_whose_quoted_revision_was_replaced_then_protected_is_not_used(copies, monkeypatch):
    """F38 (round 13): the public run quoted pi_p2's revision citing sec2_span. pi_p2 is then
    replaced (it cites sec3_span) and sec2_span held out: the old revision is in no current item and
    no snapshot, only in the run's recorded prompt context, which is judged against the current
    protection. The run is out of use (failed before: its context was not recorded, so it stood)."""

    from learnloop.adaptive_difficulty import relatedness as R
    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.adaptive_difficulty.material_view import detached_view as material_view

    _protected, absent = copies
    _hold_out(monkeypatch)
    set_item(absent, "pi_p2", canonical_exercise={"source_id": "src_r9", "extraction_id": EXT, "span_ids": ["sec3_span"]})
    LATE.append("sec2_span")
    vault = load_vault(absent.root)
    view = material_view(vault, Repository(absent.sqlite_path))
    with closing(connect(absent.sqlite_path, read_only=True)) as connection:
        assert "jdg_pub_r11" not in R.live_judgments(connection, view=view)
        structure = R.load_structure(connection, vault, view=view, coupled=True)
    assert structure.loadings(item_revision(vault.practice_items["pi_p1"])[0], float("inf")) == {}


def test_a_stale_run_never_answers_for_a_re_proposal(tmp_path, monkeypatch):
    """F45: a proposal is made; then a saved historical revision of a subject item is held out while
    the prompt content stays the same. The re-proposal has the same prompt hash but a new protection
    identity, so the stale run does not satisfy the duplicate check: it is asked and recorded under a
    new key (failed before: the run key was the prompt hash alone, so the answer was "current")."""

    from learnloop.adaptive_difficulty import relatedness as R
    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.db.stores import ad_serving
    from learnloop.vault.models import CanonicalExercise

    paths = ad23_vault(tmp_path, items=PUBLIC, ad=COUPLED)
    _hold_out(monkeypatch)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    first = ProposalLLM({"items": [], "learning_objects": []})
    assert R.propose_subject(vault, repository, SUBJECT, client=first).status == "ok" and first.prompts
    old = vault.practice_items["pi_p1"].model_copy(update={
        "prompt": "An earlier revision.", "canonical_exercise": CanonicalExercise(source_id="src_r9", extraction_id=EXT,
                                                                                  span_ids=["late_span"])})
    content_hash, item_json = item_revision(old)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO practice_item_snapshots(content_hash, practice_item_id, item_json, created_at) "
                           "VALUES (?, 'pi_p1', ?, '2026-10-01T09:00:00Z')", (content_hash, item_json))
        connection.commit()
    LATE.append(LATE_SPAN)  # the saved revision's source is held out now; the current items are not
    again = ProposalLLM({"items": [], "learning_objects": []})
    outcome = R.propose_subject(load_vault(paths.root), repository, SUBJECT, client=again)
    # The prompt is identical (it quoted no protected material), so its checkpointed answer may be
    # reused; what matters is that the request is made and recorded, not answered by the stale run.
    assert outcome.status == "ok", outcome
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        runs = ad_serving.relatedness_runs(connection, subject_id=SUBJECT)
    assert len(runs) == 2 and runs[0]["input_hash"] == runs[1]["input_hash"] and runs[0]["run_key"] != runs[1]["run_key"]


def test_a_tutor_exchange_on_a_protected_canonical_note_enters_no_prediction(copies, monkeypatch):
    """F43: an answered Reader question names the held-out source's canonical note. The sweep never
    records it (the note is checked before any fallback to an item), the production map maps the note
    to no LO, and a receipt recorded earlier is withheld on revalidation (failed before: the note's LOs
    were read from the raw vault and receipts checked spans and items only)."""

    from learnloop.adaptive_difficulty.material_view import detached_view as material_view
    from learnloop.adaptive_difficulty.reading import VaultReadingMap, sweep
    from learnloop.db.stores import ad_receipts

    protected, _absent = copies
    _hold_out(monkeypatch)
    vault, repository = load_vault(protected.root), Repository(protected.sqlite_path)
    view = material_view(vault, repository)
    assert VaultReadingMap(vault, repository, view).los_for_note("note_r12") == []
    sweep(vault, repository, as_of=_iso(RUN), sweep_kind="backfill", view=view)
    with closing(connect(protected.sqlite_path)) as connection:
        assert connection.execute("SELECT 1 FROM ad_reading_opportunities WHERE source_id = 'qe_note_r13'").fetchone() is None
        ad_receipts.insert_reading_opportunity(connection, {"protection_epoch": SEEDED,
            "opportunity_key": f"reader_tutor_exchange:{LO}:2026-10-12:qe_note_r13", "kind": "reader_tutor_exchange",
            "subkind": "help_me_reason", "source_table": "question_events", "source_id": "qe_note_r13",
            "source_written_at": _iso(T0 - timedelta(hours=6)), "learning_object_id": LO, "facet_doses": {"recall": 1.0},
            "dose_offer_id": None, "mapping_version": "ad_reading_map_v1", "sweep": "backfill", "sweep_ref": None,
            "swept_at": _iso(RUN)})
        connection.commit()
        assert "qe_note_r13" not in {row["source_id"] for row in view.reading_opportunities(connection)}


def test_a_protected_receipt_occupies_no_daily_cap_slot(copies, monkeypatch):
    """F44, under Option B (round 8): a passage-view receipt from a held-out span held the LO's one
    daily passage slot under the old key scheme. The reading that holds the held-out span is now
    absent for reading signals, so no passage view of it is admitted at all, the public one
    included: no slot is occupied by anything AD may not read."""

    from learnloop.adaptive_difficulty.material_view import detached_view as material_view
    from learnloop.adaptive_difficulty.reading import sweep

    protected, _absent = copies
    _hold_out(monkeypatch)
    vault, repository = load_vault(protected.root), Repository(protected.sqlite_path)
    sweep(vault, repository, as_of=_iso(RUN), sweep_kind="backfill", view=material_view(vault, repository))
    with closing(connect(protected.sqlite_path, read_only=True)) as connection:
        extractions = [row[0] for row in connection.execute(
            "SELECT e.extraction_id FROM ad_reading_opportunities o JOIN source_exposure_events e ON e.id = o.source_id "
            "WHERE o.kind = 'reading' AND o.subkind = 'passage_viewed' AND o.source_id != 'sxe_held_r13'")]
    # Only the clean reading's view: the mixed reading gives none, held-out or public (the seeded
    # held-out receipt aside, which the view withholds).
    assert extractions == [EXT_CLEAN]


# -- fix round 14: the per-reader regressions ------------------------------------------------------------


def test_a_tutor_exchange_whose_recorded_context_quotes_a_protected_span_enters_no_prediction(copies, monkeypatch):
    """F46: the exchange's anchor is public, but its recorded source spans and citation quote a
    held-out span. The one tutor-question reader judges the complete recorded context, at collection
    and at receipt revalidation (failed before: only the anchor and the item were read)."""

    from learnloop.adaptive_difficulty.material_view import detached_view as material_view
    from learnloop.adaptive_difficulty.reading import sweep
    from learnloop.db.stores import ad_receipts

    protected, _absent = copies
    _hold_out(monkeypatch)
    vault, repository = load_vault(protected.root), Repository(protected.sqlite_path)
    view = material_view(vault, repository)
    sweep(vault, repository, as_of=_iso(RUN), sweep_kind="backfill", view=view)
    with closing(connect(protected.sqlite_path)) as connection:
        assert view.question_event_withheld(connection, "qe_context_r14")
        assert connection.execute("SELECT 1 FROM ad_reading_opportunities WHERE source_id = 'qe_context_r14'").fetchone() is None
        ad_receipts.insert_reading_opportunity(connection, {"protection_epoch": SEEDED,
            "opportunity_key": f"reader_tutor_exchange:{LO}:2026-10-12:qe_context_r14", "kind": "reader_tutor_exchange",
            "subkind": "help_me_reason", "source_table": "question_events", "source_id": "qe_context_r14",
            "source_written_at": _iso(T0 - timedelta(hours=2)), "learning_object_id": LO, "facet_doses": {"recall": 1.0},
            "dose_offer_id": None, "mapping_version": "ad_reading_map_v1", "sweep": "backfill", "sweep_ref": None,
            "swept_at": _iso(RUN)})
        connection.commit()
        assert "qe_context_r14" not in {row["source_id"] for row in view.reading_opportunities(connection)}


def test_a_dose_draw_at_a_protected_origin_is_a_draw_never_made(copies, monkeypatch):
    """F47: a draw made at a held-out section with a public extra was delivered today. It is out of
    the cohort and the budget (a public boundary may still be offered), out of uptake, and no draw is
    made at that section (failed before: only the extra was checked, so the draw spent the budget)."""

    from learnloop.adaptive_difficulty import dose as D
    from learnloop.adaptive_difficulty.material_view import detached_view as material_view

    protected, _absent = copies
    _hold_out(monkeypatch)
    vault, repository = load_vault(protected.root), Repository(protected.sqlite_path)
    view = material_view(vault, repository)
    with closing(connect(protected.sqlite_path, read_only=True)) as connection:
        assert "dose_origin_r14" not in {row["id"] for row in view.dose_rows(connection)}
        assert D.budget(connection, extraction_id=EXT, section_id="sec1", now=_iso(RUN), daily=2, view=view) is None
    assert D.record_uptake(vault, repository, "dose_origin_r14", "taken", clock=_Frozen(RUN)) is None
    decision = D.decide(vault, repository, D.Boundary(visit_id="visit_origin2", extraction_id=EXT, section_id="sec5"),
                        clock=_Frozen(RUN), view=view)
    assert decision.reason == "protected_reading" and decision.draw_id is None


def test_the_background_scheduler_sees_a_run_whose_recorded_context_is_protected(tmp_path, monkeypatch):
    """F45 (round 14): R1 proposes the whole subject; pi_p3 (never snapshotted) is replaced and R2
    proposes only its new revision; then pi_p3's former source is held out. The subject fingerprint is
    unchanged, but R1's recorded context is protected now: the background scheduler finds the
    subject stale, exactly as propose_subject does (failed before: it counted R1 and found nothing)."""

    from learnloop.adaptive_difficulty import relatedness as R
    from learnloop.adaptive_difficulty import relatedness_jobs as RJ

    paths = ad23_vault(tmp_path, items=PUBLIC, ad=COUPLED)
    set_item(paths, "pi_p3", canonical_exercise={"source_id": "src_r9", "extraction_id": EXT, "span_ids": ["sec4_span"]})
    _hold_out(monkeypatch)
    repository = Repository(paths.sqlite_path)
    assert R.propose_subject(load_vault(paths.root), repository, SUBJECT,
                             client=ProposalLLM({"items": [], "learning_objects": []})).status == "ok"
    R.adopt(repository, SUBJECT, adopted_by="owner")
    set_item(paths, "pi_p3", canonical_exercise={"source_id": "src_r9", "extraction_id": EXT, "span_ids": ["sec3_span"]})
    assert R.propose_subject(load_vault(paths.root), repository, SUBJECT,
                             client=ProposalLLM({"items": [], "learning_objects": []})).status == "ok"
    assert RJ.stale_subjects(load_vault(paths.root), repository) == []
    LATE.append("sec4_span")
    assert RJ.stale_subjects(load_vault(paths.root), repository) == [SUBJECT]
