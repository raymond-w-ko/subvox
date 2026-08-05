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
 * renderCall/renderResult. MCP/3rd-party tools are decorated by wrapping
 * pi.registerTool.
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
  write: "success",
  bash: "bashMode",
  "$": "bashMode",
};

const callLine = (theme: any, name: string, rest: string): Text =>
  new Text(
    `${theme.fg(NAME_COLOR[name] ?? "toolTitle", theme.bold(name))} ${rest}`,
    0,
    0,
  );

/** Collapsed renderResult → nothing (keeps tool block to a single line). */
const collapsedNone = (theme: any): Text => new Text("", 0, 0);

// --- read ---
function renderReadCall(args: any, theme: any): Text {
  const path = shortenPath(args.path);
  let suffix = "";
  if (args.offset !== undefined || args.limit !== undefined) {
    const from = args.offset ?? 1;
    const to = args.limit !== undefined ? from + args.limit - 1 : undefined;
    suffix = to ? `:${from}-${to}` : `:${from}`;
  }
  const pathColored = theme.fg("accent", path || "...");
  const suffixColored = suffix ? theme.fg("warning", suffix) : "";
  return callLine(theme, "read", pathColored + suffixColored);
}

function renderReadResult(result: any, { expanded, isPartial }: any, theme: any): Text {
  if (isPartial) return running(theme, "reading");
  const details = result.details as ReadToolDetails | undefined;
  if (details?.truncation?.truncated) {
    return new Text(theme.fg("warning", `(truncated from ${details.truncation.totalLines} lines)`), 0, 0);
  }
  if (!expanded) return collapsedNone(theme);
  return fullOutput(result, theme);
}

// --- grep / find / ls ---
function renderSearchCall(theme: any, name: string, pattern: string, scope: string, extra = ""): Text {
  // Pattern neutral so the colored name (accent) doesn't collide with it.
  let rest = theme.fg("text", pattern) + theme.fg("dim", ` in ${scope}`);
  if (extra) rest += theme.fg("dim", extra);
  return callLine(theme, name, rest);
}

function getScope(args: any): string {
  const p = shortenPath(args.path);
  return p || ".";
}

function renderSearchResult(result: any, { expanded, isPartial }: any, theme: any, label: string): Text {
  if (isPartial) return running(theme, label);
  if (!expanded) return collapsedNone(theme);
  return fullOutput(result, theme);
}

// --- bash ---
function renderBashCall(args: any, theme: any, context?: any): Text {
  const cmd = String(args.command || "");
  const timeout = args.timeout ? theme.fg("dim", ` (${args.timeout}s)`) : "";

  // Retroactive translation: show the raw command now, swap in a short
  // human label once a cheap background LLM call returns.
  const st = context?.state ?? {};
  if (st.translation) {
    return callLine(theme, "$", theme.fg("success", st.translation) + timeout);
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
  return callLine(theme, "$", theme.fg("accent", shown) + timeout);
}

function renderBashResult(result: any, { expanded, isPartial }: any, theme: any): Text {
  if (isPartial) return running(theme, "$");
  const output = getText(result);
  const details = result.details as BashToolDetails | undefined;
  // Surface errors even when collapsed.
  if (!expanded) {
    const firstLine = output.split("\n")[0];
    if (/error|command not found|no such file|exit code: [1-9]/i.test(firstLine || "")) {
      return new Text(theme.fg("error", firstLine?.slice(0, 200) || "failed"), 0, 0);
    }
    return collapsedNone(theme);
  }
  return fullOutput(result, theme);
}

// --- edit ---
// pi renders the call and result as separate vertical rows, so a standalone
// result line costs a second row. To compact, fold the success/error status
// onto the CALL line: the result renderer caches the status in module scope
// and nudges one extra render (guarded so it can't loop) for the call line to
// pick it up. Reset to null when a new edit starts so a stale status never
// leaks across calls.
let editStatus: { kind: "ok" | "err" } | null = null;

function renderEditCall(args: any, theme: any): Text {
  const path = shortenPath(args.path);
  const n = Array.isArray(args.edits) ? args.edits.length : args.oldText ? 1 : 0;
  const count = theme.fg("dim", ` (${n} edit${n === 1 ? "" : "s"})`);
  const status = editStatus
    ? editStatus.kind === "ok"
      ? theme.fg("success", " applied")
      : theme.fg("error", " failed")
    : "";
  return callLine(theme, "edit", theme.fg("accent", path || "...") + count + status);
}

function renderEditResult(result: any, { expanded, isPartial }: any, theme: any, ctx?: any): Text {
  if (isPartial) return running(theme, "editing");
  const content = getText(result);
  const isError = (content || "").startsWith("Error");
  const details = result.details as EditToolDetails | undefined;

  // Fold status into the call line (handled regardless of expanded state; the
  // expanded view shows diff/content as its own block below).
  const kind: "ok" | "err" | null = isError ? "err" : details?.diff ? "ok" : null;
  if (kind !== (editStatus?.kind ?? null)) {
    editStatus = kind ? { kind } : null;
    try {
      ctx?.invalidate?.();
    } catch {
      /* component may be gone */
    }
  }

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

// --- write ---
function renderWriteCall(args: any, theme: any): Text {
  const path = shortenPath(args.path);
  const lines = (args.content || "").split("\n").length;
  const count = theme.fg("dim", ` (${lines} lines)`);
  return callLine(theme, "write", theme.fg("accent", path || "...") + count);
}

function renderWriteResult(result: any, { expanded, isPartial }: any, theme: any): Text {
  if (isPartial) return running(theme, "writing");
  const content = getText(result);
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
  onExecuteStart?: (params: any) => void,
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
      onExecuteStart?.(params);
      return getBuiltIns(ctx.cwd)[name].execute(toolCallId, params as any, signal, onUpdate);
    },
    renderCall: renderers.renderCall as any,
    renderResult: renderers.renderResult as any,
  } as unknown as ToolDefinition);
}

