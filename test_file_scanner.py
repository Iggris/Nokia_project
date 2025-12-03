from file_scanner import FileScanner
from file_reader import FileReader


class DummyEngine:
    """fake regex engine that mimics Hyperscan's interface."""
    def __init__(self):
        self.compiled_patterns = None
        self.scan_calls = []

    def compile_patterns(self, patterns):
        self.compiled_patterns = patterns

    def scan_stream(self, chunks_iter, on_match, context=None):
        # Consume incoming chunks so we know what was scanned
        data = b"".join(chunks_iter)
        self.scan_calls.append((data, context))
        # Simulate a single match: pattern_id=0, [0, 4)
        on_match(0, 0, 4, 0, context)


def test_compile_patterns_calls_engine():
    """compile_patterns should delegate pattern compilation to the engine."""
    engine = DummyEngine()
    scanner = FileScanner(engine=engine)

    scanner.compile_patterns(["abc", "def"])

    assert engine.compiled_patterns is not None
    assert len(engine.compiled_patterns) == 2


def test_scan_file_returns_results(tmp_path):
    """
    scan_file should:
    - pass a chunks iterator to engine.scan_stream,
    - return a list of match dictionaries.
    """
    p = tmp_path / "file.txt"
    p.write_text("some content", encoding="utf-8")

    engine = DummyEngine()
    scanner = FileScanner(engine=engine)
    scanner.compile_patterns(["dummy"])

    results = scanner.scan_file(str(p), chunk_size=4)

    # Engine should have been called once
    assert len(engine.scan_calls) == 1
    data, context = engine.scan_calls[0]
    assert context == str(p)
    assert data == p.read_bytes()

    # Results should contain at least one match with required keys
    assert isinstance(results, list)
    assert len(results) == 1
    match = results[0]
    for key in ("pattern_id", "start", "end", "filename"):
        assert key in match
    assert match["filename"] == str(p)


def test_scan_file_resets_results_between_calls(tmp_path):
    """Two consecutive scan_file calls should not accumulate old results."""
    p1 = tmp_path / "a.txt"
    p2 = tmp_path / "b.txt"
    p1.write_text("aaa", encoding="utf-8")
    p2.write_text("bbb", encoding="utf-8")

    engine = DummyEngine()
    scanner = FileScanner(engine=engine)
    scanner.compile_patterns(["dummy"])

    res1 = scanner.scan_file(str(p1))
    res2 = scanner.scan_file(str(p2))

    assert len(res1) == 1
    assert len(res2) == 1
    assert res1[0]["filename"] == str(p1)
    assert res2[0]["filename"] == str(p2)


def test_scan_tree_calls_scan_file_for_each_file(tmp_path, monkeypatch):
    """scan_tree should scan all files in the given directory."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("aaa", encoding="utf-8")
    f2.write_text("bbb", encoding="utf-8")

    called = []

    def fake_scan_file(self, filename, chunk_size=4096):
        called.append(filename)
        return [{"pattern_id": 0, "start": 0, "end": 1, "filename": filename}]

    monkeypatch.setattr(FileScanner, "scan_file", fake_scan_file)

    scanner = FileScanner(engine=DummyEngine())
    scanner.compile_patterns(["dummy"])

    results = scanner.scan_tree(str(tmp_path))

    assert set(called) == {str(f1), str(f2)}
    assert len(results) == 2
    assert {r["filename"] for r in results} == {str(f1), str(f2)}