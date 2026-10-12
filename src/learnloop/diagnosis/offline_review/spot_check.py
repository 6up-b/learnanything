"""The optional owner spot-check (Slice 1 §12.1 "What the spot-check screens show").

About ten stratified items, under fifteen minutes, three screens per item:

1. **Diagnoses** - the item, the answer and up to five explanations with labels
   hidden and order shuffled; one tap each (right / partly / wrong / not sure)
   and an optional best pick, including "none".
2. **Pattern links** - each "same mistake as [earlier answer]" claim from any
   arm, both answers side by side: same mistake / different / not sure. A link
   several arms proposed is shown once and credited to each.
3. **Grade disagreements** - where the blind grade differs from the stored
   joint grade: the blind grade is right / the stored grade is right / not sure.

Every screen can be skipped and a session resumes where it stopped. Verdicts
on (b)-(e), on links and on grades stay in the scratch copy's
``review_judgments``. Verdicts on arm (a) - the stored joint diagnosis, a real
receipt - are genuine owner adjudications and are ALSO appended to the vault's
``diagnosis_adjudications`` (``adjudicator_source='human_owner'``,
``queue_reason='sampled'``), exactly as ``learnloop diagnosis adjudicate``
would record them.
"""

from __future__ import annotations

import json
import random
from contextlib import closing
from pathlib import Path
from typing import Any, Mapping, Sequence

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.diagnosis_review import (
    insert_review_row,
    review_rows,
    update_spot_check_session,
)
from learnloop.diagnosis.diagnosis_adjudication import (
    append_diagnosis_adjudication,
    diagnosis_snapshot,
)
from learnloop.diagnosis.offline_review.judge import judge_view
from learnloop.diagnosis.offline_review.runner import MAIN_ARMS, RUN_FILE, SCRATCH_FILE
from learnloop.diagnosis.split.history import VaultHistoryStore
from learnloop.vault.models import LoadedVault

SPOT_CHECK_VERSION = "spot-check-v1"
MAX_ITEMS = 10
MAX_PLANTED = 2
DIAGNOSIS_TAPS = ("right", "partly", "wrong", "not_sure")
LINK_TAPS = ("same", "different", "not_sure")
GRADE_TAPS = ("blind_right", "stored_right", "not_sure")


def _run_id(run_dir: Path) -> str:
    return str(json.loads((Path(run_dir) / RUN_FILE).read_text(encoding="utf-8"))["run_id"])


def _scratch(run_dir: Path) -> Path:
    return Path(run_dir) / SCRATCH_FILE


def _rows(run_dir: Path, table: str, *, order_by: str = "rowid", **where: Any) -> list[dict[str, Any]]:
    with closing(connect(_scratch(run_dir), read_only=True)) as connection:
        return review_rows(connection, table, where={"run_id": _run_id(run_dir), **where}, order_by=order_by)


def _answer(run_dir: Path, target: Mapping[str, Any], planted: Mapping[str, Any]) -> str:
    if target["kind"] == "planted":
        case = planted.get(target["attempt_id"]) or {}
        return str(((case.get("history") or {}).get("target") or {}).get("learner_answer_md") or "")
    with closing(connect(_scratch(run_dir), read_only=True)) as connection:
        row = connection.execute("SELECT learner_answer_md FROM practice_attempts WHERE id = ?", (target["attempt_id"],)).fetchone()
    return str(row[0] or "") if row else ""


