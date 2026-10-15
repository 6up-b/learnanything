"""Read one learner text into a named gap and act on it (implementation_handoffs §4).

1. **Kind, name first.** The context model's reading (the tutor's, the
   diagnoser's, or one stuck-text reader call) and the Decider's typed
   ``choice`` are both appended to ``judgment_ledger``;
   ``learner_text_gaps.chooser`` says whose kind is authoritative. A kind is
   acted on only when the context model named it (the Decider names nothing).
2. **Match** with T1's ``judge_pairs``: every candidate pair is judged by the
   LLM judge and the Decider, both logged. Prerequisites: the chooser's judge
   is authoritative. Beliefs: the LLM judge is; the Decider is a second
   opinion that never joins anything. No score decides anything.
3. **Act** (``actions``): a weak signal through the persisted target, a
   "needed?"-gated edge, a created prerequisite with its seed item and light
   commitment, a holding-pen sighting or candidate, the sooner check.
4. **Log** the whole reading as one ``learner_text_gaps`` row (append-only;
   the router's learner-state card reads these, :func:`named_gaps_for_card`).

**Tier 1 (mvp-0.22, owner 2026-10-13).** The Decider is the authoritative
judge of the kind, every candidate pair (beliefs included) and "needed?"; the
LLM judge and the context model's kind decide only what it gave no answer
(``tier1``). The switches ``decider_routes.learner_gap_judge`` and
``decider_routes.learner_gap_kind`` restore the steps above.

Without a pick (the reading failed, the chooser gave none, the switch is off)
nothing is targeted and the field loader keeps the F11 grounded rule, then
the opt-in classifier. Failures of optional steps are recorded in the row's
``detail`` and never fail the learner's answer.

**Only settled verdicts decide** (Codex review F1, F2). A match or a creation
needs a verdict from the authoritative judge on EVERY candidate pair; a pair
that failed, was claimed by another worker or was fenced raises
:class:`ReadingDeferred` (no ledger row; the job is retried, then logged as
``failed``). A spend refusal or a cancellation raises it with ``spend=True``
(the budget stopped the reading, not the text: the job is released and the
run stops), anywhere until the text's action is decided and written; only
the seed item, optional content made after a creation, records ``refused``
instead. A text is never finalized on a partial reading.

**Crash-safe writes** (F3). Vault writes take ids derived from the learner
text and are recorded in the job's progress BEFORE they are made, so a retry
finds and reuses them; database writes (a holding-pen candidate, a sighting)
commit in the same transaction as the ledger row. The reading, the chooser
and the authoritative kind are recorded too, before anything acts on them
(re-review F1): a retry reuses them instead of reading a stuck answer again,
and a recorded creation or edge is finished first, whatever a switch now
says (:func:`_resume`). A job switched off or gone after it wrote is logged
``failed`` with what it wrote (``jobs``), never left without a row.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_gaps as store
from learnloop.decider_judgments import enabled as decider_enabled
from learnloop.diagnosis.text_gaps import actions
from learnloop.diagnosis.text_gaps.candidates import belief_candidates, prerequisite_candidates
from learnloop.diagnosis.text_gaps.contract import (
    DRAFT_ROUTE,
    PIPELINE_VERSION,
    UNREAD,
    GapReading,
    LearnerText,
    PrerequisiteDraft,
)
from learnloop.diagnosis.text_gaps.judges import (
    DeciderKind,
    DeciderPairExecutor,
    LLMPairExecutor,
    TextBudget,
    ask_needed,
    decider_kind,
    draft_prerequisite,
    log_reading,
    needed_context,
    query_vector,
    read_text,
)
from learnloop.diagnosis.text_gaps.kinds import (
    BELIEF_FIELD,
    PREREQUISITE_FIELD,
    SAME_BELIEF,
    SAME_PREREQUISITE,
    belief_query,
    prerequisite_query,
)
from learnloop.matching.judge import JudgedPair, judge_pairs
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault

LOG = logging.getLogger(__name__)
ClientFactory = Callable[[], Any]
#: The seed item's promotion unit (analysis + authoring + gates): its input
#: estimate. Each physical request in it is admitted with the seed route's
#: output budget under the shared policy (``learnloop.ai.output_budget``;
#: the hand-set 6,000 is retired: a reasoning model's thinking counts too).
SEED_INPUT_TOKENS = 12_000
#: The seed's promotion analysis runs on the tutor's client (Codex review F12).
TUTOR_ROUTE = "tutor_qa"
#: ``judge_pairs`` statuses that carry a verdict this pipeline may act on.
SETTLED = ("judged", "already_judged")
#: What ``judge_pairs`` stops on (its ``not_run`` error names one of these).
_STOPS = ("SpendLimitExceeded", "SpendCancelled", "AIInterrupted")


class ReadingDeferred(Exception):
    """The reading cannot be finished now: no ledger row is written.

    ``spend``: a spend refusal or a cancellation stopped it (the budget, not
    the text): the job is released and the run stops. Otherwise a judge gave
    no verdict on a candidate pair (failed, claimed elsewhere, fenced): the
    job is retried with backoff and, after its last attempt, logged as
    ``failed`` with no target.
    """

    def __init__(self, reason: str, *, spend: bool = False) -> None:
        super().__init__(reason)
        self.reason = reason
        self.spend = spend


@dataclass
class PipelineClients:
    """Client factories, resolved only when a step needs one (None: unavailable)."""

    judge: ClientFactory | None = None
    reader: ClientFactory | None = None
    decider: ClientFactory | None = None
    drafter: ClientFactory | None = None
    tutor: ClientFactory | None = None
    embedder: ClientFactory | None = None

    _cache: dict[str, Any] | None = None

    def get(self, name: str) -> Any | None:
        if self._cache is None:
            self._cache = {}
        if name not in self._cache:
            factory = getattr(self, name)
            try:
                self._cache[name] = factory() if factory is not None else None
            except Exception:  # noqa: BLE001 - an unavailable route is a recorded skip
                LOG.warning("learner-text gap client %s unavailable", name, exc_info=True)
                self._cache[name] = None
        return self._cache[name]


def _ready(vault: LoadedVault, task: str, *, timeout: int | None = None) -> Any | None:
    from learnloop.ai.routing import ready_client_for_task

    resolved = ready_client_for_task(vault.root, vault.config, task, timeout_seconds=timeout)
    return resolved.client if resolved.ready else None


def default_clients(vault: LoadedVault) -> PipelineClients:
    timeout = int(vault.config.learner_text_gaps.judge_timeout_seconds)

    def embedder() -> Any | None:
        from learnloop.diagnosis.split.jobs import default_embedding_client

        return default_embedding_client(vault)

    return PipelineClients(
        judge=lambda: _ready(vault, "learner_gap_judge", timeout=timeout),
        reader=lambda: _ready(vault, "learner_gap_reader", timeout=timeout),
        decider=lambda: _ready(vault, "learner_gap_decider"),
        drafter=lambda: _ready(vault, "authoring"),
        tutor=lambda: _ready(vault, "tutor_qa"),
        embedder=embedder,
    )


def authoritative(chooser: str, reading: GapReading | None, decider: DeciderKind) -> str:
    """The kind the chooser switch makes authoritative (``unread`` without one)."""

    if chooser == "decider":
        return decider.choice if decider.status == "ok" and decider.choice else UNREAD
    if reading is not None and reading.status == "ok":
        return reading.kind
    return UNREAD


def _verdicts(results: Sequence[JudgedPair]) -> dict[str, str]:
    """Settled verdicts only: a ``fenced`` pair's verdict was never appended."""

    return {
        pair.right.id: str(pair.verdict) for pair in results
        if pair.status in SETTLED and pair.verdict in ("same", "different", "unsure")
    }


