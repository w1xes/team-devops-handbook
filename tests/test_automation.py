"""Behavioral tests for the shared commit convention and actual Git hooks."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_commit import validate
from changelog import render


class CommitFormatTests(unittest.TestCase):
    def test_valid_messages(self):
        for text in ["docs: описати запуск", "feat(cli)!: change output", "fix: handle EOF\n\nExplain why."]:
            with self.subTest(text=text):
                self.assertIsNone(validate(text))

    def test_invalid_messages(self):
        for text in ["", "fix2", "wip: try again", "Fix: typo", "feat:", "fix: x ", "fix: x\nbody", "docs: " + "x" * 67]:
            with self.subTest(text=text):
                self.assertIsNotNone(validate(text))

    def test_changelog_groups_and_marks_breaking_changes(self):
        text = render([
            ("abc1234", "feat(cli)!: change output", ""),
            ("def5678", "fix: reject errors", "BREAKING CHANGE: new exit status"),
            ("1234567", "wip", ""),
        ])
        self.assertIn("## feat", text)
        self.assertIn("**BREAKING** change output (`abc1234`)", text)
        self.assertIn("**BREAKING** reject errors", text)
        self.assertNotIn("wip", text)


class GitHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.run_git("init", "-b", "main")
        self.run_git("config", "user.name", "Hook test fixture")
        self.run_git("config", "user.email", "fixture@example.invalid")
        shutil.copytree(ROOT / ".githooks", self.path / ".githooks")
        shutil.copytree(ROOT / "scripts", self.path / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        self.run_git("config", "core.hooksPath", ".githooks")

    def run_git(self, *args):
        return subprocess.run(["git", *args], cwd=self.path, capture_output=True, text=True, check=True)

    def stage(self, text):
        (self.path / "file.txt").write_text(text, encoding="utf-8")
        self.run_git("add", "file.txt")

    def test_hooks_reject_whitespace_and_invalid_message_then_allow_valid_commit(self):
        self.stage("trailing space \n")
        bad_space = subprocess.run(["git", "commit", "-m", "docs: test spaces"], cwd=self.path, capture_output=True, text=True)
        self.assertNotEqual(bad_space.returncode, 0)
        self.assertIn("trailing whitespace", bad_space.stdout + bad_space.stderr)
        self.stage("clean\n")
        bad_message = subprocess.run(["git", "commit", "-m", "fix2"], cwd=self.path, capture_output=True, text=True)
        self.assertNotEqual(bad_message.returncode, 0)
        self.assertIn("Conventional Commits", bad_message.stderr)
        self.run_git("commit", "-m", "docs: record clean fixture")
        self.assertEqual(self.run_git("log", "-1", "--format=%s").stdout.strip(), "docs: record clean fixture")

    def test_changelog_reads_real_history_and_since(self):
        self.stage("first\n")
        self.run_git("commit", "-m", "docs: first entry")
        first = self.run_git("rev-parse", "HEAD").stdout.strip()
        self.stage("second\n")
        self.run_git("commit", "-m", "feat: second entry")
        result = subprocess.run([sys.executable, str(self.path / "scripts/changelog.py"), "--since", first], cwd=self.path, text=True, capture_output=True, check=True)
        self.assertIn("second entry", result.stdout)
        self.assertNotIn("first entry", result.stdout)


if __name__ == "__main__":
    unittest.main()
