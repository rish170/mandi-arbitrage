import runpy
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if __name__ == "__main__":
    target = BACKEND_DIR / "scripts" / "benchmark.py"
    runpy.run_path(str(target), run_name="__main__")
