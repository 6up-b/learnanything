"""The ChatGPT-plan session: sign-in, the access token for a call, status, sign-out.

One registration per machine (the saved ``oaiapp_…`` client id and the
validated identity). A sign-in validates everything before it replaces any
saved credential; a returning sign-in must be the same ChatGPT account.

The access token is refreshed shortly before it expires, under a cross-process
lock that re-reads the store first, so two LearnLoop processes never race a
rotating refresh token. A terminal refresh error (``invalid_grant`` and its
relatives) clears the tokens and keeps the registration: the next step is
``learnloop ai signin chatgpt``. A network or server failure keeps them.

Every credential commit (sign-in, refresh, sign-out) happens under that same
``refresh.lock``, re-reading the store first, so none can undo another: a
refresh that finishes during a sign-out commits before the sign-out reads the
tokens, and the sign-out then revokes and clears the live ones. A sign-out
also advances a sign-out epoch; a sign-in that began before it is refused at
commit (its tokens are revoked, never saved), as is a cancelled one. Tokens
and their grant are numbered with one generation (see ``store``); a token is
used only when its snapshot and ``account.json`` agree, and only while that
grant includes ChatGPT plan usage.

Usage errors become machine-local state that readiness reads without any
network call: ``subscription_sharing_usage_limit_exceeded`` pauses plan
requests (the docs: pause, link to ChatGPT's usage settings, do not infer a
reset time) for the profile's ``usage_limit_pause_minutes``;
``subscription_sharing_user_not_eligible`` marks the account ineligible until
the next sign-in.
"""
from __future__ import annotations

from collections.abc import Callable
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime, timezone
import secrets
import time
from typing import Any

from learnloop.ai.chatgpt_plan.oauth import (
    AGENT_NAME,
    AUTH_ISSUER,
    DYNAMIC_CLIENT_ID,
    HTTP_TIMEOUT_SECONDS,
    PLAN_SCOPE,
    TERMINAL_REFRESH_ERRORS,
    CallbackListener,
    Discovery,
    EndpointUnreachable,
    HttpCall,
    SignInError,
    TokenEndpointError,
    authorization_url,
    discover,
    exchange_code,
    fetch_jwks,
    granted_scopes,
    new_pkce_pair,
    refresh_grant,
    revoke_refresh_token,
    states_match,
    urllib_call,
    validate_id_token,
)
from learnloop.ai.chatgpt_plan.store import (
    LOCK_TIMEOUT_SECONDS,
    Account,
    LockCancelled,
    PlanStore,
    StoreError,
    Tokens,
)
from learnloop.ai.errors import AIProviderUnavailable

MANAGE_USAGE_URL = "https://chatgpt.com/settings/usage"
SIGN_IN_COMMAND = "learnloop ai signin chatgpt"
#: Refresh this long before the access token expires (tokens last ~1 hour).
REFRESH_MARGIN_SECONDS = 300
DEFAULT_PAUSE_MINUTES = 15
SIGN_IN_TIMEOUT_SECONDS = 300.0


class ChatGPTSignInRequired(AIProviderUnavailable):
    """No usable ChatGPT sign-in on this machine."""


class ChatGPTPlanNotEnabled(AIProviderUnavailable):
    """Signed in, but the grant does not include ChatGPT plan usage."""


class ChatGPTPlanUsageExhausted(AIProviderUnavailable):
    """A usage limit was reached; plan requests are paused."""


class ChatGPTPlanNotEligible(AIProviderUnavailable):
    """ChatGPT plan usage is unavailable for this user, workspace or policy."""


class TokenWaitAborted(AIProviderUnavailable):
    """The caller stopped waiting for the credential step (interrupt or deadline); nothing was sent."""


def _now_iso(now: float | None = None) -> str:
    return datetime.fromtimestamp(time.time() if now is None else now, timezone.utc).isoformat(timespec="seconds")


