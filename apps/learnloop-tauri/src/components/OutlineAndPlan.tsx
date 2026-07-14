import { useCallback, useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../api/client";
import type {
  BuildPlan,
  BuildPlanStage,
  CommandError,
  EffectiveOutlineDto,
  EffectiveUnitDto,
  OutlineUnit,
  SelectionPreviewDto,
  SourceOutline,
  StartExtractionRepairInput
} from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill, SectionHeader, TermSelect } from "./term";
import { AddToCollectionPanel } from "./AddToCollection";

// The canonical source-role vocabulary (role_authority.KNOWN_ROLES / §4.2), in
// the spec's ordering. Authority is finalized on source-set MEMBERSHIP, not here —
// this control records the learner's intended role for the import-batch flow,
// which has no collection yet.
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
// Roles that carry assessment-only authority: they never define concepts (§4.2).
const ASSESSMENT_ONLY_ROLES = new Set(["exam", "problem_set"]);

// ING M3 (source-ingestion v2 §5.7): the Outline & unit-selection screen and the
// Build-plan screen. Both are deterministic previews with ZERO pedagogical LLM
// calls — the outline is a byte-stable read of the extraction, the plan sums token
// budgets. The only egress-capable action here is consent-gated page repair.

function Card({ children, style = {} }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div style={{ border: `1px solid ${COLOR.border}`, borderRadius: 2, padding: "14px 18px", ...style }}>{children}</div>
  );
}

const SIGNAL_ORDER = ["examples", "exercises", "equations", "figures", "definitions", "theorems", "tables"];

