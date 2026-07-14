// Track record — two views, not one (spec §4.12). One tap from the forecast hero.
// Exam/answer calibration and forecast performance are DIFFERENT things and get two
// separate sections, never merged. Minimum-N honesty everywhere: a confident curve
// through a handful of samples is exactly the dishonesty this surface exists to prevent,
// so below the minimum we show plain language only. Badly calibrated is rendered as
// plainly as well calibrated. Keyboard-reachable; never color-only.

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AnswerCalibrationReportDto, CalibrationBinDto, ForecastTrackRecordDto } from "../api/dto";
import { COLOR, FONT_MONO } from "./term";

const pct = (v: number | null | undefined): string => (v == null ? "—" : `${Math.round(v * 100)}%`);
const num3 = (v: number | null | undefined): string => (v == null ? "—" : v.toFixed(3));

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: 10, color: COLOR.textFaint, letterSpacing: "0.16em", textTransform: "uppercase", fontFamily: FONT_MONO, marginBottom: 8 }}>
      {children}
    </div>
  );
}

// Reliability curve: predicted vs observed per bin. Sparse bins (below the minimum
// per-bin count) are grayed and excluded from the read. Text-labeled, not color-only.
function ReliabilityCurve({ bins, size = 150 }: { bins: CalibrationBinDto[]; size?: number }) {
  const pad = 18;
  const plot = size - pad * 2;
  const xy = (frac: number) => pad + Math.max(0, Math.min(1, frac)) * plot;
  const yOf = (frac: number) => size - pad - Math.max(0, Math.min(1, frac)) * plot;
  const minBinN = 3;
  const solid = bins.filter((b) => b.count >= minBinN && b.meanPredicted != null && b.meanObserved != null);
  return (
    <svg width={size} height={size} style={{ display: "block", overflow: "visible" }} role="img" aria-label="reliability curve: predicted probability against observed frequency">
      {/* perfect-calibration diagonal */}
      <line x1={xy(0)} y1={yOf(0)} x2={xy(1)} y2={yOf(1)} stroke={COLOR.borderStrong} strokeWidth={1} strokeDasharray="2 3" />
      <line x1={pad} y1={size - pad} x2={size - pad} y2={size - pad} stroke={COLOR.border} strokeWidth={1} />
      <line x1={pad} y1={pad} x2={pad} y2={size - pad} stroke={COLOR.border} strokeWidth={1} />
      <text x={xy(0)} y={size - 4} fill={COLOR.textFaint} fontFamily={FONT_MONO} fontSize={8}>0</text>
      <text x={size - pad - 4} y={size - 4} fill={COLOR.textFaint} fontFamily={FONT_MONO} fontSize={8}>predicted</text>
      {/* dots: grayed when sparse, amber when counted */}
      {bins.map((b, i) => {
        if (b.meanPredicted == null || b.meanObserved == null) return null;
        const sparse = b.count < minBinN;
        return (
          <circle
            key={i}
            cx={xy(b.meanPredicted)}
            cy={yOf(b.meanObserved)}
            r={sparse ? 2 : 3}
            fill={sparse ? COLOR.borderStrong : COLOR.amber}
            opacity={sparse ? 0.6 : 1}
          >
            <title>
              {`${pct(b.lower)}–${pct(b.upper)}: predicted ${pct(b.meanPredicted)}, observed ${pct(b.meanObserved)} (n=${b.count}${sparse ? ", too sparse — excluded" : ""})`}
            </title>
          </circle>
        );
      })}
      {/* connect the counted bins */}
      {solid.length >= 2 ? (
        <path
          d={solid.map((b, i) => `${i === 0 ? "M" : "L"} ${xy(b.meanPredicted as number).toFixed(1)} ${yOf(b.meanObserved as number).toFixed(1)}`).join(" ")}
          fill="none"
          stroke={COLOR.amber}
          strokeWidth={1.25}
        />
      ) : null}
    </svg>
  );
}

