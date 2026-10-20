"""The single intent control (spec §5.1, §5.2): choose, preview, apply.

One segmented control on an LO, a subject, a source, an item (and, from DL3,
a capture). Each choice creates or versions the control's **own** commitment
for that scope through ``learnloop.curriculum.commitments`` (``provenance =
{"via": "intent_control", "scope": …}``). A later choice on the same scope
versions or re-disposes that commitment; "Check once" creates a fresh
``test_me_later`` commitment (its date is counted from its creation). Request
commitments other paths created (capture adoption, the Reader's presets and
written questions, Reader follow-ups) are never versioned or re-disposed.

The consequence line is computed by the same resolution the queue uses: the
choice is resolved as a virtual newest commitment and every covered item is
compared before and after (:func:`preview`), so the line names exactly the
settings it replaces. The projected cost is "about N min/day of reviews":
§6.4's estimate of each covered item with memory state, at the choice's
recall target (§5.3), as §6.3's review-load projection counts them.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from learnloop.clock import Clock, SystemClock, utc_now_iso
from learnloop.curriculum import commitments as C
from learnloop.ids import new_ulid
from learnloop.scheduling.intent.model import (
    CHOICE_DISPOSITION,
    CHOICE_LABEL,
    CHOICE_PRESET,
    CHOICES,
    INTENT_CONTROL_VIA,
    ChoiceStamp,
    CommitmentSnapshot,
)
from learnloop.scheduling.intent.resolution import ItemIntent, Resolution, load_snapshots

#: What each choice does, in plain words (§5.2's table).
CHOICE_DOES: dict[str, str] = {
    "master": "new and harder material keeps coming, and reviews keep it at 92%",
    "learn": "new material until it's fluent, reviews at 90%",
    "keep": "reviews only, at 85%; no new or harder material",
    "light_touch": "occasional reviews at 80%; lapses are fine, and it's left out of re-entry",
    "check_once": "one check on your own after a delay, then nothing until you choose again",
    "reference": "kept and searchable, never served",
    "pause": "not served until you resume; your history is kept",
    "let_go": "not served; your history is kept",
}


#: The consequence line's first part, by choice ("Pause 12 topics").
CHOICE_PHRASE: dict[str, str] = {
    "master": "Master {what}",
    "learn": "Learn {what}",
    "keep": "Keep {what}",
    "light_touch": "Light touch on {what}",
    "check_once": "Check {what} once",
    "reference": "Keep {what} as reference",
    "pause": "Pause {what}",
    "let_go": "Let go of {what}",
}


#: ``(choice, {item id: resolved intent after the choice}) -> (minutes/day or None, label)``.
CostFunction = Callable[[str, Mapping[str, ItemIntent]], tuple[float | None, str]]


class IntentControlError(ValueError):
    """A choice the control cannot apply (unknown scope, nothing to act on)."""


@dataclass(frozen=True)
class Scope:
    kind: str  # learning_object | practice_item | subject | source
    id: str

    def as_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "id": self.id}


@dataclass(frozen=True)
class ScopeContents:
    """What a scope covers: its LO targets (or its one item) and every item."""

    scope: Scope
    title: str
    learning_object_ids: tuple[str, ...]
    item_ids: tuple[str, ...]

    def targets(self) -> list[dict[str, str]]:
        if self.scope.kind == "practice_item":
            return [{"target_kind": "legacy_practice_item", "target_ref": self.scope.id, "role": "required"}]
        return [
            {"target_kind": "learning_object", "target_ref": lo_id, "role": "required"}
            for lo_id in self.learning_object_ids
        ]


def scope_contents(vault: Any, repository: Any, scope: Scope) -> ScopeContents:
    """A subject or source fans out to its active LOs (§5.1)."""

    if scope.kind == "practice_item":
        item = vault.practice_items.get(scope.id)
        if item is None:
            raise IntentControlError(f"unknown practice item: {scope.id}")
        lo_id = getattr(item, "learning_object_id", None)
        return ScopeContents(scope, _item_title(item), (str(lo_id),) if lo_id else (), (scope.id,))
    if scope.kind == "learning_object":
        lo = vault.learning_objects.get(scope.id)
        if lo is None:
            raise IntentControlError(f"unknown learning object: {scope.id}")
        los: list[str] = [scope.id]
        title = lo.title
    elif scope.kind == "subject":
        los = sorted(
            lo.id for lo in vault.learning_objects.values() if scope.id in (lo.subjects or []) and lo.status == "active"
        )
        title = scope.id.replace("-", " ").replace("_", " ")
    elif scope.kind == "source":
        from learnloop.reader.recap import source_learning_objects

        found: set[str] = set()
        for extraction_id in _source_extractions(repository, scope.id):
            found.update(source_learning_objects(vault, repository, extraction_id))
        los = sorted(
            lo_id
            for lo_id in found
            if lo_id in vault.learning_objects and vault.learning_objects[lo_id].status == "active"
        )
        title = "this source"
    else:
        raise IntentControlError(f"unknown scope kind: {scope.kind}")
    if not los:
        raise IntentControlError("nothing to set here: no active topic")
    lo_set = set(los)
    items = sorted(
        item.id for item in vault.practice_items.values() if getattr(item, "learning_object_id", None) in lo_set
    )
    return ScopeContents(scope, title, tuple(los), tuple(items))


def _source_extractions(repository: Any, source_id_or_extraction: str) -> list[str]:
    """A source scope's readings: the extraction itself, or every reading of
    the source's current revision (the library card names the source)."""

    if repository.get_extraction_run(source_id_or_extraction) is not None:
        return [source_id_or_extraction]
    artifact = repository.get_source_artifact(source_id_or_extraction) or {}
    revision = artifact.get("current_revision_id")
    if not revision:
        return []
    return [str(run["id"]) for run in repository.extraction_runs_for_revision(str(revision))]


