import unittest
from unittest.mock import patch, MagicMock
from depdetect.scanner import folder_scanner


class TestFolderScanner(unittest.TestCase):
    @patch("depdetect.scanner.folder_scanner.Path")
    def test_scan_invalid_directory(self, mock_path):
        mock_path.return_value.exists.return_value = False
        mock_path.return_value.is_dir.return_value = False
        with self.assertRaises(SystemExit):
            folder_scanner.scan("invalid/path", 1, [], "")

    @patch("depdetect.scanner.folder_scanner.os.walk")
    @patch("depdetect.scanner.folder_scanner.Path")
    @patch("depdetect.scanner.folder_scanner.constant")
    def test_scan_detects_markers(
        self, mock_constant, mock_path, mock_walk
    ):
        # Setup constants
        mock_constant.DEFAULT_IGNORE_DIRS = set()
        mock_constant.SCRIPT_EXTENSIONS = {".py"}
        mock_constant.TEXT_EXTENSIONS = {".txt"}
        mock_constant.MARKERS = {
            "scas": {"files": {"requirements.txt"}, "globs": set()},
            "infra": {"files": set(), "globs": {"infra/*"}},
            "artifacts": {"files": set(), "globs": set()},
        }
        mock_constant.SCA_KINDS = ["scas"]
        mock_constant.INFRA_KINDS = ["infra"]

        # Setup os.walk
        mock_walk.return_value = [
            ("root", ["src"], ["requirements.txt", "script.py", "notes.txt"]),
            ("root/infra", [], ["infra_file.tf"]),
        ]

        # Setup Path
        def resolve_side_effect(file):
            mock = MagicMock()
            mock.suffix = "." + file.split(".")[-1] if "." in file else ""
            mock.resolve.return_value = mock
            # Simulate relative_to returning a mock with correct as_posix and parts
            rel_path = file
            mock.relative_to.return_value = MagicMock(
                parts=rel_path.split("/"), as_posix=lambda: rel_path
            )
            return mock

        mock_path.side_effect = resolve_side_effect

        result = folder_scanner.scan("root", 2, [], "")
        self.assertEqual(result["classification"], "likely_project")
        self.assertIn("scas", result["hits"])
        self.assertEqual(result["counts"]["script_files"], 1)
        self.assertEqual(result["counts"]["text_files"], 2)

    def test_should_skip_dir(self):
        self.assertTrue(folder_scanner.should_skip_dir("venv", {"venv", ".git"}))
        self.assertFalse(folder_scanner.should_skip_dir("src", {"venv", ".git"}))

    def test_match_any_glob(self):
        globs = {"*.py", "docs/*"}
        self.assertTrue(folder_scanner.match_any_glob("main.py", globs))
        self.assertTrue(folder_scanner.match_any_glob("docs/readme.md", globs))
        self.assertFalse(folder_scanner.match_any_glob("image.png", globs))


if __name__ == "__main__":
    unittest.main()
