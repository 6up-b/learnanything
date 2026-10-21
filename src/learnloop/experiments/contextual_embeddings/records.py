"""E0's experiment-owned repository: receipts and verdicts (spec §4.3, §6).

Spec §4.3: "Reuse ``model_call_receipts``, ``judgment_ledger`` and
``source_tool_calls`` for their existing roles." The frozen copies are
read-only and the service copies belong to the system arms, so each copy's
paid run gets its own writable repository: a fresh vault initialized under
the private run directory (``fixtures-local`` only), at this code's
migration head.

* **Receipts (Codex review F4).** Every model call of a copy's run is
  observed into this repository's ``model_call_receipts``
  (``owner_kind = "experiment_e0"``), installed explicitly around the run, so
  the receipts never depend on the working directory: the CLI's own observer
  would otherwise search upward from it for a vault (and fail, or write into
  an unrelated one).
* **Verdicts (Codex review F10).** Every label pass, adjudication and answer
  judgement is appended to ``judgment_ledger``, task-keyed (``e0_label``,
  ``e0_label_sets``, ``e0_label_adjudication``, ``e0_answer_judgement``),
  with the complete input identity (the role call's checkpoint key) as
  ``input_hash``, the resolved model and prompt version, the canonical span
  references and the call's receipt ids in ``rationale``. The id is derived
  from that identity, so a resumed run appends nothing twice.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
from typing import Any

OWNER_KIND = "experiment_e0"


class ExperimentRecords:
    """One copy's writable experiment repository (under fixtures-local only)."""

    def __init__(self, root: Path) -> None:
        from learnloop.experiments.contextual_embeddings.corpus import _inside_local_root
        from learnloop.vault.loader import init_vault, load_vault
        from learnloop.vault.paths import VaultPaths
        from learnloop.vault.repository import vault_repository

        root = Path(root)
        if not _inside_local_root(root):
            raise ValueError("an experiment repository must be under fixtures-local")
        if not (root / "learnloop.toml").is_file():
            init_vault(root)
        vault = load_vault(root, load_environment=False)
        self.root = vault.root
        self.repository = vault_repository(VaultPaths(vault.root, vault.config))

    @contextmanager
    def receipts(self, owner_id: str) -> Iterator[None]:
        """Observe every model call in this context into this repository."""

        from learnloop.ai.execution import record_model_calls

        with record_model_calls(self.repository, owner_kind=OWNER_KIND, owner_id=owner_id):
            yield

    def judgment(self, *, task: str, left_id: str, right_kind: str | None, right_id: str | None, verdict: str,
                 score: float | None, details: Mapping[str, Any], call: Any) -> str:
        from learnloop.db.stores.judgments import append_judgment

        judgment_id = "e0j_" + hashlib.sha256(json.dumps(
            [task, left_id, right_kind, right_id, call.checkpoint_key, call.role], sort_keys=True,
        ).encode()).hexdigest()[:32]
        rationale = json.dumps({"role": call.role, "receipts": list(call.receipts), "cached": call.cached,
                                **dict(details)}, sort_keys=True, default=str)
        with self.repository.connection() as connection:
            if connection.execute("SELECT 1 FROM judgment_ledger WHERE id = ?", (judgment_id,)).fetchone():
                return judgment_id
            append_judgment(connection, task=task, left_kind="e0_question", left_id=left_id, right_kind=right_kind,
                            right_id=right_id, judge="llm", judge_model=call.model or "unknown",
                            prompt_version=call.prompt_version, input_hash=call.checkpoint_key, verdict=verdict,
                            score=score, rationale=rationale, id=judgment_id)
            connection.commit()
        return judgment_id

    def judgments(self, task: str | None = None) -> list[dict[str, Any]]:
        with self.repository.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM judgment_ledger" + (" WHERE task = ?" if task else "") + " ORDER BY id",
                (task,) if task else (),
            ).fetchall()
            columns = [item[0] for item in connection.execute("SELECT * FROM judgment_ledger LIMIT 0").description]
        return [dict(zip(columns, row, strict=True)) for row in rows]

    def completed_outputs(self, prompt: str) -> list[str]:
        """The output texts of this repository's COMPLETED receipts whose
        input is exactly ``prompt`` (by text or prompt hash), newest first:
        what a resume can recover a settled response from (fix round 4,
        Medium 11)."""

        from learnloop.ai.execution import content_key

        with self.repository.connection() as connection:
            rows = connection.execute(
                "SELECT output_text FROM model_call_receipts WHERE owner_kind = ? AND status = 'completed' "
                "AND output_text IS NOT NULL AND (input_text = ? OR prompt_hash = ?) ORDER BY started_at DESC",
                (OWNER_KIND, prompt, content_key(prompt))).fetchall()
        return [str(row[0]) for row in rows]

    def receipt_count(self) -> int:
        with self.repository.connection() as connection:
            return int(connection.execute(
                "SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = ?", (OWNER_KIND,)).fetchone()[0])
