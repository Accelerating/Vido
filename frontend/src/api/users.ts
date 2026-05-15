import { apiGet, apiPost, apiPut, apiDelete } from "./client";

export interface UserProfile {
  id: number;
  username: string;
  is_admin: boolean;
  created_at: string;
}

export interface CreateUserInput {
  username: string;
  password: string;
  is_admin: boolean;
}

export interface UpdateUserInput {
  username?: string;
  password?: string;
  is_admin?: boolean;
}

export function getUsers(): Promise<UserProfile[]> {
  return apiGet<UserProfile[]>("/api/users");
}

export function createUser(input: CreateUserInput): Promise<UserProfile> {
  return apiPost<UserProfile>("/api/users", input);
}

export function updateUser(id: number, input: UpdateUserInput): Promise<UserProfile> {
  return apiPut<UserProfile>(`/api/users/${id}`, input);
}

export function deleteUser(id: number): Promise<void> {
  return apiDelete(`/api/users/${id}`);
}
