// Connect once, consent once (docs/specs/ux_learnloop_v1.md §6.6, §8.3, Q4).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AiConnectionDto } from "../api/dto";
import { ConnectAISheet } from "./ConnectAI";

const { api, openUrl } = vi.hoisted(() => ({
  api: {
    getAiConnection: vi.fn(),
    connectAi: vi.fn(),
    chatgptPlanSigninStart: vi.fn(),
    chatgptPlanStatus: vi.fn(),
    setOpenrouterApiKey: vi.fn()
  },
  openUrl: vi.fn()
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/plugin-opener", () => ({ openUrl }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.useRealTimers();
});

const BASE: AiConnectionDto = {
  canAuthor: false,
  provider: "codex_medium",
  providerLabel: "ChatGPT",
  consentKey: "codex",
  consented: false,
  consentedAt: null,
  needs: "connect",
  message: null,
  whatLeaves: "LearnLoop sends passages of the books you add, and your answers, to ChatGPT to write questions and give feedback.",
  chatgptSignedIn: false,
  openrouterKeyPresent: false
};
const CONNECTED: AiConnectionDto = { ...BASE, canAuthor: true, consented: true, needs: null, released: ["src_1"] };

function open(onConnected = vi.fn(), onOpenSettings = vi.fn()) {
  render(<ConnectAISheet onClose={vi.fn()} onConnected={onConnected} onOpenSettings={onOpenSettings} />);
  return { onConnected, onOpenSettings };
}

describe("ConnectAISheet", () => {
  it("asks once, in one sentence, when an AI is already set up", async () => {
    api.getAiConnection.mockResolvedValue({ ...BASE, canAuthor: true, needs: "consent" });
    api.connectAi.mockResolvedValue(CONNECTED);
    const { onConnected } = open();
    expect(await screen.findByText(BASE.whatLeaves)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    await waitFor(() => expect(api.connectAi).toHaveBeenCalledWith({ provider: "current" }));
    expect(onConnected).toHaveBeenCalledWith(CONNECTED);
  });

  it("puts Continue with ChatGPT first and connects straight away when signed in", async () => {
    api.getAiConnection.mockResolvedValue({ ...BASE, chatgptSignedIn: true });
    api.connectAi.mockResolvedValue(CONNECTED);
    const { onConnected } = open();
    await screen.findByRole("button", { name: "Continue with ChatGPT" });
    expect(screen.getAllByRole("button")[0].textContent).toBe("Continue with ChatGPT");
    expect(screen.getByText(/What leaves this computer/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Continue with ChatGPT" }));
    await waitFor(() => expect(api.connectAi).toHaveBeenCalledWith({ provider: "chatgpt" }));
    expect(onConnected).toHaveBeenCalledWith(CONNECTED);
  });

  it("signs in through the browser first when needed", async () => {
    api.getAiConnection.mockResolvedValue(BASE);
    api.chatgptPlanSigninStart.mockResolvedValue({
      authorizeUrl: "https://auth.openai.com/authorize?x=1",
      attempt: { id: "a", status: "waiting", result: null, error: null, startedAt: 1, finishedAt: null }
    });
    api.chatgptPlanStatus.mockResolvedValue({
      attempt: { id: "a", status: "succeeded", result: null, error: null, startedAt: 1, finishedAt: 2 }
    });
    api.connectAi.mockResolvedValue(CONNECTED);
    const { onConnected } = open();
    fireEvent.click(await screen.findByRole("button", { name: "Continue with ChatGPT" }));
    await waitFor(() => expect(openUrl).toHaveBeenCalledWith("https://auth.openai.com/authorize?x=1"));
    expect(await screen.findByText("Waiting for the browser…")).toBeTruthy();
    await waitFor(() => expect(api.connectAi).toHaveBeenCalledWith({ provider: "chatgpt" }), { timeout: 3000 });
    expect(onConnected).toHaveBeenCalled();
  });

  it("connects an OpenRouter key", async () => {
    api.getAiConnection.mockResolvedValue(BASE);
    api.setOpenrouterApiKey.mockResolvedValue({ keyPresent: true });
    api.connectAi.mockResolvedValue(CONNECTED);
    open();
    fireEvent.click(await screen.findByRole("button", { name: "Use an OpenRouter key" }));
    fireEvent.change(screen.getByLabelText("OpenRouter key"), { target: { value: "sk-or-test" } });
    fireEvent.click(screen.getByRole("button", { name: "Connect" }));
    await waitFor(() => expect(api.connectAi).toHaveBeenCalledWith({ provider: "openrouter" }));
    expect(api.setOpenrouterApiKey).toHaveBeenCalledWith("sk-or-test");
  });

  it("leaves everything else to Settings", async () => {
    api.getAiConnection.mockResolvedValue(BASE);
    const { onOpenSettings } = open();
    fireEvent.click(await screen.findByRole("button", { name: "Other (advanced) ▸" }));
    expect(onOpenSettings).toHaveBeenCalled();
  });

  it("says a refusal in one plain line", async () => {
    api.getAiConnection.mockResolvedValue({ ...BASE, chatgptSignedIn: true });
    api.connectAi.mockRejectedValue({ code: "chatgpt_models_unavailable", message: "Couldn't reach ChatGPT to finish connecting. Try again.", retryable: true });
    open();
    fireEvent.click(await screen.findByRole("button", { name: "Continue with ChatGPT" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toContain("Couldn't reach ChatGPT to finish connecting");
  });
});
