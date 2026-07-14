import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { CommandError, SourceSetDto, SourceSetSummaryDto } from "../api/dto";
import { COLOR, Faint, FONT_MONO, TermSelect } from "./term";

// Shared "add to collection…" panel (§4.3). A source joins a source set here; the
// membership — not the source — carries role, scope, and priority, and pins the
// current revision so later re-extractions don't silently change what synthesis
// reads. Used on ready library rows AND on the build-plan step, so it takes a
// resolved (sourceId, revisionId) plus the unit scope to pin (empty = whole
// source). upsert_source_set replaces the whole member list, so adding to an
// existing set re-sends its members with the new one appended.

// The canonical source-role vocabulary (role_authority.KNOWN_ROLES / §4.2).
const SOURCE_ROLES = [
  "primary_textbook",
  "lecture",
  "paper",
  "reference",
  "alternate_explanation",
  "problem_set",
  "exam",
  "notes"
] as const;

function kebab(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function AddToCollectionPanel({
  sourceId,
  revisionId,
  scopeUnitIds,
  seedRole,
  onClose,
  onAdded
}: {
  sourceId: string;
  revisionId: string | null;
  scopeUnitIds: string[];
  seedRole: string | null;
  onClose: () => void;
  onAdded: (setId: string, setTitle: string) => void;
}): JSX.Element {
  const [sets, setSets] = useState<SourceSetSummaryDto[]>([]);
  const [subjects, setSubjects] = useState<string[]>([]);
  const [mode, setMode] = useState<"existing" | "new">("new");
  const [selectedSetId, setSelectedSetId] = useState<string>("");
  const [newName, setNewName] = useState("");
  const [newSubjectId, setNewSubjectId] = useState<string>("");
  const [role, setRole] = useState<string>(seedRole || "reference");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void Promise.all([api.listSourceSets(), api.loadVault()])
      .then(([setsSnap, vault]) => {
        if (cancelled) return;
        const list = setsSnap.sourceSets ?? [];
        setSets(list);
        setSubjects(vault.vault?.subjects ?? []);
        if (list.length > 0) {
          setMode("existing");
          setSelectedSetId(list[0].id);
        }
      })
      .catch((e) => {
        if (!cancelled) setError((e as CommandError).message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const confirm = useCallback(async () => {
    if (!revisionId) {
      setError("This source has no pinned revision yet — finish extraction first.");
      return;
    }
    const member = {
      sourceId,
      revisionId,
      defaultRole: role,
      scope: scopeUnitIds.map((unitId) => ({ unitId, roleOverride: null })),
      priority: 1
    };
    setBusy(true);
    setError(null);
    try {
      let payload: SourceSetDto;
      let title: string;
      if (mode === "existing") {
        if (!selectedSetId) {
          setError("Pick a collection.");
          setBusy(false);
          return;
        }
        const { sourceSet } = await api.getSourceSet(selectedSetId);
        // Re-pin: drop any prior membership for this exact revision, then append.
        const members = [
          ...sourceSet.members.filter((m) => !(m.sourceId === sourceId && m.revisionId === revisionId)),
          member
        ];
        payload = { id: sourceSet.id, subjectId: sourceSet.subjectId, title: sourceSet.title, members };
        title = sourceSet.title;
      } else {
        const id = kebab(newName);
        if (!id) {
          setError("Name the collection.");
          setBusy(false);
          return;
        }
        if (!newSubjectId) {
          setError("Pick a subject for the new collection.");
          setBusy(false);
          return;
        }
        payload = { id, subjectId: newSubjectId, title: newName.trim(), members: [member] };
        title = newName.trim();
      }
      const { sourceSet } = await api.upsertSourceSet(payload);
      setDone(sourceSet.title);
      onAdded(sourceSet.id, title);
    } catch (e) {
      setError((e as CommandError).message);
    } finally {
      setBusy(false);
    }
  }, [mode, selectedSetId, newName, newSubjectId, role, revisionId, sourceId, scopeUnitIds, onAdded]);

  const scopeLabel = scopeUnitIds.length > 0 ? `${scopeUnitIds.length} unit(s)` : "whole source";

  return (
    <div style={{ border: `1px solid ${COLOR.amber}`, background: "#1c1710", padding: "12px 14px", display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
        <span style={{ color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 12 }}>add to collection</span>
        <Faint style={{ fontSize: 11 }}>pins this revision · scope {scopeLabel}</Faint>
        <span style={{ flex: 1 }} />
        <span onClick={onClose} style={{ cursor: "pointer", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 12 }}>
          ✕
        </span>
      </div>

      {done ? (
        <Faint style={{ fontSize: 12, color: COLOR.green }}>✓ pinned to {done}</Faint>
      ) : (
        <>
          {!revisionId && (
            <Faint style={{ fontSize: 11, color: COLOR.amber }}>no pinned revision — finish extraction first.</Faint>
          )}

          <div style={{ display: "flex", gap: 6 }}>
            {sets.length > 0 && (
              <ModeChip label="use existing" on={mode === "existing"} onClick={() => setMode("existing")} />
            )}
            <ModeChip label="new collection" on={mode === "new"} onClick={() => setMode("new")} />
          </div>

          {mode === "existing" ? (
            <TermSelect
              value={selectedSetId}
              options={sets.map((s) => ({ value: s.id, label: `${s.title} · ${s.memberCount}` }))}
              onChange={setSelectedSetId}
              placeholder="pick a collection…"
              width={260}
            />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => e.stopPropagation()}
                placeholder="collection name"
                style={{ background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}`, padding: "6px 10px", fontFamily: FONT_MONO, fontSize: 12, outline: "none" }}
              />
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Faint style={{ fontSize: 11 }}>subject</Faint>
                <TermSelect
                  value={newSubjectId}
                  options={subjects}
                  onChange={setNewSubjectId}
                  placeholder="pick a subject…"
                  width={200}
                />
              </div>
            </div>
          )}

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              title="the source's authority in this collection — finalized on membership, not on the source. Pins the current revision so later re-extractions don't change what synthesis reads."
              style={{ color: COLOR.textFaint, fontSize: 11, cursor: "help", textDecoration: "underline dotted", textUnderlineOffset: 3 }}
            >
              role
            </span>
            <TermSelect value={role} options={SOURCE_ROLES as unknown as string[]} onChange={setRole} width={200} />
          </div>

          {error && <Faint style={{ fontSize: 11, color: COLOR.red }}>{error}</Faint>}

          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ flex: 1 }} />
            <span
              onClick={() => {
                if (!busy && revisionId) void confirm();
              }}
              style={{
                padding: "5px 12px",
                border: `1px solid ${busy || !revisionId ? COLOR.border : COLOR.amber}`,
                background: busy || !revisionId ? "transparent" : "#241d12",
                color: busy || !revisionId ? COLOR.textFaint : COLOR.amber,
                fontFamily: FONT_MONO,
                fontSize: 12,
                cursor: busy || !revisionId ? "default" : "pointer"
              }}
            >
              {busy ? "pinning…" : mode === "new" ? "create & pin →" : "pin to collection →"}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

function ModeChip({ label, on, onClick }: { label: string; on: boolean; onClick: () => void }) {
  return (
    <span
      onClick={onClick}
      style={{
        padding: "3px 10px",
        fontSize: 11,
        fontFamily: FONT_MONO,
        border: `1px solid ${on ? COLOR.amber : COLOR.border}`,
        background: on ? "#241d12" : "transparent",
        color: on ? COLOR.amber : COLOR.textDim,
        cursor: "pointer"
      }}
    >
      {label}
    </span>
  );
}
