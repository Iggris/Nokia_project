from pathlib import Path

"""
Generates test inputs for:
- FileReader:  test_data/inputs/r_<id>.txt + file_reader_tests.jsonl
- FileScanner: test_data/inputs/s_<id>_input.txt + s_<id>_patterns.txt + file_scanner_tests.jsonl
"""

ROOT = Path.cwd()
INPUTS = ROOT / "test_data" / "inputs"
INPUTS.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def gen_reader_tests(n: int = 10):
    """
    Creates:
      test_data/inputs/r_1.txt ... r_n.txt
      test_data/inputs/file_reader_tests.jsonl
    """
    contents = [
        "ABCDEFGH12345678",          # 16 bytes
        "ABCDE",                     # 5 bytes
        "HELLO",                     # 5 bytes
        "",                          # empty
        "0123456789" * 10,           # 100 chars
        "A" * 4096,                  # 4096
        "B" * 4097,                  # 4097
        "LoremIpsumDolorSitAmet",    # 21
        "Z" * 3,                     # 3
        "END",                       # 3
    ]
    chunk_sizes = [1, 2, 4, 8, 16, 32, 64, 4096, 3, 5]
    full_flags = [False, False, False, False, False, True, False, True, False, False]

    lines = []

    for i in range(1, n + 1):
        test_id = f"r_{i}"
        file_path = INPUTS / f"{test_id}.txt"
        content = contents[(i - 1) % len(contents)]
        write_text(file_path, content)

        lines.append(
            f'{{"input":"test_data/inputs/{test_id}.txt","chunk_size":{chunk_sizes[(i - 1) % len(chunk_sizes)]},"full_file":{str(full_flags[(i - 1) % len(full_flags)]).lower()}}}'
        )

    (INPUTS / "file_reader_tests.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[gen_reader_tests] wrote {n} reader inputs + file_reader_tests.jsonl")


def gen_scanner_tests(n: int = 10):
    """
    Creates:
      test_data/inputs/s_<id>_input.txt
      test_data/inputs/s_<id>_patterns.txt
      test_data/inputs/file_scanner_tests.jsonl
    """
    patterns_sets = [
        ["ERROR", "WARN", r"timeout\s+\d+", r"user:\s*\w+"],
        ["ABC", "XYZ"],
        ["HELLO", "WORLD"],
        [r"\d+", r"ID:\s*\d+"],
        ["END"],
    ]

    inputs = [
        "ERROR user: alice\nINFO ok\nWARN timeout 15",
        "xxABCyyXYZzz",
        "HELLO WORLD",
        "ID: 12345 and 678",
        "no matches here",
        "ERROR xx ERROR",
        "WARNWARN",
        "timeout 9 timeout 10",
        "user: bob user: ann",
        "END\nEND",
    ]

    lines = []

    for i in range(1, n + 1):
        test_id = f"s_{i}"
        in_file = INPUTS / f"{test_id}_input.txt"
        pat_file = INPUTS / f"{test_id}_patterns.txt"

        write_text(in_file, inputs[(i - 1) % len(inputs)])
        write_text(pat_file, "\n".join(patterns_sets[(i - 1) % len(patterns_sets)]) + "\n")

        lines.append(
            f'{{"patterns":"{test_id}_patterns.txt","input":"{test_id}_input.txt","engine":"python"}}'
        )

    (INPUTS / "file_scanner_tests.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[gen_scanner_tests] wrote {n} scanner inputs+patterns + file_scanner_tests.jsonl")


def main():
    gen_reader_tests(10)
    gen_scanner_tests(10)
    print("\nDONE: test_data/inputs populated.")


if __name__ == "__main__":
    main()
