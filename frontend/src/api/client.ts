const BASE = "";

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const resp = await fetch(`${BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  return resp;
}

export async function apiGet<T = unknown>(path: string): Promise<T> {
  const resp = await apiFetch(path);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `Error ${resp.status}`);
  }
  return resp.json();
}

export async function apiPost<T = unknown>(path: string, body?: unknown): Promise<T> {
  const resp = await apiFetch(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `Error ${resp.status}`);
  }
  return resp.json();
}

export async function apiPut<T = unknown>(path: string, body?: unknown): Promise<T> {
  const resp = await apiFetch(path, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `Error ${resp.status}`);
  }
  return resp.json();
}

export async function apiDelete(path: string): Promise<void> {
  const resp = await apiFetch(path, { method: "DELETE" });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `Error ${resp.status}`);
  }
}
