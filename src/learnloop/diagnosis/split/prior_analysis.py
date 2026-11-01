"""The diagnoser's prior-analysis arm (learner-blindness relax; owner direction 2026-11-01).

``diagnosis.history_includes_prior_analysis``: whether the history-aware
diagnoser's context re-feeds, for each prior attempt it shows, what
LearnLoop's diagnoser wrote about that attempt then (the latest completed live
diagnosis's ``analysis_md`` written before the diagnosed attempt, bounded) and,
for an earlier workbench attempt, its step trace (``workbench_trace``, the
same rendering the current attempt gets).

Not a fixed preference (no-made-up-constants, 2026-10-24): re-feeding a
model's own earlier reading can anchor it, or can let it build on it. The
default ``randomized`` assigns each diagnosed attempt to one arm by a seeded
equipoise draw (:func:`assign`: a hash of the attempt id under
:data:`DESIGN`, so a retry or a replay lands in the same arm) and records the
arm, its assignment and propensity on the diagnosis's context receipt next to
the context hash (an earlier analysis shown folds its own input record into
the diagnosis's; an earlier workbench trace shown counts its item as a
solution read and leaves the record incomplete, :data:`TRACE_UNRECORDED`); ``learnloop diagnose m2-report`` reads E2's
``anchoring_suspect`` rate per arm (``reports._e2_prior_analysis_arms``).
``on`` / ``off`` fix the arm (``assignment: config``).

The arm changes the diagnoser's context only: the blind grader never reads
any of it (``attempts`` imports nothing here), a diagnosis is still never
evidence, and the ``off`` arm's context, prompt and hash are today's byte for
byte. Read-only; nothing is written and no model is called.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from typing import Any

ARM_ON = "with_prior_analysis"
ARM_OFF = "without_prior_analysis"
#: The design's identity: part of the seeded draw, so a new design re-draws.
DESIGN = "prior-analysis-arm-v1"
#: ``keep``: a two-arm equipoise design (each arm equally likely), a
#: structural property of the experiment, never a tuned preference.
EQUIPOISE = 0.5
#: The diagnoser prompt version's suffix in the ``on`` arm.
SUFFIX = "+prior-analysis-v1"
#: ``keep``: a prompt-size bound on each earlier analysis (never a judgement).
ANALYSIS_CHARS = 1_500
#: Why a diagnosis's input record is incomplete when it showed an earlier
#: workbench trace: its assists record no write-time provenance (Codex review F3).
TRACE_UNRECORDED = "an earlier workbench trace's assists record no write-time provenance"
NOTE = (
    "A prior attempt may carry `earlier_diagnosis`: what LearnLoop's diagnoser wrote about it at the time "
    "(possibly wrong, and written with less history than you have), and an earlier workbench attempt its "
    "`workbench_trace` (the assists it was shown, help never evidence). Test them against the attempts and "
    "the current answer; never repeat an earlier reading because it was written."
)


@dataclass(frozen=True)
class Arm:
    """One diagnosis's arm and how it was assigned (recorded on its receipt)."""

    arm: str
    assignment: str
    propensity: float
    draw: float | None = None

    @property
    def on(self) -> bool:
        return self.arm == ARM_ON

    def receipt(self) -> dict[str, Any]:
        out: dict[str, Any] = {"arm": self.arm, "assignment": self.assignment, "design": DESIGN,
                               "propensity": self.propensity}
        if self.draw is not None:
            out["draw"] = round(self.draw, 6)
        return out


def configured(vault: Any) -> str:
    section = getattr(getattr(vault, "config", None), "diagnosis", None)
    value = str(getattr(section, "history_includes_prior_analysis", "randomized") or "randomized")
    return value if value in ("randomized", "on", "off") else "randomized"


