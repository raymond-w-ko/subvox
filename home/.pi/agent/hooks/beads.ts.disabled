import type { HookAPI } from "@mariozechner/pi-coding-agent/hooks";

export default function (pi: HookAPI) {
  pi.on("session", async (event) => {
    if (event.reason === "compact") {
      pi.send("<hook>This session has been compacted. Run `bd prime` now to refresh beads issue tracking workflow details.</hook>");
    }
  });
}
