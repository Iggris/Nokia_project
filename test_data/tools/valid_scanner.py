"""
Need to be repair
"""

import json
import sys
from pathlib import Path
import subprocess

def load_tests():
    p = Path("test_data/inputs/file_scanner_tests.jsonl")
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

def main():
    tests = load_tests()
    ok = True

    for i, _ in enumerate(tests, start=1):
        test_id = f"s_{i}"
        expected = Path("test_data/expected") / f"{test_id}.expected.txt"
        out = Path("test_data/out") / f"{test_id}.out.txt"

        if not expected.exists():
            print("x MISSING EXPECTED:", expected)
            ok = False
            continue
        if not out.exists():
            print("x MISSING OUTPUT:", out)
            ok = False
            continue

        try:
            subprocess.run(
                ["python", "test_data/tools/valid_txt.py", str(expected), str(out)],
                check=True
            )
            print("+ PASS:", test_id)
        except subprocess.CalledProcessError:
            print("x FAIL:", test_id)
            ok = False

    if not ok:
        sys.exit(1)

    print("\n+ ALL SCANNER TESTS PASSED")

if __name__ == "__main__":
    main()
