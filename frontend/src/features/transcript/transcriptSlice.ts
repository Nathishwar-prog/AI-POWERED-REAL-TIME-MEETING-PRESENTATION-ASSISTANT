/**
 * Redux slice holding the rolling live transcript shown in the context pane.
 */

import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { TranscriptEvent } from "../../types/api";

/** One transcript line as displayed to the presenter. */
export interface TranscriptLine {
  text: string;
  speaker: string;
  start: number;
}

export interface TranscriptState {
  lines: TranscriptLine[];
}

/** Keep memory bounded during a long meeting. */
const MAX_LINES = 200;

const initialState: TranscriptState = { lines: [] };

const transcriptSlice = createSlice({
  name: "transcript",
  initialState,
  reducers: {
    transcriptLineReceived(state, action: PayloadAction<TranscriptEvent>) {
      state.lines.push({
        text: action.payload.text,
        speaker: action.payload.speaker,
        start: action.payload.start,
      });
      if (state.lines.length > MAX_LINES) {
        state.lines.splice(0, state.lines.length - MAX_LINES);
      }
    },
    transcriptCleared(state) {
      state.lines = [];
    },
  },
});

export const { transcriptLineReceived, transcriptCleared } = transcriptSlice.actions;
export default transcriptSlice.reducer;
