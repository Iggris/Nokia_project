import sys
import json
from pathlib import Path

"""
What this script does:
- Reads input files from test_data/inputs/
- Runs FileReader.chunks
- Saves generated output
- Validates output using valid.py
"""

# To see file_reader.py
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from file_reader import FileReader

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

def run_one(test_id, input_path, chunk_size, full_file):
    chunks_hex = [
        chunk.hex()
        for chunk in FileReader.chunks(input_path, chunk_size=chunk_size, full_file=full_file)
    ]

    out = {
        "chunk_size": chunk_size,
        "full_file": full_file,
        "chunks_hex": chunks_hex,
        "chunk_count": len(chunks_hex),
    }

    out_path = f"test_data/out/{test_id}.out.json"
    save_json(out_path, out)
    return out_path

def validate(expected_path, out_path):
    expected = load_json(expected_path)
    out = load_json(out_path)

    if expected != out:
        print("x FAIL:", out_path)
        print("\nEXPECTED:", expected)
        print("\nGOT:", out)
        return False

    print("+ PASS:", out_path)
    return True

def main():
    Path("test_data/out").mkdir(parents=True, exist_ok=True)

    tests = [
        (
            "file_reader_chunks_1",
            "test_data/inputs/reader_input_1.txt",
            4,
            False,
            "test_data/expected/file_reader_chunks_1.expected.json"
        ),
        (
            "file_reader_full_2",
            "test_data/inputs/reader_input_2.txt",
            4096,
            True,
            "test_data/expected/file_reader_full_2.expected.json"
        ),
    ]

    ok = True

    for test_id, input_path, chunk_size, full_file, expected_path in tests:
        out_path = run_one(test_id, input_path, chunk_size, full_file)
        if not validate(expected_path, out_path):
            ok = False

    if ok:
        print("\n====================")
        print("+ ALL TESTS PASSED")
    else:
        print("\nx SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
