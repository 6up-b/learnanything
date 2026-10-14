"""Router R2c: teach-back dialogues summarized into the card's typed evidence (spec §15.1).

Owner direction (2026-10-12, D11): a learner's teach-back dialogue is among
the richest evidence LearnLoop collects. After the blind grader has graded the
dialogue (post-grade, off the hot path: a background thread started by the
finishing RPC), an LLM summarizer condenses it: what was explained correctly,
what was missing or wrong, and a few of the learner's own words. The summary
enters ``LearnerStateCardV1`` as typed evidence with its source attempt
(``evidence_sections.teach_back_summaries``, the registry hook R2a built), so
both router models read it at the next boundary.

* **Inputs.** The transcript the grader graded (``learner_answer_md``), the
  topic's title and the grade's result word. Never the rubric, a reference
  answer or source text; a dialogue on exam or reserved material is never
  summarized (the card's own withholding rule).
* **Storage.** One ``model_work_checkpoints`` row per attempt (WORKFLOW:
  model work kept so it is never paid twice; key
  ``router_teach_back_summary:v1:<attempt>``). Replay never reads it.
* **Route and spend.** The router LLM's route (``router_llm``), under the
  router's daily guard (owner ``router_teach_back_summary``); subscription
  routes uncapped.
* **Switch.** ``router.teach_back_summary`` (on), acting only where the
  mixture serves (the R2b + R2c successor, ``router.mode = "mixture"``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import logging
import threading
import time
from typing import Any

from learnloop.ai.schemas import WireModel

LOG = logging.getLogger(__name__)

PURPOSE = "router_teach_back_summary"
VERSION = "router_teach_back_summary_v1"
CACHE_PREFIX = "router_teach_back_summary:v1:"
SECTION = "teach_back_summaries"
#: The summary's lists stay short (the card's budget).
MAX_POINTS = 5
POINT_LIMIT = 240
#: How many summaries the card shows (newest first).
CARD_LIMIT = 6
TIMEOUT_SECONDS = 120.0


class TeachBackSummary(WireModel):

    explained_correctly: list[str]
    missing_or_wrong: list[str]
    learner_words: list[str]


def summary_prompt(topic: str, result: str, transcript: str) -> str:
    return "\n".join([
        "Summarize one learner's teach-back dialogue for a study app. The learner explained a topic to a "
        "simulated student who asked follow-up questions.",
        "",
        f"Topic: {topic}. The grader's overall result: {result}.",
        "",
        f"1. explained_correctly: up to {MAX_POINTS} short points the learner explained correctly.",
        f"2. missing_or_wrong: up to {MAX_POINTS} short points the learner left out or got wrong.",
        "3. learner_words: up to 3 short quotes, in the learner's own words, that show their understanding "
        "(or its gap).",
        "Plain words; no scores; nothing that is not in the dialogue.",
        "",
        "--- the dialogue ---",
        transcript,
    ])


def _clip(points: Sequence[str], limit: int) -> list[str]:
    out = []
    for point in list(points)[:limit]:
        text = " ".join(str(point).split())
        out.append(text if len(text) <= POINT_LIMIT else text[: POINT_LIMIT - 1].rstrip() + "…")
    return [point for point in out if point]


def _result_word(correctness: Any) -> str:
    if correctness is None:
        return "not graded"
    value = float(correctness)
    return "correct" if value >= 0.999 else "incorrect" if value <= 0.001 else "partly correct"


def summarize(vault: Any, repository: Any, attempt_id: str, *, runtime: Any) -> dict[str, Any] | None:
    """Summarize one graded teach-back attempt and store it; returns the stored summary.

    None (nothing sent) when the attempt is not a graded teach-back, is exam
    or reserved material, or is already summarized; a model failure is logged."""

    from learnloop.ai.transport import execute_structured_operation
    from learnloop.daily_plan.router_card import CardGatherer
    from learnloop.daily_plan.router_runtime import LLM, SUMMARY_RECEIPT_OWNER, SpendRefused

    key = CACHE_PREFIX + attempt_id
    if repository.model_checkpoint(key) is not None:
        return None
    with repository.connection() as connection:
        attempt = connection.execute(
            "SELECT id, practice_item_id, learning_object_id, attempt_type, correctness, learner_answer_md, created_at "
            "FROM practice_attempts WHERE id = ?", (attempt_id,),
        ).fetchone()
    if attempt is None or attempt["attempt_type"] != "teach_back" or not (attempt["learner_answer_md"] or "").strip():
        return None
    unknowns: list[str] = []
    withheld = CardGatherer(vault, repository)._withheld_items(unknowns)
    if withheld is None or str(attempt["practice_item_id"]) in withheld:
        return None
    learning_object = vault.learning_objects.get(attempt["learning_object_id"])
    topic = learning_object.title if learning_object is not None else str(attempt["learning_object_id"])
    prompt = summary_prompt(topic, _result_word(attempt["correctness"]), str(attempt["learner_answer_md"]))
    try:
        client = runtime.models.client(vault, LLM, timeout_seconds=TIMEOUT_SECONDS)
    except Exception:  # noqa: BLE001 - not set up: no summary
        return None
    from learnloop.ai.spend import is_subscription_transport
    from learnloop.daily_plan.router_runtime import _supports_isolation

    subscription = bool(is_subscription_transport(client=client))
    started = time.monotonic()
    try:
        # Every physical request (a transport retry or a JSON repair included)
        # is admitted by the router's daily guard in its start receipt.
        with runtime.spend.metered(repository, vault.config, owner_kind=SUMMARY_RECEIPT_OWNER, owner_id=attempt_id):
            # An isolated turn, as the blind grader reads the same dialogue:
            # no tools, files, memories or MCP servers beside the prompt.
            answer = execute_structured_operation(
                client, purpose=PURPOSE, prompt=prompt, result_model=TeachBackSummary,  # type: ignore[arg-type]
                timeout_seconds=TIMEOUT_SECONDS, isolated=_supports_isolation(client),
            )
    except SpendRefused:
        LOG.info("router R2c: teach-back summary of %s refused by the daily guard", attempt_id)
        return None
    except Exception:  # noqa: BLE001 - a summary is context; its failure is logged, never raised
        LOG.warning("router R2c: the teach-back summary of %s failed", attempt_id, exc_info=True)
        return None
    summary = {
        "version": VERSION,
        "attempt_id": str(attempt["id"]),
        "practice_item_id": str(attempt["practice_item_id"]),
        "learning_object_id": str(attempt["learning_object_id"]),
        "at": str(attempt["created_at"]),
        "explained_correctly": _clip(answer.explained_correctly, MAX_POINTS),
        "missing_or_wrong": _clip(answer.missing_or_wrong, MAX_POINTS),
        "learner_words": _clip(answer.learner_words, 3),
        "model": getattr(client, "model", None),
        "latency_ms": int(round((time.monotonic() - started) * 1000)),
    }
    repository.save_model_checkpoint(key, purpose=PURPOSE, result=summary, usage={"subscription": subscription})
    return summary


def summaries_active(vault: Any) -> bool:
    from learnloop.daily_plan.policy import mixture_active

    return bool(getattr(vault.config.router, "teach_back_summary", False)) and mixture_active(vault)


def schedule(vault: Any, sqlite_path: Any, attempt_id: str, *, runtime: Any = None) -> threading.Thread | None:
    """Summarize a just-graded teach-back off the hot path (a daemon thread; inline in an inline runtime)."""

    if not summaries_active(vault):
        return None
    from learnloop.daily_plan.router_runtime import LLM, default_runtime
    from learnloop.db.repositories import Repository

    runtime = runtime if runtime is not None else default_runtime()
    if runtime.readiness(vault).get(LLM) is not None:
        return None

    def run() -> None:
        try:
            summarize(vault, Repository.attach(sqlite_path), attempt_id, runtime=runtime)
        except Exception:  # noqa: BLE001
            LOG.warning("router R2c: the teach-back summary job failed", exc_info=True)

    if runtime.inline:
        run()
        return None
    import contextvars

    context = contextvars.copy_context()
    thread = threading.Thread(target=context.run, args=(run,), name="learnloop-teach-back-summary", daemon=True)
    thread.start()
    return thread


def summaries_for(connection: Any, learning_object_ids: Sequence[str], *, before: str,
                  withheld: frozenset[str] | None, titles: Mapping[str, str]) -> list[dict[str, Any]]:
    """The card's typed evidence: summaries of teach-backs on these topics, made before ``before``."""

    if not learning_object_ids or withheld is None:
        return []
    wanted = set(learning_object_ids)
    out = []
    for row in connection.execute(
        "SELECT result_json FROM model_work_checkpoints WHERE purpose = ? ORDER BY created_at DESC", (PURPOSE,)
    ):
        try:
            summary = json.loads(row["result_json"] or "{}")
        except ValueError:
            continue
        if summary.get("learning_object_id") not in wanted or str(summary.get("at") or "") >= before:
            continue
        if str(summary.get("practice_item_id")) in withheld:
            continue
        out.append({
            "attempt_id": summary.get("attempt_id"),
            "at": summary.get("at"),
            "learning_object_id": summary.get("learning_object_id"),
            "topic": titles.get(str(summary.get("learning_object_id")), summary.get("learning_object_id")),
            "explained_correctly": list(summary.get("explained_correctly") or ()),
            "missing_or_wrong": list(summary.get("missing_or_wrong") or ()),
            "learner_words": list(summary.get("learner_words") or ()),
            "source": "teach_back_summary",
        })
    out.sort(key=lambda entry: str(entry.get("at") or ""), reverse=True)
    return out[:CARD_LIMIT]


__all__ = [
    "CACHE_PREFIX",
    "PURPOSE",
    "SECTION",
    "TeachBackSummary",
    "schedule",
    "summaries_active",
    "summaries_for",
    "summarize",
    "summary_prompt",
]
