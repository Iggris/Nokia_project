import argparse
import json
import os
import random
import re
import string
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Type

import psutil

from engines.python_engine import PythonEngine
from engines.hs_engine import HyperscanEngine
from file_reader import FileReader

class TextGenerator:
    """
    Text and simple regex generator:
    - generates pattern words
    - turns them into regexes of type r"\\bword\\b"
    - generates text with controlled number of matches:
        match_type = 0 -> no matches
        match_type = 1 -> few matches
        match_type = 2 -> many matches
    """

    def __init__(self, alphabet: str = string.ascii_lowercase):
        self.alphabet = alphabet
        self.pattern_words: List[str] = []
        self.patterns: List[str] = []

    def generate_pattern_words(self, n: int = 5, min_len: int = 4, max_len: int = 8) -> List[str]:
        words = set()
        while len(words) < n:
            length = random.randint(min_len, max_len)
            word = "".join(random.choice(self.alphabet) for _ in range(length))
            words.add(word)
        self.pattern_words = list(words)
        return self.pattern_words

    def generate_regexes(self, use_word_boundaries: bool = True) -> List[str]:
        if not self.pattern_words:
            raise ValueError("First, call generate_pattern_words().")
        if use_word_boundaries:
            self.patterns = [rf"\b{re.escape(w)}\b" for w in self.pattern_words]
        else:
            self.patterns = [re.escape(w) for w in self.pattern_words]
        return self.patterns

    def _generate_random_word(self, min_len: int = 3, max_len: int = 10, forbidden=None) -> str:
        if forbidden is None:
            forbidden = set()
        while True:
            length = random.randint(min_len, max_len)
            word = "".join(random.choice(self.alphabet) for _ in range(length))
            if word not in forbidden:
                return word

    def generate_text(
        self,
        num_lines: int,
        avg_line_len: int,
        match_type: int,
        p_few: float = 0.02,
        p_many: float = 0.4,
    ) -> str:
        if not self.pattern_words:
            raise ValueError("First, generate pattern_words and regexes.")

        texts: List[str] = []
        forbidden = set(self.pattern_words)

        for _ in range(num_lines):
            line_words: List[str] = []
            current_len = 0

            while current_len < avg_line_len:
                if match_type == 0:
                    w = self._generate_random_word(forbidden=forbidden)
                elif match_type == 1:
                    w = random.choice(self.pattern_words) if random.random() < p_few else self._generate_random_word(forbidden=forbidden)
                elif match_type == 2:
                    w = random.choice(self.pattern_words) if random.random() < p_many else self._generate_random_word(forbidden=forbidden)
                else:
                    raise ValueError("match_type must be 0, 1, or 2.")

                line_words.append(w)
                current_len += len(w) + 1

            texts.append(" ".join(line_words))

        return "\n".join(texts)


def null_callback(id: int, from_: int, to: int, flags: int, context: Any):
    pass


def _get_proc() -> psutil.Process:
    return psutil.Process(os.getpid())


def mem_chunks(data: bytes, chunk_size: int = 4096) -> Iterable[bytes]:
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]


def one_block(data: bytes) -> Iterable[bytes]:
    yield data


def file_one_chunk(path: str) -> Iterable[bytes]:
    with open(path, "rb") as f:
        yield f.read()