// ── Model-input preview ──────────────────────────────────────────────────
// The byte-exact display markdown the authoring batch feeds the model for the
// current selection. Deterministic backend render, zero LLM calls. `unitIds`
// null falls back to the persisted selection (used on the plan step). While the
// panel is open it re-fetches on `revalidateKey` changes (debounced) so the
// preview tracks the learner's edits without blanking.
function ModelInputPreview({
  extractionRef,
  unitIds,
  revalidateKey,
  onClose
}: {
  extractionRef: string;
  unitIds: string[] | null;
  revalidateKey: string;
  onClose: () => void;
}) {
  const [preview, setPreview] = useState<SelectionPreviewDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const firstFetch = useRef(true);

  useEffect(() => {
    let cancelled = false;
    const isFirst = firstFetch.current;
    firstFetch.current = false;
    if (isFirst) setLoading(true);
    else setRefreshing(true);
    const run = () => {
      api
        .getSelectionPreview(extractionRef, unitIds)
        .then((next) => {
          if (cancelled) return;
          setPreview(next);
          setError(null);
        })
        .catch((e) => {
          if (cancelled) return;
          setError((e as CommandError).message);
        })
        .finally(() => {
          if (cancelled) return;
          setLoading(false);
          setRefreshing(false);
        });
    };
    const timer = window.setTimeout(run, isFirst ? 0 : 500);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
    // `unitIds` is read fresh whenever `revalidateKey` changes (which encodes the
    // selection + boundary overrides), so it is intentionally not a dep.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [extractionRef, revalidateKey]);

  return (
    <div style={{ border: `1px solid ${COLOR.border}`, background: COLOR.bg }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          background: COLOR.bgElev,
          borderBottom: `1px solid ${COLOR.border}`,
          padding: "8px 14px",
          fontSize: 12
        }}
      >
        <span style={{ fontFamily: FONT_MONO, color: COLOR.textDim }}>
          model input · {preview ? preview.approxTokens.toLocaleString() : "…"} tokens ≈
        </span>
        {refreshing && <Faint style={{ fontSize: 11 }}>refreshing…</Faint>}
        <span style={{ flex: 1 }} />
        <span onClick={onClose} style={{ cursor: "pointer", color: COLOR.textFaint, fontFamily: FONT_MONO }}>
          ✕
        </span>
      </div>
      <div style={{ padding: "6px 14px" }}>
        <Faint style={{ fontSize: 11 }}>
          this is the exact markdown the authoring batch feeds the model for your selection — figures become [Figure: …]
          placeholders; unselected units are omitted.
        </Faint>
      </div>
      {loading ? (
        <div style={{ padding: "12px 16px" }}>
          <Faint>◐ rendering…</Faint>
        </div>
      ) : error ? (
        <div style={{ padding: "12px 16px", color: COLOR.red, fontSize: 12 }}>{error}</div>
      ) : (
        <div
          className="ll-scroll"
          style={{
            maxHeight: 320,
            overflowY: "auto",
            padding: "12px 16px",
            fontFamily: FONT_MONO,
            fontSize: 12.5,
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            color: COLOR.text
          }}
        >
          {preview?.markdown}
        </div>
      )}
    </div>
  );
}

// Amber toggle link that opens/closes the model-input preview panel.
function PreviewToggle({ open, onToggle }: { open: boolean; onToggle: () => void }) {
  return (
    <span onClick={onToggle} style={{ color: COLOR.amber, cursor: "pointer", fontSize: 12, fontFamily: FONT_MONO }}>
      {open ? "hide model input" : "preview model input →"}
    </span>
  );
}

// ── Flow shell: outline → build plan → start batch ──────────────────────
export function OutlinePlanFlow({
  sourceRef,
  sourceUri,
  subjectId,
  suggestedRole = null,
  onClose,
  onOpenBatch
}: {
  sourceRef: string;
  sourceUri: string | null;
  subjectId: string | null;
  suggestedRole?: string | null;
  onClose: () => void;
  onOpenBatch: (batchId: string) => void;
}) {
  const [step, setStep] = useState<"outline" | "plan">("outline");
  const [outline, setOutline] = useState<SourceOutline | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  // The learner's persisted role override for this selection (empty = none). Falls
  // back to the library's suggested role for display when there is no override.
  const [role, setRole] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const next = await api.getSourceOutline(sourceRef);
      setOutline(next);
      const prior = next.selection.selectedUnitIds;
      setSelected(new Set(prior.length ? prior : next.units.map((u) => u.unitId)));
      const priorOverrides: Record<string, string> = {};
      for (const ov of next.selection.boundaryOverrides) {
        const unitId = ov["unitId"] as string | undefined;
        const op = ov["op"] as string | undefined;
        if (unitId && op) priorOverrides[unitId] = op;
      }
      setOverrides(priorOverrides);
      setRole(next.selection.roleOverride ?? "");
      setError(null);
    } catch (e) {
      setError((e as CommandError).message);
    } finally {
      setLoading(false);
    }
  }, [sourceRef]);

  useEffect(() => {
    void load();
  }, [load]);

  // Esc steps back through the flow: plan → outline, outline → close. Ignored
  // while a text field is focused so it never eats an in-progress edit.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== "Escape") return;
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (step === "plan") setStep("outline");
      else onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [step, onClose]);

  function toggleUnit(unitId: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(unitId)) next.delete(unitId);
      else next.add(unitId);
      return next;
    });
  }

  function cycleOverride(unitId: string) {
    setOverrides((current) => {
      const next = { ...current };
      const now = next[unitId];
      if (!now) next[unitId] = "merge_with_next";
      else if (now === "merge_with_next") next[unitId] = "split_at_heading";
      else delete next[unitId];
      return next;
    });
  }

  async function persistSelection(roleValue: string = role) {
    if (!outline) return;
    const boundaryOverrides = Object.entries(overrides).map(([unitId, op]) => ({ op, unitId }));
    await api.saveUnitSelection({
      extractionId: outline.extractionId,
      selectedUnitIds: [...selected],
      boundaryOverrides,
      roleOverride: roleValue || null
    });
  }

  // Persist the role choice immediately (mirrors the auto-persisting selection).
  async function onRoleChange(nextRole: string) {
    setRole(nextRole);
    try {
      await persistSelection(nextRole);
      setError(null);
    } catch (e) {
      setError((e as CommandError).message);
    }
  }

  async function toPlan() {
    try {
      await persistSelection();
      setStep("plan");
      setError(null);
    } catch (e) {
      setError((e as CommandError).message);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "10px 24px",
          borderBottom: `1px solid ${COLOR.border}`,
          background: COLOR.bgElev,
          flexShrink: 0
        }}
      >
        {/* back is contextual (mirrors esc): plan → outline, outline → library */}
        <span
          onClick={() => (step === "plan" ? setStep("outline") : onClose())}
          style={{
            color: COLOR.textDim,
            cursor: "pointer",
            fontFamily: FONT_MONO,
            fontSize: 12,
            border: `1px solid ${COLOR.border}`,
            padding: "3px 12px"
          }}
        >
          ← back
        </span>
        {/* spacer between back and the step group (≥ the intra-group gap) */}
        <span style={{ width: 32, flexShrink: 0 }} />
        {/* Flat [chip][arrow][chip] trio with one uniform gap and both boxes
            always visible — equal 150px chips make the arrow the exact visual
            midpoint regardless of label length or which step is active. */}
        <span style={{ display: "inline-flex", alignItems: "center", gap: 24 }}>
          {([
            { id: "outline" as const, label: "1 · outline" },
            { id: "plan" as const, label: "2 · build plan" }
          ]).map((s, index) => {
            const active = step === s.id;
            return (
              <span key={s.id} style={{ display: "contents" }}>
                {index > 0 && (
                  <span
                    style={{
                      color: step === "plan" ? COLOR.amber : COLOR.textFaint,
                      fontSize: 15,
                      fontWeight: 700
                    }}
                  >
                    ⟶
                  </span>
                )}
                <span
                  onClick={() => {
                    if (s.id === "outline") setStep("outline");
                    else if (step === "outline") void toPlan();
                  }}
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 12,
                    padding: "3px 0",
                    width: 150,
                    display: "inline-flex",
                    justifyContent: "center",
                    cursor: "pointer",
                    border: `1px solid ${active ? COLOR.amber : COLOR.border}`,
                    background: active ? "#241d12" : "transparent",
                    color: active ? COLOR.amber : COLOR.textDim
                  }}
                >
                  {s.label}
                </span>
              </span>
            );
          })}
        </span>
        <span style={{ flex: 1 }} />
        <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>esc back</Faint>
      </div>

      {error && <div style={{ color: COLOR.red, fontSize: 12, padding: "8px 24px" }}>{error}</div>}

      {loading || !outline ? (
        <div style={{ padding: 24, color: COLOR.textFaint }}>◐ loading outline…</div>
      ) : step === "outline" ? (
        <OutlineView
          outline={outline}
          selected={selected}
          overrides={overrides}
          role={role}
          suggestedRole={suggestedRole}
          onRoleChange={onRoleChange}
          onToggle={toggleUnit}
          onCycleOverride={cycleOverride}
          onSave={() => persistSelection()}
          onNext={toPlan}
          onRepaired={load}
        />
      ) : (
        <BuildPlanView
          outline={outline}
          sourceUri={sourceUri}
          selectedUnitIds={[...selected]}
          subjectId={subjectId}
          role={role}
          suggestedRole={suggestedRole}
          onBack={() => setStep("outline")}
          onOpenBatch={onOpenBatch}
        />
      )}
    </div>
  );
}

