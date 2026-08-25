# Change-stack model

Read this reference for PRs with multiple conceptual outcomes, cross-layer dependencies, lifecycle changes, or data-model changes.

## Research basis

This skill adapts CodeRabbit's Change Stack inspection model to a text-based agent workflow. Official documentation reviewed on 2026-08-25:

- [Change Stack documentation](https://docs.coderabbit.ai/pr-reviews/change-stack)
- [CodeRabbit changelog announcement](https://docs.coderabbit.ai/changelog#coderabbit-change-stack)
- [PR Walkthroughs](https://docs.coderabbit.ai/pr-reviews/walkthroughs)

CodeRabbit defines cohorts as independent conceptual groupings and layers as their natural reading order. Layers are anchored to changed line ranges and get range-specific summaries. Foundational data shapes and contracts precede consumers, call sites, and tests. Diagrams appear only where they add value. This skill preserves those ideas without claiming CodeRabbit's proprietary analysis or UI.

## Construct cohorts

A cohort should answer one review question such as “Does token rotation preserve existing sessions?” or “Can the new audit event reach its sink safely?” It should not merely answer “Which files changed?”

Prefer separate cohorts when changes:

- deliver independent outcomes;
- have distinct entry points and blast radii;
- can fail independently;
- require different domain expertise; or
- are mechanical support work with no behavioral coupling.

Keep work together when ranges share one contract, transaction, lifecycle, or externally visible outcome. Do not split tests and docs away from the behavior they prove or describe unless they cover several cohorts.

## Order layers

Draw a lightweight dependency graph between changed ranges. An edge from A to B means B consumes, calls, instantiates, configures, persists, deploys, or verifies A. Topologically order that graph, then merge adjacent nodes when one reading step can explain them without hiding risk.

Useful layer roles include:

1. contracts, schemas, types, protocol shapes, configuration, and migrations;
2. domain rules and core algorithms;
3. persistence, adapters, background work, and external integrations;
4. API, CLI, UI, or event entry points;
5. downstream consumers and call-site propagation;
6. tests, fixtures, documentation, and deployment proof.

These are heuristics, not mandatory names or count. A migration may need to follow compatibility code; a test helper may establish a contract before production code. Follow actual dependency and rollout order.

## Summarize ranges

Use post-change line numbers when possible. For deleted code, anchor to the nearest surviving hunk or use diff coordinates and say that the range was deleted.

Each summary should cover:

- behavior introduced, removed, or changed;
- role in its cohort;
- inputs, outputs, state, or contract affected;
- prerequisite and downstream ranges;
- review-relevant edge cases, without inventing a finding.

Example:

> `src/session/store.ts:44-78` adds compare-and-swap token rotation. It implements the atomicity required by the refresh handler in `src/http/refresh.ts:91-118`; callers now distinguish stale-token conflicts from storage failures. Review focus: concurrent refreshes and retry behavior.

## Choose diagrams

- Sequence diagram: request, event, async job, or callback crosses at least three components and ordering matters.
- State diagram: lifecycle gains or changes states, transitions, retries, or terminal paths.
- Entity-relationship diagram: persisted entities, keys, cardinality, or migration relationships change.

Skip diagrams for simple call chains, static module lists, or relationships already clearer in two sentences. Never add an edge based only on filenames or convention.

## Reconcile coverage

Before verdict, reconcile ledger against provider diff:

- every changed path accounted for;
- every hunk assigned or explicitly excluded;
- renames and deletions reviewed for lost behavior and callers;
- generated outputs match their source;
- tests mapped to claimed behavior;
- all findings anchored to current head;
- cross-cohort contracts reviewed once end to end.

Coverage does not mean equal prose for every file. It means no change disappears from review reasoning.
