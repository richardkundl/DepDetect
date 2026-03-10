# AGENTS.md

## Repo Rules
- Package layout uses `src/`.
- Run tests with `python -m unittest discover -s tests`.
- No `PYTHONPATH` setup is required; repo-root `sitecustomize.py` handles `src/` imports.

## Boundaries
- Keep scanner code library-style: no printing and no `SystemExit` from scanner modules.
- Keep CLI responsibilities in `src/depdetect/cli.py`: argument parsing, stdout/stderr output, exit-code mapping, and optional JSON file writing.
- Keep typed scanner exceptions in `src/depdetect/scanner/errors.py`.

## Stability
- Treat CLI exit codes as stable.
- Treat the JSON report shape as stable.
- If either changes, update README and contract tests together.

## Tests
- Use `tests/sample` for fixture-backed detection tests.
- Prefer one marker per fixture unless testing mixed-language or multi-marker behavior.
- Keep a negative fixture for no-hit behavior.
- When adding markers, add:
  - constant coverage
  - fixture coverage
  - CLI JSON-contract coverage when behavior changes materially

## Docs
- Keep README aligned with the current CLI behavior, JSON format, exit codes, and PowerShell usage.
