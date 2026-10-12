"""Recurrence groups (Slice 2 T1, spec_embedding_consumers_v1 §3.4).

The ``hypothesis_recurrence_*`` projection is rebuilt deterministically from
raw ledgers, with no model and no embedding call:

* **exact classes**: every concrete causal-hypothesis episode belongs to the
  class of its ``statement_normalized`` (the old key; always grouped);
* **validated diagnoser citations** (Slice 1 §5.4) of each attempt's live
  diagnosis in force, resolved to statement classes;
* **``same_cause`` verdicts** in ``judgment_ledger`` (the judge, the owner's
  M1 verdicts, ...) plus the diagnosis card's "not the same mistake" taps.
  The highest-authority verdict per pair wins: owner > verifier > llm =
  diagnoser > learner_card.

Classes are joined by incremental union in adjudication order
(:mod:`learnloop.matching.union`); a union that would put two classes with a
recorded ``different`` verdict (at equal or higher authority) into one group
is refused and logged for review. Only merged groups get rows, so a vault
with no merges has an empty projection and every ``recurrence_key`` is the
old exact key.

Resolving an attempt-level link to classes. A citation names a cause of the
diagnosed attempt (``cause:<event>:<cause>`` or an earlier hypothesis id)
and an earlier attempt. The cause gives the anchor class; the cited attempt's
class is the anchor class itself when present, else its only class (learner
-state classes first), else the only one on the anchor's target facet. An
attempt-level verdict without a citation behind it resolves only when each
attempt has one class. Anything else is an ``unresolved_link`` review case and
joins nothing.

The projection is empty unless the vault is at a ``RECURRENCE_GROUP_VERSIONS``
successor with ``recurrence.enabled`` on. :func:`refresh_recurrence_groups`
recomputes it when its input fingerprint (cheap ledger counters) changed; the
``recurrence_groups`` rebuild replayer forces it, and vault open
(``sync_vault_state``) re-syncs it so the kill switch takes effect there.

**Prepared vs active.** ``learnloop upgrade --to mvp-0.11`` builds the groups
BEFORE its config switch as PREPARED (state ``active = 0``), which no
consumer reads (``recurrence_group_map`` returns only active groups); only
after the config rename succeeds does :func:`activate_recurrence_groups` flip
them. Consumers that hold the vault use :func:`active_group_map`, which also
checks the effective algorithm version and kill switch directly.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.algorithm_versions import RECURRENCE_GROUP_VERSIONS
from learnloop.db.repositories import Repository
from learnloop.db.stores import recurrence as store
from learnloop.matching.union import UnionEdge, union_with_refusals
from learnloop.recurrence import GROUP_RECURRENCE_KEY_VERSION, group_key_for, normalize_statement
from learnloop.vault.models import LoadedVault

BUILDER_VERSION = GROUP_RECURRENCE_KEY_VERSION
#: Authority when verdicts conflict (§3.1). ``exact_key`` verdicts never join
#: classes: the exact key is the base, not an edge.
AUTHORITY = {"owner": 4, "verifier": 3, "llm": 2, "diagnoser": 2, "learner_card": 1}
_VERDICTS = {"same": "same", "different": "different", "not_sure": "unsure", "unsure": "unsure"}
CAUSE_REF_PREFIX = "cause:"


def recurrence_active(vault: LoadedVault) -> bool:
    config = getattr(vault.config, "recurrence", None)
    return (
        vault.config.algorithms.algorithm_version in RECURRENCE_GROUP_VERSIONS
        and bool(getattr(config, "enabled", True))
    )


def active_group_map(vault: LoadedVault, repository: Repository) -> dict[str, str]:
    """The group map in force for this vault's EFFECTIVE config, else empty.

    Gated twice: on the vault's algorithm version and kill switch (so a
    switch turned off takes effect before any refresh), and on the stored
    activation (so prepared groups of an unfinished upgrade are never read).
    """

    if not recurrence_active(vault):
        return {}
    return repository.recurrence_group_map()


def _facet_of(target_ref: Any) -> str | None:
    if isinstance(target_ref, Mapping) and target_ref.get("kind") == "facet_capability" and target_ref.get("facet_id"):
        return str(target_ref["facet_id"])
    return None


def _case_id(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class Episode:
    key: str
    attempt_id: str
    learning_object_id: str
    statement_normalized: str
    cause_scope: str
    facet: str | None
    first_created_at: str
    version_ids: tuple[str, ...]


class EpisodeIndex:
    """Statement classes over concrete episodes, by attempt."""

    def __init__(self, episodes: Sequence[Episode]) -> None:
        self.episodes = {episode.key: episode for episode in episodes}
        self.by_version_id: dict[str, str] = {}
        self.class_episodes: dict[str, list[Episode]] = {}
        self.by_attempt: dict[str, dict[str, list[Episode]]] = {}
        for episode in episodes:
            for version_id in episode.version_ids:
                self.by_version_id[version_id] = episode.key
            self.class_episodes.setdefault(episode.statement_normalized, []).append(episode)
            self.by_attempt.setdefault(episode.attempt_id, {}).setdefault(episode.statement_normalized, []).append(episode)
        for members in self.class_episodes.values():
            members.sort(key=lambda episode: (episode.first_created_at, episode.key))
        self.class_order = {
            statement: (members[0].first_created_at, members[0].key)
            for statement, members in self.class_episodes.items()
        }

    def episode(self, ref: str) -> Episode | None:
        key = self.by_version_id.get(ref, ref)
        return self.episodes.get(key)

    def classes_on(self, attempt_id: str) -> dict[str, list[Episode]]:
        return self.by_attempt.get(attempt_id, {})

    def representative(self, attempt_id: str, statement: str) -> str | None:
        members = self.classes_on(attempt_id).get(statement) or []
        return members[0].key if members else None

    def resolve_on(self, attempt_id: str, *, prefer: str | None, facet: str | None) -> tuple[str | None, str]:
        classes = self.classes_on(attempt_id)
        if not classes:
            return None, "no_hypotheses_on_attempt"
        if prefer is not None and prefer in classes:
            return prefer, "anchor_class"
        learner = [statement for statement, members in classes.items() if any(e.cause_scope == "learner_state" for e in members)]
        pool = sorted(learner or classes)
        if len(pool) == 1:
            return pool[0], "only_class"
        if facet:
            on_facet = [statement for statement in pool if any(e.facet == facet for e in classes[statement])]
            if len(on_facet) == 1:
                return on_facet[0], "facet_match"
        return None, "ambiguous_classes"


def load_episode_index(connection: Any) -> EpisodeIndex:
    rows = store.hypothesis_episode_rows(connection)
    version_ids: dict[str, list[str]] = {}
    for row in connection.execute("SELECT episode_key, id FROM causal_hypotheses ORDER BY episode_key, version, id"):
        version_ids.setdefault(str(row[0]), []).append(str(row[1]))
    episodes = [
        Episode(
            key=str(row["episode_key"]),
            attempt_id=str(row["attempt_id"]),
            learning_object_id=str(row["learning_object_id"]),
            statement_normalized=str(row["statement_normalized"]),
            cause_scope=str(row.get("cause_scope") or "unknown"),
            facet=_facet_of(row.get("target_ref")),
            first_created_at=str(row["first_created_at"]),
            version_ids=tuple(version_ids.get(str(row["episode_key"]), [])),
        )
        for row in rows
    ]
    return EpisodeIndex(episodes)


def claim_for_citation(proposal: Mapping[str, Any], citation: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """The pattern claim a validated citation came from.

    The stored proposal keeps only the claims that survived validation, so a
    citation's ``claim_index`` (its position before validation) may point past
    a dropped claim. The claim is the one that cites this attempt with this
    quote; the index breaks ties only when it names one of them.
    """

    claims = [claim for claim in proposal.get("pattern_claims") or [] if isinstance(claim, Mapping)]
    attempt_id = str(citation.get("attempt_id") or "")
    quote = str(citation.get("quote") or "")
    matching = [
        (index, claim)
        for index, claim in enumerate(claims)
        if any(
            isinstance(cited, Mapping)
            and str(cited.get("attempt_id") or "") == attempt_id
            and str(cited.get("quote") or "") == quote
            for cited in claim.get("cited") or []
        )
    ]
    if not matching:
        return None
    index = citation.get("claim_index")
    for position, claim in matching:
        if position == index:
            return claim
    refs = {str(claim.get("hypothesis_ref") or "") for _position, claim in matching}
    return matching[0][1] if len(refs) == 1 else None


def _primary_statement(event: Mapping[str, Any]) -> str | None:
    """The event's highest-weight cause (first on ties), normalized."""

    best: tuple[float, int] | None = None
    chosen: str | None = None
    for position, cause in enumerate(event.get("candidate_causes") or []):
        if not isinstance(cause, Mapping):
            continue
        statement = normalize_statement(str(cause.get("statement") or ""))
        if not statement:
            continue
        key = (-float(cause.get("prior_weight") or 0.0), position)
        if best is None or key < best:
            best, chosen = key, statement
    return chosen