def _item_title(item: Any) -> str:
    prompt = str(getattr(item, "prompt", "") or "").strip().splitlines()
    text = prompt[0] if prompt else item.id
    return text if len(text) <= 60 else text[:57] + "…"


def own_commitments(snapshots: Sequence[CommitmentSnapshot], scope: Scope) -> list[CommitmentSnapshot]:
    """The control's commitments for exactly this scope, newest choice last."""

    found = [
        snapshot
        for snapshot in snapshots
        if snapshot.via == INTENT_CONTROL_VIA
        and not snapshot.retired
        and isinstance(snapshot.scope, Mapping)
        and snapshot.scope.get("kind") == scope.kind
        and str(snapshot.scope.get("id")) == scope.id
    ]
    return sorted(found, key=lambda s: (s.choice.at, s.choice.row_id))


def _all_snapshots(repository: Any) -> list[CommitmentSnapshot]:
    with repository.connection() as connection:
        return load_snapshots(connection)


# -- preview ----------------------------------------------------------------


@dataclass(frozen=True)
class Preview:
    choice: str
    label: str
    does: str
    consequence: str
    replaced_topics: int
    replaced_items: int
    replaced_commitment_ids: tuple[str, ...]
    served_item_ids: tuple[str, ...]
    excluded_item_ids: tuple[str, ...]
    cost_minutes_per_day: float | None
    cost_label: str
    after: Mapping[str, ItemIntent] = field(default_factory=dict, compare=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "choice": self.choice,
            "label": self.label,
            "does": self.does,
            "consequence": self.consequence,
            "replaced_topics": self.replaced_topics,
            "replaced_items": self.replaced_items,
            "cost_minutes_per_day": None if self.cost_minutes_per_day is None else round(self.cost_minutes_per_day, 1),
            "cost_label": self.cost_label,
            "served_count": len(self.served_item_ids),
            "excluded_count": len(self.excluded_item_ids),
        }


