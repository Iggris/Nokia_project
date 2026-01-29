import sys
import json
from pathlib import Path
import io
from contextlib import redirect_stdout

"""
What this script does:
- Reads tests from test_data/inputs/file_scanner_tests.jsonl
- Runs FileScanner.scan_file (prints matches)
- Captures stdout and writes outputs to test_data/out/s_<n>.out.txt
- IDs are always s_1, s_2, s_3...
"""

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from file_scanner import FileScanner
from engines.python_engine import PythonEngine


def load_tests(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def load_patterns(path):
    return [ln.strip() for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]


def save_text(path, data):
    Path(path).write_text(data, encoding="utf-8")


def run_one(test_id, patterns_file, input_file):
    patterns_path = Path("test_data/inputs") / patterns_file
    input_path = Path("test_data/inputs") / input_file

    scanner = FileScanner(engine=PythonEngine())
    scanner.compile_patterns(load_patterns(patterns_path))

    buf = io.StringIO()
    with redirect_stdout(buf):
        scanner.scan_file(str(input_path))

    out_path = Path("test_data/out") / f"{test_id}.out.txt"
    save_text(out_path, buf.getvalue())
    return str(out_path)


def main():
    Path("test_data/out").mkdir(parents=True, exist_ok=True)

    tests = load_tests("test_data/inputs/file_scanner_tests.jsonl")

    for i, t in enumerate(tests, start=1):
        test_id = f"s_{i}"
        out_path = run_one(test_id, t["patterns"], t["input"])
        print("+ WROTE:", out_path)

    print("\n+ DONE (FileScanner outputs generated)")


if __name__ == "__main__":
    main()