def _continuing_class(index: "EpisodeIndex", proposal: Mapping[str, Any], attempt_id: str, episode_key: str) -> str | None:
    classes = index.classes_on(attempt_id)
    found: set[str] = set()
    for event in proposal.get("event_diagnoses") or []:
        if not isinstance(event, Mapping) or not event.get("prior_hypothesis_id"):
            continue
        continued = index.episode(str(event["prior_hypothesis_id"]))
        if continued is None or continued.key != episode_key:
            continue
        statement = _primary_statement(event)
        if statement is not None and statement in classes:
            found.add(statement)
    return next(iter(found)) if len(found) == 1 else None


def _cause_of(proposal: Mapping[str, Any], ref: str) -> tuple[str, str | None] | None:
    """(normalized statement, target facet) of ``cause:<event>:<cause>``."""

    parts = ref[len(CAUSE_REF_PREFIX):].split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        return None
    event_index, cause_index = int(parts[0]), int(parts[1])
    for event in proposal.get("event_diagnoses") or []:
        if not isinstance(event, Mapping) or int(event.get("event_index", -1)) != event_index:
            continue
        causes = [cause for cause in event.get("candidate_causes") or [] if isinstance(cause, Mapping)]
        if 0 <= cause_index < len(causes):
            statement = normalize_statement(str(causes[cause_index].get("statement") or ""))
            return (statement, _facet_of(causes[cause_index].get("target_ref"))) if statement else None
    return None


