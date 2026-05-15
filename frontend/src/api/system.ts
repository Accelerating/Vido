import { apiGet, apiPost } from "./client";

export interface YtdlpVersion {
  version: string;
  error: string | null;
}

export interface YtdlpUpdate {
  ok: boolean;
  version?: string;
  error?: string;
}

export function getYtdlpVersion(): Promise<YtdlpVersion> {
  return apiGet<YtdlpVersion>("/api/system/ytdlp-version");
}

export function updateYtdlp(): Promise<YtdlpUpdate> {
  return apiPost<YtdlpUpdate>("/api/system/ytdlp-update");
}
