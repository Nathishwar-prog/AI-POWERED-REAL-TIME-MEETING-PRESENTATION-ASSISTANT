/** A single question + suggested-answer card for the presenter. */

import { useState } from "react";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Grow from "@mui/material/Grow";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import CheckIcon from "@mui/icons-material/Check";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import MenuBookIcon from "@mui/icons-material/MenuBook";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";

import { timeAgo } from "../../lib/time";
import type { QaCardModel } from "./qaSlice";

function Eyebrow({ children, color = "text.secondary" }: { children: string; color?: string }) {
  return (
    <Typography variant="overline" sx={{ color, lineHeight: 1, display: "block" }}>
      {children}
    </Typography>
  );
}

export default function QaCard({ card }: { card: QaCardModel }) {
  const { question, answer } = card;
  const [copied, setCopied] = useState(false);
  const accent = answer.grounded ? "success.main" : "warning.main";

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(answer.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked — ignore */
    }
  };

  return (
    <Grow in appear timeout={350}>
      <Card sx={{ position: "relative", overflow: "hidden", pl: 0.5 }}>
        <Box
          sx={{
            position: "absolute",
            left: 0,
            top: 0,
            bottom: 0,
            width: 4,
            bgcolor: accent,
          }}
        />
        <Box sx={{ p: 2.25, pl: 2.5 }}>
          <Stack direction="row" alignItems="flex-start" spacing={1}>
            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
              <Eyebrow>QUESTION</Eyebrow>
              <Typography sx={{ fontWeight: 600, mt: 0.5 }}>{question.text}</Typography>
            </Box>
            <Tooltip title={copied ? "Copied" : "Copy answer"}>
              <IconButton size="small" onClick={copy} sx={{ mt: -0.5 }}>
                {copied ? (
                  <CheckIcon fontSize="small" color="success" />
                ) : (
                  <ContentCopyIcon fontSize="small" />
                )}
              </IconButton>
            </Tooltip>
          </Stack>

          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.75 }}>
            {question.speaker} · {timeAgo(question.asked_at)}
          </Typography>

          <Box
            sx={{
              mt: 1.5,
              pt: 1.5,
              borderTop: "1px solid",
              borderColor: "divider",
            }}
          >
            <Eyebrow color={answer.grounded ? "success.main" : "warning.main"}>
              {answer.grounded ? "SUGGESTED ANSWER" : "NOT IN DOCUMENT"}
            </Eyebrow>
            <Typography sx={{ mt: 0.5, whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
              {answer.text}
            </Typography>
          </Box>

          {!answer.grounded && (
            <Chip
              size="small"
              icon={<WarningAmberIcon />}
              color="warning"
              variant="outlined"
              label="No matching section found"
              sx={{ mt: 1.5 }}
            />
          )}

          {answer.sources.map((source, index) => (
            <Accordion
              key={index}
              disableGutters
              elevation={0}
              square
              sx={{
                mt: 1.5,
                border: "1px solid",
                borderColor: "divider",
                borderRadius: 2,
                overflow: "hidden",
                bgcolor: "#fbfbfd",
              }}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: 44 }}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <MenuBookIcon sx={{ fontSize: 18, color: "primary.main" }} />
                  <Typography variant="body2" fontWeight={600}>
                    {source.section_title}
                  </Typography>
                  <Chip size="small" variant="outlined" label={source.score.toFixed(2)} />
                </Stack>
              </AccordionSummary>
              <AccordionDetails>
                <Box
                  sx={{
                    fontSize: 13.5,
                    color: "text.secondary",
                    borderLeft: "3px solid",
                    borderColor: "primary.light",
                    pl: 1.5,
                    whiteSpace: "pre-wrap",
                    lineHeight: 1.55,
                  }}
                >
                  {source.snippet}
                </Box>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      </Card>
    </Grow>
  );
}