// ── Resulting-shape strip (live boundary-override preview, §5.3) ──────────
// Deterministic backend read of how the learner's merge/split intents reshape
// the units. Debounced refetch as overrides change; keeps the last shape while
// refreshing so the strip never blanks. Only rendered when ≥1 override is set.
function kindGlyph(unit: EffectiveUnitDto): { glyph: string; color: string } {
  if (unit.kind === "merged") return { glyph: "⊕", color: COLOR.amber };
  if (unit.kind === "split") return { glyph: "⊘", color: COLOR.cyan };
  return { glyph: "·", color: COLOR.textFaint };
}

function ResultingShape({
  extractionRef,
  overrides
}: {
  extractionRef: string;
  overrides: Record<string, string>;
}) {
  const [shape, setShape] = useState<EffectiveOutlineDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const overridesKey = JSON.stringify(overrides);

  useEffect(() => {
    let cancelled = false;
    setRefreshing(true);
    const boundaryOverrides = Object.entries(overrides).map(([unitId, op]) => ({ op, unitId }));
    const run = () => {
      api
        .getEffectiveOutline(extractionRef, boundaryOverrides)
        .then((next) => {
          if (cancelled) return;
          setShape(next);
          setError(null);
        })
        .catch((e) => {
          if (cancelled) return;
          setError((e as CommandError).message);
        })
        .finally(() => {
          if (!cancelled) setRefreshing(false);
        });
    };
    const timer = window.setTimeout(run, 400);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
    // `overrides` is read fresh whenever its serialized key changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [extractionRef, overridesKey]);

  const units = shape?.units ?? [];
  return (
    <div style={{ border: `1px solid ${COLOR.border}`, background: COLOR.bg }}>
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: 10,
          background: COLOR.bgElev,
          borderBottom: `1px solid ${COLOR.border}`,
          padding: "8px 14px",
          flexWrap: "wrap"
        }}
      >
        <Faint style={{ fontFamily: FONT_MONO, fontSize: 12 }}>resulting units · {units.length}</Faint>
        {refreshing && <Faint style={{ fontSize: 11 }}>refreshing…</Faint>}
        <span style={{ flex: 1 }} />
        <Faint style={{ fontSize: 11 }}>boundary overrides preview — how units will be treated after re-extraction</Faint>
      </div>
      {error && <div style={{ padding: "10px 14px", color: COLOR.red, fontSize: 12 }}>{error}</div>}
      <div style={{ display: "flex", flexDirection: "column" }}>
        {units.map((unit) => {
          const { glyph, color } = kindGlyph(unit);
          return (
            <div
              key={unit.effectiveId}
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: 10,
                padding: "5px 14px",
                borderTop: `1px solid ${COLOR.border}`,
                fontSize: 12
              }}
            >
              <span style={{ color, fontFamily: FONT_MONO, width: 14, flexShrink: 0, textAlign: "center" }}>{glyph}</span>
              <span
                style={{ color: COLOR.text, flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                title={unit.label}
              >
                {unit.label}
              </span>
              {unit.splitNoop && (
                <Faint style={{ color: COLOR.amber, fontSize: 11, flexShrink: 0 }}>
                  no level-2 headings — split has no effect
                </Faint>
              )}
              <Faint style={{ fontFamily: FONT_MONO, fontSize: 11, flexShrink: 0 }}>
                ~{unit.approxTokens.toLocaleString()}t · {unit.blockCount} blocks
              </Faint>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Role control (§4.2) ──────────────────────────────────────────────────
// Records the learner's intended source role. Authority is finalized on
// source-set MEMBERSHIP, not here — the tooltip says so, and the import-batch
// flow does not consume this yet, so the control never overclaims.
function RoleControl({
  role,
  suggestedRole,
  onRoleChange
}: {
  role: string;
  suggestedRole: string | null;
  onRoleChange: (role: string) => void;
}) {
  const effectiveRole = role || suggestedRole || "";
  const overridden = role !== "" && suggestedRole != null && role !== suggestedRole;
  const assessmentOnly = ASSESSMENT_ONLY_ROLES.has(effectiveRole);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginTop: -4 }}>
      <span
        title="a source's authority is finalized on collection (source-set) membership; this records your intended role for the build"
        style={{
          color: COLOR.textFaint,
          fontSize: 12,
          cursor: "help",
          textDecoration: "underline dotted",
          textUnderlineOffset: 3
        }}
      >
        role
      </span>
      <TermSelect
        value={effectiveRole}
        options={SOURCE_ROLES as unknown as string[]}
        onChange={onRoleChange}
        placeholder="choose role…"
        width={210}
      />
      {overridden && <Faint style={{ fontSize: 11 }}>suggested: {suggestedRole}</Faint>}
      {assessmentOnly && (
        <Faint style={{ color: COLOR.amber, fontSize: 11 }}>
          assessment-only authority — never defines concepts
        </Faint>
      )}
    </div>
  );
}

// ── Outline & unit selection ─────────────────────────────────────────────
function OutlineView({
  outline,
  selected,
  overrides,
  role,
  suggestedRole,
  onRoleChange,
  onToggle,
  onCycleOverride,
  onSave,
  onNext,
  onRepaired
}: {
  outline: SourceOutline;
  selected: Set<string>;
  overrides: Record<string, string>;
  role: string;
  suggestedRole: string | null;
  onRoleChange: (role: string) => void;
  onToggle: (unitId: string) => void;
  onCycleOverride: (unitId: string) => void;
  onSave: () => Promise<void>;
  onNext: () => void;
  onRepaired: () => void;
}) {
  const [repairOpen, setRepairOpen] = useState(false);
  const [saved, setSaved] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const selectedIds = outline.units.filter((u) => selected.has(u.unitId)).map((u) => u.unitId);
  const selectedCount = selectedIds.length;
  const selectedTokens = outline.units.filter((u) => selected.has(u.unitId)).reduce((sum, u) => sum + u.approxTokens, 0);

  async function save() {
    await onSave();
    setSaved(true);
    window.setTimeout(() => setSaved(false), 1500);
  }

  return (
    <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "18px 24px", display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
        <SectionHeader style={{ marginTop: 0 }}>{outline.title}</SectionHeader>
        <Pill color="slate">{outline.extractor}</Pill>
        <Faint>
          {outline.unitCount} units · {outline.blockCount} blocks · ~{outline.approxTokens.toLocaleString()} tokens
        </Faint>
        {outline.difficultPageCount > 0 && (
          <span
            onClick={() => setRepairOpen(true)}
            style={{ color: COLOR.amber, cursor: "pointer", fontSize: 12, fontFamily: FONT_MONO }}
          >
            ⚠ improve {outline.difficultPageCount} difficult page{outline.difficultPageCount === 1 ? "" : "s"} →
          </span>
        )}
      </div>

      <RoleControl role={role} suggestedRole={suggestedRole} onRoleChange={onRoleChange} />

      {outline.selection.needsReview.length > 0 && (
        <div style={{ border: `1px solid ${COLOR.amber}`, background: "#241d12", padding: "8px 14px", fontSize: 12, color: COLOR.amber }}>
          {outline.selection.needsReview.length} prior selection(s) could not be re-anchored after re-extraction and need review:{" "}
          <span style={{ fontFamily: FONT_MONO }}>{outline.selection.needsReview.join(", ")}</span>
        </div>
      )}

      {outline.units.length === 1 ? (
        <SingleUnitSummary
          unit={outline.units[0]}
          totalTokens={outline.approxTokens}
          override={overrides[outline.units[0].unitId] ?? null}
          onCycleOverride={() => onCycleOverride(outline.units[0].unitId)}
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {outline.units.map((unit) => (
            <UnitRow
              key={unit.unitId}
              unit={unit}
              checked={selected.has(unit.unitId)}
              override={overrides[unit.unitId] ?? null}
              onToggle={() => onToggle(unit.unitId)}
              onCycleOverride={() => onCycleOverride(unit.unitId)}
            />
          ))}
        </div>
      )}

      {Object.keys(overrides).length > 0 && (
        <ResultingShape extractionRef={outline.extractionId} overrides={overrides} />
      )}

      <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 6, flexWrap: "wrap" }}>
        <Faint>
          {selectedCount}/{outline.units.length} units selected · ~{selectedTokens.toLocaleString()} tokens
        </Faint>
        <PreviewToggle open={previewOpen} onToggle={() => setPreviewOpen((v) => !v)} />
        <span style={{ flex: 1 }} />
        <button onClick={() => void save()} style={buttonStyle(false)}>
          {saved ? "✓ saved" : "save selection"}
        </button>
        <button onClick={onNext} style={buttonStyle(selectedCount > 0)} disabled={selectedCount === 0}>
          build plan →
        </button>
      </div>

      {previewOpen && (
        <ModelInputPreview
          extractionRef={outline.extractionId}
          unitIds={selectedIds}
          revalidateKey={`${selectedIds.join(",")}|${JSON.stringify(overrides)}`}
          onClose={() => setPreviewOpen(false)}
        />
      )}

      {repairOpen && (
        <RepairDialog
          outline={outline}
          onClose={() => setRepairOpen(false)}
          onStarted={() => {
            setRepairOpen(false);
            onRepaired();
          }}
        />
      )}
    </div>
  );
}

function UnitRow({
  unit,
  checked,
  override,
  onToggle,
  onCycleOverride
}: {
  unit: OutlineUnit;
  checked: boolean;
  override: string | null;
  onToggle: () => void;
  onCycleOverride: () => void;
}) {
  const pages =
    unit.pageStart != null ? `p${unit.pageStart}${unit.pageEnd && unit.pageEnd !== unit.pageStart ? `–${unit.pageEnd}` : ""}` : null;
  const signals = SIGNAL_ORDER.filter((k) => (unit.structuralSignals[k] ?? 0) > 0).map((k) => `${k} ${unit.structuralSignals[k]}`);
  return (
    <Card style={{ borderLeft: `3px solid ${checked ? COLOR.amber : COLOR.border}`, display: "flex", gap: 12 }}>
      <span onClick={onToggle} style={{ cursor: "pointer", color: checked ? COLOR.amber : COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 14, userSelect: "none" }}>
        {checked ? "[✓]" : "[ ]"}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
          <span style={{ color: COLOR.text, fontSize: 13, fontWeight: 600 }}>{unit.label || unit.unitId}</span>
          {pages && <Faint style={{ fontFamily: FONT_MONO, fontSize: 11 }}>{pages}</Faint>}
          <Faint style={{ fontSize: 11 }}>~{unit.approxTokens.toLocaleString()} tokens</Faint>
          {unit.inventory.inventoried && <Pill color="green">inventory cached</Pill>}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 5, flexWrap: "wrap", fontSize: 11 }}>
          {signals.length > 0 ? (
            <span style={{ color: COLOR.textDim, fontFamily: FONT_MONO }}>{signals.join(" · ")}</span>
          ) : (
            <Faint>prose</Faint>
          )}
          {unit.healthFlags.map((flag) => (
            <Pill key={flag} color="amber">{flag}</Pill>
          ))}
          <span style={{ flex: 1 }} />
          <span
            onClick={onCycleOverride}
            title="boundary override: merge-with-next / split-at-heading"
            style={{
              cursor: "pointer",
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: override ? COLOR.cyan : COLOR.textFaint,
              border: `1px solid ${override ? COLOR.cyan : COLOR.border}`,
              padding: "1px 8px"
            }}
          >
            {override ? `⤳ ${override.replace(/_/g, " ")}` : "⤳ boundary"}
          </span>
        </div>
      </div>
    </Card>
  );
}

