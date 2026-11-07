// Mobile v2 J2: the full answer on the phone's feedback is a reveal, recorded before it shows, as
// on the desktop (UX Phase 4, Codex review F1 round 3). The gate is the desktop's own
// (`screens/feedback/answerExposureGate.ts`, pure); this is the phone's lifecycle around it: the
// page hidden, `pagehide`, `freeze` and `blur` hide the answer at once, and it shows again only after
// a fresh row is acknowledged. A tick renews the row while the learner is here.
import { useCallback, useEffect, useRef, useState } from "react";
import { AnswerExposureGate, EXPOSURE, type ExposureStatus } from "@desktop/screens/feedback/answerExposureGate";
import { phone } from "../api/phone";

const INTERRUPTIONS = ["pagehide", "freeze", "blur"] as const;
const PRESENCE = ["pointerdown", "keydown", "touchstart", "scroll"] as const;

export function useAnswerDisplay(attemptId: string, wanted: boolean): { shown: boolean; status: ExposureStatus } {
  const [, setVersion] = useState(0);
  const bump = useCallback(() => setVersion((value) => value + 1), []);
  const gates = useRef<{ attemptId: string; gate: AnswerExposureGate } | null>(null);
  if (gates.current === null || gates.current.attemptId !== attemptId) {
    gates.current = {
      attemptId,
      gate: new AnswerExposureGate((displayId) => phone.recordAnswerDisplay(attemptId, displayId), () => Date.now(), bump)
    };
  }
  const gate = gates.current.gate;
  const wantedRef = useRef(wanted);
  wantedRef.current = wanted;

  useEffect(() => {
    if (!wanted) return undefined;
    gate.activity();
    gate.check(document.visibilityState !== "hidden");
    bump();
    const tick = window.setInterval(() => {
      gate.check(wantedRef.current && document.visibilityState !== "hidden");
      bump();
    }, EXPOSURE.tickMs);
    const interrupt = () => {
      gate.interrupt();
      bump();
    };
    const visibility = () => {
      if (document.visibilityState === "hidden") {
        interrupt();
        return;
      }
      gate.activity();
      gate.check(wantedRef.current);
      bump();
    };
    const present = () => gate.activity();
    document.addEventListener("visibilitychange", visibility);
    for (const name of INTERRUPTIONS) window.addEventListener(name, interrupt);
    for (const name of PRESENCE) window.addEventListener(name, present, { passive: true });
    return () => {
      window.clearInterval(tick);
      document.removeEventListener("visibilitychange", visibility);
      for (const name of INTERRUPTIONS) window.removeEventListener(name, interrupt);
      for (const name of PRESENCE) window.removeEventListener(name, present);
    };
  }, [gate, wanted, bump]);

  const shown = wanted && document.visibilityState !== "hidden" && gate.covered();
  return { shown, status: wanted ? gate.status() : "waiting" };
}
