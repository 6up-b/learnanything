import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { RuntimeHealth, SettingsDto, UseCaseChoiceInput } from "../api/dto";
import { COLOR, FONT_MONO, TermCheckbox, TermSelect } from "../components/term";
import { SectionHeader } from "../components/ui";

// UI metadata for the backend's use-case -> [ai.routing] expansion
// (services/settings_store.USE_CASE_ROUTES). primaryRoute is the camelized
// routing key the current selection is derived from.
const USE_CASES: Array<{ id: string; label: string; hint: string; primaryRoute: string }> = [
  { id: "grading", label: "grading", hint: "attempt grading + misconception match", primaryRoute: "grading" },
  { id: "ingest", label: "ingest / synthesis", hint: "canonical ingest, study-map synthesis, authoring", primaryRoute: "canonicalIngest" },
  { id: "tutor", label: "tutor", hint: "tutor Q&A, teach-back, rung variants", primaryRoute: "tutorQa" },
  { id: "animation", label: "animation", hint: "manim explainer-scene authoring", primaryRoute: "animation" }
];

export const PALETTE_STORAGE_KEY = "learnloop.palette";
const PALETTES = [
  { value: "", label: "terminal (default)" },
  { value: "dracula", label: "dracula" },
  { value: "gruvbox", label: "gruvbox" },
  { value: "nord", label: "nord" },
  { value: "catppuccin-mocha", label: "catppuccin mocha" }
];

function applyPalette(palette: string) {
  if (palette) {
    document.documentElement.dataset.palette = palette;
    localStorage.setItem(PALETTE_STORAGE_KEY, palette);
  } else {
    delete document.documentElement.dataset.palette;
    localStorage.removeItem(PALETTE_STORAGE_KEY);
  }
}

type UseCaseDraft = { provider: string; model: string };

