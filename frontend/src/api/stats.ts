import { apiGet } from "./client";

export interface Stats {
  disk_free_bytes: number;
  disk_total_bytes: number;
  tasks_pending: number;
  tasks_downloading: number;
  tasks_completed: number;
  tasks_failed: number;
  videos_count: number;
}

export function getStats(): Promise<Stats> {
  return apiGet<Stats>("/api/stats");
}
