import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

const YEET_PROMPT = `Now, based on your knowledge of the project, commit all changed files now in a series of logically connected groupings with super detailed commit messages for each and then push. Take your time to do it right. Don't edit the code at all. Don't commit obviously ephemeral files. Use ultrathink.`;

export default function (pi: ExtensionAPI) {
  pi.registerCommand("yeet", {
    description: "Commit changed files in logical groups, then push",
    handler: async (args, ctx) => {
      const prompt = args?.trim()
        ? `${YEET_PROMPT}\n\nAdditional instructions from the user:\n${args.trim()}`
        : YEET_PROMPT;

      if (ctx.isIdle()) {
        pi.sendUserMessage(prompt);
      } else {
        pi.sendUserMessage(prompt, { deliverAs: "followUp" });
        ctx.ui.notify("Queued /yeet as a follow-up", "info");
      }
    },
  });
}