export function SettingsScreen({
  manualGrading,
  onSelectGradingProvider,
  onHealthChanged,
  onToast,
  onError
}: {
  manualGrading: boolean;
  onSelectGradingProvider: (provider: string) => void;
  onHealthChanged: (health: RuntimeHealth) => void;
  onToast: (message: string) => void;
  onError: (message: string) => void;
}) {
  const [settings, setSettings] = useState<SettingsDto | null>(null);
  const [drafts, setDrafts] = useState<Record<string, UseCaseDraft>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [keyDraft, setKeyDraft] = useState("");
  const [transcriptionKeyDraft, setTranscriptionKeyDraft] = useState("");
  const [transcriptionModelDraft, setTranscriptionModelDraft] = useState<string | null>(null);
  const [transcriptionUrlDraft, setTranscriptionUrlDraft] = useState<string | null>(null);
  const [palette, setPalette] = useState(() => localStorage.getItem(PALETTE_STORAGE_KEY) ?? "");

  const acceptSettings = useCallback((next: SettingsDto) => {
    setSettings(next);
    if (next.health) onHealthChanged(next.health);
  }, [onHealthChanged]);

  useEffect(() => {
    api
      .getSettings()
      .then(setSettings)
      .catch((error) => onError((error as Error).message));
  }, [onError]);

  const providerByName = useMemo(() => {
    const map = new Map<string, { model: string | null }>();
    for (const provider of settings?.ai.providers ?? []) map.set(provider.name, provider);
    return map;
  }, [settings]);

  // Selectable backends: configured providers minus the materialized
  // per-use-case openrouter_<usecase> profiles (implementation detail).
  const providerOptions = useMemo(
    () =>
      (settings?.ai.providers ?? [])
        .map((provider) => provider.name)
        .filter((name) => name === "openrouter" || !name.startsWith("openrouter_")),
    [settings]
  );

  const currentForUseCase = useCallback(
    (useCase: (typeof USE_CASES)[number]): UseCaseDraft => {
      const routed = settings?.ai.routing[useCase.primaryRoute] ?? settings?.ai.activeProvider ?? "codex";
      if (routed && routed.startsWith("openrouter")) {
        const model = providerByName.get(routed)?.model ?? providerByName.get("openrouter")?.model ?? "";
        return { provider: "openrouter", model: model ?? "" };
      }
      return { provider: routed ?? "codex", model: "" };
    },
    [settings, providerByName]
  );

  const draftFor = (useCase: (typeof USE_CASES)[number]): UseCaseDraft =>
    drafts[useCase.id] ?? currentForUseCase(useCase);

  const applyUseCase = async (useCase: (typeof USE_CASES)[number]) => {
    const draft = draftFor(useCase);
    if (useCase.id === "grading" && draft.provider === "manual") {
      onSelectGradingProvider("manual");
      setDrafts((d) => ({ ...d, [useCase.id]: draft }));
      return;
    }
    const choice: UseCaseChoiceInput = { provider: draft.provider };
    if (draft.provider === "openrouter") choice.openrouterModel = draft.model;
    setBusy(useCase.id);
    try {
      const result = await api.updateAiSettings({ useCases: { [useCase.id]: choice } });
      acceptSettings(result);
      setDrafts((d) => {
        const next = { ...d };
        delete next[useCase.id];
        return next;
      });
      onToast(`${useCase.label} → ${draft.provider === "openrouter" ? `openrouter (${draft.model})` : draft.provider}`);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setBusy(null);
    }
  };

  const saveKey = async (value: string) => {
    setBusy("apikey");
    try {
      const result = await api.setOpenrouterApiKey(value);
      setSettings((current) =>
        current
          ? {
              ...current,
              openrouter: {
                keyPresent: result.keyPresent,
                keyHint: result.keyHint,
                settingsEnvPath: result.settingsEnvPath
              }
            }
          : current
      );
      setKeyDraft("");
      onToast(
        value
          ? `openrouter key saved (${result.ready ? "ready" : result.status})`
          : "openrouter key removed"
      );
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setBusy(null);
    }
  };

  const rowStyle = {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "7px 0",
    borderBottom: `1px solid ${COLOR.border}`,
    fontFamily: FONT_MONO,
    fontSize: 12
  } as const;
  const labelStyle = { width: 170, color: COLOR.text } as const;
  const hintStyle = { color: COLOR.textFaint, fontSize: 10 } as const;
  const inputStyle = {
    background: COLOR.bgInput,
    border: `1px solid ${COLOR.border}`,
    borderRadius: 2,
    color: COLOR.text,
    fontFamily: FONT_MONO,
    fontSize: 12,
    padding: "4px 8px"
  } as const;
  const buttonStyle = (enabled: boolean) =>
    ({
      background: enabled ? COLOR.washAmber : COLOR.bgInput,
      border: `1px solid ${enabled ? COLOR.amber : COLOR.border}`,
      borderRadius: 2,
      color: enabled ? COLOR.amber : COLOR.textFaint,
      fontFamily: FONT_MONO,
      fontSize: 11,
      padding: "3px 10px",
      cursor: enabled ? "pointer" : "default"
    }) as const;

  if (!settings) {
    return (
      <div style={{ padding: 24, fontFamily: FONT_MONO, color: COLOR.textDim }}>loading settings…</div>
    );
  }

  const envOverride = settings.ai.envProviderOverride;

  return (
    <div style={{ padding: "18px 26px", overflowY: "auto", height: "100%", maxWidth: 760 }}>
      <SectionHeader>AI models</SectionHeader>
      {envOverride ? (
        <div
          style={{
            ...rowStyle,
            borderBottom: "none",
            background: COLOR.washRed,
            border: `1px solid ${COLOR.red}`,
            borderRadius: 2,
            padding: "6px 10px",
            color: COLOR.red,
            marginBottom: 8
          }}
        >
          LEARNLOOP_AI_PROVIDER={envOverride} is set in the environment and overrides every route below.
        </div>
      ) : null}
      {USE_CASES.map((useCase) => {
        const draft = draftFor(useCase);
        const current = currentForUseCase(useCase);
        const isManual = useCase.id === "grading" && manualGrading && !drafts[useCase.id];
        const dirty =
          !isManual && (draft.provider !== current.provider || (draft.provider === "openrouter" && draft.model !== current.model));
        const canApply =
          dirty && busy === null && (draft.provider !== "openrouter" || draft.model.trim().length > 0);
        const options =
          useCase.id === "grading" ? [...providerOptions, "manual"] : providerOptions;
        return (
          <div key={useCase.id} style={rowStyle}>
            <span style={labelStyle}>
              {useCase.label}
              <div style={hintStyle}>{useCase.hint}</div>
            </span>
            <TermSelect
              value={isManual ? "manual" : draft.provider}
              options={options}
              width={170}
              onChange={(provider) =>
                setDrafts((d) => ({ ...d, [useCase.id]: { provider, model: draft.model } }))
              }
            />
            {draft.provider === "openrouter" ? (
              <input
                style={{ ...inputStyle, flex: 1, minWidth: 180 }}
                placeholder="model slug, e.g. anthropic/claude-sonnet-4.5"
                value={draft.model}
                onChange={(event) =>
                  setDrafts((d) => ({
                    ...d,
                    [useCase.id]: { provider: "openrouter", model: event.target.value }
                  }))
                }
              />
            ) : (
              <span style={{ flex: 1, color: COLOR.textFaint, fontSize: 11 }}>
                {providerByName.get(draft.provider)?.model ?? ""}
              </span>
            )}
            <button
              type="button"
              style={buttonStyle(canApply)}
              disabled={!canApply}
              onClick={() => void applyUseCase(useCase)}
            >
              {busy === useCase.id ? "…" : "apply"}
            </button>
          </div>
        );
      })}
      <div style={{ ...rowStyle, borderBottom: "none" }}>
        <span style={{ ...hintStyle, fontSize: 10 }}>
          Choices persist to learnloop.toml; an OpenRouter pick materializes a per-use-case provider
          profile so different tasks can run different models.
        </span>
      </div>

      <SectionHeader>OpenRouter API key</SectionHeader>
      <div style={rowStyle}>
        <span style={labelStyle}>
          status
          <div style={hintStyle}>{settings.openrouter.settingsEnvPath}</div>
        </span>
        <span style={{ color: settings.openrouter.keyPresent ? COLOR.green : COLOR.textDim, fontSize: 11 }}>
          {settings.openrouter.keyPresent
            ? `saved${settings.openrouter.keyHint ? ` · ends in ····${settings.openrouter.keyHint}` : ""}`
            : "not set"}
        </span>
      </div>
      <div style={{ ...rowStyle, borderBottom: "none" }}>
        <span style={labelStyle}>set key</span>
        <input
          type="password"
          style={{ ...inputStyle, flex: 1 }}
          placeholder="sk-or-…"
          value={keyDraft}
          onChange={(event) => setKeyDraft(event.target.value)}
        />
        <button
          type="button"
          style={buttonStyle(keyDraft.trim().length > 0 && busy === null)}
          disabled={keyDraft.trim().length === 0 || busy !== null}
          onClick={() => void saveKey(keyDraft.trim())}
        >
          {busy === "apikey" ? "…" : "save"}
        </button>
        {settings.openrouter.keyPresent ? (
          <button
            type="button"
            style={buttonStyle(busy === null)}
            disabled={busy !== null}
            onClick={() => void saveKey("")}
          >
            clear
          </button>
        ) : null}
      </div>

      <SectionHeader>Ingestion</SectionHeader>
      <div style={rowStyle}>
        <span style={labelStyle}>
          native multimodal
          <div style={hintStyle}>
            send audio/PDF media to the routed chat model when it declares the modality
          </div>
        </span>
        <TermCheckbox
          checked={settings.ingest.nativeMultimodal}
          label={settings.ingest.nativeMultimodal ? "enabled" : "disabled"}
          disabled={busy !== null}
          onChange={(next) => {
            setBusy("ingest");
            api
              .updateIngestSettings({ nativeMultimodal: next })
              .then((result) => {
                acceptSettings(result);
                onToast(`native multimodal → ${next ? "on" : "off"}`);
              })
              .catch((error) => onError((error as Error).message))
              .finally(() => setBusy(null));
          }}
        />
      </div>
      <div style={rowStyle}>
        <span style={labelStyle}>
          transcription
          <div style={hintStyle}>OpenAI-compatible /audio/transcriptions endpoint</div>
        </span>
        <input
          style={{ ...inputStyle, width: 170 }}
          placeholder="model, e.g. whisper-1"
          value={transcriptionModelDraft ?? settings.ingest.transcriptionModel}
          onChange={(event) => setTranscriptionModelDraft(event.target.value)}
        />
        <input
          style={{ ...inputStyle, flex: 1, minWidth: 160 }}
          placeholder="base URL"
          value={transcriptionUrlDraft ?? settings.ingest.transcriptionBaseUrl}
          onChange={(event) => setTranscriptionUrlDraft(event.target.value)}
        />
        <button
          type="button"
          style={buttonStyle(
            busy === null &&
              ((transcriptionModelDraft !== null && transcriptionModelDraft !== settings.ingest.transcriptionModel) ||
                (transcriptionUrlDraft !== null && transcriptionUrlDraft !== settings.ingest.transcriptionBaseUrl))
          )}
          disabled={busy !== null}
          onClick={() => {
            setBusy("transcription");
            api
              .updateIngestSettings({
                ...(transcriptionModelDraft !== null ? { transcriptionModel: transcriptionModelDraft } : {}),
                ...(transcriptionUrlDraft !== null ? { transcriptionBaseUrl: transcriptionUrlDraft } : {})
              })
              .then((result) => {
                acceptSettings(result);
                setTranscriptionModelDraft(null);
                setTranscriptionUrlDraft(null);
                onToast("transcription settings saved");
              })
              .catch((error) => onError((error as Error).message))
              .finally(() => setBusy(null));
          }}
        >
          {busy === "transcription" ? "…" : "apply"}
        </button>
      </div>
      <div style={{ ...rowStyle, borderBottom: "none" }}>
        <span style={labelStyle}>
          transcription key
          <div style={hintStyle}>
            {settings.ingest.transcriptionKey.keyPresent
              ? `saved${settings.ingest.transcriptionKey.keyHint ? ` · ends in ····${settings.ingest.transcriptionKey.keyHint}` : ""}`
              : "not set"}
          </div>
        </span>
        <input
          type="password"
          style={{ ...inputStyle, flex: 1 }}
          placeholder="endpoint API key"
          value={transcriptionKeyDraft}
          onChange={(event) => setTranscriptionKeyDraft(event.target.value)}
        />
        <button
          type="button"
          style={buttonStyle(transcriptionKeyDraft.trim().length > 0 && busy === null)}
          disabled={transcriptionKeyDraft.trim().length === 0 || busy !== null}
          onClick={() => {
            setBusy("transcription-key");
            api
              .setTranscriptionApiKey(transcriptionKeyDraft.trim())
              .then((result) => {
                setSettings((current) =>
                  current
                    ? {
                        ...current,
                        ingest: {
                          ...current.ingest,
                          transcriptionKey: { keyPresent: result.keyPresent, keyHint: result.keyHint }
                        }
                      }
                    : current
                );
                setTranscriptionKeyDraft("");
                onToast("transcription key saved");
              })
              .catch((error) => onError((error as Error).message))
              .finally(() => setBusy(null));
          }}
        >
          {busy === "transcription-key" ? "…" : "save"}
        </button>
      </div>

      <SectionHeader>Appearance</SectionHeader>
      <div style={{ ...rowStyle, borderBottom: "none" }}>
        <span style={labelStyle}>color palette</span>
        <TermSelect
          value={palette}
          options={PALETTES}
          width={200}
          onChange={(next) => {
            setPalette(next);
            applyPalette(next);
            onToast(`palette → ${PALETTES.find((p) => p.value === next)?.label ?? next}`);
          }}
        />
        <span style={{ display: "inline-flex", gap: 4 }} aria-hidden="true">
          {[COLOR.amber, COLOR.green, COLOR.cyan, COLOR.red, COLOR.pink].map((tone, index) => (
            <span
              key={index}
              style={{ width: 14, height: 14, borderRadius: 2, background: tone, border: `1px solid ${COLOR.border}` }}
            />
          ))}
        </span>
      </div>
    </div>
  );
}
