---
name: microdiff
description: Use when user types `microdiff`
---

1. Get change set.
   - Git repo: compare working tree with `HEAD`. Include staged, unstaged, untracked, deleted, renamed, binary, and submodule changes.
   - No usable Git diff or work outside repo: reconstruct changes from immediately previous work turn using available context, files, and tool results. Prefix uncertain claims with `?`.
   - Unavailable: output exactly `no diff available`; stop.
   - Empty: output exactly `no changes`; stop.

2. Compress by behavior/purpose, not file or hunk. Minimize groups and characters while remaining semantically isomorphic at review level: every material change recoverable; no invented claims.

3. Preserve behavior, public interfaces, control/data flow, errors/edge cases, schema/config/dependencies, tests, deletions, and breaks. Omit cosmetic, generated, import, and lockfile noise unless meaningful.

4. Output microdiff only.  Use Markdown headings to separate groups and bullets for each change. You may use `code`, **bold**, and _italics_ when meaningful. Below is the general template for microdiff output. Use it as a guide, but adapt to the situation. Avoid unnecessary sections or empty sections. Do NOT output the entire microdiff as a single code block.

## scope [optional paths]
- ＋ adds
- Δ changes
- − removals
- ‼ breaks/risks
- ? inferred
