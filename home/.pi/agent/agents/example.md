---
# Required local agent name. With package below, runtime name becomes rko.example.
name: example

# Optional namespace. Use the full runtime name, rko.example, when launching it.
package: rko

# Required discovery/listing summary shown to the parent agent.
description: Documentation-only no-op agent demonstrating every supported agent frontmatter setting

# Strict child tool allowlist. Omit this key for Pi's normal tools. Values may be
# comma-separated or YAML block-list entries. Extension tool names require their
# provider extension; mcp:server/tool selects a direct MCP tool. Read-only tools
# keep this example harmless even if its no-op prompt is ignored.
tools: read, grep, find, ls

# Default model. Omit it to inherit subagents.defaultModel or the parent model.
# Bare IDs use normal registry resolution; provider-qualified IDs are also valid.
model: z-ai/glm-5.2

# Ordered provider/model fallbacks used only for model/provider failures such as
# auth, quota, timeout, or unavailable model—not ordinary task failures.
fallbackModels: z-ai/glm-5.2

# Reasoning level: off, minimal, low, medium, high, xhigh, max, or false to clear
# a bundled/default thinking value. Unsupported levels may be clamped/rejected by
# the chosen model.
thinking: off

# replace uses only this file's prompt body. append adds it to Pi's base prompt.
systemPromptMode: replace

# Whether inherited project instructions such as AGENTS.md remain in child prompt.
inheritProjectContext: false

# Whether child sees Pi's discovered skills catalog. Explicit skills below remain
# selectable regardless of this value.
inheritSkills: false

# Default launch context when caller omits context: fresh or fork. Explicit call
# context wins. fork requires a persisted parent session.
defaultContext: fresh

# Default single-agent background behavior when caller omits async.
async: false

# Default positive runtime deadline in milliseconds. Explicit call deadline wins.
timeoutMs: 60000

# Default assistant-turn budget as one-line JSON. maxTurns requests wrap-up;
# graceTurns allows additional assistant boundaries. Explicit call budget wins.
turnBudget: {"maxTurns":1,"graceTurns":0}

# Default acceptance policy. Supported levels: auto, attested, checked, verified;
# reviewed is inferred-only. Use an object with level none plus a reason to disable.
# Full objects may also contain criteria, evidence, verify, review, and stopRules.
acceptance: {"level":"none","reason":"Documentation-only no-op agent"}

# Acceptance inference hint only: read-only or writer. It does not change tools.
acceptanceRole: read-only

# Explicit selected skills. Accepts comma-separated or YAML block-list values.
# Empty means none; missing skills normally warn rather than fail.
skills:

# Private skill files/directories, resolved relative to this agent file. This only
# discovers candidates; skills above still selects them. Empty means no private path.
skillPath:

# Child extension policy. Omitted loads normal discovered extensions; empty disables
# normal extensions; a list allowlists paths. Required pi-subagents runtime pieces,
# path-like tools, and subagentOnlyExtensions still load.
extensions:

# Extension paths loaded only for this agent's child sessions. Use this to provide
# private custom tools without registering them in the parent. Empty means none.
subagentOnlyExtensions:

# Default result artifact path for single-agent runs. Relative paths use the
# configured single-run output base or this run's artifact directory.
output: example-agent-output.md

# Files a chain/parallel run asks this agent to read first. Values may be comma-
# separated or a YAML block list. Empty prevents this example from reading anything.
defaultReads:

# Whether this agent maintains progress.md by default.
defaultProgress: false

# Compatibility field currently parsed but not enforced by pi-subagents v1.
interactive: false

# Maximum nested delegation depth for this agent; may only tighten inherited limit.
# Zero forbids this child from spawning subagents.
maxSubagentDepth: 0

# Implementation-completion guard. False is appropriate for advisors/no-op agents
# that must not be judged as implementation workers.
completionGuard: false

# Default child tool-call budget as one-line JSON. soft nudges finalization; after
# hard, block selects tools to reject ("*" means all). Explicit call budget wins.
# Hard budgets are normally unsuitable for mutation-capable agents.
toolBudget: {"soft":1,"hard":1,"block":"*"}

# Optional durable role memory. scope is user or project; path is a safe relative
# name under that scope's agent-memory directory. Read-only agents receive it as
# read-only context, and the directory is not created eagerly.
memory:
  scope: user
  path: rko-example-noop

# Optional @gotgenes/pi-permission-system integration. This is pass-through
# frontmatter, not a core pi-subagents field. Policies may map tools/commands to
# allow, ask, or deny. Deny-all reinforces this example's no-op behavior when the
# permission extension is installed; otherwise this block is inert.
permission:
  "*": deny
---

You are a documentation-only no-op example agent.

Do not call tools. Do not inspect files. Do not run commands. Do not edit or create
files. Do not delegate. Do not use or update memory. Do not analyze the requested
task or make decisions.

If launched, reply exactly:

No-op example agent; no work performed.