def _parse_iso(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return None


@dataclass(frozen=True)
class PlanStatus:
    """What this machine's ChatGPT sign-in can do, from local files only."""

    signed_in: bool
    plan_usage_enabled: bool
    email: str | None
    subject: str | None
    client_id: str | None
    secret_store: str | None
    access_expires_at: float | None
    usage_limit: dict[str, Any] | None
    not_eligible: dict[str, Any] | None
    welcome_pending: bool
    signed_out_reason: str | None
    id_token_signature: str | None
    store_dir: str
    error: str | None = None

    def paused_until(self, pause_minutes: int) -> float | None:
        if not self.usage_limit:
            return None
        at = _parse_iso(self.usage_limit.get("at"))
        return None if at is None else at + pause_minutes * 60

    def readiness(self, *, pause_minutes: int = DEFAULT_PAUSE_MINUTES, now: float | None = None) -> tuple[str, str]:
        """``(state, message)``: ``ready``, ``signed_out``, ``plan_usage_disabled``,
        ``not_eligible``, ``usage_exhausted`` or ``store_error``."""

        current = time.time() if now is None else now
        if self.error:
            return "store_error", f"The ChatGPT sign-in store cannot be read: {self.error}"
        if not self.signed_in:
            reason = f" ({self.signed_out_reason})" if self.signed_out_reason else ""
            return "signed_out", f"Not signed in with ChatGPT on this machine{reason}. Run `{SIGN_IN_COMMAND}`."
        if not self.plan_usage_enabled:
            return "plan_usage_disabled", (
                f"Signed in as {self.email or 'your ChatGPT account'}, but ChatGPT plan usage was not granted. "
                f"Run `{SIGN_IN_COMMAND} --consent` and allow plan usage."
            )
        if self.not_eligible:
            return "not_eligible", (
                "ChatGPT plan usage is unavailable for this account, workspace or policy "
                f"({self.not_eligible.get('code') or 'not eligible'}). Sign in again after it changes."
            )
        until = self.paused_until(pause_minutes)
        if until is not None and current < until:
            return "usage_exhausted", (
                "ChatGPT plan usage exhausted: a usage limit was reached at "
                f"{self.usage_limit.get('at') if self.usage_limit else '?'}; LearnLoop pauses plan requests until "
                f"{_now_iso(until)}. Manage usage: {MANAGE_USAGE_URL} "
                "(`learnloop ai resume chatgpt` tries again sooner)."
            )
        return "ready", f"Signed in with ChatGPT as {self.email or self.subject or 'your account'}; plan usage enabled."

    def as_dict(self, *, pause_minutes: int = DEFAULT_PAUSE_MINUTES) -> dict[str, Any]:
        state, message = self.readiness(pause_minutes=pause_minutes)
        until = self.paused_until(pause_minutes)
        if until is not None and until <= time.time():
            until = None
        return {
            "signed_in": self.signed_in,
            "plan_usage_enabled": self.plan_usage_enabled,
            "email": self.email,
            "client_id": self.client_id,
            "secret_store": self.secret_store,
            "access_expires_at": _now_iso(self.access_expires_at) if self.access_expires_at else None,
            "usage_limit": self.usage_limit,
            "paused_until": _now_iso(until) if until is not None else None,
            "not_eligible": self.not_eligible,
            "welcome_pending": self.welcome_pending,
            "signed_out_reason": self.signed_out_reason,
            "id_token_signature": self.id_token_signature,
            "store_dir": self.store_dir,
            "state": state,
            "message": message,
            "manage_usage_url": MANAGE_USAGE_URL,
        }


@dataclass(frozen=True)
class SignInResult:
    email: str | None
    subject: str
    client_id: str
    plan_usage_enabled: bool
    new_registration: bool
    secret_store: str
    id_token_signature: str
    welcome_pending: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "email": self.email, "client_id": self.client_id, "plan_usage_enabled": self.plan_usage_enabled,
            "new_registration": self.new_registration, "secret_store": self.secret_store,
            "id_token_signature": self.id_token_signature, "welcome_pending": self.welcome_pending,
        }


