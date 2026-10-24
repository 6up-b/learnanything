// Connect an AI once, say OK once (docs/specs/ux_learnloop_v1.md §6.6, §8.3,
// owner decision Q4). Continue with ChatGPT comes first and routes every use
// case to the plan; an OpenRouter key does the same; everything else lives in
// Settings. When an AI is already set up (e.g. Codex), the sheet asks for the
// one OK, in one sentence about what leaves this computer.

import { useEffect, useRef, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type { AiConnectionDto } from "../api/dto";
import { plainError } from "../copy/ingestErrors";
import { COLOR, FONT_MONO } from "./term";
import { screenLeavesKey } from "../app/keymap";

const POLL_MS = 1000;

const primary: CSSProperties = {
  background: "#000",
  border: "1px solid #000",
  borderRadius: 4,
  color: "#fff",
  fontSize: 13,
  fontWeight: 600,
  padding: "7px 16px",
  cursor: "pointer",
  alignSelf: "flex-start"
};

const quiet: CSSProperties = {
  background: "none",
  border: "none",
  padding: 0,
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 12,
  cursor: "pointer",
  textDecoration: "underline",
  textUnderlineOffset: 2,
  alignSelf: "flex-start"
};

async function openExternal(url: string) {
  const { openUrl } = await import("@tauri-apps/plugin-opener");
  await openUrl(url);
}

export function ConnectAISheet({
  onClose,
  onConnected,
  onOpenSettings
}: {
  onClose: () => void;
  onConnected: (connection: AiConnectionDto) => void;
  onOpenSettings: () => void;
}) {
  const [connection, setConnection] = useState<AiConnectionDto | null>(null);
  const [busy, setBusy] = useState(false);
  const [waitingForBrowser, setWaitingForBrowser] = useState(false);
  const [keyOpen, setKeyOpen] = useState(false);
  const [key, setKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    api.getAiConnection().then(
      (dto) => {
        if (alive.current) setConnection(dto);
      },
      (failure: unknown) => {
        if (alive.current) setError(plainError(failure).line);
      }
    );
    return () => {
      alive.current = false;
    };
  }, []);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { modal: true })) return;
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const connect = async (provider: "chatgpt" | "openrouter" | "current") => {
    setBusy(true);
    setError(null);
    try {
      const next = await api.connectAi({ provider });
      if (!alive.current) return;
      setConnection(next);
      onConnected(next);
      // The one-time OK closes once it lands (UX Phase 1 re-test: "Connected
      // … Close" stayed over the Library for the whole build and sat over the
      // next card). The books' own lines say what happens next ("◐ Writing
      // questions …"), and the settings dot turns green. A sign-in keeps its
      // "Connected" line: there the confirmation is the result.
      if (provider === "current" && next.needs === null) onClose();
    } catch (failure) {
      if (alive.current) setError(plainError(failure, "LearnLoop couldn't connect.").line);
    } finally {
      if (alive.current) setBusy(false);
    }
  };

  const continueWithChatGPT = async () => {
    if (connection?.chatgptSignedIn) {
      await connect("chatgpt");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const started = await api.chatgptPlanSigninStart({});
      if (started.authorizeUrl) await openExternal(started.authorizeUrl);
      setWaitingForBrowser(true);
      const attemptId = started.attempt?.id ?? null;
      // Follow the sign-in until the browser comes back, then connect.
      for (;;) {
        await new Promise((resolve) => setTimeout(resolve, POLL_MS));
        if (!alive.current) return;
        const status = await api.chatgptPlanStatus();
        const attempt = status.attempt;
        if (!attempt || (attemptId !== null && attempt.id !== attemptId)) break;
        if (attempt.status === "waiting") continue;
        setWaitingForBrowser(false);
        if (attempt.status === "succeeded") {
          await connect("chatgpt");
        } else if (attempt.status === "failed") {
          setError(attempt.error?.message ? `Signing in didn't finish: ${attempt.error.message}` : "Signing in didn't finish. Try again.");
        }
        return;
      }
      setWaitingForBrowser(false);
    } catch (failure) {
      if (alive.current) {
        setWaitingForBrowser(false);
        setError(plainError(failure, "Signing in didn't start.").line);
      }
    } finally {
      if (alive.current) setBusy(false);
    }
  };

  const connectKey = async () => {
    if (!key.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.setOpenrouterApiKey(key.trim());
      setKey("");
    } catch (failure) {
      if (alive.current) setError(plainError(failure, "LearnLoop couldn't save that key.").line);
      setBusy(false);
      return;
    }
    await connect("openrouter");
  };

  const needs = connection?.needs ?? null;
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Connect an AI"
      style={{ position: "fixed", inset: 0, zIndex: 80, background: "rgba(0,0,0,0.45)", display: "flex", alignItems: "center", justifyContent: "center" }}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: 560,
          maxWidth: "calc(100vw - 32px)",
          background: COLOR.bgElev,
          border: `1px solid ${COLOR.borderStrong}`,
          borderRadius: 6,
          padding: "22px 26px",
          display: "flex",
          flexDirection: "column",
          gap: 14,
          fontFamily: FONT_MONO,
          fontSize: 12,
          color: COLOR.textDim,
          lineHeight: 1.6
        }}
      >
        <div style={{ fontSize: 15, color: COLOR.text }}>Get questions on what you read</div>
        <div>LearnLoop uses an AI to write questions from your books and to give feedback on your answers.</div>

        {connection === null && !error ? <div>…</div> : null}

        {needs === "consent" ? (
          <>
            <div>LearnLoop is set up to use {connection?.providerLabel}.</div>
            <div style={{ color: COLOR.text }}>{connection?.whatLeaves}</div>
            <button type="button" style={primary} disabled={busy} onClick={() => void connect("current")}>
              OK
            </button>
          </>
        ) : null}

        {needs === "connect" ? (
          <>
            <button type="button" style={primary} disabled={busy} onClick={() => void continueWithChatGPT()}>
              Continue with ChatGPT
            </button>
            {waitingForBrowser ? <div>Waiting for the browser…</div> : null}
            <button type="button" style={quiet} onClick={() => setKeyOpen((open) => !open)}>
              Use an OpenRouter key
            </button>
            {keyOpen ? (
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <input
                  aria-label="OpenRouter key"
                  type="password"
                  value={key}
                  onChange={(event) => setKey(event.target.value)}
                  style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "4px 8px", flex: 1 }}
                />
                <button
                  type="button"
                  disabled={busy || !key.trim()}
                  onClick={() => void connectKey()}
                  style={{ ...quiet, textDecoration: "none", border: `1px solid ${COLOR.borderStrong}`, padding: "4px 10px", color: COLOR.text }}
                >
                  Connect
                </button>
              </div>
            ) : null}
            <button type="button" style={quiet} onClick={onOpenSettings}>
              Other (advanced) ▸
            </button>
            <div style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 10 }}>
              What leaves this computer: passages of the books you add, and your answers, go to the AI you connect. Your
              library stays here.
              {connection?.deciderNote ? ` ${connection.deciderNote}` : null}
            </div>
          </>
        ) : null}

        {needs === null && connection !== null ? (
          <div style={{ color: COLOR.text }}>Connected to {connection.providerLabel}. Questions are on.</div>
        ) : null}

        {error ? (
          <div role="alert" style={{ color: COLOR.amber }}>
            {error}
          </div>
        ) : null}

        <button type="button" style={{ ...quiet, alignSelf: "flex-end" }} onClick={onClose}>
          {needs === null && connection !== null ? "Close" : "Not now"}
        </button>
      </div>
    </div>
  );
}
