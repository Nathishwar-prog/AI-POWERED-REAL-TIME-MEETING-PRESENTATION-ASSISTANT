/**
 * Redux slice holding the question + suggested-answer cards, newest first.
 */

import { createSlice, nanoid, type PayloadAction } from "@reduxjs/toolkit";

import type { QaEvent } from "../../types/api";

/** A QA event plus a client-side id and arrival time for rendering. */
export interface QaCardModel extends QaEvent {
  cardId: string;
  receivedAt: number;
}

export interface QaState {
  cards: QaCardModel[];
}

const initialState: QaState = { cards: [] };

const qaSlice = createSlice({
  name: "qa",
  initialState,
  reducers: {
    qaReceived: {
      reducer(state, action: PayloadAction<QaCardModel>) {
        state.cards.unshift(action.payload);
      },
      prepare(event: QaEvent) {
        return { payload: { ...event, cardId: nanoid(), receivedAt: Date.now() } };
      },
    },
    qaCleared(state) {
      state.cards = [];
    },
  },
});

export const { qaReceived, qaCleared } = qaSlice.actions;
export default qaSlice.reducer;
