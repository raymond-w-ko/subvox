/**
 * rko-compact-tool-display
 *
 * Codex-GUI-style tool rendering for Pi.
 *
 * Live TUI:
 *   - Every tool call renders as ONE line (the invocation: `read path`,
 *     `$ cmd`, `edit path`, ...).
 *   - Collapsed tool results render NOTHING extra (single line total).
 *   - Press `ctrl+o` (app.tools.expand) to expand a tool's full output.
 *   - Thinking blocks and normal assistant messages are rendered by Pi's own
 *     AssistantMessageComponent (Markdown) and are left untouched — they stay
 *     full/multiline.
 *
 * Transcript / HTML export (`/export`):
 *   - Pi's export-html renderer invokes renderResult twice (collapsed and
 *     expanded) and stores both, so exported transcripts show the FULL output
 *     even though the live TUI collapses to one line.
 *
 * Mechanism: re-register built-in tools with the same name (delegating
 * execute() to the originals via create*Tool(cwd)), supplying custom
 * renderCall/renderResult. When pi-hashline-edit-pro is loaded, keep its
 * read/replace/undo execution intact through Pi's renderer-only override API
 * and only wrap built-in write; otherwise wrap built-in read/edit/write.
 */

import type {
  BashToolDetails,
  EditToolDetails,
  ExtensionAPI,
  ReadToolDetails,
  ToolDefinition,
} from "@earendil-works/pi-coding-agent";
import {
  createBashTool,
  createEditTool,
  createFindTool,
  createGrepTool,
  createLsTool,
  createReadTool,
  createWriteTool,
} from "@earendil-works/pi-coding-agent";
import { Text } from "@earendil-works/pi-tui";
import { homedir } from "os";
import { captureModelApi } from "./llm.js";
import { translateCommand } from "./translate.js";

// ============================================================================
// Small helpers
// ============================================================================

function shortenPath(p: string | undefined): string {
  if (!p) return "";
  const home = homedir();
  return p.startsWith(home) ? `~${p.slice(home.length)}` : p;
}

/** Extract the concatenated text from a tool result's content blocks. */
function getText(result: any): string {
  const blocks = Array.isArray(result?.content) ? result.content : [];
  return blocks
    .filter((b: any) => b && b.type === "text" && typeof b.text === "string")
    .map((b: any) => b.text)
    .join("\n");
}

/** Full output, trimmed of trailing blank lines, no tool box framing. */
function fullOutput(result: any, theme: any): Text {
  const text = getText(result).replace(/\r/g, "").trimEnd();
  if (!text) return new Text("", 0, 0);
  const lines = text.split("\n").map((l) => theme.fg("toolOutput", l));
  // paddingX=1 indent, paddingY=0 so no vertical blank rows.
  return new Text(lines.join("\n"), 1, 0);
}

const running = (theme: any, label: string) =>
  new Text(theme.fg("dim", `${label}…`), 0, 0);

// ============================================================================
// Built-in tool cache (per-cwd) so execute() delegates to originals
// ============================================================================

const toolCache = new Map<string, ReturnType<typeof createBuiltIns>>();

function createBuiltIns(cwd: string) {
  return {
    read: createReadTool(cwd),
    grep: createGrepTool(cwd),
    find: createFindTool(cwd),
    ls: createLsTool(cwd),
    bash: createBashTool(cwd),
    edit: createEditTool(cwd),
    write: createWriteTool(cwd),
  };
}

function getBuiltIns(cwd: string) {
  let tools = toolCache.get(cwd);
  if (!tools) {
    tools = createBuiltIns(cwd);
    toolCache.set(cwd, tools);
  }
  return tools;
}

// ============================================================================
// One-line renderers
// ============================================================================

/**
 * Tasteful per-tool name colors (all real pi theme keys). Content stays
 * accent/dim so the NAME carries the per-tool hue and reads at a glance.
 */
