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

    def test_pi_builtin_overrides_and_auth_clearing(self):
        with redirect_stdout(self.output):
            app.setting_pi_gateway(app.State(False), "https://gateway.example.test", "test-new-key")
        providers = json.loads(self.files[app.PI_MODELS])["providers"]
        self.assertEqual(providers["other"], {"baseUrl": "https://other.example.test"})
        self.assertEqual(providers["openai"], {
            "baseUrl": "https://gateway.example.test/v1", "apiKey": "test-new-key",
        })
        self.assertEqual(providers["xai"], {
            "baseUrl": "https://gateway.example.test/v1", "apiKey": "test-new-key",
        })
        self.assertEqual(providers["anthropic"], {
            "baseUrl": "https://gateway.example.test", "apiKey": "test-new-key",
            "authHeader": True, "headers": {"x-api-key": ""},
        })
        self.assertEqual(self.files[app.PI_AUTH], "{}\n")
        self.unlink.assert_not_called()
        for private in ("test-new-key", "test-saved-pi-key", "gateway.example.test"):
            self.assertNotIn(private, self.output.getvalue())

    def test_pi_dry_run_keeps_credentials(self):
        state = self.run_gateway(dry_run=True)
        self.assertEqual(state.failures, 0)
        self.assertIn(app.PI_AUTH, self.files)
        self.assertIn("all saved provider credentials", self.output.getvalue())
        self.unlink.assert_not_called()

    def test_missing_pi_auth_is_created(self):
        self.files.pop(app.PI_AUTH)
        self.assertEqual(self.run_gateway().failures, 0)
        self.assertEqual(self.files[app.PI_AUTH], "{}\n")
        self.assertIn(f"created {app.PI_AUTH}", self.output.getvalue())

    def test_missing_pi_auth_dry_run_reports_creation(self):
        self.files.pop(app.PI_AUTH)
        self.assertEqual(self.run_gateway(dry_run=True).failures, 0)
        self.assertNotIn(app.PI_AUTH, self.files)
        self.assertIn(f"create {app.PI_AUTH}", self.output.getvalue())

    def test_pi_key_syntax_is_literal(self):
        with redirect_stdout(self.output):
            app.setting_pi_gateway(app.State(False), "https://gateway.example.test", "!${TEST_KEY}$suffix")
        providers = json.loads(self.files[app.PI_MODELS])["providers"]
        for name in ("openai", "xai", "anthropic"):
            self.assertEqual(providers[name]["apiKey"], "$!$${TEST_KEY}$$suffix")

    def test_missing_pi_models_created_before_auth_clearing(self):
        self.files.pop(app.PI_MODELS)

        @contextmanager
        def open_file(path, mode, encoding):
            self.assertEqual((path, mode, encoding), (app.PI_MODELS, "x", "utf-8"))
            stream = io.StringIO()
            yield stream
            self.files[path] = stream.getvalue()

        def write(path, text):
            if path == app.PI_AUTH:
                providers = json.loads(self.files[app.PI_MODELS])["providers"]
                self.assertEqual(set(providers), {"openai", "xai", "anthropic"})
            self.write(path, text)

        with patch.object(Path, "open", open_file), patch.object(Path, "write_text", write):
            self.assertEqual(self.run_gateway().failures, 0)
        if not app.WINDOWS:
            self.os_chmod.assert_called_once_with(app.PI_MODELS, 0o600)
        self.assertEqual(self.files[app.PI_AUTH], "{}\n")
        self.unlink.assert_not_called()

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

    def test_auth_clearing_failure_is_reported_without_contents(self):
        def write(path, text):
            if path == app.PI_AUTH:
                raise PermissionError("test-saved-pi-key")
            self.write(path, text)

        with patch.object(Path, "write_text", write):
            self.assertEqual(self.run_gateway().failures, 1)
        self.assertIn(app.PI_AUTH, self.files)
        self.assertNotIn("test-saved-pi-key", self.output.getvalue())

    def test_pi_auth_is_read_without_leaking_credentials(self):
        reads = []

        def read(path):
            reads.append(path)
            return self.files[path]

        with patch.object(Path, "read_text", read):
            self.assertEqual(self.run_gateway().failures, 0)
        self.assertIn(app.PI_AUTH, reads)
        self.assertEqual(self.files[app.PI_AUTH], "{}\n")
        self.unlink.assert_not_called()
        self.assertNotIn("test-saved-pi-key", self.output.getvalue())

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


