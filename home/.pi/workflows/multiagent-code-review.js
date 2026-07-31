export const meta = {
  name: 'multiagent_code_review_sample',
  description: 'Five-model parallel code review with one evidence-checking synthesis pass',
  phases: [
    { title: 'Review' },
    { title: 'Synthesize' },
  ],
};

// Study source only: pi-dynamic-workflows does not auto-register arbitrary .js
// files from this directory. Pass this script to the workflow tool when ready.
// Pass { target: 'git diff HEAD' }, a commit range, file path, or PR description.
// Agents inspect the repository from the workflow working directory.
const requestedTarget =
  args && typeof args.target === 'string' ? args.target.trim() : '';
const target = requestedTarget || 'current working tree diff (git diff HEAD)';

if (target.length > 2_000) {
  throw new Error('args.target must be 2,000 characters or fewer');
}

const findingSchema = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      maxItems: 8,
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['P0', 'P1', 'P2', 'P3'] },
          file: { type: 'string' },
          line: { type: 'number' },
          title: { type: 'string' },
          evidence: { type: 'string' },
          impact: { type: 'string' },
          suggestedFix: { type: 'string' },
        },
        required: [
          'severity',
          'file',
          'line',
          'title',
          'evidence',
          'impact',
          'suggestedFix',
        ],
      },
    },
  },
  required: ['findings'],
};

const reviewers = [
  {
    id: 'sol-fresh-eyes',
    model: 'openai-codex/gpt-5.6-sol',
  },
  {
    id: 'fable-fresh-eyes',
    model: 'anthropic/claude-fable-5',
  },
  {
    id: 'kimi-fresh-eyes',
    model: 'openrouter/moonshotai/kimi-k3',
  },
  {
    id: 'grok-fresh-eyes',
    model: 'openrouter/x-ai/grok-4.5',
  },
  {
    id: 'minimax-fresh-eyes',
    model: 'openrouter/minimax/minimax-m3',
  },
];

// Deliberately identical for every reviewer. Diversity comes from model lineage,
// not assigned responsibilities or narrowing lenses.
const sharedPrompt = `
Check over everything again with fresh eyes, looking for any blunders, mistakes,
errors, oversights, omissions, logical issues, problems, misconceptions, confusion,
bugs, etc. Be SUPER thorough and meticulous!

Review target: ${target}

Inspect all relevant repository files, callers, tests, configuration, git diff, and
history as needed. Do not modify files. Look broadly rather than limiting review to
one category. Report only actionable, evidence-backed problems introduced or exposed
by the target. Exclude style-only preferences and unsupported speculation. Every
finding needs exact file, line, evidence, impact, and smallest reasonable fix. Return
no finding when evidence is insufficient.
`;

phase('Review');
const rawReviews = await parallel(
  reviewers.map((reviewer) => () =>
    agent(sharedPrompt, {
      label: `review:${reviewer.id}`,
      model: reviewer.model,
      schema: findingSchema,
    }),
  ),
);

// Keep every intended reviewer in ledger. null means missing coverage, not "no issues".
const ledger = reviewers.map((reviewer, reviewerIndex) => {
  const result = rawReviews[reviewerIndex];
  return {
    reviewerId: reviewer.id,
    model: reviewer.model,
    status: result === null ? 'failed' : 'complete',
    findings:
      result === null
        ? []
        : result.findings.map((finding, findingIndex) => ({
            id: `${reviewer.id}:${findingIndex + 1}`,
            ...finding,
          })),
  };
});

const reportSchema = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    findings: {
      type: 'array',
      maxItems: 12,
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['P0', 'P1', 'P2', 'P3'] },
          file: { type: 'string' },
          line: { type: 'number' },
          title: { type: 'string' },
          evidence: { type: 'string' },
          impact: { type: 'string' },
          suggestedFix: { type: 'string' },
          sourceIds: { type: 'array', items: { type: 'string' } },
        },
        required: [
          'severity',
          'file',
          'line',
          'title',
          'evidence',
          'impact',
          'suggestedFix',
          'sourceIds',
        ],
      },
    },
    missingCoverage: { type: 'array', items: { type: 'string' } },
  },
  required: ['summary', 'findings', 'missingCoverage'],
};

phase('Synthesize');
const report = await agent(
  `Act as senior review chair. Re-check candidate findings against repository and target.
Deduplicate overlapping reports. Keep only evidence-backed defects. Rank by severity,
then confidence. Preserve sourceIds from candidate IDs. List failed reviewer IDs under
missingCoverage; never treat failed coverage as a clean review.

Target: ${target}

Complete review ledger:
${JSON.stringify(ledger, null, 2)}`,
  {
    label: 'synthesize:sol',
    model: 'openai-codex/gpt-5.6-sol',
    schema: reportSchema,
  },
);

return {
  target,
  ledger,
  report,
};
