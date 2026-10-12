"""Import M1 pattern-link verdicts into the vault's ``judgment_ledger`` (§12.1).

They become the first ``same_cause`` rows Slice 2 T1 evaluates against. Only
links between two REAL attempts are imported: planted learners' ids exist only
in the scratch copy. The LLM judge's rows keep their model, prompt version and
input hash; the owner's spot-check verdicts are imported as ``judge='owner'``.
Re-running the import appends nothing twice (same question, judge and input
hash). The ledger is append-only; nothing here edits a verdict.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import closing
from pathlib import Path
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.diagnosis_review import review_rows
from learnloop.db.stores.judgments import append_judgment
from learnloop.diagnosis.offline_review.judge import revision_of
from learnloop.diagnosis.offline_review.report import current_revisions
from learnloop.diagnosis.offline_review.runner import RUN_FILE, SCRATCH_FILE
from learnloop.diagnosis.offline_review.spot_check import SPOT_CHECK_VERSION

IMPORT_VERSION = "m1-link-import-v1"


def _planted_ids(connection, run_id: str) -> set[str]:
    ids: set[str] = set()
    for row in review_rows(connection, "review_planted_cases", where={"run_id": run_id}):
        record = row.get("history") or {}
        ids.add(str(row["target_attempt_id"]))
        for attempt in record.get("history") or []:
            ids.add(str(attempt.get("attempt_id")))
    return ids


def import_pattern_links(run_dir: Path, vault_repository: Repository, *, dry_run: bool = False) -> dict[str, Any]:
    run_dir = Path(run_dir)
    run_id = str(json.loads((run_dir / RUN_FILE).read_text(encoding="utf-8"))["run_id"])
    candidates: list[dict[str, Any]] = []
    superseded = 0
    with closing(connect(run_dir / SCRATCH_FILE, read_only=True)) as scratch:
        planted = _planted_ids(scratch, run_id)
        # Only the judgment revision over each target's CURRENT links counts:
        # a link set that changed on resume was re-judged as a new revision.
        revisions = current_revisions(
            review_rows(scratch, "review_diagnoses", where={"run_id": run_id}),
            review_rows(scratch, "review_targets", where={"run_id": run_id}),
        )["links"]
        for row in scratch.execute(
            "SELECT left_id, right_id, judge_model, prompt_version, input_hash, verdict, rationale "
            "FROM judgment_ledger WHERE task = 'same_cause' AND judge = 'llm' "
            "AND left_kind = 'attempt' AND right_kind = 'attempt' ORDER BY created_at, id"
        ):
            if revision_of({"rationale": row[6]}) != revisions.get(str(row[0])):
                superseded += 1
                continue
            candidates.append(
                {
                    "left_id": row[0], "right_id": row[1], "judge": "llm", "judge_model": row[2],
                    "prompt_version": row[3], "input_hash": row[4], "verdict": row[5],
                    "rationale": row[6] or "",
                }
            )
        for row in review_rows(scratch, "review_judgments", where={"run_id": run_id, "task": "same_cause", "judge": "owner"}):
            candidates.append(
                {
                    "left_id": row["subject_id"], "right_id": row["other_id"], "judge": "owner", "judge_model": None,
                    "prompt_version": SPOT_CHECK_VERSION,
                    "input_hash": hashlib.sha256(f"{run_id}:{row['id']}".encode("utf-8")).hexdigest(),
                    "verdict": row["verdict"],
                    "rationale": json.dumps({"source": "m1_spot_check", "run_id": run_id, "review_judgment_id": row["id"]}, sort_keys=True),
                }
            )
    eligible = [row for row in candidates if row["left_id"] not in planted and row["right_id"] not in planted]
    report = {
        "import_version": IMPORT_VERSION,
        "run_id": run_id,
        "candidates": len(candidates),
        "excluded_planted": len(candidates) - len(eligible),
        "excluded_superseded_revision": superseded,
        "imported": 0,
        "already_present": 0,
        "dry_run": dry_run,
    }
    seen: set[tuple[str, ...]] = set()
    with vault_repository.connection() as connection:
        has_ledger = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='judgment_ledger'"
        ).fetchone() is not None
        if not has_ledger and not dry_run:
            raise ValueError("the vault database has no judgment_ledger; open the vault with learnloop once to migrate it")
        report["vault_has_ledger"] = has_ledger
        for row in eligible:
            # A verdict's identity is its question, judge, input AND rationale:
            # the judge's two passes over one link may share an input.
            key = (row["left_id"], row["right_id"], row["judge"], row["input_hash"], row["rationale"])
            exists = key in seen or (has_ledger and connection.execute(
                "SELECT 1 FROM judgment_ledger WHERE task = 'same_cause' AND left_kind = 'attempt' AND left_id = ? "
                "AND right_kind = 'attempt' AND right_id = ? AND judge = ? AND input_hash = ? AND rationale = ?",
                key,
            ).fetchone() is not None)
            seen.add(key)
            if exists:
                report["already_present"] += 1
                continue
            if dry_run:
                report["imported"] += 1
                continue
            append_judgment(
                connection,
                task="same_cause",
                left_kind="attempt",
                left_id=row["left_id"],
                right_kind="attempt",
                right_id=row["right_id"],
                judge=row["judge"],
                judge_model=row["judge_model"],
                prompt_version=row["prompt_version"],
                input_hash=row["input_hash"],
                verdict=row["verdict"],
                rationale=row["rationale"],
            )
            report["imported"] += 1
    return report


__all__ = ["IMPORT_VERSION", "import_pattern_links"]
