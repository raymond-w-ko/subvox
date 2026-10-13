"""Offline regression tests for artifact-management.py."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "artifact_management", Path(__file__).with_name("artifact-management.py")
)
management = importlib.util.module_from_spec(spec)
spec.loader.exec_module(management)


class ArtifactManagementTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.responses = {
            "/user": {"login": "owner"},
            "/user/repos?affiliation=owner&per_page=100": [
                [{"full_name": "owner/first", "owner": {"login": "owner"}}],
                [
                    {"full_name": "owner/private", "owner": {"login": "OWNER"}},
                    {"full_name": "org/repo", "owner": {"login": "org"}},
                ],
            ],
            "/repos/owner/first/actions/artifacts?per_page=100": [
                {"artifacts": [{"id": 1, "name": "first"}]},
                {"artifacts": [{"id": 2, "name": "second\nline"}]},
            ],
            "/repos/owner/private/actions/artifacts?per_page=100": [{"artifacts": []}],
        }

    def gh(self, command, **kwargs):
        self.calls.append(command)
        self.assertEqual(command[:2], ["gh", "api"])
        self.assertEqual(kwargs, {"capture_output": True, "text": True, "check": True})
        endpoint = command[2]
        if command[-2:] == ["--method", "DELETE"]:
            return SimpleNamespace(stdout="", stderr="")
        response = self.responses[endpoint]
        if isinstance(response, Exception):
            raise response
        if isinstance(response, list):
            self.assertEqual(command[-2:], ["--paginate", "--slurp"])
        return SimpleNamespace(stdout=json.dumps(response), stderr="")

    def invoke(self, *args, gh=None):
        output = io.StringIO()
        with patch.object(management.subprocess, "run", side_effect=gh or self.gh):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                code = management.main(list(args))
        return code, output.getvalue()

    def deletions(self):
        return [call[2] for call in self.calls if "DELETE" in call]

    def test_default_lists_all_owned_repositories_without_deletion(self):
        code, output = self.invoke()
        self.assertEqual(code, 0)
        self.assertIn("owner/first: 2 artifact(s)", output)
        self.assertIn("owner/private: 0 artifact(s)", output)
        self.assertNotIn("org/repo", output)
        self.assertIn('"second\\nline"', output)
        self.assertEqual(self.deletions(), [])

    def test_explicit_repository_is_preview_only(self):
        code, _ = self.invoke("owner/first")
        self.assertEqual(code, 0)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.deletions(), [])

    def test_delete_requires_explicit_valid_repository_before_any_api_call(self):
        for args in [("--delete",), ("--delete", "first"), ("--delete", "owner/../other")]:
            with self.subTest(args=args), self.assertRaises(SystemExit) as error:
                self.invoke(*args)
            self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.calls, [])

    def test_delete_uses_entire_paginated_snapshot(self):
        code, _ = self.invoke("--delete", "owner/first")
        self.assertEqual(code, 0)
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.deletions(), [
            "/repos/owner/first/actions/artifacts/1",
            "/repos/owner/first/actions/artifacts/2",
        ])

    def test_failed_fetch_never_deletes(self):
        self.responses["/repos/owner/first/actions/artifacts?per_page=100"] = (
            subprocess.CalledProcessError(1, ["gh"], stderr="fetch failed")
        )
        code, output = self.invoke("--delete", "owner/first")
        self.assertEqual(code, 1)
        self.assertIn("fetch failed", output)
        self.assertEqual(self.deletions(), [])

    def test_invalid_later_page_never_deletes(self):
        self.responses["/repos/owner/first/actions/artifacts?per_page=100"][1] = {
            "artifacts": [{"id": "2/other", "name": "invalid"}]
        }
        code, _ = self.invoke("--delete", "owner/first")
        self.assertEqual(code, 1)
        self.assertEqual(self.deletions(), [])

    def test_delete_error_stops_remaining_requests(self):
        def fail_delete(command, **kwargs):
            result = self.gh(command, **kwargs)
            if "DELETE" in command:
                raise subprocess.CalledProcessError(1, command, stderr="delete failed")
            return result

        code, output = self.invoke("--delete", "owner/first", gh=fail_delete)
        self.assertEqual(code, 1)
        self.assertIn("delete failed", output)
        self.assertEqual(self.deletions(), ["/repos/owner/first/actions/artifacts/1"])

    def test_empty_repository_never_deletes(self):
        code, _ = self.invoke("--delete", "owner/private")
        self.assertEqual(code, 0)
        self.assertEqual(self.deletions(), [])


if __name__ == "__main__":
    unittest.main()