def benchmark_stream_precompiled(
    engine_cls: Type,
    patterns: List[bytes],
    make_chunks: Callable[[], Iterable[bytes]],
    repeats: int = 5,
) -> Dict[str, Any]:
    proc = _get_proc()
    engine = engine_cls()

    cpu_before = proc.cpu_times()
    mem_before = proc.memory_info().rss
    t0 = time.perf_counter()

    engine.compile_patterns(patterns)

    t1 = time.perf_counter()
    cpu_after = proc.cpu_times()
    mem_after = proc.memory_info().rss

    compile_time_wall = t1 - t0
    compile_cpu_user = cpu_after.user - cpu_before.user
    compile_cpu_sys = cpu_after.system - cpu_before.system
    compile_mem_delta = mem_after - mem_before

    scan_times: List[float] = []
    cpu_before_scan = proc.cpu_times()
    mem_before_scan = proc.memory_info().rss

    for _ in range(repeats):
        chunks_iter = make_chunks()
        t_start = time.perf_counter()
        engine.scan_stream(chunks_iter, null_callback, context=None)
        t_end = time.perf_counter()
        scan_times.append(t_end - t_start)

    cpu_after_scan = proc.cpu_times()
    mem_after_scan = proc.memory_info().rss

    scan_cpu_user = cpu_after_scan.user - cpu_before_scan.user
    scan_cpu_sys = cpu_after_scan.system - cpu_before_scan.system
    scan_mem_delta = mem_after_scan - mem_before_scan
    scan_avg_time_wall = sum(scan_times) / len(scan_times) if scan_times else 0.0

    return {
        "engine": engine_cls.__name__,
        "mode": "stream_precompiled",
        "repeats": repeats,
        "compile": {
            "wall_time": compile_time_wall,
            "cpu_user": compile_cpu_user,
            "cpu_sys": compile_cpu_sys,
            "mem_delta": compile_mem_delta,
            "mem_after": mem_after,
        },
        "scan": {
            "times_wall": scan_times,
            "avg_time_wall": scan_avg_time_wall,
            "cpu_user": scan_cpu_user,
            "cpu_sys": scan_cpu_sys,
            "mem_delta": scan_mem_delta,
            "mem_after": mem_after_scan,
        },
    }

@dataclass
class PatternParams:
    n: int = 8
    min_len: int = 4
    max_len: int = 8
    word_boundaries: bool = True


@dataclass
class GeneratedTextParams:
    num_lines: int
    avg_line_len: int
    match_type: int
    p_few: float = 0.02
    p_many: float = 0.4


@dataclass
class Scenario:
    name: str
    source: str  # "generated" or "file"
    file_path: Optional[str] = None
    gen: Optional[GeneratedTextParams] = None
    chunk_mode: str = "stream"  # "stream" or "one_block"
    chunk_size: int = 4096      # used for "stream" mode


def _engine_classes(engine_arg: str) -> Sequence[Type]:
    if engine_arg == "python":
        return (PythonEngine,)
    if engine_arg == "hyperscan":
        return (HyperscanEngine,)
    return (PythonEngine, HyperscanEngine)


def _build_patterns(seed: int, pp: PatternParams) -> List[bytes]:
    random.seed(seed)
    gen = TextGenerator()
    gen.generate_pattern_words(n=pp.n, min_len=pp.min_len, max_len=pp.max_len)
    regexes = gen.generate_regexes(use_word_boundaries=pp.word_boundaries)
    return [r.encode("utf-8") for r in regexes], gen


def _make_chunks_for_scenario(s: Scenario, gen_obj: Optional[TextGenerator]) -> Callable[[], Iterable[bytes]]:
    if s.source == "generated":
        assert s.gen is not None
        assert gen_obj is not None
        text_str = gen_obj.generate_text(
            num_lines=s.gen.num_lines,
            avg_line_len=s.gen.avg_line_len,
            match_type=s.gen.match_type,
            p_few=s.gen.p_few,
            p_many=s.gen.p_many,
        )
        data = text_str.encode("utf-8")

        if s.chunk_mode == "one_block":
            return lambda d=data: one_block(d)
        else:
            return lambda d=data, cs=s.chunk_size: mem_chunks(d, chunk_size=cs)

    # file
    assert s.file_path is not None
    FileReader.validate(s.file_path)

    if s.chunk_mode == "one_block":
        return lambda p=s.file_path: file_one_chunk(p)
    else:
        return lambda p=s.file_path, cs=s.chunk_size: FileReader.chunks(p, chunk_size=cs)