def _unsettled(results: Sequence[JudgedPair]) -> list[dict[str, Any]]:
    return [
        {"id": pair.right.id, "status": pair.status, "error": pair.error} for pair in results
        if not (pair.status in SETTLED and pair.verdict in ("same", "different", "unsure"))
    ]


def _stopped(results: Sequence[JudgedPair]) -> str | None:
    return next((str(pair.error) for pair in results if pair.status == "not_run" and pair.error in _STOPS), None)


def _judge_all(
    repository: Repository, kind: Any, pairs: list, *, budget: TextBudget, clients: PipelineClients,
    decider_on: bool, vault: LoadedVault | None = None,
) -> dict[str, Any]:
    """Both judges on the same pairs; each verdict lands in ``judgment_ledger``.

    A spend stop or a cancellation of either judge raises
    :class:`ReadingDeferred` (``spend=True``): what was judged is in the
    ledger and is reused when the text is read again. At mvp-0.22 (Tier 1)
    the Decider decides and the LLM judges only the pairs it gave no answer
    (``tier1.judge_all``; the result's ``authority`` is ``selected``).
    """

    if vault is not None and _tier1(vault, "learner_gap_judge"):
        from learnloop.diagnosis.text_gaps import tier1

        return tier1.judge_all(repository, kind, pairs, budget=budget, clients=clients)
    out: dict[str, Any] = {"llm": None, "decider": None, "llm_results": [], "decider_results": [],
                           "llm_unsettled": [], "decider_unsettled": []}
    for name, executor_type, client in (
        ("llm", LLMPairExecutor, clients.get("judge")),
        ("decider", DeciderPairExecutor, clients.get("decider") if decider_on else None),
    ):
        if client is None or not pairs:
            continue
        executor = executor_type(budget, client)
        results = _with_standing(repository, kind, judge_pairs(repository, kind, pairs, execute=executor),
                                 judge=name, producer=executor.producer)
        stop = _stopped(results)
        if stop is not None:
            raise ReadingDeferred(f"{name} pair judging stopped: {stop}", spend=True)
        out[name] = _verdicts(results)
        out[f"{name}_unsettled"] = _unsettled(results)
        out[f"{name}_results"] = [pair.as_dict() for pair in results]
    return out


def _tier1(vault: LoadedVault, switch: str) -> bool:
    """Tier 1 for a learner-text gap judgment: its ``[decider_routes]`` switch at mvp-0.22.

    ``learner_text_gaps.decider_enabled = false`` keeps learner text from the
    Decider at every version (review F5): the predecessor path then runs, as
    it did with that setting before mvp-0.22.
    """

    return decider_enabled(vault.config, switch) and bool(vault.config.learner_text_gaps.decider_enabled)


def _pair_authority(vault: LoadedVault, chooser: str) -> str:
    """The authoritative pair judge before Tier 1: the chooser's (``llm`` for ``context_model``).

    With the Tier-1 kind on, ``chooser`` names who decided the kind (the
    Decider, or the context model as its fallback), so the configured
    ``learner_text_gaps.chooser`` names the pair judge, as it did before.
    """

    if _tier1(vault, "learner_gap_kind"):
        chooser = str(vault.config.learner_text_gaps.chooser)
    return "decider" if chooser == "decider" else "llm"


def _require_settled(judged: Mapping[str, Any], authority: str) -> None:
    """Every candidate pair has a verdict from the authoritative judge (F1)."""

    unsettled = judged.get(f"{authority}_unsettled") or []
    if unsettled:
        names = ", ".join(f"{entry['id']} ({entry['status']})" for entry in unsettled)
        raise ReadingDeferred(f"the {authority} judge gave no verdict on: {names}")


