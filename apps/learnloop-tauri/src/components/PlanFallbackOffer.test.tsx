// Plan-first transport T1: the shell asks before OpenRouter does anything.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import {
  clearFallbackOffer,
  currentFallbackOffer,
  extractFallbackOffer,
  noteFallbackOffer,
  resetDeclinedFallbackOrigins
} from "../app/planFallback";
import { PlanFallbackOffer } from "./PlanFallbackOffer";

const { api } = vi.hoisted(() => ({ api: { aiUseFallback: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  clearFallbackOffer();
  resetDeclinedFallbackOrigins();
  vi.clearAllMocks();
});

const errorWithHint = {
  code: "ai_unavailable",
  message: "Not signed in with ChatGPT.",
  details: {
    fallback_available: "openrouter", fallback_tasks: ["tutor_qa"], fallback_profile: "openrouter", plan_signed_out: true,
    fallback_offer_id: "fo_1", fallback_origin: "ask_tutor_question"
  }
};

it("reads the typed hint from an error's details or a result, and nothing else", () => {
  expect(extractFallbackOffer(errorWithHint)).toEqual({
    provider: "openrouter", profile: "openrouter", tasks: ["tutor_qa"], planSignedOut: true,
    offerId: "fo_1", origin: "ask_tutor_question"
  });
  expect(extractFallbackOffer({ fallbackAvailable: "openrouter", fallbackTasks: ["grading"], fallbackProfile: "openrouter" }))
    .toMatchObject({ tasks: ["grading"], planSignedOut: false });
  expect(extractFallbackOffer({ code: "ai_unavailable", details: {} })).toBeNull();
  expect(extractFallbackOffer({ fallbackAvailable: "codex", fallbackTasks: ["grading"] })).toBeNull();
  expect(extractFallbackOffer({ fallbackAvailable: "openrouter", fallbackTasks: [] })).toBeNull();
  expect(extractFallbackOffer(null)).toBeNull();
});

it("answers only the feature that asked last: a newer offer replaces the shown one (review F4)", () => {
  noteFallbackOffer(errorWithHint);
  noteFallbackOffer({ fallbackAvailable: "openrouter", fallbackTasks: ["grading"], fallbackProfile: "openrouter" });
  expect(currentFallbackOffer()).toMatchObject({ tasks: ["grading"], planSignedOut: false });
});

it("takes the grant back with Stop using OpenRouter (review F8)", async () => {
  api.aiUseFallback.mockResolvedValue({ version: 1, provider: "openrouter", profile: "openrouter", grantedTasks: ["tutor_qa"], scope: "session" });
  render(<PlanFallbackOffer onContinueWithChatGPT={vi.fn()} />);
  act(() => noteFallbackOffer(errorWithHint));
  fireEvent.click(screen.getByRole("button", { name: "Use OpenRouter instead" }));
  await screen.findByText(/OpenRouter will do this for the rest of this session/);
  api.aiUseFallback.mockResolvedValue({ version: 1, provider: "openrouter", profile: "openrouter", grantedTasks: [], scope: "session" });
  fireEvent.click(screen.getByRole("button", { name: "Stop using OpenRouter" }));
  await waitFor(() =>
    expect(api.aiUseFallback).toHaveBeenLastCalledWith({ provider: "openrouter", stop: true })
  );
  await waitFor(() => expect(currentFallbackOffer()).toBeNull());
});

it("shows nothing without an offer", () => {
  render(<PlanFallbackOffer onContinueWithChatGPT={vi.fn()} />);
  expect(screen.queryByRole("status", { name: "ChatGPT unavailable" })).toBeNull();
});

it("sends nothing until the learner chooses OpenRouter, then answers exactly that offer (redesign D)", async () => {
  api.aiUseFallback.mockResolvedValue({ version: 1, provider: "openrouter", profile: "openrouter", grantedTasks: ["tutor_qa"], scope: "session" });
  render(<PlanFallbackOffer onContinueWithChatGPT={vi.fn()} />);
  act(() => noteFallbackOffer(errorWithHint));
  expect(screen.getByText("ChatGPT isn't available right now.")).toBeTruthy();
  expect(api.aiUseFallback).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Use OpenRouter instead" }));
  await waitFor(() => expect(api.aiUseFallback).toHaveBeenCalledWith({ provider: "openrouter", offerId: "fo_1" }));
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

const otherAction = {
  code: "ai_unavailable",
  message: "Not signed in with ChatGPT.",
  details: {
    fallback_available: "openrouter", fallback_tasks: ["hint_writer"], fallback_profile: "openrouter",
    plan_signed_out: false, fallback_offer_id: "fo_2", fallback_origin: "practice.request_hint"
  }
};

it("Not now mutes that action's question for the session; another action still asks (Q2)", () => {
  render(<PlanFallbackOffer onContinueWithChatGPT={vi.fn()} />);
  act(() => noteFallbackOffer(errorWithHint));
  fireEvent.click(screen.getByRole("button", { name: "Not now" }));
  expect(currentFallbackOffer()).toBeNull();
  act(() => noteFallbackOffer({ ...errorWithHint, details: { ...errorWithHint.details, fallback_offer_id: "fo_3" } }));
  expect(currentFallbackOffer()).toBeNull();
  expect(screen.queryByRole("status", { name: "ChatGPT unavailable" })).toBeNull();
  act(() => noteFallbackOffer(otherAction));
  expect(currentFallbackOffer()).toMatchObject({ offerId: "fo_2", origin: "practice.request_hint" });
  expect(screen.getByText("ChatGPT isn't available right now.")).toBeTruthy();
  expect(api.aiUseFallback).not.toHaveBeenCalled();
});

it("a stale offer says Try it again and grants nothing", async () => {
  api.aiUseFallback.mockRejectedValue({ code: "not_offered", message: "That choice is no longer open. Try it again.", retryable: false });
  render(<PlanFallbackOffer onContinueWithChatGPT={vi.fn()} />);
  act(() => noteFallbackOffer(otherAction));
  fireEvent.click(screen.getByRole("button", { name: "Use OpenRouter instead" }));
  await waitFor(() => expect(api.aiUseFallback).toHaveBeenCalledWith({ provider: "openrouter", offerId: "fo_2" }));
  expect(await screen.findByRole("alert")).toHaveProperty("textContent", "That choice is no longer open. Try it again.");
  expect(screen.queryByText(/OpenRouter will do this for the rest of this session/)).toBeNull();
});
