import argparse
import json
from functools import partial
from pathlib import Path

import depdetect.scanner as scanner


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Detect whether a folder contains vulnerability-scannable project metadata.",
        formatter_class=partial(argparse.HelpFormatter, width=150, max_help_position=35),
    )
    ap.add_argument("path", help="Folder to scan")
    ap.add_argument(
        "--max-depth",
        type=int,
        default=6,
        help="Max directory depth to scan (-1 for unlimited). Default: 6",
    )
    ap.add_argument(
        "--ignore-dir",
        action="append",
        default=[],
        help="Directory name to ignore (repeatable).",
    )
    ap.add_argument("--json-out", default="", help="Write full report to JSON file.")
    ap.add_argument(
        "--linguist",
        action="store_true",
        help="Detect languages using github-linguist if available in PATH.",
    )

    return ap.parse_args()


def main() -> None:
    args = parse_args()
    result = scanner.scan(args.path, args.max_depth, args.ignore_dir, args.json_out)
    if args.linguist:
        languages = scanner.linguist(args.path)
        result["languages"] = languages

    if args.json_out:
        print(f"Full report written to {args.json_out}")
        out_path = Path(args.json_out)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nWrote JSON report: {out_path}")