def _with_standing(
    repository: Repository, kind: Any, results: Sequence[JudgedPair], *, judge: str, producer: str,
) -> list[JudgedPair]:
    """``already_judged`` pairs take the producer's standing verdict from the ledger."""

    from learnloop.matching.judge import pair_input_hash

    out = []
    for pair in results:
        if pair.status == "already_judged" and pair.verdict is None:
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                row = connection.execute(
                    "SELECT verdict FROM judgment_ledger j WHERE task = ? AND judge = ? AND judge_model = ? "
                    "AND prompt_version = ? AND input_hash = ? "
                    "AND NOT EXISTS (SELECT 1 FROM judgment_ledger s WHERE s.supersedes_id = j.id) "
                    "ORDER BY created_at DESC LIMIT 1",
                    (kind.task, judge, producer, kind.prompt_version, pair_input_hash(kind, pair.left, pair.right)),
                ).fetchone()
            if row is not None:
                pair = JudgedPair(pair.left, pair.right, pair.status, verdict=str(row[0]), score=pair.score)
        out.append(pair)
    return out


def _embed_query(repository: Repository, budget: TextBudget, clients: PipelineClients, vault: LoadedVault,
                 subject: Any, field_name: str, detail: dict[str, Any]) -> tuple[Any, str | None]:
    if not vault.config.embedding.enabled:
        detail["embedding"] = "disabled"
        return None, None
    embedder = clients.get("embedder")
    if embedder is None:
        detail["embedding"] = "unavailable"
        return None, None
    try:
        vector = query_vector(repository, budget, embedder, subject, field_name=field_name)
    except (SpendLimitExceeded, AIInterrupted) as exc:
        # Without the vector the shortlist would differ: read the text later.
        raise ReadingDeferred(f"query embedding refused: {exc}", spend=True) from exc
    except Exception as exc:  # noqa: BLE001 - the structural candidates still run
        detail["embedding"] = f"failed: {type(exc).__name__}"
        return None, None
    detail["embedding"] = "ok"
    return vector, str(getattr(embedder, "model_id", "") or "") or None


# -- prerequisites ------------------------------------------------------------------------------

#: ``checkpoint(**changes)``: merge into the job's progress and persist it.
Checkpoint = Callable[..., None]


def _prerequisite(
    root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, reading: GapReading, *,
    chooser: str, budget: TextBudget, clients: PipelineClients, now_iso: str, clock: Clock | None,
    progress: Mapping[str, Any], checkpoint: Checkpoint,
) -> actions.ActionOutcome:
    config = vault.config.learner_text_gaps
    detail: dict[str, Any] = {}
    if reading.prerequisite_refs:
        # The diagnoser named it from its validated neighbourhood: its pick.
        target = reading.prerequisite_refs[0]
        learning_object = vault.learning_objects.get(target)
        if learning_object is None or (text.subject_id and text.subject_id not in learning_object.subjects):
            return actions.ActionOutcome("unmatched_prerequisite", detail={"reason": "diagnoser_ref_outside_subject"})
        outcome = actions.ActionOutcome(
            "matched_prerequisite", target_kind="learning_object", target_id=target,
            target_subject_id=text.subject_id or learning_object.subjects[0], match_basis="diagnoser_ref",
        )
        return outcome
    if not reading.prerequisite_name:
        return actions.ActionOutcome("unnamed", detail={"reason": "no prerequisite named"})
    # A creation or an edge an earlier attempt recorded never reaches here:
    # :func:`_resume` finishes it first, without judging again.
    query = prerequisite_query(text, reading.prerequisite_name, reading.prerequisite_line)
    vector, model_id = _embed_query(repository, budget, clients, vault, query, PREREQUISITE_FIELD, detail)
    candidates = prerequisite_candidates(
        vault, repository, text, query=query, query_vector=vector, model_id=model_id, top_k=int(config.top_k),
        limit=int(config.judge_max_pairs), day_start=actions.day_start(now_iso),
    )
    detail["candidates"] = candidates.summary()
    judged = _judge_all(repository, SAME_PREREQUISITE, candidates.pairs(query), budget=budget, clients=clients,
                        decider_on=bool(config.decider_enabled), vault=vault)
    authority = judged.get("authority") or _pair_authority(vault, chooser)
    detail["judges"] = {"authoritative": authority, "llm": judged["llm"], "decider": judged["decider"]}
    if "selected_judges" in judged:
        detail["judges"]["selected"] = judged["selected_judges"]
    verdicts = judged[authority]
    if candidates.subjects and verdicts is None:
        # The authoritative judge's route is not available: nothing decides.
        detail["reason"] = f"no {authority} judge"
        return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
    _require_settled(judged, authority)
    verdicts = verdicts or {}
    same = [subject for subject in candidates.subjects if verdicts.get(subject.id) == "same"]
    if len(same) > 1:
        # F11's uniqueness: identity is never decided by list order (F5).
        detail.update(reason="ambiguous", same=[subject.id for subject in same])
        return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
    if same and same[0].id in text.anchor_learning_object_ids:
        # The named knowledge is the asking item's own LO: not a prerequisite
        # of it, so no target (a prerequisite question never targets its own
        # item's LO), no edge and no sooner check (F5).
        detail.update(reason="own_learning_object", same=[same[0].id])
        return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
    if same:
        matched = same[0]
        outcome = actions.ActionOutcome(
            "matched_prerequisite", target_kind="learning_object", target_id=matched.id,
            target_subject_id=text.subject_id or (matched.scope.get("subjects") or (None,))[0],
            match_basis=f"judge:{judged.get('selected_judges', {}).get(matched.id, authority)}:"
                        f"{matched.scope.get('basis')}",
            detail=detail,
        )
        _maybe_edge(root, vault, repository, text, outcome, chooser=chooser, budget=budget, clients=clients,
                    clock=clock, checkpoint=checkpoint)
        return outcome
    if any(verdicts.get(subject.id) == "unsure" for subject in candidates.subjects):
        detail["reason"] = "unsure"
        return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
    if text.subject_id is None:
        # Without a grounded subject only the anchors were judged (F4): no
        # subject-wide duplicate check ran, so nothing is created.
        detail["reason"] = "no_subject"
        return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
    return _create(root, vault, repository, text, reading, budget=budget, clients=clients, now_iso=now_iso,
                   clock=clock, detail=detail, progress=progress, checkpoint=checkpoint)