@dataclass
class _Build:
    index: EpisodeIndex
    edges: list[UnionEdge] = field(default_factory=list)
    reviews: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: (diagnosed attempt, cited attempt) -> resolved (anchor class, cited class, anchor episode, cited episode).
    citation_pairs: dict[tuple[str, str], list[tuple[str, str, str | None, str | None]]] = field(default_factory=dict)
    #: Episode-level labelled pairs (for B3): (left episode, right episode, verdict, judge, ref).
    labelled: list[dict[str, Any]] = field(default_factory=list)

    def review(self, case_kind: str, *, left: str | None, right: str | None, source: str | None,
               occurred_at: str | None, detail: Mapping[str, Any], blocking: tuple[str | None, str | None] = (None, None)) -> None:
        case_id = _case_id(case_kind, left, right, source, blocking)
        self.reviews.setdefault(
            case_id,
            {
                "id": case_id,
                "case_kind": case_kind,
                "left_ref": left,
                "right_ref": right,
                "blocking_left_ref": blocking[0],
                "blocking_right_ref": blocking[1],
                "source_ref": source,
                "occurred_at": occurred_at,
                "detail": dict(detail),
                "builder_version": BUILDER_VERSION,
            },
        )

    def edge(self, left_class: str, right_class: str, *, verdict: str, judge: str, source: str, ref: str,
             occurred_at: str, left_episode: str | None, right_episode: str | None) -> None:
        self.labelled.append(
            {
                "left_episode": left_episode, "right_episode": right_episode, "left_class": left_class,
                "right_class": right_class, "verdict": verdict, "judge": judge, "source": source, "ref": ref,
                "occurred_at": occurred_at,
            }
        )
        self.edges.append(
            UnionEdge(
                left=left_class, right=right_class, verdict=verdict, authority=AUTHORITY[judge], judge=judge,
                source=source, ref=ref, occurred_at=occurred_at, left_ref=left_episode, right_ref=right_episode,
            )
        )

    # -- one resolved citation ------------------------------------------------------

    def resolve_citation(
        self, diagnosis: Mapping[str, Any], citation: Mapping[str, Any]
    ) -> tuple[list[tuple[str, str, str | None, str | None]], str | None, tuple[str, str, str | None, str | None] | None]:
        """(class pairs the citation links, why it is unresolved, the attempt pair).

        The attempt pair is (the diagnosed attempt's class, the cited
        attempt's class, their episodes): what an attempt-level verdict on
        the same two answers (a card tap, an M1 import) is about.
        """

        attempt_id = str(diagnosis["attempt_id"])
        cited = str(citation.get("attempt_id") or "")
        proposal = diagnosis.get("proposal") or {}
        claim = claim_for_citation(proposal, citation)
        if claim is None:
            return [], "claim_not_found", None
        ref = str(claim.get("hypothesis_ref") or "")
        pairs: list[tuple[str, str, str | None, str | None]] = []
        if ref.startswith(CAUSE_REF_PREFIX):
            cause = _cause_of(proposal, ref)
            if cause is None:
                return [], "cause_ref_unknown", None
            anchor, facet = cause
            if anchor not in self.index.classes_on(attempt_id):
                return [], "cause_not_materialized", None
            anchor_episode = self.index.representative(attempt_id, anchor)
            own, own_episode = anchor, anchor_episode
        else:
            episode = self.index.episode(ref)
            if episode is None:
                return [], "hypothesis_ref_unknown", None
            anchor, facet, anchor_episode = episode.statement_normalized, episode.facet, episode.key
            # The event whose primary cause continues this prior hypothesis
            # (its ``prior_hypothesis_id``) names the diagnosed attempt's own
            # class exactly; otherwise fall back to the one-class rule.
            own = _continuing_class(self.index, proposal, attempt_id, episode.key)
            reason = "prior_hypothesis_id"
            if own is None:
                own, reason = self.index.resolve_on(attempt_id, prefer=anchor, facet=facet)
            if own is None:
                return [], f"diagnosed_attempt:{reason}", None
            own_episode = self.index.representative(attempt_id, own)
            pairs.append((own, anchor, own_episode, anchor_episode))
        target, reason = self.index.resolve_on(cited, prefer=anchor, facet=facet)
        if target is None:
            return pairs, f"cited_attempt:{reason}", None
        target_episode = self.index.representative(cited, target)
        pairs.append((anchor, target, anchor_episode, target_episode))
        return pairs, None, (own, target, own_episode, target_episode)


