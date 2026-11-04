"""Offline theme tests. Run with uv run --with textual==8.2.8 this_file.py."""

import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from rich.color import Color
from textual.widgets import Button, Checkbox


spec = importlib.util.spec_from_file_location(
    "update_inputs", Path(__file__).with_name("update-inputs.py")
)
updater = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = updater
spec.loader.exec_module(updater)


class ThemeTests(unittest.IsolatedAsyncioTestCase):
    async def test_themes_mount_and_toggle_without_changing_update_state(self):
        for theme in updater.UPDATE_THEMES:
            with self.subTest(theme=theme):
                app = updater.UpdateInputsApp(
                    {"neru"}, updater.SystemTarget("Linux", "nixvac"), theme=theme
                )
                async with app.run_test(size=(150, 40)) as pilot:
                    self.assertEqual(app.theme, f"subvox-{theme}")
                    self.assertEqual(app.current_theme.dark, theme == "dark")
                    self.assertEqual(app.selected_inputs(), ("neru",))
                    candidate = Path("/unused/candidate.lock")
                    app.candidate = candidate
                    app.validated = True
                    app.set_busy(True)
                    await pilot.press("t")
                    self.assertEqual(
                        app.theme, "subvox-light" if theme == "dark" else "subvox-dark"
                    )
                    self.assertEqual(app.selected_inputs(), ("neru",))
                    self.assertEqual(app.candidate, candidate)
                    self.assertTrue(app.validated)
                    self.assertTrue(app.busy)
                    self.assertTrue(app.query_one("#generate", Button).disabled)
                    self.assertTrue(app.query_one("#input-neru", Checkbox).disabled)
                    await pilot.press("t")
                    self.assertEqual(app.theme, f"subvox-{theme}")

    def test_base_colors_are_in_the_standard_256_palette(self):
        palette = {
            Color.from_ansi(index).get_truecolor().hex for index in range(16, 256)
        }
        for theme in updater.UPDATE_THEMES.values():
            for name in (
                "primary", "secondary", "accent", "foreground", "background",
                "surface", "panel", "success", "warning", "error",
            ):
                self.assertIn(getattr(theme, name), palette, (theme.name, name))
            for color in theme.variables.values():
                self.assertIn(color, palette)

    def test_cli_theme_and_selection(self):
        for theme in updater.UPDATE_THEMES:
            with patch.object(sys, "argv", ["update", "--theme", theme, "core"]):
                with patch.object(updater, "UpdateInputsApp") as app:
                    updater.main()
            self.assertEqual(app.call_args.args[0], set(updater.CORE))
            self.assertEqual(app.call_args.kwargs, {"theme": theme})
            app.return_value.run.assert_called_once_with()

    def test_default_auto_detects(self):
        for mode in updater.UPDATE_THEMES:
            with patch.object(updater, "detect_terminal_theme", return_value=mode):
                app = updater.UpdateInputsApp(
                    set(), updater.SystemTarget("Linux", "nixvac")
                )
            self.assertEqual(app.theme, f"subvox-{mode}")

    def test_explicit_theme_skips_detection(self):
        with patch.object(updater, "detect_terminal_theme") as detect:
            updater.UpdateInputsApp(
                set(), updater.SystemTarget("Linux", "nixvac"), theme="light"
            )
        detect.assert_not_called()

    def test_cli_defaults_to_auto(self):
        with patch.object(sys, "argv", ["update"]):
            with patch.object(updater, "UpdateInputsApp") as app:
                updater.main()
        self.assertEqual(app.call_args.kwargs, {"theme": "auto"})


class DetectionTests(unittest.TestCase):
    def test_terminal_background_takes_priority_over_environment(self):
        for background, expected in (
            ((1, 1, 1), "light"),
            ((0.9, 0.9, 0.8), "light"),
            ((0, 0, 0), "dark"),
            ((0.1, 0.1, 0.2), "dark"),
        ):
            with self.subTest(background=background):
                with patch.object(
                    updater, "query_terminal_background", return_value=background
                ), patch.dict(updater.os.environ, {"COLORFGBG": "0;15"}):
                    self.assertEqual(updater.detect_terminal_theme(), expected)

    def test_environment_fallback(self):
        for value, expected in (
            ("15;0", "dark"), ("0;15", "light"),
            ("0;default;255", "light"), ("15;234", "dark"),
            ("", "dark"), ("invalid", "dark"), ("0;256", "dark"),
            ("0;-1", "dark"),
        ):
            with self.subTest(value=value):
                with patch.object(
                    updater, "query_terminal_background", return_value=None
                ), patch.dict(updater.os.environ, {"COLORFGBG": value}):
                    self.assertEqual(updater.detect_terminal_theme(), expected)

    def query_background(self, response, timeout=False):
        data = io.BytesIO(response)
        with (
            patch.object(sys.stdin, "isatty", return_value=True),
            patch.object(sys.stdout, "isatty", return_value=True),
            patch("builtins.open") as open_terminal,
            patch.object(updater.select, "select") as select_input,
            patch.object(updater.termios, "tcgetattr", return_value=["saved"]),
            patch.object(updater.tty, "setcbreak"),
            patch.object(updater.termios, "tcsetattr") as restore,
        ):
            terminal = open_terminal.return_value.__enter__.return_value
            terminal.fileno.return_value = 42
            terminal.read.side_effect = data.read
            # The first select checks for pending user input, before the query.
            calls = iter([([], [], [])])
            select_input.side_effect = lambda *_: next(
                calls, ([], [], []) if timeout else ([42], [], [])
            )
            result = updater.query_terminal_background()
            terminal.write.assert_called_once_with(b"\x1b]11;?\x1b\\")
            restore.assert_called_once_with(42, updater.termios.TCSANOW, ["saved"])
            return result

    def test_query_accepts_both_terminators_and_rgb_widths(self):
        for response, expected in (
            (b"\x1b]11;rgb:ffff/ffff/ffff\x07", (1, 1, 1)),
            (b"\x1b]11;rgb:00/00/00\x1b\\", (0, 0, 0)),
            (b"\x1b]11;rgb:f/0/0\x07", (1, 0, 0)),
        ):
            with self.subTest(response=response):
                self.assertEqual(self.query_background(response), expected)

    def test_query_timeout_and_malformed_reply_restore_terminal(self):
        self.assertIsNone(self.query_background(b"", timeout=True))
        self.assertIsNone(self.query_background(b"not a color\x07"))

    def test_non_interactive_query_does_not_open_terminal(self):
        with patch.object(sys.stdin, "isatty", return_value=False):
            with patch("builtins.open") as open_terminal:
                self.assertIsNone(updater.query_terminal_background())
        open_terminal.assert_not_called()


if __name__ == "__main__":
    unittest.main()