def _maybe_edge(
    root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, outcome: actions.ActionOutcome, *,
    chooser: str, budget: TextBudget, clients: PipelineClients, clock: Clock | None, checkpoint: Checkpoint,
) -> None:
    config = vault.config.learner_text_gaps
    anchor, matched = text.anchor, str(outcome.target_id)
    item = vault.practice_items.get(text.practice_item_id) if text.practice_item_id else None
    if item is None or anchor is None or matched == anchor:
        outcome.detail["edge"] = "not_applicable"
        return
    authority = _pair_authority(vault, chooser)
    if actions.declared_prerequisite(vault, matched, anchor):
        outcome.detail["edge"] = "declared"
        return
    if not config.add_edges_enabled:
        outcome.detail["edge"] = "disabled"
        return
    context = needed_context(vault, item, vault.learning_objects[matched])
    if _tier1(vault, "learner_gap_judge"):
        # Tier 1: the Decider's "needed?", else the LLM judge's.
        from learnloop.diagnosis.text_gaps import tier1

        authority = "selected"
        needed = tier1.ask_needed(vault, repository, budget, context=context, learning_object_id=matched,
                                  practice_item_id=item.id, clients=clients)
        # The Decider's own refusal fell back; only the deciding judge's stops the reading.
        refused = ["selected"] if needed["selected"].get("status") == "refused" else []
    else:
        needed = ask_needed(
            repository, budget, context=context,
            learning_object_id=matched, practice_item_id=item.id, judge_client=clients.get("judge"),
            decider_client=clients.get("decider") if config.decider_enabled else None,
        )
        refused = [name for name, entry in needed.items() if entry.get("status") == "refused"]
    if refused:
        raise ReadingDeferred(f"\"needed?\" refused for {', '.join(refused)}", spend=True)
    if (needed.get(authority) or {}).get("verdict") != "yes":
        outcome.detail["needed"] = {"authoritative": authority, **needed}
        outcome.detail["edge"] = "not_needed"
        return
    # Recorded BEFORE it is written, with the match it finishes (F3): a retry
    # writes this edge and logs this match (:func:`_resume`), never asking,
    # judging or adding again.
    edge = {
        "prerequisite": matched, "dependent": anchor, "edge_id": actions.edge_id_for(text, matched, anchor),
        "needed": needed, "authority": authority,
        "outcome": {"target_subject_id": outcome.target_subject_id, "match_basis": outcome.match_basis,
                    "detail": dict(outcome.detail)},
    }
    checkpoint(edge=edge)
    _write_edge(root, vault, repository, text, outcome, edge=edge, clock=clock)


def _write_edge(
    root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, outcome: actions.ActionOutcome, *,
    edge: Mapping[str, Any], clock: Clock | None,
) -> None:
    """Write the recorded edge (idempotent: an edge already on disk is ``added``)."""

    needed = dict(edge.get("needed") or {})
    prerequisite, dependent = str(edge["prerequisite"]), str(edge["dependent"])
    outcome.detail["needed"] = {"authoritative": str(edge.get("authority") or "llm"), **needed}
    asking = text.practice_item_id or text.source_id
    rationale = (needed.get("llm") or {}).get("rationale") or f"{asking} builds on {prerequisite}"
    written_id, status = actions.add_prerequisite_edge(
        root, vault, prerequisite_lo=prerequisite, dependent_lo=dependent, text=text, rationale=str(rationale),
        clock=clock, edge_id=str(edge["edge_id"]), origin="match",
    )
    outcome.edge_id = written_id
    outcome.detail["edge"] = status
    if written_id:
        sync_vault_state(load_vault(root), repository, clock=clock)


def _resume(
    root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, *, budget: TextBudget,
    clients: PipelineClients, now_iso: str, clock: Clock | None, progress: Mapping[str, Any],
    checkpoint: Checkpoint,
) -> actions.ActionOutcome | None:
    """Finish the vault write an earlier attempt of this job recorded (F3,
    re-review F1); None when it recorded none.

    Whatever the reading, the chooser or the creation and edge switches now
    say: a creation whose draft is recorded, or a matched edge whose id is,
    is finished and logged, never left on disk without a ledger row (the
    daily cap and ``learnloop gaps undo`` read the row). Judging again could
    see the half-written LO itself, or a newer candidate, and orphan it.
    """

    created = dict(progress.get("created") or {})
    if created.get("draft"):
        outcome = _create(root, vault, repository, text, None, budget=budget, clients=clients, now_iso=now_iso,
                          clock=clock, detail=dict(created.get("detail") or {}), progress=progress,
                          checkpoint=checkpoint)
        outcome.detail["resumed"] = "creation"
        return outcome
    edge = dict(progress.get("edge") or {})
    if edge.get("edge_id") and edge.get("prerequisite") and edge.get("dependent"):
        recorded = dict(edge.get("outcome") or {})
        outcome = actions.ActionOutcome(
            "matched_prerequisite", target_kind="learning_object", target_id=str(edge["prerequisite"]),
            target_subject_id=recorded.get("target_subject_id") or text.subject_id,
            match_basis=recorded.get("match_basis") or "resumed", detail=dict(recorded.get("detail") or {}),
        )
        _write_edge(root, vault, repository, text, outcome, edge=edge, clock=clock)
        outcome.detail["resumed"] = "edge"
        return outcome
    return None


