// The one sheet before LearnLoop uses AI (docs/specs/ux_learnloop_v1.md §6.6, §8.3, Q4): one OK, to one
// sentence, for every use; "What's sent" names each service; OK first, then connecting; "Not now" leaves what
// needs AI waiting.
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

const SENTENCE =
  "LearnLoop uses AI for questions, replies, feedback and other learning help. It can send your books, files you choose, your questions and your answers to the services you connect.";
const DECIDER =
  "With an OpenRouter key, LearnLoop also asks Perplexity, through OpenRouter, short questions about your answers and questions (whether a mix-up or a gap is one it already knows) and about the book passages behind a reworded skill.";
const SENT = [
  "To ChatGPT: passages of your books and of files you add, your questions to the tutor, and your answers, to write questions, reply and give feedback.",
  DECIDER,
  "Sending a whole file (a recording to transcribe, a scan to read) asks once more, for that file.",
  "You say OK once, and it covers every use. Your library stays on this computer."
];

const BASE: AiConnectionDto = {
  canAuthor: false,
  provider: "codex_medium",
  providerLabel: "ChatGPT",
  consentKey: "codex",
  consented: false,
  consentedAt: null,
  needs: "connect",
  message: null,
  title: "Before LearnLoop uses AI",
  whatLeaves: SENTENCE,
  whatsSent: SENT,
  deciderNote: DECIDER,
  chatgptSignedIn: false,
  openrouterKeyPresent: false
};
/** The OK given, no AI connected yet: the sheet goes on to connecting. */
const OK_GIVEN: AiConnectionDto = { ...BASE, consented: true, consentedAt: "2026-11-21T09:00:00+00:00" };
const CONNECTED: AiConnectionDto = { ...OK_GIVEN, canAuthor: true, needs: null, released: ["src_1"] };

function open(onConnected = vi.fn(), onOpenSettings = vi.fn(), onClose = vi.fn()) {
  render(<ConnectAISheet onClose={onClose} onConnected={onConnected} onOpenSettings={onOpenSettings} />);
  return { onConnected, onOpenSettings, onClose };
}