def _source_citations(build: _Build, diagnoses: Sequence[Mapping[str, Any]]) -> None:
    for diagnosis in diagnoses:
        for position, citation in enumerate(diagnosis.get("validated_citations") or []):
            cited = str(citation.get("attempt_id") or "")
            ref = f"citation:{diagnosis['id']}:{citation.get('claim_index')}:{cited}:{position}"
            pairs, reason, attempt_pair = build.resolve_citation(diagnosis, citation)
            if reason is not None:
                build.review(
                    "unresolved_link", left=str(diagnosis["attempt_id"]), right=cited, source=ref,
                    occurred_at=str(diagnosis.get("created_at") or ""), detail={"source": "citation", "reason": reason},
                )
            if attempt_pair is not None:
                build.citation_pairs.setdefault((str(diagnosis["attempt_id"]), cited), []).append(attempt_pair)
            for anchor, target, anchor_episode, target_episode in pairs:
                build.edge(
                    anchor, target, verdict="same", judge="diagnoser", source="citation", ref=ref,
                    occurred_at=str(diagnosis.get("created_at") or ""),
                    left_episode=anchor_episode, right_episode=target_episode,
                )


def _source_taps(build: _Build, connection: Any) -> None:
    for tap in store.not_same_mistake_taps(connection):
        diagnosis = store.diagnosis_with_citations(connection, str(tap["diagnosis_id"]))
        ref = f"tap:{tap['id']}"
        cited = str(tap.get("cited_attempt_id") or "")
        targeted: list[tuple[str, str, str | None, str | None]] = []
        reason = "diagnosis_missing" if diagnosis is None else "citation_not_found"
        for citation in (diagnosis or {}).get("validated_citations") or []:
            if str(citation.get("attempt_id") or "") != cited:
                continue
            _pairs, why, attempt_pair = build.resolve_citation(diagnosis, citation)  # type: ignore[arg-type]
            # The learner disowned the cited answer: this answer's cause and
            # the cited answer's are "different"; nothing else is implied.
            if attempt_pair is not None:
                targeted.append(attempt_pair)
            if why is not None:
                reason = why
        if not targeted:
            build.review(
                "unresolved_link", left=str(tap["attempt_id"]), right=cited, source=ref,
                occurred_at=str(tap.get("responded_at") or ""), detail={"source": "learner_card", "reason": reason or "no_cited_class"},
            )
            continue
        for anchor, target, anchor_episode, target_episode in targeted:
            build.edge(
                anchor, target, verdict="different", judge="learner_card", source="learner_card", ref=ref,
                occurred_at=str(tap.get("responded_at") or ""), left_episode=anchor_episode, right_episode=target_episode,
            )