/**
 * Decorates a non-built-in tool (MCP, custom) with a one-line renderer.
 * Mutates the already-registered tool object so the live TUI picks it up.
 */
function decorateGenericTool(pi: ExtensionAPI, tool: any, name: string): void {
  const wrappedNames = new Set<string>();

  const apply = (t: any): void => {
    if (!t || typeof t !== "object") return;
    const n = typeof t.name === "string" ? t.name : undefined;
    if (!n || wrappedNames.has(n)) return;
    // Never clobber our own built-in overrides.
    const own = ["read", "grep", "find", "ls", "bash", "edit", "write"];
    if (own.includes(n)) return;
    if (typeof t.renderCall === "function" && typeof t.renderResult === "function") return;

    const label = typeof t.label === "string" ? t.label : n;
    t.renderCall = (args: any, theme: any) =>
      callLine(theme, label, theme.fg("accent", summarizeArgs(args)));
    t.renderResult = (result: any, { expanded, isPartial }: any, theme: any) => {
      if (isPartial) return running(theme, label);
      if (!expanded) return collapsedNone(theme);
      return fullOutput(result, theme);
    };
    wrappedNames.add(n);
  };

  // Intercept future registrations.
  const original = pi.registerTool.bind(pi);
  (pi as any).registerTool = (def: any) => {
    original(def);
    try {
      apply(def);
    } catch {
      /* ignore */
    }
  };

  // Decorate tools already registered.
  try {
    const all = pi.getAllTools() as any[];
    if (Array.isArray(all)) for (const t of all) apply(t);
  } catch {
    /* ignore */
  }

  if (tool && typeof tool === "object") apply(tool);
}

function summarizeArgs(args: any): string {
  if (!args || typeof args !== "object") return "";
  const keys = Object.keys(args);
  if (keys.length === 0) return "";
  const first = keys[0];
  const v = args[first];
  const val = typeof v === "string" ? v : JSON.stringify(v);
  return `${first}=${val}`.slice(0, 100);
}

// ============================================================================
// Entry
// ============================================================================

export default function (pi: ExtensionAPI): void {
  // Route one-shot completions through Pi's own provider/auth stack.
  captureModelApi(pi);

  registerBuiltin(pi, "read", { renderCall: renderReadCall, renderResult: renderReadResult });
  registerBuiltin(pi, "grep", {
    renderCall: (a, t) => renderSearchCall(t, "grep", `/${a.pattern}/`, getScope(a)),
    renderResult: (r, o, t) => renderSearchResult(r, o, t, "grep"),
  });
  registerBuiltin(pi, "find", {
    renderCall: (a, t) => renderSearchCall(t, "find", a.pattern, getScope(a), a.limit !== undefined ? ` (limit ${a.limit})` : ""),
    renderResult: (r, o, t) => renderSearchResult(r, o, t, "find"),
  });
  registerBuiltin(pi, "ls", {
    renderCall: (a, t) => renderSearchCall(t, "ls", getScope(a), "", a.limit !== undefined ? ` (limit ${a.limit})` : ""),
    renderResult: (r, o, t) => renderSearchResult(r, o, t, "ls"),
  });
  registerBuiltin(pi, "bash", { renderCall: renderBashCall, renderResult: renderBashResult });
  registerBuiltin(pi, "edit", { renderCall: renderEditCall, renderResult: renderEditResult }, () => {
    editStatus = null;
  });
  registerBuiltin(pi, "write", { renderCall: renderWriteCall, renderResult: renderWriteResult });

  // Generic/MCP tools → one line too.
  decorateGenericTool(pi, undefined, "generic");
}
