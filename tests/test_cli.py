import json
import unittest
from pathlib import Path
from unittest.mock import patch

from depdetect import cli


SAMPLE_ROOT = Path(__file__).parent / "sample"
TEST_ROOT = Path(__file__).parent


class TestCli(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
