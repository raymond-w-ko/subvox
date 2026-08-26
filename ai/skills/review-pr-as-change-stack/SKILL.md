---
name: review-pr-as-change-stack
description: Transform a pull request or diff into a standalone, lettered stack of semantic changes with explicit predecessor and successor dependencies, then review it in that order. Use when the user asks for a change-stack review or needs a compressed logical walkthrough of a large, cross-cutting change. Do not use for creating or managing stacked PR branches.
---

# Review a PR as a Change Stack

Turn a flat file diff into a standalone artifact that replaces file-order browsing with a logical reading order. The artifact must make sense inside the assistant turn without requiring the reader to open source locations. The stack is a review model, not a request to rewrite history or create stacked PRs.

## Preserve review scope

- Treat a review-only request as read-only. Do not edit code, submit review comments, approve, request changes, switch branches, fetch, pull, or push unless the request explicitly includes that action.
- For GitHub PRs, start with `git status -sb`, then use `gh pr view <target> --json number,title,body,baseRefName,headRefName,headRefOid,author,isDraft,mergeStateStatus,files,commits,statusCheckRollup,closingIssuesReferences` and `gh pr diff <target>`. Do not use web search for PR contents.
- Read applicable repository instructions and the smallest set of architecture or contributor docs needed to understand intent.
- Capture the PR head SHA before analysis. Recheck it before the final verdict; if it moved, revisit affected ranges or label the review stale.
- Use the PR description, linked issue, commit metadata, and code together. Distinguish stated intent from behavior inferred from the diff.

If no PR is available but the user supplied a diff or clearly identified a comparison, use that changeset and state the base/head assumption. If the target remains ambiguous, ask before reviewing the wrong diff.

## Inventory every change privately

Build a private coverage ledger containing every changed path and hunk: added, modified, deleted, renamed, binary, generated, vendored, lockfile, and submodule changes. Record each item's status, semantic stack entry, and review state.

Do not silently omit low-signal changes. Generated or mechanical changes may collapse into their source entry, but verify that the source explains them. Report anything unavailable or intentionally not inspected.

## Build the change stack

1. Identify material semantic changes. Each becomes one stack entry that may span files, hunks, and implementation layers.
2. Build a dependency graph. A predecessor must define, enable, configure, persist, expose, or otherwise make a successor meaningful. Infer an edge only when imports, calls, types, data flow, configuration, tests, rollout order, or repository evidence support it.
3. Topologically order entries and label them `A`, `B`, `C`, and so on. Give every entry a behavior-focused heading in exact form `## A: ...`, `## B: ...`.
4. Put contracts, schemas, data shapes, configuration, and migrations before behavior that consumes them. Put integrations, entry points, consumers, tests, and docs after their prerequisites. Follow actual dependency order, not this list as a fixed template.
5. Merge entries until the stack is as small as possible without hiding a material behavior, contract, failure mode, or dependency.
6. **Compress changes into caveman English while remaining semantically isomorphic.** Remove filler and allow terse fragments, but preserve every material interface, behavior, control/data flow, error and edge case, schema/config/dependency change, test obligation, deletion, and break. Never invent claims.
7. Explain both directions of every edge. Each entry says `Depends on: none.` or names predecessor letters and why. Each predecessor says which successors depend on it and why.
8. Do not emit file-and-line anchors, source-navigation instructions, or summaries that force the reader to inspect another file. Mention a component, type, function, command, or file name only when its identity carries necessary meaning; explain relevant behavior inline.

For a PR with multiple concerns, cross-entry dependencies, lifecycle changes, or data-model changes, read [references/change-stack-model.md](references/change-stack-model.md) before finalizing the stack.

## Review in stack order

Start with entry `A` and carry its contracts through successors. For each entry:

- Read enough unchanged context to understand the behavior.
- Trace changed definitions to callers and consumers, and changed call sites back to their definitions.
- Check applicable risks: correctness, compatibility, migration safety, error paths, state and concurrency, cleanup, authorization and trust boundaries, resource use, observability, deployment ordering, and platform behavior.
- Check that tests prove the changed contract and important failure paths. Run safe, focused validation when practical; report exact commands and limits.
- Verify each potential finding against the current post-change code. Drop speculative, duplicate, style-only, or already-covered findings.

After entry review, inspect cross-stack interactions and blast radius. Pay special attention to shared contracts, persistence, configuration, security boundaries, and rollout order that connect otherwise independent entries.

## Report

Lead with verdict: `ready`, `needs changes`, or `review incomplete`, plus reviewed head SHA when available.

Then emit lettered stack entries. Use this shape:

```markdown
## A: Behavior-focused title

Change: Standalone caveman-English account of all material behavior in this entry.

Depends on: none.

Successors: B depends on A because ...

Review: clear, or `[blocker|major|minor] Finding title` plus concrete failure scenario and smallest credible fix direction.
```

Continue with `## B: ...`, `## C: ...`. For each successor, state `Depends on A because ...`; for multiple predecessors, explain each one. Use `Successors: none.` for terminal entries. Separate uncertain questions from findings.

Finish with compact **Cross-stack risks** and **Validation and gaps** sections. Include interactions, compatibility, rollout/migration, test coverage, commands run, unavailable context, unreviewed semantic changes, and residual risks. Do not append a file-by-file or line-by-line source map unless the user explicitly asks for one.

Use a Mermaid sequence, state, or entity-relationship diagram only when it materially clarifies a relationship across at least three components or states. Keep every node and edge grounded in inspected code.

If review cannot cover the full diff, transform the full semantic stack first, review highest-risk entries, and name every unreviewed semantic change. Never imply complete coverage without private ledger reconciliation.
