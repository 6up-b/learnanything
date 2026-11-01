// The one blob-URL video player (Reader RW5d P2b lifted it out of the concept
// inspector, spec_reader_show_me_figures_v1 §9b.3): the concept inspector's
// animations and the Reader's Manim figures both play content-addressed mp4s
// from the llmedia:// store through it.
import { useEffect, useState } from "react";
import { convertFileSrc } from "@tauri-apps/api/core";
import { COLOR, FONT_MONO, Faint } from "./term";

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
export function useAnimationBlobUrl(fileName: string | null, attempt: number) {
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

export function AnimationPlayer({ fileName, label }: { fileName: string; label?: string }) {
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
          aria-label={label}
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
