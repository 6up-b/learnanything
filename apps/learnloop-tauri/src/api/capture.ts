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
  receivedAt: string;
}

export interface InboxSummary {
  count: number;
  newCount: number;
  captures: CaptureDto[];
  pinnedVault: string | null;
  vaultMismatch: boolean;
  enabled: boolean;
}
