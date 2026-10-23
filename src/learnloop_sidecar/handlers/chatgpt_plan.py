"""Desktop "Continue with ChatGPT": sign-in, status and plan-usage actions.

``chatgpt_plan_signin_start`` starts the loopback listener and returns the
authorization URL; the desktop opens it in the system browser and polls
``chatgpt_plan_status`` until the attempt ends. One attempt at a time; a new
start cancels the previous one. Cancel waits briefly for the attempt to end, so
its reply is usually final; a callback that is already being finished is
refused at commit, so a cancelled attempt never saves. The sign-in is machine-global (it lives in
the LearnLoop config directory, never in a vault), so none of these needs a
vault, and none returns a token. ``ai_use_fallback`` (plan-first transport T1)
records the learner's "Use OpenRouter instead" for the open vault's session. Desktop
only: never phone-allowed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from typing import Any, Literal

from pydantic import Field

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


class UseFallbackParams(ParamsModel):
    # The one fallback the owner approved (2026-10-21).
    provider: Literal["openrouter"]
    # The tasks the feature's hint named (``fallback_tasks``).
    tasks: list[str] = Field(default_factory=list)
    # True: stop using OpenRouter for every task this session.
    stop: bool = False


@method("ai_use_fallback", UseFallbackParams)
def ai_use_fallback(ctx: SidecarContext, params: UseFallbackParams) -> dict[str, Any]:
    """The learner chose "Use OpenRouter instead" (plan-first transport T1).

    While the ChatGPT plan is unavailable, the named tasks run on the
    configured OpenRouter profile (``ai.plan_fallback_profile``) for the rest
    of this session, on this vault only (a vault switch clears the grant):
    the tasks of the feature that asked, and only those this vault was
    offered (review F4), and only while the plan cannot serve them (a ready
    plan route is always used first). A granted request is an ordinary
    metered request, so every feature's spend caps apply. Refused when no
    OpenRouter profile with a key is configured: the offer is never shown
    then. ``stop: true`` revokes every grant on this vault.
    """

    from learnloop.ai import plan_fallback

    vault, _repository = ctx.require_vault()
    if params.stop:
        plan_fallback.revoke(vault.root)
        return versioned({"provider": params.provider, "profile": plan_fallback.offer_profile(vault.config),
                          "granted_tasks": [], "scope": "session"})
    offered = set(plan_fallback.offered_tasks(vault.root))
    not_offered = sorted({task for task in params.tasks if task not in offered})
    if not_offered or not params.tasks:
        raise SidecarError(
            "not_offered",
            "Name the tasks of the offer you are answering (its fallback_tasks); "
            f"not offered on this vault: {', '.join(not_offered) or 'none given'}.",
            details={"offered_tasks": sorted(offered)},
        )
    profile = plan_fallback.offer_profile(vault.config)
    if profile is None:
        raise SidecarError("fallback_unavailable",
                           "OpenRouter isn't set up on this computer. Add an OpenRouter key in Settings first.")
    plan_fallback.grant(vault.root, params.tasks)
    return versioned({"provider": params.provider, "profile": profile,
                      "granted_tasks": plan_fallback.granted_tasks(vault.root), "scope": "session"})


__all__ = ["ATTEMPTS", "SignInAttempts", "chatgpt_plan_payload"]
