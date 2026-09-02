/**
 * Minimal typed fetch wrapper for the backend REST API.
 *
 * URLs are relative by default so the Vite dev proxy (development) and the
 * backend's own static mount (production) both work with no configuration.
 * Set `VITE_API_BASE` only when the API is on a different origin.
 */

import type {
  AudioDevice,
  DocumentInfo,
  SessionSource,
  SessionStatus,
} from "../types/api";

const API_BASE: string = import.meta.env.VITE_API_BASE ?? "";

/** Base URL for the presenter WebSocket, derived from the page origin. */
export function presenterWsUrl(): string {
  const configured = import.meta.env.VITE_WS_BASE;
  if (configured) return `${configured}/ws/presenter`;
  const scheme = window.location.protocol === "https:" ? "wss" : "ws";
  return `${scheme}://${window.location.host}/ws/presenter`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const detail = await response
      .json()
      .then((body) => body.detail as string)
      .catch(() => response.statusText);
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

/** Upload a `.docx` and make it the active document. */
export function uploadDocument(file: File): Promise<DocumentInfo> {
  const form = new FormData();
  form.append("file", file);
  return request<DocumentInfo>("/api/documents", { method: "POST", body: form });
}

/** Start a meeting session with the given audio source. */
export function startSession(
  source: SessionSource,
  path?: string,
): Promise<SessionStatus> {
  return request<SessionStatus>("/api/session/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source, path: path || null }),
  });
}

/** List input audio devices for the loopback source. */
export function listAudioDevices(): Promise<AudioDevice[]> {
  return request<AudioDevice[]>("/api/audio/devices");
}

/** Stop the active meeting session (safe to call when none is running). */
export function stopSession(): Promise<SessionStatus> {
  return request<SessionStatus>("/api/session/stop", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
}