class ClaudePluginRemovalTests(unittest.TestCase):
    plugin_id = "fable-advisor@fable-advisor"

    def setUp(self):
        self.addCleanup(patch.stopall)
        self.query = patch.object(app, "claude_json", return_value=[]).start()
        self.run = patch.object(app, "claude_run", return_value=True).start()
        self.output = io.StringIO()
        self.plugin = {"id": self.plugin_id, "scope": "user", "enabled": True}

    def apply(self, dry_run=False):
        state = app.State(dry_run)
        with redirect_stdout(self.output):
            app.ensure_claude_plugin_absent(state, self.plugin_id)
        return state

    def test_absent_plugin_does_not_run_uninstall(self):
        self.assertEqual(self.apply().failures, 0)
        self.query.assert_called_once_with("plugin", "list")
        self.run.assert_not_called()

    def test_installed_or_disabled_plugin_is_uninstalled_and_verified(self):
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                self.plugin["enabled"] = enabled
                self.query.reset_mock()
                self.run.reset_mock()
                self.query.side_effect = [[self.plugin], []]
                self.assertEqual(self.apply().failures, 0)
                self.run.assert_called_once_with(
                    "plugin", "uninstall", self.plugin_id, "--scope", "user"
                )
                self.assertEqual(self.query.call_args_list, [call("plugin", "list")] * 2)

    def test_project_and_unrelated_plugins_are_not_removed(self):
        self.query.return_value = [
            {"id": self.plugin_id, "scope": "project"},
            {"id": "codex@openai-codex", "scope": "user"},
        ]
        self.assertEqual(self.apply().failures, 0)
        self.run.assert_not_called()

    def test_dry_run_only_queries_and_reports_uninstall(self):
        self.query.return_value = [self.plugin]
        self.assertEqual(self.apply(dry_run=True).failures, 0)
        self.query.assert_called_once_with("plugin", "list")
        self.run.assert_not_called()
        self.assertIn(f"claude plugin uninstall {self.plugin_id} --scope user", self.output.getvalue())
        self.assertNotIn("FIXED", self.output.getvalue())

    def test_successful_exit_without_removal_is_failure(self):
        self.query.return_value = [self.plugin]
        self.assertEqual(self.apply().failures, 1)
        self.assertEqual(self.query.call_count, 2)
        self.assertIn("still installed after uninstall", self.output.getvalue())
        self.assertNotIn("FIXED", self.output.getvalue())

    def test_uninstall_nonzero_exit_is_failure(self):
        self.query.return_value = [self.plugin]
        self.run.return_value = False
        self.assertEqual(self.apply().failures, 1)
        self.query.assert_called_once_with("plugin", "list")
        self.assertNotIn("FIXED", self.output.getvalue())

    def test_query_errors_prevent_uninstall(self):
        for error in (OSError(), RuntimeError(), ValueError(),
                      subprocess.TimeoutExpired("claude", 60)):
            with self.subTest(error=type(error)):
                self.query.side_effect = error
                self.assertEqual(self.apply().failures, 1)
                self.run.assert_not_called()

    def test_malformed_listing_is_failure(self):
        for listing in (None, {}, "invalid", [None]):
            with self.subTest(listing=listing):
                self.query.return_value = listing
                self.assertEqual(self.apply().failures, 1)
                self.run.assert_not_called()

    def test_uninstall_and_verification_errors_are_reported(self):
        self.query.return_value = [self.plugin]
        self.run.side_effect = subprocess.TimeoutExpired("claude", 180)
        self.assertEqual(self.apply().failures, 1)
        self.run.side_effect = None
        self.query.side_effect = [[self.plugin], RuntimeError("verification failed")]
        self.assertEqual(self.apply().failures, 1)
        self.assertNotIn("FIXED", self.output.getvalue())

    def test_settings_remove_fable_without_reinstalling_it(self):
        with patch.object(app, "ensure_claude_plugin") as install:
            state = app.State(False)
            with redirect_stdout(self.output):
                app.setting_claude_plugins(state)
        self.assertEqual(state.failures, 0)
        self.assertIn(self.plugin_id, app.CLAUDE_UNINSTALL_PLUGINS)
        self.assertNotIn(self.plugin_id, [entry[0] for entry in app.CLAUDE_PLUGINS])
        install.assert_called_once_with(state, "codex@openai-codex", "openai-codex", "openai/codex-plugin-cc")


