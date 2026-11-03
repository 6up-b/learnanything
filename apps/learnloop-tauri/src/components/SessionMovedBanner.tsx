// Mobile M2a (§6.5): "This session continued on your phone". The desktop has stopped writing
// to it (the practice screen is frozen, and the sidecar refuses a write that gets through).

import { useState, type CSSProperties } from "react";
import type { SessionMoved } from "../app/sessionMoved";
import { COLOR, FONT_MONO } from "./term";

const button: CSSProperties = {
  background: "none",
  border: `1px solid ${COLOR.borderStrong}`,
  borderRadius: 4,
  color: COLOR.text,
  fontFamily: FONT_MONO,
  fontSize: 12,
  padding: "4px 10px",
  cursor: "pointer"
};

export function SessionMovedBanner({
  moved,
  onAdoptBack,
  onStartFresh,
  onLetGo
}: {
  moved: SessionMoved | null;
  onAdoptBack: (moved: SessionMoved) => Promise<void>;
  onStartFresh: (moved: SessionMoved) => Promise<void>;
  /** A session that ended elsewhere: this desktop stops holding it, and starts nothing. */
  onLetGo: () => void;
}) {
  const [busy, setBusy] = useState(false);
  if (!moved) return null;
  const where = moved.ownerLabel || "your phone";
  const run = (action: (moved: SessionMoved) => Promise<void>) => {
    setBusy(true);
    void action(moved).finally(() => setBusy(false));
  };
  return (
    <div
      role="status"
      aria-label="Session moved"
      style={{
        position: "fixed",
        left: "50%",
        transform: "translateX(-50%)",
        bottom: 16,
        zIndex: 70,
        width: 460,
        maxWidth: "calc(100vw - 32px)",
        background: COLOR.bgElev,
        border: `1px solid ${COLOR.borderStrong}`,
        borderRadius: 6,
        padding: "12px 14px",
        display: "flex",
        flexDirection: "column",
        gap: 8,
        fontFamily: FONT_MONO,
        fontSize: 12,
        color: COLOR.textDim,
        lineHeight: 1.5
      }}
    >
      {moved.reason === "adopted" ? (
        <>
          <div style={{ color: COLOR.text }}>This session continued on {where}.</div>
          <div>Nothing here is being saved to it now. Your answers from there carry over if you take it back.</div>
        </>
      ) : (
        <div style={{ color: COLOR.text }}>This session ended on another device.</div>
      )}
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <button type="button" style={button} disabled={busy} onClick={() => run(onStartFresh)}>Start fresh</button>
        {moved.reason === "adopted" ? (
          <button type="button" style={{ ...button, color: COLOR.amberLink }} disabled={busy} onClick={() => run(onAdoptBack)}>
            Take it back
          </button>
        ) : (
          <button type="button" style={{ ...button, color: COLOR.amberLink }} disabled={busy} onClick={onLetGo}>OK</button>
        )}
      </div>
    </div>
  );
}
