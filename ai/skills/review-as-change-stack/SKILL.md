---
name: review-as-change-stack
description: Transform any code changeset—local working tree, staged diff, refs or commits, supplied patch, or pull request—into a standalone lettered stack of semantic changes, then review it in dependency order. Use for change-stack reviews or logical walkthroughs of large, cross-cutting diffs; not for creating or managing stacked branches.
---

# Review Changes as a Change Stack

Turn any flat diff into a standalone logical reading order. Change stack is a review model, not a request to rewrite history or create stacked branches.

## Core directives

- **Compress presentation, never review coverage. Account for every in-scope hunk; preserve every review-material semantic fact.**
- **DAG order controls comprehension; risk controls review depth.**
- **No `ready` verdict without reconciled coverage and explicit proof.**

## Establish changeset

- Keep review-only work read-only. Do not edit code, submit review comments, approve, request changes, switch branches, fetch, pull, or push unless explicitly requested.
- Start repository-backed reviews with `git status -sb`. Read applicable repository instructions and only architecture or contributor docs needed to understand intent.
- Use exact changeset user selected; do not silently widen or narrow it:
  - All local changes: inspect `git status --short`, `git diff`, `git diff --cached`, and untracked file contents.
  - Unstaged or staged changes: use `git diff` or `git diff --cached`, respectively.
  - Refs, commits, or ranges: use requested `git diff` form and state base/head ordering. Resolve immutable SHAs when possible.
  - Supplied patch or diff: use it directly and state any missing base/head context.
  - GitHub PR: use `gh pr view <target> --json number,title,body,baseRefName,headRefName,headRefOid,author,isDraft,mergeStateStatus,files,commits,statusCheckRollup,closingIssuesReferences` and `gh pr diff <target>`, not web search.
- Capture target identity or diff snapshot before analysis. Recheck mutable targets before verdict; revisit changed ranges or label review stale if target moved.
- Use issue/PR description, commit metadata, and code together when available. Distinguish stated intent from behavior inferred from changes.

If target remains ambiguous, ask before reviewing wrong changeset.

## Track coverage privately

Build private ledger for every changed path and hunk, including added, modified, deleted, renamed, binary, generated, vendored, lockfile, submodule, staged, unstaged, and untracked changes in scope. Record status, semantic stack entry, and review state.

Do not silently omit low-signal changes. Mechanical or generated output may share source entry, but verify source explains it. Report unavailable or intentionally uninspected material.

## Build change stack

1. Group changes by material behavior or review question, not file. One entry may span files, hunks, and implementation layers.
2. Split entries when outcomes, entry points, blast radii, failure modes, or needed expertise differ. Keep changes together when they share one contract, transaction, lifecycle, or visible outcome. Keep tests and docs with behavior they prove or describe unless they span entries.
3. Build dependency graph. `A` precedes `B` only when `A` defines, enables, configures, persists, exposes, calls, instantiates, deploys, or verifies something `B` needs. Require evidence from imports, calls, types, data flow, configuration, tests, rollout order, or repository context.
4. Topologically order entries and label them `A`, `B`, `C`, and so on. Use exact heading form `## A: ...`.
5. Put contracts, schemas, types, data shapes, configuration, and migrations before consumers when dependency supports it. Follow actual dependency and rollout order; layer roles are heuristics, not mandatory titles.
6. Merge adjacent entries until stack is smallest version that still exposes every material behavior, contract, failure mode, and dependency.
7. Compress into caveman English while preserving every material interface, behavior, input/output, state transition, control/data flow, error, edge case, schema/config/dependency change, compatibility effect, test obligation, deletion, and break. Never invent claims.
8. Explain every edge both ways. Each entry names predecessors and why; each predecessor names successors and why.
9. Make each entry self-contained. Do not emit line anchors, navigation instructions, file lists, hunk narration, import noise, or generated repetition unless identity itself matters. Explain relevant behavior inline.

## Review in stack order

Start with `A`; carry its contracts through successors. For each entry:

- Read enough unchanged context to understand behavior.
- Trace changed definitions to callers and consumers, and changed call sites back to definitions.
- Check applicable correctness, compatibility, migration, error, state, concurrency, cleanup, authorization, trust, resource, observability, deployment, and platform risks.
- Check tests prove changed contract and important failures. Run safe focused validation when practical; report exact commands and limits.
- Verify potential findings against current post-change code. Drop speculative, duplicate, style-only, or already-covered findings.

Then inspect cross-entry contracts and blast radius, especially persistence, configuration, security boundaries, lifecycle, and rollout order.

## Report

Lead with `ready`, `needs changes`, or `review incomplete`, plus reviewed SHA, range, PR head, or snapshot identifier when available.

Use this shape for every entry:

```markdown
## A: Behavior-focused title

Change: Standalone caveman-English account of all material behavior in this entry.

Depends on: none.

Successors: B depends on A because ...

Review: clear, or `[blocker|major|minor] Finding title` plus concrete failure scenario and smallest credible fix direction.
```

For multiple predecessors or successors, explain each edge. Use `Successors: none.` for terminal entries. Separate uncertain questions from findings.

Finish with compact **Cross-stack risks** and **Validation and gaps** sections covering interactions, compatibility, rollout/migration, test coverage, commands, unavailable context, unreviewed semantic changes, and residual risks. Do not append source map unless requested.

Use Mermaid sequence, state, or entity-relationship diagram only when it materially clarifies relationships across at least three components or states. Ground every node and edge in inspected code.

Before verdict, reconcile ledger: every path and hunk represented or excluded; renames and deletions checked for lost behavior and callers; generated output tied to source; tests mapped to claims; findings current; cross-entry contracts traced end to end; dependency edges explained both ways.

If full review is impossible, still build complete semantic stack, review highest-risk entries, and name every unreviewed change. Never imply complete coverage without ledger reconciliation.
