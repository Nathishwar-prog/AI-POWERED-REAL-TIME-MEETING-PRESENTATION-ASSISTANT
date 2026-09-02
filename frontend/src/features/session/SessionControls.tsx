/** Start/stop the meeting session and pick the audio source. */

import { useEffect, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";

import LiveDot from "../../components/LiveDot";
import StepHeader from "../../components/StepHeader";
import { listAudioDevices } from "../../api/client";
import { useAppDispatch, useAppSelector } from "../../app/store";
import type { AudioDevice, SessionSource } from "../../types/api";
import {
  filePathChanged,
  sourceChanged,
  startSessionThunk,
  stopSessionThunk,
} from "./sessionSlice";

/** Devices that usually carry "what you hear" (the other participants). */
const LOOPBACK_HINTS = ["stereo mix", "cable output", "voicemeeter", "what u hear", "wave out", "loopback"];

export default function SessionControls() {
  const dispatch = useAppDispatch();
  const { runState, source, filePath, error } = useAppSelector((s) => s.session);
  const documentReady = useAppSelector((s) => s.document.status === "ready");

  const running = runState === "running";
  const busy = runState === "starting" || runState === "stopping";

  // `file` needs a path; `loopback` optionally takes a device name; `mock` ignores it.
  const usesPath = source === "file" || source === "loopback";

  const [devices, setDevices] = useState<AudioDevice[]>([]);
  useEffect(() => {
    if (source !== "loopback") return;
    listAudioDevices()
      .then(setDevices)
      .catch(() => setDevices([]));
  }, [source]);

  const selectedIsMic =
    source === "loopback" &&
    filePath !== "" &&
    filePath !== "both" &&
    !LOOPBACK_HINTS.some((h) => filePath.toLowerCase().includes(h));

  const handleStart = () => {
    dispatch(
      startSessionThunk({ source, path: usesPath ? filePath.trim() || undefined : undefined }),
    );
  };

  return (
    <Box>
      <StepHeader step={2} title="Meeting audio" done={running} />

      <Stack spacing={1.5}>
        <TextField
          select
          size="small"
          label="Source"
          value={source}
          disabled={running || busy}
          onChange={(e) => dispatch(sourceChanged(e.target.value as SessionSource))}
          fullWidth
        >
          <MenuItem value="mock">Scripted transcript (demo)</MenuItem>
          <MenuItem value="file">Audio file (Whisper)</MenuItem>
          <MenuItem value="loopback">Live meeting audio (Whisper)</MenuItem>
        </TextField>

        {source === "file" && (
          <TextField
            size="small"
            label="Audio file path"
            placeholder="sample_data/meeting.wav"
            value={filePath}
            disabled={running || busy}
            onChange={(e) => dispatch(filePathChanged(e.target.value))}
            fullWidth
          />
        )}

        {source === "loopback" && (
          <>
            <TextField
              select
              size="small"
              label="Input device"
              value={filePath}
              disabled={running || busy}
              onChange={(e) => dispatch(filePathChanged(e.target.value))}
              fullWidth
              helperText="“System audio” captures what you hear (the other participants) — works with any headset. Pick a mic only to capture your own voice."
            >
              {devices.length === 0 && (
                <MenuItem value="">System audio — what you hear</MenuItem>
              )}
              {devices.map((d) => (
                <MenuItem key={d.name} value={d.value}>
                  {d.name}
                </MenuItem>
              ))}
            </TextField>
            {selectedIsMic && (
              <Alert severity="warning" sx={{ py: 0 }}>
                This is a microphone — it only hears you, not the other participants.
                Choose “System audio” instead.
              </Alert>
            )}
          </>
        )}

        {running ? (
          <Button
            variant="contained"
            color="error"
            size="large"
            fullWidth
            startIcon={<StopIcon />}
            disabled={busy}
            onClick={() => dispatch(stopSessionThunk())}
          >
            Stop listening
          </Button>
        ) : (
          <Button
            variant="contained"
            size="large"
            fullWidth
            startIcon={<PlayArrowIcon />}
            disabled={!documentReady || busy}
            onClick={handleStart}
          >
            {busy ? "Starting…" : "Start listening"}
          </Button>
        )}
      </Stack>

      {running && (
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1.25, color: "success.main" }}>
          <LiveDot active />
          <Typography variant="caption" fontWeight={600}>
            Listening for questions…
          </Typography>
        </Stack>
      )}

      {!documentReady && !running && (
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>
          Upload a document first to enable the session.
        </Typography>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 1.5 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
}
