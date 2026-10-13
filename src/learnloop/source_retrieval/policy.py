"""Retrieval policies: what a caller's context may receive (spec_source_practice_and_probes_v1 §5).

The caller's server-side context decides what may be retrieved, never a
model's arguments (SC2). This module is pure: :class:`CallerContext` names
where a call comes from (built on the server by ``learnloop.instructional``),
and :func:`derive_policy` maps it to one of the four learner-facing policies
the Reader spec defines (its §7.2): ``reading``, ``assisted_practice``,
``post_attempt`` and ``cold_attempt``. ``authoring`` is not a policy any caller
can request; S1's verifier builds that scope itself.

It lives here, below the service, so ``find_sources`` and ``compare_sources``
can derive and assert a policy without importing the service (SC12).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Mapping

RetrievalPolicy = Literal["reading", "assisted_practice", "post_attempt", "cold_attempt"]
POLICIES: tuple[str, ...] = ("reading", "assisted_practice", "post_attempt", "cold_attempt")
#: Caller kinds (§5.2). ``code`` is a server-side caller with no model in the
#: loop (the plan, S2b, the Reader's UI); ``agent`` is an external agent.
CALLER_KINDS: tuple[str, ...] = ("tutor", "plan", "reader", "need", "router", "agent", "harvest",
                                 "learner", "dl3_box", "code")
#: Tutor contexts bound to a practice item.
ITEM_BOUND_CONTEXTS = frozenset({"practice", "feedback"})


class PolicyRefused(ValueError):
    """A request the caller's context does not allow (G2)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CallerContext:
    """Where a call comes from, built on the server (never from arguments).

    ``context`` is the tutor's question context when there is one
    (``practice``, ``feedback``, ``library``, ``reader``). ``cold`` is true
    while a cold administration of ``item_id`` is open, or while the item is
    reserved for a held-out exam (``notes`` then names ``exam_reserved``). ``window_open`` says
    whether the item's attempt window is still open (a redo, guided redo or
    retry is possible); None when no item is bound.
    """

    kind: str
    ref: str | None = None
    context: str | None = None
    item_id: str | None = None
    attempt_id: str | None = None
    learning_object_ids: tuple[str, ...] = ()
    cold: bool = False
    window_open: bool | None = None
    post_attempt_requested: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["learning_object_ids"] = list(self.learning_object_ids)
        value["notes"] = list(self.notes)
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CallerContext":
        return cls(
            kind=str(value["kind"]), ref=value.get("ref"), context=value.get("context"),
            item_id=value.get("item_id"), attempt_id=value.get("attempt_id"),
            learning_object_ids=tuple(value.get("learning_object_ids") or ()),
            cold=bool(value.get("cold")), window_open=value.get("window_open"),
            post_attempt_requested=bool(value.get("post_attempt_requested")),
            notes=tuple(value.get("notes") or ()),
        )


def derive_policy(caller: CallerContext) -> tuple[str, str]:
    """``(policy, how it was derived)`` for ``caller`` (§5.2)."""

    if caller.cold:
        if "exam_reserved" in caller.notes:
            return "cold_attempt", "the item is reserved for a held-out exam"
        return "cold_attempt", "a cold administration is open for this item"
    if caller.item_id is not None and (caller.context in ITEM_BOUND_CONTEXTS or caller.post_attempt_requested):
        if caller.post_attempt_requested and caller.window_open is False:
            return "post_attempt", "the item's attempt window is closed"
        if caller.post_attempt_requested:
            return "assisted_practice", "post_attempt requested while the attempt window is open"
        return "assisted_practice", f"tutor {caller.context} context bound to the item"
    if caller.kind == "router":
        return "reading", "router discovery (answers withheld from the model)"
    return "reading", f"{caller.kind} caller with no item bound"


def assert_policy(caller: CallerContext, requested: str | None) -> str:
    """The derived policy; a requested policy that differs is refused (G2).

    An argument can narrow a request but never widen its policy, so a
    ``policy`` argument is only ever an assertion of the derived one.
    """

    derived, _reason = derive_policy(caller)
    if requested is not None and requested != derived:
        if requested == "authoring":
            raise PolicyRefused("policy_refused", "authoring is internal to the verifier; no caller may request it")
        raise PolicyRefused(
            "policy_refused",
            f"requested policy {requested!r} differs from the caller's {derived!r}",
        )
    return derived


__all__ = [
    "CALLER_KINDS",
    "ITEM_BOUND_CONTEXTS",
    "POLICIES",
    "CallerContext",
    "PolicyRefused",
    "RetrievalPolicy",
    "assert_policy",
    "derive_policy",
]