def assign(setting: str, attempt_id: str) -> Arm:
    """The arm of one diagnosed attempt under ``setting``."""

    if setting == "on":
        return Arm(ARM_ON, "config", 1.0)
    if setting == "off":
        return Arm(ARM_OFF, "config", 0.0)
    digest = hashlib.sha256(f"{DESIGN}:{attempt_id}".encode("utf-8")).hexdigest()
    draw = int(digest[:12], 16) / float(16 ** 12)
    return Arm(ARM_ON if draw < EQUIPOISE else ARM_OFF, "randomized", EQUIPOISE, draw)


#: ``(prior attempt ids, cutoff instant) -> {attempt id: {"earlier_diagnosis": {...}, "workbench_trace": {...}}}``.
PriorReader = Callable[[Sequence[str], str], Mapping[str, Mapping[str, Any]]]


@dataclass(frozen=True)
class PriorAnalysis:
    """What :func:`learnloop.diagnosis.split.context.assemble_diagnosis_context` is handed."""

    arm: Arm
    read: PriorReader


def _excerpt(text: str, limit: int = ANALYSIS_CHARS) -> str:
    value = str(text or "").strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def repository_reader(vault: Any, repository: Any) -> PriorReader:
    """The reader over the vault's ledger: per prior attempt, its latest
    completed live diagnosis written strictly before the cutoff (its
    ``analysis_md``, bounded, and the diagnosis id the provenance records)
    and, for a workbench attempt, its step trace with the symbolic switch
    read now (as the current attempt's is)."""

    def read(attempt_ids: Sequence[str], before: str) -> dict[str, dict[str, Any]]:
        from learnloop.db.connection import connect
        from learnloop.diagnosis.split.workbench_trace import WORKBENCH_SURFACES, trace_for_attempt
        from learnloop.symbolic_view import switch_now

        ids = sorted({str(value) for value in attempt_ids if value})
        out: dict[str, dict[str, Any]] = {}
        if not ids:
            return out
        marks = ",".join("?" for _ in ids)
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            diagnoses = connection.execute(
                f"SELECT id, attempt_id, proposal_json, created_at FROM attempt_diagnoses WHERE attempt_id IN ({marks}) "
                "AND mode = 'live' AND status = 'completed' AND created_at < ? ORDER BY created_at DESC, id DESC",
                (*ids, before),
            ).fetchall()
            attempts = [dict(row) for row in connection.execute(
                f"SELECT id, entry_surface, submission_id FROM practice_attempts WHERE id IN ({marks})", tuple(ids))]
        for row in diagnoses:
            attempt_id = str(row["attempt_id"])
            if "earlier_diagnosis" in out.get(attempt_id, {}):
                continue
            try:
                proposal = json.loads(row["proposal_json"]) if row["proposal_json"] else {}
            except (TypeError, ValueError):
                proposal = {}
            analysis = str((proposal or {}).get("analysis_md") or "").strip()
            if not analysis:
                continue
            out.setdefault(attempt_id, {})["earlier_diagnosis"] = {
                "diagnosis_id": str(row["id"]), "written": str(row["created_at"] or "")[:10],
                "analysis_md": _excerpt(analysis), "full_text": analysis,
            }
        symbolic = switch_now(vault)
        for attempt in attempts:
            if str(attempt.get("entry_surface") or "") not in WORKBENCH_SURFACES:
                continue
            trace = trace_for_attempt(repository, attempt, symbolic_enabled=symbolic)
            if trace:
                out.setdefault(str(attempt["id"]), {})["workbench_trace"] = trace
        return out

    return read


def for_attempt(vault: Any, repository: Any, attempt_id: str) -> PriorAnalysis:
    """The live diagnosis's prior-analysis input: its arm and the ledger reader."""

    return PriorAnalysis(arm=assign(configured(vault), attempt_id), read=repository_reader(vault, repository))


__all__ = [
    "ANALYSIS_CHARS",
    "ARM_OFF",
    "ARM_ON",
    "Arm",
    "DESIGN",
    "EQUIPOISE",
    "NOTE",
    "PriorAnalysis",
    "PriorReader",
    "SUFFIX",
    "TRACE_UNRECORDED",
    "assign",
    "configured",
    "for_attempt",
    "repository_reader",
]
