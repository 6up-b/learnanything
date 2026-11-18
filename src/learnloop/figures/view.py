"""How a stored figure is presented now: its row under today's switches, and the view the Reader is sent.

A stored row is never rewritten; what goes out is computed on every read. :func:`figure_view` presents a row through
one chain (:func:`_presented_row`): a legacy ``verified`` shown as an illustration (:func:`shown_row`), each tier or
panel kind that is switched off shown as "can't draw this yet" with its program withheld (:func:`advanced_off_row`,
:func:`sketch_off_row`, :func:`rich_off_row`), a sketch verified under another engine or verifier verified again by
code, its verdict appended to ``judgment_ledger`` (:func:`sketch_rechecked`), a figure whose stated claim the source
check proved different shown failed (:func:`source_rejected`), and the free-text label rule applied as presented
(:func:`worded_row`). The view adds the code-owned label, the predictions without their answers, the source check's
lines and, for a quick figure, its fuller version's state (:func:`fuller_state`). :func:`redelivered_view` presents a
view kept since its build as it may go out now.

Whether the figure itself may go out is :mod:`.protection`'s question, asked by the callers before this module
presents it; the view asks it only of what it adds (a fuller version's learner state, a pre-build's unqueued intent).
This module imports nothing of the request, the grounding, the listing or the build: they import it.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Mapping
from contextlib import closing
from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import figures as store
from learnloop.db.stores.judgments import append_judgment
from learnloop.figure_admission import (
    advanced_panels_enabled,
    predictions_enabled,
    revisions_enabled,
    rich_tiers_enabled,
    show_me_enabled,
)
from learnloop.figures import elements as E
from learnloop.figures import labels as L
from learnloop.figures import rich as RICH
from learnloop.figures import sketch as K
from learnloop.figures import source_check as SC
from learnloop.figures import spec as S
from learnloop.figures import verify as V
from learnloop.figures.protection import RICH_INTENT_KEY, learner_state_withheld
from learnloop.figures.sketch import sketch_ready
from learnloop.figures.spec import RICH_SPEC_VERSIONS


#: What a figure built with nothing from the learner's books says (RW1c's
#: abstention): a code-owned label (:mod:`.labels`).
NOT_FROM_BOOKS_LABEL = L.NOT_FROM_BOOKS_LABEL
LEDGER_TASK = "figure_verified"
#: Why a reconstruction is an illustration in RW5a (the owner's scope
#: decision, 2026-10-21: "matches the book's equation (checked)" is RW5c's).
RECONSTRUCTION_REASON = "the book check comes in a later version"


LABELS = {
    "illustrative": L.ILLUSTRATIVE_LABEL,
}
#: The sketch's code-owned badges (spec §6.6, §9.5; :mod:`.labels`): never "checked against the book".
SKETCH_LABEL = L.SKETCH_LABEL
SKETCH_UNCHECKED_LABEL = L.SKETCH_UNCHECKED_LABEL
SKETCH_NOT_FROM_BOOKS_LABEL = L.SKETCH_NOT_FROM_BOOKS_LABEL
#: What a stored sketch shows while the tier is off, and when a new engine refuses it.
SKETCH_OFF_KIND = "a simulation (figures.sketch_enabled is off)"
ENGINE_CHANGED_REASON = "couldn't run under this version · rebuild"


def rich_row(row: Mapping[str, Any]) -> bool:
    """RW5d P2b: a stored rich figure (a Manim figure)."""

    return row.get("tier") in RICH.RICH_TIERS or row.get("spec_version") in RICH_SPEC_VERSIONS


#: What a stored figure that uses an RW5b panel shows while the panels are off.
ADVANCED_OFF_KIND = "a panel kind that is switched off (figures.advanced_panels_enabled)"


# ---------------------------------------------------------------------------
# A stored row under the switches now
# ---------------------------------------------------------------------------

def shown_row(row: Mapping[str, Any]) -> Mapping[str, Any]:
    """The row as RW5a may show it: nothing in RW5a produces "verified", and a
    stored one (from a build before the owner's scope decision of
    2026-10-21) is shown as the illustration RW5a's rules make it."""

    if store.shown_verification(row.get("verification")) == row.get("verification"):
        return row
    report = row.get("verification_report") or {}
    return {**row, "verification": V.ILLUSTRATIVE,
            "verification_report": {**report, "reason": RECONSTRUCTION_REASON}}


#: The properties code checked before a figure shows, as closed keys (final
#: round, High 1): the Reader's code-owned frame names each with its own
#: words, so nothing model-written can reach the frame's badge.
PROPERTY_CHECKS = ("values_finite", "integrates_to_one", "sums_to_one", "nonnegative", "bounded", "finite",
                   "monotone_nondecreasing", "shaded_areas")


