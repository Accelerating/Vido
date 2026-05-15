import { apiGet, apiPost, apiDelete } from "./client";

export interface Task {
  id: number;
  url: string;
  site: string | null;
  quality: string;
  format: string | null;
  format_desc: string | null;
  cookie_profile_id: number | null;
  status: "pending" | "downloading" | "completed" | "failed";
  title: string | null;
  file_path: string | null;
  error_message: string | null;
  log: string | null;
  created_at: string;
  finished_at: string | null;
}

export interface CreateTaskInput {
  url: string;
  quality: string;
  format?: string;
  cookie_profile_id?: number;
}

export function getTasks(status?: string): Promise<Task[]> {
  const qs = status ? `?status=${status}` : "";
  return apiGet<Task[]>(`/api/tasks${qs}`);
}

export function createTask(input: CreateTaskInput): Promise<Task> {
  return apiPost<Task>("/api/tasks", input);
}

export interface FormatInfo {
  code: string;
  ext: string;
  resolution: string;
  fps: string | null;
  file_size: string;
  tbr: string;
  vcodec: string;
  acodec: string;
  note: string;
}

export interface ListFormatsInput {
  url: string;
  cookie_profile_id?: number;
}

export function fetchFormats(input: ListFormatsInput): Promise<FormatInfo[]> {
  return apiPost<FormatInfo[]>("/api/tasks/formats", input);
}

export function deleteTask(id: number): Promise<void> {
  return apiDelete(`/api/tasks/${id}`);
}