def _source_judgments(build: _Build, connection: Any) -> None:
    rows = store.same_cause_judgments(connection)
    superseded = {str(row["supersedes_id"]) for row in rows if row.get("supersedes_id")}
    for row in rows:
        if str(row["id"]) in superseded:
            continue
        verdict = _VERDICTS.get(str(row.get("verdict") or ""))
        judge = str(row.get("judge") or "")
        if verdict is None or judge not in AUTHORITY:
            continue
        ref = f"judgment:{row['id']}"
        occurred = str(row.get("created_at") or "")
        left_kind, right_kind = row.get("left_kind"), row.get("right_kind")
        if left_kind == "hypothesis" and right_kind == "hypothesis":
            left, right = build.index.episode(str(row["left_id"])), build.index.episode(str(row["right_id"] or ""))
            if left is None or right is None:
                build.review("unresolved_link", left=str(row["left_id"]), right=row.get("right_id"), source=ref,
                             occurred_at=occurred, detail={"source": "judgment", "reason": "hypothesis_unknown", "judge": judge})
                continue
            build.edge(left.statement_normalized, right.statement_normalized, verdict=verdict, judge=judge,
                       source="judgment", ref=ref, occurred_at=occurred, left_episode=left.key, right_episode=right.key)
            continue
        if left_kind != "attempt" or right_kind != "attempt":
            continue  # planted subjects and other kinds never touch vault groups
        if judge in ("diagnoser", "learner_card"):
            # Read from their raw ledgers (receipts and card taps) instead.
            continue
        left_attempt, right_attempt = str(row["left_id"]), str(row["right_id"] or "")
        pairs = build.citation_pairs.get((left_attempt, right_attempt)) or [
            (target, anchor, target_episode, anchor_episode)
            for anchor, target, anchor_episode, target_episode in build.citation_pairs.get((right_attempt, left_attempt)) or []
        ]
        if not pairs:
            left_class, why = build.index.resolve_on(left_attempt, prefer=None, facet=None)
            right_class, why_right = (
                build.index.resolve_on(right_attempt, prefer=left_class, facet=None) if left_class else (None, why)
            )
            if left_class is None or right_class is None:
                build.review("unresolved_link", left=left_attempt, right=right_attempt, source=ref, occurred_at=occurred,
                             detail={"source": "judgment", "judge": judge, "reason": why if left_class is None else why_right})
                continue
            pairs = [(left_class, right_class, build.index.representative(left_attempt, left_class),
                      build.index.representative(right_attempt, right_class))]
        for left_class, right_class, left_episode, right_episode in pairs:
            build.edge(left_class, right_class, verdict=verdict, judge=judge, source="judgment", ref=ref,
                       occurred_at=occurred, left_episode=left_episode, right_episode=right_episode)


