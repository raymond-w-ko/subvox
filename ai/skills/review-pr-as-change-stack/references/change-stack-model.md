# Change-stack model

Read this reference for PRs with multiple conceptual outcomes, cross-entry dependencies, lifecycle changes, or data-model changes.

## Research basis

This skill adapts CodeRabbit's Change Stack inspection model to a text-based agent workflow. Official documentation reviewed on 2026-08-25:

- [Change Stack documentation](https://docs.coderabbit.ai/pr-reviews/change-stack)
- [CodeRabbit changelog announcement](https://docs.coderabbit.ai/changelog#coderabbit-change-stack)
- [PR Walkthroughs](https://docs.coderabbit.ai/pr-reviews/walkthroughs)

CodeRabbit defines cohorts as independent conceptual groupings and layers as their natural reading order. Foundational data shapes and contracts precede consumers, call sites, and tests. Diagrams appear only where they add value. CodeRabbit's UI anchors layers to changed ranges; this skill intentionally replaces those navigation anchors with a self-contained assistant-turn artifact. It preserves logical grouping and dependency order without claiming CodeRabbit's proprietary analysis or UI.

## Choose semantic entries

A stack entry should answer one review question such as “Does token rotation preserve existing sessions?” or “Can the new audit event reach its sink safely?” It should not merely answer “Which files changed?”

Prefer separate entries when changes:

- deliver independent outcomes;
- have distinct entry points and blast radii;
- can fail independently;
- require different domain expertise; or
- are mechanical support work with no behavioral coupling.

Keep work together when changes share one contract, transaction, lifecycle, or externally visible outcome. Do not split tests and docs away from the behavior they prove or describe unless they cover several entries.

## Order predecessors and successors

Draw a lightweight dependency graph between semantic changes. An edge from A to B means B consumes, calls, instantiates, configures, persists, deploys, or verifies A. Topologically order that graph, assign letters, then merge adjacent nodes when one reading step can explain them without hiding risk.

Useful layer roles include:

1. contracts, schemas, types, protocol shapes, configuration, and migrations;
2. domain rules and core algorithms;
3. persistence, adapters, background work, and external integrations;
4. API, CLI, UI, or event entry points;
5. downstream consumers and call-site propagation;
6. tests, fixtures, documentation, and deployment proof.

These are heuristics, not mandatory titles or count. A migration may need to follow compatibility code; a test helper may establish a contract before production code. Follow actual dependency and rollout order.

## Preserve meaning while compressing

Compress changes into caveman English while remaining semantically isomorphic. Reader should recover every review-material fact without reopening the diff.

Each entry should preserve:

- behavior introduced, removed, or changed;
- public and internal contracts affected;
- inputs, outputs, state, or contract affected;
- control flow, data flow, errors, and review-relevant edge cases;
- predecessor requirements and successor use;
- compatibility, rollout, tests, deletions, and breaking effects.

Omit file lists, hunk narration, import noise, and generated repetition when they add no semantic information. Keep exact technical terms and code symbols when paraphrase would lose meaning.

## Standalone output example

```markdown
## A: Version session-token contract

Change: Token record gains generation number and rotation timestamp. Existing readers accept old records with default generation `0`; writers always emit new shape.

Depends on: none.

Successors: B depends on A for stale-token detection. C depends on A for compatibility fixtures.

Review: clear.

## B: Rotate tokens atomically

Change: Refresh compares expected generation before write. Concurrent refresh: one succeeds; loser gets stale-token conflict, not storage failure.

Depends on A because generation number supplies compare-and-swap guard.

Successors: C depends on B to prove concurrent behavior.

Review: `[major] Retry can replay stale generation` Retry path reuses old generation after conflict, allowing repeated failure. Reload current record before retry.

## C: Prove old-record and concurrent-refresh behavior

Change: Tests cover generation default, new writes, one-winner concurrency, stale-token error mapping.

Depends on A for old/new record shapes. Depends on B for atomic rotation behavior.

Successors: none.

Review: clear.
```

## Choose diagrams

- Sequence diagram: request, event, async job, or callback crosses at least three components and ordering matters.
- State diagram: lifecycle gains or changes states, transitions, retries, or terminal paths.
- Entity-relationship diagram: persisted entities, keys, cardinality, or migration relationships change.

Skip diagrams for simple call chains, static module lists, or relationships already clearer in two sentences. Never add an edge based only on filenames or convention.

## Reconcile coverage

Before verdict, reconcile private ledger against provider diff:

- every changed path accounted for;
- every hunk represented by a semantic entry or explicitly excluded;
- renames and deletions reviewed for lost behavior and callers;
- generated outputs match their source;
- tests mapped to claimed behavior;
- all findings verified against current head;
- cross-entry contracts reviewed once end to end;
- every dependency edge explained in both predecessor and successor entries.

Coverage does not mean equal prose for every file or any source-navigation appendix. It means no material change disappears from standalone artifact.
