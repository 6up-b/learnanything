// The library exemplar picker (spec_p2 §3.1 — the previously deferred discovery
// slice): pick a goal, a learning object, familiar-anchor exemplars, and one
// unseen sibling; compose + register a draft blueprint (template-authored,
// owner-reviewed here via the three §3.2 checks); then the ONE atomic
// confirmation starts a real certifying run. This replaces the fixture-only
// Golden Path front door — the offline demo stays reachable, clearly labeled.

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import type {
  CommandError,
  ComposeDraftResult,
  ExemplarPoolEntryDto,
  GoalDto,
  RunListEntryDto,
} from "../../api/dto";
import { COLOR, Card, Dim, Faint, FONT_MONO, KeyBar, Meta, Pill, SectionHeader } from "../term";
import { PrimaryButton, SecondaryButton } from "./shared";
import { ExemplarConfirmDialog, type ConfirmInput } from "../ExemplarConfirmDialog";

const REVIEW_CHECKS = [
  { key: "source_grounded", label: "exemplars are grounded in material I actually studied" },
  { key: "rubric_verbatim", label: "the rubric matches what these tasks really require" },
  { key: "one_family", label: "these are one family of tasks (one skill, one unit)" },
] as const;

const EMPTY_ANCHORS: Set<string> = new Set();

