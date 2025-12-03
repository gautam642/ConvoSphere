import type { Session, CreateSessionRequest, SendMessageRequest, GeminiAnalysis } from './types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function listSessions(): Promise<Session[]> {
  return jsonFetch<Session[]>(`${API_BASE}/api/sessions`);
}

export function createSession(body: CreateSessionRequest): Promise<Session> {
  return jsonFetch<Session>(`${API_BASE}/api/sessions`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function getSession(sessionId: string): Promise<Session> {
  return jsonFetch<Session>(`${API_BASE}/api/sessions/${encodeURIComponent(sessionId)}`);
}

export function sendMessage(sessionId: string, text: string): Promise<Session> {
  const body: SendMessageRequest = { text };
  return jsonFetch<Session>(`${API_BASE}/api/sessions/${encodeURIComponent(sessionId)}/send`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function triggerGemini(sessionId: string, text: string): Promise<GeminiAnalysis> {
    const body = { text: text }; // The API expects a SendMessageRequest which only has a 'text' field.
    return jsonFetch<GeminiAnalysis>(`${API_BASE}/api/sessions/${encodeURIComponent(sessionId)}/trigger_gemini`, {
        method: 'POST',
        body: JSON.stringify(body),
    });
}
