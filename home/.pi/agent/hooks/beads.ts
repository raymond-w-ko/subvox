import type { HookAPI } from "@mariozechner/pi-coding-agent/hooks";

export default function (pi: HookAPI) {
  pi.on("session", async (event) => {
    if (event.reason === "start" || event.reason === "compact") {
      pi.send("<hook>This is your automated reminder to run `bd prime` if beads is mentioned in the system prompt. Either run it or respond quietly if unnecessary</hook>");
    }
  });
}
