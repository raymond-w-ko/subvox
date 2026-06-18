from __future__ import annotations

import unittest

import _setup_ai_config as setup


class ClaudeConfigMergeTest(unittest.TestCase):
    def test_preserves_unmanaged_home_settings(self) -> None:
        existing = {
            "permissions": {"allow": ["Bash(git status:*)"]},
            "env": {"USER_ENV": "keep"},
            "statusLine": {"extra": "keep"},
            "hooks": {"PreToolUse": [{"matcher": "Read", "hooks": []}]},
        }

        merged = setup.merge_claude_home_settings(existing)

        self.assertEqual(merged["permissions"], existing["permissions"])
        self.assertEqual(merged["env"]["USER_ENV"], "keep")
        self.assertEqual(merged["statusLine"]["extra"], "keep")
        self.assertEqual(merged["hooks"], existing["hooks"])

    def test_preserves_unmanaged_claude_json_settings(self) -> None:
        existing = {
            "numStartups": 4,
            "mcpServers": {
                "custom": {"command": "custom-mcp"},
                "agent-mail": {"command": "stale"},
            },
            "projects": {"/tmp/project": {"allowedTools": ["Read"]}},
        }

        merged = setup.merge_claude_json_settings(existing, token=None)

        self.assertEqual(merged["numStartups"], 4)
        self.assertEqual(merged["projects"], existing["projects"])
        self.assertEqual(merged["mcpServers"]["custom"], {"command": "custom-mcp"})
        self.assertNotIn("agent-mail", merged["mcpServers"])


class CodexConfigMergeTest(unittest.TestCase):
    def test_preserves_unmanaged_existing_settings(self) -> None:
        existing = {
            "projects": {"/tmp/project": {"trust_level": "trusted"}},
            "tui": {"unknown_tui_setting": "keep"},
            "features": {"local_feature": True},
            "mcp_servers": {"custom": {"command": "custom-mcp"}},
        }

        merged = setup.merge_codex_settings(existing, token=None)

        self.assertEqual(merged["projects"], existing["projects"])
        self.assertEqual(merged["tui"]["unknown_tui_setting"], "keep")
        self.assertIs(merged["features"]["local_feature"], True)
        self.assertEqual(merged["mcp_servers"]["custom"], {"command": "custom-mcp"})

    def test_updates_managed_codex_status_settings(self) -> None:
        merged = setup.merge_codex_settings({"tui": {"status_line": ["old"]}}, token=None)

        self.assertEqual(
            merged["tui"]["status_line"],
            [
                "model-with-reasoning",
                "project-name",
                "git-branch",
                "pull-request-number",
                "branch-changes",
                "permissions",
                "task-progress",
                "run-state",
            ],
        )
        self.assertIs(merged["tui"]["status_line_use_colors"], True)


if __name__ == "__main__":
    unittest.main()
