/**
 * Redux middleware that owns the single presenter WebSocket connection.
 *
 * Lifecycle is driven entirely by session actions so components never touch the
 * socket (single responsibility):
 *
 *  - `startSession.fulfilled`  -> clear old data, open the socket
 *  - `stopSession.pending`     -> close the socket
 *
 * While a session is running the socket auto-reconnects with a capped backoff.
 */

import type { Middleware } from "@reduxjs/toolkit";

import type { PresenterEvent } from "../types/api";
import { qaCleared, qaReceived } from "../features/qa/qaSlice";
import {
  startSessionThunk,
  stopSessionThunk,
} from "../features/session/sessionSlice";
import {
  transcriptCleared,
  transcriptLineReceived,
} from "../features/transcript/transcriptSlice";
import { presenterWsUrl } from "../api/client";

const MAX_BACKOFF_MS = 5000;

export const wsMiddleware: Middleware = (store) => {
  let socket: WebSocket | null = null;
  let wantConnection = false;
  let backoffMs = 500;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  const clearReconnect = () => {
    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  const closeSocket = () => {
    clearReconnect();
    if (socket) {
      socket.onclose = null;
      socket.close();
      socket = null;
    }
  };

  const openSocket = () => {
    clearReconnect();
    socket = new WebSocket(presenterWsUrl());

    socket.onopen = () => {
      backoffMs = 500;
    };

    socket.onmessage = (message) => {
      let event: PresenterEvent;
      try {
        event = JSON.parse(message.data as string) as PresenterEvent;
      } catch {
        return;
      }
      if (event.type === "qa") {
        store.dispatch(qaReceived(event));
      } else if (event.type === "transcript") {
        store.dispatch(transcriptLineReceived(event));
      }
    };

    socket.onclose = () => {
      socket = null;
      if (!wantConnection) return;
      reconnectTimer = setTimeout(openSocket, backoffMs);
      backoffMs = Math.min(backoffMs * 2, MAX_BACKOFF_MS);
    };
  };

  return (next) => (action) => {
    if (startSessionThunk.fulfilled.match(action)) {
      store.dispatch(qaCleared());
      store.dispatch(transcriptCleared());
      closeSocket(); // drop any stale socket first
      wantConnection = true;
      openSocket();
    } else if (
      stopSessionThunk.pending.match(action) ||
      stopSessionThunk.fulfilled.match(action)
    ) {
      wantConnection = false;
      closeSocket();
    }
    return next(action);
  };
};