def _source_registry_disagreements(build: _Build, diagnoses: Sequence[Mapping[str, Any]]) -> None:
    """§3.5: the diagnoser's registry match vs the top-1 neighbour by embedding."""

    for diagnosis in diagnoses:
        retrieval = (diagnosis.get("retrieval") or {}).get("registry_retrieval") or {}
        matches = [row for row in retrieval.get("matches") or [] if isinstance(row, Mapping)]
        # A ranking over fewer than two records carries no neighbour signal
        # (mean-centring a single vector leaves zero).
        if not matches or int(retrieval.get("universe") or 0) < 2:
            continue
        top = min(matches, key=lambda row: (int(row.get("rank") or 10**6), str(row.get("registry_id") or "")))
        top_ref = f"{top.get('kind')}:{top.get('registry_id')}"
        for event in (diagnosis.get("proposal") or {}).get("event_diagnoses") or []:
            match = (event or {}).get("registry_match") if isinstance(event, Mapping) else None
            if not isinstance(match, Mapping):
                continue
            kind = str(match.get("kind") or "")
            if kind in ("durable", "candidate"):
                chosen = f"{kind}:{match.get('id')}"
                if chosen == top_ref:
                    continue
            elif kind != "new":
                continue
            else:
                chosen = "new"
            build.review(
                "registry_disagreement", left=chosen, right=top_ref, source=f"diagnosis:{diagnosis['id']}",
                occurred_at=str(diagnosis.get("created_at") or ""),
                detail={
                    "attempt_id": diagnosis["attempt_id"], "event_index": event.get("event_index"),
                    "top_score": top.get("score"), "model_id": retrieval.get("model_id"),
                },
            )


@dataclass
class GroupBuild:
    members: list[dict[str, Any]]
    reviews: list[dict[str, Any]]
    labelled: list[dict[str, Any]]
    group_count: int
    #: The union's inputs, for replaying it with a subset of sources (B3).
    classes: list[str] = field(default_factory=list)
    class_order: dict[str, Any] = field(default_factory=dict)
    edges: list[UnionEdge] = field(default_factory=list)


def compute_groups(connection: Any) -> GroupBuild:
    """The projection's rows from the ledgers (pure read)."""

    index = load_episode_index(connection)
    build = _Build(index=index)
    diagnoses = store.diagnoses_in_force(connection)
    _source_citations(build, diagnoses)
    _source_taps(build, connection)
    _source_judgments(build, connection)
    _source_registry_disagreements(build, diagnoses)
    result = union_with_refusals(index.class_episodes.keys(), build.edges, order=index.class_order)
    for refusal in result.refused:
        build.review(
            "refused_union", left=refusal.edge.left_ref or refusal.edge.left, right=refusal.edge.right_ref or refusal.edge.right,
            source=refusal.edge.ref, occurred_at=refusal.edge.occurred_at,
            blocking=(refusal.blocking.left_ref or refusal.blocking.left, refusal.blocking.right_ref or refusal.blocking.right),
            detail={
                "edge_judge": refusal.edge.judge, "edge_classes": [refusal.edge.left, refusal.edge.right],
                "blocking_judge": refusal.blocking.judge, "blocking_ref": refusal.blocking.ref,
                "blocking_classes": [refusal.blocking.left, refusal.blocking.right],
            },
        )
    for conflict in result.self_conflicts:
        build.review(
            "exact_key_conflict", left=conflict.left_ref, right=conflict.right_ref, source=conflict.ref,
            occurred_at=conflict.occurred_at, detail={"class": conflict.left, "judge": conflict.judge},
        )
    members: list[dict[str, Any]] = []
    group_count = 0
    for root, classes in result.components().items():
        if len(classes) < 2:
            continue
        group_count += 1
        key = group_key_for(root)
        root_episode = index.class_episodes[root][0].key
        for statement in classes:
            join = result.joined_by.get(statement)
            for position, episode in enumerate(index.class_episodes[statement]):
                if statement == root and position == 0:
                    joined, joined_ref, judge = "root", None, None
                elif position == 0 and join is not None:
                    joined = "citation" if join.source == "citation" else "judgment"
                    joined_ref, judge = join.ref, join.judge
                else:
                    joined, joined_ref, judge = "exact_key", None, None
                members.append(
                    {
                        "episode_key": episode.key,
                        "statement_normalized": statement,
                        "group_key": key,
                        "root_episode_key": root_episode,
                        "class_count": len(classes),
                        "joined_by": joined,
                        "joined_by_ref": joined_ref,
                        "judge": judge,
                        "builder_version": BUILDER_VERSION,
                    }
                )
    members.sort(key=lambda row: row["episode_key"])
    reviews = sorted(build.reviews.values(), key=lambda row: (row["case_kind"], str(row["occurred_at"] or ""), row["id"]))
    return GroupBuild(
        members=members, reviews=reviews, labelled=build.labelled, group_count=group_count,
        classes=sorted(index.class_episodes), class_order=dict(index.class_order), edges=list(build.edges),
    )


