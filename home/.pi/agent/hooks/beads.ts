import type { HookAPI } from "@mariozechner/pi-coding-agent/hooks";

export default function (pi: HookAPI) {
  pi.on("session", async (event) => {
    if (event.reason === "start" || event.reason === "compact") {
      pi.send("Run `bd prime` if beads is used for issue tracking in this project.");
    }
  });
}
