/** Upload control for the pre-meeting `.docx`. */

import { type ChangeEvent } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import DescriptionIcon from "@mui/icons-material/Description";
import UploadFileIcon from "@mui/icons-material/UploadFile";

import StepHeader from "../../components/StepHeader";
import { useAppDispatch, useAppSelector } from "../../app/store";
import { uploadDocumentThunk } from "./documentSlice";

export default function DocumentUpload() {
  const dispatch = useAppDispatch();
  const { status, sections, chunks, fileName, error } = useAppSelector((s) => s.document);
  const isUploading = status === "uploading";
  const isReady = status === "ready";

  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) dispatch(uploadDocumentThunk(file));
    event.target.value = ""; // allow re-selecting the same file
  };

  return (
    <Box>
      <StepHeader step={1} title="Presentation document" done={isReady} />

      <Box
        component="label"
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          p: 1.5,
          cursor: isUploading ? "default" : "pointer",
          borderRadius: 2,
          border: "1px dashed",
          borderColor: isReady ? "success.main" : "divider",
          bgcolor: isReady ? "success.light" : "transparent",
          transition: "border-color .15s, background-color .15s",
          "&:hover": { borderColor: isUploading ? undefined : "primary.main" },
        }}
      >
        <input hidden type="file" accept=".docx" onChange={handleFile} disabled={isUploading} />
        {isUploading ? (
          <CircularProgress size={20} />
        ) : isReady ? (
          <CheckCircleIcon color="success" />
        ) : (
          <UploadFileIcon color="action" />
        )}
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="body2" fontWeight={600} noWrap>
            {isUploading
              ? "Uploading…"
              : isReady
                ? fileName ?? "Document ready"
                : "Choose a .docx file"}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {isReady
              ? `${sections} sections · ${chunks} chunks indexed`
              : "Click to browse — replace it any time"}
          </Typography>
        </Box>
      </Box>

      {isReady && (
        <Stack direction="row" spacing={0.5} alignItems="center" sx={{ mt: 1, color: "text.secondary" }}>
          <DescriptionIcon sx={{ fontSize: 14 }} />
          <Typography variant="caption">Retrieval runs against this document.</Typography>
        </Stack>
      )}

      {status === "error" && error && (
        <Alert severity="error" sx={{ mt: 1.5 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
}
