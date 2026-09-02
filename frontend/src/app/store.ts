/**
 * Redux Toolkit store configuration and typed hooks.
 *
 * Import `useAppDispatch` / `useAppSelector` (not the bare react-redux hooks)
 * everywhere so components get full type inference for state and thunks.
 */

import { configureStore } from "@reduxjs/toolkit";
import { useDispatch, useSelector } from "react-redux";

import documentReducer from "../features/document/documentSlice";
import qaReducer from "../features/qa/qaSlice";
import sessionReducer from "../features/session/sessionSlice";
import transcriptReducer from "../features/transcript/transcriptSlice";
import { wsMiddleware } from "./wsMiddleware";

export const store = configureStore({
  reducer: {
    document: documentReducer,
    session: sessionReducer,
    qa: qaReducer,
    transcript: transcriptReducer,
  },
  middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(wsMiddleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

/** Typed `useDispatch` - knows about thunk actions. */
export const useAppDispatch = () => useDispatch<AppDispatch>();

/** Typed `useSelector` - infers `RootState`. */
export const useAppSelector = useSelector.withTypes<RootState>();
