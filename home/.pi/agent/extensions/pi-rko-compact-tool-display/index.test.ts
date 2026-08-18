import assert from "node:assert/strict";
import { homedir } from "node:os";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";

const piRoot = join(homedir(), "src/pi");
const compactPath = fileURLToPath(new URL("./index.ts", import.meta.url));
const hashlinePath = join(homedir(), "src/pi-hashline-edit-pro/index.ts");
const builtInNames = ["read", "bash", "edit", "write", "grep", "find", "ls"];

async function importPiModule(relativePath: string): Promise<any> {
  return import(pathToFileURL(join(piRoot, relativePath)).href);
}

async function createRunner(extensionPaths: string[], initialActiveTools: string[]) {
  const [{ loadExtensions }, { ExtensionRunner }, { SessionManager }, { AuthStorage }, testUtils] = await Promise.all([
    importPiModule("packages/coding-agent/src/core/extensions/loader.ts"),
    importPiModule("packages/coding-agent/src/core/extensions/runner.ts"),
    importPiModule("packages/coding-agent/src/core/session-manager.ts"),
    importPiModule("packages/coding-agent/src/core/auth-storage.ts"),
    importPiModule("packages/coding-agent/test/model-runtime-test-utils.ts"),
  ]);

  const loaded = await loadExtensions(extensionPaths, process.cwd());
  assert.deepEqual(loaded.errors, []);

  const runner = new ExtensionRunner(
    loaded.extensions,
    loaded.runtime,
    process.cwd(),
    SessionManager.inMemory(),
    await testUtils.createInMemoryModelRegistry(AuthStorage.inMemory()),
  );
  let activeTools = [...initialActiveTools];

  runner.bindCore(
    {
      sendMessage() {},
      sendUserMessage() {},
      appendEntry() {},
      setSessionName() {},
      getSessionName() {
        return undefined;
      },
      setLabel() {},
      getActiveTools() {
        return activeTools;
      },
      getAllTools() {
        return [
          ...builtInNames.map((name) => ({
            name,
            description: "",
            parameters: {},
            sourceInfo: {
              source: "builtin",
              path: `<builtin:${name}>`,
              scope: "temporary",
              origin: "top-level",
            },
          })),
          ...runner.getAllRegisteredTools().map(({ definition, sourceInfo }: any) => ({
            name: definition.name,
            description: definition.description,
            parameters: definition.parameters,
            sourceInfo,
          })),
        ];
      },
      setActiveTools(names: string[]) {
        activeTools = [...names];
      },
      refreshTools() {},
      getCommands() {
        return [];
      },
      async setModel() {
        return false;
      },
      getThinkingLevel() {
        return "off";
      },
      setThinkingLevel() {},
    },
    {
      getModel() {
        return undefined;
      },
      getScopedModels() {
        return [];
      },
      isIdle() {
        return true;
      },
      isProjectTrusted() {
        return true;
      },
      getSignal() {
        return undefined;
      },
      abort() {},
      hasPendingMessages() {
        return false;
      },
      shutdown() {},
      getContextUsage() {
        return undefined;
      },
      compact() {},
      getSystemPrompt() {
        return "";
      },
    },
  );

  await runner.emit({ type: "session_start", reason: "startup" });
  return { runner, getActiveTools: () => activeTools };
}

const theme = {
  fg(_key: string, text: string) {
    return text;
  },
  bg(_key: string, text: string) {
    return text;
  },
  bold(text: string) {
    return text;
  },
};

function renderContext() {
  return {
    args: { path: "x" },
    toolCallId: "1",
    invalidate() {},
    lastComponent: undefined,
    state: {} as Record<string, unknown>,
    cwd: process.cwd(),
    executionStarted: true,
    argsComplete: true,
    isPartial: false,
    expanded: false,
    showImages: false,
    isError: false,
  };
}

test("preserves Hashline tools and renders edge outcomes accurately", async () => {
  const { runner } = await createRunner([compactPath, hashlinePath], builtInNames);
  const owners = new Map(
    runner.getAllRegisteredTools().map((tool: any) => [tool.definition.name, tool.sourceInfo.path]),
  );
  assert.equal(owners.get("read"), hashlinePath);
  assert.equal(owners.get("replace"), hashlinePath);

  const undo = runner.getToolDefinition("undo_last_replace");
  const undoContext = renderContext();
  undo.renderCall({ path: "x" }, theme, undoContext);
  const undoCollapsed = undo.renderResult(
    {
      content: [{ type: "text", text: "No undo history for x. There is no previous replace to revert." }],
      details: {},
    },
    { expanded: false, isPartial: false },
    theme,
    undoContext,
  );
  assert.equal(undoContext.state.compactToolStatus, "err");
  assert.match(undo.renderCall({ path: "x" }, theme, undoContext).render(100).join("\n"), /failed/);
  assert.match(undoCollapsed.render(100).join("\n"), /No undo history/);

  const replace = runner.getToolDefinition("replace");
  const replaceContext = renderContext();
  replace.renderCall({ path: "x" }, theme, replaceContext);
  replace.renderResult(
    {
      content: [{ type: "text", text: "No changes made to x\nClassification: noop" }],
      details: { diff: "", classification: "noop" },
    },
    { expanded: false, isPartial: false },
    theme,
    replaceContext,
  );
  assert.equal(replaceContext.state.compactToolStatus, "noop");
  assert.match(replace.renderCall({ path: "x" }, theme, replaceContext).render(100).join("\n"), /unchanged/);

  const read = runner.getToolDefinition("read");
  const readContext = renderContext();
  const result = {
    content: [{ type: "text", text: "abc│line" }],
    details: { truncation: { truncated: true, totalLines: 100 } },
  };
  const collapsed = read.renderResult(result, { expanded: false, isPartial: false }, theme, readContext);
  const expanded = read.renderResult(result, { expanded: true, isPartial: false }, theme, readContext);
  assert.deepEqual(collapsed.render(100), []);
  assert.match(expanded.render(100).join("\n"), /abc│line/);
  assert.match(expanded.render(100).join("\n"), /truncated from 100 lines/);
});

test("keeps fallback file wrappers active without built-in tools", async () => {
  const { getActiveTools } = await createRunner([compactPath], ["grep", "find", "ls", "bash"]);
  for (const name of ["read", "edit", "write"]) {
    assert(getActiveTools().includes(name), `${name} must remain active`);
  }
});