class PendingSignIn:
    """One authorization attempt: its listener, PKCE verifier, state and nonce."""

    def __init__(
        self, session: "PlanSession", *, discovery: Discovery, client_id: str, new_registration: bool,
        expected_subject: str | None, login_hint: str | None, consent: bool, port: int | None,
    ) -> None:
        self.session = session
        self.discovery = discovery
        self.client_id = client_id
        self.new_registration = new_registration
        self.expected_subject = expected_subject
        self.state = secrets.token_urlsafe(32)
        self.nonce = secrets.token_urlsafe(32)
        self.code_verifier, challenge = new_pkce_pair()
        self.listener = CallbackListener(port=port)
        self.redirect_uri = self.listener.redirect_uri
        self.authorize_url = authorization_url(
            discovery, client_id=client_id, redirect_uri=self.redirect_uri, state=self.state,
            nonce=self.nonce, code_challenge=challenge, host_id=session.store.host_id(),
            agent_name_hint=AGENT_NAME if new_registration else None,
            login_hint=login_hint, consent=consent,
        )
        self.started_at = time.monotonic()
        #: A sign-out after this point invalidates the attempt (checked at commit).
        self.signout_epoch = session._signout_epoch()
        self.cancelled = False

    def wait(self, timeout: float = SIGN_IN_TIMEOUT_SECONDS) -> SignInResult:
        """Wait for the browser to return, then finish; the listener always closes."""

        try:
            params = self.listener.wait(timeout)
        finally:
            self.close()
        if self.listener.cancelled:
            raise SignInError("Sign-in cancelled.", code="cancelled")
        if params is None:
            raise SignInError("The sign-in timed out before the browser returned to LearnLoop.", code="timed_out")
        return self.finish(params)

    def cancel(self) -> None:
        """End the wait; a callback already being finished is refused at commit."""

        self.cancelled = True
        self.listener.cancel()

    def close(self) -> None:
        self.listener.close()

    def finish(self, params: dict[str, str]) -> SignInResult:
        return self.session._complete(self, params)


