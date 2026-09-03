/**
 * Material UI theme — "Ivory / Navy".
 *
 * Warm ivory-cream canvas with crisp white cards, near-black text for contrast,
 * a navy primary accent and powder-blue light fills. Semantic green/amber are
 * kept for the grounded / not-in-document states.
 */

import { createTheme } from "@mui/material/styles";

// --- palette (near-white ivory · black · powder blue · navy) -----------
const IVORY = "#F8F5EF"; // near-white warm
const BLACK = "#161616";
const POWDER = "#8FB4CE";
const NAVY = "#17293F";

const INK = BLACK; // primary text
const MUTED = "#5E594D"; // secondary text (warm dark grey)
const BORDER = "#E6E0D2"; // faint warm hairline
const CARD_BORDER = "#EAE4D6";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: NAVY, light: "#DCE6EE", dark: "#0E1B2B", contrastText: "#FFFFFF" },
    secondary: { main: POWDER, dark: "#5E88A6" },
    success: { main: "#1C6B44", light: "#DEEAE0" },
    warning: { main: "#A96E2C", light: "#F1E5CF" },
    error: { main: "#B14A3F" },
    background: { default: "#F4F1E9", paper: "#FFFFFF" },
    text: { primary: INK, secondary: MUTED },
    divider: BORDER,
  },
  shape: { borderRadius: 14 },
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
    h6: { fontWeight: 700, letterSpacing: "-0.01em", color: INK },
    subtitle1: { fontWeight: 600 },
    subtitle2: { fontWeight: 600, letterSpacing: "0.02em" },
    button: { textTransform: "none", fontWeight: 600 },
    overline: { fontWeight: 700, letterSpacing: "0.09em" },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: `linear-gradient(180deg, ${IVORY} 0%, #F3EFE6 50%, #EDE8DB 100%)`,
          backgroundAttachment: "fixed",
        },
        "::selection": { background: POWDER },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: "rgba(250, 248, 243, 0.82)",
          backdropFilter: "saturate(180%) blur(10px)",
          color: INK,
          borderBottom: `1px solid ${CARD_BORDER}`,
        },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          border: `1px solid ${CARD_BORDER}`,
          boxShadow:
            "0 2px 4px rgba(22,22,22,0.05), 0 18px 40px rgba(22,22,22,0.10)",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        outlined: { borderColor: CARD_BORDER },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { borderRadius: 11, paddingInline: 18 },
        containedPrimary: {
          boxShadow: "0 6px 16px rgba(23,41,63,0.30)",
          "&:hover": { boxShadow: "0 10px 24px rgba(23,41,63,0.38)" },
        },
      },
    },
    MuiChip: { styleOverrides: { root: { fontWeight: 600 } } },
    MuiAccordion: {
      styleOverrides: { root: { "&:before": { display: "none" } } },
    },
  },
});
