/**
 * Wire types mirroring the backend Pydantic models in `backend/app/models.py`.
 * Keep this file in sync with that module - it is the single source of truth for
 * the shapes exchanged over REST and the presenter WebSocket.
 */

/** A citation shown to the presenter: which document section backed the answer. */
export interface SourceRef {
  section_title: string;
  snippet: string;
  score: number;
}

/** The LLM's grounded answer plus its sources. */
export interface SuggestedAnswer {
  text: string;
  sources: SourceRef[];
  grounded: boolean;
}

/** A detected participant question. */
export interface Question {
  id: string;
  text: string;
  asked_at: string;
  speaker: string;
}

/** Summary returned by `POST /api/documents`. */
export interface DocumentInfo {
  doc_id: string;
  sections: number;
  chunks: number;
}

/** Status returned by the session endpoints and `GET /api/status`. */
export interface SessionStatus {
  session_running: boolean;
  active_doc_id: string | null;
}

/** `{ type: "transcript" }` event pushed over the presenter WebSocket. */
export interface TranscriptEvent {
  type: "transcript";
  text: string;
  speaker: string;
  start: number;
  end: number;
}

/** `{ type: "qa" }` event pushed over the presenter WebSocket. */
export interface QaEvent {
  type: "qa";
  question: Question;
  answer: SuggestedAnswer;
}

export type PresenterEvent = TranscriptEvent | QaEvent;

/** Which audio source a session should use. */
export type SessionSource = "mock" | "file" | "loopback";

/** A capture option reported by `GET /api/audio/devices`. */
export interface AudioDevice {
  /** What to send as `path` to start a loopback session. */
  value: string;
  name: string;
  channels: number;
  rate: number;
  hostapi: string;
}
