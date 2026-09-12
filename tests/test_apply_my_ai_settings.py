"""Run with uv run --with tomlkit --python 3.14 python -B -m unittest discover -s tests."""

import importlib.util
import io
import json
import subprocess
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from unittest.mock import call, patch

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
            app.PI_MODELS: json.dumps({
                "providers": {"other": {"baseUrl": "https://other.example.test"}},
            }),
            app.PI_AUTH: '{"other": {"key": "test-saved-pi-key"}}',
            app.GROK_CONFIG: '# keep Grok comment\n[models]\ndefault = "old-model"\n'
            'temperature = 0.7\n[ui]\ntheme = "keep-theme"\n'
            '[model.other]\nmodel = "keep-model"\n'
            '[model.proxy]\napi_key = "test-old-grok-key"\nenv_key = "OLD_KEY"\n',
        }
        self.writes = []
        self.output = io.StringIO()
        self.addCleanup(patch.stopall)
        patch.object(Path, "is_file", lambda path: path in self.files).start()
        patch.object(Path, "exists", lambda path: path in self.files).start()
        patch.object(Path, "is_symlink", return_value=False).start()
        patch.object(Path, "read_text", lambda path: self.files[path]).start()
        patch.object(Path, "write_text", lambda path, text: self.write(path, text)).start()
        self.chmod = patch.object(Path, "chmod").start()
        self.mkdir = patch.object(Path, "mkdir").start()
        self.open = patch.object(Path, "open").start()
        self.os_chmod = patch.object(app.os, "chmod").start()
        self.unlink = patch.object(Path, "unlink", autospec=True).start()
        self.unlink.side_effect = lambda path: self.files.pop(path)
        self.plugin_check = patch.object(app, "ensure_pi_anthropic_plugin_absent", return_value=True).start()

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
        self.assertTrue(provider["supports_websockets"])
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
        self.unlink.assert_not_called()
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

    def test_pi_builtin_overrides_and_auth_removal(self):
        with redirect_stdout(self.output):
            app.setting_pi_gateway(app.State(False), "https://gateway.example.test", "test-new-key")
        providers = json.loads(self.files[app.PI_MODELS])["providers"]
        self.assertEqual(providers["other"], {"baseUrl": "https://other.example.test"})
        self.assertEqual(providers["openai"], {
            "baseUrl": "https://gateway.example.test/v1", "apiKey": "test-new-key",
        })
        self.assertEqual(providers["anthropic"], {
            "baseUrl": "https://gateway.example.test", "apiKey": "test-new-key",
            "authHeader": True, "headers": {"x-api-key": ""},
        })
        self.unlink.assert_called_once_with(app.PI_AUTH)
        self.assertNotIn(app.PI_AUTH, self.files)
        for private in ("test-new-key", "test-saved-pi-key", "gateway.example.test"):
            self.assertNotIn(private, self.output.getvalue())

    def test_pi_dry_run_keeps_credentials(self):
        state = self.run_gateway(dry_run=True)
        self.assertEqual(state.failures, 0)
        self.assertIn(app.PI_AUTH, self.files)
        self.assertIn("all saved provider credentials", self.output.getvalue())
        self.unlink.assert_not_called()

    def test_pi_key_syntax_is_literal(self):
        with redirect_stdout(self.output):
            app.setting_pi_gateway(app.State(False), "https://gateway.example.test", "!${TEST_KEY}$suffix")
        providers = json.loads(self.files[app.PI_MODELS])["providers"]
        for name in ("openai", "anthropic"):
            self.assertEqual(providers[name]["apiKey"], "$!$${TEST_KEY}$$suffix")

    def test_missing_pi_models_created_before_auth_removal(self):
        self.files.pop(app.PI_MODELS)

        @contextmanager
        def open_file(path, mode, encoding):
            self.assertEqual((path, mode, encoding), (app.PI_MODELS, "x", "utf-8"))
            stream = io.StringIO()
            yield stream
            self.files[path] = stream.getvalue()

        def unlink(path):
            providers = json.loads(self.files[app.PI_MODELS])["providers"]
            self.assertEqual(set(providers), {"openai", "anthropic"})
            self.files.pop(path)

        self.unlink.side_effect = unlink
        with patch.object(Path, "open", open_file):
            self.assertEqual(self.run_gateway().failures, 0)
        if not app.WINDOWS:
            self.os_chmod.assert_called_once_with(app.PI_MODELS, 0o600)
        self.unlink.assert_called_once_with(app.PI_AUTH)

    def test_failed_pi_write_keeps_credentials(self):
        def write(path, text):
            if path == app.PI_MODELS and '"anthropic"' in text:
                raise PermissionError("test-secret-error")
            self.write(path, text)

        with patch.object(Path, "write_text", write):
            self.assertEqual(self.run_gateway().failures, 1)
        self.assertIn(app.PI_AUTH, self.files)
        self.unlink.assert_not_called()
        self.assertNotIn("test-secret-error", self.output.getvalue())

    def test_malformed_pi_models_keeps_credentials(self):
        self.files[app.PI_MODELS] = '{"providers": invalid}'
        self.assertEqual(self.run_gateway().failures, 1)
        self.assertEqual(self.files[app.PI_MODELS], '{"providers": invalid}')
        self.assertIn(app.PI_AUTH, self.files)
        self.unlink.assert_not_called()

    def test_auth_removal_failure_is_reported_without_contents(self):
        self.unlink.side_effect = PermissionError("test-saved-pi-key")
        self.assertEqual(self.run_gateway().failures, 1)
        self.assertIn(app.PI_AUTH, self.files)
        self.assertNotIn("test-saved-pi-key", self.output.getvalue())

    def test_pi_auth_is_never_read(self):
        def read(path):
            if path == app.PI_AUTH:
                raise AssertionError("must not read saved credentials")
            return self.files[path]

        with patch.object(Path, "read_text", read):
            self.assertEqual(self.run_gateway().failures, 0)
        self.unlink.assert_called_once_with(app.PI_AUTH)

    def test_pi_plugin_failure_preserves_auth(self):
        self.plugin_check.return_value = False
        self.run_gateway()
        self.plugin_check.assert_called_once()
        self.unlink.assert_not_called()
        self.assertIn(app.PI_AUTH, self.files)

    def test_grok_routes_all_model_tasks_through_proxy(self):
        self.assertEqual(self.run_gateway().failures, 0)
        config = tomlkit.parse(self.files[app.GROK_CONFIG])
        self.assertEqual(config["model"]["proxy"], {
            "name": "CLIProxyAPI",
            "model": "grok-4.6",
            "base_url": "https://gateway.example.test/v1",
            "api_key": "test-new-key",
            "api_backend": "responses",
            "supports_backend_search": True,
        })
        for purpose in ("default", "web_search", "session_summary", "image_description"):
            self.assertEqual(config["models"][purpose], "proxy")
        self.assertEqual(config["models"]["temperature"], 0.7)
        self.assertEqual(config["ui"]["theme"], "keep-theme")
        self.assertEqual(config["model"]["other"]["model"], "keep-model")
        self.assertIn("# keep Grok comment", self.files[app.GROK_CONFIG])
        for value in ("test-new-key", "test-old-grok-key", "gateway.example.test"):
            self.assertNotIn(value, self.output.getvalue())

    def test_grok_model_and_key_rotation(self):
        self.assertEqual(self.run_gateway().failures, 0)
        proxy = json.loads(self.files[app.AI_PROXY_CONFIG])
        proxy.update(grok_model="grok-custom-alias", api_key="test-rotated-key")
        self.files[app.AI_PROXY_CONFIG] = json.dumps(proxy)
        self.assertEqual(self.run_gateway().failures, 0)
        config = tomlkit.parse(self.files[app.GROK_CONFIG])
        self.assertEqual(config["model"]["proxy"]["model"], "grok-custom-alias")
        self.assertEqual(config["model"]["proxy"]["api_key"], "test-rotated-key")
        self.assertNotIn("test-rotated-key", self.output.getvalue())

    def test_invalid_grok_model_prevents_gateway_changes(self):
        for value in (None, "", "two words", 7, [], {}):
            with self.subTest(value=value):
                proxy = json.loads(self.files[app.AI_PROXY_CONFIG])
                proxy["grok_model"] = value
                self.files[app.AI_PROXY_CONFIG] = json.dumps(proxy)
                before = self.files.copy()
                self.assertEqual(self.run_gateway().failures, 1)
                self.assertEqual(self.files, before)
        self.unlink.assert_not_called()

    def test_missing_grok_config_created_privately(self):
        self.files.pop(app.GROK_CONFIG)

        @contextmanager
        def open_file(path, mode, encoding):
            self.assertEqual((path, mode, encoding), (app.GROK_CONFIG, "x", "utf-8"))
            stream = io.StringIO()
            yield stream
            self.files[path] = stream.getvalue()

        with patch.object(Path, "open", open_file):
            self.assertEqual(self.run_gateway().failures, 0)
        config = tomlkit.parse(self.files[app.GROK_CONFIG])
        self.assertEqual(config["models"]["web_search"], "proxy")
        self.assertEqual(config["model"]["proxy"]["api_key"], "test-new-key")
        if not app.WINDOWS:
            self.os_chmod.assert_called_once_with(app.GROK_CONFIG, 0o600)

    def test_missing_grok_config_dry_run_does_not_create_it(self):
        self.files.pop(app.GROK_CONFIG)
        self.assertEqual(self.run_gateway(dry_run=True).failures, 0)
        self.assertNotIn(app.GROK_CONFIG, self.files)
        self.open.assert_not_called()
        self.mkdir.assert_not_called()
        self.chmod.assert_not_called()

    def test_malformed_grok_config_is_preserved(self):
        self.files[app.GROK_CONFIG] = '[model.proxy\napi_key = "test-old-grok-key"'
        before = self.files[app.GROK_CONFIG]
        self.assertEqual(self.run_gateway().failures, 1)
        self.assertEqual(self.files[app.GROK_CONFIG], before)
        self.assertNotIn("test-old-grok-key", self.output.getvalue())

    def test_failed_grok_model_write_preserves_model_selections(self):
        def write(path, text):
            if path == app.GROK_CONFIG:
                raise PermissionError("test-private-detail")
            self.write(path, text)

        before = self.files[app.GROK_CONFIG]
        with patch.object(Path, "write_text", write):
            self.assertEqual(self.run_gateway().failures, 1)
        self.assertEqual(self.files[app.GROK_CONFIG], before)
        self.assertNotIn("test-private-detail", self.output.getvalue())