// ── Single-unit summary (§5.7) ───────────────────────────────────────────
// Some sources extract to exactly one unit — a YouTube transcript, a short web
// page, a single-section note. A checkbox tree of one row is noise: there is
// nothing to deselect (dropping the only unit would send an empty batch), so we
// show a plain summary line and keep "all units selected". The boundary override
// stays visible as the manual split escape hatch — it's the only way to carve a
// one-unit source into sub-heading pieces before re-extraction.
function SingleUnitSummary({
  unit,
  totalTokens,
  override,
  onCycleOverride
}: {
  unit: OutlineUnit;
  totalTokens: number;
  override: string | null;
  onCycleOverride: () => void;
}) {
  // "document" reads wrong for a transcript-style unit; pick the noun from the
  // unit. A YouTube caption unit carries a time_range locator (backend
  // normalizers.captions_to_ir) even when its label is the video's own title, so
  // the locator scheme is the reliable signal; the label regex is a fallback.
  const label = unit.label || unit.unitId;
  const scheme = typeof unit.locator?.scheme === "string" ? (unit.locator.scheme as string) : "";
  const isTimed = scheme === "time_range" || /transcript|caption|subtitle/i.test(label);
  const noun = isTimed ? "transcript" : "document";
  return (
    <Card style={{ borderLeft: `3px solid ${COLOR.amber}`, display: "flex", flexDirection: "column", gap: 8 }}>
      <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
        single-unit source · {label} · ~{totalTokens.toLocaleString()} tokens · the whole {noun} will be used
      </Faint>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", fontSize: 11 }}>
        <span
          onClick={onCycleOverride}
          title="boundary override: merge-with-next / split-at-heading"
          style={{
            cursor: "pointer",
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: override ? COLOR.cyan : COLOR.textFaint,
            border: `1px solid ${override ? COLOR.cyan : COLOR.border}`,
            padding: "1px 8px"
          }}
        >
          {override ? `⤳ ${override.replace(/_/g, " ")}` : "⤳ boundary"}
        </span>
        <Faint style={{ fontSize: 11 }}>split by sub-headings via boundary →</Faint>
      </div>
    </Card>
  );
}