describe("ConnectAISheet", () => {
  // UX Phase 1 re-test (#5): after the one-time OK the sheet stayed open over
  // the Library for the whole build ("Connected … Close") and covered the next
  // card the learner wanted. It closes once the OK lands.
  it("closes itself once the one-time OK lands", async () => {
    api.getAiConnection.mockResolvedValue({ ...BASE, canAuthor: true, needs: "consent" });
    api.connectAi.mockResolvedValue(CONNECTED);
    const { onConnected, onClose } = open();
    await screen.findByText(SENTENCE);
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
    expect(onClose).toHaveBeenCalledWith(CONNECTED);
    expect(onConnected).toHaveBeenCalledWith(CONNECTED);
  });

  it("stays open when the OK did not land, saying why", async () => {
    api.getAiConnection.mockResolvedValue({ ...BASE, canAuthor: true, needs: "consent" });
    api.connectAi.mockRejectedValue(new Error("the AI's settings could not be saved"));
    const { onClose } = open();
    await screen.findByText(SENTENCE);
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("keeps a sign-in's confirmation on screen", async () => {
    api.getAiConnection.mockResolvedValue({ ...OK_GIVEN, chatgptSignedIn: true });
    api.connectAi.mockResolvedValue(CONNECTED);
    const { onClose } = open();
    fireEvent.click(await screen.findByRole("button", { name: "Continue with ChatGPT" }));
    expect(await screen.findByText("Connected to ChatGPT. Questions are on.")).toBeTruthy();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("asks once, in one sentence, for every use, with one primary action", async () => {
    api.getAiConnection.mockResolvedValue({ ...BASE, canAuthor: true, needs: "consent" });
    api.connectAi.mockResolvedValue(CONNECTED);
    const { onConnected } = open();
    expect(await screen.findByText(SENTENCE)).toBeTruthy();
    expect(screen.getByRole("dialog", { name: "Before LearnLoop uses AI" })).toBeTruthy();
    expect(screen.getAllByRole("button")[0].textContent).toBe("OK");
    // Connecting is offered only once the OK is given.
    expect(screen.queryByRole("button", { name: "Continue with ChatGPT" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    await waitFor(() => expect(api.connectAi).toHaveBeenCalledWith({ provider: "current" }));
    expect(onConnected).toHaveBeenCalledWith(CONNECTED);
  });

  // Tier 1 (the Decider landing): an OpenRouter key also lets the Decider's
  // small judgments reach Perplexity; "What's sent" says so, as Settings does.
  it("lists each service and what goes to it under What's sent, folded until asked", async () => {
    api.getAiConnection.mockResolvedValue(BASE);
    open();
    const details = await screen.findByRole("button", { name: /What's sent/ });
    expect(details.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByText(DECIDER)).toBeNull();
    fireEvent.click(details);
    const list = screen.getByRole("list", { name: "What's sent" });
    expect([...list.querySelectorAll("li")].map((item) => item.textContent)).toEqual(SENT);
    // The per-book opt-out the old sentence pointed to is retired (owner, 2026-10-13).
    expect(screen.queryByText(/never to send a book|private from its details/i)).toBeNull();
  });

  it("says nothing about the Decider when none of its routes is on", async () => {
    api.getAiConnection.mockResolvedValue({ ...BASE, deciderNote: null, whatsSent: SENT.filter((line) => line !== DECIDER) });
    open();
    fireEvent.click(await screen.findByRole("button", { name: /What's sent/ }));
    expect(screen.getByRole("list", { name: "What's sent" }).textContent).not.toContain("Perplexity");
  });

  it("asks for the OK first when nothing is connected, then offers connecting", async () => {
    api.getAiConnection.mockResolvedValue(BASE);
    api.connectAi.mockResolvedValue(OK_GIVEN);
    const { onClose } = open();
    fireEvent.click(await screen.findByRole("button", { name: "OK" }));
    await waitFor(() => expect(api.connectAi).toHaveBeenCalledWith({ provider: "current" }));
    const next = await screen.findByRole("button", { name: "Continue with ChatGPT" });
    expect(screen.getAllByRole("button")[0]).toBe(next);
    expect(screen.queryByRole("button", { name: "OK" })).toBeNull();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("Not now leaves it waiting: it closes with what it read, and reading needs no OK", async () => {
    api.getAiConnection.mockResolvedValue({ ...BASE, canAuthor: true, needs: "consent" });
    const { onClose } = open();
    expect(await screen.findByText("Reading works without it. Anything that needs AI waits for your OK.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Not now" }));
    expect(onClose).toHaveBeenCalledWith({ ...BASE, canAuthor: true, needs: "consent" });
    expect(api.connectAi).not.toHaveBeenCalled();
  });

  it("puts Continue with ChatGPT first and connects straight away when signed in", async () => {
    api.getAiConnection.mockResolvedValue({ ...OK_GIVEN, chatgptSignedIn: true });
    api.connectAi.mockResolvedValue(CONNECTED);
    const { onConnected } = open();
    await screen.findByRole("button", { name: "Continue with ChatGPT" });
    expect(screen.getAllByRole("button")[0].textContent).toBe("Continue with ChatGPT");
    fireEvent.click(screen.getByRole("button", { name: "Continue with ChatGPT" }));
    await waitFor(() => expect(api.connectAi).toHaveBeenCalledWith({ provider: "chatgpt" }));
    expect(onConnected).toHaveBeenCalledWith(CONNECTED);
  });

  it("signs in through the browser first when needed", async () => {
    api.getAiConnection.mockResolvedValue(OK_GIVEN);
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
    api.getAiConnection.mockResolvedValue(OK_GIVEN);
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
    api.getAiConnection.mockResolvedValue(OK_GIVEN);
    const { onOpenSettings } = open();
    fireEvent.click(await screen.findByRole("button", { name: "Other (advanced) ▸" }));
    expect(onOpenSettings).toHaveBeenCalled();
  });

  it("says a refusal in one plain line", async () => {
    api.getAiConnection.mockResolvedValue({ ...OK_GIVEN, chatgptSignedIn: true });
    api.connectAi.mockRejectedValue({ code: "chatgpt_models_unavailable", message: "Couldn't reach ChatGPT to finish connecting. Try again.", retryable: true });
    open();
    fireEvent.click(await screen.findByRole("button", { name: "Continue with ChatGPT" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toContain("Couldn't reach ChatGPT to finish connecting");
  });
});
