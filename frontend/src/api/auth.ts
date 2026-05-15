import { apiPost, apiGet } from "./client";

export interface User {
  id: number;
  username: string;
  created_at: string;
  is_admin: boolean;
}

export function login(username: string, password: string): Promise<User> {
  return apiPost<User>("/api/auth/login", { username, password });
}

export function register(username: string, password: string): Promise<User> {
  return apiPost<User>("/api/auth/register", { username, password });
}

export function logout(): Promise<void> {
  return apiPost<void>("/api/auth/logout");
}

export function getMe(): Promise<User> {
  return apiGet<User>("/api/auth/me");
}

export function canRegister(): Promise<{ can_register: boolean }> {
  return apiGet<{ can_register: boolean }>("/api/auth/can-register");
}