def build_spot_check_plan(
    run_dir: Path,
    vault: LoadedVault,
    *,
    seed: int,
    max_items: int = MAX_ITEMS,
) -> list[dict[str, Any]]:
    """The ordered screens for up to ``max_items`` stratified items (seeded)."""

    rng = random.Random(seed)
    targets = _rows(run_dir, "review_targets", order_by="position")
    planted = {row["target_attempt_id"]: row for row in _rows(run_dir, "review_planted_cases")}
    diagnoses: dict[str, list[dict[str, Any]]] = {}
    for row in _rows(run_dir, "review_diagnoses"):
        if row["arm"] in MAIN_ARMS and row["status"] == "completed" and row.get("proposal"):
            diagnoses.setdefault(row["target_id"], []).append(row)
    grades = {
        row["attempt_id"]: row.get("record")
        for row in _rows(run_dir, "review_blind_grades", purpose="primary", status="completed")
    }
    with closing(connect(_scratch(run_dir), read_only=True)) as connection:
        stored_scores = {
            str(row[0]): row[1]
            for row in connection.execute("SELECT id, rubric_score FROM practice_attempts")
        }
    # Stratify: one item per learning object first, at most MAX_PLANTED planted.
    chosen: list[dict[str, Any]] = []
    seen_lo: set[str] = set()
    planted_count = 0
    candidates = [target for target in targets if len(diagnoses.get(target["id"], [])) >= 2]
    for pass_index in (0, 1):
        for target in candidates:
            if len(chosen) >= max_items:
                break
            if target in chosen:
                continue
            if target["kind"] == "planted" and planted_count >= MAX_PLANTED:
                continue
            if pass_index == 0 and target["learning_object_id"] in seen_lo:
                continue
            chosen.append(target)
            seen_lo.add(target["learning_object_id"])
            planted_count += 1 if target["kind"] == "planted" else 0
    store = None
    screens: list[dict[str, Any]] = []
    for target in chosen:
        item = vault.practice_items.get(target["practice_item_id"])
        answer = _answer(run_dir, target, planted)
        prompt = item.prompt if item is not None else ""
        options = list(diagnoses.get(target["id"], []))[:5]
        rng.shuffle(options)
        screens.append(
            {
                "kind": "diagnoses",
                "target_id": target["id"],
                "attempt_id": target["attempt_id"],
                "item_prompt": prompt,
                "learner_answer_md": answer,
                "options": [
                    {"label": f"Explanation {chr(ord('A') + index)}", "diagnosis_id": row["id"], "view": judge_view(row["proposal"])}
                    for index, row in enumerate(options)
                ],
            }
        )
        links: dict[str, set[str]] = {}
        for row in diagnoses.get(target["id"], []):
            for claim in (row.get("proposal") or {}).get("pattern_claims") or []:
                if claim.get("relation") == "disconfirming":
                    continue
                for citation in claim.get("cited") or []:
                    links.setdefault(str(citation.get("attempt_id")), set()).add(row["id"])
        if links:
            entries = []
            planted_case = planted.get(target["attempt_id"])
            history = {
                row["attempt_id"]: row
                for row in ((planted_case or {}).get("history") or {}).get("history") or []
            }
            for cited in sorted(links):
                if cited in history:
                    earlier = history[cited]
                    earlier_item = vault.practice_items.get(earlier["practice_item_id"])
                    earlier_answer = earlier["learner_answer_md"]
                else:
                    if store is None:
                        store = VaultHistoryStore(vault, Repository.attach(_scratch(run_dir), read_only=True))
                    attempt = store.attempt(cited)
                    if attempt is None:
                        continue
                    earlier_item = vault.practice_items.get(attempt.practice_item_id)
                    earlier_answer = attempt.learner_answer_md
                entries.append(
                    {
                        "cited_attempt_id": cited,
                        "earlier_item_prompt": earlier_item.prompt if earlier_item is not None else "",
                        "earlier_answer_md": earlier_answer,
                        "credited_diagnosis_ids": sorted(links[cited]),
                    }
                )
            rng.shuffle(entries)
            if entries:
                screens.append(
                    {
                        "kind": "links",
                        "target_id": target["id"],
                        "attempt_id": target["attempt_id"],
                        "item_prompt": prompt,
                        "learner_answer_md": answer,
                        "links": entries,
                    }
                )
        record = grades.get(target["attempt_id"])
        stored = stored_scores.get(target["attempt_id"])
        if target["kind"] == "real" and record and stored is not None and float(record.get("rubric_score") or 0) != float(stored):
            grade_options = [("blind", record.get("rubric_score")), ("stored", stored)]
            rng.shuffle(grade_options)
            screens.append(
                {
                    "kind": "grade",
                    "target_id": target["id"],
                    "attempt_id": target["attempt_id"],
                    "item_prompt": prompt,
                    "learner_answer_md": answer,
                    "max_points": record.get("max_points"),
                    "grades": [{"label": f"Grade {index + 1}", "source": source, "score": score} for index, (source, score) in enumerate(grade_options)],
                }
            )
    return screens