class PiPluginTests(unittest.TestCase):
    listing = "User packages:\n  npm:pi-anthropic-oauth\n    /example/plugin\n"

    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.object(app, "WINDOWS", False).start()
        self.which = patch.object(app.shutil, "which", return_value="/example/pi.sh").start()
        self.run = patch.object(app.subprocess, "run").start()
        self.output = io.StringIO()

    def result(self, stdout="", returncode=0):
        return subprocess.CompletedProcess([], returncode, stdout, "private-error-detail")

    def check(self, dry_run=False):
        self.state = app.State(dry_run)
        with redirect_stdout(self.output):
            return app.ensure_pi_anthropic_plugin_absent(self.state)

    def test_absent_plugin_is_not_uninstalled(self):
        self.run.return_value = self.result("User packages:\n  npm:pi-anthropic-oauth-other\n")
        self.assertTrue(self.check())
        self.run.assert_called_once_with(
            ["/example/pi.sh", "list"], capture_output=True, text=True, timeout=180
        )

    def test_windows_skips_plugin_commands(self):
        with patch.object(app, "WINDOWS", True):
            for dry_run in (False, True):
                self.assertTrue(self.check(dry_run=dry_run))
                self.assertEqual(self.state.failures, 0)
        self.which.assert_not_called()
        self.run.assert_not_called()

    def test_installed_plugin_is_uninstalled_and_verified(self):
        self.run.side_effect = [self.result(self.listing), self.result(), self.result()]
        self.assertTrue(self.check())
        self.assertEqual(self.run.call_args_list, [
            call(["/example/pi.sh", "list"], capture_output=True, text=True, timeout=180),
            call(["/example/pi.sh", "uninstall", "npm:pi-anthropic-oauth"], capture_output=True, text=True, timeout=180),
            call(["/example/pi.sh", "list"], capture_output=True, text=True, timeout=180),
        ])

    def test_dry_run_only_lists(self):
        self.run.return_value = self.result(self.listing)
        self.assertTrue(self.check(dry_run=True))
        self.assertEqual(self.run.call_count, 1)
        self.assertIn("WOULD", self.output.getvalue())
        self.assertIn("pi.sh uninstall npm:pi-anthropic-oauth", self.output.getvalue())

    def test_list_failure_prevents_uninstall(self):
        self.run.return_value = self.result(returncode=1)
        self.assertFalse(self.check())
        self.assertEqual(self.run.call_count, 1)
        self.assertEqual(self.state.failures, 1)
        self.assertNotIn("private-error-detail", self.output.getvalue())

    def test_uninstall_failure_is_reported(self):
        self.run.side_effect = [self.result(self.listing), self.result(returncode=1)]
        self.assertFalse(self.check())
        self.assertEqual(self.run.call_count, 2)
        self.assertEqual(self.state.failures, 1)

    def test_successful_exit_without_removal_is_failure(self):
        self.run.side_effect = [self.result(self.listing), self.result(), self.result(self.listing)]
        self.assertFalse(self.check())
        self.assertEqual(self.state.failures, 1)
        self.assertIn("still installed", self.output.getvalue())

    def test_missing_command_is_reported(self):
        self.which.return_value = None
        self.assertFalse(self.check())
        self.assertEqual(self.state.failures, 1)
        self.run.assert_not_called()

    def test_timeout_is_reported_without_command_output(self):
        self.run.side_effect = subprocess.TimeoutExpired("pi.sh", 180, output="private-output")
        self.assertFalse(self.check())
        self.assertEqual(self.state.failures, 1)
        self.assertNotIn("private-output", self.output.getvalue())


if __name__ == "__main__":
    unittest.main()
