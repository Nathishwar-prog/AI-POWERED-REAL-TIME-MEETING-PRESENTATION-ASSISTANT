/**
 * Redux slice for the uploaded document: upload lifecycle + ingest summary.
 */

import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { uploadDocument } from "../../api/client";
import type { DocumentInfo } from "../../types/api";

export type UploadStatus = "idle" | "uploading" | "ready" | "error";

export interface DocumentState {
  status: UploadStatus;
  docId: string | null;
  sections: number;
  chunks: number;
  fileName: string | null;
  error: string | null;
}

const initialState: DocumentState = {
  status: "idle",
  docId: null,
  sections: 0,
  chunks: 0,
  fileName: null,
  error: null,
};

/** Upload a `.docx` to the backend and store the returned ingest summary. */
export const uploadDocumentThunk = createAsyncThunk<
  DocumentInfo & { fileName: string },
  File,
  { rejectValue: string }
>("document/upload", async (file, { rejectWithValue }) => {
  try {
    const info = await uploadDocument(file);
    return { ...info, fileName: file.name };
  } catch (err) {
    return rejectWithValue(err instanceof Error ? err.message : "Upload failed");
  }
});

const documentSlice = createSlice({
  name: "document",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(uploadDocumentThunk.pending, (state) => {
        state.status = "uploading";
        state.error = null;
      })
      .addCase(uploadDocumentThunk.fulfilled, (state, action) => {
        state.status = "ready";
        state.docId = action.payload.doc_id;
        state.sections = action.payload.sections;
        state.chunks = action.payload.chunks;
        state.fileName = action.payload.fileName;
      })
      .addCase(uploadDocumentThunk.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload ?? "Upload failed";
      });
  },
});

export default documentSlice.reducer;
