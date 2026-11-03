// Mobile M2a (§6.5): a start found a session open on another device.

import type { CSSProperties } from "react";
import { useElsewhereQuestion } from "../app/sessionHandoff";
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

export function SessionElsewherePrompt() {
  const question = useElsewhereQuestion();
  if (!question) return null;
  const { details, answer } = question;
  const where = details.owner_label || "another device";
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="A session is open elsewhere"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 80,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0, 0, 0, 0.5)"
      }}
    >
      <div
        style={{
          width: 420,
          maxWidth: "calc(100vw - 32px)",
          background: COLOR.bgElev,
          border: `1px solid ${COLOR.borderStrong}`,
          borderRadius: 6,
          padding: "14px 16px",
          display: "flex",
          flexDirection: "column",
          gap: 10,
          fontFamily: FONT_MONO,
          fontSize: 12,
          color: COLOR.textDim,
          lineHeight: 1.5
        }}
      >
        <div style={{ color: COLOR.text }}>You have a session open on {where}.</div>
        {details.has_draft ? (
          <div>It has an unsent answer{details.draft_first_line ? `: “${details.draft_first_line}”` : "."}</div>
        ) : null}
        <div>Continue it here, or start fresh. Starting fresh keeps that answer on record.</div>
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button type="button" style={{ ...button, border: "none" }} onClick={() => answer("cancel")}>Cancel</button>
          <button type="button" style={button} onClick={() => answer("fresh")}>Start fresh</button>
          <button type="button" style={{ ...button, color: COLOR.amberLink }} onClick={() => answer("adopt")}>Continue it here</button>
        </div>
      </div>
    </div>
  );
}
