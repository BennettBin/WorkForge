const BASE_URL = "http://127.0.0.1:8080";

export function getBaseUrl(): string {
  return BASE_URL;
}

export function getWsBaseUrl(): string {
  if (BASE_URL.startsWith("https://")) {
    return `wss://${BASE_URL.slice("https://".length)}`;
  }
  if (BASE_URL.startsWith("http://")) {
    return `ws://${BASE_URL.slice("http://".length)}`;
  }
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
    const lowered = text.toLowerCase();
    const sessionInvalid =
      response.status === 401 ||
      lowered.includes("session not found") ||
      lowered.includes("session expired") ||
      lowered.includes("missing token");
    if (sessionInvalid) {
      localStorage.removeItem("wf_token");
      localStorage.removeItem("wf_user_id");
      localStorage.removeItem("wf_username");
      localStorage.removeItem("wf_email");
      if (typeof window !== "undefined" && window.location.pathname !== "/Login") {
        window.location.href = "/Login";
      }
    }
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

export async function downloadFile(url: string, filename?: string): Promise<void> {
  const response = await fetch(`${BASE_URL}${url}`, {
    method: "GET",
    headers: { ...authHeader() },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  const blob = await response.blob();
  const objectUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename || "download";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(objectUrl);
}
