# tests/test_cli.py
import sys
import json
import types
import unittest

from unittest import mock

import depdetect.cli as cli


class TestCli(unittest.TestCase):
    def test_parse_args_defaults(monkeypatch):
        test_args = ["prog", "some/path"]
        monkeypatch.setattr(sys, "argv", test_args)
        args = cli.parse_args()
        assert args.path == "some/path"
        assert args.max_depth == 6
        assert args.ignore_dir == []
        assert args.linguist is False
        assert args.json_out == ""

    def test_parse_args_all_options(monkeypatch):
        test_args = [
            "prog",
            "folder",
            "--max-depth",
            "3",
            "--ignore-dir",
            "venv",
            "--ignore-dir",
            "build",
            "--linguist",
            "--json-out",
            "out.json",
        ]
        monkeypatch.setattr(sys, "argv", test_args)
        args = cli.parse_args()
        assert args.path == "folder"
        assert args.max_depth == 3
        assert args.ignore_dir == ["venv", "build"]
        assert args.linguist is True
        assert args.json_out == "out.json"

    @mock.patch("depdetect.cli.parse_args")
    @mock.patch("depdetect.cli.scanner")
    def test_main_basic(mock_scanner, mock_parse_args, tmp_path, capsys):
        # Setup mock args
        args = types.SimpleNamespace(
            path="testdir",
            max_depth=2,
            ignore_dir=["venv"],
            linguist=False,
            json_out="",
        )
        mock_parse_args.return_value = args
        mock_scanner.scan.return_value = {"result": "ok"}

        cli.main()

        mock_scanner.scan.assert_called_once_with("testdir", 2, ["venv"], "")
        captured = capsys.readouterr()
        assert "Full report written" not in captured.out

    @mock.patch("depdetect.cli.parse_args")
    @mock.patch("depdetect.cli.scanner")
    def test_main_with_linguist_and_json(
        mock_scanner, mock_parse_args, tmp_path, capsys
    ):
        json_file = tmp_path / "report.json"
        args = types.SimpleNamespace(
            path="testdir",
            max_depth=1,
            ignore_dir=[],
            linguist=True,
            json_out=str(json_file),
        )
        mock_parse_args.return_value = args
        mock_scanner.scan.return_value = {"result": "ok"}
        mock_scanner.linguist.return_value = {"Python": 100}

        cli.main()

        mock_scanner.scan.assert_called_once_with("testdir", 1, [], str(json_file))
        mock_scanner.linguist.assert_called_once_with("testdir")
        # Check file written
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["result"] == "ok"
        assert data["languages"] == {"Python": 100}
        captured = capsys.readouterr()
        assert "Wrote JSON report" in captured.out


if __name__ == "__main__":
    unittest.main()
