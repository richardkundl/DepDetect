import json
import unittest
from pathlib import Path
from unittest.mock import patch

from depdetect import cli


SAMPLE_ROOT = Path(__file__).parent / "sample"
TEST_ROOT = Path(__file__).parent


class TestCli(unittest.TestCase):
    def run_main(self, *args: str) -> None:
        with patch("sys.argv", ["depdetect", *args]):
            cli.main()

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
                cli.main()

            self.assertTrue(json_path.exists())
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["classification"], "likely_scripts_only")
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
                cli.main()

            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["languages"], {"Python": 100.0})
            mock_linguist.assert_called_once_with(str(SAMPLE_ROOT / "negative"))
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_invalid_path_exits(self):
        missing_path = SAMPLE_ROOT / "does_not_exist"

        with self.assertRaises(SystemExit) as exc_info:
            self.run_main(str(missing_path))

        self.assertEqual(str(exc_info.exception), f"Not a directory: {missing_path}")

    def test_main_ignore_dir_excludes_nested_marker(self):
        json_path = TEST_ROOT / "_report_ignore_dir.json"

        try:
            self.run_main(
                str(SAMPLE_ROOT / "ignore_dir_custom"),
                "--ignore-dir",
                "skipme",
                "--json-out",
                str(json_path),
            )

            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["classification"], "likely_scripts_only")
            self.assertEqual(report["hits"], {})
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_without_ignore_dir_detects_nested_marker(self):
        json_path = TEST_ROOT / "_report_without_ignore_dir.json"

        try:
            self.run_main(
                str(SAMPLE_ROOT / "ignore_dir_custom"),
                "--json-out",
                str(json_path),
            )

            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["classification"], "likely_project")
            self.assertEqual(report["hits"]["python"], ["skipme/requirements.txt"])
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_max_depth_excludes_deep_marker(self):
        json_path = TEST_ROOT / "_report_max_depth_excluded.json"

        try:
            self.run_main(
                str(SAMPLE_ROOT / "max_depth_only"),
                "--max-depth",
                "1",
                "--json-out",
                str(json_path),
            )

            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["classification"], "likely_scripts_only")
            self.assertEqual(report["hits"], {})
        finally:
            json_path.unlink(missing_ok=True)

    def test_main_max_depth_allows_deep_marker_when_increased(self):
        json_path = TEST_ROOT / "_report_max_depth_included.json"

        try:
            self.run_main(
                str(SAMPLE_ROOT / "max_depth_only"),
                "--max-depth",
                "2",
                "--json-out",
                str(json_path),
            )

            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["classification"], "likely_project")
            self.assertEqual(
                report["hits"]["python"], ["level1/level2/requirements.txt"]
            )
        finally:
            json_path.unlink(missing_ok=True)

    @patch(
        "depdetect.cli.scanner.linguist",
        side_effect=SystemExit(
            "The --linguist option requires the `github-linguist` executable in PATH."
        ),
    )
    def test_main_linguist_missing_exits_cleanly(self, mock_linguist):
        with self.assertRaises(SystemExit) as exc_info:
            self.run_main(str(SAMPLE_ROOT / "negative"), "--linguist")

        self.assertEqual(
            str(exc_info.exception),
            "The --linguist option requires the `github-linguist` executable in PATH.",
        )
        mock_linguist.assert_called_once_with(str(SAMPLE_ROOT / "negative"))

    @patch(
        "depdetect.cli.scanner.linguist",
        side_effect=SystemExit("Language detection failed: command returned 1"),
    )
    def test_main_linguist_tool_failure_exits_cleanly(self, mock_linguist):
        with self.assertRaises(SystemExit) as exc_info:
            self.run_main(str(SAMPLE_ROOT / "negative"), "--linguist")

        self.assertEqual(
            str(exc_info.exception), "Language detection failed: command returned 1"
        )
        mock_linguist.assert_called_once_with(str(SAMPLE_ROOT / "negative"))

    @patch(
        "depdetect.cli.scanner.linguist",
        side_effect=SystemExit("Language detection returned invalid JSON output."),
    )
    def test_main_linguist_invalid_json_exits_cleanly(self, mock_linguist):
        with self.assertRaises(SystemExit) as exc_info:
            self.run_main(str(SAMPLE_ROOT / "negative"), "--linguist")

        self.assertEqual(
            str(exc_info.exception),
            "Language detection returned invalid JSON output.",
        )
        mock_linguist.assert_called_once_with(str(SAMPLE_ROOT / "negative"))


if __name__ == "__main__":
    unittest.main()
