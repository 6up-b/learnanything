// FacetInspector (§3.4 / §9.6): a facet-contract drawer opened from the facet
// surfaces (radar / gravity well / knowledge field). It shows the semantic
// contract, the padlock chip with verbatim lock reasons, blueprint-recipe
// membership (each LO linkable via the existing onInspect plumbing), the
// dual-axis evidence readout (Ready = predicted now vs Ready-ghost =
// before-evidence prior) with a capability ledger, and cross-links.
//
// Two restructure gestures live inside it:
//  · "merge into…" — autocomplete over api.listFacets, side-by-side contract
//    comparison, survivor pick, rationale → api.proposeFacetMerge (a REVIEW
//    item, never an auto-merge). If EITHER facet is locked the gesture instead
//    surfaces the lock reasons and offers a durable restructure request.
//  · "propose split…" — only routes through queueRestructureRequest when the
//    facet is locked; unlocked splits are authored via the registry review
//    flow (there is no split endpoint yet — we say so rather than fake one).

import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type {
  FacetDetailDto,
  FacetSummaryDto,
  RestructureRequestDto,
} from "../api/dto";
import { EntityLink } from "./ui";
import { COLOR, Faint, FONT_MONO, Meta, Pill, SectionHeader, TermSelect } from "./term";
import { FacetEvidenceReceipt } from "./KnowledgeModel";

const LOCK_GLYPH = "\u{1F512}"; // 🔒

export function FacetInspector({
  facetId,
  onClose,
  onInspect,
  onError,
}: {
  facetId: string;
  onClose: () => void;
  onInspect: (id: string) => void;
  onError?: (message: string) => void;
}) {
  const [detail, setDetail] = useState<FacetDetailDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    setDetail(null);
    api
      .getFacetDetail(facetId)
      .then((data) => {
        if (!cancelled) {
          setDetail(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : String(err);
        setLoadError(message);
        setLoading(false);
        onError?.(message);
      });
    return () => {
      cancelled = true;
    };
  }, [facetId, onError]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 60,
        display: "flex",
        justifyContent: "flex-end",
        background: "rgba(6,6,6,0.55)",
        backdropFilter: "blur(2px)",
      }}
      onClick={onClose}
    >
      <div
        className="ll-scroll"
        onClick={(event) => event.stopPropagation()}
        style={{
          width: 480,
          maxWidth: "100%",
          height: "100%",
          overflowY: "auto",
          background: COLOR.bg,
          borderLeft: `1px solid ${COLOR.borderStrong}`,
          boxShadow: "-8px 0 24px rgba(0,0,0,0.4)",
          padding: "16px 20px 40px",
          fontFamily: FONT_MONO,
          fontSize: 13,
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 11, color: COLOR.textFaint }}>evidence facet</div>
            <div style={{ fontSize: 15, fontWeight: 600, color: COLOR.text, overflowWrap: "anywhere" }}>
              {detail?.facet.title ?? facetId}
            </div>
            <Meta style={{ fontSize: 11 }}>{facetId}</Meta>
          </div>
          <button type="button" onClick={onClose} style={{ ...btnStyle, flexShrink: 0 }}>
            esc ✕
          </button>
        </div>

        {loading ? <Faint style={{ display: "block", marginTop: 18 }}>loading facet contract…</Faint> : null}
        {loadError ? <div style={{ color: COLOR.red, fontSize: 12, marginTop: 18 }}>{loadError}</div> : null}

        {detail ? <FacetBody facetId={facetId} detail={detail} onInspect={onInspect} /> : null}
      </div>
    </div>
  );
}

