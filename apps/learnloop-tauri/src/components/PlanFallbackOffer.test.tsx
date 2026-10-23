// Plan-first transport T1: the shell asks before OpenRouter does anything.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { clearFallbackOffer, currentFallbackOffer, extractFallbackOffer, noteFallbackOffer } from "../app/planFallback";
import { PlanFallbackOffer } from "./PlanFallbackOffer";

const { api } = vi.hoisted(() => ({ api: { aiUseFallback: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  clearFallbackOffer();
  vi.clearAllMocks();
});

const errorWithHint = {
  code: "ai_unavailable",
  message: "Not signed in with ChatGPT.",
  details: { fallback_available: "openrouter", fallback_tasks: ["tutor_qa"], fallback_profile: "openrouter", plan_signed_out: true }
};

it("reads the typed hint from an error's details or a result, and nothing else", () => {
  expect(extractFallbackOffer(errorWithHint)).toEqual({
    provider: "openrouter", profile: "openrouter", tasks: ["tutor_qa"], planSignedOut: true
  });
  expect(extractFallbackOffer({ fallbackAvailable: "openrouter", fallbackTasks: ["grading"], fallbackProfile: "openrouter" }))
    .toMatchObject({ tasks: ["grading"], planSignedOut: false });
  expect(extractFallbackOffer({ code: "ai_unavailable", details: {} })).toBeNull();
  expect(extractFallbackOffer({ fallbackAvailable: "codex", fallbackTasks: ["grading"] })).toBeNull();
  expect(extractFallbackOffer({ fallbackAvailable: "openrouter", fallbackTasks: [] })).toBeNull();
  expect(extractFallbackOffer(null)).toBeNull();
});

it("merges the tasks of several features into one offer", () => {
  noteFallbackOffer(errorWithHint);
  noteFallbackOffer({ fallbackAvailable: "openrouter", fallbackTasks: ["grading"], fallbackProfile: "openrouter" });
  expect(currentFallbackOffer()).toMatchObject({ tasks: ["grading", "tutor_qa"], planSignedOut: true });
});

it("shows nothing without an offer", () => {
  render(<PlanFallbackOffer onContinueWithChatGPT={vi.fn()} />);
  expect(screen.queryByRole("status", { name: "ChatGPT unavailable" })).toBeNull();
});

it("sends nothing until the learner chooses OpenRouter, then grants exactly the offered tasks", async () => {
  api.aiUseFallback.mockResolvedValue({ version: 1, provider: "openrouter", profile: "openrouter", grantedTasks: ["tutor_qa"], scope: "session" });
  render(<PlanFallbackOffer onContinueWithChatGPT={vi.fn()} />);
  act(() => noteFallbackOffer(errorWithHint));
  expect(screen.getByText("ChatGPT isn't available right now.")).toBeTruthy();
  expect(api.aiUseFallback).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Use OpenRouter instead" }));
  await waitFor(() => expect(api.aiUseFallback).toHaveBeenCalledWith({ provider: "openrouter", tasks: ["tutor_qa"] }));
  await screen.findByText(/OpenRouter will do this for the rest of this session/);
});

it("offers Continue with ChatGPT only when the plan is signed out, and Not now dismisses", () => {
  const onContinue = vi.fn();
  render(<PlanFallbackOffer onContinueWithChatGPT={onContinue} />);
  act(() => noteFallbackOffer({ fallbackAvailable: "openrouter", fallbackTasks: ["grading"], planSignedOut: false }));
  expect(screen.queryByRole("button", { name: "Continue with ChatGPT" })).toBeNull();
  act(() => clearFallbackOffer());
  act(() => noteFallbackOffer(errorWithHint));
  fireEvent.click(screen.getByRole("button", { name: "Continue with ChatGPT" }));
  expect(onContinue).toHaveBeenCalled();
  expect(currentFallbackOffer()).toBeNull();
  act(() => noteFallbackOffer(errorWithHint));
  fireEvent.click(screen.getByRole("button", { name: "Not now" }));
  expect(screen.queryByRole("status", { name: "ChatGPT unavailable" })).toBeNull();
  expect(api.aiUseFallback).not.toHaveBeenCalled();
});
