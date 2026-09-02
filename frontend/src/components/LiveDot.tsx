/** A small coloured dot that pulses while a session is live. */

import Box from "@mui/material/Box";
import { keyframes } from "@mui/system";

const pulse = keyframes`
  0%   { box-shadow: 0 0 0 0 rgba(22,163,74,0.45); }
  70%  { box-shadow: 0 0 0 8px rgba(22,163,74,0); }
  100% { box-shadow: 0 0 0 0 rgba(22,163,74,0); }
`;

export default function LiveDot({ active }: { active: boolean }) {
  return (
    <Box
      component="span"
      sx={{
        width: 9,
        height: 9,
        borderRadius: "50%",
        flexShrink: 0,
        bgcolor: active ? "success.main" : "text.disabled",
        animation: active ? `${pulse} 1.8s ease-out infinite` : "none",
      }}
    />
  );
}
