"""What a prediction was about: its target, serialized canonically and hashed (EP spec §7.7.2, §7.7.4).

A forecast is scorable later only if its target can be named exactly: the members it is about (an item at a
content revision, a learning object, a facet, a surface group and where that grouping came from), the unit of the
outcome, the action it is conditional on, its horizon and anchor, and the versions of the event definition and of
the resolver that will label it. :class:`PredictionTarget` holds those, and ``target_hash`` is the sha256 of its
canonical JSON.

The canonical form never depends on construction order (members are sorted by every field, so two lists of the
same members hash alike, and a repeated member is refused rather than silently collapsed) and holds no display
text: a title or statement can be edited without changing what was predicted, so none is accepted. Every value is
a string or null, so no float formatting reaches the hash.

Dependency-light by design: the standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

TARGET_SCHEMA = "prediction_target/1"

#: The member kinds a target names. A kind outside these is refused: a new one is a schema change.
MEMBER_ITEM = "item"
MEMBER_LEARNING_OBJECT = "learning_object"
MEMBER_FACET = "facet"
MEMBER_SURFACE_GROUP = "surface_group"
MEMBER_KINDS = (MEMBER_ITEM, MEMBER_LEARNING_OBJECT, MEMBER_FACET, MEMBER_SURFACE_GROUP)


def _text(value: Any, name: str, *, optional: bool = True) -> str | None:
    if value is None:
        if optional:
            return None
        raise ValueError(f"{name} is required")
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string, not {type(value).__name__}")
    if not optional and not value:
        raise ValueError(f"{name} is required")
    return value


@dataclass(frozen=True)
class TargetMember:
    """One member: its kind and id, the revision it was predicted at (an item's content hash), and the source of
    its identity where that can differ (a surface-group key's: authored, or derived from the item)."""

    kind: str
    id: str
    revision: str | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in MEMBER_KINDS:
            raise ValueError(f"unknown target member kind {self.kind!r}")
        _text(self.id, "member id", optional=False)
        _text(self.revision, "member revision")
        _text(self.source, "member source")

    def sort_key(self) -> tuple[str, str, str, str]:
        # None sorts before every string and differs from "": the pair (flag, text) keeps them apart.
        return (self.kind, self.id, "" if self.revision is None else "\x01" + self.revision,
                "" if self.source is None else "\x01" + self.source)

    def to_dict(self) -> dict[str, str | None]:
        return {"kind": self.kind, "id": self.id, "revision": self.revision, "source": self.source}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "TargetMember":
        return cls(raw["kind"], raw["id"], raw.get("revision"), raw.get("source"))


@dataclass(frozen=True)
class PredictionTarget:
    """What a forecast is about (module docstring). ``members`` is held in canonical order."""

    kind: str
    members: tuple[TargetMember, ...]
    unit: str
    event_version: str
    resolver_version: str
    action_kind: str | None = None
    action_id: str | None = None
    horizon_kind: str | None = None
    horizon: str | None = None
    anchor_kind: str | None = None
    anchor_id: str | None = None
    schema: str = TARGET_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != TARGET_SCHEMA:
            raise ValueError(f"unsupported target schema {self.schema!r}")
        for name in ("kind", "unit", "event_version", "resolver_version"):
            _text(getattr(self, name), name, optional=False)
        for name in ("action_kind", "action_id", "horizon_kind", "horizon", "anchor_kind", "anchor_id"):
            _text(getattr(self, name), name)
        members = tuple(self.members)
        if not members:
            raise ValueError("a target names at least one member")
        if any(not isinstance(member, TargetMember) for member in members):
            raise TypeError("members must be TargetMember values")
        ordered = tuple(sorted(members, key=TargetMember.sort_key))
        if len(set(ordered)) != len(ordered):
            raise ValueError("a target member is repeated")
        object.__setattr__(self, "members", ordered)

    def to_dict(self) -> dict[str, Any]:
        """The canonical form: every field, members in canonical order."""

        return {
            "schema": self.schema,
            "kind": self.kind,
            "members": [member.to_dict() for member in self.members],
            "unit": self.unit,
            "action": {"kind": self.action_kind, "id": self.action_id},
            "horizon": {"kind": self.horizon_kind, "value": self.horizon},
            "anchor": {"kind": self.anchor_kind, "id": self.anchor_id},
            "event_version": self.event_version,
            "resolver_version": self.resolver_version,
        }

    def canonical_json(self) -> str:
        """Sorted keys, compact separators, UTF-8 text kept as is: the bytes ``target_hash`` hashes."""

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def target_hash(self) -> str:
        """``sha256:<hex>`` of :meth:`canonical_json` (a pinned identity, ``tests/identity_pins_helpers.py``)."""

        return "sha256:" + hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "PredictionTarget":
        if raw.get("schema") != TARGET_SCHEMA:
            raise ValueError(f"unsupported target schema {raw.get('schema')!r}")
        action, horizon, anchor = raw.get("action") or {}, raw.get("horizon") or {}, raw.get("anchor") or {}
        return cls(
            kind=raw["kind"],
            members=tuple(TargetMember.from_dict(entry) for entry in raw["members"]),
            unit=raw["unit"],
            event_version=raw["event_version"],
            resolver_version=raw["resolver_version"],
            action_kind=action.get("kind"),
            action_id=action.get("id"),
            horizon_kind=horizon.get("kind"),
            horizon=horizon.get("value"),
            anchor_kind=anchor.get("kind"),
            anchor_id=anchor.get("id"),
            schema=raw["schema"],
        )

    @classmethod
    def from_json(cls, text: str) -> "PredictionTarget":
        return cls.from_dict(json.loads(text))


__all__ = ["MEMBER_KINDS", "PredictionTarget", "TARGET_SCHEMA", "TargetMember"]
