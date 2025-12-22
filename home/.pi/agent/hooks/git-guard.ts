import type { HookAPI } from "@mariozechner/pi-coding-agent/hooks";

// Destructive patterns to block - tuple of [regex, reason]
const DESTRUCTIVE_PATTERNS: [RegExp, string][] = [
  // Git commands that discard uncommitted changes
  [
    /git\s+checkout\s+--\s+/i,
    "git checkout -- discards uncommitted changes permanently. Use 'git stash' first.",
  ],
  [
    /git\s+checkout\s+(?!-b\b)(?!--orphan\b)[^\s]+\s+--\s+/i,
    "git checkout <ref> -- <path> overwrites working tree. Use 'git stash' first.",
  ],
  [
    /git\s+restore\s+(?!--staged\b)[^\s]*\s*$/i,
    "git restore discards uncommitted changes. Use 'git stash' or 'git diff' first.",
  ],
  [
    /git\s+restore\s+--worktree/i,
    "git restore --worktree discards uncommitted changes permanently.",
  ],
  // Git reset variants
  [
    /git\s+reset\s+--hard/i,
    "git reset --hard destroys uncommitted changes. Use 'git stash' first.",
  ],
  [
    /git\s+reset\s+--merge/i,
    "git reset --merge can lose uncommitted changes.",
  ],
  // Git clean
  [
    /git\s+clean\s+-[a-z]*f/i,
    "git clean -f removes untracked files permanently. Review with 'git clean -n' first.",
  ],
  // Force operations
  [
    /git\s+push\s+.*--force(?!-with-lease)/i,
    "Force push can destroy remote history. Use --force-with-lease if necessary.",
  ],
  [
    /git\s+push\s+-f\b/i,
    "Force push (-f) can destroy remote history. Use --force-with-lease if necessary.",
  ],
  [
    /git\s+branch\s+-D\b/,
    "git branch -D force-deletes without merge check. Use -d for safety.",
  ],
  // Destructive filesystem commands
  [
    /rm\s+-[a-z]*r[a-z]*f|rm\s+-[a-z]*f[a-z]*r/i,
    "rm -rf is destructive. List files first, then delete individually with permission.",
  ],
  [
    /rm\s+-rf\s+[/~]/i,
    "rm -rf on root or home paths is extremely dangerous.",
  ],
  // Git stash drop/clear without explicit permission
  [
    /git\s+stash\s+drop/i,
    "git stash drop permanently deletes stashed changes. List stashes first.",
  ],
  [
    /git\s+stash\s+clear/i,
    "git stash clear permanently deletes ALL stashed changes.",
  ],
];

// Patterns that are safe even if they match above (allowlist)
const SAFE_PATTERNS: RegExp[] = [
  /git\s+checkout\s+-b\s+/i,           // Creating new branch
  /git\s+checkout\s+--orphan\s+/i,     // Creating orphan branch
  /git\s+restore\s+--staged\s+/i,      // Unstaging (safe)
  /git\s+clean\s+-n/i,                 // Dry run
  /git\s+clean\s+--dry-run/i,          // Dry run
  // Allow rm -rf on temp directories (these are designed for ephemeral data)
  /rm\s+-[a-z]*r[a-z]*f[a-z]*\s+\/tmp\//i,
  /rm\s+-[a-z]*r[a-z]*f[a-z]*\s+\/var\/tmp\//i,
  /rm\s+-[a-z]*r[a-z]*f[a-z]*\s+\$TMPDIR\//i,
  /rm\s+-[a-z]*r[a-z]*f[a-z]*\s+\$\{TMPDIR/i,
  /rm\s+-[a-z]*r[a-z]*f[a-z]*\s+"\$TMPDIR\//i,
  /rm\s+-[a-z]*r[a-z]*f[a-z]*\s+"\$\{TMPDIR/i,
];

export default function (pi: HookAPI) {
  pi.on("tool_call", async (event) => {
    // Only check bash commands
    if (event.toolName !== "bash") return undefined;

    const command = event.input.command as string;
    if (!command) return undefined;

    // Check if command matches any safe pattern first
    for (const pattern of SAFE_PATTERNS) {
      if (pattern.test(command)) {
        return undefined;
      }
    }

    // Check if command matches any destructive pattern
    for (const [pattern, reason] of DESTRUCTIVE_PATTERNS) {
      if (pattern.test(command)) {
        return {
          block: true,
          reason: `BLOCKED by git-guard\n\nReason: ${reason}\n\nCommand: ${command}\n\nIf this operation is truly needed, ask the user for explicit permission and have them run the command manually.`,
        };
      }
    }

    // Allow all other commands
    return undefined;
  });
}