def run_scenarios(
    scenarios: List[Scenario],
    seed: int,
    pattern_params: PatternParams,
    engine_arg: str,
    repeats: int,
    verbose: bool = True,
) -> List[Dict[str, Any]]:
    patterns, gen_obj = _build_patterns(seed, pattern_params)

    results: List[Dict[str, Any]] = []
    engines = _engine_classes(engine_arg)

    for s in scenarios:
        if verbose:
            print(f"\nSCENARIO: {s.name}  source={s.source}  chunk_mode={s.chunk_mode}  chunk_size={s.chunk_size}")

        make_chunks = _make_chunks_for_scenario(s, gen_obj if s.source == "generated" else None)

        for engine_cls in engines:
            if verbose:
                print(f"  -> Engine: {engine_cls.__name__}")

            res = benchmark_stream_precompiled(engine_cls, patterns, make_chunks, repeats=repeats)
            res["scenario"] = s.name
            res["source"] = s.source
            res["chunk_mode"] = s.chunk_mode
            res["chunk_size"] = s.chunk_size
            if s.file_path:
                res["file_path"] = s.file_path

            results.append(res)

            if verbose:
                print(
                    f"     compile: {res['compile']['wall_time']:.6f}s, "
                    f"avg scan: {res['scan']['avg_time_wall']:.6f}s"
                )

    return results

def default_scenarios() -> List[Scenario]:
    return [
        Scenario(name="small_no_matches_stream", source="generated",
                 gen=GeneratedTextParams(num_lines=200, avg_line_len=60, match_type=0),
                 chunk_mode="stream", chunk_size=4096),
        Scenario(name="small_few_matches_stream", source="generated",
                 gen=GeneratedTextParams(num_lines=200, avg_line_len=60, match_type=1),
                 chunk_mode="stream", chunk_size=4096),
        Scenario(name="small_many_matches_stream", source="generated",
                 gen=GeneratedTextParams(num_lines=200, avg_line_len=60, match_type=2),
                 chunk_mode="stream", chunk_size=4096),

        Scenario(name="large_no_matches_stream", source="generated",
                 gen=GeneratedTextParams(num_lines=5000, avg_line_len=80, match_type=0),
                 chunk_mode="stream", chunk_size=4096),
        Scenario(name="large_few_matches_stream", source="generated",
                 gen=GeneratedTextParams(num_lines=5000, avg_line_len=80, match_type=1),
                 chunk_mode="stream", chunk_size=4096),
        Scenario(name="large_many_matches_stream", source="generated",
                 gen=GeneratedTextParams(num_lines=5000, avg_line_len=80, match_type=2),
                 chunk_mode="stream", chunk_size=4096),
    ]
