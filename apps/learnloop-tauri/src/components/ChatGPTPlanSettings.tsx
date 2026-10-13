// Settings → ChatGPT plan: "Continue with ChatGPT" (Sign in with ChatGPT for
// open-source apps). The sign-in is machine-wide and never reaches a vault;
// the sidecar runs the loopback listener and this screen opens OpenAI's page
// in the system browser. Polling follows the attempt itself: it runs while the
// current attempt is "waiting" (also after Settings reopens mid-sign-in, and
// after cancel until the sidecar reports the attempt ended). Copy follows
// OpenAI's UI/UX guidelines: "Continue with ChatGPT" starts sign-in, a
// one-time "You're using your ChatGPT plan" confirmation, "Using ChatGPT plan"
// with a "Manage usage" link while a route uses it, and "Usage limit reached"
// with "Manage usage" as the primary action.
import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { ChatGPTPlanDto } from "../api/dto";
import { errorMessage } from "../errors";
import type { SettingsStyles } from "./NativeMediaSettings";
import { COLOR } from "./term";

const POLL_MS = 1000;

async function openExternal(url: string) {
  const { openUrl } = await import("@tauri-apps/plugin-opener");
  await openUrl(url);
}

function stateLine(plan: ChatGPTPlanDto): { text: string; color: string } {
  switch (plan.state) {
    case "ready":
      return { text: `signed in as ${plan.email ?? "your ChatGPT account"} · plan usage enabled`, color: COLOR.green };
    case "plan_usage_disabled":
      return { text: `signed in as ${plan.email ?? "your account"} · plan usage not granted`, color: COLOR.amber };
    case "usage_exhausted":
      return { text: `usage limit reached · paused until ${plan.pausedUntil ?? "later"}`, color: COLOR.red };
    case "not_eligible":
      return { text: "plan usage is unavailable for this account or workspace", color: COLOR.red };
    case "store_error":
      return { text: plan.message, color: COLOR.red };
    default:
      return { text: "not signed in", color: COLOR.textDim };
  }
}

