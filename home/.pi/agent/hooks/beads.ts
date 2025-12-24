import type { HookAPI } from "@mariozechner/pi-coding-agent/hooks";

export default function (pi: HookAPI) {
  pi.on("session", async (event, ctx) => {
    if (event.reason === "start" || event.reason === "before_compact") {
      const result = await ctx.exec("bd", ["prime"]);
      if (result.code === 0) {
        if (result.stdout.trim()) {
          pi.send(result.stdout);
        }
        ctx.ui.notify(`bd prime completed`, "info");
      } else {
        ctx.ui.notify(`bd prime failed: ${result.stderr}`, "error");
      }
    }
  });
}