def _create(
    root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, reading: GapReading | None, *,
    budget: TextBudget, clients: PipelineClients, now_iso: str, clock: Clock | None,
    detail: dict[str, Any], progress: Mapping[str, Any], checkpoint: Checkpoint,
) -> actions.ActionOutcome:
    config = vault.config.learner_text_gaps
    created = dict(progress.get("created") or {})
    if not created.get("draft"):
        if reading is None:
            raise ValueError("a creation without a recorded draft needs its reading")
        if not config.create_prerequisites_enabled:
            detail["reason"] = "creation_disabled"
            return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
        if actions.creations_today(repository, now_iso=now_iso) >= int(config.max_creations_per_day):
            detail["reason"] = "daily_cap"
            return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
        subject_id = actions.subject_for_creation(vault, text)
        if subject_id is None:
            detail["reason"] = "no_subject"
            return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
        drafter = clients.get("drafter")
        if drafter is None:
            detail["reason"] = "no_drafter"
            return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
        anchor_lo = vault.learning_objects.get(text.anchor) if text.anchor else None
        context = {
            "named": {"name": reading.prerequisite_name, "line": reading.prerequisite_line},
            "learner_text": text.text,
            "about": dict(text.context),
            "asking_learning_objective": (
                {"title": anchor_lo.title, "statement": anchor_lo.summary} if anchor_lo is not None else None
            ),
            "subject": vault.subjects[subject_id].metadata.title if subject_id in vault.subjects else subject_id,
            "concepts_in_subject": sorted({
                vault.concepts[lo.concept].title for lo in vault.learning_objects.values()
                if subject_id in lo.subjects and lo.concept in vault.concepts
            })[:40],
        }
        from learnloop.diagnosis.text_gaps.provenance import drafter_record

        # Diagnosis input provenance: what the drafter is shown, frozen before
        # it runs (codex review F3) and kept with the draft, so a resumed
        # creation records the same.
        with repository.connection() as connection:
            provenance = drafter_record(connection, vault, text, reading, subject_id=subject_id,
                                        shown_concept_titles=context["concepts_in_subject"])
        try:
            draft = draft_prerequisite(budget, drafter, context)
        except (SpendLimitExceeded, AIInterrupted) as exc:
            raise ReadingDeferred(f"draft refused: {exc}", spend=True) from exc
        except Exception as exc:  # noqa: BLE001
            detail["reason"] = f"draft_failed: {type(exc).__name__}"
            return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
        # Recorded BEFORE anything is written: a retry reuses the draft and
        # the ids derived from it and this text (F3).
        created = {**actions.creation_ids(text, draft, dependent_lo=text.anchor), "subject_id": subject_id,
                   "draft": draft.model_dump(mode="json"), "detail": detail,
                   "provenance": provenance.as_json()}
        checkpoint(created=created)
    if not created.get("edge_status"):
        written = actions.write_created_prerequisite(
            root, repository, draft=PrerequisiteDraft.model_validate(created["draft"]),
            subject_id=str(created["subject_id"]), concept_id=str(created["concept_id"]),
            learning_object_id=str(created["learning_object_id"]), edge_id=created.get("edge_id"),
            dependent_lo=text.anchor, text=text, clock=clock,
        )
        created.update(written)
        checkpoint(created=created)
    subject_id = str(created["subject_id"])
    outcome = actions.ActionOutcome(
        "created_prerequisite", target_kind="learning_object", target_id=created["learning_object_id"],
        target_subject_id=subject_id, match_basis="created", edge_id=created.get("edge_id"),
        created_concept_id=created.get("concept_id"), created_learning_object_id=created["learning_object_id"],
        detail={**detail, "edge": created.get("edge_status") or "no_asking_learning_object",
                "draft": created.get("draft")},
        created_provenance=created.get("provenance"),
    )
    if "seed" in created:
        outcome.seed_practice_item_id, outcome.seed_status = created["seed"]
    elif text.question_event_id:
        outcome.seed_practice_item_id, outcome.seed_status = _seed(
            root, text, created["learning_object_id"], budget=budget, clients=clients, clock=clock,
        )
        created["seed"] = [outcome.seed_practice_item_id, outcome.seed_status]
        checkpoint(created=created)
    else:
        outcome.seed_status = "no_tutor_exchange"
    return outcome


def _seed_route(budget: TextBudget) -> str:
    """The route the seed's promotion unit is admitted on (Codex review F12).

    The unit spans the tutor's analysis call and the authoring call. A
    metered route anywhere in it meters the whole unit (every further
    physical request is admitted before it is sent): the costliest one, or
    one without a price (refused before sending, never estimated as free).
    """

    metered = [
        route for route in (TUTOR_ROUTE, DRAFT_ROUTE)
        if (info := budget.spend.routes.get(route)) is not None and info.billing == "metered"
    ]
    if not metered:
        return DRAFT_ROUTE
    return max(metered, key=lambda route: (
        budget.spend.routes[route].price_per_million is None, budget.spend.routes[route].price_per_million or 0.0,
    ))


