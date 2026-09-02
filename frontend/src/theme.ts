/**
 * Material UI theme — a bright, modern, white-surfaced presenter UI.
 *
 * Design intent: a soft grey page canvas with crisp white cards, an indigo
 * primary accent, generous rounding, and low-contrast borders + soft shadows so
 * content (not chrome) draws the eye.
 */

import { createTheme } from "@mui/material/styles";

const INK = "#0f172a";
const MUTED = "#64748b";
const BORDER = "#e7e9ee";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#4f46e5", light: "#eef2ff", dark: "#4338ca" },
    secondary: { main: "#0ea5e9" },
    success: { main: "#16a34a", light: "#dcfce7" },
    warning: { main: "#d97706", light: "#fef3c7" },
    error: { main: "#dc2626" },
    background: { default: "#f5f6f8", paper: "#ffffff" },
    text: { primary: INK, secondary: MUTED },
    divider: BORDER,
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: [
      "system-ui",
      "-apple-system",
      "Segoe UI",
      "Roboto",
      "Helvetica",
      "Arial",
      "sans-serif",
    ].join(","),
    h6: { fontWeight: 700, letterSpacing: "-0.01em" },
    subtitle1: { fontWeight: 600 },
    subtitle2: { fontWeight: 600, letterSpacing: "0.02em" },
    button: { textTransform: "none", fontWeight: 600 },
    overline: { fontWeight: 700, letterSpacing: "0.08em" },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: { backgroundColor: "#f5f6f8" },
        "::selection": { background: "#c7d2fe" },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: "rgba(255,255,255,0.85)",
          backdropFilter: "saturate(180%) blur(8px)",
          color: INK,
          borderBottom: `1px solid ${BORDER}`,
        },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          border: `1px solid ${BORDER}`,
          boxShadow: "0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.05)",
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: { root: { borderRadius: 10, paddingInline: 18 } },
    },
    MuiChip: { styleOverrides: { root: { fontWeight: 600 } } },
    MuiAccordion: {
      styleOverrides: {
        root: { "&:before": { display: "none" } },
      },
    },
  },
});
