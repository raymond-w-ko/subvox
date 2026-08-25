---
name: review-pr-as-change-stack
description: Review a pull request or diff as dependency-ordered change cohorts and line-range layers, then perform an evidence-backed code review in that order. Use when the user asks for a change-stack review or needs a logical walkthrough of a large, cross-cutting change. Do not use for creating or managing stacked PR branches.
---

# Review a PR as a Change Stack

Turn a flat file diff into a logical reading order, then review it. The stack is a review model, not a request to rewrite history or create stacked PRs.

## Preserve review scope

- Treat a review-only request as read-only. Do not edit code, submit review comments, approve, request changes, switch branches, fetch, pull, or push unless the request explicitly includes that action.
- For GitHub PRs, start with `git status -sb`, then use `gh pr view <target> --json number,title,body,baseRefName,headRefName,headRefOid,author,isDraft,mergeStateStatus,files,commits,statusCheckRollup,closingIssuesReferences` and `gh pr diff <target>`. Do not use web search for PR contents.
- Read applicable repository instructions and the smallest set of architecture or contributor docs needed to understand intent.
- Capture the PR head SHA before analysis. Recheck it before the final verdict; if it moved, revisit affected ranges or label the review stale.
- Use the PR description, linked issue, commit metadata, and code together. Distinguish stated intent from behavior inferred from the diff.

If no PR is available but the user supplied a diff or clearly identified a comparison, use that changeset and state the base/head assumption. If the target remains ambiguous, ask before reviewing the wrong diff.

## Inventory every change

Build a private coverage ledger containing every changed path and hunk: added, modified, deleted, renamed, binary, generated, vendored, lockfile, and submodule changes. Record each item's status, changed ranges, assigned cohort/layer, and review state.

Do not silently omit low-signal files. Generated or mechanical changes may receive one grouped summary, but name them and verify that their source change explains them. Report anything unavailable or intentionally not inspected.

## Build the change stack

1. Identify independent conceptual outcomes. Each becomes a **cohort**. A cohort may span directories, and one file may contribute ranges to multiple cohorts.
2. Within each cohort, order **layers** by dependency and natural reading order. Put contracts, schemas, data shapes, configuration, and migrations before core behavior; put integrations, entry points, consumers, tests, and docs after what they depend on. Use actual dependencies, not this list as a fixed template.
3. Anchor every layer to exact changed ranges. Assign each range one primary home and cross-reference it where another layer depends on it.
4. Name cohorts and layers by behavior or responsibility, not by directory or file type.
5. Infer a relationship only when imports, calls, types, data flow, configuration, tests, or repository evidence support it.

For a PR with multiple concerns, cross-layer dependencies, lifecycle changes, or data-model changes, read [references/change-stack-model.md](references/change-stack-model.md) before finalizing the stack.

## Review in stack order

Start with the lowest prerequisite layer and carry its contracts upward. For each layer:

- Read enough unchanged context to understand the changed ranges.
- Trace changed definitions to callers and consumers, and changed call sites back to their definitions.
- Check applicable risks: correctness, compatibility, migration safety, error paths, state and concurrency, cleanup, authorization and trust boundaries, resource use, observability, deployment ordering, and platform behavior.
- Check that tests prove the changed contract and important failure paths. Run safe, focused validation when practical; report exact commands and limits.
- Verify each potential finding against the current post-change code. Drop speculative, duplicate, style-only, or already-covered findings.

After layer review, inspect cross-cohort interactions and blast radius. Pay special attention to shared contracts, persistence, configuration, security boundaries, and rollout order that connect otherwise independent cohorts.

## Report

Lead with verdict: `ready`, `needs changes`, or `review incomplete`, plus reviewed head SHA.

Then provide:

1. **Stack map** — cohorts in a useful order; dependency-ordered layers inside each cohort.
2. **Range summaries** — `path:start-end`, what changed, why the range belongs here, and what later ranges depend on it. Group only truly mechanical ranges.
3. **Findings** — place each under its owning layer and format as `[blocker|major|minor] path:line — title`, followed by concrete failure scenario and smallest credible fix direction. Separate uncertain questions from findings.
4. **Cross-stack checks** — interactions, compatibility, rollout/migration, and test coverage spanning layers or cohorts.
5. **Validation and gaps** — commands run, files or ranges not inspected, unavailable context, and residual risks.

Use a Mermaid sequence, state, or entity-relationship diagram only when it materially clarifies a relationship across at least three components or states. Keep every node and edge grounded in inspected code.

If review cannot cover the full diff, map the full stack first, review highest-risk layers, and list every unreviewed range. Never imply complete coverage without ledger reconciliation.
