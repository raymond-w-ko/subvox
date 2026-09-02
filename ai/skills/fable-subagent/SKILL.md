---
name: fable-subagent
description: Delegate a scoped code review or targeted debugging problem to Claude Fable 5 through non-interactive `claude -p`, then independently validate its findings. Use when the user says "use fable subagent", "fable agent review", asks Fable for a second opinion on a diff, or wants Fable 5 to investigate a specific bug or issue.
---

# Fable Subagent

Use Claude Fable 5 as a read-only peer by default. Keep Codex responsible for scope, validation, and final reporting.

## Workflow

1. Define a bounded task: exact diff/base, files, symptom, constraints, and desired output.
2. Check worktree state. Do not let Fable edit unless the user explicitly requested implementation.
3. When collaboration tools exist, spawn one subagent to operate `claude -p`; keep the main agent available for validation.
4. Skip all preflight calls unless the user explicitly requests an exact diagnostic. Otherwise, do not check authentication, smoke-test inference, run `claude mcp get fff`, or probe `fff` separately. Assume the configured CLI, authentication, and tools work.
5. Run one substantive review with no timeout. Capture stdout, stderr, exit code, and session ID when JSON output is used.
6. Independently verify every finding against code and tests. Discard speculative or stylistic findings.
7. Report validated findings first. Separately report invocation failures using evidence from the substantive call only.

## Invocation

Pass exact model ID `--model claude-fable-5-1` on every call. Never use floating aliases such as `fable` and never fall back to another model. If Claude Fable 5.1 is unavailable, report the failure.

Do not make a warm-up, authentication, MCP, or smoke-test call unless the user explicitly requests that exact diagnostic. Fable 5 tokens are expensive. Spend them only on the requested task.

Prefer read-only repository tools for contextual review:

```text
claude -p --model claude-fable-5-1 --permission-mode=dontAsk --tools="Read,Grep,Glob,mcp__fff__find_files,mcp__fff__grep,mcp__fff__multi_grep" --allowedTools="Read,Grep,Glob,mcp__fff__find_files,mcp__fff__grep,mcp__fff__multi_grep" --output-format json "<self-contained review or debugging prompt>"
```

Expose `fff` only as part of the substantive task. Do not call it beforehand to confirm connectivity unless the user explicitly requests that exact diagnostic. Prefer `mcp__fff__grep`, `mcp__fff__find_files`, or `mcp__fff__multi_grep`; use built-in `Grep` or `Glob` when `fff` is unavailable or cannot express the search. Use `Read` only for identified files. `--tools` exposes the tools; matching `--allowedTools` grants non-interactive permission. Both flags are required for unattended `claude -p` calls.

For a supplied diff that needs no repository access, disable tools and pipe the diff:

```text
git diff <base>...HEAD | claude -p --model claude-fable-5-1 --permission-mode=dontAsk --tools="" --output-format json "Review the diff from stdin. Report only concrete correctness, safety, or regression issues."
```

Use `=` with variadic flags such as `--tools`, `--allowedTools`, and `--add-dir`; otherwise they may consume the prompt. For input larger than the CLI stdin limit, let Fable read named files instead of piping everything.

Pass `--permission-mode=dontAsk` on every review-only call so only tools explicitly granted through `--allowedTools` can run. Do not grant `Edit`, `Write`, or unrestricted `Bash`. If implementation is explicitly requested, authorize the smallest required tool set and permission mode, then review Fable's diff before keeping it.

## Prompt Shape

For code review, include:

- base and head or exact diff scope;
- surrounding files Fable should inspect;
- project constraints and relevant tests;
- request for actionable findings only, sorted by severity;
- required evidence: path, line, failure scenario, and suggested fix;
- instruction to say `no findings` instead of inventing concerns.

For a targeted problem, include the observed symptom, reproduction, expected behavior, suspected area without asserting a cause, and commands Fable may safely run. Ask for root cause plus a minimal proof or test.

If a broad review says `no findings` but risk remains, independently inspect the risky boundary first. Make a targeted Fable follow-up only when the expected value outweighs its token cost or the user requests it. Use the returned session ID or a fresh prompt focused on concrete boundaries such as retries, live state, error paths, concurrency, or partial completion. Do not lead Fable toward a predetermined answer.

## Failure Handling

- Do not run diagnostic inference, authentication, MCP, or `fff` probes after a failure unless the user explicitly requests that exact diagnostic.
- Diagnose from the substantive call's stdout, stderr, and exit code. Never print tokens or dump the full environment.
- If `fff` fails during the substantive call, use built-in `Grep` or `Glob` and report the fallback.
- Do not retry a token-spending invocation unless the user requests it.
- Disable timeouts. Let Fable run until completion or explicit user cancellation; never terminate it because elapsed time exceeds a limit.
- Treat silence as normal because text/JSON mode may emit nothing until completion.

Fable output is evidence to investigate, never authority. Reproduce bugs, inspect exact lines, and run focused local tests before presenting findings or changing code.
