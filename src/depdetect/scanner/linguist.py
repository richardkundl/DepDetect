from typing import Any
import subprocess
import json


def linguist(path: str) -> dict[str, Any]:
    """Call github-linguist on the given path and print the results."""
    languages = {}
    try:
        result = subprocess.run(
            ["github-linguist", "--json", path],
            capture_output=True,
            text=True,
            check=True,
        )
        languages = json.loads(result.stdout)
        print("Detected languages:")
        for lang, details in languages.items():
            print(f"- {lang}: {details['size']} bytes ({details['percentage']}%)")
    except FileNotFoundError:
        print("Error: github-linguist is not installed or not found in PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error running github-linguist: {e.stderr}")

    return languages
