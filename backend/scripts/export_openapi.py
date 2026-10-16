import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

ROOT_DIR = BACKEND_DIR.parent
OPENAPI_JSON_PATH = ROOT_DIR / "docs" / "openapi.json"

from app.main import app

def main():
    schema = app.openapi()
    OPENAPI_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OPENAPI_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"Successfully exported OpenAPI schema to {OPENAPI_JSON_PATH}")

if __name__ == "__main__":
    main()
