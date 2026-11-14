// An inline "make a subject" row for dialogs that require a subject. A vault
// can have none (new-vault onboarding lets the student skip the first one), and
// a required picker with nothing in it is a dead end. Uses the same CLI call as
// the Ingest screen's "+ new subject".

import { useState } from "react";
import { api } from "../api/client";
import { errorMessage } from "../errors";
import { COLOR, FONT_MONO } from "./term";

export function subjectIdFromTitle(title: string): string {
  return title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

export function NewSubjectControl({
  disabled = false,
  onCreated,
  onError
}: {
  disabled?: boolean;
  onCreated: (subject: { id: string; title: string }) => void;
  onError: (message: string | null) => void;
}) {
  const [title, setTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const id = subjectIdFromTitle(title);
  const blocked = disabled || creating || !id;

  async function create() {
    if (blocked) return;
    const trimmed = title.trim();
    setCreating(true);
    onError(null);
    try {
      const res = await api.runCliCommand(["add-subject", id, trimmed]);
      if (res.exitCode !== 0) {
        onError(res.stderr.trim() || `add-subject failed (exit ${res.exitCode})`);
        return;
      }
      setTitle("");
      onCreated({ id, title: trimmed });
    } catch (err) {
      onError(errorMessage(err, "Could not create the subject."));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={(e) => {
          e.stopPropagation();
          if (e.key === "Enter") void create();
        }}
        placeholder="new subject title"
        disabled={disabled || creating}
        style={{
          width: 240,
          background: COLOR.bgInput,
          color: COLOR.text,
          border: `1px solid ${COLOR.border}`,
          padding: "6px 10px",
          fontFamily: FONT_MONO,
          fontSize: 12,
          outline: "none"
        }}
      />
      <button
        type="button"
        onClick={() => void create()}
        disabled={blocked}
        style={{
          padding: "6px 12px",
          border: `1px solid ${COLOR.borderStrong}`,
          background: "transparent",
          color: COLOR.textDim,
          fontFamily: FONT_MONO,
          fontSize: 12,
          cursor: blocked ? "default" : "pointer",
          opacity: blocked ? 0.4 : 1
        }}
      >
        {creating ? "creating…" : "create subject"}
      </button>
    </div>
  );
}
