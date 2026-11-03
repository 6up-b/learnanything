"""Mobile PR-5 (``spec_mobile_tailnet_v1`` §6.8, T8): who a request comes from.

The device and surface of a request come from the authenticated token, carried
on the handler context, and never from request parameters. The phone host sets
``SidecarContext.request_origin`` around each call
(:meth:`SidecarContext.acting_as`); the desktop sidecar leaves it ``None``, which
means the desktop, so every desktop write and response stays as it was.

Three things read it:

* **provenance:** an attempt's ``entry_surface`` and an offer's or a binding's
  surface (:func:`practice_surface`, :func:`offer_surface`). A session's
  ``owner_device_id`` changes on handoff, so it never says which device made an
  attempt: the request does;
* **session ownership:** ``SidecarContext.origin_device_id`` (§6.5);
* **device eligibility:** :func:`device_class` (§6.4).
"""

from __future__ import annotations

from dataclasses import dataclass

from learnloop.scheduling.device_eligibility import DESKTOP, PHONE

#: The surfaces the desktop has always recorded (the stores' own defaults).
DESKTOP_PRACTICE = "desktop_practice"
DESKTOP_QUEUE = "desktop_queue"
#: The surfaces of a phone request (§6.8, G11).
PHONE_PRACTICE = "phone_practice"
PHONE_QUEUE = "phone_queue"


@dataclass(frozen=True)
class RequestOrigin:
    """One authenticated caller: the paired device and the surface it runs."""

    device_id: str
    surface: str = PHONE

    def __post_init__(self) -> None:
        if not self.device_id or not self.device_id.strip():
            raise ValueError("A request origin names a device.")
        if self.surface != PHONE:
            raise ValueError(f"Unknown request surface {self.surface!r}.")


def device_class(origin: RequestOrigin | None) -> str:
    """The class the eligibility module asks about (§6.4); None is the desktop."""

    return DESKTOP if origin is None else origin.surface


def practice_surface(origin: RequestOrigin | None) -> str:
    """``entry_surface`` of an attempt and of a submission's binding."""

    return DESKTOP_PRACTICE if origin is None else PHONE_PRACTICE


def offer_surface(origin: RequestOrigin | None) -> str:
    """``entry_surface`` of a published scheduler offer."""

    return DESKTOP_QUEUE if origin is None else PHONE_QUEUE
