export interface CaptureDto {
  captureId: string;
  kind: "text" | "url" | "image";
  text: string | null;
  url: string | null;
  note: string | null;
  mediaSha256: string | null;
  mediaMime: string | null;
  mediaDeletePending: boolean;
  mediaRetainedShared: boolean;
  status: "new" | "routed" | "dismissed" | "purged";
  /** A desktop save that began but did not record its route (e.g. a crash). */
  pendingRoute: "make_card" | "quick_add" | "ask_tutor" | null;
  receivedAt: string;
}

export interface InboxSummary {
  count: number;
  newCount: number;
  captures: CaptureDto[];
  /** Purged captures whose original media deletion failed; never paged away. */
  deletePending: CaptureDto[];
  deletePendingCount: number;
  pinnedVault: string | null;
  vaultMismatch: boolean;
  enabled: boolean;
}