// ── Build plan ───────────────────────────────────────────────────────────
function BuildPlanView({
  outline,
  sourceUri,
  selectedUnitIds,
  subjectId,
  role,
  suggestedRole,
  onBack,
  onOpenBatch
}: {
  outline: SourceOutline;
  sourceUri: string | null;
  selectedUnitIds: string[];
  subjectId: string | null;
  role: string;
  suggestedRole: string | null;
  onBack: () => void;
  onOpenBatch: (batchId: string) => void;
}) {
  const [plan, setPlan] = useState<BuildPlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [addedTo, setAddedTo] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getBuildPlan([{ extractionId: outline.extractionId, selectedUnitIds }], subjectId)
      .then((next) => {
        if (!cancelled) setPlan(next);
      })
      .catch((e) => {
        if (!cancelled) setError((e as CommandError).message);
      });
    return () => {
      cancelled = true;
    };
  }, [outline.extractionId, subjectId, selectedUnitIds.join(",")]);

  const canStart = Boolean(sourceUri);
  async function startBatch() {
    if (!plan || !sourceUri) return;
    setStarting(true);
    setError(null);
    try {
      // The source is already imported; re-importing is idempotent and snapshots
      // the plan estimate onto the batch payload (§8.6.2).
      const batch = await api.startImportBatch({
        sources: [sourceUri],
        subjectId,
        estimate: plan.totals as unknown as Record<string, unknown>
      });
      onOpenBatch(batch.id);
    } catch (e) {
      setError((e as CommandError).message);
    } finally {
      setStarting(false);
    }
  }

  if (error) return <div style={{ padding: 24, color: COLOR.red, fontSize: 12 }}>{error}</div>;
  if (!plan) return <div style={{ padding: 24, color: COLOR.textFaint }}>◐ computing budget…</div>;

  const routingColor = plan.routing === "create" ? COLOR.green : COLOR.cyan;
  return (
    <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "18px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
        <SectionHeader style={{ marginTop: 0 }}>Build plan</SectionHeader>
        <span style={{ color: routingColor, fontFamily: FONT_MONO, fontSize: 12, border: `1px solid ${routingColor}`, padding: "1px 8px" }}>
          {plan.routing === "create" ? "＋ create study map" : "↻ update study map"}
        </span>
        <Faint>
          provider {plan.provider}
          {plan.providerContextTokens != null ? ` · context ${plan.providerContextTokens.toLocaleString()}` : ""}
        </Faint>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {plan.stages.map((stage) => (
          <StageRow key={stage.stage} stage={stage} />
        ))}
      </div>

      <div style={{ display: "flex", gap: 24, flexWrap: "wrap", fontSize: 12, fontFamily: FONT_MONO, color: COLOR.textDim }}>
        <span>
          <Faint>calls</Faint> {plan.totals.calls}
        </span>
        <span>
          <Faint>input</Faint> ~{plan.totals.inputTokens.toLocaleString()}t
        </span>
        <span>
          <Faint>max output</Faint> ≤{plan.totals.maxOutputTokens.toLocaleString()}t
        </span>
        <span style={{ color: plan.totals.cacheSavingsTokens > 0 ? COLOR.green : COLOR.textDim }}>
          <Faint>cache savings</Faint> ~{plan.totals.cacheSavingsTokens.toLocaleString()}t
        </span>
      </div>

      <ConsentSummary plan={plan} />

      <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
        <PreviewToggle open={previewOpen} onToggle={() => setPreviewOpen((v) => !v)} />
        <span
          onClick={() => setAddOpen((v) => !v)}
          title="pin this source (at its current revision) and the selected units into a collection with a role — the collection is what synthesis reads and groups"
          style={{ color: COLOR.amberLink, cursor: "pointer", fontSize: 12, fontFamily: FONT_MONO }}
        >
          {addOpen ? "hide add to collection" : "add to collection →"}
        </span>
        {addedTo && <Faint style={{ fontSize: 11, color: COLOR.green }}>✓ pinned to {addedTo}</Faint>}
      </div>

      {addOpen && (
        <AddToCollectionPanel
          sourceId={outline.sourceId ?? outline.extractionId}
          revisionId={outline.revisionId}
          scopeUnitIds={selectedUnitIds}
          seedRole={role || suggestedRole}
          onClose={() => setAddOpen(false)}
          onAdded={(_setId, setTitle) => {
            setAddedTo(setTitle);
            setAddOpen(false);
          }}
        />
      )}

      {previewOpen && (
        <ModelInputPreview
          extractionRef={outline.extractionId}
          unitIds={null}
          revalidateKey="plan"
          onClose={() => setPreviewOpen(false)}
        />
      )}

      {plan.warnings.length > 0 && (
        <div style={{ border: `1px solid ${COLOR.amber}`, background: "#241d12", padding: "8px 14px", fontSize: 12, color: COLOR.amber, display: "flex", flexDirection: "column", gap: 4 }}>
          {plan.warnings.map((w) => (
            <span key={w}>⚠ {w}</span>
          ))}
        </div>
      )}

      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <button onClick={onBack} style={buttonStyle(false)}>
          ← units
        </button>
        <span style={{ flex: 1 }} />
        <Faint>
          will create: {plan.whatWillBeCreated.selectedUnits} unit(s) from {plan.whatWillBeCreated.sources} source(s)
        </Faint>
        <button
          onClick={() => void startBatch()}
          style={buttonStyle(canStart)}
          disabled={starting || !canStart}
          title={canStart ? "" : "no canonical URI to re-import from"}
        >
          {starting ? "starting…" : "start batch →"}
        </button>
      </div>
    </div>
  );
}