def _advanced_kinds(row: Mapping[str, Any]) -> list[str]:
    """The RW5b panel kinds a stored figure's spec uses (none when it has no spec)."""

    if not row.get("spec_json"):
        return []
    try:
        return list(S.advanced_kinds(json.loads(row["spec_json"])))
    except (TypeError, ValueError, AttributeError):
        return []


def advanced_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]:
    """RW5b: a shown figure that uses a heat map, vector field, trajectory or
    iterated map, while ``figures.advanced_panels_enabled`` is off, is the
    unsupported-kind state ("can't draw this yet"); its spec never goes out."""

    if advanced_panels_enabled(vault) or row.get("verification") not in store.SHOWN or not row.get("spec_json"):
        return row
    try:
        kinds = S.advanced_kinds(json.loads(row["spec_json"]))
    except (TypeError, ValueError):
        return row
    if not kinds:
        return row
    report = dict(row.get("verification_report") or {})
    return {**row, "verification": V.UNSUPPORTED, "unsupported_kind": ADVANCED_OFF_KIND, "spec_json": None,
            "verification_report": {**report, "reason": f"{', '.join(dict.fromkeys(kinds))} is switched off"}}


def sketch_row(row: Mapping[str, Any]) -> bool:
    """RW5d P2: a stored sketch."""

    return row.get("tier") == "sketch" or row.get("spec_version") == S.SKETCH_VERSION


def sketch_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]:
    """RW5d P2: a shown sketch while ``figures.sketch_enabled`` is off (or the
    engine can't run here) is the unsupported-kind state ("can't draw this
    yet"); its program never goes out."""

    if not sketch_row(row) or row.get("verification") not in store.SHOWN or sketch_ready(vault):
        return row
    report = dict(row.get("verification_report") or {})
    return {**row, "verification": V.UNSUPPORTED, "unsupported_kind": SKETCH_OFF_KIND, "spec_json": None,
            "verification_report": {**report, "reason": "the sketch tier is switched off"}}


def rich_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]:
    """RW5d P2b: a shown rich figure while ``figures.rich_tiers_enabled`` is
    off is the unsupported-kind state ("can't show this kind here"); its
    program and video never go out."""

    if not rich_row(row) or row.get("verification") not in store.SHOWN or rich_tiers_enabled(vault):
        return row
    report = dict(row.get("verification_report") or {})
    return {**row, "verification": V.UNSUPPORTED, "unsupported_kind": RICH.RICH_OFF_KIND, "spec_json": None,
            "media_file_name": None, "verification_report": {**report, "reason": "the rich tiers are switched off",
                                                             "rich_off": True}}


# ---------------------------------------------------------------------------
# A sketch verified again under this engine and verifier
# ---------------------------------------------------------------------------

_RECHECKED: dict[tuple[str, str, str], dict[str, Any]] = {}
_RECHECKED_GUARD = threading.Lock()
#: The input revision a re-verification judgment records (Codex review F8):
#: the program, the engine it was run under and (Codex review F11, round 3)
#: the verifier's report version.
REVERIFY_VERSION = "sketch-reverify-v1"


def reverify_hash(spec_json: str, engine_sha256: str, verifier_version: str | None = None) -> str:
    from learnloop.figures.sketch_verify import VERIFIER_REPORT_VERSION

    verifier = verifier_version or VERIFIER_REPORT_VERSION
    return hashlib.sha256(f"{REVERIFY_VERSION}\n{engine_sha256}\n{verifier}\n{spec_json}".encode("utf-8")).hexdigest()


def _stored_verifier(row: Mapping[str, Any]) -> str | None:
    """The verifier report version a stored row's report was made by (None:
    before the version existed)."""

    found = (row.get("verification_report") or {}).get("verifier_version")
    return str(found) if found else None