const NAME_COLOR: Record<string, string> = {
  read: "toolTitle",
  grep: "accent",
  find: "accent",
  ls: "accent",
  edit: "warning",
  replace: "warning",
  undo: "warning",
  write: "success",
  bash: "bashMode",
  "$": "bashMode",
  todo: "warning",
  ffgrep: "accent",
  fffind: "accent",
};

const callLine = (theme: any, name: string, rest: string, bg?: (l: string) => string): Text =>
  new Text(
    `${theme.fg(NAME_COLOR[name] ?? "toolTitle", theme.bold(name))} ${rest}`,
    0,
    0,
    bg,
  );

// --- status-colored background (replicates the original tool box) -----------
// The original paints the whole tool block with a background that flips
// pending -> success/error. pi only auto-fills a full row when the Text has a
// customBgFn (4th arg), so each call line carries one. Status must live in
// context.state: it belongs to one tool row, not every row sharing a tool name.
type ToolStatus = "pending" | "ok" | "err";

function statusBg(theme: any, ctx: any): ((l: string) => string) | undefined {
  const status: ToolStatus = ctx?.state?.compactToolStatus ?? "pending";
  const key = status === "pending" ? "toolPendingBg" : status === "ok" ? "toolSuccessBg" : "toolErrorBg";
  return (l: string) => theme.bg(key, l);
}

function setToolStatus(status: ToolStatus, ctx: any): void {
  const state = ctx?.state;
  if (!state || state.compactToolStatus === status) return;

  state.compactToolStatus = status;
  if (state.compactToolStatusInvalidationQueued) return;
  state.compactToolStatusInvalidationQueued = true;

  // renderResult runs after renderCall. Defer one row-local invalidation so the
  // call line can pick up the final status without re-entering updateDisplay().
  queueMicrotask(() => {
    state.compactToolStatusInvalidationQueued = false;
    try {
      ctx?.invalidate?.();
    } catch {
      /* component may be gone */
    }
  });
}

function beginRenderedCall(ctx: any): void {
  const state = ctx?.state;
  if (!state || state.compactToolInitialized) return;
  state.compactToolInitialized = true;
  state.compactToolStatus = "pending";
}

function resultIsError(name: string, content: string, details: any): boolean {
  if (name === "bash") {
    // Real failures end with a status line (or an explicit Error) — never by
    // word-matching arbitrary output (a successful grep containing "isError"
    // must not be treated as a failed command).
    return (
      /Command exited with code [1-9]\d*|Command timed out|Command aborted/.test(content || "") ||
      /^Error:/m.test(content || "")
    );
  }
  if (name === "edit" || name === "write") {
    return (content || "").startsWith("Error");
  }
  const first = (content || "").split("\n")[0].trim();
  return (
    first.length > 0 &&
    first.length < 200 &&
    /^(error|could not|cannot|no such|permission denied|command not found|failed|eof)/i.test(first)
  );
}

/** Collapsed renderResult → nothing (keeps tool block to a single line). */
const collapsedNone = (theme: any): Text => new Text("", 0, 0);

// --- read ---
function renderReadCall(args: any, theme: any, ctx?: any): Text {
  beginRenderedCall(ctx);
  const path = shortenPath(args.path);
  let suffix = "";
  if (args.offset !== undefined || args.limit !== undefined) {
    const from = args.offset ?? 1;
    const to = args.limit !== undefined ? from + args.limit - 1 : undefined;
    suffix = to ? `:${from}-${to}` : `:${from}`;
  }
  const pathColored = theme.fg("accent", path || "...");
  const suffixColored = suffix ? theme.fg("warning", suffix) : "";
  return callLine(theme, "read", pathColored + suffixColored, statusBg(theme, ctx));
}

