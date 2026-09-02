/** The list of QA cards, newest first, with a friendly empty state. */

import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import ForumOutlinedIcon from "@mui/icons-material/ForumOutlined";

import { useAppSelector } from "../../app/store";
import QaCard from "./QaCard";

export default function QaList() {
  const cards = useAppSelector((s) => s.qa.cards);
  const running = useAppSelector((s) => s.session.runState === "running");

  if (cards.length === 0) {
    return (
      <Paper
        variant="outlined"
        sx={{ py: 7, px: 3, textAlign: "center", borderStyle: "dashed" }}
      >
        <Box
          sx={{
            width: 52,
            height: 52,
            mx: "auto",
            mb: 1.5,
            borderRadius: "50%",
            display: "grid",
            placeItems: "center",
            bgcolor: "primary.light",
            color: "primary.main",
          }}
        >
          <ForumOutlinedIcon />
        </Box>
        <Typography fontWeight={600}>No questions yet</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          {running
            ? "Listening… suggested answers will appear here the moment someone asks."
            : "Upload a document and start listening to see suggested answers here."}
        </Typography>
      </Paper>
    );
  }

  return (
    <Stack spacing={2}>
      {cards.map((card) => (
        <QaCard key={card.cardId} card={card} />
      ))}
    </Stack>
  );
}