def _seed(root: Path, text: LearnerText, learning_object_id: str, *, budget: TextBudget, clients: PipelineClients,
          clock: Clock | None) -> tuple[str | None, str]:
    tutor, drafter = clients.get("tutor"), clients.get("drafter")
    if tutor is None or drafter is None:
        return None, "no_client"
    budget.register_llm(TUTOR_ROUTE, tutor)
    budget.register_llm(DRAFT_ROUTE, drafter)
    try:
        # The promotion path's analysis and authoring calls are one admitted
        # unit: on a metered route each further physical request inside it is
        # admitted (and charged) before it is sent.
        route = _seed_route(budget)
        with budget.request(route, "learner_gap_seed", input_tokens=SEED_INPUT_TOKENS,
                            output_tokens=budget.spend.output_limit(route)):
            return actions.seed_from_question(
                root, question_event_id=str(text.question_event_id), learning_object_id=learning_object_id,
                tutor_client=tutor, authoring_client=drafter, clock=clock,
            )
    except (SpendLimitExceeded, AIInterrupted):
        # The text was read and acted on (the LO is written); the seed is
        # optional content: recorded as refused, promotable by hand.
        return None, "refused"
    except Exception as exc:  # noqa: BLE001 - the LO stays; the seed can be promoted by hand
        LOG.warning("seed item for %s failed", learning_object_id, exc_info=True)
        return None, f"failed:{type(exc).__name__}"


# -- beliefs --------------------------------------------------------------------------------------


def _belief(
    vault: LoadedVault, repository: Repository, text: LearnerText, reading: GapReading, *, budget: TextBudget,
    clients: PipelineClients, clock: Clock | None,
) -> actions.ActionOutcome:
    config = vault.config.learner_text_gaps
    if text.source_kind == "diagnosis":
        match = dict(reading.registry_match or {})
        kind = match.get("kind")
        outcome = actions.ActionOutcome(
            "belief_registry_path", match_basis="diagnoser_registry_match",
            detail={"registry_match": match, "note": "normalized by the diagnoser's registry_match path"},
        )
        if kind in ("durable", "candidate") and match.get("id"):
            outcome.target_kind, outcome.target_id = str(kind), str(match["id"])
        return outcome
    if not reading.belief_statement:
        return actions.ActionOutcome("unnamed", detail={"reason": "no belief stated"})
    if not config.sightings_enabled:
        return actions.ActionOutcome("signal_only", detail={"reason": "sightings_disabled"})
    detail: dict[str, Any] = {}
    query = belief_query(text, reading.belief_statement)
    vector, model_id = _embed_query(repository, budget, clients, vault, query, BELIEF_FIELD, detail)
    candidates = belief_candidates(
        vault, repository, text, query=query, query_vector=vector, model_id=model_id, top_k=int(config.top_k),
        limit=int(config.judge_max_pairs),
    )
    detail["candidates"] = candidates.summary()
    judged = _judge_all(repository, SAME_BELIEF, candidates.pairs(query), budget=budget, clients=clients,
                        decider_on=bool(config.decider_enabled), vault=vault)
    # Beliefs: the LLM judge is authoritative; the Decider is logged only.
    # At mvp-0.22 (Tier 1) the Decider decides, the LLM where it gave none.
    authority = str(judged.get("authority") or "llm")
    detail["judges"] = {"authoritative": authority, "llm": judged["llm"], "decider": judged["decider"]}
    if "selected_judges" in judged:
        detail["judges"]["selected"] = judged["selected_judges"]
    verdicts = judged[authority]
    if candidates.subjects and verdicts is None:
        return actions.ActionOutcome("signal_only", detail={**detail, "reason": f"no {authority} judge"})
    # A failed pair could be the true match: a new candidate would duplicate it.
    _require_settled(judged, authority)
    same = [subject for subject in candidates.subjects if (verdicts or {}).get(subject.id) == "same"]
    if len(same) > 1:
        return actions.ActionOutcome("unplaced", detail={
            **detail, "reason": "ambiguous", "same": [subject.id for subject in same]})
    outcome = actions.record_belief(
        vault, repository, text=text, statement=reading.belief_statement,
        matched=dict(same[0].scope) if same else None, clock=clock,
    )
    outcome.detail = {**detail, **outcome.detail}
    return outcome


# -- one learner text -------------------------------------------------------------------------------


def _decide(
    repository: Repository, text: LearnerText, vault: LoadedVault, *, budget: TextBudget,
    clients: PipelineClients, progress: Mapping[str, Any], checkpoint: Checkpoint,
) -> tuple[GapReading | None, DeciderKind, str, str]:
    """The reading, the Decider's kind, the chooser and the authoritative kind.

    Recorded in the job's progress before anything acts on them, and reused
    by every retry of the job (re-review F1): a stuck answer is read once (a
    second reading could differ, or fail, and orphan what the first one
    wrote), and a chooser switched between attempts does not change a
    reading already acted on.
    """

    decided = progress.get("decided")
    if isinstance(decided, Mapping):
        recorded = decided.get("reading")
        return (
            GapReading.from_progress(recorded) if isinstance(recorded, Mapping) else None,
            DeciderKind(**dict(decided["decider"])), str(decided["chooser"]), str(decided["kind"]),
        )
    if _tier1(vault, "learner_gap_kind"):
        # Tier 1: the Decider's kind is authoritative; the context model names the gap.
        from learnloop.diagnosis.text_gaps import tier1

        return tier1.decide_kind(vault, repository, text, budget, clients, progress, checkpoint)
    config = vault.config.learner_text_gaps
    reading = text.reading
    if reading is None and text.context_judge == "gap_reader":
        if isinstance(progress.get("reading"), Mapping):
            # Read by an earlier attempt that stopped before the kind (a
            # refused Decider): never paid for twice.
            reading = GapReading.from_progress(progress["reading"])
        else:
            reader = clients.get("reader")
            reading = read_text(budget, reader, text) if reader is not None else GapReading(
                "none", judge="llm", status="unavailable", prompt_version="")
            if reading.status == "refused":
                raise ReadingDeferred("the stuck-text reading was refused", spend=True)
            if reading.status == "ok":
                checkpoint(reading=reading.as_progress())
    if reading is not None and reading.status == "ok":
        log_reading(repository, text, reading)
    decider = DeciderKind("disabled")
    if config.decider_enabled:
        decider_client = clients.get("decider")
        decider = decider_kind(repository, budget, decider_client, text) if decider_client is not None else DeciderKind("unavailable")
        if decider.status == "refused":
            raise ReadingDeferred(f"the Decider's kind was refused: {decider.error}", spend=True)
    chooser = str(config.chooser)
    kind = authoritative(chooser, reading, decider)
    checkpoint(decided={"reading": reading.as_progress() if reading is not None else None,
                        "decider": decider.as_dict(), "chooser": chooser, "kind": kind})
    return reading, decider, chooser, kind


