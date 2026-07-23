import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { RuntimeHealth, SettingsDto, UseCaseChoiceInput } from "../api/dto";
import { COLOR, FONT_MONO, TermSelect } from "../components/term";
import { SectionHeader } from "../components/ui";

const USE_CASES = [
  {
    id: "grading",
    label: "grading",
    hint: "attempt grading and misconception matching",
    primaryRoute: "grading"
  },
  {
    id: "ingest",
    label: "ingest / synthesis",
    hint: "canonical ingest, study-map synthesis, and authoring",
    primaryRoute: "canonicalIngest"
  },
  {
    id: "tutor",
    label: "tutor",
    hint: "tutor Q&A, teach-back, and rung variants",
    primaryRoute: "tutorQa"
  }
] as const;

type UseCase = (typeof USE_CASES)[number];
type UseCaseDraft = { provider: string; model: string };

export function SettingsScreen({
  manualGrading,
  onSelectGradingProvider,
  onHealthChanged,
  onToast,
  onError
}: {
  manualGrading: boolean;
  onSelectGradingProvider: (provider: string) => Promise<void>;
  onHealthChanged: (health: RuntimeHealth) => void;
  onToast: (message: string) => void;
  onError: (message: string) => void;
}) {
  const [settings, setSettings] = useState<SettingsDto | null>(null);
  const [drafts, setDrafts] = useState<Record<string, UseCaseDraft>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [keyDraft, setKeyDraft] = useState("");

  const acceptSettings = useCallback(
    (next: SettingsDto) => {
      setSettings(next);
      if (next.health) onHealthChanged(next.health);
    },
    [onHealthChanged]
  );

  useEffect(() => {
    api
      .getSettings()
      .then(setSettings)
      .catch((error) => onError((error as Error).message));
  }, [onError]);

  const providerByName = useMemo(() => {
    const map = new Map<string, { model: string | null }>();
    for (const provider of settings?.ai.providers ?? []) {
      map.set(provider.name, provider);
    }
    return map;
  }, [settings]);

  // Per-use-case OpenRouter profiles are an implementation detail. The user
  // selects "openrouter" plus a model slug and the backend materializes them.
  const providerOptions = useMemo(
    () =>
      (settings?.ai.providers ?? [])
        .map((provider) => provider.name)
        .filter((name) => name === "openrouter" || !name.startsWith("openrouter_")),
    [settings]
  );

  const currentForUseCase = useCallback(
    (useCase: UseCase): UseCaseDraft => {
      const routed =
        settings?.ai.routing[useCase.primaryRoute] ??
        settings?.ai.activeProvider ??
        "codex";
      if (routed.startsWith("openrouter")) {
        return {
          provider: "openrouter",
          model:
            providerByName.get(routed)?.model ??
            providerByName.get("openrouter")?.model ??
            ""
        };
      }
      return { provider: routed, model: "" };
    },
    [providerByName, settings]
  );

  const draftFor = (useCase: UseCase): UseCaseDraft =>
    drafts[useCase.id] ?? currentForUseCase(useCase);

  const applyUseCase = async (useCase: UseCase) => {
    const draft = draftFor(useCase);
    setBusy(useCase.id);
    try {
      if (useCase.id === "grading" && draft.provider === "manual") {
        await onSelectGradingProvider("manual");
      } else {
        const choice: UseCaseChoiceInput = { provider: draft.provider };
        if (draft.provider === "openrouter") {
          choice.openrouterModel = draft.model.trim();
        }
        const result = await api.updateAiSettings({
          useCases: { [useCase.id]: choice }
        });
        acceptSettings(result);
        onToast(
          `${useCase.label} → ${
            draft.provider === "openrouter"
              ? `openrouter (${draft.model.trim()})`
              : draft.provider
          }`
        );
      }
      setDrafts((current) => {
        const next = { ...current };
        delete next[useCase.id];
        return next;
      });
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setBusy(null);
    }
  };

  const saveKey = async (value: string) => {
    setBusy("api-key");
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
          ? `OpenRouter key saved (${result.ready ? "ready" : result.status})`
          : "OpenRouter key removed"
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
    padding: "9px 0",
    borderBottom: `1px solid ${COLOR.border}`,
    fontFamily: FONT_MONO,
    fontSize: 12
  } as const;
  const labelStyle = { width: 180, flex: "0 0 180px", color: COLOR.text } as const;
  const hintStyle = { color: COLOR.textFaint, fontSize: 10, marginTop: 2 } as const;
  const inputStyle = {
    background: COLOR.bgInput,
    border: `1px solid ${COLOR.border}`,
    borderRadius: 2,
    color: COLOR.text,
    fontFamily: FONT_MONO,
    fontSize: 12,
    padding: "5px 8px"
  } as const;
  const buttonStyle = (enabled: boolean) =>
    ({
      background: enabled ? COLOR.washAmber : COLOR.bgInput,
      border: `1px solid ${enabled ? COLOR.amber : COLOR.border}`,
      borderRadius: 2,
      color: enabled ? COLOR.amber : COLOR.textFaint,
      fontFamily: FONT_MONO,
      fontSize: 11,
      padding: "4px 10px",
      cursor: enabled ? "pointer" : "default"
    }) as const;

  if (!settings) {
    return (
      <div style={{ padding: 24, fontFamily: FONT_MONO, color: COLOR.textDim }}>
        loading settings…
      </div>
    );
  }

  return (
    <div
      style={{
        padding: "18px 26px 32px",
        overflowY: "auto",
        height: "100%",
        maxWidth: 820
      }}
    >
      <SectionHeader>AI models</SectionHeader>
      {settings.ai.envProviderOverride ? (
        <div
          style={{
            ...rowStyle,
            border: `1px solid ${COLOR.red}`,
            background: COLOR.washRed,
            borderRadius: 2,
            color: COLOR.red,
            padding: "7px 10px",
            marginBottom: 8
          }}
        >
          LEARNLOOP_AI_PROVIDER={settings.ai.envProviderOverride} overrides the
          persisted routes below.
        </div>
      ) : null}

      {USE_CASES.map((useCase) => {
        const draft = draftFor(useCase);
        const current = currentForUseCase(useCase);
        const isManual =
          useCase.id === "grading" &&
          manualGrading &&
          drafts[useCase.id] === undefined;
        const dirty =
          isManual
            ? false
            : draft.provider !== current.provider ||
              (draft.provider === "openrouter" &&
                draft.model.trim() !== current.model);
        const canApply =
          dirty &&
          busy === null &&
          (draft.provider !== "openrouter" || draft.model.trim().length > 0);
        const options =
          useCase.id === "grading"
            ? [...providerOptions, "manual"]
            : providerOptions;
        return (
          <div key={useCase.id} style={rowStyle}>
            <span style={labelStyle}>
              {useCase.label}
              <div style={hintStyle}>{useCase.hint}</div>
            </span>
            <TermSelect
              value={isManual ? "manual" : draft.provider}
              options={options}
              width={175}
              ariaLabel={`${useCase.label} provider`}
              onChange={(provider) => {
                const defaultModel =
                  provider === "openrouter"
                    ? draft.model ||
                      providerByName.get("openrouter")?.model ||
                      ""
                    : draft.model;
                setDrafts((currentDrafts) => ({
                  ...currentDrafts,
                  [useCase.id]: { provider, model: defaultModel }
                }));
              }}
            />
            {draft.provider === "openrouter" ? (
              <input
                style={{ ...inputStyle, flex: 1, minWidth: 210 }}
                aria-label={`${useCase.label} OpenRouter model`}
                placeholder="vendor/model"
                value={draft.model}
                onChange={(event) =>
                  setDrafts((currentDrafts) => ({
                    ...currentDrafts,
                    [useCase.id]: {
                      provider: "openrouter",
                      model: event.target.value
                    }
                  }))
                }
              />
            ) : (
              <span
                style={{
                  flex: 1,
                  color: COLOR.textFaint,
                  fontSize: 11,
                  overflow: "hidden",
                  textOverflow: "ellipsis"
                }}
              >
                {draft.provider === "manual"
                  ? "self grading"
                  : providerByName.get(draft.provider)?.model ?? ""}
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

      <p style={{ ...hintStyle, margin: "8px 0 22px" }}>
        Provider choices are stored in this vault. OpenRouter selections can
        use a different model for each workload.
      </p>

      <SectionHeader>OpenRouter API key</SectionHeader>
      <div style={rowStyle}>
        <span style={labelStyle}>
          status
          <div style={hintStyle}>{settings.openrouter.settingsEnvPath}</div>
        </span>
        <span
          style={{
            color: settings.openrouter.keyPresent
              ? COLOR.green
              : COLOR.textDim,
            fontSize: 11
          }}
        >
          {settings.openrouter.keyPresent
            ? `saved${
                settings.openrouter.keyHint
                  ? ` · ends in ····${settings.openrouter.keyHint}`
                  : ""
              }`
            : "not set"}
        </span>
      </div>
      <div style={{ ...rowStyle, borderBottom: "none" }}>
        <span style={labelStyle}>set key</span>
        <input
          type="password"
          aria-label="OpenRouter API key"
          autoComplete="off"
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
          {busy === "api-key" ? "…" : "save"}
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
    </div>
  );
}
