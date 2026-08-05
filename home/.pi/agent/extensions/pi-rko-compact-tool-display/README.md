# pi-rko-compact-tool-display

Codex-GUI-style compact tool rendering for Pi.

## Effect

Live TUI:

- Every tool call renders as **ONE line** — the invocation (`read ~/x.ts:5-14`,
  `$ git status (30s)`, `edit /tmp/a.ts (2 edits)`, `write /tmp/b.ts (N lines)`, ...).
- Collapsed tool **results render nothing** extra, so each tool block stays a
  single line (errors still surface collapsed).
- Press `ctrl+o` (`app.tools.expand`) to reveal a tool's full output inline.
- **Thinking blocks and normal assistant messages are untouched** — they render
  as full, multi-line Markdown (Pi's own `AssistantMessageComponent`).

Transcript / HTML export:

- Pi's export-html renderer invokes `renderResult` both collapsed and expanded
  and stores both, so `/export` transcripts show the **full** output even
  though the live view is collapsed.

## How it works

Re-registers the built-in tools (`read`, `grep`, `find`, `ls`, `bash`, `edit`,
`write`) under the same name via `pi.registerTool`, delegating `execute()` to
the originals (`createReadTool(cwd)` etc., cached per-cwd) so behavior is
unchanged, and supplies custom `renderCall` / `renderResult`.

MCP / 3rd-party tools get a one-line renderer by wrapping `pi.registerTool` and
decorating `pi.getAllTools()`.

No `npm install` needed — Pi's jiti loader provides `@earendil-works/pi-*` as
virtual modules.

## Install

Already dropped in `~/.pi/agent/extensions/` (auto-discovered). Restart pi or run
`/reload`.

## Typecheck

```
npm i -D typescript @types/node   # optional, only to typecheck
npx tsc -p tsconfig.json
```

(tsconfig points `node_modules` symlink at `~/src/pi/node_modules` for types.)

## Config

None required for one-line collapse. Optional: retroactive bash translation.

### Bash command → human-readable label

When a background LLM call returns, the rendered `$ <command>` line is
**retroactively replaced** by a short plain-English label. Pi supports this via
the tool render context: `state` (persistent per tool row) + `invalidate()`
(redraw that row → `renderCall` re-runs with the new label).

Completions run through **Pi's own provider/auth stack** (see `llm.ts`) — no raw
HTTP, no env API keys. It captures the session's bound `Model` (from
`ctx.getModel()` on `session_start` / `before_agent_start` / `model_select`) and
calls `model.api.streamSimple(...)`, reusing the configured provider, stored
credentials, base URL, headers, and provider hooks.

Model is **hardcoded** to `openrouter / google/gemini-3.5-flash-lite` (resolved
via `modelRegistry.find`, still reusing Pi's openrouter auth).

Env:

| var | meaning |
|-----|---------|
| `RKO_TRANSLATE_MODEL` | optional `provider/id` override; default `openrouter/google/gemini-3.5-flash-lite` |
| `RKO_TRANSLATE_THINKING` | optional thinking level; default `off` |
| `RKO_BASH_TRANSLATOR` | `1` (default) enable, `0` disable |

Thinking levels (`reasoning` option): `off`, `minimal`, `low`, `medium`,
`high`, `xhigh`, `max`. Higher = better labels, slower/more tokens; `off` =
fastest/cheapest.

## Cost-saving cache

Labels are deterministic (temperature 0, pinned model), so results are cached
in SQLite at `~/.cache/pi-rko-compact-tool-display.sqlite` (see `cache.ts`, uses
`node:sqlite` — the same driver Pi's own storage uses) keyed by
`model|thinking|command`. Hits avoid the LLM call entirely — including across
`/reload` and restarts. Capped at 500 rows (oldest dropped by `created_at`).
Failed translations are stored as `""` so they're not retried. Delete the file
to clear it.

Drains: 4s hard timeout, deduped per command, silent no-op on failure (the raw
command is already shown, so a miss costs nothing).

## Files

- `index.ts` — entry + all renderers
- `llm.ts` — Pi-native one-shot completion bridge (reuses provider/auth)
- `translate.ts` — background bash translator + in-flight dedupe
- `cache.ts` — persistent SQLite cache (`node:sqlite`, ~/.cache)

> Note: translation is live-only. `state` lives in memory on the tool component;
a restored/reloaded session shows raw commands again.
