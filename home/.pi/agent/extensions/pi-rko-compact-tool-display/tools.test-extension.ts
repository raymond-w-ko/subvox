import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Text } from "@earendil-works/pi-tui";
import { Type } from "typebox";

/** Offline fixtures for renderer-only overrides; no third-party checkout is required. */
export default function (pi: ExtensionAPI): void {
  pi.registerToolRenderer((toolName, next) =>
    toolName === "fixture_fallback" ? { renderShell: "default" } : next(),
  );
  for (const name of ["read", "replace", "undo_last_replace", "todo", "ffgrep", "fffind", "unrelated"]) {
    pi.registerTool({
      name,
      label: `Fixture ${name}`,
      description: `Original ${name} execution`,
      parameters: Type.Object({ value: Type.String() }),
      exposure: "deferred",
      annotations: { readOnlyHint: true },
      renderShell: "default",
      renderCall: () => new Text("original call", 0, 0),
      renderResult: () => new Text("original result", 0, 0),
      async execute() {
        return { content: [{ type: "text", text: `${name}: original execution` }], details: {} };
      },
    });
  }
}