function renderReadResult(result: any, { expanded, isPartial }: any, theme: any, ctx?: any): Text {
  if (isPartial) return running(theme, "reading");
  const details = result.details as ReadToolDetails | undefined;
  setToolStatus(resultIsError("read", getText(result), undefined) ? "err" : "ok", ctx);
  if (details?.truncation?.truncated) {
    return new Text(theme.fg("warning", `(truncated from ${details.truncation.totalLines} lines)`), 0, 0);
  }
  if (!expanded) return collapsedNone(theme);
  return fullOutput(result, theme);
}

// --- grep / find / ls ---
function renderSearchCall(theme: any, name: string, pattern: string, scope: string, extra = "", ctx?: any): Text {
  beginRenderedCall(ctx);
  // Pattern neutral so the colored name (accent) doesn't collide with it.
  let rest = theme.fg("text", pattern) + theme.fg("dim", ` in ${scope}`);
  if (extra) rest += theme.fg("dim", extra);
  return callLine(theme, name, rest, statusBg(theme, ctx));
}

function getScope(args: any): string {
  const p = shortenPath(args.path);
  return p || ".";
}

function renderSearchResult(result: any, { expanded, isPartial }: any, theme: any, label: string, ctx?: any): Text {
  if (isPartial) return running(theme, label);
  setToolStatus(ctx?.isError || resultIsError(label, getText(result), result.details) ? "err" : "ok", ctx);
  if (!expanded) return collapsedNone(theme);
  return fullOutput(result, theme);
}

// --- external tools ---
function renderTodoCall(args: any, theme: any, context?: any): Text {
  beginRenderedCall(context);
  const action = String(args.action || "...");
  let detail = "";
  if (args.id !== undefined) detail += ` #${args.id}`;
  if (typeof args.subject === "string" && args.subject) detail += ` ${args.subject}`;
  if (typeof args.status === "string" && args.status) detail += ` ${args.status}`;
  return callLine(
    theme,
    "todo",
    theme.fg("accent", action) + theme.fg("dim", detail),
    statusBg(theme, context),
  );
}

function renderTodoResult(result: any, { expanded, isPartial }: any, theme: any, context?: any): Text {
  if (isPartial) return running(theme, "todo");
  const content = getText(result);
  const isError = Boolean(context?.isError || result.details?.error || resultIsError("todo", content, result.details));
  setToolStatus(isError ? "err" : "ok", context);
  if (!expanded) return collapsedNone(theme);
  return fullOutput(result, theme);
}

function registerExternalRenderers(pi: ExtensionAPI): void {
  pi.registerToolRenderer("todo", {
    renderShell: "self",
    renderCall: renderTodoCall,
    renderResult: renderTodoResult,
  });
  pi.registerToolRenderer("ffgrep", {
    renderShell: "self",
    renderCall: (args: any, theme: any, context?: any) => {
      const extra = args.limit !== undefined ? ` (limit ${args.limit})` : args.cursor ? " (page)" : "";
      return renderSearchCall(theme, "ffgrep", `/${args.pattern || ""}/`, getScope(args), extra, context);
    },
    renderResult: (result: any, options: any, theme: any, context?: any) =>
      renderSearchResult(result, options, theme, "ffgrep", context),
  });
  pi.registerToolRenderer("fffind", {
    renderShell: "self",
    renderCall: (args: any, theme: any, context?: any) => {
      const extra = args.limit !== undefined ? ` (limit ${args.limit})` : args.cursor ? " (page)" : "";
      return renderSearchCall(theme, "fffind", args.pattern || "", getScope(args), extra, context);
    },
    renderResult: (result: any, options: any, theme: any, context?: any) =>
      renderSearchResult(result, options, theme, "fffind", context),
  });
}

