// P2 golden-path fixtures — the mock layer (spec_tauri_ui §4/§5, U-031).
//
// Captured VERBATIM from the real sidecar handlers driving the deterministic
// golden_path fixture vault (scripts/gen_goldenpath_fixtures.py). Every P2 screen
// renders offline from these — no live jobs, no AI providers (per-screen render
// acceptance). Regenerate with: uv run python scripts/gen_goldenpath_fixtures.py

import type {
  AssessOpenDto,
  AssessResultDto,
  BlueprintVersionDto,
  BoundaryDiffDto,
  ConfirmReceiptDto,
  DepthInvitationResultDto,
  LadderPolicyDto,
  PoolDto,
  PoolNextSurfaceDto,
  ReaderPromptContractDto,
  RestoreDto,
  RunStateDto,
  TriageResultDto,
} from "../../api/dto";

import confirmReceipt from "./confirmReceipt.json";
import blueprintVersion from "./blueprintVersion.json";
import runStatusReady from "./runStatusReady.json";
import runStatusReadyToAssess from "./runStatusReadyToAssess.json";
import runStatusAssessed from "./runStatusAssessed.json";
import ladderPolicy from "./ladderPolicy.json";
import readerPromptContract from "./readerPromptContract.json";
import poolAssembled from "./poolAssembled.json";
import poolNextSurface from "./poolNextSurface.json";
import assessOpen from "./assessOpen.json";
import assessResult from "./assessResult.json";
import restore from "./restore.json";
import boundaryDiff from "./boundaryDiff.json";
import depthInvitation from "./depthInvitation.json";
import triageDecisive from "./triageDecisive.json";
import triageProvisional from "./triageProvisional.json";

export const goldenPathFixtures = {
  confirmReceipt: confirmReceipt as unknown as ConfirmReceiptDto,
  blueprintVersion: blueprintVersion as unknown as BlueprintVersionDto,
  runStatusReady: runStatusReady as unknown as RunStateDto,
  runStatusReadyToAssess: runStatusReadyToAssess as unknown as RunStateDto,
  runStatusAssessed: runStatusAssessed as unknown as RunStateDto,
  ladderPolicy: ladderPolicy as unknown as LadderPolicyDto,
  readerPromptContract: readerPromptContract as unknown as ReaderPromptContractDto,
  poolAssembled: poolAssembled as unknown as PoolDto,
  poolNextSurface: poolNextSurface as unknown as PoolNextSurfaceDto,
  assessOpen: assessOpen as unknown as AssessOpenDto,
  assessResult: assessResult as unknown as AssessResultDto,
  restore: restore as unknown as RestoreDto,
  boundaryDiff: boundaryDiff as unknown as BoundaryDiffDto,
  depthInvitation: depthInvitation as unknown as DepthInvitationResultDto,
  triageDecisive: triageDecisive as unknown as TriageResultDto,
  triageProvisional: triageProvisional as unknown as TriageResultDto,
};

export type GoldenPathFixtures = typeof goldenPathFixtures;