def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def scenarios_from_config(cfg: Dict[str, Any]) -> List[Scenario]:
    tests = cfg.get("tests", [])
    out: List[Scenario] = []

    for t in tests:
        src = t["source"]
        name = t.get("name", "unnamed")
        chunk_mode = t.get("chunk_mode", "stream")
        chunk_size = int(t.get("chunk_size", 4096))

        if src == "generated":
            g = t["generated"]
            out.append(
                Scenario(
                    name=name,
                    source="generated",
                    gen=GeneratedTextParams(
                        num_lines=int(g["num_lines"]),
                        avg_line_len=int(g["avg_line_len"]),
                        match_type=int(g["match_type"]),
                        p_few=float(g.get("p_few", 0.02)),
                        p_many=float(g.get("p_many", 0.4)),
                    ),
                    chunk_mode=chunk_mode,
                    chunk_size=chunk_size,
                )
            )
        elif src == "file":
            out.append(
                Scenario(
                    name=name,
                    source="file",
                    file_path=t["file_path"],
                    chunk_mode=chunk_mode,
                    chunk_size=chunk_size,
                )
            )
        else:
            raise ValueError(f"Unknown source in config: {src}")

    return out
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="test_capabilities.py",
        description="Regex engines capability/benchmark runner: default tests or fully custom CLI/config tests.",
    )

    p.add_argument("--output", default="benchmark_results_stream.json", help="Output JSON file.")
    p.add_argument("--seed", type=int, default=1, help="Random seed for pattern generation.")
    p.add_argument("--repeats", type=int, default=5, help="How many scans per scenario.")
    p.add_argument("--engine", choices=["python", "hyperscan", "both"], default="both", help="Which engine(s) to run.")
    p.add_argument("--quiet", action="store_true", help="Less console output.")

    # pattern generation parameters
    p.add_argument("--pattern-count", type=int, default=8, help="n in generate_pattern_words(n=...).")
    p.add_argument("--pattern-min-len", type=int, default=4, help="min_len in generate_pattern_words.")
    p.add_argument("--pattern-max-len", type=int, default=8, help="max_len in generate_pattern_words.")
    p.add_argument("--no-word-boundaries", action="store_true", help="Do not wrap words with \\b...\\b.")

    # either use --config OR define a single scenario via flags
    p.add_argument("--config", help="Path to JSON config with multiple tests (overrides single-scenario flags).")

    src = p.add_mutually_exclusive_group()
    src.add_argument("--generated", action="store_true", help="Run a generated-text scenario (single scenario).")
    src.add_argument("--file", dest="file_path", help="Run a file scenario (single scenario).")

    # scenario params (for single scenario mode)
    p.add_argument("--name", default="custom", help="Scenario name (single scenario mode).")
    p.add_argument("--chunk-mode", choices=["stream", "one_block"], default="stream", help="Chunking mode.")
    p.add_argument("--chunk-size", type=int, default=4096, help="Chunk size in bytes for stream mode.")

    # generated scenario details
    p.add_argument("--num-lines", type=int, default=200, help="Generated: number of lines.")
    p.add_argument("--avg-line-len", type=int, default=60, help="Generated: approximate line length.")
    p.add_argument("--match-type", type=int, choices=[0, 1, 2], default=0, help="Generated: 0=no,1=few,2=many.")
    p.add_argument("--p-few", type=float, default=0.02, help="Generated: probability for few matches.")
    p.add_argument("--p-many", type=float, default=0.4, help="Generated: probability for many matches.")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    verbose = not args.quiet

    pattern_params = PatternParams(
        n=args.pattern_count,
        min_len=args.pattern_min_len,
        max_len=args.pattern_max_len,
        word_boundaries=not args.no_word_boundaries,
    )

    # 1) CONFIG MODE
    if args.config:
        cfg = load_config(args.config)

        seed = int(cfg.get("seed", args.seed))
        repeats = int(cfg.get("repeats", args.repeats))
        engine_arg = cfg.get("engine", args.engine)

        pp_cfg = cfg.get("pattern_words", {})
        pattern_params = PatternParams(
            n=int(pp_cfg.get("n", pattern_params.n)),
            min_len=int(pp_cfg.get("min_len", pattern_params.min_len)),
            max_len=int(pp_cfg.get("max_len", pattern_params.max_len)),
            word_boundaries=bool(pp_cfg.get("word_boundaries", pattern_params.word_boundaries)),
        )

        scenarios = scenarios_from_config(cfg)
        results = run_scenarios(
            scenarios=scenarios,
            seed=seed,
            pattern_params=pattern_params,
            engine_arg=engine_arg,
            repeats=repeats,
            verbose=verbose,
        )

    # 2) SINGLE SCENARIO MODE (flags)
    elif args.generated or args.file_path:
        if args.generated:
            scenarios = [
                Scenario(
                    name=args.name,
                    source="generated",
                    gen=GeneratedTextParams(
                        num_lines=args.num_lines,
                        avg_line_len=args.avg_line_len,
                        match_type=args.match_type,
                        p_few=args.p_few,
                        p_many=args.p_many,
                    ),
                    chunk_mode=args.chunk_mode,
                    chunk_size=args.chunk_size,
                )
            ]
        else:
            scenarios = [
                Scenario(
                    name=args.name,
                    source="file",
                    file_path=args.file_path,
                    chunk_mode=args.chunk_mode,
                    chunk_size=args.chunk_size,
                )
            ]

        results = run_scenarios(
            scenarios=scenarios,
            seed=args.seed,
            pattern_params=pattern_params,
            engine_arg=args.engine,
            repeats=args.repeats,
            verbose=verbose,
        )

    # 3) DEFAULT MODE (no args) -> run built-in tests
    else:
        results = run_scenarios(
            scenarios=default_scenarios(),
            seed=args.seed,
            pattern_params=pattern_params,
            engine_arg=args.engine,
            repeats=args.repeats,
            verbose=verbose,
        )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    if verbose:
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
