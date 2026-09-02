/**
 * Detects whether the app is running inside the Zoom client and, if so, pulls
 * basic meeting/user context via the Zoom Apps SDK.
 *
 * Everything is best-effort: any failure (normal browser, SDK missing, older
 * client, denied capability) resolves to `{ inZoom: false }` so the standalone
 * web UI is completely unaffected.
 */

import { useEffect, useState } from "react";
import type { Apis } from "@zoom/appssdk";

export interface ZoomAppContext {
  /** True once `zoomSdk.config()` has succeeded. */
  inZoom: boolean;
  /** `inMeeting`, `inMainClient`, `inWebinar`, ... when known. */
  runningContext?: string;
  /** Zoom meeting id, when available and permitted. */
  meetingId?: string;
  /** The viewer's display name, when available and permitted. */
  screenName?: string;
}

const CAPABILITIES: Apis[] = [
  "getRunningContext",
  "getMeetingContext",
  "getUserContext",
];

export function useZoomApp(): ZoomAppContext {
  const [ctx, setCtx] = useState<ZoomAppContext>({ inZoom: false });

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const zoomSdk = (await import("@zoom/appssdk")).default;
        await zoomSdk.config({ capabilities: CAPABILITIES });

        const next: ZoomAppContext = { inZoom: true };
        try {
          next.runningContext = (await zoomSdk.getRunningContext()).context;
        } catch {
          /* capability not granted - ignore */
        }
        try {
          next.meetingId = (await zoomSdk.getMeetingContext()).meetingID;
        } catch {
          /* not in a meeting or not permitted - ignore */
        }
        try {
          next.screenName = (await zoomSdk.getUserContext()).screenName;
        } catch {
          /* not permitted - ignore */
        }

        if (!cancelled) setCtx(next);
      } catch {
        if (!cancelled) setCtx({ inZoom: false });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  return ctx;
}
