"""Make CLI modules importable without relying on test collection order."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "scripts", ROOT / "vendor/template/src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