export function ChatGPTPlanSettings({
  plan: initial,
  styles,
  onToast,
  onError
}: {
  plan: ChatGPTPlanDto;
  styles: SettingsStyles;
  onToast: (message: string) => void;
  onError: (message: string) => void;
}) {
  const [plan, setPlan] = useState<ChatGPTPlanDto>(initial);
  const [busy, setBusy] = useState<string | null>(null);
  // The callbacks may change identity on every parent render; polling must not restart for that.
  const notify = useRef({ onToast, onError });
  useEffect(() => {
    notify.current = { onToast, onError };
  });
  // The attempt this screen saw waiting: only its end is announced (never an old one).
  const watched = useRef<string | null>(null);

  useEffect(() => setPlan(initial), [initial]);

  const attemptId = plan.attempt?.id ?? null;
  const waiting = plan.attempt?.status === "waiting";

  useEffect(() => {
    if (!waiting || attemptId === null) return;
    watched.current = attemptId;
    let active = true;
    let reported = false;
    const timer = setInterval(() => {
      api.chatgptPlanStatus().then((next) => {
        if (active) setPlan(next);
      }, (error: unknown) => {
        // Keep polling (the sidecar may recover); report the failure once.
        if (!active || reported) return;
        reported = true;
        notify.current.onError(errorMessage(error));
      });
    }, POLL_MS);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [attemptId, waiting]);

  useEffect(() => {
    const attempt = plan.attempt;
    if (!attempt || attempt.status === "waiting" || watched.current !== attempt.id) return;
    watched.current = null;
    if (attempt.status === "succeeded") {
      notify.current.onToast(`signed in with ChatGPT${plan.email ? ` as ${plan.email}` : ""}`);
    } else if (attempt.status === "failed" && attempt.error) {
      notify.current.onError(attempt.error.message);
    }
  }, [plan]);

  const run = async (label: string, action: () => Promise<ChatGPTPlanDto>) => {
    setBusy(label);
    try {
      const next = await action();
      setPlan(next);
      return next;
    } catch (error) {
      onError(errorMessage(error));
      return null;
    } finally {
      setBusy(null);
    }
  };

  const signIn = async () => {
    const next = await run("signin", () => api.chatgptPlanSigninStart({ consent: plan.state === "plan_usage_disabled" }));
    if (!next?.authorizeUrl) return;
    try {
      await openExternal(next.authorizeUrl);
    } catch (error) {
      onError(`Open this address in your browser to sign in: ${next.authorizeUrl} (${errorMessage(error)})`);
    }
    // Polling starts from the waiting attempt in `next` (see the effect above).
  };

  const manageUsage = () => {
    openExternal(plan.manageUsageUrl).catch((error: unknown) => onError(errorMessage(error)));
  };

  const line = stateLine(plan);
  const needsSignIn = plan.state === "signed_out" || plan.state === "plan_usage_disabled" || plan.state === "store_error";
  const continueStyle = {
    background: "#000",
    border: "1px solid #000",
    borderRadius: 4,
    color: "#fff",
    fontSize: 12,
    fontWeight: 600,
    padding: "5px 14px",
    cursor: busy === null ? "pointer" : "default"
  } as const;
  const linkStyle = {
    background: "none",
    border: "none",
    color: COLOR.amberLink,
    cursor: "pointer",
    fontSize: 11,
    padding: 0,
    textDecoration: "underline"
  } as const;

  return (
    <section aria-label="ChatGPT plan">
      <div style={styles.row}>
        <span style={styles.label}>
          status
          <div style={styles.hint}>use your ChatGPT plan for routed AI requests</div>
        </span>
        <span style={{ flex: 1, color: line.color, fontSize: 11 }}>{line.text}</span>
      </div>

      {plan.state === "usage_exhausted" ? (
        <div role="alert" style={{ ...styles.row, flexDirection: "column", alignItems: "stretch", gap: 6 }}>
          <span style={{ color: COLOR.text }}>ChatGPT · Usage limit reached</span>
          <span style={styles.hint}>
            Review your plan or LearnLoop's limit in ChatGPT settings. Routes that allow a fallback use it meanwhile.
          </span>
          <span style={{ display: "flex", gap: 8 }}>
            <button type="button" style={continueStyle} onClick={manageUsage}>Manage usage</button>
            <button
              type="button"
              style={styles.button(busy === null)}
              disabled={busy !== null}
              onClick={() => void run("resume", () => api.chatgptPlanResume())}
            >
              try again now
            </button>
          </span>
        </div>
      ) : null}

      <div style={styles.row}>
        <span style={styles.label}>account</span>
        {waiting ? (
          <>
            <span style={{ flex: 1, color: COLOR.textDim, fontSize: 11 }}>waiting for the browser…</span>
            <button
              type="button"
              style={styles.button(busy === null)}
              disabled={busy !== null}
              onClick={() => void run("cancel", () => api.chatgptPlanSigninCancel())}
            >
              cancel
            </button>
          </>
        ) : needsSignIn ? (
          <button type="button" style={continueStyle} disabled={busy !== null} onClick={() => void signIn()}>
            {busy === "signin" ? "…" : "Continue with ChatGPT"}
          </button>
        ) : (
          <>
            <span style={{ flex: 1, color: COLOR.textFaint, fontSize: 11 }}>
              {plan.email ?? "signed in"}
              {plan.secretStore ? ` · saved in ${plan.secretStore === "keyring" ? "the OS keyring" : "a private file"}` : ""}
            </span>
            <button
              type="button"
              style={styles.button(busy === null)}
              disabled={busy !== null}
              onClick={() => void run("signout", () => api.chatgptPlanSignout()).then((next) => {
                if (next?.signout) onToast(next.signout.message);
              })}
            >
              sign out
            </button>
          </>
        )}
      </div>

      {plan.usingPlan && plan.state === "ready" ? (
        <div style={styles.row}>
          <span style={styles.label}>in use</span>
          <span style={{ flex: 1, fontSize: 11 }}>Using ChatGPT plan</span>
          <button type="button" style={linkStyle} onClick={manageUsage}>Manage usage</button>
        </div>
      ) : null}

      {plan.profiles.map((profile) => {
        const uses = [
          ...profile.routes,
          ...(profile.activeProvider ? ["active provider"] : []),
          ...(profile.fallbackProvider ? ["fallback"] : [])
        ];
        return (
          <div key={profile.name} style={styles.row}>
            <span style={styles.label}>{profile.name}</span>
            <span style={{ flex: 1, fontSize: 11, color: profile.enabled ? COLOR.text : COLOR.textFaint }}>
              {profile.model ?? "no model"}
              {profile.enabled ? "" : " · disabled"}
              {" · "}
              {uses.length ? uses.join(", ") : "no route uses it yet"}
            </span>
          </div>
        );
      })}

      <div style={{ ...styles.row, borderBottom: "none" }}>
        <span style={styles.hint}>
          Signs in once for this computer; the sign-in stays in your LearnLoop config folder, never in a vault.
          Route a task to a chatgpt_plan profile in learnloop.toml (see `learnloop ai status chatgpt --vault …`).
          This is separate from any LearnLoop charges: requests on a chatgpt_plan route count toward your ChatGPT plan.
        </span>
      </div>

      {plan.welcomePending ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="You're using your ChatGPT plan"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 50
          }}
        >
          <div
            style={{
              background: COLOR.bgElev,
              border: `1px solid ${COLOR.borderStrong}`,
              borderRadius: 6,
              padding: "20px 24px",
              maxWidth: 380,
              display: "flex",
              flexDirection: "column",
              gap: 12
            }}
          >
            <strong style={{ color: COLOR.text, fontSize: 14 }}>You're using your ChatGPT plan</strong>
            <span style={{ color: COLOR.textDim, fontSize: 12, lineHeight: 1.5 }}>
              AI requests that LearnLoop routes to a chatgpt_plan profile use your ChatGPT plan. You can manage
              usage in ChatGPT settings.
            </span>
            <button
              type="button"
              style={{ ...continueStyle, alignSelf: "flex-end" }}
              onClick={() => void run("welcome", () => api.chatgptPlanAcknowledgeWelcome())}
            >
              Got it
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