def process_learner_text(
    root: Path,
    repository: Repository,
    text: LearnerText,
    *,
    clients: PipelineClients | None = None,
    budget: TextBudget | None = None,
    clock: Clock | None = None,
    progress: Mapping[str, Any] | None = None,
    save_progress: Callable[[Mapping[str, Any]], None] | None = None,
) -> dict[str, Any] | None:
    """Read, match, act and log one learner text; returns its ledger row.

    Idempotent per source: an already-read text returns its row. None when
    the pipeline is switched off. Raises :class:`ReadingDeferred` when the
    reading cannot be finished now (no row is written; see the module doc).
    """

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        existing = store.gap_for_source(connection, text.source_kind, text.source_id)
    if existing is not None:
        return existing
    vault = load_vault(root)
    config = vault.config.learner_text_gaps
    if not config.enabled:
        return None
    clients = clients or default_clients(vault)
    budget = budget or TextBudget.for_text(vault)
    state: dict[str, Any] = dict(progress or {})
    save = save_progress or (lambda _payload: None)

    def checkpoint(**changes: Any) -> None:
        state.update(changes)
        save(dict(state))

    now_iso = utc_now_iso(clock)
    with budget.receipts(repository, text.subject_key):
        reading, decider, chooser, kind = _decide(
            repository, text, vault, budget=budget, clients=clients, progress=state, checkpoint=checkpoint,
        )
        resumed = _resume(root, vault, repository, text, budget=budget, clients=clients, now_iso=now_iso,
                          clock=clock, progress=state, checkpoint=checkpoint)
        if resumed is not None:
            # What was written was a prerequisite; it is logged as one.
            outcome, kind = resumed, "prerequisite"
        elif kind == "prerequisite" and reading is not None and reading.status == "ok" and reading.names(kind):
            outcome = _prerequisite(
                root, vault, repository, text, reading, chooser=chooser, budget=budget, clients=clients,
                now_iso=now_iso, clock=clock, progress=state, checkpoint=checkpoint,
            )
        elif kind == "misconception" and reading is not None and reading.status == "ok" and reading.names(kind):
            outcome = _belief(vault, repository, text, reading, budget=budget, clients=clients, clock=clock)
        elif kind in ("prerequisite", "misconception"):
            outcome = actions.ActionOutcome("unnamed", detail={"reason": "the context model named no gap of this kind"})
        elif kind in ("slip", "wording"):
            outcome = actions.ActionOutcome("signal_only")
        else:
            outcome = actions.ActionOutcome("none", detail={"reason": "unread"} if kind == UNREAD else {})
    vault = load_vault(root)
    advance = None
    if outcome.action == "matched_prerequisite" and outcome.target_id:
        try:
            advance = actions.advance_check(vault, repository, learning_object_id=str(outcome.target_id),
                                            now_iso=now_iso)
        except Exception:  # noqa: BLE001 - the sooner check never fails the reading
            LOG.warning("sooner check failed for %s", outcome.target_id, exc_info=True)
    commitment = None
    if outcome.action == "created_prerequisite" and outcome.seed_practice_item_id:
        commitment = actions.commitment_row(
            vault, learning_object_id=str(outcome.created_learning_object_id),
            practice_item_id=outcome.seed_practice_item_id, now_iso=now_iso,
        )
    detail = dict(outcome.detail)
    detail["spend"] = budget.spend.summary()
    row = {
        "source_kind": text.source_kind, "source_id": text.source_id, "attempt_id": text.attempt_id,
        "practice_item_id": text.practice_item_id,
        "anchor_learning_object_id": text.anchor or (text.anchor_learning_object_ids[0] if text.anchor_learning_object_ids else None),
        "subject_id": text.subject_id, "learner_text": text.text[:4000], "chooser": chooser,
        "context_judge": text.context_judge,
        "context_kind": reading.kind if reading is not None and reading.status == "ok" else None,
        "decider_kind": decider.choice, "decider_json": decider.as_dict(), "kind": kind,
        "named_json": {**(reading.named() if reading is not None else {}),
                       "reading_status": reading.status if reading is not None else "none"},
        "action": outcome.action, "target_kind": outcome.target_kind, "target_id": outcome.target_id,
        "target_subject_id": outcome.target_subject_id, "match_basis": outcome.match_basis,
        "edge_id": outcome.edge_id, "created_concept_id": outcome.created_concept_id,
        "created_learning_object_id": outcome.created_learning_object_id,
        "seed_practice_item_id": outcome.seed_practice_item_id, "seed_status": outcome.seed_status,
        "detail_json": detail, "algorithm_version": vault.config.algorithms.algorithm_version,
        "pipeline_version": PIPELINE_VERSION, "created_at": now_iso,
    }
    with repository.atomic():
        connection = repository.connection()
        gap_id = store.insert_gap(connection, row)
        _record_written_texts(connection, vault, text, outcome, gap_id=gap_id, learner_words=row["learner_text"],
                              clock=clock)
        # A holding-pen candidate or a sighting commits with its ledger row:
        # a retry before this point wrote nothing, after it reads the row (F3).
        for write in outcome.writes:
            write()
        if advance is not None:
            actions.persist_check_advance(connection, advance, gap_id=gap_id, now_iso=now_iso)
        if commitment is not None:
            store.insert_commitment(connection, {**commitment, "gap_id": gap_id, "created_at": now_iso})
    if outcome.action in ("created_prerequisite",) or outcome.edge_id or advance is not None:
        repository.bump_queue_revision(clock=clock)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.gap(connection, gap_id)


