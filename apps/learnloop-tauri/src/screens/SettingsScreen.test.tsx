import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { SettingsDto } from "../api/dto";
import { clear } from "../api/queryCache";
import { SettingsScreen } from "./SettingsScreen";

const { api } = vi.hoisted(() => ({ api: { getSettings: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));

function settings(enabled: boolean): SettingsDto {
  const key = { keyPresent: false, keyHint: null };
  const bounds = { min: 1, max: 100000 };
  return {
    version: 1,
    ai: {
      activeProvider: "codex", fallbackProvider: null, routing: {}, useCases: [],
      envProviderOverride: null,
      providers: [
        ["codex", "codex"], ["openrouter", "openrouter"],
        ["openrouter_embedding", "openai_embedding"], ["custom_vectors", "openai_embedding"],
        ["openrouter_decider", "decider"], ["perplexity_direct", "decider"]
      ].map(([name, type]) => ({
        name, type, model: "test-model", baseUrl: null, apiKeyEnv: null, inputModalities: []
      }))
    },
    openrouter: { ...key, settingsEnvPath: "/test/settings.env" },
    embedding: {
      enabled, backfillEnabled: !enabled, model: "qwen/qwen3-embedding-8b", dimensions: 4096,
      privacyDisclosure: "When enabled, remote embeddings send learner-derived text to OpenRouter "
        + "and its upstream provider with data_collection=deny. Vectors approximate "
        + "plaintext: protect them like practice attempts in backups, exports and sync; "
        + "never share them across vaults."
    },
    judges: [
      {
        route: "llm_probability_decider", judge: "decider", consumer: "llm_probability",
        provider: "openrouter_decider", providerType: "decider", model: "perplexity/pplx-decider-v1.1-27b",
        ready: true, disclosure: "Learner text goes to OpenRouter, which forwards it to Perplexity."
      },
      {
        route: "router_llm", judge: "llm", consumer: "router", provider: "codex", providerType: "codex_sdk",
        model: "gpt-5.6-sol", ready: false, disclosure: "Nothing is sent yet: the router has no live consumer."
      }
    ],
    ingest: {
      pdfEngine: "auto", audioMode: "transcription",
      native: {
        modalities: [], fallbackWhenUnavailable: true, maxPdfMb: 10, maxAudioMb: 10,
        knownModalities: [], catalog: { cached: false, fetchedAt: null, stale: false, path: "" }
      },
      transcriptionProvider: "openai_compatible", transcriptionModel: "whisper-1",
      transcriptionBaseUrl: "", transcriptionKey: key,
      budgets: {
        inventoryInputTokens: 1000, inventoryOutputTokens: 1000, synthesisShardInputTokens: 1000,
        synthesisShardOutputTokens: 1000, synthesisTotalInputCeiling: 1000
      },
      budgetBounds: {
        inventoryInputTokens: bounds, inventoryOutputTokens: bounds, synthesisShardInputTokens: bounds,
        synthesisShardOutputTokens: bounds, synthesisTotalInputCeiling: bounds
      },
      providerLimits: { provider: "codex", contextTokens: null, maxOutputTokens: null }
    },
    animation: {
      enabled: false, renderer: "manim", rendererOptions: ["manim", "video_model"],
      video: { ready: false, provider: null, model: null, reason: null, maxShots: 1, timeoutSeconds: 60, resolution: "720p" },
      quality: "low", qualityOptions: ["low"], minDurationSeconds: 10, maxDurationSeconds: 60,
      timeoutSeconds: 120, durationBounds: { min: 1, max: 120 }, timeoutBounds: { min: 1, max: 600 }
    }
  };
}

function showSettings(value: SettingsDto) {
  vi.stubGlobal("localStorage", { getItem: vi.fn(() => null), setItem: vi.fn() });
  api.getSettings.mockResolvedValue(value);
  return render(<SettingsScreen
    manualGrading={false} onSelectGradingProvider={vi.fn()} onHealthChanged={vi.fn()}
    onToast={vi.fn()} onError={vi.fn()}
  />);
}

afterEach(() => { cleanup(); clear(); vi.unstubAllGlobals(); });

it.each([false, true])("discloses embedding privacy and configuration read-only when enabled=%s", async (enabled) => {
  const value = settings(enabled);
  showSettings(value);
  const section = await screen.findByRole("region", { name: "Embeddings" });
  const content = within(section);
  expect(content.getByText("status").parentElement?.textContent).toBe(`status${enabled ? "enabled" : "disabled"}`);
  expect(content.getByText("backfill").parentElement?.textContent).toBe(`backfill${enabled ? "disabled" : "enabled"}`);
  expect(content.getByText(value.embedding.model)).toBeTruthy();
  expect(content.getByText("4096")).toBeTruthy();
  expect(content.getByText(value.embedding.privacyDisclosure)).toBeTruthy();
  expect(section.querySelector("input, select, button, [role=checkbox], [role=combobox]")).toBeNull();
  expect(api.getSettings).toHaveBeenCalledOnce();
});

it("excludes embedding profiles by type from every generation provider selector", async () => {
  showSettings(settings(false));
  await screen.findByRole("region", { name: "Embeddings" });
  const selectors = screen.getAllByRole("combobox").slice(0, 4);
  expect(selectors).toHaveLength(4);
  for (const selector of selectors) {
    fireEvent.click(selector);
    const options = screen.getAllByRole("option").map((option) => option.textContent);
    expect(options).toContain("codex");
    expect(options).toContain("openrouter");
    expect(options).not.toContain("openrouter_embedding");
    expect(options).not.toContain("custom_vectors");
    expect(options).not.toContain("openrouter_decider");
    expect(options).not.toContain("perplexity_direct");
    fireEvent.keyDown(selector, { key: "Escape" });
  }
});

it("discloses each judgment route read-only, with honest key status", async () => {
  const value = settings(false);
  showSettings(value);
  const section = await screen.findByRole("region", { name: "Decision models" });
  const content = within(section);
  for (const judge of value.judges ?? []) {
    expect(content.getByText(judge.route)).toBeTruthy();
    expect(content.getByText(judge.disclosure)).toBeTruthy();
  }
  expect(content.getByText("key present")).toBeTruthy();
  expect(content.getByText("not ready")).toBeTruthy();
  expect(section.querySelector("input, select, button, [role=checkbox], [role=combobox]")).toBeNull();
});
