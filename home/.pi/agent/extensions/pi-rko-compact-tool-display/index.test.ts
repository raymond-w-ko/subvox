import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";

const piRoot = join(homedir(), "src/pi");
const compactPath = fileURLToPath(new URL("./index.ts", import.meta.url));
const hashlineCompactPath = fileURLToPath(new URL("./hashline.test-extension.ts", import.meta.url));
const hashlinePath = join(homedir(), "src/pi-hashline-edit-pro/index.ts");
const fixturePath = fileURLToPath(new URL("./tools.test-extension.ts", import.meta.url));
const builtInNames = ["read", "bash", "edit", "write", "grep", "find", "ls"];

async function importPiModule(relativePath: string): Promise<any> {
  return import(pathToFileURL(join(piRoot, relativePath)).href);
}

async function createRunner(
  extensionPaths: string[],
  initialActiveTools: string[],
  emitSessionStart = true,
) {
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

  if (emitSessionStart) {
    await runner.emit({ type: "session_start", reason: "startup" });
  }
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

async function assertHashlineRendering(toolsPath: string) {
  const { runner } = await createRunner([hashlineCompactPath, toolsPath], builtInNames, false);
  const owners = new Map(
    runner.getAllRegisteredTools().map((tool: any) => [tool.definition.name, tool.sourceInfo.path]),
  );
  assert.equal(owners.get("read"), toolsPath);
  assert.equal(owners.get("replace"), toolsPath);

  const undo = runner.resolveToolRenderers("undo_last_replace", () => runner.getToolDefinition("undo_last_replace"));
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

  const replace = runner.resolveToolRenderers("replace", () => runner.getToolDefinition("replace"));
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

  const read = runner.resolveToolRenderers("read", () => runner.getToolDefinition("read"));
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
}

test("renders Hashline-shaped tools before session_start without replacing their definitions", async () => {
  await assertHashlineRendering(fixturePath);
});

test("preserves real Hashline tools and renders edge outcomes accurately", {
  skip: !existsSync(hashlinePath),
}, async () => {
  await assertHashlineRendering(hashlinePath);
});

test("resolves external tool renderers without changing schemas, metadata, or execution", async () => {
  const { runner } = await createRunner([compactPath, fixturePath], builtInNames, false);
  for (const [name, args, label] of [
    ["todo", { action: "update", id: 3 }, "todo update #3"],
    ["ffgrep", { pattern: "symbol", path: "src/" }, "ffgrep /symbol/ in src/"],
    ["fffind", { pattern: "*.ts", path: "src/" }, "fffind *.ts in src/"],
  ] as const) {
    const definition = runner.getToolDefinition(name);
    assert.equal(definition.label, `Fixture ${name}`);
    assert.equal(definition.description, `Original ${name} execution`);
    assert.deepEqual(definition.parameters.properties, { value: { type: "string" } });
    assert.deepEqual(definition.parameters.required, ["value"]);
    assert.equal(definition.exposure, "deferred");
    assert.deepEqual(definition.annotations, { readOnlyHint: true });
    assert.equal(definition.renderShell, "default");
    assert.equal(definition.renderCall().render(100).join("\n").trimEnd(), "original call");
    const result = await definition.execute("1", { value: "original" }, undefined, undefined, runner.createContext());
    assert.equal(result.content[0].text, `${name}: original execution`);

    const renderers = runner.resolveToolRenderers(name, () => definition);
    assert.equal(renderers.renderShell, "self");
    assert.equal(runner.resolveToolRenderers(name, () => undefined).renderShell, "self");
    const context = renderContext();
    assert.equal(renderers.renderCall(args, theme, context).render(100).join("\n").trimEnd(), label);
    assert.deepEqual(renderers.renderResult(result, { expanded: false, isPartial: false }, theme, context).render(100), []);
    assert.match(
      renderers.renderResult(result, { expanded: true, isPartial: false }, theme, context).render(100).join("\n"),
      /original execution/,
    );
  }
});

test("delegates unrelated tools to later resolvers and base renderers", async () => {
  const { runner } = await createRunner([compactPath, fixturePath], builtInNames, false);
  const definition = runner.getToolDefinition("unrelated");
  assert.equal(runner.resolveToolRenderers("unrelated", () => definition), definition);
  assert.equal(runner.resolveToolRenderers("unregistered", () => undefined), undefined);
  assert.deepEqual(runner.resolveToolRenderers("fixture_fallback", () => undefined), { renderShell: "default" });
  const fallback = { renderShell: "default" };
  assert.equal(runner.resolveToolRenderers("toString", () => fallback), fallback);

  const { runner: hashlineRunner } = await createRunner([hashlineCompactPath, fixturePath], builtInNames, false);
  assert.equal(hashlineRunner.resolveToolRenderers("unrelated", () => definition), definition);
  assert.equal(hashlineRunner.resolveToolRenderers("unregistered", () => undefined), undefined);
  assert.deepEqual(hashlineRunner.resolveToolRenderers("fixture_fallback", () => undefined), { renderShell: "default" });
});

test("registers built-in file wrappers before session_start for reload", async () => {
  const { runner } = await createRunner([compactPath], builtInNames, false);

  for (const name of ["read", "edit", "write"]) {
    const tool = runner.getToolDefinition(name);
    assert(tool, `${name} must be registered during extension load`);
    assert.equal(tool.renderShell, "self");
  }

  const read = runner.getToolDefinition("read");
  const context = renderContext();
  const collapsed = read.renderResult(
    { content: [{ type: "text", text: "restored output" }], details: {} },
    { expanded: false, isPartial: false },
    theme,
    context,
  );
  assert.deepEqual(collapsed.render(100), []);
});