class PlanSession:
    """The machine's ChatGPT sign-in, read from (and written to) a :class:`PlanStore`."""

    def __init__(self, store: PlanStore | None = None, *, http: HttpCall = urllib_call,
                 clock: Callable[[], float] = time.time) -> None:
        self.store = store or PlanStore()
        self._http = http
        self._clock = clock

    # -- status ----------------------------------------------------------
    def status(self) -> PlanStatus:
        try:
            account = self.store.load_account()
            state = self.store.load_state()
        except StoreError as exc:
            return PlanStatus(False, False, None, None, None, None, None, None, None, False, None, None,
                              str(self.store.root), error=str(exc))
        expires_at = None
        if account is not None and account.signed_in:
            # Expiry only: the tokens themselves are never read for status.
            expires_at = account.access_expires_at if isinstance(account.access_expires_at, (int, float)) else None
        signed_in = bool(account and account.signed_in)
        return PlanStatus(
            signed_in=signed_in,
            plan_usage_enabled=bool(account and account.plan_usage_enabled),
            email=account.email if account else None,
            subject=account.subject if account else None,
            client_id=account.client_id if account else None,
            secret_store=account.secret_store if account else None,
            access_expires_at=expires_at,
            usage_limit=state.get("usage_limit") if isinstance(state.get("usage_limit"), dict) else None,
            not_eligible=state.get("not_eligible") if isinstance(state.get("not_eligible"), dict) else None,
            welcome_pending=signed_in and bool(account and account.plan_usage_enabled)
            and not state.get("welcome_acknowledged_at"),
            signed_out_reason=account.signed_out_reason if account else None,
            id_token_signature=account.id_token_signature if account else None,
            store_dir=str(self.store.root),
        )

    # -- sign-in -----------------------------------------------------------
    def begin_sign_in(self, *, issuer: str = AUTH_ISSUER, new_account: bool = False, consent: bool = False,
                      port: int | None = None) -> PendingSignIn:
        """Start one attempt: discovery, a fresh state/nonce/PKCE, the loopback listener.

        A saved registration is reused (its issued client id, the saved email as
        ``login_hint``) unless ``new_account`` registers a new client.
        """

        account = None if new_account else self.store.load_account()
        if account is not None and account.issuer.rstrip("/") != issuer.rstrip("/"):
            account = None
        discovery = discover(issuer, http=self._http)
        if account is not None:
            return PendingSignIn(
                self, discovery=discovery, client_id=account.client_id, new_registration=False,
                expected_subject=account.subject, login_hint=account.email, consent=consent, port=port,
            )
        return PendingSignIn(
            self, discovery=discovery, client_id=DYNAMIC_CLIENT_ID, new_registration=True,
            expected_subject=None, login_hint=None, consent=consent, port=port,
        )

    def _complete(self, pending: PendingSignIn, params: dict[str, str]) -> SignInResult:
        if not states_match(pending.state, params.get("state")):
            raise SignInError("The sign-in callback could not be verified (state mismatch); start again.",
                              code="state_mismatch")
        error = params.get("error")
        if error:
            if error == "access_denied":
                raise SignInError("Sign-in was declined in the browser; nothing was saved.", code="access_denied")
            raise SignInError(f"Sign-in failed in the browser ({error}).", code="authorization_error")
        code = params.get("code")
        if not code:
            raise SignInError("The callback did not contain an authorization code.", code="missing_code")
        returned = params.get("client_id")
        if pending.new_registration:
            if not returned or returned == DYNAMIC_CLIENT_ID:
                raise SignInError("Registration is incomplete: the callback returned no issued client id.",
                                  code="registration_incomplete")
            client_id = returned
        else:
            if returned and returned != pending.client_id:
                raise SignInError("The callback named a different client than this sign-in; nothing was saved.",
                                  code="client_mismatch")
            client_id = pending.client_id
        discovery = pending.discovery
        try:
            payload = exchange_code(discovery, client_id=client_id, code=code, code_verifier=pending.code_verifier,
                                    redirect_uri=pending.redirect_uri, http=self._http)
        except TokenEndpointError as exc:
            if pending.new_registration and self.store.load_account() is None:
                # Keep the issued client so the next attempt reuses it.
                self.store.save_account(Account(
                    client_id=client_id, issuer=discovery.issuer, token_endpoint=discovery.token_endpoint,
                    revocation_endpoint=discovery.revocation_endpoint, signed_out_reason="code exchange failed",
                ))
            hint = " The code was discarded; run the sign-in again." if exc.error == "invalid_grant" else ""
            raise SignInError(f"The code exchange failed ({exc}).{hint}", code=exc.error or "exchange_failed") from None
        except EndpointUnreachable as exc:
            raise SignInError(f"The token endpoint could not be reached ({exc}).", code="unreachable") from None
        access = payload.get("access_token")
        id_token = payload.get("id_token")
        if not isinstance(access, str) or not access or not isinstance(id_token, str):
            raise SignInError("The token response lacks an access token or an ID token.", code="invalid_token_response")
        identity = validate_id_token(
            id_token, issuer=discovery.issuer, client_id=client_id, nonce=pending.nonce,
            jwks=(lambda: fetch_jwks(discovery.jwks_uri, http=self._http)) if discovery.jwks_uri else None,
            now=self._clock(),
        )
        if pending.expected_subject and identity.subject != pending.expected_subject:
            raise SignInError(
                "You signed in with a different ChatGPT account than the saved one; nothing was replaced. "
                f"To switch accounts, run `{SIGN_IN_COMMAND} --new-account`.", code="account_mismatch",
            )
        scopes = granted_scopes(payload, callback_scope=params.get("scope"))
        now = self._clock()
        tokens = _tokens_from(payload, now=now, previous=None, scopes=scopes)
        account = Account(
            client_id=client_id, issuer=discovery.issuer, token_endpoint=discovery.token_endpoint,
            revocation_endpoint=discovery.revocation_endpoint, subject=identity.subject, email=identity.email,
            scopes=scopes, plan_usage_enabled=PLAN_SCOPE in scopes, signed_in=True, signed_in_at=_now_iso(now),
            id_token_signature=identity.signature, access_expires_at=tokens.expires_at,
        )
        refused: str | None = None
        with self.store.lock("refresh.lock"):
            if pending.cancelled:
                refused = "cancelled"
            elif self._signout_epoch() != pending.signout_epoch:
                refused = "signed_out"
            else:
                replaced = self.store.load_account()
                if replaced is not None and replaced.client_id != client_id:
                    # A new registration replaces the saved one: its tokens go too.
                    self.store.clear_tokens(replaced)
                account.generation = tokens.generation = (replaced.generation if replaced else 0) + 1
                account = self.store.save_sign_in(account, tokens)
                previous = self.store.load_state()
                self.store.update_state(usage_limit=None, not_eligible=None, force_refresh=None,
                                        access_expires_at=None)
        if refused is not None:
            # Never saved, so never left live either.
            self._revoke_quietly(discovery.revocation_endpoint, client_id, tokens.refresh_token)
            if refused == "cancelled":
                raise SignInError("Sign-in cancelled; nothing was saved.", code="cancelled")
            raise SignInError(
                f"You signed out while this sign-in was in progress; nothing was saved. Run `{SIGN_IN_COMMAND}` "
                "to sign in again.", code="signed_out",
            )
        return SignInResult(
            email=identity.email, subject=identity.subject, client_id=client_id,
            plan_usage_enabled=account.plan_usage_enabled, new_registration=pending.new_registration,
            secret_store=account.secret_store, id_token_signature=identity.signature,
            welcome_pending=account.plan_usage_enabled and not previous.get("welcome_acknowledged_at"),
        )

    def acknowledge_welcome(self) -> None:
        """The first-sign-in confirmation was shown; never show it again."""

        self.store.update_state(welcome_acknowledged_at=_now_iso(self._clock()))

    # -- the access token for a call ------------------------------------
    def access_token(self, *, timeout: float = HTTP_TIMEOUT_SECONDS,
                     cancelled: Callable[[], bool] | None = None) -> str:
        """A current access token, refreshed (with rotation) when near expiry.

        ``timeout`` bounds the whole step: waiting for another process's
        refresh and this one's token request. ``cancelled()`` (an interrupt or
        a passed deadline) stops a wait at once with :class:`TokenWaitAborted`.
        A refresh whose answer has arrived is always committed first: its
        refresh token has rotated, and dropping it would end the session.
        The token is returned only under a grant that includes plan usage.
        """

        started = time.monotonic()
        account, tokens = self._signed_in()
        state = self.store.load_state()
        if tokens.generation == account.generation and self._fresh(tokens) and not state.get("force_refresh"):
            return self._usable(account, tokens)
        with ExitStack() as held:
            try:
                held.enter_context(self.store.lock(
                    "refresh.lock", timeout=min(LOCK_TIMEOUT_SECONDS, max(0.0, timeout)), cancelled=cancelled))
            except LockCancelled:
                raise TokenWaitAborted("Stopped waiting for the ChatGPT token refresh.") from None
            except StoreError as exc:
                raise AIProviderUnavailable(
                    f"The ChatGPT sign-in is busy in another LearnLoop process ({exc}); try again.") from None
            return self._access_token_locked(started=started, timeout=timeout, cancelled=cancelled)

    def _access_token_locked(self, *, started: float, timeout: float,
                             cancelled: Callable[[], bool] | None) -> str:
        # Another process may have refreshed (or signed out) while this one waited.
        account, tokens = self._reconciled(*self._signed_in())
        state = self.store.load_state()
        if self._fresh(tokens) and not state.get("force_refresh"):
            return self._usable(account, tokens)
        remaining = timeout - (time.monotonic() - started)
        if (cancelled is not None and cancelled()) or remaining <= 0:
            raise TokenWaitAborted("Stopped before refreshing the ChatGPT token.")
        if not tokens.refresh_token:
            return self._sign_out_locally(account, "the session cannot be renewed (no refresh token)")
        try:
            payload = refresh_grant(account.token_endpoint, client_id=account.client_id,
                                    refresh_token=tokens.refresh_token, http=self._http,
                                    timeout=min(HTTP_TIMEOUT_SECONDS, remaining))
        except TokenEndpointError as exc:
            if exc.error in TERMINAL_REFRESH_ERRORS:
                return self._sign_out_locally(account, f"the session ended ({exc.error})")
            if exc.error == "invalid_client":
                return self._sign_out_locally(
                    account, "the registered client is no longer valid (invalid_client); "
                    f"run `{SIGN_IN_COMMAND} --new-account`")
            return self._usable(account, self._still_valid_or_raise(
                tokens, f"The ChatGPT token refresh failed ({exc})."))
        except EndpointUnreachable as exc:
            return self._usable(account, self._still_valid_or_raise(
                tokens, f"The ChatGPT token endpoint is unreachable ({exc})."))
        access = payload.get("access_token")
        if not isinstance(access, str) or not access:
            return self._usable(account, self._still_valid_or_raise(
                tokens, "The ChatGPT token refresh returned no access token."))
        new_id_token = payload.get("id_token")
        if isinstance(new_id_token, str) and new_id_token:
            try:
                identity = validate_id_token(new_id_token, issuer=account.issuer, client_id=account.client_id,
                                             nonce=None, jwks=None, now=self._clock())
            except SignInError:
                identity = None
            if identity is not None and account.subject and identity.subject != account.subject:
                return self._sign_out_locally(account, "the refreshed session belongs to another account")
        scopes = granted_scopes(payload) or (tokens.scopes if tokens.scopes is not None else account.scopes)
        refreshed = _tokens_from(payload, now=self._clock(), previous=tokens, scopes=scopes)
        # One commit: the token snapshot (with its grant) first, then the
        # account at the same generation. A crash between the two leaves a
        # newer snapshot, which the next reader rolls forward (_reconciled).
        account.generation = refreshed.generation = account.generation + 1
        account.scopes = list(scopes)
        account.plan_usage_enabled = PLAN_SCOPE in scopes
        account.access_expires_at = refreshed.expires_at
        self.store.save_tokens(account, refreshed)
        self.store.save_account(account)
        self.store.update_state(force_refresh=None)
        return self._usable(account, refreshed)

    def _reconciled(self, account: Account, tokens: Tokens) -> tuple[Account, Tokens]:
        """Finish a commit that stopped between the token snapshot and the account (caller holds the lock)."""

        if tokens.generation == account.generation:
            return account, tokens
        if tokens.generation > account.generation and tokens.scopes is not None:
            account.generation = tokens.generation
            account.scopes = list(tokens.scopes)
            account.plan_usage_enabled = PLAN_SCOPE in tokens.scopes
            account.access_expires_at = tokens.expires_at
            self.store.save_account(account)
            return account, tokens
        raise ChatGPTSignInRequired(
            f"The saved ChatGPT sign-in is inconsistent (its tokens predate its account). Run `{SIGN_IN_COMMAND}`.")

    def _usable(self, account: Account, tokens: Tokens) -> str:
        """The token, only under a grant that includes ChatGPT plan usage."""

        scopes = tokens.scopes if tokens.scopes is not None else account.scopes
        if not account.plan_usage_enabled or PLAN_SCOPE not in scopes:
            raise ChatGPTPlanNotEnabled(self.status().readiness()[1])
        return tokens.access_token

    def _fresh(self, tokens: Tokens) -> bool:
        return tokens.expires_at - REFRESH_MARGIN_SECONDS > self._clock()

    def _still_valid_or_raise(self, tokens: Tokens, message: str) -> Tokens:
        if tokens.expires_at > self._clock() + 5:
            return tokens
        raise AIProviderUnavailable(message)

    def _signed_in(self) -> tuple[Account, Tokens]:
        try:
            account = self.store.load_account()
        except StoreError as exc:
            raise ChatGPTSignInRequired(str(exc)) from None
        if account is None or not account.signed_in:
            raise ChatGPTSignInRequired(self.status().readiness()[1])
        try:
            tokens = self.store.load_tokens(account)
        except StoreError as exc:
            raise ChatGPTSignInRequired(f"{exc} Run `{SIGN_IN_COMMAND}`.") from None
        if tokens is None:
            raise ChatGPTSignInRequired(f"The saved ChatGPT sign-in has no tokens. Run `{SIGN_IN_COMMAND}`.")
        return account, tokens

    def _sign_out_locally(self, account: Account, reason: str) -> str:
        """Clear the tokens after a terminal refresh error (the caller holds ``refresh.lock``)."""

        self.store.clear_tokens(account)
        account.signed_in = False
        account.signed_out_reason = reason
        account.generation += 1
        account.access_expires_at = None
        self.store.save_account(account)
        self.store.update_state(force_refresh=None, access_expires_at=None)
        raise ChatGPTSignInRequired(f"Sign in with ChatGPT again: {reason}. Run `{SIGN_IN_COMMAND}`.")

    def _signout_epoch(self) -> int:
        value = self.store.load_state().get("signout_epoch")
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    # -- usage and error state ------------------------------------------
    def check_usable(self, *, pause_minutes: int) -> dict[str, Any] | None:
        """Refuse before any request when readiness says the plan cannot serve it.

        Returns the (expired) usage-limit record this check saw, if any; pass it
        to :meth:`note_success` after the request completes.
        """

        status = self.status()
        state, message = status.readiness(pause_minutes=pause_minutes, now=self._clock())
        if state == "ready":
            return dict(status.usage_limit) if status.usage_limit else None
        if state == "usage_exhausted":
            raise ChatGPTPlanUsageExhausted(message)
        if state == "not_eligible":
            raise ChatGPTPlanNotEligible(message)
        if state == "plan_usage_disabled":
            raise ChatGPTPlanNotEnabled(message)
        raise ChatGPTSignInRequired(message)

    def note_unauthorized(self) -> None:
        """A 401: refresh before the next request."""

        self.store.update_state(force_refresh=True)

    def note_usage_limit(self, *, code: str, request_id: str | None) -> None:
        # The id makes two pauses within one second distinguishable (note_success).
        self.store.update_state(usage_limit={"code": code, "at": _now_iso(self._clock()), "request_id": request_id,
                                             "id": secrets.token_hex(8)})

    def note_not_eligible(self, *, code: str, request_id: str | None) -> None:
        self.store.update_state(not_eligible={"code": code, "at": _now_iso(self._clock()), "request_id": request_id})

    def note_listed_models(self, slugs: list[str]) -> None:
        """Remember the account's model list (``learnloop ai models chatgpt``) for `learnloop doctor`."""

        status = self.status()
        self.store.update_state(listed_models={
            "slugs": list(slugs), "at": _now_iso(self._clock()), "subject": status.subject,
        })

    def listed_models(self) -> dict[str, Any] | None:
        """The last model list of the signed-in account, or ``None`` (never listed, or another account)."""

        record = self.store.load_state().get("listed_models")
        if not isinstance(record, dict) or not isinstance(record.get("slugs"), list):
            return None
        subject = self.status().subject
        if record.get("subject") and subject and record.get("subject") != subject:
            return None
        return record

    def resume(self) -> None:
        """Clear the usage-limit pause so the next request tries the plan again."""

        self.store.update_state(usage_limit=None)

    def note_success(self, observed_pause: dict[str, Any] | None) -> None:
        """A completed response: the expired pause it was sent under is no longer news.

        Only that record is cleared, compared under the state lock: a pause that
        another request imposed while this one was in flight stays.
        """

        if observed_pause:
            self.store.clear_state_if("usage_limit", observed_pause)

    # -- sign-out --------------------------------------------------------
    def sign_out(self) -> dict[str, Any]:
        """Clear the tokens, then revoke the renewable session; keep the registration and host id.

        The local sign-out is one commit under ``refresh.lock``: it waits for
        an in-flight refresh to commit, then clears the tokens that are live
        now, and advances the sign-out epoch so no sign-in that began earlier
        can save. Remote revocation follows, outside the lock.
        """

        try:
            with self.store.lock("refresh.lock"):
                self.store.update_state(signout_epoch=self._signout_epoch() + 1, force_refresh=None,
                                        access_expires_at=None, usage_limit=None)
                account = self.store.load_account()
                if account is None:
                    return {"signed_out": True, "revoked": None, "message": "Not signed in."}
                try:
                    tokens = self.store.load_tokens(account)
                except StoreError:
                    tokens = None
                self.store.clear_tokens(account)
                account.signed_in = False
                account.signed_out_reason = "signed out"
                account.generation += 1
                account.access_expires_at = None
                self.store.save_account(account)
        except StoreError as exc:
            return {"signed_out": False, "revoked": None, "message": f"Could not sign out: {exc}"}
        revoked: bool | None = None
        message = "Signed out."
        if tokens is not None and tokens.refresh_token and account.revocation_endpoint:
            revoked = False
            for attempt in range(3):
                try:
                    revoke_refresh_token(account.revocation_endpoint, client_id=account.client_id,
                                         refresh_token=tokens.refresh_token, http=self._http)
                    revoked = True
                    break
                except TokenEndpointError as exc:
                    if exc.status < 500:
                        break
                except EndpointUnreachable:
                    pass
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
            if not revoked:
                message = ("Signed out locally; remote revocation was not confirmed. You can disconnect "
                           "LearnLoop in ChatGPT Settings.")
        elif tokens is not None and not account.revocation_endpoint:
            message = "Signed out locally; the issuer publishes no revocation endpoint."
        return {"signed_out": True, "revoked": revoked, "message": message}

    def _revoke_quietly(self, endpoint: str | None, client_id: str, refresh_token: str | None) -> None:
        """One best-effort revocation of tokens that were never saved."""

        if not endpoint or not refresh_token:
            return
        try:
            revoke_refresh_token(endpoint, client_id=client_id, refresh_token=refresh_token, http=self._http)
        except (TokenEndpointError, EndpointUnreachable):
            pass


