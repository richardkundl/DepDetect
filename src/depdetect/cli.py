import argparse
import json
import sys
from functools import partial
from pathlib import Path
from typing import Any

import depdetect.scanner as scanner

EXIT_OK = 0
EXIT_INTERNAL_ERROR = 1
EXIT_INVALID_INPUT = 2
EXIT_EXTERNAL_TOOL_ERROR = 3


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


def render_report(report: dict[str, Any]) -> str:
    lines = [
        f"Root: {report['root']}",
        f"Classification: {report['classification']} (confidence: {report['confidence']})",
        f"Counts: total={report['counts']['files_total']}, scripts={report['counts']['script_files']}, text={report['counts']['text_files']}",
    ]

    if report["hits"]:
        lines.append("")
        lines.append("Detected markers:")
        for kind, paths in report["hits"].items():
            lines.append(f"- {kind}: {len(paths)} file(s)")
            for path in paths[:20]:
                lines.append(f"  - {path}")
            if len(paths) > 20:
                lines.append(f"  ... {len(paths) - 20} more")
    else:
        lines.append("")
        lines.append("No known project/manifest markers found.")

    return "\n".join(lines)


def main() -> int:
    try:
        args = parse_args()
        result = scanner.scan(args.path, args.max_depth, args.ignore_dir)
        if args.linguist:
            result["languages"] = scanner.linguist(args.path)
    except scanner.InvalidRootError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(EXIT_INVALID_INPUT) from exc
    except scanner.LinguistUnavailableError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(EXIT_EXTERNAL_TOOL_ERROR) from exc
    except scanner.LinguistExecutionError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(EXIT_EXTERNAL_TOOL_ERROR) from exc
    except scanner.LinguistOutputError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(EXIT_EXTERNAL_TOOL_ERROR) from exc
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        raise SystemExit(EXIT_INTERNAL_ERROR) from exc

    print(render_report(result))

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nWrote JSON report: {out_path}")

    return EXIT_OK