class SkillSymlinkTests(unittest.TestCase):
    """Use an in-memory filesystem; never touch the user's skill directories."""

    def setUp(self):
        self.home = Path("/test-home")
        self.source = Path("/test-repo/ai/skills")
        self.targets = [self.home / name / "skills" for name in (".codex", ".agents", ".claude")]
        self.directories = {self.source}
        self.files = set()
        self.links = {}
        self.output = io.StringIO()
        self.addCleanup(patch.stopall)
        patch.object(app, "HOME", self.home).start()
        patch.object(app, "SKILLS_DIR", self.source).start()
        patch.dict(app.os.environ, {"CODEX_HOME": ""}).start()
        patch.object(Path, "iterdir", lambda path: self.iterdir(path)).start()
        patch.object(Path, "exists", lambda path: self.exists(path)).start()
        patch.object(Path, "is_dir", lambda path: path in self.directories).start()
        patch.object(Path, "is_file", lambda path: path in self.files).start()
        patch.object(Path, "is_symlink", lambda path: path in self.links).start()
        patch.object(Path, "resolve", lambda path: self.links.get(path, path)).start()
        patch.object(Path, "stat", lambda path: self.stat(path)).start()
        self.mkdir = patch.object(Path, "mkdir", autospec=True).start()
        self.mkdir.side_effect = lambda path, **kwargs: self.directories.add(path)
        self.unlink = patch.object(Path, "unlink", autospec=True).start()
        self.unlink.side_effect = lambda path: self.links.pop(path)
        self.symlink = patch.object(Path, "symlink_to", autospec=True).start()
        self.symlink.side_effect = lambda path, source, **kwargs: self.links.update({path: source})
        self.run = patch.object(app.subprocess, "run").start()

    def exists(self, path):
        resolved = self.links.get(path, path)
        return resolved in self.directories or resolved in self.files

    def stat(self, path):
        if not self.exists(path):
            raise FileNotFoundError(str(path))
        return object()

    def iterdir(self, path):
        if path not in self.directories:
            raise FileNotFoundError(str(path))
        return iter(entry for entry in self.directories | self.files | self.links.keys()
                    if entry.parent == path)

    def add_skill(self, name="review", manifest=True):
        source = self.source / name
        self.directories.add(source)
        if manifest:
            self.files.add(source / "SKILL.md")
        return source

    def apply(self, dry_run=False):
        state = app.State(dry_run)
        with redirect_stdout(self.output):
            app.setting_skill_symlinks(state)
        self.run.assert_not_called()
        return state

    def test_links_all_targets_and_is_idempotent(self):
        source = self.add_skill()
        self.assertEqual(self.apply().failures, 0)
        self.assertEqual(self.links, {target / source.name: source for target in self.targets})
        self.assertEqual(self.symlink.call_count, 3)
        self.assertEqual(self.apply().warnings, 0)
        self.assertEqual(self.symlink.call_count, 3)
        self.symlink.assert_called_with(self.targets[-1] / source.name, source, target_is_directory=True)

    def test_codex_home_override(self):
        source = self.add_skill()
        with patch.dict(app.os.environ, {"CODEX_HOME": "/custom-codex"}):
            self.assertEqual(self.apply().failures, 0)
        self.assertEqual(self.links[Path("/custom-codex/skills/review")], source)
        self.assertNotIn(self.targets[0], self.directories)

    def test_skip_missing_manifest_and_claude_subagents(self):
        self.add_skill("no-manifest", manifest=False)
        for name in ("claude-subagent", "fable-subagent"):
            self.add_skill(name)
        state = self.apply()
        self.assertEqual(state.warnings, 1)
        self.assertEqual(len(self.links), 4)
        self.assertFalse(any(path.parent == self.targets[2] for path in self.links))

    def test_removes_deleted_skills_and_repairs_current_skill(self):
        source = self.add_skill()
        self.directories.update(self.targets)
        stale = self.targets[0] / "removed-skill"
        broken_current = self.targets[0] / source.name
        self.links.update({stale: self.source / "removed-skill",
                           broken_current: Path("/old-checkout/review")})
        self.assertEqual(self.apply().failures, 0)
        self.assertNotIn(stale, self.links)
        self.assertEqual(self.links[broken_current], source)
        self.assertCountEqual(self.unlink.call_args_list, [call(stale), call(broken_current)])

    def test_preserves_real_entries_valid_foreign_links_and_nested_links(self):
        source = self.add_skill()
        self.directories.update(self.targets)
        local_dir = self.targets[0] / source.name
        local_file = self.targets[1] / source.name
        foreign_link = self.targets[2] / source.name
        foreign_source = Path("/other-skills/review")
        self.directories.update({local_dir, foreign_source})
        self.files.add(local_file)
        self.links[foreign_link] = foreign_source
        nested = local_dir / "nested-broken-link"
        self.links[nested] = Path("/missing")
        before = self.links.copy()
        self.assertEqual(self.apply().warnings, 3)
        self.assertEqual(self.links, before)
        self.unlink.assert_not_called()
        self.symlink.assert_not_called()

    def test_dry_run_reports_cleanup_and_relink_without_mutation(self):
        self.add_skill()
        self.directories.add(self.targets[0])
        broken = self.targets[0] / "review"
        self.links[broken] = Path("/missing")
        before = self.links.copy()
        self.assertEqual(self.apply(dry_run=True).failures, 0)
        self.assertEqual(self.links, before)
        self.assertIn("remove broken symlink", self.output.getvalue())
        self.assertEqual(self.output.getvalue().count("skills: link "), 3)
        self.mkdir.assert_not_called()
        self.unlink.assert_not_called()
        self.symlink.assert_not_called()

    def test_missing_source_does_not_clean_targets(self):
        self.directories.remove(self.source)
        self.assertEqual(self.apply().failures, 1)
        self.mkdir.assert_not_called()
        self.unlink.assert_not_called()
        self.symlink.assert_not_called()

    def test_link_failure_does_not_stop_other_targets(self):
        self.add_skill()
        self.symlink.side_effect = [PermissionError("symlink privilege required"), None, None]
        self.assertEqual(self.apply().failures, 1)
        self.assertEqual(self.symlink.call_count, 3)

    def test_unlink_failure_preserves_broken_link(self):
        self.add_skill()
        self.directories.add(self.targets[0])
        broken = self.targets[0] / "review"
        self.links[broken] = Path("/missing")
        self.unlink.side_effect = PermissionError("cannot unlink")
        state = self.apply()
        self.assertEqual(state.failures, 1)
        self.assertEqual(self.links[broken], Path("/missing"))
        self.assertEqual(self.symlink.call_count, 2)

    def test_stat_permission_error_is_not_treated_as_dangling(self):
        self.directories.add(self.targets[0])
        self.links[self.targets[0] / "inaccessible"] = Path("/private")
        with patch.object(Path, "stat", side_effect=PermissionError("cannot stat")):
            self.assertEqual(self.apply().failures, 1)
        self.unlink.assert_not_called()


if __name__ == "__main__":
    unittest.main()
