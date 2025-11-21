import type { ChatSummary, Chat, TelegramMessage } from './types';

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

export function listChats(): Promise<ChatSummary[]> {
  return jsonFetch<ChatSummary[]>(`${API_BASE}/api/chats`);
}

export function createChat(body: {
  client_phone: string;
  client_name: string;
  client_details: string;
}): Promise<{ id: string; chat: Chat }> {
  return jsonFetch<{ id: string; chat: Chat }>(`${API_BASE}/api/chats`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function getChat(chatId: string): Promise<{ id: string; chat: Chat }> {
  return jsonFetch<{ id: string; chat: Chat }>(`${API_BASE}/api/chats/${encodeURIComponent(chatId)}`);
}

export function sendTelegram(chatId: string, text: string): Promise<{ success: boolean }> {
  return jsonFetch<{ success: boolean }>(`${API_BASE}/api/telegram/send`, {
    method: 'POST',
    body: JSON.stringify({ chat_id: chatId, text }),
  });
}

export function pollTelegram(chatId: string): Promise<{ messages: TelegramMessage[] }> {
  const url = `${API_BASE}/api/telegram/messages?chat_id=${encodeURIComponent(chatId)}`;
  return jsonFetch<{ messages: TelegramMessage[] }>(url);
}

export function sendGemini(chatId: string, text: string): Promise<{ reply: string; chat: Chat }> {
  return jsonFetch<{ reply: string; chat: Chat }>(`${API_BASE}/api/gemini/send`, {
    method: 'POST',
    body: JSON.stringify({ chat_id: chatId, text }),
  });
}
