import json
import sys
from pathlib import Path

"""
This script compares two JSON files:
- expected output
- actual output

If they are identical -> PASS
If they differ -> FAIL and prints both JSON objects
"""

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    expected_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    expected = load_json(expected_path)
    output = load_json(output_path)

    if expected != output:
        print("VALIDATION FAILED")
        print("\n--- EXPECTED ---")
        print(json.dumps(expected, ensure_ascii=False, indent=2))
        print("\n--- OUTPUT ---")
        print(json.dumps(output, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    print("VALIDATION OK")

if __name__ == "__main__":
    main()