def _record_reverification(repository: Repository | None, row: Mapping[str, Any], cached: Mapping[str, Any],
                           engine_sha256: str) -> None:
    """Codex review F8: an engine re-verification is a verifier verdict, so
    it is appended to ``judgment_ledger`` (task ``figure_verified``, judge
    ``verifier``) before the figure is delivered, superseding the figure's
    last verdict on that question. Keyed by the program, the engine and the
    verifier version (:func:`reverify_hash`): once per (figure, engine,
    verifier), however often it is listed or the process restarts. The
    rationale is its provenance: both engine digests and verifier versions,
    the outcome's reason or check count, and the digest of the report the
    delivery uses."""

    if repository is None or getattr(repository, "_read_only", False):
        return
    figure_id = str(row["id"])
    input_hash = reverify_hash(str(row["spec_json"]), engine_sha256)
    report = cached.get("report") or {}
    outcome = str(cached["outcome"])
    summary = (f"{len(report.get('checks') or [])} checks" if outcome == V.ILLUSTRATIVE
               else str(report.get("reason") or "it no longer passes"))
    digest = hashlib.sha256(json.dumps(report, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    from learnloop.figures.sketch_verify import VERIFIER_REPORT_VERSION

    rationale = (f"re-verified under sketch engine {engine_sha256[:12]} and {VERIFIER_REPORT_VERSION} (built under "
                 f"{str(row.get('engine_sha256') or '?')[:12]} and {_stored_verifier(row) or 'an unversioned verifier'})"
                 f"; report {digest[:16]}; {summary}")
    with repository.atomic():
        connection = repository.connection()
        verdicts = store.figure_verdicts(connection, LEDGER_TASK, figure_id)
        if any(found["judge"] == "verifier" and found["input_hash"] == input_hash for found in verdicts):
            return
        append_judgment(connection, task=LEDGER_TASK, left_kind="interactive_figure", left_id=figure_id,
                        judge="verifier", input_hash=input_hash, verdict=outcome, rationale=rationale[:400],
                        supersedes_id=verdicts[-1]["id"] if verdicts else None, created_at=utc_now_iso(None))


def sketch_rechecked(row: Mapping[str, Any], repository: Repository | None = None) -> Mapping[str, Any]:
    """Spec §8.5, engine upgrades: a shown sketch verified under another
    engine, or (Codex review F11, round 3) by another verifier version
    (:data:`.sketch_verify.VERIFIER_REPORT_VERSION`: a report made before a
    verification fix may carry a check line the fixed verifier would not
    give), is verified again by code (no model call) before it is shown. One
    that passes shows with this engine's and verifier's check lines; one that
    fails shows "couldn't run under this version · rebuild", never as
    checked. Remembered per (figure, engine, verifier) in this process (a row
    is never rewritten); with a ``repository`` the verdict is appended to
    ``judgment_ledger`` first (Codex review F8,
    :func:`_record_reverification`)."""

    from learnloop.figures import sketch_verify as SV
    from learnloop.figures.sketch_engine import ENGINE_SHA256

    if not sketch_row(row) or row.get("verification") not in store.SHOWN or not row.get("spec_json"):
        return row
    if row.get("engine_sha256") == ENGINE_SHA256 and _stored_verifier(row) == SV.VERIFIER_REPORT_VERSION:
        return row
    key = (str(row["id"]), ENGINE_SHA256, SV.VERIFIER_REPORT_VERSION)
    with _RECHECKED_GUARD:
        cached = _RECHECKED.get(key)
    if cached is None:
        try:
            compiled = K.parse_sketch(row["spec_json"])
            report = SV.verify_sketch(compiled)
            cached = {"outcome": report.outcome, "report": report.as_dict()}
        except Exception as exc:  # noqa: BLE001 - a program that no longer parses or runs fails closed
            cached = {"outcome": V.FAILED, "report": {"reason": f"{type(exc).__name__}", "tier": "sketch"}}
        _record_reverification(repository, row, cached, ENGINE_SHA256)
        with _RECHECKED_GUARD:
            _RECHECKED[key] = cached
    previous = dict(row.get("verification_report") or {})
    if cached["outcome"] != V.ILLUSTRATIVE:
        return {**row, "verification": V.FAILED, "spec_json": None,
                "verification_report": {**previous, "reason": ENGINE_CHANGED_REASON, "engine_changed": True}}
    # The stored report (its quote checks and assumptions, verified against the
    # passages at build time) with this engine's run and check lines over it.
    fresh = cached["report"]
    report = {**previous, **{key: fresh.get(key) for key in (
        "outcome", "checks", "not_covered", "unnamed_elements", "settings", "grid_points", "samples",
        "dropped_predictions", "engine_sha256", "verifier_version", "read_steps", "tested")}}
    return {**row, "verification_report": report, "checks": report.get("checks") or [],
            "engine_sha256": ENGINE_SHA256}


def worded_row(row: Mapping[str, Any]) -> Mapping[str, Any]:
    """Spec §9b.4 when a stored figure is presented (Reader follow-ups Nov 1b,
    Codex review F3): a figure stored before the free-text label rule (or by
    any path that skipped it) is shown, listed and reused without its
    label-like text, as :mod:`.labels` rules for an answer that still
    violates after its repair call: what it shows emptied, a label-like
    assumption (in the spec and in the stored report) dropped, and a Manim
    figure's label-like title left out and each label-like transcript line
    replaced in code's words. The stored row (the paid output) is never
    rewritten. Unchanged (the same object) when nothing reads like a label."""

    if row.get("verification") not in store.SHOWN or not row.get("spec_json"):
        return row
    raw = row["spec_json"]
    spec_json = L.strip_json(raw)
    if rich_row(row):
        try:
            program = json.loads(spec_json) if isinstance(spec_json, str) else None
        except ValueError:
            program = None
        if isinstance(program, dict):
            title, narration = program.get("title"), program.get("narration_md")
            worded = {"title": "" if L.label_like(title) is not None else title,
                      "narration_md": L.strip_lines(narration) if narration else narration}
            if worded != {"title": title, "narration_md": narration}:
                spec_json = json.dumps({**program, **worded}, ensure_ascii=False)
    report = row.get("verification_report") or {}
    assumptions = report.get("assumptions")
    kept = [item for item in assumptions if L.label_like(item.get("text") if isinstance(item, Mapping) else item)
            is None] if isinstance(assumptions, list) else assumptions
    if spec_json is raw and kept == assumptions:
        return row
    return {**row, "spec_json": spec_json, "verification_report": {**report, "assumptions": kept}}


def drawable_now(vault: Any, row: Mapping[str, Any]) -> bool:
    """A stored figure that can be drawn as configured now (RW5b's panels and
    RW5d P2's sketch tier both on when it needs them)."""

    return advanced_off_row(vault, row) is row and sketch_off_row(vault, row) is row and rich_off_row(vault, row) is row


def property_checks(report: Mapping[str, Any]) -> list[str]:
    """The closed keys of the checks a shown figure passed (§8.3 steps 1-2)."""

    held = {str(entry.get("kind")) for entry in report.get("invariants") or () if entry.get("holds")}
    passed = {"values_finite"} | held
    if report.get("shades"):
        passed.add("shaded_areas")
    return [key for key in PROPERTY_CHECKS if key in passed]


# ---------------------------------------------------------------------------
# The view
# ---------------------------------------------------------------------------

def _label(row: Mapping[str, Any]) -> str:
    verification = row["verification"]
    if verification == "illustrative" and rich_row(row):
        if row.get("grounding") == "none":
            return RICH.MANIM_NOT_FROM_BOOKS_LABEL
        report = row.get("verification_report") or {}
        return RICH.MANIM_LABEL if report.get("checks") else RICH.MANIM_UNCHECKED_LABEL
    if verification == "unsupported" and (row.get("verification_report") or {}).get("rich_off"):
        return RICH.RICH_OFF_LABEL
    if verification == "illustrative" and sketch_row(row):
        if row.get("grounding") == "none":
            return SKETCH_NOT_FROM_BOOKS_LABEL
        report = row.get("verification_report") or {}
        return SKETCH_LABEL if report.get("checks") else SKETCH_UNCHECKED_LABEL
    if verification == "failed" and (row.get("verification_report") or {}).get("engine_changed"):
        return ENGINE_CHANGED_REASON
    if verification == "illustrative" and row.get("grounding") == "none":
        return NOT_FROM_BOOKS_LABEL
    if verification in LABELS:
        return LABELS[verification]
    reason = str((row.get("verification_report") or {}).get("reason") or "")
    if verification == "unsupported":
        kind = row.get("unsupported_kind") or "something the figure language can't express"
        return f"can't draw this yet — needs {kind} · noted"
    return f"couldn't build a reliable version of this ({reason or 'its checks did not pass'})"


def _prediction_view(found: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if found is None:
        return None
    observed = found.get("observed") or {}
    return {"prediction_id": found["id"], "figure_id": found.get("figure_id"),
            "extraction_id": found.get("extraction_id"), "prediction_index": found.get("prediction_index"),
            "learner_answer": found["learner_answer"], "matched": found["matched"],
            "before": observed.get("before"), "after": observed.get("after"), "answer": observed.get("answer"),
            "explanation_text": found.get("explanation_text")}


def _anchor_span(row: Mapping[str, Any], asked: Mapping[str, Any] | None,
                 home: Mapping[str, Any] | None) -> str | None:
    """Where a figure shows: under the selection's last block; a region's
    figure (no selected text) under the region's block (Codex review F2);
    RW5d: a figure with no passage under the passage the learner was reading
    (``home``, else its own request's reading position)."""

    region = row.get("region") or {}
    home = home or (asked or {}).get("reading_at") or {}
    return (list(row.get("span_ids") or ()) or [region.get("span_id") or home.get("span_id")])[-1]


def figure_view(vault: Any, repository: Repository, row: Mapping[str, Any], *, versions: int = 1,
                home: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """A figure as the Reader shows it. The spec goes out as JSON text (its
    keys are the spec's own), and only for a shown figure. A prediction's
    answer is never sent before the learner answers it. A stored "verified"
    shows as an illustration (:func:`shown_row`).

    ``home`` (RW5d, Codex review F3): where a figure with no passage lands in
    this view (the request delivering it, or one placement in a listing);
    unset, its own request's reading position."""

    row = _presented_row(vault, repository, row)
    asked = _figure_request(repository, row)
    view: dict[str, Any] = {
        "figure_id": row["id"], "extraction_id": row["extraction_id"], "span_ids": list(row.get("span_ids") or ()),
        "anchor_span_id": _anchor_span(row, asked, home),
        "region": row.get("region"),
        "origin": row["origin"], "verification": row["verification"], "kind": row.get("kind"),
        "label": _label(row), "reason": (row.get("verification_report") or {}).get("reason") or None,
        "unsupported_kind": row.get("unsupported_kind"), "supersedes_id": row.get("supersedes_id"),
        "revision_note": row.get("revision_note"), "versions": versions, "created_at": row["created_at"],
        "spec_json": None, "demonstrates": None, "assumptions": [], "predictions": [], "property_checks": [],
    }
    if show_me_enabled(vault):
        # RW5d (absent while show me is off, so the view is RW5a/b's key for key):
        # the goal in its author's voice, the grounding and the cited passages.
        manifest = (asked or {}).get("grounding_manifest") or {}
        view.update({
            "goal_text": row.get("goal_text"), "goal_author": (asked or {}).get("goal_author"),
            "grounding": row.get("grounding") or "anchor",
            "passages": [dict(item) for item in manifest.get("passages") or ()]
            if (row.get("grounding") or "anchor") == "retrieved" else [],
        })
    if sketch_ready(vault):
        # RW5d P2 (absent while the tier is off, so the view is P1's key for key).
        view["tier"] = "sketch" if sketch_row(row) else "grammar"
        view["sketch"] = None
    if rich_tiers_enabled(vault):
        # RW5d P2b (absent while the rich tiers are off, so the view is P2's key
        # for key): the tier, a Manim figure's video and checks, and on a quick
        # figure the state of its fuller version (one figure line, two versions).
        view["tier"] = "manim" if rich_row(row) else ("sketch" if sketch_row(row) else "grammar")
        view["manim"] = None
        view["fuller"] = None if rich_row(row) else fuller_state(vault, repository, row)
    if (row.get("verification_report") or {}).get("source_check_rejected"):
        # RW5c (§6.6): the frame's failed state, with *rebuild* while revisions are on.
        view["elements"] = []
        view["source_check"] = {"status": "differs", "certification_version": SC.CERTIFICATION_VERSION,
                                "reasons": ["differs"], "recheck_due": False, "rebuild": revisions_enabled(vault)}
    if row["verification"] not in store.SHOWN or not row.get("spec_json"):
        return view
    if rich_row(row):
        return _manim_view(row, view)
    if sketch_row(row):
        return _sketch_view(vault, repository, row, view)
    compiled = S.parse_spec(row["spec_json"])
    report = row.get("verification_report") or {}
    view["spec_json"] = row["spec_json"]
    view["property_checks"] = property_checks(report)
    view["demonstrates"] = compiled.spec.demonstrates
    view["assumptions"] = report.get("assumptions") or [
        {"text": item.text, "span_id": None, "quote": None} for item in compiled.spec.assumptions]
    dropped = set(report.get("dropped_predictions") or ())
    answered: dict[int, dict[str, Any]] = {}
    if predictions_enabled(vault):
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            answered = {found["prediction_index"]: found
                        for found in store.predictions_for_figure(connection, str(row["id"]))}
        for index, (prediction, _node) in enumerate(compiled.predictions):
            if index in dropped:
                continue
            outcome = S.prediction_outcome(compiled, index)
            choices = ([{"value": value, "label": S.DIRECTION_LABELS[value]} for value in S.DIRECTIONS]
                       if prediction.observe.kind == "direction"
                       else [{"value": label, "label": label} for label in outcome["choices"]])
            view["predictions"].append({
                # The change itself is in spec_json (parameter names are the
                # spec's own keys, which the wire's camel-casing would rename).
                "index": index, "prompt": prediction.prompt, "kind": prediction.observe.kind, "choices": choices,
                "answered": _prediction_view(answered.get(index)),
            })
    _source_check_view(vault, repository, row, compiled, view)
    return view


def _sketch_view(vault: Any, repository: Repository, row: Mapping[str, Any], view: dict[str, Any]) -> dict[str, Any]:
    """A shown sketch as the Reader draws it: the program (its code runs in
    the desktop's sealed engine), the code-owned check lines and the *not
    covered* line, and its predictions (answers never sent first)."""

    from learnloop.figures import sketch_verify as SV
    from learnloop.figures.sketch_engine import ENGINE_SHA256

    compiled = K.parse_sketch(row["spec_json"])
    report = row.get("verification_report") or {}
    program = compiled.program
    view["spec_json"] = row["spec_json"]
    view["demonstrates"] = program.demonstrates
    view["assumptions"] = report.get("assumptions") or [
        {"text": item.text, "span_id": None, "quote": None} for item in program.assumptions]
    view["sketch"] = {
        "engine_sha256": ENGINE_SHA256, "seed": SV.VERIFY_SEED,
        "checks": [dict(check) for check in report.get("checks") or ()],
        "not_covered": list(report.get("not_covered") or ()),
        "unnamed_elements": int(report.get("unnamed_elements") or 0),
        "settings": int(report.get("settings") or 0),
        # Fix round 4 (the independent sandbox review): the read schedule every
        # run follows and the digest of every read verification checked, per
        # grid point (values in declared order, so no name is camelized); the
        # desktop compares its own and withdraws the checks on a difference.
        "read_steps": [int(step) for step in report.get("read_steps") or ()],
        "tested": [{"values": [float(v) for v in entry.get("values") or ()],
                    "steps": [int(s) for s in entry.get("steps") or ()],
                    "digests": [str(d) for d in entry.get("digests") or ()]}
                   for entry in report.get("tested") or ()],
    }
    dropped = set(report.get("dropped_predictions") or ())
    if predictions_enabled(vault):
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            answered = {found["prediction_index"]: found
                        for found in store.predictions_for_figure(connection, str(row["id"]))}
        for index, prediction in enumerate(program.predictions):
            if index in dropped:
                continue
            kind = prediction.observe.kind
            choices = ([{"value": value, "label": S.DIRECTION_LABELS[value]} for value in S.DIRECTIONS]
                       if kind == "direction" else
                       [{"value": label, "label": label} for label in prediction.observe.choices])
            # target_step (Codex review F5): the clock step the answer is
            # graded at, so the desktop's playback stops exactly there.
            view["predictions"].append({"index": index, "prompt": prediction.prompt, "kind": kind,
                                        "choices": choices, "answered": _prediction_view(answered.get(index)),
                                        "target_step": SV.prediction_target_step(compiled, index)})
    return view


def _manim_view(row: Mapping[str, Any], view: dict[str, Any]) -> dict[str, Any]:
    """A shown Manim figure (RW5d P2b, spec §6.8): the content-addressed video
    (played over ``llmedia://``), its title and transcript, the code-owned
    check lines and *the video itself is not checked frame by frame*. The
    scene code never goes out."""

    report = row.get("verification_report") or {}
    try:
        program = json.loads(row["spec_json"])
    except (TypeError, ValueError):
        program = {}
    view["demonstrates"] = program.get("demonstrates") or None
    view["assumptions"] = report.get("assumptions") or []
    view["manim"] = {
        "media_file_name": row.get("media_file_name"),
        "title": program.get("title") or "",
        "narration_md": program.get("narration_md") or "",
        "duration_seconds": report.get("duration_seconds"),
        "checks": [dict(check) for check in report.get("checks") or ()],
        "not_checkable": [dict(entry) for entry in report.get("not_checkable") or ()],
        "not_covered": list(report.get("not_covered") or (RICH.MANIM_NOT_COVERED,)),
    }
    return view


def source_rejected(vault: Any, repository: Repository, row: Mapping[str, Any]) -> bool:
    """RW5c (§6.6): the figure's newest check, at the current certification
    version and with the switch on, proved a stated claim different. Nothing
    reads the ledger with the switch off (G23g)."""

    if not SC.enabled(vault) or not SC.grammar_row(row) or row.get("verification") not in store.SHOWN:
        return False
    found = SC.current_row(repository, str(row["id"]))
    return found is not None and found["outcome"] == SC.DIFFERS


def _source_rejected_row(vault: Any, repository: Repository, row: Mapping[str, Any]) -> Mapping[str, Any]:
    if not source_rejected(vault, repository, row):
        return row
    report = dict(row.get("verification_report") or {})
    return {**row, "verification": V.FAILED, "spec_json": None,
            "verification_report": {**report, "reason": SC.REJECTED_REASON, "source_check_rejected": True}}


def _source_check_view(vault: Any, repository: Repository, row: Mapping[str, Any], compiled: S.CompiledFigure,
                       view: dict[str, Any]) -> None:
    """RW5c (§7.4): a shown grammar figure's ``elements`` and ``source_check``,
    read from the ledger as the switch is now (absent with it off: the view is
    RW5a/RW5d's key for key). With a ``book`` element every label in the spec
    goes out as its element id (option B); with none the figure is drawn exactly
    as before, with the closed reasons for the frame."""

    if not SC.enabled(vault) or not SC.grammar_row(row):
        return
    found = SC.current_row(repository, str(row["id"]))
    reasons = [key for key in (found.get("reasons") or {}) if key in SC.REASONS] if found else []
    view["elements"] = []
    view["source_check"] = {"status": "none", "certification_version": SC.CERTIFICATION_VERSION, "reasons": reasons,
                            "recheck_due": SC.recheck_due(found), "rebuild": False}
    if found is None or not any(element.get("role") == "book" for element in found.get("elements") or ()):
        return
    view["spec_json"], by_label = E.rewrite_spec(row["spec_json"], compiled)
    view["elements"] = found["elements"]
    view["source_check"]["status"] = "checked"
    plain = {str(element["id"]): str(element.get("plain") or "") for element in found["elements"]}
    for prediction in view["predictions"]:
        if prediction.get("kind") != "area":
            continue
        prediction["choices"] = [{"value": by_label.get(choice["value"], ""),
                                  "label": plain.get(by_label.get(choice["value"], ""), "")}
                                 for choice in prediction["choices"]]
        if prediction.get("answered"):
            prediction["answered"] = _coded_answer(prediction["answered"], by_label)


def _coded_answer(answered: Mapping[str, Any], by_label: Mapping[str, str]) -> dict[str, Any]:
    """An answered area prediction under code-owned labels: its stored answers
    (shade labels, kept as they were) go out as the shades' element ids."""

    return {**answered, "learner_answer": by_label.get(str(answered.get("learner_answer")), ""),
            "answer": by_label.get(str(answered.get("answer")), "")}


def _code_owned_labels(vault: Any, repository: Repository, row: Mapping[str, Any],
                       compiled: S.CompiledFigure) -> dict[str, str] | None:
    """Model label -> element id while this figure's labels are code-owned, else None."""

    if not SC.enabled(vault) or not SC.grammar_row(row):
        return None
    found = SC.current_row(repository, str(row["id"]))
    if found is None or not any(element.get("role") == "book" for element in found.get("elements") or ()):
        return None
    return E.rewrite_spec(row["spec_json"], compiled)[1]


def _presented_row(vault: Any, repository: Repository, row: Mapping[str, Any]) -> dict[str, Any]:
    """A stored row as :func:`figure_view` presents it under the switches now."""

    row = rich_off_row(vault, sketch_off_row(vault, advanced_off_row(vault, shown_row(row))))
    if sketch_ready(vault):
        row = sketch_rechecked(row, repository)
    # RW5c: a stated claim proved different is not shown (§6.6, Q4); the row
    # keeps steps 1-2's result, and this state comes from the ledger.
    row = _source_rejected_row(vault, repository, row)
    # After the re-verification (it reads the stored program): the free-text
    # label rule as presented (spec §9b.4, Codex review F3, Nov 1b).
    return worded_row(row)


def redelivered_view(vault: Any, repository: Repository, view: Mapping[str, Any]) -> dict[str, Any]:
    """A figure view kept since its build (a finished job's result, read
    again through ``reader.figure_job``) as it may go out now (follow-ups
    Nov 2): its fuller version is rebuilt from the current rows
    (:func:`fuller_state`), so a fuller version whose learner inputs became
    protected since, or that was stored since, is presented as it is now.
    The caller has already rechecked the figure itself
    (:func:`figure_withheld`). A view with no fuller line (the rich tiers off,
    or a rich figure) is returned as it is."""

    if ("fuller" not in view and "source_check" not in view and not SC.enabled(vault)) or not view.get("figure_id"):
        return dict(view)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = store.figure(connection, str(view["figure_id"])) if store.has_tables(connection) else None
    if row is None:
        return dict(view)
    presented = _presented_row(vault, repository, row)
    fresh = dict(view)
    if "fuller" in view:
        fresh["fuller"] = None if rich_row(presented) else fuller_state(vault, repository, presented)
    if SC.grammar_row(row) and ("source_check" in view or SC.enabled(vault)):
        # RW5c: the labels and the claim as the switch and the ledger are now,
        # never as they were when the build finished (§10.1).
        current = figure_view(vault, repository, row, versions=int(view.get("versions") or 1))
        keep = {key: current[key] for key in ("verification", "label", "reason", "spec_json", "predictions",
                                              "demonstrates", "assumptions", "property_checks") if key in current}
        fresh.update(keep)
        for key in ("elements", "source_check"):
            fresh.pop(key, None)
            if key in current:
                fresh[key] = current[key]
    return fresh


def fuller_state(vault: Any, repository: Repository, row: Mapping[str, Any]) -> dict[str, Any] | None:
    """RW5d P2b (spec §6.8, §8.6): the fuller version of a quick figure, or
    None when it has none: ``ready`` (with the rich figure's view),
    ``failed`` (code's reason; the quick version stays), ``pending`` (the
    job's phase), ``waiting_for_plan`` or ``cancelled``."""

    if row.get("verification") not in store.SHOWN:
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = store.fuller_rows(connection, str(row["id"]))
    # Codex re-review F2: a fuller version whose author's learner state was
    # read from something protected now is not delivered (nor named failed).
    rows = [found for found in rows if learner_state_withheld(vault, repository, found) is None]
    shown = [found for found in rows if found["verification"] in store.SHOWN]
    if shown:
        rich = shown[-1]
        if rich_off_row(vault, rich) is not rich:
            return None
        rich_view = figure_view(vault, repository, rich)
        return {"state": "ready", "figure": rich_view, "tier": "manim", "phase": None, "reason": None,
                "rich_job_id": None}
    job = RICH.rich_job_for_quick(repository, str(row["id"]))
    intent = (row.get("verification_report") or {}).get(RICH_INTENT_KEY)
    build_mode = ((job or {}).get("payload") or {}).get("build_mode") if job is not None \
        else (intent or {}).get("build_mode") if isinstance(intent, dict) else None
    # Landing ruling R1 (final verify F18): a fuller version built ahead of need that nobody
    # pressed for is marked, so the Reader bounds its reads for it by the prefetch lifetime
    # (pressed figures keep their polling). Present only then: every other view is unchanged.
    speculative = {"speculative": True} if build_mode == "prefetch" and not _prebuilt_pressed(repository, row) \
        else {}
    if job is not None:
        state = RICH.job_state(job)
        if state["state"] != "done":
            return {"tier": "manim", "figure": None, "phase": state.get("phase"), "reason": state.get("reason"),
                    **state, **speculative}
    if rows:
        failed = rows[-1]
        return {"state": "failed", "tier": "manim", "figure": None, "phase": None, "rich_job_id": None,
                "reason": str((failed.get("verification_report") or {}).get("reason") or "")[:300] or None}
    if job is None and isinstance(intent, dict):
        # Codex review F8: the intent committed but no job was started (the
        # sidecar stopped first, or the enqueue failed): reading this source
        # starts it (resume_rich_intents); until then the line says so.
        if build_mode == "prefetch" and _prefetch_intent_refused(vault, repository, intent):
            # Landing ruling R1 (final verify F18): a prebuild's intent is started by a read
            # only while background admission holds (resume_rich_intents); refused (battery,
            # the switch off, its passage held out) nothing will start it, so it is not pending.
            return None
        return {"state": "pending", "tier": "manim", "figure": None, "phase": "writing", "reason": None,
                "rich_job_id": None, **speculative}
    return None


def _prefetch_intent_refused(vault: Any, repository: Repository, intent: Mapping[str, Any]) -> bool:
    """Landing ruling R1: whether background admission refuses a prebuild's unqueued rich
    intent now: figures ahead of need off, this machine not on mains, or its input held out.
    (Foreground work only delays it, so it is not a refusal.)"""

    from learnloop.figures.power import power_state, prefetch_switch
    from learnloop.figures.protection import _withheld

    if not prefetch_switch(vault) or not power_state().on_mains:
        return True
    return _withheld(vault, repository, intent.get("base") or {}) is not None


def _figure_request(repository: Repository, row: Mapping[str, Any]) -> dict[str, Any] | None:
    """The ``figure_requests`` row a figure was built for (RW5d), or None (RW5a/b rows before 224)."""

    if not row.get("request_id"):
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.request(connection, str(row["request_id"]))


def _prebuilt_pressed(repository: Repository, row: Mapping[str, Any]) -> bool:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = connection.execute(
            "SELECT 1 FROM figure_requests WHERE figure_id = ? AND build_mode = 'pressed' LIMIT 1",
            (str(row["id"]),)).fetchone()
    return found is not None


__all__ = [
    "ADVANCED_OFF_KIND",
    "ENGINE_CHANGED_REASON",
    "LABELS",
    "LEDGER_TASK",
    "NOT_FROM_BOOKS_LABEL",
    "PROPERTY_CHECKS",
    "RECONSTRUCTION_REASON",
    "REVERIFY_VERSION",
    "SKETCH_LABEL",
    "SKETCH_NOT_FROM_BOOKS_LABEL",
    "SKETCH_OFF_KIND",
    "SKETCH_UNCHECKED_LABEL",
    "advanced_off_row",
    "drawable_now",
    "figure_view",
    "fuller_state",
    "property_checks",
    "redelivered_view",
    "reverify_hash",
    "rich_off_row",
    "rich_row",
    "shown_row",
    "sketch_off_row",
    "sketch_rechecked",
    "sketch_row",
    "source_rejected",
    "worded_row",
]
