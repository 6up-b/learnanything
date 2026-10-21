# Security stage: Codex tool lockdown (2026-10-21)

Branch `security/codex-tool-lockdown` from main `c80c54cbb` (migration head 217).
Source finding: `fixtures-local/codex-isolation-tool-surface.md` (read-only investigation, 2026-10-21).

## Plan (written before the code)

1. **One turn path, always locked down.** `SdkCodexClient._run_structured` is the only place LearnLoop
   starts a Codex SDK turn (`thread_start` has exactly one call site in `src/`). Every turn it starts runs
   the locked-down profile: never the vault as cwd (a fresh empty temp dir, or the diagnosis snapshot
   workspace), the `learnloop_isolated_turn` permission profile (read the turn dir + platform minimum, write
   nowhere, network off), every tool-bearing feature off, no MCP servers, no apps/connectors, no web search,
   `agents.enabled=false`, `features.multi_agent(_v2)=false`, `tools.experimental_request_user_input.enabled=false`,
   `tools.update_plan.enabled=false`. Enforcing it in the transport routes `PaidCalls.call`, `tutor_qa` and every
   other caller (and RW5a's `figure_author`) through it without touching call sites, and leaves non-Codex
   transports unchanged.
2. **Approvals.** `thread_start` and `turn` get `approval_mode=ApprovalMode.deny_all`; the SDK client's
   approval handler is replaced by one that declines every server request (command, file change,
   permissions, user input, MCP elicitation, dynamic tool call) and records it. Missing `ApprovalMode`, a
   `thread_start`/`turn` that cannot take it, or an SDK client whose handler cannot be replaced refuses the
   turn.
3. **Launch self-check, cached.** Extend `_verified_isolated_overrides`: every feature `features list` shows on
   must be on a reviewed permitted list (0.163.0's non-tool features); any other feature on is switched off
   and must then read off; `debug models --bundled` (local, no model call) must advertise for the turn's model
   only tool metadata LearnLoop removes or neutralizes. Fail closed with a typed error. Cache successes per
   process and config fingerprint (CLI argv, binary, Codex config files, project-config ancestors, sandbox, env).
4. **Answer refusal.** A turn whose items contain anything but user/assistant text and reasoning (any
   command, patch, MCP, web, sub-agent, image, user-input or unknown item) is a failed call; the diagnosis
   workspace turn may additionally run commands (its shell reads the snapshot) and nothing else.
5. **Inner requests.** Tap the SDK's notification router: count model requests per thread, sub-agent threads,
   Guardian reviews, tool items and server requests; fold child-thread tokens into the receipt and the
   admission settle; cap tool rounds of a locked-down turn at 0 (interrupt the turn at the first tool item or
   second model request and refuse it).
6. **Fix 5 (LearnLoop-owned model catalog):** decide after checking what config can remove; record which.
7. Tests fail-first on `c80c54cbb`; at most 6 synthetic live checks in empty temp dirs.
