"""Desktop "Continue with ChatGPT": sign-in, status and plan-usage actions.

``chatgpt_plan_signin_start`` starts the loopback listener and returns the
authorization URL; the desktop opens it in the system browser and polls
``chatgpt_plan_status`` until the attempt ends. One attempt at a time; a new
start cancels the previous one. Cancel waits briefly for the attempt to end, so
its reply is usually final; a callback that is already being finished is
refused at commit, so a cancelled attempt never saves. The sign-in is machine-global (it lives in
the LearnLoop config directory, never in a vault), so none of these needs a
vault, and none returns a token. Desktop only: never phone-allowed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from typing import Any

from learnloop.ai.chatgpt_plan.oauth import SignInError
from learnloop.ai.chatgpt_plan.routes import plan_profiles
from learnloop.ai.chatgpt_plan.session import SIGN_IN_TIMEOUT_SECONDS, PendingSignIn, PlanSession
from learnloop.ai.chatgpt_plan.store import StoreError
from learnloop.ids import new_ulid

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams, ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


CANCEL_WAIT_SECONDS = 2.0


@dataclass
class _Attempt:
    id: str
    pending: PendingSignIn
    status: str = "waiting"  # waiting | succeeded | failed | cancelled
    result: dict[str, Any] | None = None
    error: dict[str, str] | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    done: threading.Event = field(default_factory=threading.Event)

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id, "status": self.status, "result": self.result, "error": self.error,
            "started_at": self.started_at, "finished_at": self.finished_at,
        }


class SignInAttempts:
    """The process's one sign-in attempt, run on a background thread."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._attempt: _Attempt | None = None

    def start(self, session: PlanSession, *, new_account: bool, consent: bool,
              timeout: float = SIGN_IN_TIMEOUT_SECONDS) -> _Attempt:
        self.cancel()
        pending = session.begin_sign_in(new_account=new_account, consent=consent)
        attempt = _Attempt(id=new_ulid(), pending=pending)
        with self._lock:
            self._attempt = attempt

        def run() -> None:
            try:
                result = pending.wait(timeout=timeout)
            except SignInError as exc:
                outcome = ("cancelled" if exc.code == "cancelled" else "failed", None,
                           {"code": exc.code, "message": str(exc)})
            except StoreError as exc:
                outcome = ("failed", None, {"code": "store_error", "message": str(exc)})
            except Exception as exc:  # noqa: BLE001 - surfaced to the desktop, never raised on a daemon thread
                outcome = ("failed", None, {"code": type(exc).__name__, "message": str(exc)})
            else:
                outcome = ("succeeded", result.as_dict(), None)
            with self._lock:
                attempt.status, attempt.result, attempt.error = outcome
                attempt.finished_at = time.time()
            attempt.done.set()

        threading.Thread(target=run, name="learnloop-chatgpt-signin", daemon=True).start()
        return attempt

    def cancel(self, *, wait: float = CANCEL_WAIT_SECONDS) -> bool:
        with self._lock:
            attempt = self._attempt
        if attempt is None or attempt.status != "waiting":
            return False
        attempt.pending.cancel()
        # Usually immediate; a code exchange in flight may take longer, and the
        # desktop keeps polling until the attempt reports its end.
        attempt.done.wait(wait)
        return True

    def snapshot(self) -> dict[str, Any] | None:
        with self._lock:
            return self._attempt.snapshot() if self._attempt is not None else None


ATTEMPTS = SignInAttempts()


def chatgpt_plan_payload(ctx: SidecarContext) -> dict[str, Any]:
    """Status (local files only), the current attempt, and the open vault's plan profiles."""

    session = PlanSession()
    profiles: list[dict[str, Any]] = []
    pause = 15
    if ctx.vault is not None:
        profiles = plan_profiles(ctx.vault.config)
        in_use = [entry for entry in profiles if entry["in_use"]]
        if in_use:
            pause = min(entry["usage_limit_pause_minutes"] for entry in in_use)
    status = session.status().as_dict(pause_minutes=pause)
    return {**status, "attempt": ATTEMPTS.snapshot(), "profiles": profiles,
            "using_plan": any(entry["in_use"] and entry["enabled"] for entry in profiles)}


@method("chatgpt_plan_status", EmptyParams)
def chatgpt_plan_status(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]:
    return versioned(chatgpt_plan_payload(ctx))


class SignInStartParams(ParamsModel):
    new_account: bool = False
    consent: bool = False


@method("chatgpt_plan_signin_start", SignInStartParams)
def chatgpt_plan_signin_start(ctx: SidecarContext, params: SignInStartParams) -> dict[str, Any]:
    try:
        attempt = ATTEMPTS.start(PlanSession(), new_account=params.new_account, consent=params.consent)
    except (SignInError, StoreError) as exc:
        raise SidecarError(getattr(exc, "code", "sign_in_failed"), str(exc)) from None
    return versioned({**chatgpt_plan_payload(ctx), "authorize_url": attempt.pending.authorize_url})


@method("chatgpt_plan_signin_cancel", EmptyParams)
def chatgpt_plan_signin_cancel(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]:
    cancelled = ATTEMPTS.cancel()
    return versioned({**chatgpt_plan_payload(ctx), "cancelled": cancelled})


@method("chatgpt_plan_signout", EmptyParams)
def chatgpt_plan_signout(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]:
    ATTEMPTS.cancel()
    result = PlanSession().sign_out()
    return versioned({**chatgpt_plan_payload(ctx), "signout": result})


@method("chatgpt_plan_acknowledge_welcome", EmptyParams)
def chatgpt_plan_acknowledge_welcome(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]:
    PlanSession().acknowledge_welcome()
    return versioned(chatgpt_plan_payload(ctx))


@method("chatgpt_plan_resume", EmptyParams)
def chatgpt_plan_resume(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]:
    PlanSession().resume()
    return versioned(chatgpt_plan_payload(ctx))


__all__ = ["ATTEMPTS", "SignInAttempts", "chatgpt_plan_payload"]
