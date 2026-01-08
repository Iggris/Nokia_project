import os
import sys
from multiprocessing import Pool
from pathlib import Path

from engines.base_engine import RegexEngine
from file_regex.file_regex import FileRegex
from file_scanner import FileScanner


def init_worker():
    pid = os.getpid()
    cpu_count = os.cpu_count()
    cpu = pid % cpu_count
    os.sched_setaffinity(pid, {cpu})


class FileScannerPool:
    """
    Class designed to use FileScanner with multiprocessing
    """
    @staticmethod
    def scan_file(patterns_path: str, engine: RegexEngine, filename: str):
        """
        Creates FileScanner and scans single file,
        (worker function for multiprocessing)

        Args:
            patterns_path (str): path to compiled Hyperscan database or
                a text file with regexes (one per line)
            engine (RegexEngine): RegexEngine instance to be used in scanning
            filename (str): Path to the file that should be scanned
        """
        scanner = FileScanner(engine)
        try:
            scanner.engine.load_db(patterns_path)
        except Exception:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))

            fr = FileRegex(patterns_path)
            patterns = fr.elements()
            scanner.compile_patterns(patterns)

        scanner.scan_file(filename)

    @staticmethod
    def scan_tree(patterns_path: str, engine: RegexEngine, dirname: str, follow_symlinks=False):
        """
        Recursively scans all files in a directory tree using multiprocessing.

        Args:
            patterns_path (str): Path to a compiled Hyperscan database or
                a text file containing regex patterns (one per line).
            engine (RegexEngine): RegexEngine instance passed to each worker.
            dirname (str): Root directory to scan recursively.
            follow_symlinks (bool): Whether to follow symbolic links during traversal.

        Notes:
            Each file is scanned in a separate worker process using
            FileScannerPool.scan_file via multiprocessing.Pool.starmap().
        """
        root = Path(dirname)
        if not root.exists():
            print(f"[scan_tree] Directory {root} does not exist")
            return

        # for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        #     dirpath = Path(dirpath)
        #     filenames = [dirpath / name for name in filenames]
        #     args = [(patterns_path, engine, filename) for filename in filenames]
        #
        #     with Pool() as pool:
        #         pool.starmap(FileScannerPool.scan_file, args)

        with Pool(initializer=init_worker) as pool:
            for dirpath, dirnames, filenames in os.walk(root,
                                                        followlinks=follow_symlinks):
                dirpath = Path(dirpath)
                filenames = [dirpath / name for name in filenames]
                args = [(patterns_path, engine, filename) for filename in
                        filenames]
                pool.starmap(FileScannerPool.scan_file, args)