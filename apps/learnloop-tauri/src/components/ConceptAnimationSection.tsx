import { useEffect, useRef, useState } from "react";
import { convertFileSrc } from "@tauri-apps/api/core";
import { api } from "../api/client";
import type { AnimationRuntimeDto, ConceptAnimationDto, StoryboardDto } from "../api/dto";
import { COLOR, FONT_MONO, Faint } from "./term";
import { MarkdownMath } from "../render/MarkdownMath";

const PENDING_STATUSES = new Set(["queued", "generating", "validating", "rendering"]);

const PHASE_LABEL: Record<string, Record<string, string>> = {
  manim: {
    queued: "queued",
    generating: "authoring scene code",
    validating: "validating scene code",
    rendering: "rendering with manim"
  },
  video_model: {
    queued: "queued",
    generating: "writing the storyboard",
    validating: "checking the storyboard",
    rendering: "video model generating shots (may take minutes)"
  }
};

function phaseLabel(status: string, renderer: string): string {
  return PHASE_LABEL[renderer]?.[status] ?? PHASE_LABEL.manim[status] ?? status;
}

const LINK_STYLE = {
  color: COLOR.amberLink,
  cursor: "pointer",
  fontFamily: FONT_MONO,
  fontSize: 12,
  background: "none",
  border: "none",
  padding: 0
} as const;

const CODEC_HINT =
  "this webview cannot decode H.264: install gstreamer1.0-libav (Debian/Ubuntu) or gst-libav (Arch) and restart the app";

type MediaFailure = { message: string; hint: string | null };

function describeMediaError(error: MediaError | null): MediaFailure {
  const detail = error?.message ? ` (${error.message})` : "";
  switch (error?.code) {
    case 1:
      return { message: `playback aborted${detail}`, hint: null };
    case 2:
      return { message: `network error while loading the video${detail}`, hint: null };
    case 3:
      return { message: `the video could not be decoded${detail}`, hint: CODEC_HINT };
    case 4:
      return { message: `the video format is not supported here${detail}`, hint: CODEC_HINT };
    default:
      return { message: `playback failed${detail}`, hint: null };
  }
}

