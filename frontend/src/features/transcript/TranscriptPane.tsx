/** Collapsible live-transcript pane for meeting context. */

import { useEffect, useRef, useState } from "react";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Collapse from "@mui/material/Collapse";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

import { useAppSelector } from "../../app/store";

export default function TranscriptPane() {
  const [open, setOpen] = useState(true);
  const lines = useAppSelector((s) => s.transcript.lines);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Keep the newest line in view.
  useEffect(() => {
    const el = scrollRef.current;
    if (el && open) el.scrollTop = el.scrollHeight;
  }, [lines.length, open]);

  return (
    <Box>
      <Stack direction="row" alignItems="center" spacing={1}>
        <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
          Live transcript
        </Typography>
        <Chip size="small" variant="outlined" label={lines.length} />
        <IconButton size="small" onClick={() => setOpen((v) => !v)}>
          {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Stack>

      <Collapse in={open}>
        <Box
          ref={scrollRef}
          sx={{
            mt: 1,
            p: 1.25,
            maxHeight: 200,
            overflowY: "auto",
            borderRadius: 2,
            bgcolor: "#f8f9fb",
            border: "1px solid",
            borderColor: "divider",
            fontSize: 13,
          }}
        >
          {lines.length === 0 ? (
            <Typography variant="caption" color="text.secondary">
              Nothing transcribed yet.
            </Typography>
          ) : (
            <Stack spacing={0.75}>
              {lines.map((line, index) => (
                <Box key={index}>
                  <Typography
                    component="span"
                    variant="caption"
                    sx={{ fontWeight: 700, color: "primary.main", mr: 0.75 }}
                  >
                    {line.speaker}
                  </Typography>
                  <Typography component="span" variant="body2" color="text.secondary">
                    {line.text}
                  </Typography>
                </Box>
              ))}
            </Stack>
          )}
        </Box>
      </Collapse>
    </Box>
  );
}
