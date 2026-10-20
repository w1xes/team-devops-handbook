"""Exercise the real configuration and CLI examples used in the handbook."""

from functools import partial
import http.server
from pathlib import Path
import subprocess
import tarfile
import tempfile
import threading
import unittest

from editorconfig import get_properties

ROOT = Path(__file__).resolve().parents[1]


class EditorConfigurationTests(unittest.TestCase):
    def test_effective_settings_for_four_file_types(self):
        for filename, size in [("demo.py", "4"), ("demo.sh", "4"), ("demo.md", "2")]:
            with self.subTest(filename=filename):
                props = get_properties(str(ROOT / filename))
                self.assertEqual(props["indent_size"], size)
                self.assertEqual(props["end_of_line"], "lf")
        self.assertEqual(get_properties(str(ROOT / "Makefile"))["indent_style"], "tab")
        self.assertEqual(get_properties(str(ROOT / "demo.md"))["trim_trailing_whitespace"], "false")

    def test_wrong_and_correct_conflict_resolutions_have_different_behavior(self):
        for variant, expected in [("wrong", "2"), ("correct", "4")]:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as folder:
                fixture = ROOT / "assets/conflict" / f"{variant}.editorconfig"
                Path(folder, ".editorconfig").write_bytes(fixture.read_bytes())
                props = get_properties(str(Path(folder, "demo.sh")))
                self.assertEqual(props["indent_size"], expected)
        self.assertEqual((ROOT / ".editorconfig").read_bytes(),
                         (ROOT / "assets/conflict/correct.editorconfig").read_bytes())


class IgnoreConfigurationTests(unittest.TestCase):
    def test_real_archive_environment_cache_and_compiled_binary_are_ignored(self):
        def status():
            return subprocess.check_output(
                ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT
            )
        before = status()
        build = ROOT / "build"
        created_build = not build.exists()
        build.mkdir(exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(prefix=".ignore-check.", dir=ROOT) as folder, \
                    tempfile.TemporaryDirectory(prefix="lab2-", dir=build) as output:
                temp = Path(folder)
                archive = temp / "sample.tar.gz"
                source = temp / "source.txt"
                source.write_text("sample\n")
                with tarfile.open(archive, "w:gz") as result:
                    result.add(source, arcname="source.txt")
                source.unlink()
                environment = temp / ".env"
                environment.write_text("LAB_EXAMPLE=dummy\n")
                cache = temp / "__pycache__" / "demo.pyc"
                cache.parent.mkdir()
                cache.write_bytes(b"test fixture")
                executable = Path(output, "demo")
                subprocess.run(["cc", "-x", "c", "-o", str(executable), "-"], cwd=ROOT,
                               input="int main(void) { return 0; }\n", text=True, check=True)
                subprocess.run([str(executable)], check=True)
                files = [archive, environment, cache, executable]
                result = subprocess.check_output(
                    ["git", "check-ignore", *[str(p.relative_to(ROOT)) for p in files]],
                    cwd=ROOT, text=True,
                )
                self.assertEqual(len(result.splitlines()), 4)
                self.assertEqual(status(), before)
        finally:
            if created_build:
                build.rmdir()


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class CurlReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        Path(cls.folder.name, "health.json").write_text('{"status":"ok"}\n')
        cls.server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietHandler, directory=cls.folder.name)
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.folder.cleanup()

    def request(self, path, fail=True):
        command = ["curl", "--disable", "--silent", "--show-error", "--noproxy", "127.0.0.1",
                   "--connect-timeout", "2", "--max-time", "5"]
        if fail:
            command.append("--fail-with-body")
        command.append(f"http://127.0.0.1:{self.server.server_port}/{path}")
        return subprocess.run(command, text=True, capture_output=True)

    def test_success_returns_documented_json_and_zero(self):
        result = self.request("health.json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '{"status":"ok"}\n')
        self.assertEqual(result.stderr, "")

    def test_missing_resource_fails_with_body(self):
        result = self.request("missing")
        self.assertEqual(result.returncode, 22)
        self.assertIn("404", result.stdout)
        self.assertIn("404", result.stderr)

    def test_missing_resource_without_fail_flag_returns_zero(self):
        result = self.request("missing", fail=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn("404", result.stdout)


if __name__ == "__main__":
    unittest.main()