def _tokens_from(payload: dict[str, Any], *, now: float, previous: Tokens | None,
                 scopes: list[str] | None) -> Tokens:
    expires_in = payload.get("expires_in")
    lifetime = float(expires_in) if isinstance(expires_in, (int, float)) and expires_in > 0 else 3600.0
    earliest = payload.get("earliest_refresh_at")
    refresh = payload.get("refresh_token")
    id_token = payload.get("id_token")
    return Tokens(
        access_token=str(payload["access_token"]),
        refresh_token=refresh if isinstance(refresh, str) and refresh else (previous.refresh_token if previous else None),
        id_token=id_token if isinstance(id_token, str) and id_token else (previous.id_token if previous else None),
        token_type=str(payload.get("token_type") or "Bearer"),
        expires_at=now + lifetime,
        saved_at=now,
        earliest_refresh_at=float(earliest) if isinstance(earliest, (int, float)) else None,
        scopes=list(scopes) if scopes is not None else None,
    )


__all__ = [
    "ChatGPTPlanNotEligible",
    "ChatGPTPlanNotEnabled",
    "ChatGPTPlanUsageExhausted",
    "ChatGPTSignInRequired",
    "MANAGE_USAGE_URL",
    "PendingSignIn",
    "PlanSession",
    "PlanStatus",
    "SIGN_IN_COMMAND",
    "SignInResult",
    "TokenWaitAborted",
]
