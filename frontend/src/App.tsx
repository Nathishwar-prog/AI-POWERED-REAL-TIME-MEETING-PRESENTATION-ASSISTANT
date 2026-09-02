/** Top-level presenter view: a setup rail on the left, live Q&A on the right. */

import { useEffect } from "react";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Container from "@mui/material/Container";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import LockIcon from "@mui/icons-material/Lock";
import VideocamIcon from "@mui/icons-material/Videocam";

import LiveDot from "./components/LiveDot";
import { useAppDispatch, useAppSelector } from "./app/store";
import { sourceChanged } from "./features/session/sessionSlice";
import DocumentUpload from "./features/document/DocumentUpload";
import QaList from "./features/qa/QaList";
import SessionControls from "./features/session/SessionControls";
import TranscriptPane from "./features/transcript/TranscriptPane";
import { useZoomApp } from "./zoom/useZoomApp";

export default function App() {
  const dispatch = useAppDispatch();
  const running = useAppSelector((s) => s.session.runState === "running");
  const answerCount = useAppSelector((s) => s.qa.cards.length);
  const zoom = useZoomApp();

  // Inside the Zoom client the only usable audio source is local loopback.
  useEffect(() => {
    if (zoom.inZoom) dispatch(sourceChanged("loopback"));
  }, [zoom.inZoom, dispatch]);

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar position="sticky" elevation={0}>
        <Toolbar sx={{ gap: 1.5 }}>
          <Box
            sx={{
              width: 34,
              height: 34,
              borderRadius: 2,
              display: "grid",
              placeItems: "center",
              color: "#fff",
              background: "linear-gradient(135deg, #6366f1, #0ea5e9)",
            }}
          >
            <AutoAwesomeIcon sx={{ fontSize: 20 }} />
          </Box>
          <Box sx={{ flexGrow: 1, lineHeight: 1.1 }}>
            <Typography variant="h6" component="div">
              Presenter Assistant
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Live answers from your document
            </Typography>
          </Box>

          {zoom.inZoom && (
            <Chip
              size="small"
              variant="outlined"
              icon={<VideocamIcon />}
              label={zoom.meetingId ? `Zoom · ${zoom.meetingId}` : "Zoom App"}
            />
          )}
          <Chip
            size="small"
            variant="outlined"
            icon={<LiveDot active={running} />}
            label={running ? "Listening" : "Idle"}
            sx={{
              pl: 1,
              borderColor: running ? "success.main" : "divider",
              color: running ? "success.main" : "text.secondary",
            }}
          />
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Stack direction={{ xs: "column", md: "row" }} spacing={3} alignItems="flex-start">
          <Paper
            variant="outlined"
            sx={{
              p: 2.5,
              width: { xs: "100%", md: 400 },
              flexShrink: 0,
              position: { md: "sticky" },
              top: { md: 88 },
            }}
          >
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              sx={{ mb: 0.5, color: "text.secondary" }}
            >
              <LockIcon sx={{ fontSize: 16 }} />
              <Typography variant="caption">
                Private to you{zoom.inZoom ? " — only you see this panel" : " — don't screen-share this window"}
              </Typography>
            </Stack>

            <Stack spacing={2.5} divider={<Divider flexItem />} sx={{ mt: 2 }}>
              <DocumentUpload />
              <SessionControls />
              <TranscriptPane />
            </Stack>
          </Paper>

          <Box sx={{ flexGrow: 1, width: "100%" }}>
            <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1.5 }}>
              <Typography variant="h6">Suggested answers</Typography>
              {answerCount > 0 && (
                <Chip size="small" color="primary" variant="outlined" label={answerCount} />
              )}
            </Stack>
            <QaList />
          </Box>
        </Stack>
      </Container>
    </Box>
  );
}
