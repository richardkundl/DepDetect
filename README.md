# depdetect

Detect whether a folder looks like a vulnerability-scannable project by checking for common dependency manifests,
infrastructure markers, and build artifacts.

## Features
- Scans a directory tree for known manifest files and glob patterns.
- Classifies results as "likely_project" or "likely_scripts_only" with a confidence score.
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

## Output
The scan always prints a summary to stdout.

If `--json-out` is provided, the tool also writes a JSON report with:
- `classification`: `likely_project` or `likely_scripts_only`
- `confidence`: `low`, `medium`, `high`
- `counts`: total files, script files, text files
- `hits`: matched markers by category
- `notes`: guidance for scanning focus
- `languages`: detected languages when `--linguist` is used successfully

## Development
Run tests from a fresh checkout:

```bash
python -m unittest discover -s tests
```

No `PYTHONPATH` setup is required.

## License
MIT