def _record_written_texts(connection: Any, vault: LoadedVault, text: LearnerText, outcome: actions.ActionOutcome, *,
                          gap_id: str, learner_words: str, clock: Clock | None) -> None:
    """Diagnosis input provenance, in the ledger row's transaction: a
    question's words (the gap's), a created prerequisite's drafted title and
    a seeded item's question each record what they were written from
    (``text_gaps.provenance``). A gap drawn from an answer shows the answer
    itself (rule (b)) and needs no record."""

    from learnloop.db.stores.write_provenance import WriteRecord, record_text_write
    from learnloop.diagnosis.text_gaps.provenance import TUTOR_UNRECORDED, question_record

    if text.source_kind == "tutor_question":
        record_text_write(
            connection, kind="learner_text_gap", record_id=gap_id, text=learner_words, writer="gap_reader",
            record=question_record(connection, str(text.question_event_id or text.source_id),
                                   topics=text.anchor_learning_object_ids),
            clock=clock,
        )
    created = outcome.created_learning_object_id
    if outcome.action == "created_prerequisite" and created and created in vault.learning_objects:
        drafted = (WriteRecord.from_json(outcome.created_provenance) if outcome.created_provenance is not None
                   else WriteRecord.incomplete("the drafter's inputs were not recorded (drafted before write-time "
                                               "provenance)"))
        record_text_write(connection, kind="learning_object", record_id=str(created),
                          text=vault.learning_objects[str(created)].title, writer="prerequisite_drafter",
                          record=drafted, clock=clock)
        seeded = outcome.seed_practice_item_id
        item = vault.practice_items.get(str(seeded)) if seeded else None
        if item is not None:
            # Authored by the question-promotion path from the tutor's answer.
            record_text_write(
                connection, kind="practice_item", record_id=str(seeded), text=item.prompt, writer="gap_seed",
                record=drafted.join(WriteRecord.incomplete(TUTOR_UNRECORDED)), clock=clock,
            )


def failed_row(
    text: LearnerText, *, vault: LoadedVault, error: str, now_iso: str, progress: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The ledger row for a learner text whose job gave up (no target).

    Whatever an earlier attempt already wrote to the vault (its job progress:
    a created concept and LO, an added edge) is named on the row, so it
    counts toward the daily creation cap and the owner can undo it
    (``learnloop gaps undo``) (F3).
    """

    progress = dict(progress or {})
    created = dict(progress.get("created") or {})
    written = created.get("learning_object_id") if created.get("learning_object_id") in vault.learning_objects else None
    edge_ids = {edge.id for edge in actions.edges_on_disk(vault)}
    edge_id = next((
        str(candidate) for candidate in (created.get("edge_id"), (progress.get("edge") or {}).get("edge_id"))
        if candidate and candidate in edge_ids
    ), None)
    return {
        "source_kind": text.source_kind, "source_id": text.source_id, "attempt_id": text.attempt_id,
        "practice_item_id": text.practice_item_id,
        "anchor_learning_object_id": text.anchor_learning_object_ids[0] if text.anchor_learning_object_ids else None,
        "subject_id": text.subject_id, "learner_text": text.text[:4000],
        "chooser": str(vault.config.learner_text_gaps.chooser), "context_judge": text.context_judge,
        "kind": UNREAD, "action": "failed", "edge_id": edge_id,
        "created_concept_id": created.get("concept_id") if written else None,
        "created_learning_object_id": written,
        "detail_json": {"error": error, **({
            "progress": {"created": bool(written), "edge_id": edge_id},
            "edge_prerequisite": (progress.get("edge") or {}).get("prerequisite") if not written else None,
        } if written or edge_id else {})},
        "algorithm_version": vault.config.algorithms.algorithm_version, "pipeline_version": PIPELINE_VERSION,
        "created_at": now_iso,
    }


# -- what the router's learner-state card reads ------------------------------------------------


def named_gaps_for_card(
    connection: Any, *, learning_object_ids: Sequence[str] | None = None, before: str | None = None,
    since: str | None = None,
) -> list[dict[str, Any]]:
    """Each named gap as a typed event (router spec §4), oldest first.

    Undone gaps are kept with their reversal so the card can say so. No
    learner-facing text other than the learner's own question is included.
    """

    rows = store.gaps(connection, since=since, before=before, learning_object_ids=learning_object_ids)
    reversed_by: dict[str, list[str]] = {}
    for reversal in store.reversals(connection, [row["id"] for row in rows]):
        reversed_by.setdefault(reversal["gap_id"], []).append(reversal["reversal"])
    return [
        {
            "event_id": row["id"], "at": row["created_at"], "source": row["source_kind"], "kind": row["kind"],
            "named": {key: value for key, value in (row.get("named") or {}).items() if key != "reading_status"},
            "action": row["action"], "target": (
                {"kind": row["target_kind"], "id": row["target_id"], "subject": row["target_subject_id"]}
                if row.get("target_id") else None
            ),
            "chooser": row["chooser"], "context_kind": row["context_kind"], "decider_kind": row["decider_kind"],
            "reversals": reversed_by.get(row["id"], []),
        }
        for row in rows
        if row["kind"] not in ("none", UNREAD)
    ]


__all__ = [
    "PipelineClients",
    "ReadingDeferred",
    "authoritative",
    "default_clients",
    "failed_row",
    "named_gaps_for_card",
    "process_learner_text",
]
