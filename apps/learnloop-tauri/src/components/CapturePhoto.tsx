import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CaptureMediaDto } from "../api/capture";
import { COLOR } from "./term";
import { errorMessage } from "../errors";

/**
 * Desktop-only preview of a photo capture. The sidecar resolves the image from
 * the capture's stored content hash; no filesystem path is ever named here.
 */
export function CapturePhoto({ captureId, maxHeight = 320 }: { captureId: string; maxHeight?: number }) {
  const [media, setMedia] = useState<CaptureMediaDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let alive = true;
    setMedia(null);
    setError(null);
    api.getCaptureMedia(captureId).then(
      (value) => { if (alive) setMedia(value); },
      (err) => { if (alive) setError(errorMessage(err, "Could not load the captured photo.")); }
    );
    return () => { alive = false; };
  }, [captureId]);

  if (error) return <p role="alert" style={{ color: COLOR.red }}>{error}</p>;
  if (!media) return <p style={{ color: COLOR.textFaint }}>Loading photo…</p>;
  return (
    <figure style={{ margin: "8px 0" }}>
      <img
        src={media.dataUrl}
        alt="Captured photo"
        onClick={() => setExpanded((value) => !value)}
        style={{ display: "block", maxWidth: "100%", maxHeight: expanded ? "none" : maxHeight, cursor: expanded ? "zoom-out" : "zoom-in", border: `1px solid ${COLOR.border}` }}
      />
      <figcaption style={{ color: COLOR.textFaint, fontSize: 11 }}>
        {media.originalWidth}×{media.originalHeight} original · click to {expanded ? "shrink" : "enlarge"}
      </figcaption>
    </figure>
  );
}
