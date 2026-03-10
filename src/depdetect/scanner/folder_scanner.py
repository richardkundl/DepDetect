import fnmatch
import json
import os
import subprocess
from pathlib import Path

import depdetect.scanner.constant as constant
from .errors import (
    InvalidRootError,
    LinguistExecutionError,
    LinguistOutputError,
    LinguistUnavailableError,
)


def should_skip_dir(dirname: str, ignore_dirs: set[str]) -> bool:
    return dirname in ignore_dirs


def match_any_glob(rel_posix: str, globs: set[str]) -> bool:
    return any(fnmatch.fnmatch(rel_posix, g) for g in globs)


def scan(root: str, max_depth: int, ignore_dirs: list[str]) -> dict:
    root = Path(root)
    if not root.exists() or not root.is_dir():
        raise InvalidRootError(f"Not a directory: {root}")

    ignore_dirs = set(constant.DEFAULT_IGNORE_DIRS) | set(ignore_dirs)

    root = root.resolve()
    found = {k: [] for k in constant.MARKERS.keys()}

    counts = {
        "files_total": 0,
        "script_files": 0,
        "text_files": 0,
    }

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip ignored dirs
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d, ignore_dirs)]

        rel_dir = Path(dirpath).resolve().relative_to(root)
        depth = 0 if str(rel_dir) == "." else len(rel_dir.parts)
        if 0 <= max_depth < depth:
            dirnames[:] = []
            continue

        for name in filenames:
            counts["files_total"] += 1
            p = Path(dirpath) / name
            rel = p.resolve().relative_to(root)
            rel_posix = rel.as_posix()

            ext = os.path.splitext(name)[1].lower()
            if ext in constant.SCRIPT_EXTENSIONS:
                counts["script_files"] += 1
            if ext in constant.TEXT_EXTENSIONS:
                counts["text_files"] += 1

            for kind, spec in constant.MARKERS.items():
                if name in spec["files"] or match_any_glob(rel_posix, spec["globs"]):
                    found[kind].append(rel_posix)

    # Determine "scannability"

    sca_hits = sum(len(found[k]) for k in constant.SCA_KINDS)
    infra_hits = sum(len(found[k]) for k in constant.INFRA_KINDS)
    artifact_hits = len(found["artifacts"])

    likely_project = (sca_hits + infra_hits + artifact_hits) > 0

    classification = "likely_project" if likely_project else "likely_scripts_only"

    # Simple confidence heuristic
    score = 0
    if sca_hits:
        score += 3
    if infra_hits:
        score += 2
    if artifact_hits:
        score += 2
    if counts["script_files"] > 0 and not likely_project:
        score += 1
    confidence = "high" if score >= 4 else "medium" if score >= 2 else "low"

    result = {
        "root": str(root),
        "classification": classification,
        "confidence": confidence,
        "counts": counts,
        "hits": {k: sorted(v) for k, v in found.items() if v},
        "notes": [
            "Dependency manifests/lockfiles indicate SCA (dependency vulnerability) scanning is likely applicable.",
            "Container/IaC markers indicate misconfiguration scanning is likely applicable.",
            "If no markers are found, prioritize secrets and code-pattern scanning over dependency CVEs.",
        ],
    }

    return result


def linguist(root: str) -> dict[str, Any]:
    root_path = Path(root).resolve()

    try:
        completed = subprocess.run(
            ["github-linguist", "--json", str(root_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise LinguistUnavailableError(
            "The --linguist option requires the `github-linguist` executable in PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "github-linguist failed."
        raise LinguistExecutionError(f"Language detection failed: {stderr}") from exc

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise LinguistOutputError(
            "Language detection returned invalid JSON output."
        ) from exc
