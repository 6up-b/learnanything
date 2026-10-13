import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ChatGPTPlanDto } from "../api/dto";
import { ChatGPTPlanSettings } from "./ChatGPTPlanSettings";

const { api, openUrl } = vi.hoisted(() => ({
  api: {
    chatgptPlanStatus: vi.fn(),
    chatgptPlanSigninStart: vi.fn(),
    chatgptPlanSigninCancel: vi.fn(),
    chatgptPlanSignout: vi.fn(),
    chatgptPlanAcknowledgeWelcome: vi.fn(),
    chatgptPlanResume: vi.fn()
  },
  openUrl: vi.fn()
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/plugin-opener", () => ({ openUrl }));

const styles = {
  row: {},
  label: {},
  hint: {},
  button: () => ({})
};

function plan(overrides: Partial<ChatGPTPlanDto> = {}): ChatGPTPlanDto {
  return {
    signedIn: false,
    planUsageEnabled: false,
    email: null,
    clientId: null,
    secretStore: null,
    accessExpiresAt: null,
    pausedUntil: null,
    welcomePending: false,
    signedOutReason: null,
    state: "signed_out",
    message: "Not signed in with ChatGPT on this machine.",
    manageUsageUrl: "https://chatgpt.com/settings/usage",
    attempt: null,
    profiles: [],
    usingPlan: false,
    ...overrides
  };
}

const ready = plan({
  signedIn: true, planUsageEnabled: true, email: "learner@example.com", secretStore: "file", state: "ready",
  usingPlan: true,
  profiles: [{
    name: "chatgpt", model: "gpt-test-fast", enabled: true, responseFormat: "json_schema", reasoningEffort: "low",
    usageLimitPauseMinutes: 15, routes: ["source_query_rewrite", "source_rerank"], activeProvider: false,
    fallbackProvider: false, inUse: true
  }]
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function show(value: ChatGPTPlanDto, onToast = vi.fn(), onError = vi.fn()) {
  render(<ChatGPTPlanSettings plan={value} styles={styles} onToast={onToast} onError={onError} />);
  return { onToast, onError };
}

it("continues with ChatGPT in the system browser and reports the result", async () => {
  api.chatgptPlanSigninStart.mockResolvedValue(plan({
    authorizeUrl: "https://auth.openai.com/api/accounts/authorize?client_id=dynamic_agent_client",
    attempt: { id: "a", status: "waiting", result: null, error: null, startedAt: 1, finishedAt: null }
  }));
  api.chatgptPlanStatus.mockResolvedValue({
    ...ready,
    welcomePending: true,
    attempt: { id: "a", status: "succeeded", result: null, error: null, startedAt: 1, finishedAt: 2 }
  });
  const { onToast } = show(plan());
  fireEvent.click(screen.getByRole("button", { name: "Continue with ChatGPT" }));
  await waitFor(() => expect(openUrl).toHaveBeenCalledWith(
    "https://auth.openai.com/api/accounts/authorize?client_id=dynamic_agent_client"
  ));
  expect(api.chatgptPlanSigninStart).toHaveBeenCalledWith({ consent: false });
  await waitFor(() => expect(onToast).toHaveBeenCalledWith("signed in with ChatGPT as learner@example.com"), {
    timeout: 3000
  });
  // The one-time confirmation follows the first sign-in.
  expect(screen.getByRole("dialog", { name: "You're using your ChatGPT plan" })).toBeTruthy();
});

it("asks for consent again when plan usage was not granted", async () => {
  api.chatgptPlanSigninStart.mockResolvedValue(plan({ authorizeUrl: "https://auth.example/consent" }));
  api.chatgptPlanStatus.mockResolvedValue(plan({ state: "plan_usage_disabled", signedIn: true }));
  show(plan({ state: "plan_usage_disabled", signedIn: true, email: "learner@example.com" }));
  expect(screen.getByText(/plan usage not granted/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Continue with ChatGPT" }));
  await waitFor(() => expect(api.chatgptPlanSigninStart).toHaveBeenCalledWith({ consent: true }));
});

it("shows Using ChatGPT plan with Manage usage, the routes, and the confirmation once", async () => {
  api.chatgptPlanAcknowledgeWelcome.mockResolvedValue({ ...ready, welcomePending: false });
  show({ ...ready, welcomePending: true });
  expect(screen.getByText("Using ChatGPT plan")).toBeTruthy();
  expect(screen.getByText(/source_query_rewrite, source_rerank/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Manage usage" }));
  await waitFor(() => expect(openUrl).toHaveBeenCalledWith("https://chatgpt.com/settings/usage"));
  fireEvent.click(screen.getByRole("button", { name: "Got it" }));
  await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  expect(api.chatgptPlanAcknowledgeWelcome).toHaveBeenCalled();
});

it("puts Manage usage first when a usage limit is reached", async () => {
  api.chatgptPlanResume.mockResolvedValue(ready);
  show({ ...ready, state: "usage_exhausted", pausedUntil: "2026-10-12T18:00:00+00:00" });
  const alert = screen.getByRole("alert");
  const buttons = alert.querySelectorAll("button");
  expect(buttons[0].textContent).toBe("Manage usage");
  expect(screen.getByText(/paused until 2026-10-12T18:00:00\+00:00/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "try again now" }));
  await waitFor(() => expect(api.chatgptPlanResume).toHaveBeenCalled());
  await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
});

it("signs out and says whether revocation was confirmed", async () => {
  api.chatgptPlanSignout.mockResolvedValue(plan({
    signout: { signedOut: true, revoked: true, message: "Signed out." }
  }));
  const { onToast } = show(ready);
  fireEvent.click(screen.getByRole("button", { name: "sign out" }));
  await waitFor(() => expect(onToast).toHaveBeenCalledWith("Signed out."));
  expect(screen.getByRole("button", { name: "Continue with ChatGPT" })).toBeTruthy();
});
