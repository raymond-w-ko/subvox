# pi-rko-compact-tool-display

Codex-GUI-style compact tool rendering for Pi.

## Effect

Live TUI:

- Every supported tool call renders as **ONE line** — the invocation (`read ~/x.ts:5-14`,
  `$ git status (30s)`, `edit /tmp/a.ts (2 edits)`, `ffgrep /symbol/ in src/`, `todo update #3`, ...).
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

Always re-registers the built-in `grep`, `find`, `ls`, and `bash` tools under the
same names via `pi.registerTool`, delegating `execute()` to the originals
(`createReadTool(cwd)` etc., cached per-cwd) so behavior is unchanged.

File tools are selected at `session_start`, after every extension factory has run:

- When `pi-hashline-edit-pro` is present, `read`, `replace`, and
  `undo_last_replace` receive renderer-only overrides through
  `pi.registerToolRenderer`, preserving Hashline schemas, metadata, and
  execution. Its `edit` disablement remains intact. Built-in `write` still gets
  the compact wrapper because Hashline does not replace that tool; it post-processes
  write results to add auto-read anchors.
- Without `pi-hashline-edit-pro`, built-in `read`, `edit`, and `write` get the
  compact wrappers.

No load-last naming trick is required. Pi allows renderer overrides before or after
their target tool, and `session_start` sees the final registered-tool provenance.

External `todo`, `ffgrep`, and `fffind` tools also receive renderer-only overrides,
preserving their original schemas, state, and execution while replacing only TUI
rendering.

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
HTTP, no env API keys. It captures the session's `ModelRegistry` (from
`session_start` / `before_agent_start` / `model_select`) and calls
`ModelRegistry.complete(model, context, options)` — the same request path pi's
agent uses — reusing the configured provider, stored credentials, base URL,
headers, and provider hooks. No `pi-ai/compat` usage.

> Requires a current pi built from `~/src/pi` main. The extension uses both
> `ModelRegistry.complete` (added after 0.83.0) and `pi.registerToolRenderer` for
> external-tool rendering.

All settings are top-level constants in **`config.ts`** (no env vars). Edit
there:

| constant | meaning |
|----------|---------|
| `CONFIG.enabled` | master switch for bash translation |
| `CONFIG.model` | model (default `openrouter/google/gemini-3.5-flash-lite`) |
| `CONFIG.thinking` | thinking level; default `low` |
| `CONFIG.debug` | write `/tmp/rko-llm.log` diagnostics |

Thinking levels: `off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`.
Note `gemini-3.5-flash-lite` (openrouter) **requires** reasoning — `off` is
forced to `low`. Also note `ModelRegistry.complete` needs `reasoningEffort` (not
just `reasoning`) because it goes through `provider.stream`.

## Cost-saving cache

