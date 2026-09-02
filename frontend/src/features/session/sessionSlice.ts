/**
 * Redux slice for the meeting session lifecycle (start / stop).
 *
 * The WebSocket connection is not managed here - `wsMiddleware` reacts to the
 * `startSession`/`stopSession` fulfilled actions to open and close the socket.
 */

import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { startSession, stopSession } from "../../api/client";
import type { SessionSource, SessionStatus } from "../../types/api";

export type SessionRunState = "idle" | "starting" | "running" | "stopping";

export interface SessionState {
  runState: SessionRunState;
  source: SessionSource;
  filePath: string;
  error: string | null;
}

const initialState: SessionState = {
  runState: "idle",
  source: "mock",
  filePath: "",
  error: null,
};

/** Start the transcription-to-answer pipeline on the backend. */
export const startSessionThunk = createAsyncThunk<
  SessionStatus,
  { source: SessionSource; path?: string },
  { rejectValue: string }
>("session/start", async ({ source, path }, { rejectWithValue }) => {
  try {
    return await startSession(source, path);
  } catch (err) {
    return rejectWithValue(err instanceof Error ? err.message : "Could not start session");
  }
});

/** Stop the active pipeline. */
export const stopSessionThunk = createAsyncThunk<SessionStatus, void, { rejectValue: string }>(
  "session/stop",
  async (_, { rejectWithValue }) => {
    try {
      return await stopSession();
    } catch (err) {
      return rejectWithValue(err instanceof Error ? err.message : "Could not stop session");
    }
  },
);

const sessionSlice = createSlice({
  name: "session",
  initialState,
  reducers: {
    sourceChanged(state, action: { payload: SessionSource }) {
      state.source = action.payload;
    },
    filePathChanged(state, action: { payload: string }) {
      state.filePath = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(startSessionThunk.pending, (state) => {
        state.runState = "starting";
        state.error = null;
      })
      .addCase(startSessionThunk.fulfilled, (state, action) => {
        state.runState = action.payload.session_running ? "running" : "idle";
      })
      .addCase(startSessionThunk.rejected, (state, action) => {
        state.runState = "idle";
        state.error = action.payload ?? "Could not start session";
      })
      .addCase(stopSessionThunk.pending, (state) => {
        state.runState = "stopping";
      })
      .addCase(stopSessionThunk.fulfilled, (state) => {
        state.runState = "idle";
      })
      .addCase(stopSessionThunk.rejected, (state, action) => {
        state.runState = "idle";
        state.error = action.payload ?? "Could not stop session";
      });
  },
});

export const { sourceChanged, filePathChanged } = sessionSlice.actions;
export default sessionSlice.reducer;
