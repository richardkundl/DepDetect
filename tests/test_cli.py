import json
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from depdetect import cli
from depdetect.scanner.errors import (
    InvalidRootError,
    LinguistExecutionError,
    LinguistOutputError,
    LinguistUnavailableError,
)


SAMPLE_ROOT = Path(__file__).parent / "sample"
TEST_ROOT = Path(__file__).parent


class TestCli(unittest.TestCase):
    def run_main(self, *args: str) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with (
            patch("sys.argv", ["depdetect", *args]),
            patch("sys.stdout", stdout),
            patch("sys.stderr", stderr),
        ):
            exit_code = cli.main()
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def read_json_report(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def assert_json_contract(
        self,
        report: dict,
        *,
        classification: str,
        confidence: str,
        files_total: int,
        script_files: int,
        text_files: int,
    ) -> None:
        self.assertEqual(
            set(report.keys()),
            {"root", "classification", "confidence", "counts", "hits", "notes"},
        )
        self.assertIsInstance(report["root"], str)
        self.assertEqual(report["classification"], classification)
        self.assertEqual(report["confidence"], confidence)
        self.assertEqual(
            report["counts"],
            {
                "files_total": files_total,
                "script_files": script_files,
                "text_files": text_files,
            },
        )
        self.assertIsInstance(report["hits"], dict)
        self.assertEqual(len(report["notes"]), 3)
        self.assertTrue(all(isinstance(note, str) for note in report["notes"]))

    def test_parse_args_supports_linguist_flag(self):
        with patch("sys.argv", ["depdetect", "tests/sample/negative", "--linguist"]):
            args = cli.parse_args()

        self.assertEqual(args.path, "tests/sample/negative")
        self.assertTrue(args.linguist)

    def test_main_writes_json_report_without_linguist(self):
        json_path = TEST_ROOT / "_report_without_linguist.json"

        try:
            with patch(
                "sys.argv",
                [
                    "depdetect",
                    str(SAMPLE_ROOT / "negative"),
                    "--json-out",
                    str(json_path),
                ],
            ):
                exit_code = cli.main()

            self.assertEqual(exit_code, cli.EXIT_OK)
            self.assertTrue(json_path.exists())
            report = self.read_json_report(json_path)
            self.assert_json_contract(
                report,
                classification="likely_scripts_only",
                confidence="low",
                files_total=1,
                script_files=0,
                text_files=1,
            )
            self.assertEqual(report["hits"], {})
            self.assertNotIn("languages", report)
        finally:
            json_path.unlink(missing_ok=True)

    @patch("depdetect.cli.scanner.linguist", return_value={"Python": 100.0})
    def test_main_adds_languages_when_linguist_enabled(self, mock_linguist):
        json_path = TEST_ROOT / "_report_with_linguist.json"

        try:
            with patch(
                "sys.argv",
                [
                    "depdetect",
                    str(SAMPLE_ROOT / "negative"),
                    "--json-out",
                    str(json_path),
                    "--linguist",
                ],
            ):
                exit_code = cli.main()

            self.assertEqual(exit_code, cli.EXIT_OK)
            report = self.read_json_report(json_path)
            self.assertEqual(report["languages"], {"Python": 100.0})
            mock_linguist.assert_called_once_with(str(SAMPLE_ROOT / "negative"))
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_invalid_path_exits(self):
        missing_path = SAMPLE_ROOT / "does_not_exist"

        with (
            patch("depdetect.cli.scanner.scan", side_effect=InvalidRootError(f"Not a directory: {missing_path}")),
            patch("sys.argv", ["depdetect", str(missing_path)]),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()) as stderr,
        ):
            with self.assertRaises(SystemExit) as exc_info:
                cli.main()

        self.assertEqual(exc_info.exception.code, cli.EXIT_INVALID_INPUT)
        self.assertEqual(stderr.getvalue().strip(), f"Not a directory: {missing_path}")

    def test_main_unexpected_error_exits_with_internal_code(self):
        with (
            patch("depdetect.cli.scanner.scan", side_effect=RuntimeError("boom")),
            patch("sys.argv", ["depdetect", str(SAMPLE_ROOT / "negative")]),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()) as stderr,
        ):
            with self.assertRaises(SystemExit) as exc_info:
                cli.main()

        self.assertEqual(exc_info.exception.code, cli.EXIT_INTERNAL_ERROR)
        self.assertEqual(stderr.getvalue().strip(), "Unexpected error: boom")

    def test_main_ignore_dir_excludes_nested_marker(self):
        json_path = TEST_ROOT / "_report_ignore_dir.json"

        try:
            exit_code, stdout, stderr = self.run_main(
                str(SAMPLE_ROOT / "ignore_dir_custom"),
                "--ignore-dir",
                "skipme",
                "--json-out",
                str(json_path),
            )

            self.assertEqual(exit_code, cli.EXIT_OK)
            self.assertIn("No known project/manifest markers found.", stdout)
            self.assertEqual(stderr, "")
            report = self.read_json_report(json_path)
            self.assert_json_contract(
                report,
                classification="likely_scripts_only",
                confidence="low",
                files_total=0,
                script_files=0,
                text_files=0,
            )
            self.assertEqual(report["hits"], {})
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_without_ignore_dir_detects_nested_marker(self):
        json_path = TEST_ROOT / "_report_without_ignore_dir.json"

        try:
            exit_code, stdout, stderr = self.run_main(
                str(SAMPLE_ROOT / "ignore_dir_custom"),
                "--json-out",
                str(json_path),
            )

            self.assertEqual(exit_code, cli.EXIT_OK)
            self.assertIn("Detected markers:", stdout)
            self.assertEqual(stderr, "")
            report = self.read_json_report(json_path)
            self.assert_json_contract(
                report,
                classification="likely_project",
                confidence="medium",
                files_total=1,
                script_files=0,
                text_files=1,
            )
            self.assertEqual(report["hits"]["python"], ["skipme/requirements.txt"])
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_max_depth_excludes_deep_marker(self):
        json_path = TEST_ROOT / "_report_max_depth_excluded.json"

        try:
            exit_code, _stdout, stderr = self.run_main(
                str(SAMPLE_ROOT / "max_depth_only"),
                "--max-depth",
                "1",
                "--json-out",
                str(json_path),
            )

            self.assertEqual(exit_code, cli.EXIT_OK)
            self.assertEqual(stderr, "")
            report = self.read_json_report(json_path)
            self.assert_json_contract(
                report,
                classification="likely_scripts_only",
                confidence="low",
                files_total=0,
                script_files=0,
                text_files=0,
            )
            self.assertEqual(report["hits"], {})
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_max_depth_allows_deep_marker_when_increased(self):
        json_path = TEST_ROOT / "_report_max_depth_included.json"

        try:
            exit_code, stdout, stderr = self.run_main(
                str(SAMPLE_ROOT / "max_depth_only"),
                "--max-depth",
                "2",
                "--json-out",
                str(json_path),
            )

            self.assertEqual(exit_code, cli.EXIT_OK)
            self.assertIn("level1/level2/requirements.txt", stdout)
            self.assertEqual(stderr, "")
            report = self.read_json_report(json_path)
            self.assert_json_contract(
                report,
                classification="likely_project",
                confidence="medium",
                files_total=1,
                script_files=0,
                text_files=1,
            )
            self.assertEqual(
                report["hits"]["python"], ["level1/level2/requirements.txt"]
            )
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_mixed_language_report_matches_json_contract(self):
        json_path = TEST_ROOT / "_report_mixed_language.json"

        try:
            exit_code, stdout, stderr = self.run_main(
                str(SAMPLE_ROOT / "mixed_language"),
                "--json-out",
                str(json_path),
            )

            self.assertEqual(exit_code, cli.EXIT_OK)
            self.assertIn("Classification: likely_project (confidence: high)", stdout)
            self.assertEqual(stderr, "")
            report = self.read_json_report(json_path)
            self.assert_json_contract(
                report,
                classification="likely_project",
                confidence="high",
                files_total=4,
                script_files=1,
                text_files=0,
            )
            self.assertEqual(
                report["hits"],
                {
                    "container": ["Dockerfile"],
                    "node": ["package.json"],
                    "python": ["pyproject.toml"],
                },
            )
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_node_workspace_marker_matches_json_contract(self):
        json_path = TEST_ROOT / "_report_node_nx.json"

        try:
            exit_code, stdout, stderr = self.run_main(
                str(SAMPLE_ROOT / "node_nx"),
                "--json-out",
                str(json_path),
            )

            self.assertEqual(exit_code, cli.EXIT_OK)
            self.assertIn("Detected markers:", stdout)
            self.assertEqual(stderr, "")
            report = self.read_json_report(json_path)
            self.assert_json_contract(
                report,
                classification="likely_project",
                confidence="medium",
                files_total=1,
                script_files=0,
                text_files=0,
            )
            self.assertEqual(report["hits"], {"node": ["nx.json"]})
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_python_env_marker_matches_json_contract(self):
        json_path = TEST_ROOT / "_report_python_requirements_glob.json"

        try:
            exit_code, stdout, stderr = self.run_main(
                str(SAMPLE_ROOT / "python_requirements_glob"),
                "--json-out",
                str(json_path),
            )

            self.assertEqual(exit_code, cli.EXIT_OK)
            self.assertIn("requirements-dev.txt", stdout)
            self.assertEqual(stderr, "")
            report = self.read_json_report(json_path)
            self.assert_json_contract(
                report,
                classification="likely_project",
                confidence="medium",
                files_total=1,
                script_files=0,
                text_files=1,
            )
            self.assertEqual(report["hits"], {"python": ["requirements-dev.txt"]})
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_dotnet_central_package_marker_matches_json_contract(self):
        json_path = TEST_ROOT / "_report_dotnet_directory_packages.json"

        try:
            exit_code, stdout, stderr = self.run_main(
                str(SAMPLE_ROOT / "dotnet_directory_packages"),
                "--json-out",
                str(json_path),
            )

            self.assertEqual(exit_code, cli.EXIT_OK)
            self.assertIn("Directory.Packages.props", stdout)
            self.assertEqual(stderr, "")
            report = self.read_json_report(json_path)
            self.assert_json_contract(
                report,
                classification="likely_project",
                confidence="medium",
                files_total=1,
                script_files=0,
                text_files=0,
            )
            self.assertEqual(report["hits"], {"dotnet": ["Directory.Packages.props"]})
        finally:
            json_path.unlink(missing_ok=True)

    @patch(
        "depdetect.cli.scanner.linguist",
        side_effect=LinguistUnavailableError(
            "The --linguist option requires the `github-linguist` executable in PATH."
        ),
    )
    def test_main_linguist_missing_exits_cleanly(self, mock_linguist):
        with (
            patch("sys.argv", ["depdetect", str(SAMPLE_ROOT / "negative"), "--linguist"]),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()) as stderr,
        ):
            with self.assertRaises(SystemExit) as exc_info:
                cli.main()

        self.assertEqual(exc_info.exception.code, cli.EXIT_EXTERNAL_TOOL_ERROR)
        self.assertEqual(
            stderr.getvalue().strip(),
            "The --linguist option requires the `github-linguist` executable in PATH.",
        )
        mock_linguist.assert_called_once_with(str(SAMPLE_ROOT / "negative"))

    @patch(
        "depdetect.cli.scanner.linguist",
        side_effect=LinguistExecutionError("Language detection failed: command returned 1"),
    )
    def test_main_linguist_tool_failure_exits_cleanly(self, mock_linguist):
        with (
            patch("sys.argv", ["depdetect", str(SAMPLE_ROOT / "negative"), "--linguist"]),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()) as stderr,
        ):
            with self.assertRaises(SystemExit) as exc_info:
                cli.main()

        self.assertEqual(exc_info.exception.code, cli.EXIT_EXTERNAL_TOOL_ERROR)
        self.assertEqual(
            stderr.getvalue().strip(), "Language detection failed: command returned 1"
        )
        mock_linguist.assert_called_once_with(str(SAMPLE_ROOT / "negative"))

    @patch(
        "depdetect.cli.scanner.linguist",
        side_effect=LinguistOutputError("Language detection returned invalid JSON output."),
    )
    def test_main_linguist_invalid_json_exits_cleanly(self, mock_linguist):
        with (
            patch("sys.argv", ["depdetect", str(SAMPLE_ROOT / "negative"), "--linguist"]),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()) as stderr,
        ):
            with self.assertRaises(SystemExit) as exc_info:
                cli.main()

        self.assertEqual(exc_info.exception.code, cli.EXIT_EXTERNAL_TOOL_ERROR)
        self.assertEqual(
            stderr.getvalue().strip(),
            "Language detection returned invalid JSON output.",
        )
        mock_linguist.assert_called_once_with(str(SAMPLE_ROOT / "negative"))


if __name__ == "__main__":
    unittest.main()
