// Settings → Ingestion → media: one row per media modality that has a native
// ingest path (PDF, audio), each with its own authority ([ingest.pdf] engine,
// [ingest.audio] mode), a readiness line computed by the sidecar with the same
// judgement the import pipeline uses, and a capabilities panel that declares
// (or detects, for OpenRouter) which modalities each chat provider accepts.
import { useEffect, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type {
  AudioMode,
  NativeModalityStateDto,
  PdfEngine,
  ProviderCapabilitiesDto,
  SettingsDto,
  SettingsProviderDto
} from "../api/dto";
import { COLOR, TermCheckbox, TermSelect } from "./term";

const PDF_ENGINE_OPTIONS: Array<{ value: PdfEngine; label: string }> = [
  { value: "auto", label: "local — auto (marker if installed, else pypdf)" },
  { value: "marker", label: "local — marker (structured, math, OCR)" },
  { value: "pypdf", label: "local — pypdf (fast, no OCR)" },
  { value: "native", label: "send to the ingest model natively" }
];

const AUDIO_MODE_OPTIONS: Array<{ value: AudioMode; label: string }> = [
  { value: "transcription", label: "transcription endpoint / route (below)" },
  { value: "native", label: "send to the ingest model natively (mp3/wav)" }
];

const CHAT_PROVIDER_TYPES = new Set(["openai_chat", "openrouter"]);

export interface SettingsStyles {
  row: CSSProperties;
  label: CSSProperties;
  hint: CSSProperties;
  button: (enabled: boolean) => CSSProperties;
}

function ReadinessLine({ state }: { state: NativeModalityStateDto }) {
  if (state.ready) {
    return (
      <span style={{ color: COLOR.green, fontSize: 10 }}>
        ready · {state.providerName} ({state.model ?? "no model"}) accepts {state.modality}
      </span>
    );
  }
  return <span style={{ color: COLOR.red, fontSize: 10 }}>not ready · {state.message}</span>;
}

function ModalityChips({ modalities, known }: { modalities: string[]; known: string[] }) {
  return (
    <span style={{ display: "inline-flex", gap: 6 }}>
      {known.map((modality) => {
        const on = modalities.includes(modality);
        return (
          <span key={modality} style={{ color: on ? COLOR.text : COLOR.textFaint, fontSize: 10 }}>
            {on ? "▣" : "▢"} {modality}
          </span>
        );
      })}
    </span>
  );
}

export function NativeMediaSettings({
  settings,
  busy,
  setBusy,
  acceptSettings,
  onToast,
  onError,
  styles
}: {
  settings: SettingsDto;
  busy: string | null;
  setBusy: (value: string | null) => void;
  acceptSettings: (next: SettingsDto) => void;
  onToast: (message: string) => void;
  onError: (message: string) => void;
  styles: SettingsStyles;
}) {
  const native = settings.ingest.native;
  const pdfState = native.modalities.find((entry) => entry.modality === "pdf") ?? null;
  const audioState = native.modalities.find((entry) => entry.modality === "audio") ?? null;
  const [detections, setDetections] = useState<Record<string, ProviderCapabilitiesDto>>({});
  const [detecting, setDetecting] = useState<string | null>(null);

  const saveIngest = (input: Parameters<typeof api.updateIngestSettings>[0], toast: string) => {
    setBusy("ingest");
    api
      .updateIngestSettings(input)
      .then((result) => {
        acceptSettings(result);
        onToast(toast);
      })
      .catch((error) => onError((error as Error).message))
      .finally(() => setBusy(null));
  };

  const detect = (provider: string, refresh: boolean, { quiet = false } = {}) => {
    if (!quiet) setDetecting(provider);
    return api
      .detectProviderCapabilities({ provider, refresh })
      .then((result) => setDetections((current) => ({ ...current, [provider]: result })))
      .catch((error) => {
        if (!quiet) onError((error as Error).message);
      })
      .finally(() => {
        if (!quiet) setDetecting(null);
      });
  };

  const applyModalities = (provider: string, inputModalities: string[]) => {
    setBusy("modalities");
    api
      .updateProviderModalities({ provider, inputModalities })
      .then((result) => {
        acceptSettings(result);
        onToast(`${provider} accepts: ${inputModalities.join(", ") || "text only"}`);
      })
      .catch((error) => onError((error as Error).message))
      .finally(() => setBusy(null));
  };

  // One background lookup for the routed OpenRouter profile when its
  // declaration is missing or the catalog is stale. Never blocks rendering;
  // a failure leaves the declared state on screen.
  useEffect(() => {
    const routed = [pdfState, audioState].filter(
      (state): state is NativeModalityStateDto =>
        state !== null && state.providerType === "openrouter" && state.providerName !== null && (!state.declared || native.catalog.stale)
    );
    const providers = Array.from(new Set(routed.map((state) => state.providerName as string)));
    for (const provider of providers) {
      if (!detections[provider]) void detect(provider, false, { quiet: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pdfState?.providerName, audioState?.providerName, native.catalog.stale]);

  const chatProviders: SettingsProviderDto[] = settings.ai.providers.filter((provider) =>
    CHAT_PROVIDER_TYPES.has(provider.type)
  );

  const detectButton = (provider: string) => (
    <button
      type="button"
      style={styles.button(busy === null && detecting === null)}
      disabled={busy !== null || detecting !== null}
      onClick={() => void detect(provider, Boolean(detections[provider]))}
    >
      {detecting === provider ? "…" : detections[provider] ? "refresh" : "detect"}
    </button>
  );

  return (
    <>
      <div style={styles.row}>
        <span style={styles.label}>
          PDF
          <div style={styles.hint}>how PDF sources become text · page ranges only apply to local engines</div>
        </span>
        <TermSelect
          value={settings.ingest.pdfEngine}
          options={PDF_ENGINE_OPTIONS}
          width={300}
          disabled={busy !== null}
          onChange={(value) => saveIngest({ pdfEngine: value as PdfEngine }, `PDF engine → ${value}`)}
        />
        {settings.ingest.pdfEngine === "native" && pdfState ? (
          <>
            <ReadinessLine state={pdfState} />
            {!pdfState.ready && pdfState.providerType === "openrouter" && pdfState.providerName
              ? detectButton(pdfState.providerName)
              : null}
          </>
        ) : (
          <span style={styles.hint}>PDF bytes stay on this machine</span>
        )}
      </div>
      {settings.ingest.pdfEngine === "native" ? (
        <div style={styles.row}>
          <span style={styles.label}>
            <div style={styles.hint}>
              otherwise imports fail with native_pdf_unavailable until the ingest route is fixed · max{" "}
              {native.maxPdfMb} MB per PDF
            </div>
          </span>
          <TermCheckbox
            checked={native.fallbackWhenUnavailable}
            label="fall back to local extraction when the model cannot take the file"
            disabled={busy !== null}
            onChange={(next) =>
              saveIngest({ nativeFallbackWhenUnavailable: next }, `native fallback → ${next ? "on" : "off"}`)
            }
          />
        </div>
      ) : null}

      <div style={styles.row}>
        <span style={styles.label}>
          audio
          <div style={styles.hint}>
            how audio sources become transcripts
            {settings.ingest.audioMode === "native"
              ? ` · other formats still use the transcription settings below · max ${native.maxAudioMb} MB`
              : ""}
          </div>
        </span>
        <TermSelect
          value={settings.ingest.audioMode}
          options={AUDIO_MODE_OPTIONS}
          width={300}
          disabled={busy !== null}
          onChange={(value) => saveIngest({ audioMode: value as AudioMode }, `audio → ${value}`)}
        />
        {settings.ingest.audioMode === "native" && audioState ? (
          <>
            <ReadinessLine state={audioState} />
            {!audioState.ready && audioState.providerType === "openrouter" && audioState.providerName
              ? detectButton(audioState.providerName)
              : null}
          </>
        ) : null}
      </div>

      <div style={{ ...styles.row, alignItems: "flex-start" }}>
        <span style={styles.label}>
          model capabilities
          <div style={styles.hint}>
            input modalities each chat provider declares ([ai.providers.*] input_modalities) — this is what
            ingestion trusts
          </div>
        </span>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, flex: 1 }}>
          {chatProviders.length === 0 ? (
            <span style={styles.hint}>no OpenAI-compatible chat providers configured</span>
          ) : null}
          {chatProviders.map((provider) => {
            const detection = detections[provider.name];
            const detectedDiffers =
              detection?.detected != null &&
              (detection.detected.length !== provider.inputModalities.length ||
                detection.detected.some((m) => !provider.inputModalities.includes(m)));
            return (
              <div key={provider.name} style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <span style={{ color: COLOR.text, minWidth: 220 }}>
                  {provider.name}
                  <span style={{ color: COLOR.textFaint }}> ({provider.model ?? "no model"})</span>
                </span>
                {provider.type === "openai_chat" ? (
                  <span style={{ display: "inline-flex", gap: 8 }}>
                    {native.knownModalities.map((modality) => (
                      <TermCheckbox
                        key={modality}
                        compact
                        checked={provider.inputModalities.includes(modality)}
                        label={modality}
                        disabled={busy !== null}
                        onChange={(next) =>
                          applyModalities(
                            provider.name,
                            next
                              ? [...provider.inputModalities, modality]
                              : provider.inputModalities.filter((m) => m !== modality)
                          )
                        }
                      />
                    ))}
                  </span>
                ) : (
                  <>
                    <ModalityChips modalities={provider.inputModalities} known={native.knownModalities} />
                    {detectButton(provider.name)}
                    {detection ? (
                      <span style={{ ...styles.hint, color: detection.source === "unavailable" ? COLOR.red : COLOR.textFaint }}>
                        {detection.message}
                        {detection.source === "cache" ? ` (cached${detection.stale ? ", stale" : ""})` : ""}
                      </span>
                    ) : null}
                    {detection && detectedDiffers ? (
                      <button
                        type="button"
                        style={styles.button(busy === null)}
                        disabled={busy !== null}
                        onClick={() => applyModalities(provider.name, detection.detected ?? [])}
                      >
                        apply detected: {(detection.detected ?? []).join(", ") || "text only"}
                      </button>
                    ) : null}
                  </>
                )}
              </div>
            );
          })}
          <span style={styles.hint}>
            OpenRouter capabilities come from openrouter.ai/api/v1/models (cached 24h at {native.catalog.path}
            {native.catalog.cached ? `, fetched ${native.catalog.fetchedAt ?? "?"}` : ", not fetched yet"}); other
            providers are declared by hand.
          </span>
        </div>
      </div>
    </>
  );
}
