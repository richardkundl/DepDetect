# depdetect

Detect whether a folder looks like a vulnerability-scannable project by checking for common dependency manifests,
infrastructure markers, and build artifacts.

## Features
- Scans a directory tree for known manifest files and glob patterns.
- Classifies results as "likely_project" or "likely_scripts_only" with a confidence score.
- Detects common language and workspace markers such as `package.json`, `nx.json`, `turbo.json`, `bun.lockb`, `pyproject.toml`, `requirements-*.txt`, `environment.yml`, and `Directory.Packages.props`.
- Optional language detection via `github-linguist`.
- JSON report output for automation.

## Install
From source:

```bash
pip install -e .
```

## Usage
After installing from source with `pip install -e .`, you can run:

```bash
depdetect /path/to/project
```

Or run directly as a module from the repository checkout:

```bash
python -m depdetect /path/to/project
```

Options:

```bash
depdetect /path --max-depth 4 --ignore-dir venv --ignore-dir build --json-out report.json
```

Enable language detection (requires the `github-linguist` executable in PATH):

```bash
depdetect /path --linguist
```

### Windows PowerShell
Install from the repository root:

```powershell
python -m pip install -e .
```

Run with the installed console command:

```powershell
depdetect .\path\to\project --max-depth 4 --ignore-dir venv --ignore-dir build --json-out report.json
```

Or run as a module without using the console command:

```powershell
python -m depdetect .\path\to\project --max-depth 4 --ignore-dir venv --ignore-dir build --json-out report.json
```

## Output
The scan always prints a summary to stdout.

If `--json-out` is provided, the tool also writes a JSON report with:
- `classification`: `likely_project` or `likely_scripts_only`
- `confidence`: `low`, `medium`, `high`
- `counts`: total files, script files, text files
- `hits`: matched markers by category
- `notes`: guidance for scanning focus
- `languages`: detected languages when `--linguist` is used successfully

JSON format:

```json
{
  "root": "/absolute/path/to/project",
  "classification": "likely_project",
  "confidence": "high",
  "counts": {
    "files_total": 4,
    "script_files": 1,
    "text_files": 0
  },
  "hits": {
    "container": ["Dockerfile"],
    "node": ["package.json"],
    "python": ["pyproject.toml"]
  },
  "notes": [
    "Dependency manifests/lockfiles indicate SCA (dependency vulnerability) scanning is likely applicable.",
    "Container/IaC markers indicate misconfiguration scanning is likely applicable.",
    "If no markers are found, prioritize secrets and code-pattern scanning over dependency CVEs."
  ],
  "languages": {
    "Python": 100.0
  }
}
```

Notes:
- `languages` is present only when `--linguist` is used successfully.
- `hits` contains only categories that were matched.
- `root` is written as an absolute path.

## Exit Codes
- `0`: success
- `1`: unexpected internal error
- `2`: invalid input, such as a non-existent or non-directory scan path
- `3`: external tool error, such as `github-linguist` being unavailable, failing, or returning invalid JSON

## Development
Run tests from a fresh checkout:

```bash
python -m unittest discover -s tests
```

No `PYTHONPATH` setup is required.

## License
MIT