// --- bash ---
function renderBashCall(args: any, theme: any, context?: any): Text {
  beginRenderedCall(context);
  const cmd = String(args.command || "");
  const timeout = args.timeout ? theme.fg("dim", ` (${args.timeout}s)`) : "";

  // Expanded: show the original command again (instead of the translated
  // label), unwrapped so the full command is visible under ctrl+o.
  if (context?.expanded) {
    return callLine(theme, "$", theme.fg("accent", cmd) + timeout, statusBg(theme, context));
  }

  // Retroactive translation: show the raw command now, swap in a short
  // human label once a cheap background LLM call returns.
  const st = context?.state ?? {};
  if (st.translation) {
    return callLine(theme, "$", theme.fg("success", st.translation) + timeout, statusBg(theme, context));
  }
  // Retroactive translation: show raw now, swap in a short human label once a
  // cheap background LLM call returns. Commands stream in over several renders,
  // so debounce: fire only after the command stops changing (~250ms). Firing on
  // an early partial (e.g. just `cd ~/s`) would lock translationDone and leave
  // the full pipeline command untranslated forever.
  const trimmed = cmd.trim();
  if (!st.translationDone && trimmed.length >= 4) {
    if (trimmed !== st.lastCmd) {
      st.lastCmd = trimmed;
      if (st.timer) clearTimeout(st.timer);
      const invalidate = context?.invalidate;
      st.timer = setTimeout(() => {
        st.translationDone = true;
        translateCommand(st.lastCmd)
          .then((label) => {
            if (label) {
              st.translation = label;
              try {
                invalidate?.();
              } catch {
                /* component may be gone */
              }
            }
          })
          .catch(() => {});
      }, 250);
    }
  }

  const shown = cmd.length > 100 ? `${cmd.slice(0, 97)}…` : cmd;
  return callLine(theme, "$", theme.fg("accent", shown) + timeout, statusBg(theme, context));
}

function renderBashResult(result: any, { expanded, isPartial }: any, theme: any, ctx?: any): Text {
  if (isPartial) return running(theme, "$");
  const output = getText(result);
  const details = result.details as BashToolDetails | undefined;
  setToolStatus(resultIsError("bash", output, details) ? "err" : "ok", ctx);
  // Surface real failures when collapsed. Judge only by the trailing status
  // line the tool appends on error — never by word-matching arbitrary output
  // (a successful grep whose results contain "isError" must stay success).
  if (!expanded) {
    if (resultIsError("bash", output, details)) {
      let msg = "failed";
      if (/Command timed out/.test(output)) msg = "timed out";
      else if (/Command aborted/.test(output)) msg = "aborted";
      else {
        const m = output.match(/Command exited with code (\d+)/);
        if (m) msg = `exit ${m[1]}`;
      }
      return new Text(theme.fg("error", msg), 0, 0, (l) => theme.bg("toolErrorBg", l));
    }
    return collapsedNone(theme);
  }
  return fullOutput(result, theme);
}

// --- edit ---
function renderEditCall(args: any, theme: any, ctx?: any): Text {
  beginRenderedCall(ctx);
  const path = shortenPath(args.path);
  const n = Array.isArray(args.edits) ? args.edits.length : args.oldText ? 1 : 0;
  const count = theme.fg("dim", ` (${n} edit${n === 1 ? "" : "s"})`);
  const status: ToolStatus = ctx?.state?.compactToolStatus ?? "pending";
  const word = status === "ok" ? theme.fg("success", " applied") : status === "err" ? theme.fg("error", " failed") : "";
  return callLine(theme, "edit", theme.fg("accent", path || "...") + count + word, statusBg(theme, ctx));
}

function renderEditResult(result: any, { expanded, isPartial }: any, theme: any, ctx?: any): Text {
  if (isPartial) return running(theme, "editing");
  const content = getText(result);
  const isError = (content || "").startsWith("Error");
  const details = result.details as EditToolDetails | undefined;

  // Fold status into the call line (handled regardless of expanded state; the
  // expanded view shows diff/content as its own block below).
  setToolStatus(isError ? "err" : "ok", ctx);

  if (!expanded) return collapsedNone(theme);
  if (details?.diff) {
    const lines = details.diff.split("\n").map((l) => {
      if (l.startsWith("+") && !l.startsWith("+++")) return theme.fg("success", l);
      if (l.startsWith("-") && !l.startsWith("---")) return theme.fg("error", l);
      if (l.startsWith("@@")) return theme.fg("warning", l);
      return theme.fg("dim", l);
    });
    return new Text(lines.join("\n"), 1, 0);
  }
  return fullOutput(result, theme);
}

