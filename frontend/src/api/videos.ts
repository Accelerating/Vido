import { apiGet } from "./client";

export interface Video {
  id: number;
  task_id: number;
  title: string | null;
  file_path: string;
  file_size: number | null;
  duration: number | null;
  has_thumbnail: boolean;
  created_at: string;
}

export function getVideos(): Promise<Video[]> {
  return apiGet<Video[]>("/api/videos");
}

export function getVideoStreamUrl(id: number): string {
  return `/api/videos/${id}/stream`;
}

export function getThumbnailUrl(id: number): string {
  return `/api/videos/${id}/thumbnail`;
}
