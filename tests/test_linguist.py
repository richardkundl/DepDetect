import subprocess
import unittest
from unittest.mock import patch, MagicMock
from src.depdetect.scanner.linguist import linguist


class TestLinguist(unittest.TestCase):
    @patch("src.depdetect.scanner.linguist.subprocess.run")
    def test_linguist_success(self, mock_run):
        mock_output = '{"Python": {"size": 1000, "percentage": 100.0}}'
        mock_run.return_value = MagicMock(stdout=mock_output)
        result = linguist("some/path")
        self.assertIn("Python", result)
        self.assertEqual(result["Python"]["size"], 1000)
        self.assertEqual(result["Python"]["percentage"], 100.0)

    @patch(
        "src.depdetect.scanner.linguist.subprocess.run", side_effect=FileNotFoundError
    )
    def test_linguist_file_not_found(self, mock_run):
        result = linguist("some/path")
        self.assertEqual(result, {})

    @patch("src.depdetect.scanner.linguist.subprocess.run")
    def test_linguist_called_process_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "github-linguist", stderr="Some error"
        )
        result = linguist("some/path")
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