def _virtual(
    contents: ScopeContents, choice: str, own: Sequence[CommitmentSnapshot], *, now_iso: str
) -> CommitmentSnapshot:
    """The choice as a virtual newest commitment (the very rule the queue uses)."""

    stamp = ChoiceStamp(now_iso, "~virtual")
    items = frozenset(contents.item_ids) if contents.scope.kind == "practice_item" else frozenset()
    los = frozenset() if contents.scope.kind == "practice_item" else frozenset(contents.learning_object_ids)
    base = dict(
        choice=stamp,
        retired=False,
        item_targets=items,
        learning_object_targets=los,
        via=INTENT_CONTROL_VIA,
        provenance={"via": INTENT_CONTROL_VIA, "scope": contents.scope.as_dict(), "choice": choice},
    )
    depth_own = next((s for s in reversed(own) if s.action == "help_me_remember"), None)
    if choice in CHOICE_PRESET:
        if depth_own is not None:
            return replace(depth_own, depth_preset=CHOICE_PRESET[choice], disposition="active", **base)
        return CommitmentSnapshot(
            id="~virtual", action="help_me_remember", created_at=now_iso, depth_preset=CHOICE_PRESET[choice],
            disposition="active", **base,
        )
    if choice == "check_once":
        return CommitmentSnapshot(
            id="~virtual", action="test_me_later", created_at=now_iso,
            depth_preset=depth_own.depth_preset if depth_own is not None else "keep_in_touch",
            disposition="one_check_pending", **base,
        )
    if choice in CHOICE_DISPOSITION:
        latest = own[-1] if own else None
        if latest is not None:
            return replace(latest, disposition=CHOICE_DISPOSITION[choice], **base)
        return CommitmentSnapshot(
            id="~virtual", action="help_me_remember", created_at=now_iso, depth_preset="remember_key_ideas",
            disposition=CHOICE_DISPOSITION[choice], **base,
        )
    raise IntentControlError(f"unknown choice: {choice}")


def _plural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def _subject_phrase(contents: ScopeContents) -> str:
    if contents.scope.kind == "practice_item":
        return "this item"
    if contents.scope.kind == "learning_object":
        return "this topic"
    return _plural(len(contents.learning_object_ids), "topic")


def preview(
    vault: Any,
    repository: Any,
    scope: Scope,
    choice: str,
    *,
    clock: Clock | None = None,
    snapshots: Sequence[CommitmentSnapshot] | None = None,
    contents: ScopeContents | None = None,
    cost: CostFunction | None = None,
) -> Preview:
    if choice not in CHOICES:
        raise IntentControlError(f"unknown choice: {choice}")
    contents = contents or scope_contents(vault, repository, scope)
    snapshots = list(snapshots) if snapshots is not None else _all_snapshots(repository)
    targets = dict(vault.config.intent.recall_targets)
    current = Resolution(snapshots, targets)
    now_iso = utc_now_iso(clock)
    virtual = _virtual(contents, choice, own_commitments(snapshots, scope), now_iso=now_iso)
    after_resolution = current.with_snapshot(virtual)
    item_los = {
        item_id: str(getattr(vault.practice_items[item_id], "learning_object_id", "") or "")
        for item_id in contents.item_ids
        if item_id in vault.practice_items
    }
    # The scope's own earlier settings are what the choice changes, not what
    # it "replaces elsewhere": the line names the other settings it overrides.
    own_ids = {snapshot.id for snapshot in own_commitments(snapshots, scope)}
    replaced_ids: set[str] = set()
    replaced_topics: set[str] = set()
    replaced_items: set[str] = set()
    after: dict[str, ItemIntent] = {}
    served: list[str] = []
    excluded: list[str] = []
    for item_id, lo_id in item_los.items():
        before = current.for_item(item_id, lo_id)
        now_intent = after_resolution.for_item(item_id, lo_id)
        after[item_id] = now_intent
        (excluded if now_intent.excluded else served).append(item_id)
        if before.decided_by is None or before.decided_by == virtual.id or before.decided_by in own_ids:
            continue
        if now_intent.decided_by != virtual.id:
            continue
        replaced_ids.add(before.decided_by)
        if before.level == "practice_item":
            replaced_items.add(item_id)
        else:
            replaced_topics.add(lo_id)
    label = CHOICE_LABEL[choice]
    parts = [CHOICE_PHRASE[choice].format(what=_subject_phrase(contents))]
    if replaced_topics or replaced_items:
        named = []
        if replaced_topics:
            named.append(_plural(len(replaced_topics), "topic"))
        if replaced_items:
            named.append(_plural(len(replaced_items), "item"))
        parts.append("replaces your earlier setting on " + " and ".join(named))
    does = CHOICE_DOES[choice]
    if choice == "check_once":
        days = int(vault.config.capture.test_me_later_days)
        does = f"one check on your own in {days} day{'' if days == 1 else 's'}, then nothing until you choose again"
    cost_minutes, cost_label = cost(choice, after) if cost is not None else (None, "")
    return Preview(
        choice=choice,
        label=label,
        does=does,
        consequence=" · ".join(parts),
        replaced_topics=len(replaced_topics),
        replaced_items=len(replaced_items),
        replaced_commitment_ids=tuple(sorted(replaced_ids)),
        served_item_ids=tuple(served),
        excluded_item_ids=tuple(excluded),
        cost_minutes_per_day=cost_minutes,
        cost_label=cost_label,
        after=after,
    )