def render_screen(screen: Mapping[str, Any]) -> str:
    """Terminal text for one screen. Arms, modes, models and ids never appear."""

    lines = ["Item:", str(screen.get("item_prompt") or "").strip(), "", "Your answer:", str(screen.get("learner_answer_md") or "").strip(), ""]
    if screen["kind"] == "diagnoses":
        lines.append("Which of these explains what went wrong? Tap each: right / partly / wrong / not sure.")
        for option in screen["options"]:
            view = option["view"]
            lines += ["", f"--- {option['label']} ---", str(view.get("explanation") or "").strip()]
            for event in view.get("causes") or []:
                for cause in event.get("candidate_causes") or []:
                    if cause.get("statement"):
                        lines.append(f"  - possible cause: {cause['statement']}")
                if event.get("misconception_statement"):
                    lines.append(f"  - belief: {event['misconception_statement']}")
            for repair in view.get("repairs") or []:
                if repair.get("eliciting_question"):
                    lines.append(f"  - question to try: {repair['eliciting_question']}")
    elif screen["kind"] == "links":
        lines.append("Each earlier answer below was called \"the same mistake\". Same / different / not sure?")
        for index, link in enumerate(screen["links"]):
            lines += ["", f"--- Earlier answer {index + 1} ---", f"Item: {str(link['earlier_item_prompt']).strip()}", str(link["earlier_answer_md"]).strip()]
    elif screen["kind"] == "grade":
        lines.append("Two graders disagree. Which grade is right?")
        for grade in screen["grades"]:
            lines.append(f"- {grade['label']}: {grade['score']} / {screen.get('max_points')}")
    return "\n".join(lines)


def start_or_resume_session(run_dir: Path, vault: LoadedVault, *, seed: int, new: bool = False, max_items: int = MAX_ITEMS) -> tuple[str, list[dict[str, Any]], int]:
    """The open session (resumed at its position) or a new one."""

    sessions = _rows(run_dir, "review_spot_check_sessions", order_by="started_at")
    open_sessions = [row for row in sessions if not row.get("finished_at")]
    if open_sessions and not new:
        session = open_sessions[-1]
        return session["id"], list(session.get("plan") or []), int(session.get("position") or 0)
    plan = build_spot_check_plan(run_dir, vault, seed=seed, max_items=max_items)
    with closing(connect(_scratch(run_dir))) as connection, connection:
        session_id = insert_review_row(
            connection,
            "review_spot_check_sessions",
            {"run_id": _run_id(run_dir), "plan_json": plan, "position": 0},
        )
    return session_id, plan, 0


def advance_session(run_dir: Path, session_id: str, position: int, *, finished: bool = False) -> None:
    with closing(connect(_scratch(run_dir))) as connection, connection:
        update_spot_check_session(connection, session_id, position=position, finished=finished)


def _record(run_dir: Path, *, session_id: str, screen: str, task: str, subject_kind: str, subject_id: str, verdict: str, other_kind: str | None = None, other_id: str | None = None, detail: Mapping[str, Any] | None = None) -> str:
    with closing(connect(_scratch(run_dir))) as connection, connection:
        return insert_review_row(
            connection,
            "review_judgments",
            {
                "run_id": _run_id(run_dir),
                "session_id": session_id,
                "screen": screen,
                "task": task,
                "subject_kind": subject_kind,
                "subject_id": subject_id,
                "other_kind": other_kind,
                "other_id": other_id,
                "judge": "owner",
                "verdict": verdict,
                "detail_json": dict(detail or {}),
            },
        )


def _arm_of(run_dir: Path, diagnosis_id: str) -> tuple[str | None, str | None]:
    rows = _rows(run_dir, "review_diagnoses", id=diagnosis_id)
    if not rows:
        return None, None
    targets = _rows(run_dir, "review_targets", id=rows[0]["target_id"])
    return rows[0]["arm"], (targets[0]["kind"] if targets else None)


def _adjudicate_arm_a(vault_repository: Repository | None, attempt_id: str, rating: str, repair_md: str | None) -> dict[str, Any]:
    """Map a tap on arm (a) to a full-authority adjudication, when one exists."""

    if vault_repository is None:
        return {"vault_adjudication": None, "reason": "no_vault_repository"}
    snapshot = diagnosis_snapshot(vault_repository, attempt_id)
    if snapshot is None:
        return {"vault_adjudication": None, "reason": "no_diagnosis_receipt"}
    if snapshot.system_abstained:
        verdict = {"right": "correctly_abstained", "wrong": "should_not_have_abstained"}.get(rating)
    elif rating == "right":
        verdict = "correct"
    elif rating == "wrong" and repair_md:
        verdict = "wrong_repair"
    else:
        verdict = None
    if verdict is None:
        return {"vault_adjudication": None, "reason": f"{rating}_is_not_a_full_authority_verdict"}
    try:
        record = append_diagnosis_adjudication(
            vault_repository,
            attempt_id=attempt_id,
            verdict=verdict,
            adjudicated_repair_md=repair_md if verdict == "wrong_repair" else None,
            queue_reason="sampled",
            adjudicator_source="human_owner",
            rationale="Slice 1 M1 spot-check (arm a: stored joint diagnosis)",
        )
    except ValueError as exc:
        return {"vault_adjudication": None, "reason": str(exc)[:200]}
    return {"vault_adjudication": record["id"], "verdict": verdict}


