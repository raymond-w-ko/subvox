"""Run with uv run --with tomlkit --python 3.14 python -B -m unittest discover -s tests."""

import importlib.util
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import tomlkit

spec = importlib.util.spec_from_file_location(
    "apply_my_ai_settings", Path(__file__).resolve().parents[1] / "bin/apply_my_ai_settings.py"
)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.files = {
            app.AI_PROXY_CONFIG: json.dumps({
                "base_url": "https://gateway.example.test",
                "api_key": "test-new-key",
            }),
            app.CODEX_CONFIG: '# keep comment\nmodel = "keep-model"\n'
            '[model_providers.other]\nname = "keep-provider"\n'
            '[model_providers.cliproxyapi]\nenv_key = "OLD_ENV"\n'
            'experimental_bearer_token = "test-old-codex-key"\n',
            app.CLAUDE_SETTINGS: json.dumps({
                "enabledPlugins": {"keep-plugin": True},
                "env": {"KEEP": "keep-value", "ANTHROPIC_AUTH_TOKEN": "test-old-claude-key"},
            }),
        }
        self.writes = []
        self.output = io.StringIO()
        self.addCleanup(patch.stopall)
        patch.object(Path, "is_file", lambda path: path in self.files).start()
        patch.object(Path, "read_text", lambda path: self.files[path]).start()
        patch.object(Path, "write_text", lambda path, text: self.write(path, text)).start()
        self.chmod = patch.object(Path, "chmod").start()
        self.mkdir = patch.object(Path, "mkdir").start()
        self.open = patch.object(Path, "open").start()
        self.os_chmod = patch.object(app.os, "chmod").start()

    def write(self, path, text):
        self.files[path] = text
        self.writes.append(path)

    def run_gateway(self, dry_run=False):
        state = app.State(dry_run)
        with redirect_stdout(self.output):
            app.setting_gateway(state)
        return state

    def test_merge_and_rotation_preserve_unrelated_settings(self):
        self.assertEqual(self.run_gateway().failures, 0)
        codex = tomlkit.parse(self.files[app.CODEX_CONFIG])
        self.assertEqual(codex["model_provider"], "cliproxyapi")
        self.assertEqual(codex["model"], "keep-model")
        self.assertEqual(codex["model_providers"]["other"]["name"], "keep-provider")
        self.assertIn("# keep comment", self.files[app.CODEX_CONFIG])
        provider = codex["model_providers"]["cliproxyapi"]
        self.assertEqual(provider["experimental_bearer_token"], "test-new-key")
        self.assertEqual(provider["base_url"], "https://gateway.example.test/v1")
        self.assertEqual(provider["wire_api"], "responses")
        self.assertFalse(provider["requires_openai_auth"])
        self.assertNotIn("env_key", provider)
        claude = json.loads(self.files[app.CLAUDE_SETTINGS])
        self.assertEqual(claude["enabledPlugins"], {"keep-plugin": True})
        self.assertEqual(claude["env"], {
            "KEEP": "keep-value",
            "ANTHROPIC_BASE_URL": "https://gateway.example.test",
            "ANTHROPIC_AUTH_TOKEN": "test-new-key",
            "ANTHROPIC_API_KEY": "",
        })
        before = len(self.writes)
        self.assertEqual(self.run_gateway().failures, 0)
        self.assertEqual(len(self.writes), before)
        for secret in ("test-new-key", "test-old-codex-key", "test-old-claude-key"):
            self.assertNotIn(secret, self.output.getvalue())

    def test_dry_run_has_no_writes_or_secret_output(self):
        before = self.files.copy()
        self.assertEqual(self.run_gateway(dry_run=True).failures, 0)
        self.assertEqual(before, self.files)
        self.chmod.assert_not_called()
        self.mkdir.assert_not_called()
        self.open.assert_not_called()
        for secret in ("test-new-key", "test-old-codex-key", "test-old-claude-key"):
            self.assertNotIn(secret, self.output.getvalue())

    def test_invalid_input_leaves_both_configs_untouched(self):
        for value in (None, [], {}, {"api_key": ""}, {"api_key": 123},
                      {"api_key": "YOUR_GATEWAY_KEY"},
                      {"api_key": "test-new-key", "base_url": "file:///tmp/gateway"},
                      {"api_key": "test-new-key", "base_url": "https://user:secret@host"},
                      {"api_key": "test-new-key", "base_url": "https://host?key=secret"},
                      {"api_key": "test-new-key", "base_url": "https://host:invalid"}):
            with self.subTest(value=value):
                self.files[app.AI_PROXY_CONFIG] = json.dumps(value)
                before = self.files.copy()
                self.assertEqual(self.run_gateway().failures, 1)
                self.assertEqual(self.files, before)
        self.assertEqual(self.writes, [])

    def test_unreadable_or_malformed_proxy_file(self):
        for error in (FileNotFoundError(), PermissionError(), UnicodeDecodeError("utf8", b"x", 0, 1, "invalid")):
            with patch.object(Path, "read_text", side_effect=error):
                self.assertEqual(self.run_gateway().failures, 1)
        self.files[app.AI_PROXY_CONFIG] = '{"api_key": "test-new-key", invalid}'
        self.assertEqual(self.run_gateway().failures, 1)
        self.assertEqual(self.writes, [])
        self.assertNotIn("test-new-key", self.output.getvalue())

    def test_url_suffixes(self):
        for suffix in ("", "/", "/v1", "/v1/"):
            self.files[app.AI_PROXY_CONFIG] = json.dumps({
                "api_key": "test-new-key", "base_url": "https://gateway.example.test" + suffix,
            })
            self.assertEqual(self.run_gateway().failures, 0)
            codex = tomlkit.parse(self.files[app.CODEX_CONFIG])
            self.assertEqual(codex["model_providers"]["cliproxyapi"]["base_url"], "https://gateway.example.test/v1")
            claude = json.loads(self.files[app.CLAUDE_SETTINGS])
            self.assertEqual(claude["env"]["ANTHROPIC_BASE_URL"], "https://gateway.example.test")

    def test_unrelated_codex_edit_does_not_leak_provider_token(self):
        with redirect_stdout(self.output):
            app.setting_codex_model(app.State(False))
        self.assertNotIn("test-old-codex-key", self.output.getvalue())

    def test_missing_claude_settings_created_privately(self):
        self.files.pop(app.CLAUDE_SETTINGS)
        stream = io.StringIO()
        self.open.return_value.__enter__.return_value = stream
        with redirect_stdout(self.output):
            result = app.ensure_entry(
                app.State(False), app.CLAUDE_SETTINGS, ["env", "ANTHROPIC_AUTH_TOKEN"],
                "test-new-key", "claude", sensitive=True, create=True,
            )
        self.assertTrue(result)
        self.open.assert_called_once_with("x", encoding="utf-8")
        self.assertEqual(json.loads(stream.getvalue())["env"]["ANTHROPIC_AUTH_TOKEN"], "test-new-key")
        if not app.WINDOWS:
            self.os_chmod.assert_called_once_with(app.CLAUDE_SETTINGS, 0o600)
        self.assertNotIn("test-new-key", self.output.getvalue())

    def test_bad_claude_config_is_preserved(self):
        for text in ("[]", '{"env": invalid}'):
            self.files[app.CLAUDE_SETTINGS] = text
            self.assertEqual(self.run_gateway().failures, 1)
            self.assertEqual(self.files[app.CLAUDE_SETTINGS], text)


if __name__ == "__main__":
    unittest.main()