function StageRow({ stage }: { stage: BuildPlanStage }) {
  const color = stage.exceedsCeiling ? COLOR.red : COLOR.cyan;
  const pct = Math.min(100, (stage.inputTokens / Math.max(stage.ceiling, 1)) * 100);
  return (
    <Card style={{ borderLeft: `3px solid ${color}`, display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ color: COLOR.text, fontSize: 13, fontWeight: 600 }}>{stage.stage}</span>
        <Faint style={{ fontFamily: FONT_MONO, fontSize: 11 }}>{stage.calls} call(s)</Faint>
        <span style={{ flex: 1 }} />
        {stage.exceedsCeiling && <Pill color="red">over ceiling</Pill>}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, fontFamily: FONT_MONO }}>
        <Faint style={{ width: 90 }}>input vs ceiling</Faint>
        <div style={{ flex: 1, height: 6, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, position: "relative" }}>
          <div style={{ position: "absolute", inset: 0, width: `${pct}%`, background: color }} />
        </div>
        <span style={{ color: COLOR.text, minWidth: 150, textAlign: "right" }}>
          ~{stage.inputTokens.toLocaleString()}t / {stage.ceiling.toLocaleString()}t
        </span>
      </div>
      <Faint style={{ fontFamily: FONT_MONO, fontSize: 11 }}>
        max output ≤{stage.maxOutputTokens.toLocaleString()}t
        {stage.cachedTokens > 0 ? ` · cached ~${stage.cachedTokens.toLocaleString()}t` : ""}
      </Faint>
    </Card>
  );
}

