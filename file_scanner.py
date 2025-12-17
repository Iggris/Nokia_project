import os
from multiprocessing.pool import Pool
from re import match
from typing import List, Dict
from engines.base_engine import RegexEngine  
from engines.hs_engine import HyperscanEngine 
from engines.python_engine import PythonEngine
from file_reader import FileReader
from pathlib import Path


class FileScanner:
    """Class for scanning files using various regex engines"""
    
    def __init__(self, engine: RegexEngine = None):
        """
        Args:
            engine: Implementacja RegexEngine (domyślnie HyperscanEngine)
        """
        self.engine = engine or HyperscanEngine()
        #self.engine = engine or PythonEngine()  #for comparison

    def compile_patterns(self, patterns: List[str]) -> None:
        """Compiles patterns as bytes"""
        pattern_bytes = [pattern.encode('utf-8') for pattern in patterns]
        self.engine.compile_patterns(pattern_bytes)
    
    def _match_callback(self, pattern_id: int, start: int, end: int, flags: int, filename: str):
        """Callback triggered when a match is found
        """

        with open(filename, "r") as f:
            f.seek(start)
            match = f.read(end - start)

        print(f"Regex with ID: {pattern_id}, filename: '{filename}', from: {start} end: {end}, match: '{match}'")

    def scan_file(self, filename: str, chunk_size: int = 4096,full_file: bool = False) -> None:
        """Scans file in streaming mode (STREAM mode)
        
        Args:
            filename: file path
            chunk_size: Chunk size in bytes for scanning file (default 4096)
            full_file: If True, read entire file as single chunk (default False)
        """

        def callback(pattern_id, start, end, flags, context):
            self._match_callback(pattern_id, start, end, flags, filename)

        try:
            self.engine.scan_stream(FileReader.chunks(filename, chunk_size=chunk_size,full_file=full_file), callback, context=filename)
            
        except Exception as e:
            print(f"An error occurred while trying to scan file: '{filename}': {e}")

    def scan_tree(self, root, follow_symlinks=False, full_file=False) -> None:
        root = Path(root)
        if not root.exists():
            print(f"[scan_tree] Directory {root} does not exist")
            return

        for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
            dirpath = Path(dirpath)

            for name in filenames:
                path = dirpath / name

                try:
                    self.scan_file(str(path), full_file=full_file)
                except PermissionError:
                    print(f"[scan_tree] No permissions for the file: {path}")
                except Exception as e:
                    print(f"[scan_tree] Error with file {path}: {e}")