export function GoldenPathSetup({
  onRunStarted,
  onOpenDemo,
  onError,
}: {
  onRunStarted: (runId: string) => void;
  onOpenDemo: () => void;
  onError: (message: string) => void;
}) {
  const [goals, setGoals] = useState<GoalDto[] | null>(null);
  const [pool, setPool] = useState<ExemplarPoolEntryDto[] | null>(null);
  const [goalId, setGoalId] = useState<string | null>(null);
  const [loId, setLoId] = useState<string | null>(null);
  // Keyed by learning object so browsing other families never wipes a pick.
  const [picks, setPicks] = useState<Map<string, { anchors: Set<string>; heldOut: string | null }>>(
    () => new Map(),
  );
  const [composed, setComposed] = useState<ComposeDraftResult | null>(null);
  const [checks, setChecks] = useState<Set<string>>(() => new Set());
  const [reviewed, setReviewed] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [runs, setRuns] = useState<RunListEntryDto[] | null>(null);

  useEffect(() => {
    // Existing runs first — a run spans days, and without this list an
    // in-flight run would be unreachable after an app restart.
    api.goldenPathListRuns().then((snap) => setRuns(snap.runs)).catch(() => setRuns([]));
    api.goalsList().then((snap) => setGoals(snap.goals)).catch(() => setGoals([]));
    api
      .blueprintDiscoverCandidates()
      .then((snap) => setPool(snap.pool))
      .catch((error) => {
        setPool([]);
        onError((error as CommandError).message);
      });
  }, [onError]);

  const activeGoals = useMemo(() => (goals ?? []).filter((g) => g.status === "active"), [goals]);
  const entry = useMemo(() => (pool ?? []).find((e) => e.learningObjectId === loId) ?? null, [pool, loId]);
  const anchors = (loId ? picks.get(loId)?.anchors : undefined) ?? EMPTY_ANCHORS;
  const heldOut = (loId ? picks.get(loId)?.heldOut : undefined) ?? null;

  // Changing the selection invalidates any composed draft.
  const resetDraft = useCallback(() => {
    setComposed(null);
    setChecks(new Set());
    setReviewed(false);
  }, []);

  const updatePick = (
    mutate: (prev: { anchors: Set<string>; heldOut: string | null }) => { anchors: Set<string>; heldOut: string | null },
  ) => {
    if (!loId) return;
    resetDraft();
    setPicks((prev) => {
      const next = new Map(prev);
      next.set(loId, mutate(next.get(loId) ?? { anchors: EMPTY_ANCHORS, heldOut: null }));
      return next;
    });
  };

  const toggleAnchor = (id: string) =>
    updatePick((pick) => {
      const anchors = new Set(pick.anchors);
      if (anchors.has(id)) anchors.delete(id);
      else anchors.add(id);
      return { anchors, heldOut: pick.heldOut === id ? null : pick.heldOut };
    });

  const chooseHeldOut = (id: string) =>
    updatePick((pick) => {
      const anchors = new Set(pick.anchors);
      anchors.delete(id);
      return { anchors, heldOut: id };
    });

  const compose = async () => {
    if (!loId || !heldOut || anchors.size === 0) return;
    setBusy(true);
    try {
      const result = await api.blueprintComposeDraft({
        learningObjectId: loId,
        anchorItemIds: [...anchors],
        heldOutItemId: heldOut,
      });
      setComposed(result);
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const review = async () => {
    if (!composed) return;
    setBusy(true);
    try {
      await api.blueprintReview(
        composed.blueprint.blueprintVersionId,
        Object.fromEntries([...checks].map((k) => [k, true])),
      );
      setReviewed(true);
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const confirmInput: Omit<ConfirmInput, "depthPreset"> | null = useMemo(() => {
    if (!composed || !reviewed || !goalId) return null;
    return {
      goalId,
      blueprintVersionId: composed.blueprint.blueprintVersionId,
      contractBody: JSON.parse(composed.contractBodyJson) as Record<string, unknown>,
      sourceRev: composed.sourceRev,
      unitId: composed.unitId,
      assessmentPracticeItemId: composed.heldOutItemId,
    };
  }, [composed, reviewed, goalId]);

  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
      <div style={{ flexShrink: 0, borderBottom: `1px solid ${COLOR.border}`, padding: "22px 32px", display: "flex", flexDirection: "column", gap: 8 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 11, letterSpacing: "0.18em", color: COLOR.textFaint }}>
            GOLDEN PATH · CHOOSE YOUR TASK
          </span>
          <span
            onClick={onOpenDemo}
            style={{ marginLeft: "auto", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textFaint, textDecoration: "underline", textUnderlineOffset: 2, cursor: "pointer" }}
          >
            open offline demo
          </span>
        </div>
        <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.textDim }}>
          pick tasks you actually want to master; one stays unseen as your held-out assessment.
        </span>
      </div>

      <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "18px 32px", display: "flex", flexDirection: "column", gap: 14, maxWidth: 760 }}>
        {runs && runs.length > 0 ? (
          <>
            <SectionHeader style={{ marginTop: 0 }}>Your runs</SectionHeader>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {runs.map((run) => {
                const done = run.currentState === "complete";
                return (
                  <Card
                    key={run.runId}
                    style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}
                  >
                    <Meta>{run.runId}</Meta>
                    <Pill color={done ? "green" : "amber"}>{run.currentState.replace(/_/g, " ")}</Pill>
                    <Pill color={run.mode === "certifying" ? "green" : "slate"}>{run.mode}</Pill>
                    <Faint style={{ fontSize: 11 }}>goal {run.goalId}</Faint>
                    <span style={{ marginLeft: "auto" }}>
                      <SecondaryButton onClick={() => onRunStarted(run.runId)}>
                        {done ? "view run →" : "resume run →"}
                      </SecondaryButton>
                    </span>
                  </Card>
                );
              })}
            </div>
            <Faint style={{ fontSize: 11 }}>…or start a new run below.</Faint>
          </>
        ) : null}

        <SectionHeader style={{ marginTop: runs && runs.length > 0 ? undefined : 0 }}>1 · Goal</SectionHeader>
        {goals === null ? (
          <Faint style={{ fontSize: 12 }}>◐ loading goals…</Faint>
        ) : activeGoals.length === 0 ? (
          <Faint style={{ fontSize: 12 }}>no active goal — create one from the Today tab first (the goal banner's "new goal").</Faint>
        ) : (
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {activeGoals.map((g) => (
              <SecondaryButton key={g.id} onClick={() => setGoalId(g.id)} active={goalId === g.id}>
                {g.title ?? g.id}
              </SecondaryButton>
            ))}
          </div>
        )}

        <SectionHeader>2 · Task family (learning object)</SectionHeader>
        {pool === null ? (
          <Faint style={{ fontSize: 12 }}>◐ loading exemplar pool…</Faint>
        ) : pool.length === 0 ? (
          <Faint style={{ fontSize: 12 }}>no active practice items yet — ingest a source and build a study map first.</Faint>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {pool.map((e) => (
              <Card
                key={e.learningObjectId}
                onClick={() => {
                  if (loId !== e.learningObjectId) {
                    setLoId(e.learningObjectId);
                    resetDraft();
                  }
                }}
                selected={loId === e.learningObjectId}
                style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: 10 }}
              >
                <span style={{ flex: 1, fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{e.title}</span>
                <Faint style={{ fontSize: 11 }}>{e.items.length} items</Faint>
              </Card>
            ))}
          </div>
        )}

        {entry ? (
          <>
            <SectionHeader>3 · Exemplars</SectionHeader>
            <Faint style={{ fontSize: 11 }}>
              mark 1–2 <Dim>anchors</Dim> (tasks like the ones you want to master) and exactly one <Dim>held-out</Dim> sibling —
              ideally one you have never attempted; it becomes the cold assessment.
            </Faint>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {entry.items.map((item) => {
                const isAnchor = anchors.has(item.practiceItemId);
                const isHeldOut = heldOut === item.practiceItemId;
                return (
                  <Card key={item.practiceItemId} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <span style={{ flex: 1, fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{item.prompt}</span>
                      {item.attempted ? <Pill color="amber">seen</Pill> : <Pill color="green">fresh</Pill>}
                    </div>
                    <div style={{ display: "flex", gap: 8 }}>
                      <SecondaryButton onClick={() => toggleAnchor(item.practiceItemId)} active={isAnchor}>
                        {isAnchor ? "✓ anchor" : "anchor"}
                      </SecondaryButton>
                      <SecondaryButton onClick={() => chooseHeldOut(item.practiceItemId)} active={isHeldOut}>
                        {isHeldOut ? "✓ held out" : "hold out"}
                      </SecondaryButton>
                    </div>
                  </Card>
                );
              })}
            </div>
            <div>
              <PrimaryButton onClick={() => void compose()} disabled={busy || anchors.size === 0 || !heldOut}>
                compose draft blueprint →
              </PrimaryButton>
            </div>
          </>
        ) : null}

        {composed ? (
          <>
            <SectionHeader>4 · Owner review</SectionHeader>
            {composed.warnings.map((w, i) => (
              <Faint key={i} style={{ fontSize: 11, color: COLOR.amber }}>⚠ {w}</Faint>
            ))}
            <Card style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <Meta>{composed.blueprint.blueprintVersionId}</Meta>
                <Pill color={reviewed ? "green" : "amber"}>{reviewed ? "reviewed" : composed.blueprint.status}</Pill>
              </div>
              {REVIEW_CHECKS.map((c) => (
                <label key={c.key} style={{ display: "flex", gap: 8, alignItems: "flex-start", fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={checks.has(c.key)}
                    disabled={reviewed}
                    onChange={() =>
                      setChecks((prev) => {
                        const next = new Set(prev);
                        if (next.has(c.key)) next.delete(c.key);
                        else next.add(c.key);
                        return next;
                      })
                    }
                    style={{ marginTop: 2 }}
                  />
                  <span>{c.label}</span>
                </label>
              ))}
              {!reviewed ? (
                <div>
                  <PrimaryButton onClick={() => void review()} disabled={busy || checks.size < REVIEW_CHECKS.length}>
                    mark reviewed
                  </PrimaryButton>
                </div>
              ) : null}
            </Card>

            <SectionHeader>5 · Confirm &amp; start</SectionHeader>
            {!goalId ? (
              <Faint style={{ fontSize: 12 }}>select a goal above to enable confirmation.</Faint>
            ) : !reviewed ? (
              <Faint style={{ fontSize: 12 }}>complete the owner review to enable confirmation.</Faint>
            ) : (
              <div>
                <PrimaryButton onClick={() => setConfirmOpen(true)}>review confirmation ↵</PrimaryButton>
              </div>
            )}
          </>
        ) : null}
      </div>

      <KeyBar keys={[{ key: "pick", label: "anchors + held-out" }, { key: "↵", label: "confirm" }]} />

      {confirmOpen && composed ? (
        <ExemplarConfirmDialog
          blueprintVersionId={composed.blueprint.blueprintVersionId}
          confirmInput={confirmInput}
          onConfirmed={(runId) => {
            setConfirmOpen(false);
            onRunStarted(runId);
          }}
          onClose={() => setConfirmOpen(false)}
          onError={onError}
        />
      ) : null}
    </div>
  );
}