// A native <video src="llmedia://…"> does not reliably range-request a custom
// URI scheme in WebKitGTK, so the bytes are fetched (like the PDF reader does
// over llpdf://) and played from an in-memory blob URL, which is seekable.
// `attempt` re-runs the fetch on demand (retry link).
function useAnimationBlobUrl(fileName: string | null, attempt: number) {
  const [url, setUrl] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    setUrl(null);
    setLoadError(null);
    if (!fileName) return;
    let cancelled = false;
    let objectUrl: string | null = null;
    fetch(convertFileSrc(fileName, "llmedia"))
      .then((response) => {
        if (!response.ok) throw new Error(`animation store returned HTTP ${response.status}`);
        return response.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch((error: unknown) => {
        if (!cancelled) setLoadError(error instanceof Error ? error.message : String(error));
      });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [fileName, attempt]);

  return { url, loadError };
}

function AnimationPlayer({ fileName }: { fileName: string }) {
  const [attempt, setAttempt] = useState(0);
  const [playbackError, setPlaybackError] = useState<MediaFailure | null>(null);
  const { url, loadError } = useAnimationBlobUrl(fileName, attempt);

  useEffect(() => {
    setPlaybackError(null);
  }, [url]);

  const failure: MediaFailure | null = loadError
    ? { message: `could not load the video: ${loadError}`, hint: null }
    : playbackError;

  return (
    <div>
      {url ? (
        <video
          controls
          preload="metadata"
          style={{ width: "100%", border: `1px solid ${COLOR.border}`, background: "#000" }}
          src={url}
          onError={(event) => setPlaybackError(describeMediaError(event.currentTarget.error))}
        />
      ) : !failure ? (
        <Faint style={{ fontSize: 12 }}>loading video…</Faint>
      ) : null}
      {failure ? (
        <div style={{ marginTop: 4, fontSize: 11, lineHeight: 1.5 }}>
          <div style={{ color: COLOR.red }}>{failure.message}</div>
          {failure.hint ? <div style={{ color: COLOR.textDim }}>{failure.hint}</div> : null}
          <button type="button" style={LINK_STYLE} onClick={() => setAttempt((value) => value + 1)}>
            retry
          </button>
        </div>
      ) : null}
    </div>
  );
}

function StoryboardList({ storyboard }: { storyboard: StoryboardDto }) {
  return (
    <ol style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 11, color: COLOR.textDim, lineHeight: 1.5 }}>
      {storyboard.shots.map((shot, index) => (
        <li key={index} style={{ marginBottom: 4 }}>
          <span style={{ color: COLOR.text }}>{shot.caption || `shot ${index + 1}`}</span>
          {shot.durationSeconds ? <Faint style={{ fontSize: 10 }}> · {shot.durationSeconds}s</Faint> : null}
          <div style={{ color: COLOR.textFaint }}>{shot.prompt}</div>
        </li>
      ))}
      {typeof storyboard.totalCost === "number" ? (
        <Faint style={{ display: "block", fontSize: 10 }}>reported cost: ${storyboard.totalCost.toFixed(2)}</Faint>
      ) : null}
    </ol>
  );
}

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

  const pollStatus = (animationId: string, renderer: string = "manim") => {
    stopPolling();
    // Video jobs take minutes and are polled by the sidecar every 30 s; the
    // inspector need not hammer the RPC channel for them.
    const interval = renderer === "video_model" ? 5000 : 2000;
    pollRef.current = window.setInterval(() => {
      api
        .getConceptAnimationStatus(animationId)
        .then((row) => {
          setLatest(row);
          if (!PENDING_STATUSES.has(row.status)) stopPolling();
        })
        .catch(() => stopPolling());
    }, interval);
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
        if (preferred && PENDING_STATUSES.has(preferred.status)) pollStatus(preferred.animationId, preferred.renderer);
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
        renderer: runtime?.renderer ?? "manim",
        storyboard: null,
        videoJobIds: [],
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
      pollStatus(requested.animationId, runtime?.renderer ?? "manim");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (runtime && !runtime.enabled) {
    return <Faint>animations are disabled ([animation] enabled = false in learnloop.toml)</Faint>;
  }
  const videoRenderer = runtime?.renderer === "video_model";
  if (runtime && videoRenderer && !runtime.videoReady) {
    return (
      <div style={{ fontSize: 12, color: COLOR.textDim, lineHeight: 1.5 }}>
        <div>video model not ready: {runtime.videoReason ?? "no video model configured"}.</div>
        <div style={{ fontFamily: FONT_MONO, color: COLOR.textFaint, marginTop: 4 }}>
          configure in Settings → Animation (renderer, video model, OpenRouter key)
        </div>
      </div>
    );
  }
  if (runtime && !videoRenderer && runtime.manimAvailable === false) {
    return (
      <div style={{ fontSize: 12, color: COLOR.textDim, lineHeight: 1.5 }}>
        <div>manim is not installed{runtime.manimReason ? ` (${runtime.manimReason})` : ""}.</div>
        <div style={{ fontFamily: FONT_MONO, color: COLOR.textFaint, marginTop: 4 }}>
          reinstall the app&apos;s Python environment (uv sync) · verify: python -m manim --version
        </div>
      </div>
    );
  }

  return (
    <div>
      {latest?.status === "completed" && latest.videoFileName ? (
        <div>
          <AnimationPlayer fileName={latest.videoFileName} />
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
              {latest.renderer === "video_model" && latest.storyboard
                ? ` · ${latest.storyboard.shots.length} shot${latest.storyboard.shots.length === 1 ? "" : "s"}`
                : ""}
            </Faint>
            <button type="button" style={LINK_STYLE} onClick={() => setConsentOpen(true)}>
              regenerate…
            </button>
            {latest.storyboard ? (
              <button type="button" style={LINK_STYLE} onClick={() => setShowDebug((value) => !value)}>
                {showDebug ? "hide storyboard" : "show storyboard"}
              </button>
            ) : null}
          </div>
          {showDebug && latest.storyboard ? <StoryboardList storyboard={latest.storyboard} /> : null}
        </div>
      ) : latest && PENDING_STATUSES.has(latest.status) ? (
        <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.amber }}>
          ◐ {phaseLabel(latest.status, latest.renderer)}…
        </div>
      ) : latest?.status === "cancelled" ? (
        <div style={{ fontSize: 12, lineHeight: 1.5 }}>
          <div style={{ color: COLOR.textDim }}>generation cancelled{latest.videoJobIds.length ? " · submitted shots are still billed" : ""}.</div>
          <div style={{ marginTop: 4, display: "flex", gap: 12 }}>
            <button type="button" style={LINK_STYLE} onClick={() => setConsentOpen(true)}>
              generate again…
            </button>
          </div>
        </div>
      ) : latest?.status === "failed" ? (
        <div style={{ fontSize: 12, lineHeight: 1.5 }}>
          <div style={{ color: COLOR.red }}>
            generation failed at {latest.failureStage ?? "unknown"}: {latest.failureReason ?? "unknown error"}
          </div>
          <div style={{ marginTop: 4, display: "flex", gap: 12 }}>
            <button type="button" style={LINK_STYLE} onClick={() => setConsentOpen(true)}>
              retry…
            </button>
            {(latest.renderStderr || latest.sceneCode || latest.storyboard || latest.videoJobIds.length) ? (
              <button type="button" style={LINK_STYLE} onClick={() => setShowDebug((value) => !value)}>
                {showDebug ? "hide details" : "show details"}
              </button>
            ) : null}
          </div>
          {showDebug && latest.storyboard ? <StoryboardList storyboard={latest.storyboard} /> : null}
          {showDebug && latest.videoJobIds.length ? (
            <Faint style={{ display: "block", fontSize: 10, marginTop: 4 }}>
              OpenRouter jobs (billed on submission): {latest.videoJobIds.join(", ")}
            </Faint>
          ) : null}
          {showDebug && (latest.renderStderr || latest.sceneCode) ? (
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
        <button type="button" style={LINK_STYLE} onClick={() => setConsentOpen(true)}>
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
              {videoRenderer ? (
                <>
                  Send this concept&apos;s description to{" "}
                  <b>{runtime ? `${runtime.provider}${runtime.model ? ` (${runtime.model})` : ""}` : "the routed AI provider"}</b>{" "}
                  to write a short storyboard (up to {runtime?.videoMaxShots ?? 4} shots), then generate each shot with{" "}
                  <b>{runtime?.videoModel ?? "the video model"}</b> through OpenRouter — billed per shot to your OpenRouter
                  account, usually 2–10 minutes, {runtime?.timeoutSeconds ?? 1800}s cap. No code runs locally.
                </>
              ) : (
                <>
                  Send this concept&apos;s description to{" "}
                  <b>{runtime ? `${runtime.provider}${runtime.model ? ` (${runtime.model})` : ""}` : "the routed AI provider"}</b>{" "}
                  and run the AI-written Manim scene locally (validated, temp directory,{" "}
                  {runtime?.timeoutSeconds ?? 600}s cap). Generated code is not reviewed by a human before running.
                </>
              )}
            </span>
          </label>
          <div style={{ marginTop: 8, display: "flex", gap: 12 }}>
            <button
              type="button"
              style={{ ...LINK_STYLE, color: consentTicked && !busy ? COLOR.amber : COLOR.textFaint }}
              disabled={!consentTicked || busy}
              onClick={() => void generate()}
            >
              {busy ? "…" : "generate"}
            </button>
            <button type="button" style={{ ...LINK_STYLE, color: COLOR.textFaint }} onClick={() => setConsentOpen(false)}>
              cancel
            </button>
          </div>
        </div>
      ) : null}

      {error ? <div style={{ marginTop: 6, color: COLOR.red, fontSize: 11 }}>{error}</div> : null}
    </div>
  );
}
