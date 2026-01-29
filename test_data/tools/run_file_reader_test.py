import sys
import json
from pathlib import Path

"""
What this script does:
- Reads tests from test_data/inputs/file_reader_tests.jsonl
- Runs FileReader.chunks
- Writes outputs to test_data/out/r_<n>.out.json
- IDs are always r_1, r_2, r_3...
"""

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from file_reader import FileReader


def load_tests(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_one(test_id, input_path, chunk_size, full_file):
    chunks_hex = [
        c.hex()
        for c in FileReader.chunks(input_path, chunk_size=int(chunk_size), full_file=bool(full_file))
    ]

    out = {
        "chunk_size": int(chunk_size),
        "full_file": bool(full_file),
        "chunks_hex": chunks_hex,
        "chunk_count": len(chunks_hex),
    }

    out_path = Path("test_data/out") / f"{test_id}.out.json"
    save_json(out_path, out)
    return str(out_path)


def main():
    Path("test_data/out").mkdir(parents=True, exist_ok=True)

    tests = load_tests("test_data/inputs/file_reader_tests.jsonl")

    for i, t in enumerate(tests, start=1):
        test_id = f"r_{i}"
        out_path = run_one(test_id, t["input"], t["chunk_size"], t["full_file"])
        print("+ WROTE:", out_path)

    print("\n+ DONE (FileReader outputs generated)")


if __name__ == "__main__":
    main()
