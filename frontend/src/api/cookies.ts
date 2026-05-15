import { apiGet, apiPost, apiDelete } from "./client";

export interface CookieProfile {
  id: number;
  site: string;
  source_type: "file_upload" | "paste";
  created_at: string;
  updated_at: string;
}

export interface CreateCookieInput {
  site: string;
  source_type: "file_upload" | "paste";
  cookie_content: string;
}

export function getCookies(): Promise<CookieProfile[]> {
  return apiGet<CookieProfile[]>("/api/cookies");
}

export function createCookie(input: CreateCookieInput): Promise<CookieProfile> {
  return apiPost<CookieProfile>("/api/cookies", input);
}

export function deleteCookie(id: number): Promise<void> {
  return apiDelete(`/api/cookies/${id}`);
}
