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

Without a pick (the reading failed, the chooser gave none, the switch is off)
nothing is targeted and the field loader keeps the F11 grounded rule, then
the opt-in classifier. Failures of optional steps are recorded in the row's
``detail`` and never fail the learner's answer.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

from learnloop.ai.spend import SpendLimitExceeded
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_gaps as store
from learnloop.diagnosis.text_gaps import actions
from learnloop.diagnosis.text_gaps.candidates import belief_candidates, prerequisite_candidates
from learnloop.diagnosis.text_gaps.contract import (
    PIPELINE_VERSION,
    UNREAD,
    GapReading,
    LearnerText,
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
#: estimate and the output budget each physical request is admitted with. A
#: practice-item proposal with its rubric and metadata does not fit the
#: default 2,000-token allowance (the live run truncated at it).
SEED_INPUT_TOKENS = 12_000
SEED_OUTPUT_TOKENS = 6_000


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
    return {pair.right.id: str(pair.verdict) for pair in results if pair.verdict in ("same", "different", "unsure")}


def _judge_all(
    repository: Repository, kind: Any, pairs: list, *, budget: TextBudget, clients: PipelineClients,
    decider_on: bool,
) -> dict[str, Any]:
    """Both judges on the same pairs; each verdict lands in ``judgment_ledger``."""

    out: dict[str, Any] = {"llm": None, "decider": None, "llm_results": [], "decider_results": []}
    judge_client = clients.get("judge")
    if judge_client is not None and pairs:
        executor = LLMPairExecutor(budget, judge_client)
        results = judge_pairs(repository, kind, pairs, execute=executor)
        out["llm"] = _verdicts(_with_standing(repository, kind, results, judge="llm", producer=executor.producer))
        out["llm_results"] = [pair.as_dict() for pair in results]
    decider_client = clients.get("decider") if decider_on else None
    if decider_client is not None and pairs:
        executor = DeciderPairExecutor(budget, decider_client)
        results = judge_pairs(repository, kind, pairs, execute=executor)
        out["decider"] = _verdicts(_with_standing(repository, kind, results, judge="decider", producer=executor.producer))
        out["decider_results"] = [pair.as_dict() for pair in results]
    return out


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
    except SpendLimitExceeded as exc:
        detail["embedding"] = f"refused: {exc}"
        return None, None
    except Exception as exc:  # noqa: BLE001 - the structural candidates still run
        detail["embedding"] = f"failed: {type(exc).__name__}"
        return None, None
    detail["embedding"] = "ok"
    return vector, str(getattr(embedder, "model_id", "") or "") or None


# -- prerequisites ------------------------------------------------------------------------------


def _prerequisite(
    root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, reading: GapReading, *,
    chooser: str, budget: TextBudget, clients: PipelineClients, now_iso: str, clock: Clock | None,
    progress: Mapping[str, Any], save_progress: Callable[[Mapping[str, Any]], None],
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
    query = prerequisite_query(text, reading.prerequisite_name, reading.prerequisite_line)
    vector, model_id = _embed_query(repository, budget, clients, vault, query, PREREQUISITE_FIELD, detail)
    candidates = prerequisite_candidates(
        vault, repository, text, query=query, query_vector=vector, model_id=model_id, top_k=int(config.top_k),
        limit=int(config.judge_max_pairs), day_start=actions.day_start(now_iso),
    )
    detail["candidates"] = candidates.summary()
    judged = _judge_all(repository, SAME_PREREQUISITE, candidates.pairs(query), budget=budget, clients=clients,
                        decider_on=bool(config.decider_enabled))
    authority = "decider" if chooser == "decider" else "llm"
    detail["judges"] = {"authoritative": authority, "llm": judged["llm"], "decider": judged["decider"]}
    verdicts = judged[authority]
    if candidates.subjects and not verdicts:
        detail["reason"] = f"no {authority} verdict"
        return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
    verdicts = verdicts or {}
    matched = next((subject for subject in candidates.subjects if verdicts.get(subject.id) == "same"), None)
    if matched is not None:
        outcome = actions.ActionOutcome(
            "matched_prerequisite", target_kind="learning_object", target_id=matched.id,
            target_subject_id=text.subject_id or (matched.scope.get("subjects") or (None,))[0],
            match_basis=f"judge:{authority}:{matched.scope.get('basis')}", detail=detail,
        )
        _maybe_edge(root, vault, repository, text, outcome, chooser=chooser, budget=budget, clients=clients,
                    clock=clock)
        return outcome
    if any(verdicts.get(subject.id) == "unsure" for subject in candidates.subjects):
        detail["reason"] = "unsure"
        return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
    return _create(root, vault, repository, text, reading, candidates.subjects, budget=budget, clients=clients,
                   now_iso=now_iso, clock=clock, detail=detail, progress=progress, save_progress=save_progress)


def _maybe_edge(
    root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, outcome: actions.ActionOutcome, *,
    chooser: str, budget: TextBudget, clients: PipelineClients, clock: Clock | None,
) -> None:
    config = vault.config.learner_text_gaps
    anchor, matched = text.anchor, str(outcome.target_id)
    item = vault.practice_items.get(text.practice_item_id) if text.practice_item_id else None
    if item is None or anchor is None or matched == anchor:
        outcome.detail["edge"] = "not_applicable"
        return
    if actions.declared_prerequisite(vault, matched, anchor):
        outcome.detail["edge"] = "declared"
        return
    if not config.add_edges_enabled:
        outcome.detail["edge"] = "disabled"
        return
    needed = ask_needed(
        repository, budget, context=needed_context(vault, item, vault.learning_objects[matched]),
        learning_object_id=matched, practice_item_id=item.id, judge_client=clients.get("judge"),
        decider_client=clients.get("decider") if config.decider_enabled else None,
    )
    authority = "decider" if chooser == "decider" else "llm"
    outcome.detail["needed"] = {"authoritative": authority, **needed}
    if (needed.get(authority) or {}).get("verdict") != "yes":
        outcome.detail["edge"] = "not_needed"
        return
    rationale = (needed.get("llm") or {}).get("rationale") or f"{item.id} builds on {matched}"
    edge_id, status = actions.add_prerequisite_edge(
        root, vault, prerequisite_lo=matched, dependent_lo=anchor, text=text, rationale=str(rationale), clock=clock,
    )
    outcome.edge_id = edge_id
    outcome.detail["edge"] = status
    if edge_id:
        sync_vault_state(load_vault(root), repository, clock=clock)


def _create(
    root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, reading: GapReading,
    shortlisted: list[Any], *, budget: TextBudget, clients: PipelineClients, now_iso: str, clock: Clock | None,
    detail: dict[str, Any], progress: Mapping[str, Any], save_progress: Callable[[Mapping[str, Any]], None],
) -> actions.ActionOutcome:
    config = vault.config.learner_text_gaps
    created = dict(progress.get("created") or {})
    if not created:
        if not config.create_prerequisites_enabled:
            detail["reason"] = "creation_disabled"
            return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
        if actions.creations_today(repository, now_iso=now_iso) >= int(config.max_creations_per_day):
            detail["reason"] = "daily_cap"
            return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
    subject_id = actions.subject_for_creation(vault, text, shortlisted)
    if subject_id is None:
        detail["reason"] = "no_subject"
        return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
    if not created.get("learning_object_id"):
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
        try:
            draft = draft_prerequisite(budget, drafter, context)
        except SpendLimitExceeded as exc:
            detail["reason"] = f"draft_refused: {exc}"
            return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
        except Exception as exc:  # noqa: BLE001
            detail["reason"] = f"draft_failed: {type(exc).__name__}"
            return actions.ActionOutcome("unmatched_prerequisite", detail=detail)
        created = actions.write_created_prerequisite(
            root, vault, repository, draft=draft, subject_id=subject_id, dependent_lo=text.anchor, text=text,
            clock=clock, progress=created,
        )
        created["draft"] = draft.model_dump(mode="json")
        save_progress({**progress, "created": created})
    outcome = actions.ActionOutcome(
        "created_prerequisite", target_kind="learning_object", target_id=created["learning_object_id"],
        target_subject_id=subject_id, match_basis="created", edge_id=created.get("edge_id"),
        created_concept_id=created.get("concept_id"), created_learning_object_id=created["learning_object_id"],
        detail={**detail, "edge": created.get("edge_status") or "no_asking_learning_object",
                "draft": created.get("draft")},
    )
    if "seed" in created:
        outcome.seed_practice_item_id, outcome.seed_status = created["seed"]
    elif text.question_event_id:
        outcome.seed_practice_item_id, outcome.seed_status = _seed(
            root, text, created["learning_object_id"], budget=budget, clients=clients, clock=clock,
        )
        created["seed"] = [outcome.seed_practice_item_id, outcome.seed_status]
        save_progress({**progress, "created": created})
    else:
        outcome.seed_status = "no_tutor_exchange"
    return outcome


def _seed(root: Path, text: LearnerText, learning_object_id: str, *, budget: TextBudget, clients: PipelineClients,
          clock: Clock | None) -> tuple[str | None, str]:
    tutor, drafter = clients.get("tutor"), clients.get("drafter")
    if tutor is None or drafter is None:
        return None, "no_client"
    from learnloop.diagnosis.text_gaps.contract import DRAFT_ROUTE

    budget.register_llm(DRAFT_ROUTE, drafter)
    try:
        # The promotion path's analysis and authoring calls are one admitted
        # unit: on a metered route each further physical request inside it is
        # admitted (and charged) before it is sent.
        with budget.request(DRAFT_ROUTE, "learner_gap_seed", input_tokens=SEED_INPUT_TOKENS,
                            output_tokens=SEED_OUTPUT_TOKENS):
            return actions.seed_from_question(
                root, question_event_id=str(text.question_event_id), learning_object_id=learning_object_id,
                tutor_client=tutor, authoring_client=drafter,
                grounding=actions.grounding_learning_object_ids(text), clock=clock,
            )
    except SpendLimitExceeded:
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
                        decider_on=bool(config.decider_enabled))
    # Beliefs: the LLM judge is authoritative; the Decider is logged only.
    detail["judges"] = {"authoritative": "llm", "llm": judged["llm"], "decider": judged["decider"]}
    verdicts = judged["llm"]
    if candidates.subjects and not verdicts:
        return actions.ActionOutcome("signal_only", detail={**detail, "reason": "no llm verdict"})
    matched = next((subject for subject in candidates.subjects if (verdicts or {}).get(subject.id) == "same"), None)
    outcome = actions.record_belief(
        vault, repository, text=text, statement=reading.belief_statement,
        matched=dict(matched.scope) if matched is not None else None, clock=clock,
    )
    outcome.detail = {**detail, **outcome.detail}
    return outcome


# -- one learner text -------------------------------------------------------------------------------


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
    the pipeline is switched off.
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
    progress = dict(progress or {})
    save = save_progress or (lambda _payload: None)
    now_iso = utc_now_iso(clock)
    with budget.receipts(repository, text.subject_key):
        reading = text.reading
        if reading is None and text.context_judge == "gap_reader":
            reader = clients.get("reader")
            reading = read_text(budget, reader, text) if reader is not None else GapReading(
                "none", judge="llm", status="unavailable", prompt_version="")
        if reading is not None and reading.status == "ok":
            log_reading(repository, text, reading)
        decider = DeciderKind("disabled")
        if config.decider_enabled:
            decider_client = clients.get("decider")
            decider = decider_kind(repository, budget, decider_client, text) if decider_client is not None else DeciderKind("unavailable")
        chooser = str(config.chooser)
        kind = authoritative(chooser, reading, decider)
        if kind == "prerequisite" and reading is not None and reading.status == "ok" and reading.names(kind):
            outcome = _prerequisite(
                root, vault, repository, text, reading, chooser=chooser, budget=budget, clients=clients,
                now_iso=now_iso, clock=clock, progress=progress, save_progress=save,
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
        "subject_id": text.subject_id, "learner_text": text.text[:4000], "chooser": str(config.chooser),
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
        if advance is not None:
            actions.persist_check_advance(connection, advance, gap_id=gap_id, now_iso=now_iso)
        if commitment is not None:
            store.insert_commitment(connection, {**commitment, "gap_id": gap_id, "created_at": now_iso})
    if outcome.action in ("created_prerequisite",) or outcome.edge_id or advance is not None:
        repository.bump_queue_revision(clock=clock)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.gap(connection, gap_id)


def failed_row(text: LearnerText, *, vault: LoadedVault, error: str, now_iso: str) -> dict[str, Any]:
    """The ledger row for a learner text whose job gave up (no target)."""

    return {
        "source_kind": text.source_kind, "source_id": text.source_id, "attempt_id": text.attempt_id,
        "practice_item_id": text.practice_item_id,
        "anchor_learning_object_id": text.anchor_learning_object_ids[0] if text.anchor_learning_object_ids else None,
        "subject_id": text.subject_id, "learner_text": text.text[:4000],
        "chooser": str(vault.config.learner_text_gaps.chooser), "context_judge": text.context_judge,
        "kind": UNREAD, "action": "failed", "detail_json": {"error": error},
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
    "authoritative",
    "default_clients",
    "failed_row",
    "named_gaps_for_card",
    "process_learner_text",
]
