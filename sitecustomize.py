import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
SRC_PATH = REPO_ROOT / "src"

if SRC_PATH.is_dir() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