function ConsentSummary({ plan }: { plan: BuildPlan }) {
  // Everything in a build plan stays on-device; the only egress in M3 is a
  // consent-gated page repair, surfaced separately. This makes that explicit.
  return (
    <div style={{ fontSize: 11, color: COLOR.textFaint, fontFamily: FONT_MONO }}>
      ▪ nothing in this plan leaves the device — synthesis runs against the local provider ({plan.provider}); external page
      repair is a separate, consent-gated action.
    </div>
  );
}

// ── Consent-gated repair dialog (§2.5) ───────────────────────────────────
function RepairDialog({
  outline,
  onClose,
  onStarted
}: {
  outline: SourceOutline;
  onClose: () => void;
  onStarted: () => void;
}) {
  const [pages, setPages] = useState("");
  const [forceOcr, setForceOcr] = useState(true);
  const [inlineMath, setInlineMath] = useState(false);
  const [tableProcessing, setTableProcessing] = useState(false);
  const [useLlm, setUseLlm] = useState(false);
  const [consented, setConsented] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function start() {
    if (!outline.revisionId) {
      setError("This extraction has no revision to repair.");
      return;
    }
    if (!consented) {
      setError("Confirm consent to run the repair.");
      return;
    }
    const pageList = pages
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (pageList.length === 0) {
      setError("Enter at least one page or range (e.g. 3-5,8).");
      return;
    }
    const input: StartExtractionRepairInput = {
      revisionId: outline.revisionId,
      pages: pageList,
      consent: {
        provider: useLlm ? "external_vlm" : "local",
        purpose: "extraction_repair",
        pages: pageList,
        cached: false,
        external: useLlm
      },
      repairOptions: { forceOcr, inlineMath, tableProcessing, useLlm },
      parentExtractionId: outline.extractionId
    };
    setBusy(true);
    setError(null);
    try {
      await api.startExtractionRepair(input);
      onStarted();
    } catch (e) {
      setError((e as CommandError).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ width: 480, maxWidth: "90vw", background: COLOR.bg, border: `1px solid ${COLOR.amber}`, padding: "18px 20px", display: "flex", flexDirection: "column", gap: 12 }}
      >
        <div style={{ color: COLOR.amber, fontSize: 14, fontWeight: 600 }}>Improve difficult pages</div>
        <Faint style={{ fontSize: 12, lineHeight: 1.5 }}>
          Re-extracts only the pages you name, composing the result with the current extraction. Unaffected units keep their
          content hashes. {outline.difficultPageCount} page(s) currently flagged.
        </Faint>

        <label style={{ fontSize: 12, color: COLOR.textDim, display: "flex", flexDirection: "column", gap: 4 }}>
          pages (e.g. 3-5,8)
          <input
            value={pages}
            onChange={(e) => setPages(e.target.value)}
            placeholder="3-5,8"
            style={{ background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}`, padding: "6px 10px", fontFamily: FONT_MONO, fontSize: 13, outline: "none" }}
          />
        </label>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <OptionChip label="force OCR" on={forceOcr} onToggle={() => setForceOcr((v) => !v)} />
          <OptionChip label="inline math" on={inlineMath} onToggle={() => setInlineMath((v) => !v)} />
          <OptionChip label="table processing" on={tableProcessing} onToggle={() => setTableProcessing((v) => !v)} />
          <OptionChip label="external VLM" on={useLlm} onToggle={() => setUseLlm((v) => !v)} danger />
        </div>

        <label style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 12, color: useLlm ? COLOR.amber : COLOR.textDim, cursor: "pointer" }}>
          <input type="checkbox" checked={consented} onChange={(e) => setConsented(e.target.checked)} />
          <span>
            I consent to {useLlm ? "sending these pages to an external VLM service" : "re-running local extraction"} for repair.
            {useLlm && " This leaves the device."}
          </span>
        </label>

        {error && <div style={{ color: COLOR.red, fontSize: 12 }}>{error}</div>}

        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button onClick={onClose} style={buttonStyle(false)}>
            cancel
          </button>
          <button onClick={() => void start()} style={buttonStyle(consented)} disabled={busy || !consented}>
            {busy ? "starting…" : "run repair"}
          </button>
        </div>
      </div>
    </div>
  );
}

function OptionChip({ label, on, onToggle, danger = false }: { label: string; on: boolean; onToggle: () => void; danger?: boolean }) {
  const color = on ? (danger ? COLOR.red : COLOR.amber) : COLOR.textFaint;
  return (
    <span
      onClick={onToggle}
      style={{ cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, color, border: `1px solid ${on ? color : COLOR.border}`, padding: "3px 10px", background: on ? "#241d12" : "transparent" }}
    >
      {on ? "☑" : "☐"} {label}
    </span>
  );
}

function buttonStyle(primary: boolean): CSSProperties {
  return {
    padding: "6px 14px",
    fontSize: 12,
    fontFamily: FONT_MONO,
    border: `1px solid ${primary ? COLOR.amber : COLOR.border}`,
    background: primary ? "#241d12" : "transparent",
    color: primary ? COLOR.amber : COLOR.textDim,
    cursor: "pointer"
  };
}
