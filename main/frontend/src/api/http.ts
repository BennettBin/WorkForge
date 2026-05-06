const BASE_URL = "http://127.0.0.1:8080";

export function getBaseUrl(): string {
  return BASE_URL;
}

function authHeader() {
  const token = localStorage.getItem("wf_token");
  const headers: Record<string, string> = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  return response.json() as Promise<T>;
}

export async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: { "Content-Type": "application/json", ...authHeader() }
  });
  return parseResponse<T>(response);
}

export async function postJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(body)
  });
  return parseResponse<T>(response);
}

export async function putJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(body)
  });
  return parseResponse<T>(response);
}

export async function postFile<T>(url: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("upload", file);
  const response = await fetch(`${BASE_URL}${url}`, {
    method: "POST",
    headers: { ...authHeader() },
    body: form
  });
  return parseResponse<T>(response);
}