# -- the current setting ---------------------------------------------------------


def current_choice(vault: Any, repository: Any, contents: ScopeContents, snapshots: Sequence[CommitmentSnapshot]) -> dict[str, Any]:
    """What the scope is set to now: its own commitment's choice, else the
    resolved intent of an LO or item (a request or a broader choice)."""

    from learnloop.scheduling.intent.model import choice_for

    own = own_commitments(snapshots, contents.scope)
    resolution = Resolution(snapshots, dict(vault.config.intent.recall_targets))
    if contents.scope.kind == "practice_item":
        resolved = resolution.for_item(contents.scope.id, contents.learning_object_ids[0] if contents.learning_object_ids else None)
    elif contents.scope.kind == "learning_object":
        resolved = resolution.for_learning_object(contents.scope.id)
    else:
        resolved = None
    latest = own[-1] if own else None
    if latest is not None and (resolved is None or resolved.decided_by == latest.id):
        choice = choice_for(latest.action, latest.depth_preset, latest.disposition)
        source = "this control"
    elif resolved is not None and not resolved.uncommitted:
        choice = resolved.choice
        source = "a broader or earlier setting" if resolved.decider_intent_control else "something you asked for"
    else:
        choice = "uncommitted"
        source = None
    deadline = None
    depth_own = next((s for s in reversed(own) if s.action == "help_me_remember"), None)
    if depth_own is not None and depth_own.goal_id:
        goal = next((g for g in vault.goals if g.id == depth_own.goal_id), None)
        if goal is not None and goal.status == "active" and goal.due_at:
            deadline = {"goal_id": goal.id, "due_at": goal.due_at}
    return {
        "choice": choice,
        "label": CHOICE_LABEL.get(choice, choice),
        "source": source,
        "deadline": deadline,
        "can_add_deadline": depth_own is not None and depth_own.disposition == "active",
    }


def describe(
    vault: Any, repository: Any, scope: Scope, *, clock: Clock | None = None, cost: CostFunction | None = None
) -> dict[str, Any]:
    """The control's whole view: the current setting and every choice's preview.

    ``cost`` is the projected-cost function (``learnloop.daily_plan.intent_cost``,
    injected by the caller: the plan's estimator and review-load projection
    live above this package)."""

    contents = scope_contents(vault, repository, scope)
    snapshots = _all_snapshots(repository)
    return {
        "scope": scope.as_dict(),
        "title": contents.title,
        "topics": len(contents.learning_object_ids),
        "items": len(contents.item_ids),
        "current": current_choice(vault, repository, contents, snapshots),
        "choices": [
            preview(
                vault, repository, scope, choice, clock=clock, snapshots=snapshots, contents=contents,
                cost=cost,
            ).as_dict()
            for choice in CHOICES
        ],
    }


# -- apply -------------------------------------------------------------------


@dataclass(frozen=True)
class Applied:
    choice: str
    commitment_id: str
    created: bool
    preview: Preview

    def as_dict(self) -> dict[str, Any]:
        return {"choice": self.choice, "commitment_id": self.commitment_id, "created": self.created,
                "preview": self.preview.as_dict()}


