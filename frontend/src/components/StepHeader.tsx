/** A numbered step heading: a small circular badge + a title, with optional trailing content. */

import type { ReactNode } from "react";
import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

interface StepHeaderProps {
  step: number;
  title: string;
  done?: boolean;
  action?: ReactNode;
}

export default function StepHeader({ step, title, done = false, action }: StepHeaderProps) {
  return (
    <Stack direction="row" alignItems="center" spacing={1.25} sx={{ mb: 1.5 }}>
      <Avatar
        sx={{
          width: 22,
          height: 22,
          fontSize: 12,
          fontWeight: 700,
          bgcolor: done ? "success.main" : "primary.main",
        }}
      >
        {done ? "✓" : step}
      </Avatar>
      <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
        {title}
      </Typography>
      {action && <Box>{action}</Box>}
    </Stack>
  );
}