// --- pi-hashline-edit-pro mutations ---
function renderHashlineCall(name: "replace" | "undo", args: any, theme: any, ctx?: any): Text {
  beginRenderedCall(ctx);
  const path = shortenPath(args.path ?? args.file_path);
  const status: ToolStatus = ctx?.state?.compactToolStatus ?? "pending";
  const word = status === "ok" ? theme.fg("success", " applied") : status === "err" ? theme.fg("error", " failed") : "";
  return callLine(theme, name, theme.fg("accent", path || "...") + word, statusBg(theme, ctx));
}

function renderHashlineResult(
  result: any,
  { expanded, isPartial }: any,
  theme: any,
  ctx: any,
  label: string,
): Text {
  if (isPartial) return running(theme, label);
  const content = getText(result);
  const isError = Boolean(
    ctx?.isError ||
    result?.isError ||
    result?.details?.error ||
    /^\[E_[A-Z_]+\]/.test(content) ||
    resultIsError(label, content, result?.details),
  );
  setToolStatus(isError ? "err" : "ok", ctx);

  if (!expanded) {
    if (!isError) return collapsedNone(theme);
    const firstLine = content.split("\n")[0]?.trim() || "failed";
    return new Text(theme.fg("error", firstLine), 0, 0, (line) => theme.bg("toolErrorBg", line));
  }

  const diff = result?.details?.diff;
  if (typeof diff === "string" && diff) {
    const warnings = content.match(/(?:^|\n)Warnings:\n[\s\S]*$/)?.[0]?.trimStart();
    const expandedText = warnings ? `${diff}\n\n${warnings}` : diff;
    const lines = expandedText.split("\n").map((line: string) => {
      if (line.startsWith("+") && !line.startsWith("+++")) return theme.fg("success", line);
      if (line.startsWith("-") && !line.startsWith("---")) return theme.fg("error", line);
      if (line.startsWith("@@")) return theme.fg("warning", line);
      return theme.fg("dim", line);
    });
    return new Text(lines.join("\n"), 1, 0);
  }
  return fullOutput(result, theme);
}

// --- write ---
function renderWriteCall(args: any, theme: any, ctx?: any): Text {
  beginRenderedCall(ctx);
  const path = shortenPath(args.path);
  const lines = (args.content || "").split("\n").length;
  const count = theme.fg("dim", ` (${lines} lines)`);
  return callLine(theme, "write", theme.fg("accent", path || "...") + count, statusBg(theme, ctx));
}

function renderWriteResult(result: any, { expanded, isPartial }: any, theme: any, ctx?: any): Text {
  if (isPartial) return running(theme, "writing");
  const content = getText(result);
  setToolStatus(resultIsError("write", content, undefined) ? "err" : "ok", ctx);
  if ((content || "").startsWith("Error")) {
    return new Text(theme.fg("error", content.split("\n")[0]), 0, 0);
  }
  if (!expanded) return collapsedNone(theme);
  return fullOutput(result, theme);
}

// ============================================================================
// Registration
// ============================================================================

interface RendererSet {
  renderCall?: (args: any, theme: any, ctx?: any) => Text;
  renderResult?: (result: any, options: any, theme: any, ctx?: any) => Text;
  renderShell?: "default" | "self";
}

