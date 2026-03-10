import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from depdetect.scanner import folder_scanner
from depdetect.scanner.constant import constant


SAMPLE_ROOT = Path(__file__).parent / "sample"


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

    def test_dotnet_globs_include_slnx(self):
        self.assertIn("*.slnx", constant.MARKERS["dotnet"]["globs"])

    def test_artifacts_include_nupkg(self):
        self.assertIn("*.nupkg", constant.MARKERS["artifacts"]["globs"])

    def test_script_extensions_include_added_shell_and_language_types(self):
        for extension in {
            ".bat",
            ".cmd",
            ".fish",
            ".ksh",
            ".mjs",
            ".cjs",
            ".jsx",
            ".tsx",
            ".java",
            ".kt",
            ".groovy",
            ".scala",
            ".go",
            ".rs",
            ".swift",
            ".cs",
            ".lua",
        }:
            self.assertIn(extension, constant.SCRIPT_EXTENSIONS)

    def test_scan_detects_new_dotnet_slnx_fixture(self):
        result = folder_scanner.scan(str(SAMPLE_ROOT / "dotnet_slnx"), 2, [], "")
        self.assertEqual(result["classification"], "likely_project")
        self.assertEqual(result["hits"]["dotnet"], ["sample.slnx"])

    def test_scan_detects_new_nupkg_fixture(self):
        result = folder_scanner.scan(str(SAMPLE_ROOT / "artifact_nupkg"), 2, [], "")
        self.assertEqual(result["classification"], "likely_project")
        self.assertEqual(result["hits"]["artifacts"], ["sample.nupkg"])

    def test_scan_counts_each_added_script_extension_fixture(self):
        fixture_dirs = {
            "script_bat": "sample.bat",
            "script_cmd": "sample.cmd",
            "script_fish": "sample.fish",
            "script_ksh": "sample.ksh",
            "script_mjs": "sample.mjs",
            "script_cjs": "sample.cjs",
            "script_jsx": "sample.jsx",
            "script_tsx": "sample.tsx",
            "script_java": "Sample.java",
            "script_kt": "sample.kt",
            "script_groovy": "sample.groovy",
            "script_scala": "Sample.scala",
            "script_go": "sample.go",
            "script_rs": "sample.rs",
            "script_swift": "sample.swift",
            "script_cs": "Sample.cs",
            "script_lua": "sample.lua",
        }

        for folder_name, file_name in fixture_dirs.items():
            with self.subTest(folder=folder_name):
                result = folder_scanner.scan(str(SAMPLE_ROOT / folder_name), 2, [], "")
                self.assertEqual(result["classification"], "likely_scripts_only")
                self.assertEqual(result["counts"]["files_total"], 1)
                self.assertEqual(result["counts"]["script_files"], 1)
                self.assertEqual(result["counts"]["text_files"], 0)
                self.assertEqual(result["hits"], {})
                self.assertTrue((SAMPLE_ROOT / folder_name / file_name).exists())

    def test_scan_negative_fixture(self):
        result = folder_scanner.scan(str(SAMPLE_ROOT / "negative"), 2, [], "")
        self.assertEqual(result["classification"], "likely_scripts_only")
        self.assertEqual(result["counts"]["files_total"], 1)
        self.assertEqual(result["counts"]["script_files"], 0)
        self.assertEqual(result["counts"]["text_files"], 1)
        self.assertEqual(result["hits"], {})


if __name__ == "__main__":
    unittest.main()
