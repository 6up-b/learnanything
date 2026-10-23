// Plan-first transport T1 (owner decision 2026-10-21): while the ChatGPT plan
// can't serve a feature, the feature shows its own "unavailable" state and this
// banner asks whether to use OpenRouter instead. Choosing it runs that feature
// on the configured OpenRouter profile for the rest of this session (inside
// its usual spend limits); nothing goes to OpenRouter otherwise. The sidecar
// only offers it when an OpenRouter key is set up.

import { useEffect, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import {
  clearFallbackOffer,
  currentFallbackOffer,
  subscribeFallbackOffer,
  type PlanFallbackOffer as Offer
} from "../app/planFallback";
import { plainError } from "../copy/ingestErrors";
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

export function PlanFallbackOffer({ onContinueWithChatGPT }: { onContinueWithChatGPT: () => void }) {
  const [offer, setOffer] = useState<Offer | null>(() => currentFallbackOffer());
  const [busy, setBusy] = useState(false);
  const [chosen, setChosen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(
    () =>
      subscribeFallbackOffer((next) => {
        setOffer(next);
        if (next) setChosen(false);
      }),
    []
  );

  if (!offer) return null;

  const stopOpenRouter = async () => {
    setBusy(true);
    setError(null);
    try {
      // Review F8: the grant can be taken back; the next unavailable feature asks again.
      await api.aiUseFallback({ provider: "openrouter", tasks: [], stop: true });
      clearFallbackOffer();
    } catch (failure) {
      setError(plainError(failure, "LearnLoop couldn't stop using OpenRouter.").line);
    } finally {
      setBusy(false);
    }
  };

  const useOpenRouter = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.aiUseFallback({ provider: "openrouter", tasks: offer.tasks });
      setChosen(true);
    } catch (failure) {
      setError(plainError(failure, "LearnLoop couldn't switch to OpenRouter.").line);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      role="status"
      aria-label="ChatGPT unavailable"
      style={{
        position: "fixed",
        right: 16,
        bottom: 16,
        zIndex: 70,
        width: 380,
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
      {chosen ? (
        <>
          <div style={{ color: COLOR.text }}>OpenRouter will do this for the rest of this session. Try it again.</div>
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button
              type="button"
              style={{ ...button, border: "none", color: COLOR.amberLink }}
              disabled={busy}
              onClick={() => void stopOpenRouter()}
            >
              Stop using OpenRouter
            </button>
            <button type="button" style={button} disabled={busy} onClick={clearFallbackOffer}>
              OK
            </button>
          </div>
          {error ? (
            <div role="alert" style={{ color: COLOR.amber }}>
              {error}
            </div>
          ) : null}
        </>
      ) : (
        <>
          <div style={{ color: COLOR.text }}>ChatGPT isn't available right now.</div>
          <div>
            OpenRouter can do this instead, with your OpenRouter key (it charges that account). Nothing goes to
            OpenRouter unless you choose it.
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="button" style={button} disabled={busy} onClick={() => void useOpenRouter()}>
              Use OpenRouter instead
            </button>
            {offer.planSignedOut ? (
              <button
                type="button"
                style={button}
                disabled={busy}
                onClick={() => {
                  clearFallbackOffer();
                  onContinueWithChatGPT();
                }}
              >
                Continue with ChatGPT
              </button>
            ) : null}
            <button type="button" style={{ ...button, border: "none", color: COLOR.amberLink }} onClick={clearFallbackOffer}>
              Not now
            </button>
          </div>
          {error ? (
            <div role="alert" style={{ color: COLOR.amber }}>
              {error}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
