import { useEffect, useRef, useState } from "react";
import { convertFileSrc } from "@tauri-apps/api/core";
import { api } from "../api/client";
import type { AnimationRuntimeDto, ConceptAnimationDto } from "../api/dto";
import { COLOR, FONT_MONO, Faint } from "./term";
import { MarkdownMath } from "../render/MarkdownMath";

const PENDING_STATUSES = new Set(["queued", "generating", "validating", "rendering"]);

const PHASE_LABEL: Record<string, string> = {
  queued: "queued",
  generating: "authoring scene code",
  validating: "validating scene code",
  rendering: "rendering with manim"
};

export function ConceptAnimationSection({ conceptId }: { conceptId: string }) {
  const [runtime, setRuntime] = useState<AnimationRuntimeDto | null>(null);
  const [latest, setLatest] = useState<ConceptAnimationDto | null>(null);
  const [consentOpen, setConsentOpen] = useState(false);
  const [consentTicked, setConsentTicked] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showDebug, setShowDebug] = useState(false);
  const pollRef = useRef<number | null>(null);

  const stopPolling = () => {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const pollStatus = (animationId: string) => {
    stopPolling();
    pollRef.current = window.setInterval(() => {
      api
        .getConceptAnimationStatus(animationId)
        .then((row) => {
          setLatest(row);
          if (!PENDING_STATUSES.has(row.status)) stopPolling();
        })
        .catch(() => stopPolling());
    }, 2000);
  };

  useEffect(() => {
    let cancelled = false;
    setLatest(null);
    setError(null);
    setConsentOpen(false);
    setConsentTicked(false);
    api.getAnimationRuntime().then((value) => !cancelled && setRuntime(value)).catch(() => {});
    api
      .listConceptAnimations(conceptId)
      .then((result) => {
        if (cancelled) return;
        const rows = result.animations ?? [];
        const preferred =
          rows.find((row) => row.status === "completed") ??
          rows.find((row) => PENDING_STATUSES.has(row.status)) ??
          rows[0] ??
          null;
        setLatest(preferred);
        if (preferred && PENDING_STATUSES.has(preferred.status)) pollStatus(preferred.animationId);
      })
      .catch((err) => !cancelled && setError((err as Error).message));
    return () => {
      cancelled = true;
      stopPolling();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conceptId]);

  const generate = async () => {
    setBusy(true);
    setError(null);
    try {
      const requested = await api.requestConceptAnimation({ conceptId, consent: true });
      setConsentOpen(false);
      setConsentTicked(false);
      setLatest({
        animationId: requested.animationId,
        conceptId,
        learningObjectId: null,
        status: requested.status,
        title: null,
        narrationMd: null,
        videoFileName: null,
        durationSeconds: null,
        provider: null,
        model: null,
        failureStage: null,
        failureReason: null
      });
      pollStatus(requested.animationId);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const linkStyle = {
    color: COLOR.amberLink,
    cursor: "pointer",
    fontFamily: FONT_MONO,
    fontSize: 12,
    background: "none",
    border: "none",
    padding: 0
  } as const;

  if (runtime && !runtime.enabled) {
    return <Faint>animations are disabled ([animation] enabled = false in learnloop.toml)</Faint>;
  }
  if (runtime && !runtime.manimAvailable) {
    return (
      <div style={{ fontSize: 12, color: COLOR.textDim, lineHeight: 1.5 }}>
        <div>manim is not installed{runtime.manimReason ? ` (${runtime.manimReason})` : ""}.</div>
        <div style={{ fontFamily: FONT_MONO, color: COLOR.textFaint, marginTop: 4 }}>
          pip install &quot;learnloop[animation]&quot; · verify: python -m manim --version
        </div>
      </div>
    );
  }

  return (
    <div>
      {latest?.status === "completed" && latest.videoFileName ? (
        <div>
          <video
            controls
            style={{ width: "100%", border: `1px solid ${COLOR.border}`, background: "#000" }}
            src={convertFileSrc(latest.videoFileName, "llmedia")}
          />
          {latest.title ? (
            <div style={{ marginTop: 6, fontSize: 12, color: COLOR.text }}>{latest.title}</div>
          ) : null}
          {latest.narrationMd ? (
            <div style={{ marginTop: 4, fontSize: 12, color: COLOR.textDim }}>
              <MarkdownMath value={latest.narrationMd} />
            </div>
          ) : null}
          <div style={{ marginTop: 6, display: "flex", gap: 12, alignItems: "baseline" }}>
            <Faint style={{ fontSize: 10 }}>
              {latest.provider ? `${latest.provider}${latest.model ? ` · ${latest.model}` : ""}` : ""}
            </Faint>
            <button type="button" style={linkStyle} onClick={() => setConsentOpen(true)}>
              regenerate…
            </button>
          </div>
        </div>
      ) : latest && PENDING_STATUSES.has(latest.status) ? (
        <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.amber }}>
          ◐ {PHASE_LABEL[latest.status] ?? latest.status}…
        </div>
      ) : latest?.status === "failed" ? (
        <div style={{ fontSize: 12, lineHeight: 1.5 }}>
          <div style={{ color: COLOR.red }}>
            generation failed at {latest.failureStage ?? "unknown"}: {latest.failureReason ?? "unknown error"}
          </div>
          <div style={{ marginTop: 4, display: "flex", gap: 12 }}>
            <button type="button" style={linkStyle} onClick={() => setConsentOpen(true)}>
              retry…
            </button>
            {(latest.renderStderr || latest.sceneCode) ? (
              <button type="button" style={linkStyle} onClick={() => setShowDebug((value) => !value)}>
                {showDebug ? "hide details" : "show details"}
              </button>
            ) : null}
          </div>
          {showDebug ? (
            <pre
              style={{
                marginTop: 6,
                maxHeight: 220,
                overflow: "auto",
                background: COLOR.bgInput,
                border: `1px solid ${COLOR.border}`,
                padding: 8,
                fontSize: 10,
                whiteSpace: "pre-wrap"
              }}
            >
              {[latest.renderStderr, latest.sceneCode].filter(Boolean).join("\n\n--- scene code ---\n\n")}
            </pre>
          ) : null}
        </div>
      ) : !consentOpen ? (
        <button type="button" style={linkStyle} onClick={() => setConsentOpen(true)}>
          + generate animation
        </button>
      ) : null}

      {consentOpen ? (
        <div style={{ marginTop: 8, border: `1px solid ${COLOR.border}`, padding: 10, fontSize: 12 }}>
          <label style={{ display: "flex", alignItems: "flex-start", gap: 10, cursor: "pointer" }}>
            <span
              style={{ fontFamily: FONT_MONO, color: consentTicked ? COLOR.amber : COLOR.textFaint, fontSize: 15 }}
              onClick={() => setConsentTicked((value) => !value)}
            >
              {consentTicked ? "▣" : "▢"}
            </span>
            <span style={{ color: COLOR.text, lineHeight: 1.5 }} onClick={() => setConsentTicked((value) => !value)}>
              Send this concept&apos;s description to{" "}
              <b>{runtime ? `${runtime.provider}${runtime.model ? ` (${runtime.model})` : ""}` : "the routed AI provider"}</b>{" "}
              and run the AI-written Manim scene locally (validated, temp directory,{" "}
              {runtime?.timeoutSeconds ?? 300}s cap). Generated code is not reviewed by a human before running.
            </span>
          </label>
          <div style={{ marginTop: 8, display: "flex", gap: 12 }}>
            <button
              type="button"
              style={{ ...linkStyle, color: consentTicked && !busy ? COLOR.amber : COLOR.textFaint }}
              disabled={!consentTicked || busy}
              onClick={() => void generate()}
            >
              {busy ? "…" : "generate"}
            </button>
            <button type="button" style={{ ...linkStyle, color: COLOR.textFaint }} onClick={() => setConsentOpen(false)}>
              cancel
            </button>
          </div>
        </div>
      ) : null}

      {error ? <div style={{ marginTop: 6, color: COLOR.red, fontSize: 11 }}>{error}</div> : null}
    </div>
  );
}