def input_fingerprint(connection: Any, *, active: bool) -> str:
    parts = [BUILDER_VERSION, bool(active), store.input_fingerprint_parts(connection)]
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode("utf-8")).hexdigest()


def _write(repository: Repository, *, active: bool, force: bool, prepare: bool = False) -> dict[str, Any]:
    if not active and not prepare:
        # Off (below the successor, or the kill switch): an empty projection,
        # so every recurrence key is the exact statement again. Read first:
        # an already-empty projection costs no write transaction.
        with repository.connection() as connection:
            present = store.projection_present(connection)
        if not present:
            return {"rebuilt": False, "active": False, "group_count": 0, "member_count": 0, "review_count": 0}
        with repository.atomic():
            cleared = store.clear_recurrence_projection(repository.connection())
        return {"rebuilt": cleared, "active": False, "group_count": 0, "member_count": 0, "review_count": 0}
    with repository.atomic():
        connection = repository.connection()
        fingerprint = input_fingerprint(connection, active=active)
        state = store.recurrence_state(connection)
        if not force and state is not None and state["input_fingerprint"] == fingerprint:
            return {"rebuilt": False, "active": active, **_counts(state)}
        build = compute_groups(connection)
        counts = {
            "group_count": build.group_count,
            "member_count": len(build.members),
            "review_count": len(build.reviews),
        }
        store.replace_recurrence_projection(
            connection,
            members=build.members,
            reviews=build.reviews,
            state={"input_fingerprint": fingerprint, "builder_version": BUILDER_VERSION, "active": active, **counts},
        )
    return {"rebuilt": True, "active": active, "prepared": prepare and not active, **counts}


def _counts(state: Mapping[str, Any]) -> dict[str, int]:
    return {key: int(state.get(key) or 0) for key in ("group_count", "member_count", "review_count")}


def refresh_recurrence_groups(vault: LoadedVault, repository: Repository, *, force: bool = False) -> dict[str, Any]:
    """Recompute the projection when its inputs (or the switch) changed.

    Safe to call often: an unchanged fingerprint costs a few counter queries.
    A schema without the projection tables (a historical copy attached
    without migrations) is left alone.
    """

    with repository.connection() as connection:
        if not _has_projection(connection):
            return {"rebuilt": False, "active": False, "skipped": "no_projection_tables"}
    return _write(repository, active=recurrence_active(vault), force=force)


def prepare_recurrence_groups(repository: Repository) -> dict[str, Any]:
    """Build the groups as PREPARED (not in force): the upgrade's pre-switch step."""

    with repository.connection() as connection:
        if not _has_projection(connection):
            return {"rebuilt": False, "active": False, "skipped": "no_projection_tables"}
    return _write(repository, active=False, force=True, prepare=True)


def activate_recurrence_groups(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """Put prepared groups in force once the vault's config switch has landed.

    A cheap flip when the inputs are unchanged since preparation; otherwise a
    full rebuild. Does nothing (and the map stays empty) unless the vault's
    effective config makes recurrence active.
    """

    if not recurrence_active(vault):
        return refresh_recurrence_groups(vault, repository)
    with repository.connection() as connection:
        if not _has_projection(connection):
            return {"rebuilt": False, "active": False, "skipped": "no_projection_tables"}
    with repository.atomic():
        connection = repository.connection()
        flipped = store.activate_prepared_projection(
            connection,
            prepared_fingerprint=input_fingerprint(connection, active=False),
            active_fingerprint=input_fingerprint(connection, active=True),
        )
        state = store.recurrence_state(connection) if flipped else None
    if flipped and state is not None:
        return {"rebuilt": False, "active": True, "activated": "prepared", **_counts(state)}
    return {**refresh_recurrence_groups(vault, repository, force=True), "activated": "rebuilt"}


def _has_projection(connection: Any) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'hypothesis_recurrence_state'"
    ).fetchone() is not None


__all__ = [
    "AUTHORITY",
    "activate_recurrence_groups",
    "active_group_map",
    "BUILDER_VERSION",
    "EpisodeIndex",
    "GroupBuild",
    "claim_for_citation",
    "compute_groups",
    "input_fingerprint",
    "load_episode_index",
    "prepare_recurrence_groups",
    "recurrence_active",
    "refresh_recurrence_groups",
]
