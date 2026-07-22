---
name: microdiff
description: Use only when the user types `microdiff`. Summarize the current change set with maximum semantic density and minimum characters.
---

## 1. Acquire change set

### Git repo
Compare the working tree to `HEAD`—the last commit.

Include:
- staged changes
- unstaged changes
- untracked files as additions
- deletions
- renames/moves
- binary and submodule changes

Use the equivalent of:
- `git status --short --untracked-files=all`
- `git diff --find-renames HEAD`

Inspect untracked files separately because normal Git diffs omit them.

Do not rely only on diff stats. Read enough of the changed content to understand its semantics.

### No usable Git repo
Reconstruct the changes made during the immediately preceding work turn using available context, files, tool results, or memory.

Prefix uncertain inferred changes with `?`.

### No change set
If changes cannot be obtained or reconstructed, output exactly:

`no diff available`

Then stop.

If the change set is available but empty, output exactly:

`no changes`

Then stop.

## 2. Semantically compress

Produce a semantic microdiff, not a line-by-line summary.

Group related edits by behavior or purpose, even when spread across multiple files. Do not mechanically emit one item per file or hunk.

Use **caveman ultra**:
- fragments, not sentences
- symbols over prose
- no articles, filler, praise, rationale, or narration
- shortest wording that remains unambiguous
- minimize characters, never material information

Preserve every review-relevant change:
- externally observable behavior
- public APIs, types, symbols, commands, routes, or events
- control/data flow
- validation, errors, retries, fallbacks, and edge cases
- schema, migrations, persistence, and serialization
- configuration, permissions, dependencies, and build behavior
- tests added, removed, or materially changed
- meaningful constants or defaults
- deletions and compatibility breaks

Usually omit:
- formatting-only edits
- import reordering
- generated-file noise
- lockfile churn beyond the actual dependency change
- repetitive implementation details already represented by a semantic group

Compression must be semantically isomorphic at review level:
- every material source change maps to a summary item
- every summary claim is supported by the change set
- related repetitions collapse into one item
- distinct behaviors remain distinct
- no invented intent

## 3. Output

Output only the microdiff. No introduction, conclusion, raw patch, or recommendations.

Preferred grammar:

`<scope>[<paths if useful>]: <compressed operations>`

Operators:
- `+` add
- `~` modify
- `-` remove
- `→` rename/move
- `!` breaking or high-risk behavior
- `?` uncertain reconstruction

One line per semantic group. Order by reviewer importance: breaking/public behavior first, internals next, tests/generated artifacts last.

Example:

`auth[session.ts,api.ts]: +refresh rotation; ~expired token 401→silent retry; -legacy cookie`
`db[schema,m042]: +users.last_seen nullable+idx`
`tests: +rotation/retry coverage; ~401 expectations`