function registerBuiltin(
  pi: ExtensionAPI,
  name: "read" | "grep" | "find" | "ls" | "bash" | "edit" | "write",
  renderers: RendererSet,
): void {
  const details = getBuiltIns(process.cwd())[name];
  pi.registerTool({
    name,
    label: name,
    description: details.description,
    parameters: details.parameters,
    prepareArguments: (details as any).prepareArguments,
    // "self" bypasses pi's Box (paddingY=1 top/bottom) and draws into a
    // plain container — no colored vertical padding rows, just a blank spacer.
    renderShell: renderers.renderShell ?? "self",
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      return getBuiltIns(ctx.cwd)[name].execute(toolCallId, params as any, signal, onUpdate);
    },
    renderCall: renderers.renderCall as any,
    renderResult: renderers.renderResult as any,
  } as unknown as ToolDefinition);
}

const HASHLINE_PACKAGE_ID = "pi-hashline-edit-pro";

function hasHashlineEditPro(pi: ExtensionAPI): boolean {
  const hashlineTools = new Set(
    pi
      .getAllTools()
      .filter((tool) => tool.sourceInfo?.source?.includes(HASHLINE_PACKAGE_ID))
      .map((tool) => tool.name),
  );
  return hashlineTools.has("read") && hashlineTools.has("replace");
}

function registerHashlineRenderers(pi: ExtensionAPI): void {
  pi.registerToolRenderer("read", {
    renderShell: "self",
    renderCall: renderReadCall,
    renderResult: renderReadResult,
  });
  pi.registerToolRenderer("replace", {
    renderShell: "self",
    renderCall: (args, theme, ctx) => renderHashlineCall("replace", args, theme, ctx),
    renderResult: (result, options, theme, ctx) =>
      renderHashlineResult(result, options, theme, ctx, "replacing"),
  });
  pi.registerToolRenderer("undo_last_replace", {
    renderShell: "self",
    renderCall: (args, theme, ctx) => renderHashlineCall("undo", args, theme, ctx),
    renderResult: (result, options, theme, ctx) =>
      renderHashlineResult(result, options, theme, ctx, "undoing"),
  });
}

function registerFileToolRenderers(pi: ExtensionAPI): void {
  if (hasHashlineEditPro(pi)) {
    registerHashlineRenderers(pi);
    // Hashline keeps Pi's built-in write tool and post-processes its result.
    registerBuiltin(pi, "write", { renderCall: renderWriteCall, renderResult: renderWriteResult });
    return;
  }

  registerBuiltin(pi, "read", { renderCall: renderReadCall, renderResult: renderReadResult });
  registerBuiltin(pi, "edit", { renderCall: renderEditCall, renderResult: renderEditResult });
  registerBuiltin(pi, "write", { renderCall: renderWriteCall, renderResult: renderWriteResult });
}

// ============================================================================
// Entry
// ============================================================================

export default function (pi: ExtensionAPI): void {
  // Route one-shot completions through Pi's own provider/auth stack.
  captureModelApi(pi);

  // All extension factories have run by session_start, so tool provenance is final.
  pi.on("session_start", () => registerFileToolRenderers(pi));

  registerBuiltin(pi, "grep", {
    renderCall: (a, t, c) => renderSearchCall(t, "grep", `/${a.pattern}/`, getScope(a), "", c),
    renderResult: (r, o, t, c) => renderSearchResult(r, o, t, "grep", c),
  });
  registerBuiltin(pi, "find", {
    renderCall: (a, t, c) =>
      renderSearchCall(t, "find", a.pattern, getScope(a), a.limit !== undefined ? ` (limit ${a.limit})` : "", c),
    renderResult: (r, o, t, c) => renderSearchResult(r, o, t, "find", c),
  });
  registerBuiltin(pi, "ls", {
    renderCall: (a, t, c) =>
      renderSearchCall(t, "ls", getScope(a), "", a.limit !== undefined ? ` (limit ${a.limit})` : "", c),
    renderResult: (r, o, t, c) => renderSearchResult(r, o, t, "ls", c),
  });
  registerBuiltin(pi, "bash", { renderCall: renderBashCall, renderResult: renderBashResult });
  registerExternalRenderers(pi);
}
