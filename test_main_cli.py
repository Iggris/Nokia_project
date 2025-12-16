import subprocess
import sys


def test_cli_run_python_engine(tmp_path):
    """
    - create a regex file with 'test'
    - create an input file containing 'test'
    - call: python main.py run regex_file input_file --engine python
    - assert that 'test' appears in stdout.
    """
    regex_file = tmp_path / "regexes.txt"
    regex_file.write_text("test\n", encoding="utf-8")

    target_file = tmp_path / "input.txt"
    target_file.write_text("this is a test line\n", encoding="utf-8")

    cmd = [
        sys.executable,
        "main.py",
        "run",
        str(regex_file),
        str(target_file),
        "--engine",
        "python",
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, f"Program exited with error: {proc.stderr}"
    assert "test" in proc.stdout


def test_cli_build_database(tmp_path):
    """
    Integration test for 'build' command:
    - create a regex file
    - call: python main.py build regex_file -o db_file
    - assert that output database file exists.
    """
    regex_file = tmp_path / "regexes.txt"
    regex_file.write_text("test\n", encoding="utf-8")

    db_file = tmp_path / "db.hs"

    cmd = [
        sys.executable,
        "main.py",
        "build",
        str(regex_file),
        "-o",
        str(db_file),
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, f"Build command failed: {proc.stderr}"
    assert db_file.exists()