function AnswerCalibrationSection({ report }: { report: AnswerCalibrationReportDto }) {
  const { items, duel } = report;
  return (
    <div>
      <SectionHeader>1 · answer calibration</SectionHeader>
      <div style={{ fontSize: 13, color: COLOR.text, fontFamily: FONT_MONO }}>
        pooled Brier {num3(items.brier)} · {items.n} {items.n === 1 ? "prediction" : "predictions"}
      </div>
      {!items.curveAvailable ? (
        <div style={{ marginTop: 6, fontSize: 12, color: COLOR.textDim }}>
          {items.n} {items.n === 1 ? "prediction" : "predictions"} so far — too few for a reliability curve (need {items.minimumN}).
        </div>
      ) : (
        <div style={{ marginTop: 8 }}>
          <ReliabilityCurve bins={items.bins} />
          <div style={{ fontSize: 10, color: COLOR.textFaint, fontFamily: FONT_MONO, marginTop: 2 }}>
            on the dashed diagonal = perfectly calibrated · gray dots too sparse to count
          </div>
        </div>
      )}

      {/* the calibration duel: learner vs model on matched attempts */}
      <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${COLOR.border}` }}>
        <div style={{ fontSize: 11, color: COLOR.textFaint, fontFamily: FONT_MONO, letterSpacing: "0.1em", marginBottom: 4 }}>
          calibration duel — matched attempts
        </div>
        {duel.n === 0 || duel.learnerBrier == null || duel.modelBrier == null ? (
          <div style={{ fontSize: 12, color: COLOR.textDim }}>no matched attempts yet — nothing to compare.</div>
        ) : (
          <div style={{ fontSize: 13, color: COLOR.text, fontFamily: FONT_MONO }}>
            you {num3(duel.learnerBrier)} · model {num3(duel.modelBrier)}{" "}
            <span style={{ color: COLOR.textDim }}>
              (n={duel.n}, {duel.learnerBrier < duel.modelBrier ? "you are better calibrated" : duel.learnerBrier > duel.modelBrier ? "the model is better calibrated" : "tied"}; lower is better)
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function ForecastTrackRecordSection({ record }: { record: ForecastTrackRecordDto }) {
  const kinds = Object.entries(record.trackRecord.byKind);
  return (
    <div>
      <SectionHeader>2 · forecast track record</SectionHeader>
      {kinds.length === 0 ? (
        <div style={{ fontSize: 12, color: COLOR.textDim }}>no forecasts issued yet.</div>
      ) : (
        <table style={{ borderCollapse: "collapse", fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
          <thead>
            <tr style={{ color: COLOR.textFaint }}>
              <th style={thStyle}>kind</th>
              <th style={thStyleR}>issued</th>
              <th style={thStyleR}>resolved</th>
              <th style={thStyleR}>censored</th>
              <th style={thStyleR}>unobs.</th>
              <th style={thStyleR}>err (resolved)</th>
            </tr>
          </thead>
          <tbody>
            {kinds.map(([kind, r]) => (
              <tr key={kind}>
                <td style={tdStyle}>{kind.replace(/_/g, " ")}</td>
                <td style={tdStyleR}>{r.issued}</td>
                <td style={tdStyleR}>{r.resolved}</td>
                <td style={tdStyleR}>{r.censored}</td>
                <td style={tdStyleR}>{r.unobservable}</td>
                <td style={tdStyleR}>{r.resolved > 0 && r.meanAbsoluteError != null ? num3(r.meanAbsoluteError) : <span style={{ color: COLOR.textFaint }}>—</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div style={{ fontSize: 10, color: COLOR.textFaint, fontFamily: FONT_MONO, marginTop: 6, lineHeight: 1.5 }}>
        mean absolute error is on the resolved subset only; censored/unobservable forecasts carry no accuracy.
      </div>
    </div>
  );
}

const thStyle: React.CSSProperties = { textAlign: "left", padding: "2px 10px 4px 0", fontWeight: 400, letterSpacing: "0.06em" };
const thStyleR: React.CSSProperties = { ...thStyle, textAlign: "right", padding: "2px 0 4px 12px" };
const tdStyle: React.CSSProperties = { textAlign: "left", padding: "2px 10px 2px 0" };
const tdStyleR: React.CSSProperties = { textAlign: "right", padding: "2px 0 2px 12px" };

export function TrackRecordView({
  goalId,
  onClose,
  onError
}: {
  goalId?: string | null;
  onClose: () => void;
  onError: (message: string) => void;
}) {
  const [calibration, setCalibration] = useState<AnswerCalibrationReportDto | null>(null);
  const [forecast, setForecast] = useState<ForecastTrackRecordDto | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([api.getAnswerCalibration(), api.getForecastTrackRecord(goalId ?? null)])
      .then(([cal, fc]) => {
        if (cancelled) return;
        setCalibration(cal);
        setForecast(fc);
      })
      .catch((e) => {
        if (!cancelled) onError((e as Error).message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [goalId, onError]);

  return (
    <div
      role="region"
      aria-label="track record"
      style={{
        marginTop: 12,
        border: `1px solid ${COLOR.borderStrong}`,
        background: COLOR.bg,
        padding: "14px 16px"
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
        <span style={{ fontSize: 11, color: COLOR.text, fontFamily: FONT_MONO, letterSpacing: "0.14em", textTransform: "uppercase" }}>
          track record
        </span>
        <span style={{ flex: 1 }} />
        <button
          type="button"
          onClick={onClose}
          style={{ padding: "2px 10px", border: `1px solid ${COLOR.border}`, background: "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 12, cursor: "pointer" }}
        >
          close ✕
        </button>
      </div>

      {loading ? (
        <div style={{ fontSize: 12, color: COLOR.textFaint, fontFamily: FONT_MONO }}>loading track record…</div>
      ) : (
        <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
          <div style={{ flex: "1 1 260px", minWidth: 240 }}>
            {calibration ? <AnswerCalibrationSection report={calibration} /> : <span style={{ color: COLOR.textFaint, fontSize: 12 }}>no calibration data</span>}
          </div>
          <div style={{ flex: "1 1 320px", minWidth: 300 }}>
            {forecast ? <ForecastTrackRecordSection record={forecast} /> : <span style={{ color: COLOR.textFaint, fontSize: 12 }}>no forecast data</span>}
          </div>
        </div>
      )}
    </div>
  );
}
