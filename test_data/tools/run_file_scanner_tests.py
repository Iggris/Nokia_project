import sys
import json
from pathlib import Path
import io
from contextlib import redirect_stdout

"""
What this script does:
- Reads test definitions from test_data/inputs/tests.jsonl
- Runs FileScanner on each input
- Captures printed output
- Saves output to test_data/out/<id>.out.txt
"""

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from file_scanner import FileScanner
from engines.python_engine import PythonEngine


def load_lines(path):
    return [ln.strip() for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]

def load_tests():
    tests_path = Path("test_data/inputs/tests.jsonl")
    return [json.loads(l) for l in tests_path.read_text(encoding="utf-8").splitlines() if l.strip()]

def main():
    Path("test_data/out").mkdir(parents=True, exist_ok=True)

    tests = load_tests()

    for t in tests:
        test_id = t["id"]
        patterns_path = Path("test_data/inputs") / t["patterns"]
        input_path = Path("test_data/inputs") / t["input"]

        scanner = FileScanner(engine=PythonEngine())
        scanner.compile_patterns(load_lines(patterns_path))

        buf = io.StringIO()
        with redirect_stdout(buf):
            scanner.scan_file(str(input_path))

        out_path = Path("test_data/out") / f"{test_id}.out.txt"
        out_path.write_text(buf.getvalue(), encoding="utf-8")
        print("+ WROTE:", out_path)

    print("\n+ DONE (outputs generated)")

if __name__ == "__main__":
    main()