def record_diagnosis_screen(
    run_dir: Path,
    *,
    session_id: str,
    screen: Mapping[str, Any],
    ratings: Mapping[str, str],
    best: str | None,
    vault_repository: Repository | None = None,
    wrong_repairs: Mapping[str, str] | None = None,
) -> list[str]:
    """``ratings`` maps option label -> tap; ``best`` is a label, "none" or None (skip)."""

    by_label = {option["label"]: option for option in screen["options"]}
    ids = []
    for label, rating in ratings.items():
        if rating not in DIAGNOSIS_TAPS or label not in by_label:
            continue
        diagnosis_id = by_label[label]["diagnosis_id"]
        arm, kind = _arm_of(run_dir, diagnosis_id)
        detail: dict[str, Any] = {"label": label, "arm": arm, "spot_check_version": SPOT_CHECK_VERSION}
        if arm == "a" and kind == "real":
            detail.update(_adjudicate_arm_a(vault_repository, screen["attempt_id"], rating, (wrong_repairs or {}).get(label)))
        ids.append(
            _record(run_dir, session_id=session_id, screen="diagnoses", task="diagnosis_rating", subject_kind="review_diagnosis", subject_id=diagnosis_id, verdict=rating, detail=detail)
        )
    if best is not None:
        verdict = "none" if best == "none" else by_label.get(best, {}).get("diagnosis_id")
        if verdict:
            ids.append(
                _record(run_dir, session_id=session_id, screen="diagnoses", task="diagnosis_best", subject_kind="review_target", subject_id=screen["target_id"], verdict=verdict, detail={"label": best})
            )
    return ids


def record_links_screen(run_dir: Path, *, session_id: str, screen: Mapping[str, Any], verdicts: Sequence[str | None]) -> list[str]:
    ids = []
    for link, verdict in zip(screen["links"], verdicts):
        if verdict not in LINK_TAPS:
            continue
        ids.append(
            _record(
                run_dir, session_id=session_id, screen="links", task="same_cause",
                subject_kind="attempt", subject_id=screen["attempt_id"],
                other_kind="attempt", other_id=link["cited_attempt_id"], verdict=verdict,
                detail={"credited_diagnosis_ids": link["credited_diagnosis_ids"]},
            )
        )
    return ids


def record_grade_screen(run_dir: Path, *, session_id: str, screen: Mapping[str, Any], choice: str | None) -> list[str]:
    """``choice`` is a grade label ("Grade 1"/"Grade 2"), "not_sure" or None (skip)."""

    if choice is None:
        return []
    if choice == "not_sure":
        verdict = "not_sure"
    else:
        source = next((grade["source"] for grade in screen["grades"] if grade["label"] == choice), None)
        if source is None:
            return []
        verdict = f"{source}_right"
    return [
        _record(run_dir, session_id=session_id, screen="grade", task="grade_disagreement", subject_kind="attempt", subject_id=screen["attempt_id"], verdict=verdict, detail={"choice": choice})
    ]


def export_judgments(run_dir: Path) -> list[dict[str, Any]]:
    """All review_judgments as JSON-ready rows (ids and verdicts, no text)."""

    return [
        {key: value for key, value in row.items() if not key.endswith("_json")}
        for row in _rows(run_dir, "review_judgments", order_by="created_at")
    ]


__all__ = [
    "DIAGNOSIS_TAPS",
    "GRADE_TAPS",
    "LINK_TAPS",
    "MAX_ITEMS",
    "SPOT_CHECK_VERSION",
    "advance_session",
    "build_spot_check_plan",
    "export_judgments",
    "record_diagnosis_screen",
    "record_grade_screen",
    "record_links_screen",
    "render_screen",
    "start_or_resume_session",
]