function FacetBody({
  facetId,
  detail,
  onInspect,
}: {
  facetId: string;
  detail: FacetDetailDto;
  onInspect: (id: string) => void;
}) {
  const { facet, lock, membership, evidence, sharedWith } = detail;
  const locked = lock.locked;

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
        {facet.kind ? <Pill color="slate">{facet.kind}</Pill> : null}
        <Pill color={facet.status === "reviewed" ? "green" : facet.status === "proposed" ? "amber" : "slate"}>
          {facet.status}
        </Pill>
        {locked ? <Pill color="red">{LOCK_GLYPH} locked</Pill> : <Pill color="green">pre-lock</Pill>}
      </div>

      {/* (b) lock chip — verbatim reasons */}
      <LockSection lock={lock} />

      {/* (a) semantic contract */}
      <SectionHeader>Semantic contract</SectionHeader>
      {facet.claim ? (
        <div style={{ fontSize: 13, color: COLOR.text, lineHeight: 1.6, marginBottom: 4 }}>{facet.claim}</div>
      ) : (
        <Faint>no claim recorded</Faint>
      )}
      <ListBlock label="preconditions" items={facet.preconditions} />
      <ListBlock label="examples (+)" items={facet.positiveExamples} />
      <ListBlock label="examples (−)" items={facet.negativeExamples} />
      <ListBlock label="non-goals" items={facet.nonGoals} />
      <ListBlock label="error signatures" items={facet.errorSignatures} />
      <ListBlock label="aliases" items={facet.aliases} />

      {/* (c) membership */}
      <SectionHeader>Membership</SectionHeader>
      {membership.length === 0 ? (
        <Faint>no blueprint-recipe component references this facet yet</Faint>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {membership.map((row, i) => (
            <div
              key={`${row.learningObjectId}-${row.recipeId}-${row.capability}-${i}`}
              style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 6, fontSize: 12 }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                <span style={{ color: COLOR.text, overflowWrap: "anywhere" }}>{row.loTitle}</span>
                <Pill color={row.role === "integration" ? "purple" : row.role === "any_of" ? "cyan" : "amber"}>
                  {row.role}
                </Pill>
              </div>
              <div style={{ marginTop: 2 }}>
                <EntityLink id={row.learningObjectId} onInspect={onInspect}>
                  <Meta>{row.learningObjectId}</Meta>
                </EntityLink>
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 2, color: COLOR.textDim }}>
                <span>cap <span style={{ color: COLOR.text }}>{row.capability}</span></span>
                <span>· {row.modality}</span>
                <Faint>{row.blueprintId} / {row.recipeId}</Faint>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* (d) evidence — dual axis */}
      <SectionHeader>Evidence</SectionHeader>
      <div style={{ display: "flex", gap: 18, flexWrap: "wrap", fontSize: 12 }}>
        <StatCell label="Ready (predicted now)" value={fmt(evidence.ready)} tone={COLOR.amber} />
        <StatCell label="Ready-ghost (before evidence)" value={fmt(evidence.readyGhost)} tone={COLOR.textFaint} />
        <StatCell label="evidence mass" value={evidence.evidenceMass.toFixed(2)} tone={COLOR.text} />
      </div>
      {evidence.capabilityLedger.length > 0 ? (
        <div style={{ marginTop: 12 }}>
          <div style={{ ...ledgerRowStyle, color: COLOR.textFaint, borderTop: "none" }}>
            <span>capability</span>
            <span style={{ textAlign: "right" }}>+mass</span>
            <span style={{ textAlign: "right" }}>−mass</span>
            <span style={{ textAlign: "right" }}>cert</span>
            <span style={{ textAlign: "center" }}>demo</span>
          </div>
          {evidence.capabilityLedger.map((row) => (
            <div key={row.capability} style={ledgerRowStyle}>
              <span style={{ color: COLOR.text, overflowWrap: "anywhere" }}>{row.capability}</span>
              <span style={{ textAlign: "right", color: COLOR.green }}>{row.directPositiveMass.toFixed(2)}</span>
              <span style={{ textAlign: "right", color: COLOR.red }}>{row.directNegativeMass.toFixed(2)}</span>
              <span style={{ textAlign: "right", color: COLOR.textDim }}>{row.certificationCredit.toFixed(2)}</span>
              <span style={{ textAlign: "center", color: row.demonstrated ? COLOR.green : COLOR.textFaint }}>
                {row.demonstrated ? "✓" : "·"}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <Faint style={{ display: "block", marginTop: 6 }}>no capability evidence yet</Faint>
      )}
      <div style={{ marginTop: 12, borderTop: `1px solid ${COLOR.border}`, paddingTop: 10 }}>
        <FacetEvidenceReceipt facetId={facetId} onInspect={onInspect} />
      </div>

      {/* (e) shared with */}
      {sharedWith.length > 0 ? (
        <>
          <SectionHeader>Also counts toward</SectionHeader>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {sharedWith.map((loId) => (
              <EntityLink key={loId} id={loId} onInspect={onInspect}>
                <Meta>{loId}</Meta>
              </EntityLink>
            ))}
          </div>
        </>
      ) : null}

      {/* restructure gestures */}
      <RestructureActions facetId={facetId} facetTitle={facet.title} locked={locked} lock={lock} selfDetail={detail} />
    </div>
  );
}

function LockSection({ lock }: { lock: FacetDetailDto["lock"] }) {
  if (!lock.locked) {
    return (
      <div style={{ marginTop: 10, border: `1px solid ${COLOR.border}`, borderLeft: `3px solid ${COLOR.greenSoft}`, padding: "8px 12px" }}>
        <Faint style={{ fontSize: 11, lineHeight: 1.6 }}>
          Pre-lock: no attempt/certification history pins this facet's identity yet, so it can still be merged or split
          cheaply. Once evidence accrues the identity locks and restructuring must go through a restructure request.
        </Faint>
      </div>
    );
  }
  return (
    <div style={{ marginTop: 10, border: `1px solid ${COLOR.border}`, borderLeft: `3px solid ${COLOR.red}`, padding: "8px 12px" }}>
      <div style={{ fontSize: 12, color: COLOR.red, marginBottom: 4 }}>{LOCK_GLYPH} identity locked — history is load-bearing</div>
      {lock.reasons.length === 0 ? (
        <Faint style={{ fontSize: 11 }}>locked (no reason detail recorded)</Faint>
      ) : (
        lock.reasons.map((reason, i) => (
          <div key={i} style={{ fontSize: 11, color: COLOR.textDim, lineHeight: 1.6 }}>
            <span style={{ color: COLOR.amber }}>{reason.source}</span> · {reason.detail}
          </div>
        ))
      )}
    </div>
  );
}

// ── restructure: merge + split ───────────────────────────────────────────────

function RestructureActions({
  facetId,
  facetTitle,
  locked,
  lock,
  selfDetail,
}: {
  facetId: string;
  facetTitle: string;
  locked: boolean;
  lock: FacetDetailDto["lock"];
  selfDetail: FacetDetailDto;
}) {
  const [mode, setMode] = useState<"none" | "merge" | "split">("none");

  return (
    <>
      <SectionHeader>Restructure</SectionHeader>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button type="button" style={btnStyle} onClick={() => setMode((m) => (m === "merge" ? "none" : "merge"))}>
          merge into…
        </button>
        <button type="button" style={btnStyle} onClick={() => setMode((m) => (m === "split" ? "none" : "split"))}>
          propose split…
        </button>
      </div>

      {mode === "merge" ? (
        <MergeFlow facetId={facetId} facetTitle={facetTitle} selfLocked={locked} selfLock={lock} selfDetail={selfDetail} />
      ) : null}
      {mode === "split" ? <SplitFlow facetId={facetId} locked={locked} lock={lock} /> : null}
    </>
  );
}

function MergeFlow({
  facetId,
  facetTitle,
  selfLocked,
  selfLock,
  selfDetail,
}: {
  facetId: string;
  facetTitle: string;
  selfLocked: boolean;
  selfLock: FacetDetailDto["lock"];
  selfDetail: FacetDetailDto;
}) {
  const [other, setOther] = useState<FacetSummaryDto | null>(null);
  const [otherDetail, setOtherDetail] = useState<FacetDetailDto | null>(null);
  const [otherLoading, setOtherLoading] = useState(false);
  const [survivor, setSurvivor] = useState<"self" | "other">("other");
  const [rationale, setRationale] = useState("");
  const [subjects, setSubjects] = useState<string[] | null>(null);
  const [subjectId, setSubjectId] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mergeDone, setMergeDone] = useState<{ proposalId: string } | null>(null);
  const [restructureDone, setRestructureDone] = useState<RestructureRequestDto | null>(null);

  // Subjects are needed for propose_facet_merge (subject-scoped). The facet
  // surfaces don't pass a subject down, so we source it from the loaded vault:
  // one subject → auto; several → a selector.
  useEffect(() => {
    let cancelled = false;
    api
      .loadVault()
      .then((snap) => {
        if (cancelled) return;
        const subs = snap.vault?.subjects ?? [];
        setSubjects(subs);
        setSubjectId((current) => current || subs[0] || "");
      })
      .catch(() => {
        if (!cancelled) setSubjects([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const pickOther = (summary: FacetSummaryDto) => {
    setOther(summary);
    setOtherDetail(null);
    setMergeDone(null);
    setRestructureDone(null);
    setError(null);
    setOtherLoading(true);
    api
      .getFacetDetail(summary.id)
      .then((data) => {
        setOtherDetail(data);
        setOtherLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : String(err));
        setOtherLoading(false);
      });
  };

  const eitherLocked = selfLocked || other?.locked === true || otherDetail?.lock.locked === true;

  const submitMerge = async () => {
    if (!other || !subjectId) return;
    const retiredFacetId = survivor === "self" ? other.id : facetId;
    const survivingFacetId = survivor === "self" ? facetId : other.id;
    setBusy(true);
    setError(null);
    try {
      const res = await api.proposeFacetMerge({
        subjectId,
        retiredFacetId,
        survivingFacetId,
        rationale: rationale.trim() || null,
      });
      setMergeDone({ proposalId: res.proposalId });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const submitRestructure = async () => {
    setBusy(true);
    setError(null);
    try {
      const facetIds = other ? [facetId, other.id] : [facetId];
      const res = await api.queueRestructureRequest({
        facetIds,
        requestedOperation: "merge",
        rationale: rationale.trim(),
      });
      setRestructureDone(res.request);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={panelStyle}>
      <div style={{ fontSize: 11, color: COLOR.textFaint, marginBottom: 8 }}>
        merge <span style={{ color: COLOR.text }}>{facetTitle || facetId}</span> with another facet
      </div>

      <FacetAutocomplete excludeId={facetId} selected={other} onPick={pickOther} />

      {otherLoading ? <Faint style={{ display: "block", marginTop: 8 }}>loading other contract…</Faint> : null}

      {other && (selfLocked || otherDetail) ? (
        eitherLocked ? (
          // Locked path — no cheap merge; queue a durable restructure request.
          <div style={{ marginTop: 12 }}>
            <div style={{ border: `1px solid ${COLOR.border}`, borderLeft: `3px solid ${COLOR.red}`, padding: "8px 12px" }}>
              <div style={{ fontSize: 12, color: COLOR.red, marginBottom: 4 }}>
                {LOCK_GLYPH} one or both facets are locked — merge can't be applied directly
              </div>
              <LockReasonList label={facetTitle || facetId} lock={selfLock} />
              {otherDetail ? <LockReasonList label={other.title || other.id} lock={otherDetail.lock} /> : null}
            </div>
            <textarea
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              placeholder="rationale (required) — why these should be one facet"
              style={textareaStyle}
            />
            {restructureDone ? (
              <div style={{ color: COLOR.green, fontSize: 12, marginTop: 6 }}>
                Restructure request queued → <Meta>{restructureDone.needId}</Meta> (surfaces in the maintenance feed).
              </div>
            ) : (
              <button
                type="button"
                style={{ ...btnStyle, marginTop: 8, opacity: rationale.trim() && !busy ? 1 : 0.4 }}
                disabled={!rationale.trim() || busy}
                onClick={() => void submitRestructure()}
              >
                queue restructure request
              </button>
            )}
          </div>
        ) : (
          // Unlocked path — side-by-side comparison → survivor → rationale → review item.
          <div style={{ marginTop: 12 }}>
            <ContractCompare
              left={{ id: facetId, title: facetTitle, detail: selfDetail }}
              rightDetail={otherDetail}
              rightId={other.id}
              rightTitle={other.title}
            />

            <div style={{ marginTop: 10, fontSize: 12 }}>
              <div style={{ color: COLOR.textFaint, marginBottom: 4 }}>which id survives?</div>
              <label style={radioLabel}>
                <input type="radio" checked={survivor === "self"} onChange={() => setSurvivor("self")} />
                <span style={{ color: COLOR.text }}>{facetId}</span> <Faint>(this facet)</Faint>
              </label>
              <label style={radioLabel}>
                <input type="radio" checked={survivor === "other"} onChange={() => setSurvivor("other")} />
                <span style={{ color: COLOR.text }}>{other.id}</span>
              </label>
            </div>

            {subjects && subjects.length > 1 ? (
              <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
                <Faint>subject</Faint>
                <TermSelect ariaLabel="Subject" value={subjectId} options={subjects} onChange={setSubjectId} width={220} />
              </div>
            ) : null}

            <textarea
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              placeholder="rationale (required)"
              style={textareaStyle}
            />

            {mergeDone ? (
              <div style={{ color: COLOR.green, fontSize: 12, marginTop: 6 }}>
                Merge review item filed → <Meta>{mergeDone.proposalId}</Meta>. Approve it in the Proposals screen.
              </div>
            ) : (
              <button
                type="button"
                style={{ ...btnStyle, marginTop: 8, opacity: rationale.trim() && subjectId && !busy ? 1 : 0.4 }}
                disabled={!rationale.trim() || !subjectId || busy}
                onClick={() => void submitMerge()}
              >
                file merge review item
              </button>
            )}
          </div>
        )
      ) : null}

      {error ? <div style={{ color: COLOR.red, fontSize: 12, marginTop: 8 }}>{error}</div> : null}
    </div>
  );
}

function SplitFlow({
  facetId,
  locked,
  lock,
}: {
  facetId: string;
  locked: boolean;
  lock: FacetDetailDto["lock"];
}) {
  const [rationale, setRationale] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<RestructureRequestDto | null>(null);

  if (!locked) {
    return (
      <div style={panelStyle}>
        <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
          This facet is pre-lock and there is no dedicated split endpoint yet. Splitting an unlocked facet is authored
          through the registry review flow (author the two successor facet contracts, then retire this one via a merge
          review). A restructure request is only queued for locked facets, where history blocks direct edits.
        </Faint>
      </div>
    );
  }

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.queueRestructureRequest({
        facetIds: [facetId],
        requestedOperation: "split",
        rationale: rationale.trim(),
      });
      setDone(res.request);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={panelStyle}>
      <div style={{ border: `1px solid ${COLOR.border}`, borderLeft: `3px solid ${COLOR.red}`, padding: "8px 12px" }}>
        <div style={{ fontSize: 12, color: COLOR.red, marginBottom: 4 }}>{LOCK_GLYPH} locked — split needs a restructure request</div>
        <LockReasonList label={facetId} lock={lock} />
      </div>
      <textarea
        value={rationale}
        onChange={(e) => setRationale(e.target.value)}
        placeholder="rationale (required) — what distinction this facet is conflating"
        style={textareaStyle}
      />
      {done ? (
        <div style={{ color: COLOR.green, fontSize: 12, marginTop: 6 }}>
          Restructure request queued → <Meta>{done.needId}</Meta> (surfaces in the maintenance feed).
        </div>
      ) : (
        <button
          type="button"
          style={{ ...btnStyle, marginTop: 8, opacity: rationale.trim() && !busy ? 1 : 0.4 }}
          disabled={!rationale.trim() || busy}
          onClick={() => void submit()}
        >
          queue restructure request
        </button>
      )}
      {error ? <div style={{ color: COLOR.red, fontSize: 12, marginTop: 8 }}>{error}</div> : null}
    </div>
  );
}

function LockReasonList({ label, lock }: { label: string; lock: FacetDetailDto["lock"] }) {
  if (!lock.locked) return null;
  return (
    <div style={{ marginTop: 4 }}>
      <Faint style={{ fontSize: 11 }}>{label}:</Faint>
      {lock.reasons.length === 0 ? (
        <Faint style={{ fontSize: 11, display: "block" }}> locked (no detail)</Faint>
      ) : (
        lock.reasons.map((reason, i) => (
          <div key={i} style={{ fontSize: 11, color: COLOR.textDim, lineHeight: 1.6 }}>
            <span style={{ color: COLOR.amber }}>{reason.source}</span> · {reason.detail}
          </div>
        ))
      )}
    </div>
  );
}

function ContractCompare({
  left,
  rightDetail,
  rightId,
  rightTitle,
}: {
  left: { id: string; title: string; detail: FacetDetailDto | null };
  rightDetail: FacetDetailDto | null;
  rightId: string;
  rightTitle: string;
}) {
  const rows: Array<{ label: string; left: string[]; right: string[] }> = useMemo(() => {
    const l = left.detail?.facet;
    const r = rightDetail?.facet;
    return [
      { label: "claim", left: l?.claim ? [l.claim] : [], right: r?.claim ? [r.claim] : [] },
      { label: "examples (+)", left: l?.positiveExamples ?? [], right: r?.positiveExamples ?? [] },
      { label: "examples (−)", left: l?.negativeExamples ?? [], right: r?.negativeExamples ?? [] },
      { label: "error signatures", left: l?.errorSignatures ?? [], right: r?.errorSignatures ?? [] },
    ];
  }, [left.detail, rightDetail]);

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, fontSize: 11, marginBottom: 6 }}>
        <div style={{ color: COLOR.amber, overflowWrap: "anywhere" }}>{left.title || left.id}</div>
        <div style={{ color: COLOR.cyan, overflowWrap: "anywhere" }}>{rightTitle || rightId}</div>
      </div>
      {rows.map((row) => (
        <div key={row.label} style={{ marginTop: 6 }}>
          <div style={{ fontSize: 10, color: COLOR.textFaint, textTransform: "uppercase", letterSpacing: "0.1em" }}>
            {row.label}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <CompareCol items={row.left} />
            <CompareCol items={row.right} />
          </div>
        </div>
      ))}
    </div>
  );
}

function CompareCol({ items }: { items: string[] }) {
  if (items.length === 0) return <Faint style={{ fontSize: 11 }}>—</Faint>;
  return (
    <div>
      {items.map((item, i) => (
        <div key={i} style={{ fontSize: 11, color: COLOR.textDim, lineHeight: 1.55 }}>
          · {item}
        </div>
      ))}
    </div>
  );
}

function FacetAutocomplete({
  excludeId,
  selected,
  onPick,
}: {
  excludeId: string;
  selected: FacetSummaryDto | null;
  onPick: (facet: FacetSummaryDto) => void;
}) {
  const [all, setAll] = useState<FacetSummaryDto[] | null>(null);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .listFacets()
      .then((data) => {
        if (!cancelled) setAll(data.facets.filter((f) => f.id !== excludeId));
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [excludeId]);

  const matches = useMemo(() => {
    if (!all) return [];
    const q = query.trim().toLowerCase();
    const pool = q
      ? all.filter((f) => f.id.toLowerCase().includes(q) || f.title.toLowerCase().includes(q))
      : all;
    return pool.slice(0, 12);
  }, [all, query]);

  return (
    <div style={{ position: "relative" }}>
      <input
        value={selected ? `${selected.title || selected.id}` : query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder={all ? "search facets…" : "loading facets…"}
        style={inputStyle}
      />
      {error ? <div style={{ color: COLOR.red, fontSize: 11, marginTop: 4 }}>{error}</div> : null}
      {open && matches.length > 0 ? (
        <div
          className="ll-scroll"
          style={{
            position: "absolute",
            zIndex: 5,
            left: 0,
            right: 0,
            maxHeight: 220,
            overflowY: "auto",
            background: COLOR.bgElev,
            border: `1px solid ${COLOR.borderStrong}`,
          }}
        >
          {matches.map((f) => (
            <div
              key={f.id}
              onClick={() => {
                onPick(f);
                setQuery("");
                setOpen(false);
              }}
              style={{ padding: "5px 10px", cursor: "pointer", fontSize: 12, borderBottom: `1px solid ${COLOR.border}` }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#241d12")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                <span style={{ color: COLOR.text, overflowWrap: "anywhere" }}>{f.title || f.id}</span>
                {f.locked ? <Pill color="red">{LOCK_GLYPH}</Pill> : null}
              </div>
              <Meta style={{ fontSize: 10 }}>{f.id}</Meta>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function StatCell({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div>
      <div style={{ fontSize: 10, color: COLOR.textFaint }}>{label}</div>
      <div style={{ fontSize: 15, color: tone, fontFamily: FONT_MONO }}>{value}</div>
    </div>
  );
}

function ListBlock({ label, items }: { label: string; items: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ fontSize: 10, color: COLOR.amber, textTransform: "uppercase", letterSpacing: "0.12em" }}>{label}</div>
      {items.map((item, i) => (
        <div key={i} style={{ fontSize: 12, color: COLOR.textDim, lineHeight: 1.6, overflowWrap: "anywhere" }}>
          · {item}
        </div>
      ))}
    </div>
  );
}

const fmt = (value: number | null) => (value == null ? "—" : value.toFixed(2));

const btnStyle: CSSProperties = {
  padding: "4px 12px",
  border: `1px solid ${COLOR.borderStrong}`,
  background: "transparent",
  color: COLOR.textDim,
  fontFamily: FONT_MONO,
  fontSize: 12,
  cursor: "pointer",
};

const panelStyle: CSSProperties = {
  marginTop: 10,
  border: `1px solid ${COLOR.border}`,
  background: COLOR.bgElev,
  padding: "12px 14px",
};

const inputStyle: CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  background: COLOR.bgInput,
  color: COLOR.text,
  border: `1px solid ${COLOR.border}`,
  padding: "6px 8px",
  fontSize: 12,
  fontFamily: FONT_MONO,
  outline: "none",
};

const textareaStyle: CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  minHeight: 52,
  marginTop: 8,
  background: COLOR.bgInput,
  color: COLOR.text,
  border: `1px solid ${COLOR.border}`,
  padding: "6px 8px",
  fontSize: 12,
  fontFamily: FONT_MONO,
  outline: "none",
  resize: "vertical",
};

const radioLabel: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 6,
  padding: "3px 0",
  cursor: "pointer",
};

const ledgerRowStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 52px 52px 46px 40px",
  gap: 6,
  alignItems: "center",
  padding: "4px 0",
  borderTop: `1px solid ${COLOR.border}`,
  fontSize: 11,
};
