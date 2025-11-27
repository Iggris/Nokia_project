import os
from typing import List, Dict
from engines.base_engine import RegexEngine  
from engines.hs_engine import HyperscanEngine 
from engines.python_engine import PythonEngine
from file_reader import FileReader
from pathlib import Path


class FileScanner:
    """Klasa do skanowania plików z użyciem różnych silników regex"""
    
    def __init__(self, engine: RegexEngine = None):
        """
        Args:
            engine: Implementacja RegexEngine (domyślnie HyperscanEngine)
        """
        self.engine = engine or HyperscanEngine()
        #self.engine = engine or PythonEngine()  #do porownania
        self.results = []
    
    def compile_patterns(self, patterns: List[str]) -> None:
        """Kompiluje wzorce jako bytes"""
        pattern_bytes = [pattern.encode('utf-8') for pattern in patterns]
        self.engine.compile_patterns(pattern_bytes)
    
    def _match_callback(self, pattern_id: int, start: int, end: int, flags: int, filename: str):
        """Callback wywoływany przy znalezieniu dopasowania
        """
        if pattern_id < len(self.engine.patterns):
            pattern = self.engine.patterns[pattern_id]
            pattern = pattern.decode('utf-8', errors='ignore')
        else:
            # if database was built from serialized compiled patterns,
            # it's impossible to retrieve its pattern rule
            pattern = "UNKNOWN"

        result = {
            'pattern_id': pattern_id,
            'start': start,
            'end': end,
            'match': pattern,
            'filename': filename
        }
        self.results.append(result)

    def scan_file(self, filename: str, chunk_size: int = 4096) -> List[Dict]:
        """Scans file in streaming mode (STREAM mode)
        
        Args:
            filename: file path
            chunk_size: Chunk size in bytes for scanning file (default 4096)
        """
        self.results = []
        
        def callback(pattern_id, start, end, flags, context):
            self._match_callback(pattern_id, start, end, flags, filename)
        
        try:
            self.engine.scan_stream(FileReader.chunks(filename, chunk_size=chunk_size), callback, context=filename)
            
        except Exception as e:
            print(f"An error occurred while trying to scan file: '{filename}': {e}")

        return self.results

    def scan_tree(self,root,follow_symlinks = False):
        root = Path(root)
        all_matches= []
        if not root.exists():
            print(f"[scan_tree] Katalog {root} nie istnieje")
            return []

        for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
            dirpath = Path(dirpath)

            for name in filenames:
                path = dirpath / name

                #dodac dodatkowe opcje

                try:
                    file_matches = self.scan_file(str(path))
                    all_matches.extend(file_matches)
                except PermissionError:
                    print(f"[scan_tree] Brak uprawnień do pliku: {path}")
                except Exception as e:
                    print(f"[scan_tree] Błąd przy pliku {path}: {e}")

        return all_matches
