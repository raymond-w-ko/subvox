---
name: claude-subagent
description: Delegate a scoped code review or targeted debugging problem to Claude Code through non-interactive `claude -p`, then independently validate its findings. Use when the user says "use claude subagent", "claude agent review", asks Claude for a second opinion on a diff, or wants Claude to investigate a specific bug or issue.
---

# Claude Subagent

Use Claude as a read-only peer by default. Keep Codex responsible for scope, validation, and final reporting.

## Workflow

1. Define a bounded task: exact diff/base, files, symptom, constraints, and desired output.
2. Check worktree state. Do not let Claude edit unless the user explicitly requested implementation.
3. When collaboration tools exist, spawn one subagent to operate `claude -p`; keep the main agent available for validation.
4. Run a short authenticated smoke call with a firm timeout. `claude auth status` alone does not prove inference works.
5. Run the review with a task-sized timeout. Capture stdout, stderr, exit code, and session ID when JSON output is used.
6. Independently verify every finding against code and tests. Discard speculative or stylistic findings.
7. Report validated findings first. Separately report Claude authentication, timeout, or startup failures.

## Invocation

Pass `--model opus` on every call by default. Use another model only when the user requests it or Opus is unavailable; report any fallback.

Smoke-test real inference before a long run:

```text
claude -p --model opus --tools="" "Reply exactly OK"
```

Prefer read-only repository tools for contextual review:

```text
claude -p --model opus --tools="Read,Grep,Glob" --output-format json "<self-contained review or debugging prompt>"
```

For a supplied diff that needs no repository access, disable tools and pipe the diff:

```text
git diff <base>...HEAD | claude -p --model opus --tools="" --output-format json "Review the diff from stdin. Report only concrete correctness, safety, or regression issues."
```

Use `=` with variadic flags such as `--tools`, `--allowedTools`, and `--add-dir`; otherwise they may consume the prompt. For input larger than the CLI stdin limit, let Claude read named files instead of piping everything.

Do not grant `Edit`, `Write`, unrestricted `Bash`, or `acceptEdits` for review-only work. If implementation is explicitly requested, authorize the smallest required tool set and review Claude's diff before keeping it.

## Prompt Shape

For code review, include:

- base and head or exact diff scope;
- surrounding files Claude should inspect;
- project constraints and relevant tests;
- request for actionable findings only, sorted by severity;
- required evidence: path, line, failure scenario, and suggested fix;
- instruction to say `no findings` instead of inventing concerns.

For a targeted problem, include the observed symptom, reproduction, expected behavior, suspected area without asserting a cause, and commands Claude may safely run. Ask for root cause plus a minimal proof or test.

If a broad review says `no findings` but risk remains, make one targeted follow-up using the returned session ID or a fresh prompt focused on concrete boundaries such as retries, live state, error paths, concurrency, or partial completion. Do not lead Claude toward a predetermined answer.

## Failure Handling

- Authentication: run a real smoke prompt. A stale OAuth session or higher-priority expired `ANTHROPIC_API_KEY` can cause `401` despite appearing logged in. Never print tokens or dump the full environment.
- Startup stall: plugins and MCP servers can start automatically. Retry once with no tools and supplied context. Use `--safe-mode` only if current `claude --help` documents it.
- Bare mode: `--bare` skips hooks, skills, plugins, MCP, `CLAUDE.md`, OAuth, and keychain reads. Use it only with explicit API-key or `apiKeyHelper` authentication, not subscription OAuth.
- Timeout: use a bounded timeout appropriate to task size. Track the launched process and terminate only its process tree; never kill unrelated Claude sessions.
- Silence: normal text/JSON mode may emit nothing until completion. Use stream JSON only when progress visibility materially helps.

Claude output is evidence to investigate, never authority. Reproduce bugs, inspect exact lines, and run focused tests before presenting findings or changing code.