Labels are deterministic (temperature 0, pinned model), so results are cached
in SQLite at `~/.cache/pi-rko-compact-tool-display.sqlite3` (see `cache.ts`, uses
`node:sqlite` — the same driver Pi's own storage uses) keyed by
`model|thinking|command`. Hits avoid the LLM call entirely — including across
`/reload` and restarts. Capped at 65536 rows (oldest dropped by `created_at`).
Only successful non-empty labels are stored. Empty/failed translations are not
cached, so a later call can retry. Delete the file to clear it.

Drains: 8s hard timeout, up to 3 attempts with 400ms / 1200ms backoff, in-flight
dedupe per command (cleared after settle), silent no-op on failure (the raw
command is already shown, so a miss costs nothing).

## Files

- `index.ts` — entry + all renderers
- `llm.ts` — Pi-native one-shot completion bridge (reuses provider/auth)
- `translate.ts` — background bash translator + in-flight dedupe
- `cache.ts` — persistent SQLite cache (`node:sqlite`, ~/.cache)
- `config.ts` — personal settings as top-level constants (KISS)
- `debug-log.ts` — /tmp diagnostics, gated by `CONFIG.debug`

> Note: translation is live-only. `state` lives in memory on the tool component;
a restored/reloaded session shows raw commands again.

## Gotchas / traps (read before changing this extension)

Hard-won lessons from building `llm.ts`/`translate.ts`. Future sessions: read
this first so you don't repeat the week of debugging.

### 1. `ctx.getModel()` does NOT exist on this pi's ExtensionContext

`typeof ctx.getModel === "undefined"` on `session_start`/`before_agent_start`.
Do **not** try to capture the active model that way — it silently never sets,
and every translation returns `""`. Use `ctx.modelRegistry.find(provider, id)`
(which is present and works) with a fallback to `registry.getAll()?.[0]`.

### 2. `Model.api` is the transport *id string*, not a stream object

On this build, `model.api` is e.g. `"openai-completions"`. Calling
`model.api.streamSimple(...)` throws (string has no method) → caught → `""` with
**no HTTP request ever sent**. The correct path is
`registry.complete(model, ctx, opts)` on the captured `ModelRegistry`.

### 3. `ModelRegistry.complete` needs `reasoningEffort`, not just `reasoning`

`complete` → `provider.stream(...)`, and request building reads
**`options.reasoningEffort`**. Only the `streamSimple` path maps
`reasoning` → `reasoningEffort`. Passing only `reasoning:"low"` silently drops it,
and openrouter ends up sending `effort:"none"` → 400. Pass **both** `reasoning`
and `reasoningEffort`.

### 4. gemini-3.5-flash-lite (openrouter) REQUIRES reasoning

`reasoning:"off"` → HTTP 400 `{"message":"Reasoning is mandatory for this
endpoint and cannot be disabled."}` — the completion returns instantly
(`stopReason:"error"`, `contentLen:0`) and the DB fills with `""`. `config.ts`
forces `off` → `low`.

### 5. Live tool args stream in — first render has empty `command`

`renderCall` fires once with `args.command === ""` before the real command
arrives. If you set your "already translated" guard on that first render, the
real command never translates (**empty-command lockout** — the #1 bug). Only
mark done / fire when `command.trim().length >= 4`.

### 6. `ModelRegistry.complete` requires a pi build newer than 0.83.0

It was added to main on **2026-07-31**, a day after the 0.83.0 tag
(2026-07-30). The live `~/pi` binary is built from `~/src/pi` via `./make.sh`
stages `binary` + `install` (installs to `~/pi`, deps embedded in the Bun
binary). If the installed binary predates that commit, `complete` is missing
and `resolveModel` can't run. Verify the build is current, or the runtime API
silently diverges from the `~/src/pi` dev checkout (which is always 296+ commits
ahead of any tag).

### 7. Commands that run before `session_start` have no captured registry

At module-load time (and on the resumed-transcript re-render flood),
`registry` is still `undefined`, so every such call fails with `""`. Empty
results are **not** written to the cache, and `translateCommand` retries up to
3 times (400ms / 1200ms backoff) so a later attempt can catch the registry
once `session_start` has fired. Older builds did persist `""` as a
known-failure; leftover empty rows are treated as cache misses. If you bump
the request/key scheme, bump `CACHE_VERSION` in `translate.ts` (or delete
`~/.cache/pi-rko-compact-tool-display.sqlite3`) so stale successful labels are
not reused.

### 8. Beware writing weird disk state: `:/ > file` truncates to 0 bytes

If a log file ever shows the literal text of an earlier `cat`/heredoc instead
of fresh lines, your shell command truncated a file it didn't create (`:` is a
no-op, so `: > file` empties it). Recreate/clear explicitly.

### 9. `~/.pi` is symlinked into the git repo

`~/.pi` realpaths to `~/subvox/home/.pi`. Editing `~/.pi/agent/extensions/…`
edits the tracked repo — don't be surprised when `git status` in `~/subvox`
shows your extension changes.

### 10. Translation fires on EVERY bash call in the session

Because the extension overrides the `bash` tool, any bash invocation — including
the agent's own tool calls — goes through `translateCommand` and lands in the
cache/DB. That's expected; just don't read a populated DB as proof of a bug.

### Debug loop that actually worked

When a translation silently fails (`""` everywhere), the fastest path is:
1. Turn `CONFIG.debug` back on, `/reload`, run one simple bash command.
2. Read `/tmp/rko-llm.log`; look for `resolveModel:` (model found?), then
   `oneShot: calling registry.complete … THINKING=…`, then the `complete
   resolved … stopReason=… errorMessage=… contentTypes=…` line.
   - `stopReason="error"` + `contentLen=0` = the request was rejected (read
     `errorMessage`).
   - no `find`/`complete` lines = the capture or the empty-command guard is the
     problem. Reset `CONFIG.debug` to `false` when done.