def apply_choice(
    vault: Any, repository: Any, scope: Scope, choice: str, *, clock: Clock | None = None
) -> Applied:
    """Write the choice (§5.1): create or version the scope's own commitment,
    or re-dispose it; "Check once" creates a fresh ``test_me_later``."""

    if choice not in CHOICES:
        raise IntentControlError(f"unknown choice: {choice}")
    contents = scope_contents(vault, repository, scope)
    snapshots = _all_snapshots(repository)
    shown = preview(vault, repository, scope, choice, clock=clock, snapshots=snapshots, contents=contents)
    own = own_commitments(snapshots, scope)
    provenance = {"via": INTENT_CONTROL_VIA, "scope": scope.as_dict(), "choice": choice}
    intent_text = f"{CHOICE_LABEL[choice]}: {contents.title}"
    targets = contents.targets()
    depth_own = next((s for s in reversed(own) if s.action == "help_me_remember"), None)
    created = False
    with repository.atomic():
        if choice in CHOICE_PRESET:
            preset = CHOICE_PRESET[choice]
            if depth_own is None:
                commitment = C.create_commitment(
                    repository, action="help_me_remember", intent_text=intent_text, targets=targets,
                    depth_preset=preset, client_idempotency_key=f"intent_control:{new_ulid()}",
                    reason="intent_control", provenance=provenance, clock=clock,
                )
                commitment_id, created = commitment.id, True
            else:
                commitment_id = depth_own.id
                head = C.resolve_head(repository, commitment_id)
                current_targets = sorted((t.target_kind, t.target_ref) for t in head.targets)
                wanted = sorted((t["target_kind"], t["target_ref"]) for t in targets)
                if head.depth_preset != preset or current_targets != wanted:
                    C.append_commitment_version(
                        repository, commitment_id=commitment_id, targets=targets, depth_preset=preset,
                        intent_text=intent_text, change_reason="intent_control", clock=clock,
                    )
                # Choosing again is a new choice (§5.3), and it resumes.
                C.change_disposition(repository, commitment_id=commitment_id, disposition="active", clock=clock)
        elif choice == "check_once":
            commitment = C.create_commitment(
                repository, action="test_me_later", intent_text=intent_text, targets=targets,
                depth_preset=depth_own.depth_preset if depth_own is not None else "keep_in_touch",
                client_idempotency_key=f"intent_control:{new_ulid()}", reason="intent_control",
                provenance=provenance, clock=clock,
            )
            commitment_id, created = commitment.id, True
        else:
            disposition = CHOICE_DISPOSITION[choice]
            latest = own[-1] if own else None
            if latest is None:
                commitment = C.create_commitment(
                    repository, action="help_me_remember", intent_text=intent_text, targets=targets,
                    depth_preset="remember_key_ideas", client_idempotency_key=f"intent_control:{new_ulid()}",
                    reason="intent_control", provenance=provenance, clock=clock,
                )
                commitment_id, created = commitment.id, True
            else:
                commitment_id = latest.id
                if contents.scope.kind in ("subject", "source"):
                    head = C.resolve_head(repository, commitment_id)
                    current_targets = sorted((t.target_kind, t.target_ref) for t in head.targets)
                    wanted = sorted((t["target_kind"], t["target_ref"]) for t in targets)
                    if current_targets != wanted:
                        C.append_commitment_version(
                            repository, commitment_id=commitment_id, targets=targets,
                            change_reason="intent_control", clock=clock,
                        )
            C.change_disposition(repository, commitment_id=commitment_id, disposition=disposition, clock=clock)
    repository.bump_queue_revision(clock=clock)
    return Applied(choice=choice, commitment_id=commitment_id, created=created, preview=shown)


__all__ = [
    "Applied",
    "CHOICE_DOES",
    "CostFunction",
    "IntentControlError",
    "Preview",
    "Scope",
    "ScopeContents",
    "apply_choice",
    "current_choice",
    "describe",
    "own_commitments",
    "preview",
    "scope_contents",
]
