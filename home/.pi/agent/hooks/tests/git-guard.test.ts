import gitGuard from "../git-guard";

// Mock HookAPI that captures the registered handler
type ToolCallEvent = { toolName: string; input: { command: string } };
type ToolCallHandler = (event: ToolCallEvent) => Promise<{ block: true; reason: string } | undefined>;

let handler: ToolCallHandler;

const mockPi = {
  on: (eventName: string, fn: ToolCallHandler) => {
    if (eventName === "tool_call") {
      handler = fn;
    }
  },
};

// Register the hook
gitGuard(mockPi as any);

// Helper to test a command
async function testCommand(command: string): Promise<{ blocked: boolean; reason?: string }> {
  const result = await handler({ toolName: "bash", input: { command } });
  if (result?.block) {
    return { blocked: true, reason: result.reason };
  }
  return { blocked: false };
}

// Test cases - easily human-inspectable
const SHOULD_BLOCK = [
  // Git checkout destructive
  "git checkout -- file.txt",
  "git checkout -- .",
  "git checkout HEAD -- src/",
  
  // Git restore destructive
  "git restore file.txt",
  "git restore .",
  "git restore --worktree file.txt",
  
  // Git reset destructive
  "git reset --hard",
  "git reset --hard HEAD~1",
  "git reset --merge",
  
  // Git clean
  "git clean -f",
  "git clean -fd",
  "git clean -fdx",
  
  // Force push
  "git push --force",
  "git push origin main --force",
  "git push -f",
  "git push -f origin main",
  
  // Branch force delete
  "git branch -D feature-branch",
  
  // rm -rf
  "rm -rf src/",
  "rm -rf .",
  "rm -fr important/",
  "rm -rf /home/user/project",
  "rm -rf ~/projects",
  
  // Stash destructive
  "git stash drop",
  "git stash drop stash@{0}",
  "git stash clear",
];

const SHOULD_ALLOW = [
  // Safe git operations
  "git status",
  "git diff",
  "git log",
  "git add .",
  "git commit -m 'message'",
  "git push",
  "git push origin main",
  "git pull",
  "git fetch",
  
  // Branch creation (safe checkout)
  "git checkout -b new-branch",
  "git checkout --orphan new-orphan",
  
  // Unstaging (safe restore)
  "git restore --staged file.txt",
  "git restore --staged .",
  
  // Dry runs (safe clean)
  "git clean -n",
  "git clean --dry-run",
  "git clean -nd",
  
  // Safe push
  "git push --force-with-lease",
  "git push origin main --force-with-lease",
  
  // Safe branch delete
  "git branch -d feature-branch",
  
  // Temp directory rm -rf (allowed)
  "rm -rf /tmp/build-cache",
  "rm -rf /var/tmp/test-output",
  "rm -rf $TMPDIR/temp-files",
  'rm -rf "$TMPDIR/temp-files"',
  
  // Regular rm
  "rm file.txt",
  "rm -f file.txt",
  "rm -r empty-dir/",
  
  // Non-bash tools (should pass through)
  "ls -la",
  "cat file.txt",
  "grep pattern file",
];

// Run tests
async function runTests() {
  console.log("=== GIT GUARD TESTS ===\n");
  
  let passed = 0;
  let failed = 0;
  
  console.log("--- SHOULD BLOCK ---\n");
  for (const cmd of SHOULD_BLOCK) {
    const result = await testCommand(cmd);
    const status = result.blocked ? "✓ BLOCKED" : "✗ ALLOWED (FAIL)";
    console.log(`${status}: ${cmd}`);
    if (result.blocked) passed++; else failed++;
  }
  
  console.log("\n--- SHOULD ALLOW ---\n");
  for (const cmd of SHOULD_ALLOW) {
    const result = await testCommand(cmd);
    const status = result.blocked ? "✗ BLOCKED (FAIL)" : "✓ ALLOWED";
    console.log(`${status}: ${cmd}`);
    if (!result.blocked) passed++; else failed++;
  }
  
  console.log("\n=== RESULTS ===");
  console.log(`Passed: ${passed}`);
  console.log(`Failed: ${failed}`);
  
  if (failed > 0) {
    process.exit(1);
  }
}

runTests();
